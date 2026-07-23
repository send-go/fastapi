"""Sendgo FastAPI 설정 모듈.

`SENDGO_` 접두사를 가진 환경변수(예: `SENDGO_ACCESS_KEY`)를 자동으로 읽어
Sendgo 코어 클라이언트 생성에 필요한 값을 바인딩합니다.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class SendgoSettings(BaseSettings):
    """환경변수 기반 Sendgo 설정.

    `SENDGO_ACCESS_KEY`, `SENDGO_SECRET_KEY`, `SENDGO_KAKAO_SENDER_KEY`,
    `SENDGO_SMS_SENDER_KEY`, `SENDGO_API_VERSION`, `SENDGO_BASE_URL`
    환경변수를 각각 아래 필드로 매핑합니다.
    """

    # Sendgo 인증 키 (필수)
    access_key: str
    secret_key: str

    # 발신 프로필 키 (선택)
    kakao_sender_key: str | None = None
    sms_sender_key: str | None = None

    # API 버전 및 기본 URL
    api_version: str = "v2"
    base_url: str = "https://sendgo.io"

    model_config = SettingsConfigDict(env_prefix="SENDGO_")
