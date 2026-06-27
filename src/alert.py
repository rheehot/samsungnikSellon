"""
알림 발송 모듈
SMTP를 사용하여 이메일 알림을 발송합니다.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date, timedelta
from typing import List, Optional

logger = logging.getLogger(__name__)


class AlertSender:
    """이메일 알림 발송 클래스"""

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str
    ):
        """
        SMTP 클라이언트 초기화

        Args:
            smtp_server: SMTP 서버 주소
            smtp_port: SMTP 포트
            sender_email: 발신자 이메일
            sender_password: 발신자 비밀번호 (앱 비밀번호)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """
        이메일 발송

        Args:
            recipients: 수신자 이메일 목록
            subject: 이메일 제목
            body: 이메일 본문
            is_html: HTML 형식 여부

        Returns:
            발송 성공 여부
        """
        if not recipients or not recipients[0]:
            logger.warning("수신자가 없어 이메일 발송 skipped")
            return False

        try:
            # 메시지 생성
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(recipients)

            # 본문 추가
            mime_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, mime_type))

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS 보안 연결
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())

            logger.info(f"이메일 발송 성공: {recipients}")
            return True

        except Exception as e:
            logger.error(f"이메일 발송 실패: {e}")
            return False

    def send_stock_alert(
        self,
        recipients: List[str],
        skhynix_ath_price: float,
        skhynix_ath_date: date,
        samsung_current: float,
        samsung_ath_price: float,
        days_passed: int
    ) -> bool:
        """
        주가 알림 이메일 발송

        Args:
            recipients: 수신자 이메일 목록
            skhynix_ath_price: SK하이닉스 전고점 가격
            skhynix_ath_date: SK하이닉스 전고점 일자
            samsung_current: 삼성전자 현재가
            samsung_ath_price: 삼성전자 전고점 가격
            days_passed: 경과 일수

        Returns:
            발송 성공 여부
        """
        subject = f"🚨 매도 권고 알림: 삼성전자 전고점 미갱신 {days_passed}일 경과"

        # 텍스트 버전
        text_body = f"""
삼성전자/SK하이닉스 주가 모니터링 알림

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 현황

SK하이닉스:
  • 전고점: {skhynix_ath_price:,.0f}원 ({skhynix_ath_date})
  • 상태: 전고점 돌파

삼성전자:
  • 현재가: {samsung_current:,.0f}원
  • 전고점: {samsung_ath_price:,.0f}원
  • 상태: 전고점 미갱신

⏱️  경과 일수: {days_passed}일

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 요약

SK하이닉스가 {skhynix_ath_date}에 전고점({skhynix_ath_price:,.0f}원)을 돌파했습니다.
하지만 {days_passed}일이 지났음에도 삼성전자는 전고점({samsung_ath_price:,.0f}원)을 갱신하지 못했습니다.

삼성전자 현재가: {samsung_current:,.0f}원
전고점 대비: {((samsung_current / samsung_ath_price) - 1) * 100:.1f}%

⚠️  이메일은 정보 제공 목적이며, 투자의 책임은 본인에게 있습니다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

발송 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

        # HTML 버전
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.6; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px; }}
        .info-box {{ background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #667eea; }}
        .alert {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }}
        .price {{ font-size: 24px; font-weight: bold; color: #333; }}
        .label {{ color: #666; font-size: 14px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 매도 권고 알림</h1>
            <p>삼성전자 전고점 미갱신 {days_passed}일 경과</p>
        </div>

        <div class="content">
            <div class="info-box">
                <div class="label">SK하이닉스</div>
                <div class="price">{skhynix_ath_price:,.0f}원</div>
                <div class="label">전고점 ({skhynix_ath_date})</div>
            </div>

            <div class="alert">
                <div class="label">삼성전자</div>
                <div class="price">{samsung_current:,.0f}원</div>
                <div class="label">전고점: {samsung_ath_price:,.0f}원</div>
                <div class="label">전고점 대비: {((samsung_current / samsung_ath_price) - 1) * 100:.1f}%</div>
            </div>

            <div class="info-box">
                <div class="label">⏱️ 경과 일수</div>
                <div class="price">{days_passed}일</div>
            </div>

            <div class="alert">
                <strong>📌 요약</strong><br>
                SK하이닉스가 {skhynix_ath_date}에 전고점을 돌파했습니다.<br>
                하지만 <strong>{days_passed}일</strong>이 지났음에도 삼성전자는 전고점을 갱신하지 못했습니다.<br><br>
                ⚠️ 이메일은 정보 제공 목적이며, 투자의 책임은 본인에게 있습니다.
            </div>
        </div>

        <div class="footer">
            발송 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}<br>
            samungnikSellon - 주가 모니터링 알림 시스템
        </div>
    </div>
</body>
</html>
"""

        return self.send_email(recipients, subject, text_body, is_html=False)

    def send_daily_status(
        self,
        recipients: List[str],
        samsung_ath_price: float,
        samsung_yesterday_price: float,
        skhynix_ath_price: float,
        skhynix_yesterday_price: float,
        skhynix_ath_date: Optional[date] = None,
        days_since_sk_ath: Optional[int] = None,
        indices: Optional[dict] = None
    ) -> bool:
        """
        매일 상태 이메일 발송

        Args:
            recipients: 수신자 이메일 목록
            samsung_ath_price: 삼성전자 전고점
            samsung_yesterday_price: 삼성전자 어제 종가
            skhynix_ath_price: SK하이닉스 전고점
            skhynix_yesterday_price: SK하이닉스 어제 종가
            skhynix_ath_date: SK하이닉스 전고점 일자 (없으면 None)
            days_since_sk_ath: SK하이닉스 전고점 이후 경과 일수 (없으면 None)
            indices: 지수 데이터 딕셔너리 (kospi, kosdaq, nasdaq, sp500, dow)

        Returns:
            발송 성공 여부
        """
        # 경과 일수에 따라 다른 제목
        if days_since_sk_ath and days_since_sk_ath >= 30:
            subject = f"🚨 [주의] 삼성전자 전고점 미갱신 {days_since_sk_ath}일 경과"
        else:
            subject = f"📊 글로벌 지수 포함 일일 주가 현황 ({date.today().strftime('%Y-%m-%d')})"

        # 어제 날짜
        yesterday = date.today() - timedelta(days=1)

        # 텍스트 버전
        text_body = f"""
🌏 글로벌 지수 & 주식 일일 보고

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 어제 종가 기준 ({yesterday})

【한국 지수】

코스피 (KOSPI):
  • 어제 종가: {indices.get('kospi', {}).get('yesterday', 0):,.2f}pt
  • 전고점: {indices.get('kospi', {}).get('ath', 0):,.2f}pt

코스닥 (KOSDAQ):
  • 어제 종가: {indices.get('kosdaq', {}).get('yesterday', 0):,.2f}pt
  • 전고점: {indices.get('kosdaq', {}).get('ath', 0):,.2f}pt

【미국 지수】

나스닥 (NASDAQ):
  • 어제 종가: {indices.get('nasdaq', {}).get('yesterday', 0):,.2f}pt
  • 전고점: {indices.get('nasdaq', {}).get('ath', 0):,.2f}pt

S&P 500:
  • 어제 종가: {indices.get('sp500', {}).get('yesterday', 0):,.2f}pt
  • 전고점: {indices.get('sp500', {}).get('ath', 0):,.2f}pt

다우 (DOW):
  • 어제 종가: {indices.get('dow', {}).get('yesterday', 0):,.2f}pt
  • 전고점: {indices.get('dow', {}).get('ath', 0):,.2f}pt

【한국 주식】

삼성전자:
  • 어제 종가: {samsung_yesterday_price:,.0f}원
  • 전고점: {samsung_ath_price:,.0f}원
  • 전고점 대비: {((samsung_yesterday_price / samsung_ath_price) - 1) * 100:.1f}%

SK하이닉스:
  • 어제 종가: {skhynix_yesterday_price:,.0f}원
  • 전고점: {skhynix_ath_price:,.0f}원
  • 전고점 대비: {((skhynix_yesterday_price / skhynix_ath_price) - 1) * 100:.1f}%

"""

        # SK하이닉스 전고점 정보가 있으면 추가
        if skhynix_ath_date and days_since_sk_ath is not None:
            text_body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 SK하이닉스 전고점 이후 현황

SK하이닉스 전고점 돌파일: {skhynix_ath_date}
경과 일수: {days_since_sk_ath}일

삼성전자 전고점 갱신 여부: {'✅ 갱신됨' if days_since_sk_ath < 0 else '❌ 미갱신'}
"""

            # 30일 이상 경과 시 경고 메시지
            if days_since_sk_ath >= 30:
                text_body += f"""
⚠️  {days_since_sk_ath}일이 지났음에도 삼성전자는 전고점을 갱신하지 못했습니다.
SK하이닉스 전고점({skhynix_ath_price:,.0f}원) 돌파 후 삼성전자가 따라가지 못하는 상황이 {days_since_sk_ath}일간 지속되었습니다.
"""

        text_body += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  이메일은 정보 제공 목적이며, 투자의 책임은 본인에게 있습니다.

발송 시각: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """

samungnikSellon - 주가 모니터링 알림 시스템
"""

        return self.send_email(recipients, subject, text_body, is_html=False)


def test_email():
    """이메일 발송 테스트"""
    # 테스트용 설정 (실제 사용 시 config에서 로드)
    sender = AlertSender(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        sender_email="test@gmail.com",
        sender_password="app-password"
    )

    # 테스트 발송
    sender.send_email(
        recipients=["test@example.com"],
        subject="테스트 이메일",
        body="이것은 테스트 이메일입니다."
    )


if __name__ == "__main__":
    test_email()
