# sendgo-fastapi

> **FastAPI에서 카카오 알림톡, 브랜드메시지, SMS를 가장 쉽게 발송하는 공식 FastAPI 확장 패키지**

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

> ⚠️ **Deprecated — 친구톡은 카카오 정책에 따라 2025-12-31 종료되었습니다.**
> 2026-01-01 부터 친구톡 발송 요청은 카카오 측에서 **브랜드메시지(자유형)** 로 자동 대체 발송됩니다.
> 호출은 계속 성공하며, 자유 본문 타입(`FT`/`FI`/`FW`)을 개별 수신자에게 보내는 경로는
> 현재 이것뿐이므로 기존 코드를 당장 바꿀 필요는 없습니다.
>
> 다음의 경우에는 **브랜드메시지**를 사용하세요.
> - 템플릿 기반 리치 타입 (`FL`/`FC`/`FM`/`FP`/`FA`)
> - 채널 친구가 **아닌** 수신자 (`targeting` = `N` / `I`)
> - 수신 동의한 전체 채널 친구 동보 (`targeting` = `F`)
>
> 메시지 타입은 1:1 대응되며 변환은 서버가 처리합니다 — `FT`→`BT`, `FI`→`BI`, `FW`→`BW`,
> `FL`→`BL`, `FC`→`BC`, `FM`→`BM`, `FP`→`BP`, `FA`→`BA`.

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

## 브랜드메시지 · 짧은 URL

이 패키지는 코어(`sendgo-python`)의 클라이언트를 그대로 노출하므로, 코어에 있는 채널이
모두 그대로 쓸 수 있습니다. 두 기능 모두 **v2 전용**입니다.

| 기능 | 접근 |
|------|------|
| 카카오 브랜드메시지 (친구톡의 후속 채널) | `sendgo.brand_message` |
| 짧은 URL (단축 + 클릭 반응 분석) | `sendgo.short_url` |

브랜드메시지는 채널 친구가 아닌 수신자에게도 보낼 수 있고(`targeting` = `N`),
수신 동의한 전체 채널 친구에게 동보 발송할 수도 있습니다(`targeting` = `F`).

짧은 URL 은 메시지 본문의 링크를 줄이고 클릭 반응(일별 추이·디바이스·유입경로·국가)을
집계합니다.

사용 예시와 파라미터는 [코어 README](https://github.com/send-go) 와
[SDK 가이드](https://sendgo.io/ko/sdk) 를 참고하세요.

## 관리 API — 채널·템플릿·발신번호 등록 (v2 전용)

코어(`sendgo-python`)의 관리 서비스가 주입받은 클라이언트에 그대로 붙어
있습니다. 콘솔에서만 되던 등록·심사를 라우트에서 처리할 수 있습니다.

| 접근 | 하는 일 | 계정 |
| --- | --- | --- |
| `.kakao_senders` | 카카오 채널 인증·등록·동기화, 브랜드메시지 M/N 신청 | 기업 |
| `.notice_templates` | 알림톡 템플릿 CRUD, 검수 요청·취소, 승인 취소, 휴면 해제 | 기업 |
| `.brand_templates` | 브랜드메시지 템플릿 CRUD, 동기화, 가져오기 | 기업 |
| `.sender_registration` | 발신번호 등록 신청, 중복 확인, 유형 안내 | 개인·기업 |
| `.message_templates` | 문자 상용구 템플릿 CRUD | 개인·기업 |
| `.kakao_images` | 카카오 이미지 업로드 — 템플릿용 URL 발급 | 기업 |
| `.rejected_numbers` | 수신거부(080) 번호 조회 | 개인·기업 |
| `.webhook` | 이벤트 웹훅 구독 — 심사 결과 수신 | 개인·기업 |

> **sendgo.io 콘솔에 들어올 일이 없습니다.** 휴대폰 발신번호는 PASS 대신
> 신분증 사본을 받아 sendgo 운영자가 대신 심사합니다. 사람이 개입하는 지점은
> 카카오 채널 인증번호 하나뿐이고, 그것도 여러분 화면에서 입력받으면 됩니다.
> 심사가 붙는 것들은 비동기라 웹훅으로 결과를 받으세요.

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile
from sendgo import SendgoError
from sendgo_fastapi import SendgoDep

router = APIRouter(prefix="/onboarding")


@router.post("/channel/code")
async def request_channel_code(yellow_id: str, phone: str, sendgo: SendgoDep):
    """1단계 — 카카오가 관리자 휴대폰으로 인증번호를 SMS 발송한다."""
    return sendgo.kakao_senders.request_token(yellow_id, phone)


@router.post("/channel")
async def register_channel(yellow_id: str, phone: str, code: str, sendgo: SendgoDep):
    """2단계 — 사용자가 입력한 인증번호로 발신프로필 생성."""
    created = sendgo.kakao_senders.create(
        token=code,
        yellow_id=yellow_id,
        phone_number=phone,
        category_code="001001",
    )
    return created["data"]["sender"]


@router.post("/templates")
async def provision_template(kakao_sender_key: str, sendgo: SendgoDep):
    try:
        created = sendgo.notice_templates.create(
            kakao_sender_key=kakao_sender_key,
            template_name="주문 접수 안내",
            template_content="#{name}님, 주문 #{orderNo}이 접수되었습니다.",
            template_message_type="BA",
            template_emphasize_type="NONE",
            category_code="001001",
            message_purpose="order_delivery",
            legal_basis="transaction",
            benefit_origin="none",
            expiry_type="none",
        )
    except SendgoError as exc:
        # POLICY_VALIDATION_FAILED 면 errors["reasons"] 에 한국어 사유가 담긴다
        raise HTTPException(status_code=422, detail=exc.errors) from exc

    code = created["data"]["template"]["templateCode"]
    sendgo.notice_templates.request_inspection(code)

    return {"templateCode": code, "inspectionStatus": "REQ"}


@router.post("/senders")
async def register_sender(alias: str, phone: str, csu: UploadFile, sendgo: SendgoDep):
    """발신번호 등록 신청. 접수만 되고(PENDING) 운영자 승인 후 쓸 수 있다."""
    return sendgo.sender_registration.create(
        sender_alias=alias,
        sender_number_type="team_main",
        phone_e164=phone,
        files={"csuCertificate": (csu.filename, csu.file, csu.content_type)},
    )
```

검수 결과는 비동기입니다. `BackgroundTasks` 나 별도 스케줄러에서
`notice_templates.sync(code)` 를 돌려 `inspectionStatus` 가 `APR` 이 되는지
확인하세요 — 요청 핸들러 안에서 기다리면 안 됩니다.

전체 파라미터는 [sendgo-python README](https://github.com/send-go/python) 를 참고하세요.

---

## 변경 사항

### 1.3.0 (2026-09-11)

- **관리 API 노출** — 코어 1.3.0 의 `kakao_senders` · `notice_templates` ·
  `brand_templates` · `sender_registration` · `message_templates` 를
  `SendgoDep` 으로 주입받은 클라이언트에서 그대로 쓸 수 있습니다.
  콘솔에서만 되던 채널 등록, 알림톡 템플릿 검수 요청, 발신번호 심사 접수를
  라우트에서 처리합니다. `UploadFile` 을 그대로 서류로 넘길 수 있습니다.
- `sendgo-python` 을 `>=1.3` 으로 올렸습니다.
- **이벤트 웹훅** 추가 — 발신번호 승인, 알림톡 검수 결과, 채널 차단,
  브랜드메시지 타겟팅 결과를 구독해 받습니다. 서명은 받은 원본 바이트로
  검증합니다(SDK 에 검증 헬퍼 포함).
- **카카오 이미지 업로드** 추가 — 브랜드메시지 템플릿의 `imageUrl` 은 카카오가
  호스팅하는 URL 이어야 하는데, 그 URL 을 얻는 길이 콘솔에만 있었습니다.
- **수신거부(080) 조회** 추가 — 자기 DB 의 수신 상태를 맞출 수 있습니다.

### 1.2.1 (2026-08-14)

- 레지스트리 목록에 노출되는 패키지 설명에서 친구톡을 브랜드메시지로 교체했습니다.
  npm/PyPI/Packagist/Maven/NuGet/RubyGems 검색 결과에 그대로 찍히는 문자열이라
  종료된 채널을 계속 홍보하고 있었습니다.
- 검색 키워드에 `brand-message` 를 추가했습니다 (`friendtalk` 은 유입 검색어라 유지).

### 1.2.0 (2026-08-14)

- **친구톡 Deprecated 표기** — 친구톡은 카카오 정책에 따라 2025-12-31 종료되었고,
  2026-01-01 부터 발송 요청이 브랜드메시지(자유형)로 자동 대체 발송됩니다.
  관련 API 에 각 언어의 표준 deprecation 표기를 달았습니다.
- 자유 본문 타입(`FT`/`FI`/`FW`)의 개별 발송 경로는 아직 친구톡 API 뿐이라는 점을
  문서에 명시했습니다 — 브랜드메시지 API 는 그 조합에 `NOT_A_BRAND_MESSAGE` 를 반환합니다.
- 브랜드메시지 전환 안내와 메시지 타입 1:1 대응표를 README 에 추가했습니다.
- 짧은 URL 지원 (1.1.0 릴리스 누락분 포함).

### 1.1.0 (2026-08-11)

- 브랜드메시지·짧은 URL 접근 방법 문서화 (코어를 그대로 노출)

## 라이선스

MIT License © 2026 [Sendgo](https://sendgo.io)

---

*키워드: 카카오 알림톡 FastAPI, 카카오 친구톡 FastAPI, SMS 발송 FastAPI, 알림톡 FastAPI 패키지, FastAPI 카카오 API 연동, FastAPI 의존성 주입, Sendgo FastAPI SDK*

## 계정 API (1.5.0)

코어 1.5.0의 계정·조직·API 키·허용 IP 관리 12개 API를 사용할 수 있습니다.
발송용 키 없이 에이전트 토큰만으로 구성할 수 있습니다.

발송용 `accessKey`/`secretKey`가 없는 단계에서 사용하는 **별도 계정 클라이언트**입니다.
콘솔에서 발급받은 에이전트 토큰(`SENDGO_AGENT_TOKEN`)으로 `/api/v2/account`를 호출합니다.
계정 조회에는 `account:read`, 키·허용 IP 변경에는 `keys:write` 권한이 필요합니다.
토큰 만료나 권한 부족(401/403)은 그대로 예외로 반환하며 자동 갱신·재시도하지 않습니다.

조직 선택은 서버에 저장되는 **사용자 계정의 현재 조직**을 바꿉니다. 같은 사용자로
여러 조직의 설정을 동시에 변경하지 마세요. 개인 계정으로 돌아가려면 조직 ID에
`null`(Python `None`, Ruby `nil`, Go `nil`) 또는 `personal`을 전달합니다.
키 발급 응답의 `data.apiKey.secretKey`는 한 번만 반환되므로 서버의 비밀 저장소에 보관하세요.
허용 IP가 하나라도 등록되면 목록 밖의 IP는 차단됩니다.
에이전트 토큰과 키는 브라우저·모바일 앱에 포함하거나 응답·로그에 출력하지 않습니다.

```python
from sendgo_fastapi import AccountDep
# SENDGO_AGENT_TOKEN 환경변수를 설정합니다.
@app.get('/internal/sendgo-status')
def status(account: AccountDep):
    return account.me()
```

## 템플릿 폴더 (1.5.0)

기업 계정의 발송용 API 키와 `apiVersion=v2` 설정으로 사용하는 서버 전용 API입니다.
폴더는 알림톡·브랜드메시지가 공유하며, 목록의 `templateType`은 `notice` 또는 `brand`입니다.
목록은 `data.folders` 트리와 `total`, `uncategorised` 개수를 반환합니다.
`templateCount`는 하위 폴더를 제외한 해당 폴더의 템플릿 수입니다.

- 생성: `name`, 선택 `parentUuid`. 최대 5단계이며 같은 부모 아래 이름 중복은 409입니다.
- 이동: 동일 발신프로필의 `templateCodes` 1~100개. `folderUuid`는 필수이며 `null`이면 미분류로 이동합니다.
- 템플릿 목록: `folderUuid=none`은 미분류, UUID는 해당 폴더, 생략은 전체입니다.
- 템플릿 등록: 선택 필드 `folderUuid`로 폴더를 지정합니다. 기존 템플릿 수정 API 대신 폴더 이동 API를 사용하세요.

승인되지 않은 키의 `403 ACCESS_KEY_NOT_APPROVED`는 토큰 재발급·재시도 없이 반환합니다.
계정 API의 `autoApprove`는 서버 설정의 실제 승인 정책을 나타냅니다.

```python
from sendgo_fastapi import SendgoDep

@app.get("/template-folders")
def folders(sendgo: SendgoDep):
    return sendgo.template_folders.list(template_type="notice")
```

코어 1.5.0 이상이 필요합니다. 전체 메서드는 [코어 문서](https://github.com/send-go/python#템플릿-폴더-150)를 참고하세요.
