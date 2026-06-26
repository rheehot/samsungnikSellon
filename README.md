# 📈 samungnikSellon

**삼성전자-SK하이닉스 주가 모니터링 및 매도 알림 시스템**

매일 아침 삼성전자와 SK하이닉스의 주가 현황을 이메일로 받아보세요. SK하이닉스가 전고점을 돌파한 후 삼성전자가 30일 이상 전고점을 갱신하지 못할 때 특별 알림이 발송됩니다.

## 🎯 기능

- ✅ 삼성전자/SK하이닉스 일일 주가 자동 수집 (Yahoo Finance API)
- ✅ 전고점(52주 신고가) 자동 추적
- ✅ **매일 아침 8시 자동 상태 이메일 발송**
- ✅ SK하이닉스 전고점 돌파 후 삼성전자 전고점 갱신 감시
- ✅ 30일 경과 시 제목에 [주의] 표시된 알림 발송
- ✅ SQLite DB로 데이터 이력 관리

## 📋 요구사항

- Python 3.11 이상
- Gmail 계정 (이메일 발송용)

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 설정 파일 수정

`config.yaml`을 열어 이메일 설정을 완성하세요:

```yaml
email:
  enabled: true
  sender: "your-email@gmail.com"      # 본인 Gmail 주소
  password: "app-password"             # Gmail 앱 비밀번호
  recipients:
    - "your-email@example.com"         # 수신자 이메일
```

**Gmail 앱 비밀번호 발급 방법:**
1. [Google 계정 보안](https://myaccount.google.com/security) 접속
2. 2단계 인증 활성화
3. "앱 비밀번호" 생성 및 입력

### 3. 실행

```bash
# 일일 모니터링 실행
python src/main.py

# 특정 날짜 실행 (테스트용)
python src/main.py --date 2026-06-26

# 현재 상태 조회
python src/main.py --status
```

### 4. 자동 스케줄 등록 (macOS/Linux)

**cron 등록 (매일 아침 8시 실행):**

```bash
# crontab 편집
crontab -e

# 매일 아침 8시에 실행
0 8 * * * cd /Users/jong-woorhee/study/vibecoding/samsungnikSellon && source venv/bin/activate && PYTHONPATH=. python src/main.py >> logs/cron.log 2>&1
```

**스케줄 등록 자동화 스크립트 (선택):**

```bash
# install_cron.sh 스크립트 실행
bash scripts/install_cron.sh
```

### 5. Render 클라우드 무료 배포 (⭐ 추천)

**로컬 PC 없이 클라우드에서 24/7 자동 실행!**

```bash
# 1. GitHub 설정 스크립트 실행
bash scripts/setup_github.sh

# 2. Render 대시보드에서 배포
# https://dashboard.render.com
# - "New +" 클릭 → "Blueprint" 선택
# - GitHub 연결 → 이 저장소 선택
# - 환경 변수 입력:
#   EMAIL_SENDER=your-email@gmail.com
#   EMAIL_PASSWORD=your-app-password
#   EMAIL_RECIPIENTS=rheehot@gmail.com
# - "Deploy Blueprint" 클릭
```

**환경 변수 (Render 대시보드에서 설정):**
```
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENTS=rheehot@gmail.com
```

✅ **완료되면 매일 아침 8시에 자동으로 이메일 발송!**

## 📁 프로젝트 구조

```
samsungnikSellon/
├── src/
│   ├── __init__.py
│   ├── main.py          # 메인 컨트롤러
│   ├── database.py      # 데이터베이스 관리
│   ├── stock_api.py     # 주가 API 연동
│   └── alert.py         # 이메일 알림 발송
├── data/                 # SQLite DB 저장소
├── logs/                 # 실행 로그
├── docs/                 # 기획서, 설계서
├── config.yaml           # 설정 파일
├── requirements.txt      # 의존성
└── README.md
```

## ⚙️ 설정

### config.yaml

```yaml
# 종목 코드
symbols:
  samsung: "005930.KS"
  skhynix: "000660.KS"

# 모니터링 설정
monitoring:
  check_days: 30          # 알림 기준 일수
  check_hour: 8            # 실행 시각 (매일 아침 8시)

# 이메일 설정
email:
  enabled: true
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender: ""
  password: ""
  recipients: [""]

# 데이터베이스
database:
  path: "./data/stock_monitor.db"
```

## 🧪 테스트

```bash
# API 테스트
python src/stock_api.py

# 이메일 발송 테스트
python src/alert.py
```

## 📊 데이터베이스 스키마

```sql
-- 주가 데이터
stock_prices (symbol, date, close_price)

-- 전고점 기록
all_time_highs (symbol, price, date, is_active)

-- 알림 발송 기록
alert_history (triggered_at, alert_sent_at, samsung_status, email_sent)
```

## ⚠️ 주의사항

- 이메일은 정보 제공 목적이며 투자의 책임은 본인에게 있습니다.
- Yahoo Finance API는 무료이지만 사용량 제한이 있을 수 있습니다.
- 주말/공휴일에는 데이터가 없을 수 있습니다.

## 📝 라이선스

MIT License

## 🤝 기여

Issue 및 PR 환영합니다!

---

**문서 버전**: 1.0  
**마지막 수정**: 2026-06-26
