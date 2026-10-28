"""Helpers for setting and clearing authentication cookies."""

from django.conf import settings


def _set_auth_cookie(response, name, token):
    """Set a secure, HTTP-only authentication cookie on a response."""

    response.set_cookie(
        key=name,
        value=str(token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
    )


def set_auth_cookies(response, access_token, refresh_token=None):
    """Set the access cookie and, when provided, the refresh cookie."""

    _set_auth_cookie(response, "access_token", access_token)
    if refresh_token:
        _set_auth_cookie(response, "refresh_token", refresh_token)
    return response


def clear_auth_cookies(response):
    """Delete the access and refresh token cookies from a response."""
    response.delete_cookie("access_token", samesite="Lax")
    response.delete_cookie("refresh_token", samesite="Lax")
    return response