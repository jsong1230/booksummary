#!/bin/bash
# 한글/영문 오디오에 대해 각각 영상 제작 스크립트 실행

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경 활성화
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️ 가상환경이 없습니다."
    exit 1
fi

# 영상 제작 스크립트 실행
python src/07_make_videos_both_languages.py "$@"

