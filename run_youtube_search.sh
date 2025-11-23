#!/bin/bash
# YouTube 영상 검색 스크립트 실행 (가상환경 자동 활성화)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경이 없으면 생성
if [ ! -d "venv" ]; then
    echo "⚠️ 가상환경이 없습니다. 가상환경을 생성합니다..."
    ./setup_venv.sh
fi

# 가상환경 활성화
source venv/bin/activate

# YouTube 영상 검색 스크립트 실행
python src/06_search_youtube.py "$@"

