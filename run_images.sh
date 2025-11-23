#!/bin/bash
# 이미지 다운로드 스크립트 실행 (가상환경 자동 활성화)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경이 없으면 생성
if [ ! -d "venv" ]; then
    echo "⚠️ 가상환경이 없습니다. 가상환경을 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 이미지 다운로드 스크립트 실행
python src/02_get_images.py "$@"

