"""
Sendgo FastAPI 확장 — 카카오 알림톡/친구톡, SMS/LMS/MMS

FastAPI 애플리케이션에서 Sendgo 코어(`sendgo-python`)를 손쉽게 사용할 수 있도록
환경변수 기반 설정 로딩과 의존성 주입(Depends)을 제공합니다.

사용법:
    from fastapi import FastAPI
    from sendgo_fastapi import SendgoDep

    app = FastAPI()

    @app.post("/notify")
    async def notify(sendgo: SendgoDep):
        sendgo.alimtalk.send(
            template_code="ORDER_CONFIRM_001",
            contacts=[{"contact": "01012345678", "var1": "ORD-001"}],
        )
        return {"success": True}
"""

from .dependencies import SendgoDep, get_sendgo, init_sendgo
from .settings import SendgoSettings

__all__ = ["SendgoSettings", "get_sendgo", "SendgoDep", "init_sendgo"]
__version__ = "1.0.0"
