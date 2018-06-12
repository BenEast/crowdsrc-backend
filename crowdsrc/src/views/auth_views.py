import base64
import re

# Crowdsrc imports
from crowdsrc.settings import BASE_DOMAIN, DEFAULT_FROM_EMAIL, CREATE, UPDATE
from crowdsrc.src.models import *
from crowdsrc.src.serializers.auth_serializers import RefreshableExpiringTokenSerializer
from crowdsrc.src.serializers.user_serializers import UserListGETSerializer, UserPATCHSerializer, UserPOSTSerializer
from crowdsrc.src.views import *

# Django imports
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.utils.encoding import force_text
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED


class ObtainExpiringAuthToken(ObtainAuthToken):
    model = RefreshableExpiringToken
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Get user token information
            serializer = manageRefreshToken(user)
            # Get serializer.data before last_login update to get correct notifications
            response_data = serializer.data

            user.last_login = timezone.now()
            user.save()

            return Response(response_data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class RefreshExpiringAuthToken(APIView):
    model = RefreshableExpiringToken
    serializer_class = RefreshableExpiringTokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            token = self.model.objects.get(
                refresh_token=request.data['refresh_token'])
            user = token.user
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # If the token was found and the refresh token hasn't expired,
        # refresh the auth token and return
        if timezone.now() <= token.refresh_expires:
            token.delete()

            token = RefreshableExpiringToken.objects.create(user=user,
                                                            refresh_token=get_refresh_token(user))

            # Get serializer data before updating last_login so we get accurate notifications
            response_data = RefreshableExpiringTokenSerializer(token).data

            user.last_login = timezone.now()
            user.save()

            return Response(response_data, status=HTTP_200_OK)
        return Response('Refresh token expired', status=HTTP_401_UNAUTHORIZED)


class CheckUsernameView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserListGETSerializer

    def retrieve(self, request, username=None, *args, **kwargs):
        # Return true if username is available, false if taken
        try:
            User.objects.get(username=username)
            return Response(False, status=HTTP_200_OK)
        except:
            return Response(True, status=HTTP_200_OK)


class RegisterUserView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPOSTSerializer
    permission_classes = (AllowAny,)

    def send_notification_email(self, email: str):
        user = self.queryset.get(email=email)

        message = 'Hello ' + user.username + '!\n\n'
        message += 'It looks like you tried to create a new account with this email address, '
        message += 'but you already have a Crowdsrc account.\n\n'
        message += 'If you forgot your password, you can reset it using the following link.\n\n'
        message += BASE_DOMAIN + '/forgot-password/'
        message += '\n\n\nQuestions or concerns? Contact us at ' + BASE_DOMAIN + '/contact/'

        send_mail('Recover Crowdsrc Account', message,
                  DEFAULT_FROM_EMAIL, [email])

    def create(self, request):
        if not validate_recaptcha(request):
            return Response('invalid recaptcha', status=HTTP_401_UNAUTHORIZED)

        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
        except Exception as e:
            if 'email is taken' in e.args:
                self.send_notification_email(request.data.get('email'))
                return Response(status=HTTP_204_NO_CONTENT)
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        instance = self.queryset.get(id=serializer.data.get('id'))
        send_confirmation_email(instance)
        log_event(request, None, instance, CREATE)

        return Response(status=HTTP_204_NO_CONTENT)


class ResendEmailVerificationView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPOSTSerializer
    permission_classes = (AllowAny,)

    def post(self, request, b64uid=None, *args, **kwargs):
        try:
            # Recover the user instance from the user id
            user_id = int.from_bytes(
                base64.urlsafe_b64decode(b64uid), byteorder='big')
            user = self.queryset.get(id=user_id)
        except:
            return Response('invalid uid', status=HTTP_400_BAD_REQUEST)

        # Check if the user has a pending email
        profile = Profile.objects.get(user_id=user.id)
        if profile.pending_email:
            send_confirmation_email(user, update=True)
        else:
            send_confirmation_email(user)

        return Response(status=HTTP_204_NO_CONTENT)


class EmailVerificationView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPOSTSerializer
    permission_classes = (AllowAny,)

    def post(self, request, b64uid=None, token=None, *args, **kwargs):
        try:
            # Recover the user instance from the user id
            user_id = int.from_bytes(
                base64.urlsafe_b64decode(b64uid), byteorder='big')
            user = self.queryset.get(id=user_id)
        except:
            return Response('Invalid verification URL', status=HTTP_400_BAD_REQUEST)

        if VerificationTokenGenerator().check_token(user, token):
            if not user.is_active:  # If the account is not active, activate the account
                user.is_active = True
                log_event(request, self.queryset.get(id=user_id), user,
                          UPDATE, extra={'note': 'Verified email'})
                user.save()

                token_serializer = manageRefreshToken(user)
                return Response(token_serializer.data, status=HTTP_200_OK)

            else:  # Else if there is a pending email, update that address
                profile = Profile.objects.get(user_id=user.id)

                if profile.pending_email:
                    user.email = profile.pending_email
                    log_event(request, self.queryset.get(id=user_id), user,
                              UPDATE, extra={'note': 'Updated email'})
                    user.save()

                    profile.pending_email = None
                    profile.save()

                    token_serializer = manageRefreshToken(user)
                    return Response(token_serializer.data, status=HTTP_200_OK)
        return Response('Invalid verification URL', status=HTTP_400_BAD_REQUEST)


class RequestPasswordResetView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPATCHSerializer
    permission_classes = (AllowAny,)

    def send_password_reset_email(self, user: User):
        token = PasswordResetTokenGenerator().make_token(user)
        b64uid = force_text(base64.urlsafe_b64encode(bytes([user.id])))

        message = 'Hello ' + user.username + ',\n\n'
        message += 'We received a request to reset your Crowdsrc password.\n'
        message += 'Click this link to reset your password: '
        message += BASE_DOMAIN + '/reset-password/?uid=' + b64uid + '&token=' + token
        message += '\n\nIf you did not request a password reset, disregard this message.'
        message += '\n\n\nQuestions or concerns? Contact us at ' + BASE_DOMAIN + '/contact/'

        send_mail('Crowdsrc Password Reset Request',
                  message, DEFAULT_FROM_EMAIL, [user.email])

    def post(self, request, *args, **kwargs):
        if not validate_recaptcha(request):
            return Response('invalid recaptcha', status=HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(Q(email=request.data.get('email'))
                                    | Q(username=request.data.get('username')))
            self.send_password_reset_email(user)
        except:
            pass

        return Response(status=HTTP_204_NO_CONTENT)


class PasswordResetView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPATCHSerializer
    permission_classes = (AllowAny,)

    def post(self, request, b64uid=None, *args, **kwargs):
        if not validate_recaptcha(request):
            return Response('invalid recaptcha', status=HTTP_400_BAD_REQUEST)
        try:
            # Recover the user instance from the user id
            user_id = int.from_bytes(
                base64.urlsafe_b64decode(b64uid), byteorder='big')
            user = self.queryset.get(id=user_id)
        except:
            return Response('Invalid verification URL', status=HTTP_400_BAD_REQUEST)

        # If reset uid and token are valid, perform the update
        if PasswordResetTokenGenerator().check_token(user, request.data.get('token')):
            # Check if password fits regex
            password = request.data.get('password')
            if not re.fullmatch(r"(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\])[A-Za-z0-9-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\]{8,}", password):
                return Response('invalid password', status=HTTP_400_BAD_REQUEST)

            user.password = make_password(password)

            log_event(request, self.queryset.get(id=user_id), user,
                      UPDATE, extra={'note': 'Reset password'})

            user.save()

            return Response(status=HTTP_204_NO_CONTENT)
        return Response('invalid reset credentials', status=HTTP_400_BAD_REQUEST)


class PasswordChangeView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPATCHSerializer

    # Allows users to change their password iff they have:
    # - A valid auth token
    # - The current password
    # - A new password that fits requirements
    def post(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Check that current password is accurate
        if not user.check_password(request.data.get('current_password')):
            return Response(status=HTTP_401_UNAUTHORIZED)

        # Check that new password fits requirements
        new_password = request.data.get('new_password')

        if not re.fullmatch(r"(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\])[A-Za-z0-9-!@$%^&*()_+|~=`{}\[\]:;'<>?,.\/\\]{8,}", new_password):
            return Response('invalid new password', status=HTTP_400_BAD_REQUEST)

        # Update password
        user.password = make_password(new_password)
        log_event(request, self.queryset.get(id=request.user.id),
                  user, UPDATE, extra={'note': 'Changed password'})
        user.save()

        # Send user an email notifying them that their password has been changed

        return Response(status=HTTP_204_NO_CONTENT)


class EmailChangeView(APIView):
    queryset = User.objects.all()
    serializer_class = UserPATCHSerializer

    def post(self, request, *args, **kwargs):
        try:
            user = self.queryset.get(id=request.user.id)
        except:
            return Response(status=HTTP_400_BAD_REQUEST)

        # Check that current password is valid
        if not user.check_password(request.data.get('current_password')):
            return Response(status=HTTP_401_UNAUTHORIZED)

        # Check that new email is of valid form
        email = request.data.get('email')

        if not re.fullmatch(r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)', email):
            return Response('invalid email', status=HTTP_400_BAD_REQUEST)

        # Check if the email is already taken
        try:
            User.objects.get(email=email)
            return Response('email is taken', status=HTTP_400_BAD_REQUEST)
        except:
            pass

        profile = Profile.objects.get(user_id=user.id)
        profile.pending_email = email
        profile.save()

        send_confirmation_email(user, update=True)

        return Response(status=HTTP_204_NO_CONTENT)
