"""
주가 모니터링 시스템 메인 컨트롤러
주가 수집, 전고점 추적, 조건 감시, 알림 발송을 조율합니다.
"""

import logging
import os
import yaml
from datetime import datetime, date, timedelta
from pathlib import Path

from src.database import Database
from src.stock_api import StockAPI
from src.alert import AlertSender
from src.config import load_config, validate_config

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StockMonitor:
    """주가 모니터링 시스템 메인 클래스"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        모니터링 시스템 초기화

        Args:
            config_path: 설정 파일 경로
        """
        self.config = self._load_config(config_path)

        # 데이터베이스 디렉토리 생성
        db_path = Path(self.config["database"]["path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = Database(self.config["database"]["path"])
        self.stock_api = StockAPI(
            retry_attempts=self.config["api"]["retry_attempts"],
            retry_delay=self.config["api"]["retry_delay"]
        )

        # 이메일 발송기 초기화 (설정된 경우)
        if self.config["email"]["enabled"]:
            self.alert_sender = AlertSender(
                smtp_server=self.config["email"]["smtp_server"],
                smtp_port=self.config["email"]["smtp_port"],
                sender_email=self.config["email"]["sender"],
                sender_password=self.config["email"]["password"]
            )
        else:
            self.alert_sender = None
            logger.info("이메일 알림 비활성화")

    def _load_config(self, config_path: str = "config.yaml") -> dict:
        """
        설정 로드 (환경 변수 우선, config.yaml 백업)

        Args:
            config_path: 설정 파일 경로

        Returns:
            설정 딕셔너리
        """
        try:
            config = load_config(config_path)

            # 설정 유효성 검사
            is_valid, error_msg = validate_config(config)
            if not is_valid:
                logger.error(f"설정 오류: {error_msg}")
                logger.error("환경 변수 또는 config.yaml을 설정해주세요.")
                raise ValueError(error_msg)

            logger.info("설정 로드 완료")
            return config

        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            raise

    def run(self, target_date: date = None, send_daily_email: bool = True):
        """
        모니터링 실행

        Args:
            target_date: 대상 날짜 (기본: 오늘)
            send_daily_email: 매일 상태 이메일 발송 여부 (기본: True)
        """
        if target_date is None:
            target_date = date.today()

        logger.info(f"모니터링 시작: {target_date}")

        # 1. 주가 수집
        samsung_price = self._collect_price("samsung", target_date)
        skhynix_price = self._collect_price("skhynix", target_date)

        # 2. 지수 수집
        indices_data = self._collect_indices(target_date)

        # 2.5. 미국 주식 & 환율 수집
        us_stocks_data = self._collect_us_stocks(target_date)
        forex_data = self._collect_forex(target_date)

        if not samsung_price or not skhynix_price:
            logger.warning("주가 수집 실패 but 지수는 성공 - 계속 진행")

        # 3. 전고점 갱신 체크
        sk_new_ath = self._check_all_time_high("skhynix", skhynix_price, target_date)
        samsung_new_ath = self._check_all_time_high("samsung", samsung_price, target_date)

        # 4. SK하이닉스 전고점 돌파 시 새로운 트리거 생성
        if sk_new_ath:
            self.db.create_alert_trigger(target_date)
            logger.info(f"새로운 알림 트리거 생성: {target_date}")

        # 5. 활성 트리거 확인 및 처리
        self._process_active_triggers(samsung_price, target_date)

        # 6. 매일 상태 이메일 발송
        if send_daily_email and self.alert_sender:
            self._send_daily_status(samsung_price, skhynix_price, target_date, indices_data, us_stocks_data, forex_data)

        logger.info("모니터링 완료")

    def _collect_price(self, symbol_key: str, target_date: date) -> float:
        """
        주가 수집

        Args:
            symbol_key: 종목 키 ("samsung" 또는 "skhynix")
            target_date: 대상 날짜

        Returns:
            종가 (실패 시 None)
        """
        symbol = self.config["symbols"][symbol_key]
        logger.info(f"{symbol_key} 주가 수집 시작")

        price = self.stock_api.get_stock_price(symbol)

        if price:
            self.db.save_price(symbol, price, target_date)
            return price
        else:
            logger.error(f"{symbol_key} 주가 수집 실패")
            return None

    def _collect_indices(self, target_date: date) -> dict:
        """
        지수 수집

        Args:
            target_date: 대상 날짜

        Returns:
            지수 데이터 딕셔너리
        """
        indices = {}
        indices_config = self.config.get("indices", {})

        for index_key, symbol in indices_config.items():
            logger.info(f"{index_key} 지수 수집 시작")

            price = self.stock_api.get_stock_price(symbol)

            if price:
                self.db.save_price(symbol, price, target_date)
                ath = self.db.get_all_time_high(symbol)
                indices[index_key] = {
                    "yesterday": price,
                    "ath": ath if ath else price
                }
                logger.info(f"{index_key} 지수: {price:,.2f}")
            else:
                logger.warning(f"{index_key} 지수 수집 실패")
                indices[index_key] = {
                    "yesterday": 0,
                    "ath": 0
                }

        return indices

    def _collect_us_stocks(self, target_date: date) -> dict:
        """
        미국 주식 수집 (ETF, 개별 종목)

        Args:
            target_date: 대상 날짜

        Returns:
            미국 주식 데이터 딕셔너리
        """
        us_stocks = {}
        us_stocks_config = self.config.get("us_stocks", {})

        for stock_key, symbol in us_stocks_config.items():
            logger.info(f"{stock_key} 미국 주식 수집 시작")

            price = self.stock_api.get_stock_price(symbol)

            if price:
                self.db.save_price(symbol, price, target_date)
                ath = self.db.get_all_time_high(symbol)
                us_stocks[stock_key] = {
                    "yesterday": price,
                    "ath": ath if ath else price
                }
                logger.info(f"{stock_key} 미국 주식: ${price:,.2f}")
            else:
                logger.warning(f"{stock_key} 미국 주식 수집 실패")
                us_stocks[stock_key] = {
                    "yesterday": 0,
                    "ath": 0
                }

        return us_stocks

    def _collect_forex(self, target_date: date) -> dict:
        """
        환율 수집

        Args:
            target_date: 대상 날짜

        Returns:
            환율 데이터 딕셔너리
        """
        forex = {}
        forex_config = self.config.get("forex", {})

        for forex_key, symbol in forex_config.items():
            logger.info(f"{forex_key} 환율 수집 시작")

            rate = self.stock_api.get_stock_price(symbol)

            if rate:
                self.db.save_price(symbol, rate, target_date)
                forex[forex_key] = {
                    "yesterday": rate,
                    "ath": rate  # 환율은 전고점 의미 없음
                }
                logger.info(f"{forex_key} 환율: {rate:,.2f}원/$")
            else:
                logger.warning(f"{forex_key} 환율 수집 실패")
                forex[forex_key] = {
                    "yesterday": 0,
                    "ath": 0
                }

        return forex

    def _check_all_time_high(self, symbol_key: str, price: float, target_date: date) -> bool:
        """
        전고점 갱신 체크

        Args:
            symbol_key: 종목 키
            price: 현재가
            target_date: 대상 날짜

        Returns:
            새로운 전고점 여부
        """
        if price is None:
            logger.warning(f"{symbol_key} 주가 없어 전고점 체크 skipped")
            return False

        symbol = self.config["symbols"][symbol_key]

        # 현재 활성 전고점 조회
        current_ath = self.db.get_active_all_time_high(symbol)

        # 기존 전고점이 없거나, 새로운 가격이 더 높은 경우
        is_new_ath = current_ath is None or price > current_ath["price"]

        if is_new_ath:
            self.db.save_all_time_high(symbol, price, target_date)
            logger.info(f"새로운 전고점 기록: {symbol_key} - {price:,.0f}원 ({target_date})")
            return True

        return False

    def _process_active_triggers(self, samsung_price: float, target_date: date):
        """
        활성 트리거 처리

        Args:
            samsung_price: 삼성전자 현재가
            target_date: 대상 날짜
        """
        active_trigger = self.db.get_active_alert_trigger()

        if not active_trigger:
            logger.info("활성 트리거 없음")
            return

        trigger_id = active_trigger["id"]
        triggered_at = date.fromisoformat(active_trigger["triggered_at"])
        days_passed = (target_date - triggered_at).days

        logger.info(f"활성 트리거: {triggered_at} ({days_passed}일 경과)")

        # 삼성전자 전고점 갱신 여부 확인
        samsung_ath_reached = self.db.check_samsung_ath_since(triggered_at)

        if samsung_ath_reached:
            # 삼성전자 전고점 갱신 -> 트리거 완료
            self.db.mark_trigger_completed(trigger_id, "ATH_REACHED")
            logger.info("삼성전자 전고점 갱신으로 트리거 완료")
            return

        # 30일 경과 및 삼성전자 미갱신 시 알림
        check_days = self.config["monitoring"]["check_days"]
        if days_passed >= check_days:
            if not active_trigger["email_sent"] and self.alert_sender:
                self._send_alert(
                    triggered_at=triggered_at,
                    days_passed=days_passed,
                    samsung_price=samsung_price,
                    trigger_id=trigger_id
                )

    def _send_alert(self, triggered_at: date, days_passed: int, samsung_price: float, trigger_id: int):
        """
        알림 발송

        Args:
            triggered_at: 트리거 발생일
            days_passed: 경과 일수
            samsung_price: 삼성전자 현재가
            trigger_id: 트리거 ID
        """
        try:
            # SK하이닉스 전고점 정보 조회
            sk_symbol = self.config["symbols"]["skhynix"]
            sk_ath = self.db.get_active_all_time_high(sk_symbol)

            # 삼성전자 전고점 조회
            samsung_symbol = self.config["symbols"]["samsung"]
            samsung_ath = self.db.get_all_time_high(samsung_symbol)

            if not sk_ath or not samsung_ath:
                logger.error("전고점 정보 부족으로 알림 발송 skipped")
                return

            # 이메일 발송
            recipients = self.config["email"]["recipients"]
            success = self.alert_sender.send_stock_alert(
                recipients=recipients,
                skhynix_ath_price=sk_ath["price"],
                skhynix_ath_date=date.fromisoformat(sk_ath["date"]),
                samsung_current=samsung_price,
                samsung_ath_price=samsung_ath,
                days_passed=days_passed
            )

            if success:
                self.db.mark_email_sent(trigger_id)
                logger.info(f"알림 발송 성공: {days_passed}일 경과")

        except Exception as e:
            logger.error(f"알림 발송 실패: {e}")

    def _send_daily_status(self, samsung_price: float, skhynix_price: float, target_date: date,
                          indices_data: dict = None, us_stocks_data: dict = None, forex_data: dict = None):
        """
        매일 상태 이메일 발송

        Args:
            samsung_price: 삼성전자 종가
            skhynix_price: SK하이닉스 종가
            target_date: 대상 날짜
            indices_data: 지수 데이터 딕셔너리
            us_stocks_data: 미국 주식 데이터 딕셔너리
            forex_data: 환율 데이터 딕셔너리
        """
        try:
            # 중복 발송 방지: 같은 날 이미 보냈으면 skip
            if self.db.is_daily_email_sent(target_date):
                logger.info(f"일일 이메일 이미 발송됨 ({target_date}) - skip")
                return

            # 전고점 정보 조회
            samsung_symbol = self.config["symbols"]["samsung"]
            skhynix_symbol = self.config["symbols"]["skhynix"]

            samsung_ath = self.db.get_all_time_high(samsung_symbol)
            skhynix_ath = self.db.get_active_all_time_high(skhynix_symbol)

            if not samsung_ath or not skhynix_ath:
                logger.warning("전고점 정보 부족으로 매일 상태 이메일 skipped")
                return

            # SK하이닉스 전고점 이후 경과 일수 계산
            sk_ath_date = date.fromisoformat(skhynix_ath["date"])
            days_since_sk_ath = (target_date - sk_ath_date).days

            # 이메일 발송
            recipients = self.config["email"]["recipients"]
            success = self.alert_sender.send_daily_status(
                recipients=recipients,
                samsung_ath_price=samsung_ath,
                samsung_yesterday_price=samsung_price,
                skhynix_ath_price=skhynix_ath["price"],
                skhynix_yesterday_price=skhynix_price,
                skhynix_ath_date=sk_ath_date,
                days_since_sk_ath=days_since_sk_ath,
                indices=indices_data,
                us_stocks=us_stocks_data,
                forex=forex_data
            )

            if success:
                self.db.mark_daily_email_sent(target_date)
                logger.info("매일 상태 이메일 발송 성공")

        except Exception as e:
            logger.error(f"매일 상태 이메일 발송 실패: {e}")

    def get_status(self) -> dict:
        """
        현재 상태 조회

        Returns:
            상태 정보 딕셔너리
        """
        samsung_symbol = self.config["symbols"]["samsung"]
        skhynix_symbol = self.config["symbols"]["skhynix"]

        samsung_latest = self.db.get_latest_price(samsung_symbol)
        skhynix_latest = self.db.get_latest_price(skhynix_symbol)

        samsung_ath = self.db.get_all_time_high(samsung_symbol)
        skhynix_ath = self.db.get_active_all_time_high(skhynix_symbol)

        active_trigger = self.db.get_active_alert_trigger()

        return {
            "timestamp": datetime.now().isoformat(),
            "samsung": {
                "current": samsung_latest,
                "ath": samsung_ath
            },
            "skhynix": {
                "current": skhynix_latest,
                "ath": skhynix_ath["price"] if skhynix_ath else None,
                "ath_date": skhynix_ath["date"] if skhynix_ath else None
            },
            "active_trigger": {
                "id": active_trigger["id"] if active_trigger else None,
                "triggered_at": active_trigger["triggered_at"] if active_trigger else None,
                "days_passed": (date.today() - date.fromisoformat(active_trigger["triggered_at"])).days if active_trigger else None,
                "email_sent": active_trigger["email_sent"] if active_trigger else None
            } if active_trigger else None
        }


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="주가 모니터링 시스템")
    parser.add_argument("--config", default="config.yaml", help="설정 파일 경로")
    parser.add_argument("--date", help="대상 날짜 (YYYY-MM-DD, 기본: 오늘)")
    parser.add_argument("--status", action="store_true", help="현재 상태 조회")

    args = parser.parse_args()

    # 모니터링 시스템 초기화
    monitor = StockMonitor(config_path=args.config)

    if args.status:
        # 상태 조회
        status = monitor.get_status()
        print(yaml.dump(status, allow_unicode=True, default_flow_style=False))
    else:
        # 모니터링 실행
        target_date = None
        if args.date:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

        monitor.run(target_date=target_date)


if __name__ == "__main__":
    main()
