#!/bin/bash
# iMac에서 실행: NotebookLM Google 계정 로그인 후 프로필을 mini-home으로 전송
#
# 사용법:
#   bash scripts/login_on_imac.sh          # 5개 프로필 순서대로 로그인
#   bash scripts/login_on_imac.sh 2        # 프로필 2번만 로그인
#
# 각 프로필을 다른 Google 계정으로 로그인해야 합니다 (NotebookLM 병렬 실행용)
# Chrome 창이 열리면 로그인 완료 후 직접 닫아주세요 → 다음 프로필이 열립니다

set -u

MINI_HOME="172.30.1.58"
MINI_HOME_USER="jsong"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 실패한 5권에 해당하는 프로필 (2~6)
PROFILES=(2 3 4 5 6)
BOOKS=("분노의 포도" "기나긴 이별" "조직의 성쇠" "오즈의 마법사" "한국의 베스트셀러")

if [ "${1:-}" != "" ]; then
    PROFILES=("$1")
    IDX=$(($1 - 2))
    BOOKS=("${BOOKS[$IDX]}")
fi

echo "============================================================"
echo "  NotebookLM 프로필 로그인 (iMac)"
echo "  로그인 완료 후 Chrome 창을 닫으면 다음 프로필로 넘어갑니다"
echo "============================================================"
echo ""

for i in "${!PROFILES[@]}"; do
    NUM="${PROFILES[$i]}"
    BOOK="${BOOKS[$i]}"
    PROFILE_DIR="$HOME/.nlm_pw_$NUM"

    echo "▶ [$NUM] $BOOK"
    echo "   프로필: $PROFILE_DIR"
    echo "   → Chrome이 열립니다. Google 로그인 후 창을 닫아주세요."
    echo ""

    "$CHROME" \
        --user-data-dir="$PROFILE_DIR" \
        --no-first-run \
        --window-size=1280,800 \
        "https://notebooklm.google.com" 2>/dev/null

    echo "   ✅ 프로필 $NUM 로그인 완료"
    echo ""
done

echo "============================================================"
echo "  모든 로그인 완료! 프로필을 mini-home으로 전송합니다..."
echo "============================================================"
echo ""

for NUM in "${PROFILES[@]}"; do
    echo "▶ 프로필 $NUM → mini-home 전송 중..."
    rsync -az --delete "$HOME/.nlm_pw_$NUM/" "$MINI_HOME_USER@$MINI_HOME:~/.nlm_pw_$NUM/"
    echo "   ✅ 전송 완료"
done

echo ""
echo "============================================================"
echo "  모든 프로필 전송 완료! mini-home에서 파이프라인 실행 가능"
echo "============================================================"
