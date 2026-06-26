#!/bin/bash
# GitHub 저장소 초기화 및 푸시 스크립트

set -e

echo "========================================="
echo "GitHub 저장소 설정"
echo "========================================="
echo ""

# Git 초기화 확인
if [ ! -d ".git" ]; then
    echo "Git 저장소 초기화..."
    git init
    git branch -M main
else
    echo "Git 저장소가 이미 초기화되어 있습니다."
fi

# .gitignore 확인
if [ ! -f ".gitignore" ]; then
    echo "⚠️  .gitignore가 없습니다. config.yaml과 .env가 GitHub에 올라갈 수 있습니다."
    read -p ".gitignore를 생성하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
venv/
env/

# 프로젝트
data/
logs/
*.db
*.log

# 설정 (민감 정보)
config.yaml
.env
EOF
        echo "✅ .gitignore 생성 완료"
    fi
fi

# 변경사항 스테이징
echo ""
echo "Git 스테이징..."
git add .

# 커밋
echo ""
echo "Git 커밋..."
git commit -m "Initial commit: 삼성전자/SK하이닉스 주가 모니터링 시스템" || echo "커밋할 내용이 없습니다."

# 원격 저장소 정보
echo ""
echo "========================================="
echo "GitHub 원격 저장소 설정"
echo "========================================="
echo ""
echo "1. GitHub에서 새 저장소를 생성하세요:"
echo "   https://github.com/new"
echo ""
echo "2. 저장소 이름: samsungnikSellon"
echo "   Public: 선택 (추천)"
echo ""
read -p "3. GitHub 저장소 URL을 입력하세요: " git_url

if [ -n "$git_url" ]; then
    # 원격 저장소 추가
    if git remote | grep -q "origin"; then
        git remote set-url origin "$git_url"
    else
        git remote add origin "$git_url"
    fi

    echo ""
    echo "푸시 중..."
    git push -u origin main || git push -u origin main --force

    echo ""
    echo "✅ GitHub에 푸시 완료!"
    echo ""
    echo "이제 Render에서 이 저장소를 연결하여 배포할 수 있습니다."
    echo "https://dashboard.render.com"
else
    echo "❌ URL이 입력되지 않았습니다."
    echo "수동으로 원격 저장소를 추가하세요:"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/samsungnikSellon.git"
    echo "  git push -u origin main"
fi
