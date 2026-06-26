# 주가 모니터링 알림 시스템 - 기획서

## 1. 프로젝트 개요

### 1.1 프로젝트명
**samsungnikSellon** (삼성전자-SK하이닉스 주가 모니터링 및 매도 알림 시스템)

### 1.2 프로젝트 목적
삼성전자와 SK하이닉스의 주가를 모니터링하고, **SK하이닉스 전고점 돌파 후 삼성전자가 1개월 이상 전고점을 갱신하지 못할 때** 이메일 알림을 발송하여 투자자에게 매도 신호를 제공합니다.

### 1.3 배경
- 반도체 동반 상승 패턴에서 SK하이닉스가 먼저 전고점을 돌파한 후 삼성전자가 따라가는 패턴 관찰
- SK하이닉스 선반영 후 삼성전자가 1개월 이상 따라가지 못하면 시장 하락 가능성 있다는 가설
- 자동화된 모니터링 시스템으로 투자 결정 지원

---

## 2. 요구사항 상세

### 2.1 핵심 요구사항
| 요구사항 | 상세 설명 |
|----------|----------|
| **R1** | 삼성전자(005930.KS)와 SK하이닉스(000660.KS)의 주가를 매일 모니터링 |
| **R2** | SK하이닉스의 전고점(52주 신고가)을 추적 |
| **R3** | SK하이닉스 전고점 돌파 시점 기록 |
| **R4** | 해당 시점 이후 삼성전자의 전고점 갱신 여부 감시 |
| **R5** | 1개월(30일) 이상 삼성전자 전고점 미갱신 시 이메일 알림 발송 |
| **R6** | 수신자 이메일 주소 설정 가능 |

### 2.2 기능 요구사항
| 요구사항 | 상세 설명 |
|----------|----------|
| **F1** | 무료 주가 API(Yahoo Finance 등) 연동 |
| **F2** | 주가 데이터 저장 및 이력 관리 |
| **F3** | 전고점 추적 및 갱신 감지 |
| **F4** | 조건 만료 시 이메일 발송 |
| **F5** | 주기적 실행 스케줄링 (cron/job scheduler) |

### 2.3 비기능 요구사항
| 요구사항 | 상세 설명 |
|----------|----------|
| **N1** | 빠른 MVP 개발 (1-2일 내 실행 가능한 버전) |
| **N2** | API 장애 시 재시도 로직 |
| **N3** | 실행 로그 기록 |
| **N4** | 설정값 외부화 (종목 코드, 기간, 이메일 등) |

---

## 3. 핵심 기능 정의

### 3.1 주가 수집 기능
- Yahoo Finance API를 통해 종가 데이터 수집
- 일일 1회 수집 (장 마감 후 또는 매일 정시)
- 수집 실패 시 최대 3회 재시도

### 3.2 전고점 추적 기능
- 각 종목의 52주 신고가 추적
- 전고점 갱신 시 DB에 기록
- SK하이닉스 전고점 갱신 시점을 특별히 기록

### 3.3 조건 감시 기능
- SK하이닉스 전고점 갱신 일자 기준
- 삼성전자 전고점 갱신 여부 매일 확인
- 30일 경과 시점까지 삼성전자 미갱신 시 트리거

### 3.4 알림 발송 기능
- 조건 만족 시 SMTP를 통한 이메일 발송
- 이메일 내용: 현재 주가, 전고점, 경과 일수, 간단 설명
- 중복 알림 방지 (이미 발송된 경우 재발송 안 함)

---

## 4. 기술 스택 (MVP)

### 4.1 개발 언어 및 런타임
- **Python 3.11+**: 데이터 처리, API 연동, 이메일 발송 용이성

### 4.2 주요 라이브러리
```python
# 주가 데이터
yfinance >= 0.2.28  # Yahoo Finance API

# 데이터 저장
sqlite3 (내장)     # 경량 DB

# 이메일 발송
smtplib (표준)     # SMTP 클라이언트
email.mime (표준)  # 이메일 포맷

# 스케줄링
schedule >= 1.2.0  # 임의 시간 실행
# 또는 cron (Linux/macOS)
```

### 4.3 배포 환경
- **로컬 실행**: 사용자 PC에서 주기적 실행
- **선택적 클라우드**: Render/Railway 등 무료 티어 활용 가능

---

## 5. 아키텍처

### 5.1 시스템 구조도
```
┌─────────────────────────────────────────────────────────────┐
│                     Scheduler (cron/schedule)                │
│                         매일 정시 실행                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Main Controller                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  1. 주가 수집 (yfinance)                                 │ │
│  │  2. 전고점 갱신 체크                                      │ │
│  │  3. 조건 만족 여부 확인                                    │ │
│  │  4. 필요 시 알림 발송                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────┬──────────────────────────────┬─────────────────┘
             │                              │
             ▼                              ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│   SQLite Database    │      │      SMTP Email Service      │
│  - 주가 이력         │      │  - 설정된 수신자에게 발송      │
│  - 전고점 기록      │      └──────────────────────────────┘
│  - 알림 발송 기록  │
└──────────────────────┘
```

### 5.2 데이터베이스 스키마
```sql
-- 주가 데이터 테이블
CREATE TABLE stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,        -- 종목 코드 (005930.KS)
    date DATE NOT NULL,           -- 날짜
    close_price REAL NOT NULL,    -- 종가
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- 전고점 기록 테이블
CREATE TABLE all_time_highs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,         -- 종목 코드
    price REAL NOT NULL,          -- 전고점 가격
    date DATE NOT NULL,           -- 발생일
    is_active BOOLEAN DEFAULT 1,  -- 현재 유효한 전고점 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 발송 기록 테이블
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at DATE NOT NULL,   -- 트리거 발생일 (SK하이닉스 전고점일)
    alert_sent_at TIMESTAMP,      -- 알림 발송 시각
    samsung_status TEXT,           -- 삼성전자 상태 (ATH_REACHED/NOT_REACHED)
    email_sent BOOLEAN DEFAULT 0, -- 이메일 발송 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. 알고리즘

### 6.1 메인 로직
```python
def main():
    # 1. 주가 수집
    samsung_price = get_stock_price("005930.KS")  # 삼성전자
    skhynix_price = get_stock_price("000660.KS")  # SK하이닉스
    
    # 2. DB 저장
    save_price("005930.KS", samsung_price)
    save_price("000660.KS", skhynix_price)
    
    # 3. 전고점 갱신 체크
    sk_new_ath = check_all_time_high("000660.KS", skhynix_price)
    samsung_new_ath = check_all_time_high("005930.KS", samsung_price)
    
    # 4. SK하이닉스 전고점 돌파 시 새로운 감시 시작
    if sk_new_ath:
        create_new_alert_trigger(s_new_ath.date)
    
    # 5. 활성 트리거 확인
    active_trigger = get_active_alert_trigger()
    if active_trigger:
        days_passed = (today - active_trigger.triggered_at).days
        
        # 6. 삼성전자 전고점 갱신 여부 확인
        samsung_ath_reached = check_samsung_ath_since(trigger_date)
        
        # 7. 30일 경과 및 삼성전자 미갱신 시 알림
        if days_passed >= 30 and not samsung_ath_reached:
            if not alert_trigger.email_sent:
                send_alert_email(
                    subject="🚨 매도 권고 알림: 삼성전자 전고점 미갱신 30일 경과",
                    body=f"""
SK하이닉스 전고점: {sk_ath_price} ({trigger_date})
삼성전자 현재가: {samsung_price}
삼성전자 전고점: {samsung_ath_price}
경과 일수: {days_passed}일

삼성전자가 {days_passed}일간 전고점을 갱신하지 못했습니다.
매도를 고려해 보시기 바랍니다.
                    """
                )
                mark_email_sent(active_trigger.id)
        
        # 삼성전자 전고점 갱신 시 트리거 종료
        elif samsung_ath_reached:
            deactivate_trigger(active_trigger.id)
```

---

## 7. 개발 범위 (MVP)

### 7.1 Phase 1: 핵심 기능 (1-2일)
- [ ] Yahoo Finance API 연동
- [ ] SQLite DB 구축
- [ ] 주가 수집 및 저장
- [ ] 전고점 추적 로직
- [ ] 조건 감시 로직
- [ ] 이메일 발송 기능

### 7.2 Phase 2: 안정화 (추가 1일)
- [ ] 에러 핸들링 및 재시도
- [ ] 로그 기능
- [ ] 설정 파일 외부화
- [ ] 테스트 및 검증

### 7.3 Phase 3: 배포 (선택)
- [ ] cron 스케줄 등록
- [ ] 또는 클라우드 배포
- [ ] 모니터링 대시보드 (선택)

---

## 8. 설정 항목

```yaml
# config.yaml
symbols:
  samsung: "005930.KS"
  skhynix: "000660.KS"

monitoring:
  check_days: 30          # 알림 발송 기준 일수
  check_hour: 16          # 매일 확인 시각 (KST)

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender: "your-email@gmail.com"
  password: "app-password"  # Gmail 앱 비밀번호
  recipients:
    - "investor@example.com"

database:
  path: "./stock_monitor.db"
```

---

## 9. 향후 확장 가능성

### 9.1 기능 확장
- 추가 종목 모니터링
- 복잡한 조건 설정 (이평선, RSI 등)
- 복수 알림 채널 (Slack, Telegram, 카카오톡)
- 웹 대시보드 제공

### 9.2 아키텍처 확장
- 클라우드 배포 (AWS Lambda + CloudWatch)
- 웹 API 추가
- DB 확장 (PostgreSQL)

---

## 10. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| Yahoo Finance API 장애 | 주가 수집 불가 | Alpha Vantage 백엔드, 재시도 로직 |
| SMTP 발송 실패 | 알림 미수신 | 로그 기록, 수동 확인 프로세스 |
| 잘못된 알림 발송 | 오해 가능 | 테스트 thorough, "정보 제공" 면책 |

---

## 11. 용어 정리

| 용어 | 설명 |
|------|------|
| **ATH (All-Time High)** | 전고점, 역대 최고가 |
| **52주 신고가** | 지난 52주(1년)간 최고가 |
| **전고점 갱신** | 기존 ATH를 높은 가격으로 갱신 |
| **트리거** | SK하이닉스 전고점 돌파로 시작하는 감시 기간 |

---

**문서 버전**: 1.0  
**작성일**: 2026-06-26  
**상태**: Draft
