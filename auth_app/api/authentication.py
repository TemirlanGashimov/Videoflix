from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication

class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None
        validated_token = self.get_validated_token(access_token)
        self.enforce_csrf(request)
        user = self.get_user(validated_token)
        return (user, validated_token)

    def enforce_csrf(self, request):
        SessionAuthentication().enforce_csrf(request)