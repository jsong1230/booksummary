#!/bin/bash
# 일당백 책 목록 수집 스크립트 실행 (가상환경 자동 활성화)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경이 없으면 생성
if [ ! -d "venv" ]; then
    echo "⚠️ 가상환경이 없습니다. 가상환경을 생성합니다..."
    ./setup_venv.sh
fi

# 가상환경 활성화
source venv/bin/activate

# 책 목록 수집 스크립트 실행
python src/00_collect_books.py

