# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**samsungnikSellon**은 삼성전자와 SK하이닉스의 주가를 모니터링하고, SK하이닉스가 전고점을 돌파한 후 삼성전자가 30일 이상 전고점을 갱신하지 못할 때 이메일로 매도 알림을 발송하는 Python 백그라운드 서비스입니다.

## 개발 환경

- **Python**: 3.11+
- **의존성 관리**: `pip install -r requirements.txt`
- **설정 파일**: `config.yaml`

## 일반적으로 사용하는 명령어

### 실행
```bash
# 일일 모니터링 실행
python src/main.py

# 특정 날짜 실행 (테스트용)
python src/main.py --date 2026-06-26

# 현재 상태 조회
python src/main.py --status
```

### 테스트
```bash
# API 테스트
python src/stock_api.py

# 데이터베이스 초기화 후 상태 확인
rm data/stock_monitor.db && python src/main.py --status
```

### 스케줄링 (cron 등록)
```bash
# crontab 편기
crontab -e

# 매일 오후 4시 실행
0 16 * * * cd /Users/jong-woorhee/study/vibecoding/samsungnikSellon && python3 src/main.py >> logs/cron.log 2>&1
```

## 코드 아키텍처

### 핵심 모듈 구조

```
src/
├── main.py          # 메인 컨트롤러 (StockMonitor 클래스)
├── database.py      # SQLite DB 관리 (Database 클래스)
├── stock_api.py     # Yahoo Finance API 연동 (StockAPI 클래스)
└── alert.py         # SMTP 이메일 발송 (AlertSender 클래스)
```

### 실행 흐름

1. **StockMonitor.run()** 호출
2. 주가 수집 (StockAPI → Database 저장)
3. 전고점 갱신 체크
4. SK하이닉스 전고점 돌파 시 alert_history 테이블에 트리거 생성
5. 활성 트리거 확인:
   - 삼성전자 전고점 갱신 시 트리거 완료
   - 30일 경과 시 이메일 발송

### 데이터베이스 스키마

```sql
-- 주가 데이터
stock_prices (id, symbol, date, close_price, created_at)

-- 전고점 기록 (is_active=1인 행이 현재 전고점)
all_time_highs (id, symbol, price, date, is_active, created_at)

-- 알림 트리거 (samsung_status='PENDING'인 활성 행)
alert_history (id, triggered_at, alert_sent_at, samsung_status, email_sent, created_at)
```

## 개발 시 유의사항

### 설정 관련
- `config.yaml`에 이메일 비밀번호 등 민감 정보가 포함되어 있으므로 커밋 시 주의
- 실제 배포 시 `.env` 파일로 이관 고려

### API 관련
- Yahoo Finance API는 무료이지만 사용량 제한이 있을 수 있음
- 재시도 로직이 구현되어 있으나, 장애 시 로그 확인 필요

### 데이터베이스
- SQLite는 단일 파일로 동작하며 `data/` 디렉토리에 저장됨
- DB 파일 삭제 후 재실행 시 자동 초기화됨

## 주요 기능 확장 포인트

### 추가 종목 모니터링
- `config.yaml`의 `symbols` 섹션에 종목 추가
- `main.py`의 `_collect_price()`, `_check_all_time_high()` 로직 확장

### 복잡한 조건 추가
- `database.py`에 새로운 조건 저장 테이블 추가
- `main.py`의 `_process_active_triggers()` 로직 확장

### 알림 채널 확장
- `alert.py`에 Slack, Telegram 등 발송 클래스 추가
- `AlertSender` 클래스 인터페이스 참고
