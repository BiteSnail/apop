# fitbit/services/token_service.py
import logging
from datetime import timedelta
from typing import Optional

import requests
from django.conf import settings
from django.utils import timezone

from fitbit.models import FitbitAccount

FITBIT_OAUTH_TOKEN_URL = "https://api.fitbit.com/oauth2/token"
log = logging.getLogger(__name__)

#시간 한국기준 아님. UTC임
def refresh_access_token_by_uid(
    fitbit_user_id: str,
    *,
    force: bool = False,
) -> Optional[str]:
    """
    주어진 fitbit_user_id에 대해 access_token을 갱신(또는 아직 유효하면 그대로 반환).

    Parameters
    ----------
    fitbit_user_id : str
        Fitbit에서 발급한 고유 사용자 ID
    force : bool, default False
        True 로 주면 만료 여부와 상관없이 무조건 리프레시 시도

    Returns
    -------
    str | None
        새(또는 기존) access_token.
        refresh_token까지도 무효(=재인증 필요)면 None 반환.
    """
    try:
        account = FitbitAccount.objects.get(fitbit_user_id=fitbit_user_id)
    except FitbitAccount.DoesNotExist:
        log.warning("FitbitAccount not found: %s", fitbit_user_id)
        return None

    # 1) 아직 만료 안 됐으면 그대로 돌려주기
    if not force and account.expires_at and account.expires_at > timezone.now() + timedelta(minutes=2):
        return account.access_token

    # 2) 리프레시 시도
    resp = requests.post(
        FITBIT_OAUTH_TOKEN_URL,
        auth=(settings.FITBIT_CLIENT_ID, settings.FITBIT_CLIENT_SECRET),  # HTTP Basic
        data={
            "grant_type": "refresh_token",
            "refresh_token": account.refresh_token,
        },
        timeout=15,
    )

    if resp.status_code == 200:
        data = resp.json()
        account.access_token = data["access_token"]
        account.refresh_token = data["refresh_token"]         # rotating!
        account.expires_at = timezone.now() + timedelta(seconds=data["expires_in"])
        account.save(update_fields=["access_token", "refresh_token", "expires_at"])
        log.info("Fitbit token refreshed for %s", fitbit_user_id)
        return account.access_token

    # 3) 실패 처리 ─ refresh_token 무효 또는 기타 오류
    err = resp.json().get("errors", [{}])[0]
    log.error("Fitbit refresh failed for %s → %s / %s",
              fitbit_user_id, err.get("errorType"), err.get("message"))
    # 필요하다면 needs_reauth BooleanField가 있다면 표시
    if hasattr(account, "needs_reauth"):
        account.needs_reauth = True
        account.save(update_fields=["needs_reauth"])
    return None



