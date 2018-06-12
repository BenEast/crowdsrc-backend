import base64
import requests

# Crowdsrc imports
from crowdsrc.src.models import *
from crowdsrc.src.serializers import *
from crowdsrc.src.serializers.auth_serializers import RefreshableExpiringTokenSerializer
from crowdsrc.settings import BASE_DOMAIN, DEFAULT_FROM_EMAIL, GOOGLE_RECAPTCHA_SECRET_KEY, TOKEN_EXPIRE_TIME, REST_FRAMEWORK as settings

# Django imports
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import force_text
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.status import HTTP_200_OK
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_jwt.settings import api_settings

from auditlog.models import LogEntry
from auditlog.diff import model_instance_diff
from auditlog.registry import auditlog


class VerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (str(user.id) + str(timestamp) + str(user.is_active) + str(user.profile.created))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[-1]
    else:
        return request.META.get('REMOTE_ADDR')


def log_event(request, start, end, action: int, extra=None):
    if start == None and end == None:
        raise ValueError('start and end cannot both be none!')

    object_key = start.id if start != None else end.id
    instance = start if start != None else end

    # Determine if instance has created/last updated
    # We don't want to log these fields

    exclude = []
    try:
        instance._meta.get_field('created')
        exclude.append('created')
    except:
        pass
    try:
        instance._meta.get_field('last_updated')
        exclude.append('last_updated')
    except:
        pass

    # Register the type to allow logging
    auditlog.register(type(instance), exclude_fields=exclude)

    log = LogEntry.objects.log_create(
        instance,
        object_pk=object_key,
        object_id=object_key,
        object_repr=str(start) if start != None else str(end),
        action=action,
        changes=model_instance_diff(start, end),
        actor_id=request.user.id,
        timestamp=timezone.now(),
        content_type_id=6,  # This is the id for auditlog listed in django_content_types table
        remote_addr=get_client_ip(request),
        additional_data=extra
    )

    # Unregister the type to disable auto (duplicate) logging
    auditlog.unregister(type(instance))


def send_confirmation_email(user: User, update=False):
    # Create a verification token for the user's email
    token = VerificationTokenGenerator().make_token(user)
    b64uid = force_text(base64.urlsafe_b64encode(bytes([user.id])))

    message = 'Hello ' + user.username + '!\n\n'

    if update:
        title = 'Crowdsrc | Update your email'
        target = [Profile.objects.get(user_id=user.id).pending_email]
        message += 'Visit the following link to verify your email and update your Crowdsrc account.\n\n'
    else:
        title = 'Crowdsrc | Activate your account'
        target = [user.email]
        message += 'Visit the following link to verify your email and activate your Crowdsrc account.\n\n'

    message += BASE_DOMAIN + '/verify/?uid=' + b64uid + '&token=' + token
    message += '\n\n\nQuestions or concerns? Contact us at ' + BASE_DOMAIN + '/contact/'

    send_mail(title, message, DEFAULT_FROM_EMAIL, target)


def get_refresh_token(user_data):
    return api_settings.JWT_ENCODE_HANDLER(api_settings.JWT_PAYLOAD_HANDLER(user_data))

def manageRefreshToken(user):
    token, created = RefreshableExpiringToken.objects.get_or_create(
        user=user, defaults={'refresh_token': get_refresh_token(user)})

    # If created, don't check if it's expired already
    if not created and token.created < timezone.now() - TOKEN_EXPIRE_TIME:
        token.delete()

        token = RefreshableExpiringToken.objects.create(user=user,
                                                        refresh_token=get_refresh_token(user))

    return RefreshableExpiringTokenSerializer(token)


# Verify that the request passed recaptcha before creating the user
def validate_recaptcha(request) -> bool:
    data = {
        'secret': GOOGLE_RECAPTCHA_SECRET_KEY,
        'response': request.data.get('recaptcha_response'),
        'remoteip': get_client_ip(request)
    }

    request = requests.post(url='https://www.google.com/recaptcha/api/siteverify',
                            data=data)

    return request.json().get('success')


class DispatchEmail(CreateAPIView):
    permission_classes = (AllowAny,)
    # serializer_class = UserListGETSerializer
    # queryset = User.objects.all()

    def post(self, request):
        message = 'Created ' + str(timezone.now())
        message += '\nEmail: ' + request.data['email']
        message += '\nUsername: ' + request.data['username']
        message += '\nName: ' + request.data['name']
        message += '\nMessage: ' + request.data['message']

        return Response({'response': send_mail('Crowdsrc Contact from ' + request.data['username'], message,
                                               DEFAULT_FROM_EMAIL, ['ben.east22@gmail.com'])})


class GlobalSearchListView(ListAPIView):
    serializer_class = ProjectListGETSerializer

    def list(self, request):
        search_terms = request.query_params.get(
            'query', None).replace(',', ' ').split()

        for search_term in search_terms:
            # Filter projects
            projects = ProjectListGETSerializer(
                Project.objects.filter(Q(title__icontains=search_term)
                                       | Q(description__icontains=search_term)
                                       | Q(website__icontains=search_term)
                                       | Q(categories__category__name__icontains=search_term)
                                       | Q(tasks__skills__skill__name__icontains=search_term)
                                       ).distinct(), many=True).data

            # Filter users -- respect privacy settings in search
            users = UserSearchSerializer(
                User.objects.filter(Q(settings__privacy__allow_email_search=True, email__icontains=search_term) |
                                    Q(settings__privacy__allow_loc_search=True, profile__location__icontains=search_term) |
                                    Q(settings__privacy__allow_username_search=True, username__icontains=search_term) |
                                    Q(settings__privacy__allow_name_search=True, first_name__icontains=search_term) |
                                    Q(settings__privacy__allow_name_search=True, last_name__icontains=search_term)).distinct(),
                many=True, context={'requester_id': request.user.id}).data

            # Filter tasks
            tasks = TaskGETSerializer(
                Task.objects.filter(Q(title__icontains=search_term)
                                    | Q(description__icontains=search_term)
                                    | Q(skills__skill__name__icontains=search_term)
                                    ).distinct(),
                context={'requester_id': request.user.id}, many=True).data

        # Paginate the results
        pages = Paginator(projects + users + tasks, settings.get('PAGE_SIZE'))
        page = pages.get_page(int(request.query_params.get('page', None)))

        return Response({'count': pages.count, 'page': page.number, 'results': page.object_list},
                        status=HTTP_200_OK)
