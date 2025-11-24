#!/bin/bash

# 완전 자동화 파이프라인 실행 스크립트
# 사용법: ./run_complete_pipeline.sh "책 제목" [저자 이름]

BOOK_TITLE="${1:-1984}"
AUTHOR="${2:-}"

echo "🚀 완전 자동화 파이프라인 시작"
echo "📚 책: $BOOK_TITLE"
if [ -n "$AUTHOR" ]; then
    echo "✍️ 저자: $AUTHOR"
fi
echo ""

# Python 스크립트 실행
if [ -n "$AUTHOR" ]; then
    python3 src/13_complete_pipeline.py --book-title "$BOOK_TITLE" --author "$AUTHOR"
else
    python3 src/13_complete_pipeline.py --book-title "$BOOK_TITLE"
fi
