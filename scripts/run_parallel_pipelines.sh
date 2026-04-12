#!/bin/bash
# 일당백 시즌2 18~23화 병렬 파이프라인 실행
# 각 파이프라인마다 별도 Chrome 프로필(Google 계정) 사용
#
# 사전 조건:
#   각 계정별 Chrome 프로필 로그인 완료
#   계정 1: ~/.notebooklm_chrome_profile       (기본, 이미 로그인됨)
#   계정 2: ~/.notebooklm_chrome_profile_2
#   계정 3: ~/.notebooklm_chrome_profile_3
#   계정 4: ~/.notebooklm_chrome_profile_4
#   계정 5: ~/.notebooklm_chrome_profile_5
#   계정 6: ~/.notebooklm_chrome_profile_6
#
# 사용법:
#   bash scripts/run_parallel_pipelines.sh
#   bash scripts/run_parallel_pipelines.sh --skip-upload   # 업로드 없이

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON="python3"
PIPELINE="$SCRIPT_DIR/notebooklm_full_pipeline.py"
LOG_DIR="$PROJECT_ROOT/logs/parallel_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

EXTRA_ARGS="${1:-}"

declare -A BOOKS
BOOKS[1]="소용돌이의 한국정치|그레고리 헨더슨"
BOOKS[2]="분노의 포도|존 스타인벡"
BOOKS[3]="기나긴 이별|레이먼드 챈들러"
BOOKS[4]="조직의 성쇠|사카이야 다이치"
BOOKS[5]="오즈의 마법사|프랭크 바움"
BOOKS[6]="한국의 베스트셀러|한기호 외"

echo "============================================================"
echo "  일당백 시즌2 18~23화 병렬 파이프라인"
echo "  로그 디렉토리: $LOG_DIR"
echo "============================================================"
echo ""

PIDS=()

for i in $(seq 1 6); do
    IFS="|" read -r TITLE AUTHOR <<< "${BOOKS[$i]}"

    if [ "$i" -eq 1 ]; then
        PROFILE_DIR="$HOME/.notebooklm_chrome_profile"
    else
        PROFILE_DIR="$HOME/.nlm_pw_$i"
    fi

    LOG_FILE="$LOG_DIR/pipeline_${i}_$(echo "$TITLE" | tr ' ' '_').log"

    echo "▶ [$i] $TITLE ($AUTHOR)"
    echo "   프로필: $PROFILE_DIR"
    echo "   로그:   $LOG_FILE"

    $PYTHON "$PIPELINE" \
        --book-title "$TITLE" \
        --author "$AUTHOR" \
        --language ko \
        --skip-upload \
        --profile-dir "$PROFILE_DIR" \
        $EXTRA_ARGS \
        > "$LOG_FILE" 2>&1 &

    PIDS+=($!)
    echo "   PID: ${PIDS[-1]}"
    echo ""
done

echo "============================================================"
echo "  모든 파이프라인 시작됨 (${#PIDS[@]}개)"
echo "  로그 실시간 확인: tail -f $LOG_DIR/*.log"
echo "============================================================"
echo ""

# 모든 프로세스 종료 대기
FAILED=0
for i in "${!PIDS[@]}"; do
    PID="${PIDS[$i]}"
    IDX=$((i + 1))
    IFS="|" read -r TITLE AUTHOR <<< "${BOOKS[$IDX]}"
    wait "$PID"
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ [$IDX] $TITLE — 완료"
    else
        echo "❌ [$IDX] $TITLE — 실패 (exit $EXIT_CODE)"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "============================================================"
if [ $FAILED -eq 0 ]; then
    echo "  모든 파이프라인 완료!"
else
    echo "  완료: $((6 - FAILED))개 / 실패: ${FAILED}개"
    echo "  로그 확인: $LOG_DIR/"
fi
echo "============================================================"
