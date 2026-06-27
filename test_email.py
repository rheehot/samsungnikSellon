"""
테스트용 이메일 발송 스크립트
"""

import yaml
from src.alert import AlertSender
from datetime import date, timedelta

# 설정 로드
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# AlertSender 초기화
alert_sender = AlertSender(
    smtp_server=config["email"]["smtp_server"],
    smtp_port=config["email"]["smtp_port"],
    sender_email=config["email"]["sender"],
    sender_password=config["email"]["password"]
)

# 테스트용 주가 데이터 (실제 데이터와 유사하게)
samsung_ath_price = 95000  # 삼성전자 전고점 예시
samsung_yesterday_price = 87000  # 삼성전자 어제 종가 예시
skhynix_ath_price = 210000  # SK하이닉스 전고점 예시
skhynix_yesterday_price = 195000  # SK하이닉스 어제 종가 예시

# 테스트용 지수 데이터 (실제 지수와 유사하게)
indices_data = {
    'kospi': {'yesterday': 2750.5, 'ath': 2850.0},
    'kosdaq': {'yesterday': 890.2, 'ath': 950.0},
    'nasdaq': {'yesterday': 17500.0, 'ath': 18500.0},
    'sp500': {'yesterday': 5450.0, 'ath': 5650.0},
    'dow': {'yesterday': 39500.0, 'ath': 41000.0}
}

# 테스트용 SK하이닉스 전고점 일자 (최근)
skhynix_ath_date = date.today() - timedelta(days=15)
days_since_sk_ath = 15

# 이메일 발송
print("테스트 이메일 발송 중...")
print("지수 데이터:")
for key, value in indices_data.items():
    print(f"  {key}: {value['yesterday']:,.2f} (전고점: {value['ath']:,.2f})")
print()

success = alert_sender.send_daily_status(
    recipients=config["email"]["recipients"],
    samsung_ath_price=samsung_ath_price,
    samsung_yesterday_price=samsung_yesterday_price,
    skhynix_ath_price=skhynix_ath_price,
    skhynix_yesterday_price=skhynix_yesterday_price,
    skhynix_ath_date=skhynix_ath_date,
    days_since_sk_ath=days_since_sk_ath,
    indices=indices_data
)

if success:
    print("✅ 테스트 이메일 발송 성공!")
    print(f"수신자: {config['email']['recipients']}")
    print("포함된 내용:")
    print("  - 한국 지수: 코스피, 코스닥")
    print("  - 미국 지수: 나스닥, S&P 500, 다우")
    print("  - 한국 주식: 삼성전자, SK하이닉스")
else:
    print("❌ 이메일 발송 실패")
