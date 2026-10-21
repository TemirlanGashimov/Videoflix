from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

def _set_auth_cookie(response, name, token):

    response.set_cookie(
        key=name,
        value=str(token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )


def set_auth_cookies(response, access_token, refresh_token=None):

    _set_auth_cookie(response, "access_token", access_token)
    if refresh_token:
        _set_auth_cookie(response, "refresh_token", refresh_token)
    return response


def clear_auth_cookies(response):
    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")
    return response


def blacklist_refresh_token(raw_token):
    if not raw_token:
        return False
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return False
    return True