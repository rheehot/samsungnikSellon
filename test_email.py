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

# 테스트용 주가 데이터 (52주 신고가 기준 실제 시세)
samsung_ath_price = 374500  # 삼성전자 52주 신고가
samsung_yesterday_price = 339500  # 삼성전자 현재가
skhynix_ath_price = 2987000  # SK하이닉스 52주 신고가
skhynix_yesterday_price = 2673000  # SK하이닉스 현재가

# 테스트용 지수 데이터 (52주 신고가 기준 실제 지수)
indices_data = {
    'kospi': {'yesterday': 8411.21, 'ath': 9385.59},     # 코스피 52주 신고가
    'kosdaq': {'yesterday': 851.37, 'ath': 1229.42},      # 코스닥 52주 신고가
    'nasdaq': {'yesterday': 25297.62, 'ath': 27190.21},   # 나스닥 52주 신고가
    'sp500': {'yesterday': 7354.02, 'ath': 7620.90},      # S&P500 52주 신고가
    'dow': {'yesterday': 51876.11, 'ath': 52655.66}       # 다우 52주 신고가
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
