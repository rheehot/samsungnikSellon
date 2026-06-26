"""
설정 관리 모듈
config.yaml 또는 환경 변수에서 설정을 로드합니다.
"""

import os
import yaml
from pathlib import Path
from typing import Optional


def load_config(config_path: str = "config.yaml") -> dict:
    """
    설정 로드

    Args:
        config_path: 설정 파일 경로

    Returns:
        설정 딕셔너리
    """
    # 환경 변수 우선
    config = {
        "symbols": {
            "samsung": os.getenv("SAMSUNG_SYMBOL", "005930.KS"),
            "skhynix": os.getenv("SKHYNIX_SYMBOL", "000660.KS")
        },
        "monitoring": {
            "check_days": int(os.getenv("CHECK_DAYS", "30")),
            "check_hour": int(os.getenv("CHECK_HOUR", "8")),
            "check_minute": int(os.getenv("CHECK_MINUTE", "0"))
        },
        "email": {
            "enabled": os.getenv("EMAIL_ENABLED", "true").lower() == "true",
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "sender": os.getenv("EMAIL_SENDER", ""),
            "password": os.getenv("EMAIL_PASSWORD", ""),
            "recipients": parse_recipients(os.getenv("EMAIL_RECIPIENTS", ""))
        },
        "database": {
            "path": os.getenv("DATABASE_PATH", "./data/stock_monitor.db")
        },
        "api": {
            "retry_attempts": int(os.getenv("API_RETRY_ATTEMPTS", "3")),
            "retry_delay": int(os.getenv("API_RETRY_DELAY", "5"))
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "./logs/monitor.log")
        }
    }

    # config.yaml이 있으면 환경 변수보다 우선 (환경 변수가 없는 경우)
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)

            # 환경 변수로 설정되지 않은 값만 파일 설정 사용
            if not config["email"]["sender"] and file_config.get("email", {}).get("sender"):
                config["email"]["sender"] = file_config["email"]["sender"]
            if not config["email"]["password"] and file_config.get("email", {}).get("password"):
                config["email"]["password"] = file_config["email"]["password"]
            if not config["email"]["recipients"] and file_config.get("email", {}).get("recipients"):
                config["email"]["recipients"] = file_config["email"]["recipients"]

        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")

    return config


def parse_recipients(recipients_str: str) -> list:
    """
    수신자 문자열 파싱

    Args:
        recipients_str: 쉼표로 구분된 이메일 문자열

    Returns:
        이메일 리스트
    """
    if not recipients_str:
        return []
    return [email.strip() for email in recipients_str.split(",") if email.strip()]


def validate_config(config: dict) -> tuple[bool, str]:
    """
    설정 유효성 검사

    Args:
        config: 설정 딕셔너리

    Returns:
        (유효 여부, 에러 메시지)
    """
    if config["email"]["enabled"]:
        if not config["email"]["sender"]:
            return False, "이메일 발신자가 설정되지 않았습니다 (EMAIL_SENDER)"
        if not config["email"]["password"]:
            return False, "이메일 비밀번호가 설정되지 않았습니다 (EMAIL_PASSWORD)"
        if not config["email"]["recipients"]:
            return False, "이메일 수신자가 설정되지 않았습니다 (EMAIL_RECIPIENTS)"

    return True, ""
