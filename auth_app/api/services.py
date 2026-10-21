from django.conf import settings


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
