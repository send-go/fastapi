"""Sendgo FastAPI 의존성 주입 모듈.

환경변수 기반 설정으로 `Sendgo` 코어 클라이언트를 생성/메모이즈하고,
FastAPI 라우트에서 `Depends`로 주입할 수 있는 `SendgoDep`을 제공합니다.

또한 `init_sendgo(app)`으로 애플리케이션 시작 시점에 클라이언트를
`app.state.sendgo`에 저장할 수 있으며, 이 경우 요청 처리 시 해당
인스턴스를 우선 사용합니다(환경변수 기반 싱글턴보다 우선).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Request
from sendgo import Sendgo, AccountClient

from .settings import SendgoSettings

# 환경변수 기반 싱글턴 클라이언트
_client: Optional[Sendgo] = None


@lru_cache
def get_settings() -> SendgoSettings:
    """환경변수를 읽어 SendgoSettings를 생성하고 캐시합니다."""
    return SendgoSettings()


def _build_client(settings: SendgoSettings) -> Sendgo:
    """설정으로부터 Sendgo 코어 클라이언트를 생성합니다."""
    return Sendgo(
        access_key=settings.access_key,
        secret_key=settings.secret_key,
        kakao_sender_key=settings.kakao_sender_key,
        sms_sender_key=settings.sms_sender_key,
        api_version=settings.api_version,
        base_url=settings.base_url,
    )


def _get_singleton() -> Sendgo:
    """환경변수 기반 싱글턴 클라이언트를 생성/메모이즈합니다."""
    global _client
    if _client is None:
        _client = _build_client(get_settings())
    return _client


def get_sendgo(request: Request) -> Sendgo:
    """FastAPI 의존성으로 주입되는 Sendgo 클라이언트를 반환합니다.

    `init_sendgo()`로 `app.state.sendgo`가 설정되어 있으면 이를 우선 사용하고,
    그렇지 않으면 환경변수 기반 싱글턴을 사용합니다.
    """
    client = getattr(request.app.state, "sendgo", None)
    if client is not None:
        return client
    return _get_singleton()


def init_sendgo(app: FastAPI, settings: SendgoSettings | None = None) -> Sendgo:
    """애플리케이션에 Sendgo 클라이언트를 초기화해 `app.state.sendgo`에 저장합니다.

    lifespan 이벤트 등에서 호출하면, 이후 `get_sendgo`/`SendgoDep`이 이 인스턴스를
    우선 사용합니다. `settings`를 생략하면 환경변수 기반 설정을 사용합니다.
    """
    client = _build_client(settings or get_settings())
    app.state.sendgo = client
    return client


# 라우트에서 `sendgo: SendgoDep` 형태로 주입받기 위한 타입 별칭
SendgoDep = Annotated[Sendgo, Depends(get_sendgo)]


# 계정 API 설정은 발송용 필수 키를 요구하는 SendgoSettings와 독립적입니다.
def get_account() -> AccountClient:
    """SENDGO_AGENT_TOKEN과 SENDGO_BASE_URL로 계정 클라이언트를 만듭니다."""
    import os
    return AccountClient(
        agent_token=os.environ.get("SENDGO_AGENT_TOKEN", ""),
        base_url=os.environ.get("SENDGO_BASE_URL", "https://sendgo.io"),
    )


AccountDep = Annotated[AccountClient, Depends(get_account)]
