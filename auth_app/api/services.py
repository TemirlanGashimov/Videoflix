from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def blacklist_refresh_token(raw_token):
    if not raw_token:
        return False
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return False
    return True