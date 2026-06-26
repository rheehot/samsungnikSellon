#!/bin/bash
# cron 자동 등록 스크립트

set -e

# 프로젝트 경로 (스크립트 위치 기준)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_DIR/venv/bin/activate"

echo "========================================="
echo "주가 모니터링 시스템 Cron 등록"
echo "========================================="
echo ""
echo "프로젝트 경로: $PROJECT_DIR"
echo "가상환경: $VENV_PATH"
echo ""

# 현재 crontab 확인
echo "현재 등록된 cron job:"
crontab -l 2>/dev/null || echo "(없음)"
echo ""

# 새로운 cron job 생성
CRON_JOB="0 8 * * * cd $PROJECT_DIR && source $VENV_PATH && PYTHONPATH=. python src/main.py >> $PROJECT_DIR/logs/cron.log 2>&1"

echo "등록할 cron job:"
echo "$CRON_JOB"
echo ""

# 사용자 확인
read -p "이 cron job을 등록하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 기존 crontab에 추가 (중복 방지)
    (crontab -l 2>/dev/null | grep -v "samsungnikSellon" | grep -v "src/main.py"; echo "$CRON_JOB") | crontab -
    echo "✅ cron job 등록 완료!"
    echo ""
    echo "등록된 cron job:"
    crontab -l | grep "samsungnikSellon\|src/main.py" || echo "(오류: 등록되지 않음)"
    echo ""
    echo "매일 아침 8시에 이메일이 발송됩니다."
else
    echo "❌ 취소되었습니다."
fi
