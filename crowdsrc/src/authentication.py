from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from crowdsrc.settings import TOKEN_EXPIRE_TIME
from crowdsrc.src.models import RefreshableExpiringToken


class ExpiringTokenAuthentication(TokenAuthentication):
    model = RefreshableExpiringToken

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise AuthenticationFailed('User inactive or deleted')

        now = timezone.now()
        if token.created < now - TOKEN_EXPIRE_TIME:
            raise AuthenticationFailed('Token has expired')

        return (token.user, token)
