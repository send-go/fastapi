# sendgo-fastapi

> **FastAPI에서 카카오 알림톡, 친구톡, SMS를 가장 쉽게 발송하는 공식 FastAPI 확장 패키지**

[![PyPI](https://img.shields.io/pypi/v/sendgo-fastapi)](https://pypi.org/project/sendgo-fastapi/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

`sendgo-fastapi`는 [`sendgo-python`](https://github.com/send-go/python) 코어를 확장한 **FastAPI 전용 패키지**입니다.
환경변수 기반 설정 로딩(pydantic-settings), 의존성 주입(`Depends`), lifespan 초기화 등 FastAPI 통합을 완벽하게 제공합니다.

---

## 목차

- [설치](#설치)
- [빠른 시작](#빠른-시작)
- [의존성 주입 사용법](#의존성-주입-사용법)
- [lifespan 초기화](#lifespan-초기화)
- [상세 사용법](#상세-사용법)
  - [알림톡](#알림톡)
  - [친구톡](#친구톡)
  - [SMS / LMS / MMS](#sms--lms--mms)
- [서비스 클래스 패턴](#서비스-클래스-패턴)
- [백그라운드 태스크 비동기 발송](#백그라운드-태스크-비동기-발송)
- [예외 처리](#예외-처리)
- [설정 옵션](#설정-옵션)
- [자주 묻는 질문](#자주-묻는-질문-faq)

---

## 설치

```bash
pip install sendgo-fastapi
```

코어 패키지 `sendgo-python`은 의존성으로 자동 설치됩니다.

---

## 빠른 시작

### 1단계 — 환경변수 설정 (`.env` 또는 셸 환경)

모든 환경변수는 `SENDGO_` 접두사를 사용하며, `SendgoSettings`가 자동으로 바인딩합니다.

```env
SENDGO_ACCESS_KEY=your_access_key
SENDGO_SECRET_KEY=your_secret_key
SENDGO_KAKAO_SENDER_KEY=your_kakao_key
SENDGO_SMS_SENDER_KEY=your_sms_key
SENDGO_API_VERSION=v2
SENDGO_BASE_URL=https://sendgo.io
```

### 2단계 — 알림톡 전송

```python
from fastapi import FastAPI
from sendgo_fastapi import SendgoDep

app = FastAPI()


@app.post("/notify")
async def notify(sendgo: SendgoDep):
    sendgo.alimtalk.send(
        template_code="ORDER_CONFIRM_001",
        contacts=[
            {"contact": "01012345678", "name": "홍길동", "var1": "ORD-001", "var2": "29,000원"},
        ],
    )
    return {"success": True}
```

`SendgoDep`은 `Annotated[Sendgo, Depends(get_sendgo)]`의 별칭으로, 라우트 인자에
타입힌트만 추가하면 Sendgo 클라이언트가 자동으로 주입됩니다.

---

## 의존성 주입 사용법

```python
from fastapi import FastAPI
from sendgo_fastapi import SendgoDep

app = FastAPI()


@app.post("/verify")
async def send_verification(sendgo: SendgoDep):
    # SMS 발송
    sendgo.sms.send_sms(
        content="[인증] 인증번호: 123456 (5분 이내 입력)",
        contacts=[{"contact": "01012345678"}],
    )
    return {"success": True}
```

환경변수 기반 클라이언트는 최초 요청 시 한 번만 생성되어 메모이즈됩니다.

---

## lifespan 초기화

애플리케이션 시작 시점에 클라이언트를 미리 생성해 `app.state.sendgo`에
저장하려면 `init_sendgo(app)`을 lifespan에서 호출하세요. 이 경우
`SendgoDep`/`get_sendgo`는 저장된 인스턴스를 우선 사용합니다.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sendgo_fastapi import SendgoDep, init_sendgo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시점에 환경변수 기반 클라이언트를 생성해 app.state.sendgo 에 저장
    init_sendgo(app)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/notify")
async def notify(sendgo: SendgoDep):
    sendgo.alimtalk.send(
        template_code="ORDER_CONFIRM_001",
        contacts=[{"contact": "01012345678", "var1": "ORD-001"}],
    )
    return {"success": True}
```

커스텀 설정을 직접 주입할 수도 있습니다.

```python
from sendgo_fastapi import SendgoSettings, init_sendgo

init_sendgo(app, SendgoSettings(access_key="...", secret_key="..."))
```

---

## 상세 사용법

### 알림톡

```python
from sendgo_fastapi import SendgoDep


@app.post("/orders/{order_id}/confirm")
async def confirm(order_id: str, sendgo: SendgoDep):
    # 다건 발송
    sendgo.alimtalk.send(
        template_code="ORDER_CONFIRM_001",
        contacts=[
            {"contact": "01011111111", "name": "홍길동", "var1": "ORD-001", "var2": "29,000원"},
            {"contact": "01022222222", "name": "김철수", "var1": "ORD-002", "var2": "15,000원"},
        ],
    )

    # 예약 발송
    sendgo.alimtalk.send(
        template_code="PROMO_SUMMER_2026",
        schedule_type="SCHEDULED",
        at="2026-07-28 09:00:00",
        contacts=[{"contact": "01012345678", "var1": "여름 한정 50% 할인"}],
    )

    # SMS 자동 대체 발송
    sendgo.alimtalk.send(
        template_code="DELIVERY_START_001",
        replace_sms="Y",
        sms_subject="[배송 시작 안내]",
        sms_content="주문하신 상품이 출고되었습니다.\n송장번호: 1234567890",
        contacts=[{"contact": "01012345678", "var1": "ORD-001", "var2": "1234567890"}],
    )
    return {"success": True}
```

### 친구톡

```python
# 텍스트형
sendgo.friendtalk.send(
    content="안녕하세요! 7월 한정 특가 이벤트를 확인해보세요.",
    contacts=[{"contact": "01012345678"}],
)

# 이미지형
sendgo.friendtalk.send(
    message_type="FI",
    content="이번 주 특가 상품을 확인하세요!",
    image_url="https://cdn.example.com/banner.jpg",
    image_link="https://example.com/event",
    contacts=[{"contact": "01012345678"}],
)

# 버튼 포함
sendgo.friendtalk.send(
    content="7월 쿠폰이 도착했습니다! 지금 바로 사용하세요.",
    buttons=[
        {"name": "쿠폰 받기", "type": "WL", "linkMo": "https://example.com/coupon"},
        {"name": "고객센터", "type": "WL", "linkMo": "https://example.com/cs"},
    ],
    contacts=[{"contact": "01012345678"}],
)
```

### SMS / LMS / MMS

```python
# SMS (90자 이하)
sendgo.sms.send_sms(
    content="[Sendgo] 인증번호: 123456 (5분 이내 입력)",
    contacts=[{"contact": "01012345678"}],
)

# LMS (장문, 2,000자 이하)
sendgo.sms.send_lms(
    subject="[중요] 서비스 점검 안내",
    content="안녕하세요. 서비스 점검이 예정되어 있습니다.\n\n■ 일시: 2026-07-25 02:00 ~ 06:00",
    contacts=[{"contact": "01012345678"}],
)

# MMS (이미지 포함)
sendgo.sms.send_mms(
    subject="[이벤트] 7월 특가",
    content="이번 달 특가 상품을 확인하세요!",
    contacts=[{"contact": "01011111111"}, {"contact": "01022222222"}],
)
```

---

## 서비스 클래스 패턴

라우트에서 직접 발송하는 대신, 재사용 가능한 서비스 클래스로 분리할 수 있습니다.

```python
# app/services/notification.py
from sendgo import Sendgo


class NotificationService:
    def __init__(self, sendgo: Sendgo) -> None:
        self._sendgo = sendgo

    def send_order_confirm(self, phone: str, order_no: str, amount: int) -> None:
        self._sendgo.alimtalk.send(
            template_code="ORDER_CONFIRM_001",
            contacts=[{"contact": phone, "var1": order_no, "var2": f"{amount:,}원"}],
        )
```

```python
# app/main.py
from typing import Annotated

from fastapi import Depends, FastAPI
from sendgo_fastapi import SendgoDep

from app.services.notification import NotificationService

app = FastAPI()


def get_notification_service(sendgo: SendgoDep) -> NotificationService:
    return NotificationService(sendgo)


NotificationDep = Annotated[NotificationService, Depends(get_notification_service)]


@app.post("/orders/{order_id}/confirm")
async def confirm(order_id: str, service: NotificationDep):
    service.send_order_confirm("01012345678", order_id, 29000)
    return {"success": True}
```

---

## 백그라운드 태스크 비동기 발송

발송을 요청 응답과 분리하려면 FastAPI의 `BackgroundTasks`를 사용하세요.

```python
from fastapi import BackgroundTasks, FastAPI
from sendgo_fastapi import SendgoDep

app = FastAPI()


@app.post("/notify")
async def notify(sendgo: SendgoDep, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        sendgo.alimtalk.send,
        template_code="ORDER_CONFIRM_001",
        contacts=[{"contact": "01012345678", "var1": "ORD-001"}],
    )
    return {"success": True, "queued": True}
```

---

## 예외 처리

```python
from fastapi import FastAPI, HTTPException
from sendgo import SendgoError
from sendgo_fastapi import SendgoDep

app = FastAPI()


@app.post("/notify")
async def notify(sendgo: SendgoDep):
    try:
        sendgo.alimtalk.send(
            template_code="ORDER_CONFIRM_001",
            contacts=[{"contact": "01012345678", "var1": "ORD-001"}],
        )
    except SendgoError as e:
        raise HTTPException(status_code=502, detail=f"Sendgo 발송 실패: {e}")
    return {"success": True}
```

전역 예외 핸들러로 처리할 수도 있습니다.

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from sendgo import SendgoError


@app.exception_handler(SendgoError)
async def sendgo_exception_handler(request: Request, exc: SendgoError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})
```

---

## 설정 옵션

`SendgoSettings`(pydantic-settings)가 `SENDGO_` 접두사 환경변수를 자동으로 읽습니다.

| 필드 | 환경변수 | 기본값 | 설명 |
|------|---------|--------|------|
| `access_key` | `SENDGO_ACCESS_KEY` | — | Sendgo 액세스 키 (필수) |
| `secret_key` | `SENDGO_SECRET_KEY` | — | Sendgo 시크릿 키 (필수) |
| `kakao_sender_key` | `SENDGO_KAKAO_SENDER_KEY` | `None` | 카카오 발신프로필 키 |
| `sms_sender_key` | `SENDGO_SMS_SENDER_KEY` | `None` | SMS 발신자 키 |
| `api_version` | `SENDGO_API_VERSION` | `"v2"` | API 버전 |
| `base_url` | `SENDGO_BASE_URL` | `"https://sendgo.io"` | API 기본 URL |

---

## 자주 묻는 질문 (FAQ)

**Q. `sendgo-python`과의 차이는 무엇인가요?**
A. `sendgo-python`은 프레임워크 독립적인 순수 Python 코어 패키지입니다. `sendgo-fastapi`는 이를 확장해 pydantic-settings 기반 환경변수 로딩, `Depends` 의존성 주입, lifespan 초기화 등 FastAPI 통합을 추가합니다.

**Q. 환경변수 없이 설정을 직접 지정할 수 있나요?**
A. 네, `init_sendgo(app, SendgoSettings(access_key="...", secret_key="..."))`처럼 설정 객체를 직접 주입할 수 있습니다.

**Q. `get_sendgo`는 요청마다 새 클라이언트를 만드나요?**
A. 아니요. 환경변수 기반 싱글턴 또는 `app.state.sendgo`에 저장된 인스턴스를 재사용합니다.

**Q. 테스트 시 Sendgo를 Mock 처리하려면?**
A. `app.dependency_overrides[get_sendgo] = lambda: mock_client`로 의존성을 교체하면 됩니다.

---

## 관련 패키지

| 언어/프레임워크 | 패키지 | GitHub |
|----------------|--------|--------|
| Python (순수) | `sendgo-python` | [python](https://github.com/send-go/python) |
| Django | `sendgo-django` | [django](https://github.com/send-go/django) |
| PHP (순수) | `sendgo/php` | [php](https://github.com/send-go/php) |
| Laravel | `sendgo/laravel` | [laravel](https://github.com/send-go/laravel) |
| 전체 목록 | — | [send-go GitHub 조직](https://github.com/send-go) |

---

## 라이선스

MIT License © 2026 [Sendgo](https://sendgo.io)

---

*키워드: 카카오 알림톡 FastAPI, 카카오 친구톡 FastAPI, SMS 발송 FastAPI, 알림톡 FastAPI 패키지, FastAPI 카카오 API 연동, FastAPI 의존성 주입, Sendgo FastAPI SDK*
