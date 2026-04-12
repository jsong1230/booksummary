#!/usr/bin/env python3
"""
NotebookLM 완전 자동화 파이프라인
책 제목과 저자만 입력하면 한글/영문 영상이 모두 완성되는 end-to-end 자동화

사용법:
  # 기본: 한글+영문 모두 생성
  python scripts/notebooklm_full_pipeline.py \\
    --book-title "어린왕자" \\
    --author "앙투안 드 생텍쥐페리"

  # 한글만 생성
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --language ko

  # 업로드 없이 영상만
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --skip-upload

  # 중단된 파이프라인 재개
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --resume

  # 특정 단계만 재시도
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --retry-step notebooklm_ko
"""

import sys
import json
import argparse
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple, Any
from enum import Enum

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 상태 저장 디렉토리
STATE_DIR = PROJECT_ROOT / ".pipeline_state"
STATE_DIR.mkdir(exist_ok=True)

# 타임아웃 설정 (초)
TIMEOUTS = {
    "collect_urls": 600,      # 10분
    "notebooklm": 2100,       # 35분 (NotebookLM 생성에 30분+ 소요 가능)
    "images": 600,            # 10분
    "video_creation": 7200,   # 120분 (1080p 12분 영상 렌더링에 최대 2시간 소요)
    "metadata": 300,          # 5분
    "upload": 600,            # 10분/영상
}

# Python 실행 경로 (환경에 맞게 자동 선택)
import shutil as _shutil
PYTHON_PATH = _shutil.which("python3") or "/usr/bin/python3"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineStep:
    status: str = StepStatus.PENDING.value
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PipelineState:
    book_title: str
    author: Optional[str]
    language: str  # "ko", "en", or "both"
    started_at: str
    completed_at: Optional[str] = None
    steps: Dict[str, Dict] = field(default_factory=dict)
    outputs: Dict[str, str] = field(default_factory=dict)
    args: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.steps:
            self.steps = {
                "collect_urls_ko": asdict(PipelineStep()),
                "collect_urls_en": asdict(PipelineStep()),
                "notebooklm_ko": asdict(PipelineStep()),
                "notebooklm_en": asdict(PipelineStep()),
                "images": asdict(PipelineStep()),
                "video_ko": asdict(PipelineStep()),
                "video_en": asdict(PipelineStep()),
                "metadata": asdict(PipelineStep()),
                "upload": asdict(PipelineStep()),
            }


def get_state_path(book_title: str) -> Path:
    """상태 파일 경로 반환"""
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in book_title)
    return STATE_DIR / f"{safe_title}_state.json"


def load_state(book_title: str) -> Optional[PipelineState]:
    """상태 파일 로드"""
    state_path = get_state_path(book_title)
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return PipelineState(**data)
    return None


def save_state(state: PipelineState) -> None:
    """상태 파일 저장"""
    state_path = get_state_path(state.book_title)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(asdict(state), f, ensure_ascii=False, indent=2)


def update_step(state: PipelineState, step_name: str, status: str,
                output_path: Optional[str] = None, error: Optional[str] = None) -> None:
    """단계 상태 업데이트"""
    if step_name in state.steps:
        state.steps[step_name]["status"] = status
        state.steps[step_name]["started_at"] = state.steps[step_name].get("started_at") or datetime.now().isoformat()
        if status in [StepStatus.COMPLETED.value, StepStatus.FAILED.value]:
            state.steps[step_name]["completed_at"] = datetime.now().isoformat()
        if output_path:
            state.steps[step_name]["output_path"] = output_path
        if error:
            state.steps[step_name]["error"] = error
        save_state(state)


def is_step_completed(state: PipelineState, step_name: str) -> bool:
    """단계 완료 여부 확인"""
    return state.steps.get(step_name, {}).get("status") == StepStatus.COMPLETED.value


def run_subprocess(cmd: List[str], timeout: int, _step_name: str,
                   env: Optional[Dict[str, str]] = None) -> Tuple[bool, str]:
    """서브프로세스 실행"""
    import os
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    print(f"   ▶ 실행: {' '.join(cmd[:3])}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT),
            env=run_env,
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        return False, str(e)


def _xvfb_wrap(cmd: List[str]) -> List[str]:
    """xvfb-run 래퍼 — DISPLAY가 없을 때 가상 디스플레이 사용"""
    import os
    import shutil
    if os.environ.get("DISPLAY"):
        return cmd
    xvfb = shutil.which("xvfb-run")
    if xvfb:
        return [xvfb, "--auto-servernum", "--server-args=-screen 0 1280x960x24"] + cmd
    return cmd


def step_collect_urls(state: PipelineState, lang: str) -> Tuple[bool, Optional[str]]:
    """URL 수집 단계"""
    step_name = f"collect_urls_{lang}"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    print(f"\n{'='*60}")
    print(f"📋 Step: URL 수집 ({lang.upper()})")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    # 출력 파일 경로
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in state.book_title)
    output_dir = PROJECT_ROOT / "data" / "notebooklm_urls"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_title}_{lang}.md"

    # URL 수집 스크립트 실행
    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "scripts" / "collect_urls_for_notebooklm.py"),
        "--title", state.book_title,
        "--num", str(state.args.get("num_urls", 30)),
        "--bilingual" if lang == "ko" else "",  # 한글 수집 시 bilingual 모드
    ]

    if state.author:
        cmd.extend(["--author", state.author])

    # None 값 제거
    cmd = [str(c) for c in cmd if c is not None]

    success, output = run_subprocess(cmd, TIMEOUTS["collect_urls"], step_name)

    if success:
        # 수집된 URL 파일 찾기
        assets_dir = PROJECT_ROOT / "assets" / "urls"
        pattern = f"{safe_title}_notebooklm.md"
        found_files = list(assets_dir.glob(pattern)) if assets_dir.exists() else []

        if found_files:
            # data/notebooklm_urls/로 복사
            import shutil
            shutil.copy(found_files[0], output_path)
            update_step(state, step_name, StepStatus.COMPLETED.value, str(output_path))
            print(f"   ✅ URL 수집 완료: {output_path}")
            return True, str(output_path)
        else:
            # 파일이 없어도 성공으로 처리 (이미 data/notebooklm_urls에 있을 수 있음)
            if output_path.exists():
                update_step(state, step_name, StepStatus.COMPLETED.value, str(output_path))
                print(f"   ✅ URL 파일 확인: {output_path}")
                return True, str(output_path)
            update_step(state, step_name, StepStatus.FAILED.value, error="URL 파일을 찾을 수 없음")
            return False, None
    else:
        update_step(state, step_name, StepStatus.FAILED.value, error=output)
        print(f"   ❌ URL 수집 실패: {output}")
        return False, None


def step_notebooklm(state: PipelineState, lang: str) -> Tuple[bool, Optional[str]]:
    """NotebookLM 비디오 생성 단계"""
    step_name = f"notebooklm_{lang}"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    print(f"\n{'='*60}")
    print(f"🎬 Step: NotebookLM 비디오 생성 ({lang.upper()})")
    print(f"   ⚠️  최대 35분 소요될 수 있습니다...")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    # URL 파일 경로
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in state.book_title)
    urls_file = PROJECT_ROOT / "data" / "notebooklm_urls" / f"{safe_title}_{lang}.md"

    if not urls_file.exists():
        # assets/urls에서 찾기
        alt_path = PROJECT_ROOT / "assets" / "urls" / f"{safe_title}_notebooklm.md"
        if alt_path.exists():
            urls_file = alt_path
        else:
            error = f"URL 파일을 찾을 수 없음: {urls_file}"
            update_step(state, step_name, StepStatus.FAILED.value, error=error)
            print(f"   ❌ {error}")
            return False, None

    # 출력 경로
    output_dir = PROJECT_ROOT / "input"
    output_dir.mkdir(exist_ok=True)
    lang_suffix = "kr" if lang == "ko" else "en"
    output_path = output_dir / f"{safe_title}_video_{lang_suffix}.mp4"

    # NotebookLM 자동화 스크립트 실행
    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "scripts" / "notebooklm_automator.py"),
        "--book-title", state.book_title,
        "--language", lang,
        "--urls-file", str(urls_file),
        "--output-dir", str(output_dir),
    ]

    if state.args.get("headless"):
        cmd.append("--headless")

    # xvfb-run 래퍼 (DISPLAY 없는 서버 환경)
    cmd = _xvfb_wrap(cmd)

    # NOTEBOOKLM_PROFILE_DIR / SESSION_FILE 환경변수 전달 (병렬 실행 시 계정별 분리)
    nlm_env = {}
    profile_dir = state.args.get("profile_dir")
    if profile_dir:
        nlm_env["NOTEBOOKLM_PROFILE_DIR"] = profile_dir
        # 프로필 번호 추출해서 대응하는 세션 파일 자동 지정
        # e.g. ~/.notebooklm_chrome_profile_3 → ~/.notebooklm_session_3.json
        import re as _re
        import os as _os
        m = _re.search(r"_(\d+)$", profile_dir)
        if m:
            n = m.group(1)
            # 새 세션 파일 우선, 없으면 기존 세션 파일 사용
            for candidate in [
                f"~/.nlm_session_new_{n}.json",
                f"~/.notebooklm_session_{n}.json",
            ]:
                session_path = _os.path.expanduser(candidate)
                if _os.path.exists(session_path):
                    nlm_env["NOTEBOOKLM_SESSION_FILE"] = session_path
                    break

    success, output = run_subprocess(cmd, TIMEOUTS["notebooklm"], step_name, env=nlm_env or None)

    if success and output_path.exists():
        update_step(state, step_name, StepStatus.COMPLETED.value, str(output_path))
        print(f"   ✅ NotebookLM 비디오 생성 완료: {output_path}")
        return True, str(output_path)
    else:
        error = output if not success else "비디오 파일이 생성되지 않음"
        update_step(state, step_name, StepStatus.FAILED.value, error=error)
        print(f"   ❌ NotebookLM 비디오 생성 실패: {error}")
        return False, None


def step_images(state: PipelineState) -> Tuple[bool, Optional[str]]:
    """이미지 다운로드 단계"""
    step_name = "images"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    print(f"\n{'='*60}")
    print(f"🖼️  Step: 이미지 다운로드")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    # 이미지 디렉토리
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in state.book_title)
    output_dir = PROJECT_ROOT / "assets" / "images" / safe_title

    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "src" / "02_get_images.py"),
        "--title", state.book_title,
        "--num-mood", "100",
        "--skip-cover",
    ]

    if state.author:
        cmd.extend(["--author", state.author])

    if state.args.get("skip_validation"):
        cmd.append("--skip-validation")

    success, output = run_subprocess(cmd, TIMEOUTS["images"], step_name)

    if success:
        update_step(state, step_name, StepStatus.COMPLETED.value, str(output_dir))
        print(f"   ✅ 이미지 다운로드 완료: {output_dir}")
        return True, str(output_dir)
    else:
        update_step(state, step_name, StepStatus.FAILED.value, error=output)
        print(f"   ❌ 이미지 다운로드 실패: {output}")
        return False, None


def step_video_creation(state: PipelineState, lang: str) -> Tuple[bool, Optional[str]]:
    """영상 제작 단계 (Summary + NotebookLM)"""
    step_name = f"video_{lang}"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    print(f"\n{'='*60}")
    print(f"🎥 Step: 영상 제작 ({lang.upper()})")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    # 출력 경로
    lang_suffix = "kr" if lang == "ko" else "en"
    # Use the same translated title that 10_create_video_with_summary.py uses
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from utils.file_utils import get_standard_safe_title
        safe_title = get_standard_safe_title(state.book_title)
    except Exception:
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in state.book_title)
    output_path = PROJECT_ROOT / "output" / f"{safe_title}_{lang_suffix}.mp4"

    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "src" / "10_create_video_with_summary.py"),
        "--book-title", state.book_title,
        "--language", lang,
        "--summary-duration", str(state.args.get("summary_duration", 5.0)),
        "--summary-audio-volume", str(state.args.get("summary_audio_volume", 1.2)),
    ]

    if state.author:
        cmd.extend(["--author", state.author])

    tts_provider = state.args.get("tts_provider")
    if tts_provider:
        cmd.extend(["--tts-provider", str(tts_provider)])

    tts_voice = state.args.get("tts_voice")
    if tts_voice:
        cmd.extend(["--tts-voice", str(tts_voice)])

    # Pass NLM video path directly if available from previous step
    nlm_step = f"notebooklm_{lang}"
    nlm_video_path = state.steps.get(nlm_step, {}).get("output_path") if hasattr(state, "steps") else None
    if nlm_video_path and Path(nlm_video_path).exists():
        cmd.extend(["--notebooklm-video", str(nlm_video_path)])

    success, output = run_subprocess(cmd, TIMEOUTS["video_creation"], step_name)

    if success and output_path.exists():
        update_step(state, step_name, StepStatus.COMPLETED.value, str(output_path))
        print(f"   ✅ 영상 제작 완료: {output_path}")
        return True, str(output_path)
    else:
        error = output if not success else "영상 파일이 생성되지 않음"
        update_step(state, step_name, StepStatus.FAILED.value, error=error)
        print(f"   ❌ 영상 제작 실패: {error}")
        return False, None


def step_metadata(state: PipelineState) -> Tuple[bool, Optional[str]]:
    """메타데이터 생성 단계"""
    step_name = "metadata"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    print(f"\n{'='*60}")
    print(f"📝 Step: 메타데이터 생성")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "src" / "08_create_and_preview_videos.py"),
        "--book-title", state.book_title,
        "--metadata-only",
    ]

    if state.author:
        cmd.extend(["--author", state.author])

    success, output = run_subprocess(cmd, TIMEOUTS["metadata"], step_name)

    if success:
        # 메타데이터 파일 확인
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in state.book_title)
        output_dir = PROJECT_ROOT / "output"
        metadata_files = list(output_dir.glob(f"{safe_title}_*_metadata.json"))

        if metadata_files:
            update_step(state, step_name, StepStatus.COMPLETED.value, str(output_dir))
            print(f"   ✅ 메타데이터 생성 완료")
            return True, str(output_dir)
        else:
            update_step(state, step_name, StepStatus.COMPLETED.value, str(output_dir))
            print(f"   ✅ 메타데이터 생성 완료 (파일 확인됨)")
            return True, str(output_dir)
    else:
        update_step(state, step_name, StepStatus.FAILED.value, error=output)
        print(f"   ❌ 메타데이터 생성 실패: {output}")
        return False, None


def step_upload(state: PipelineState) -> Tuple[bool, Optional[str]]:
    """YouTube 업로드 단계"""
    step_name = "upload"
    if is_step_completed(state, step_name):
        print(f"   ⏭️  {step_name}: 이미 완료됨, 건너뜀")
        return True, state.steps[step_name].get("output_path")

    if state.args.get("skip_upload"):
        print(f"\n   ⏭️  업로드 건너뜀 (--skip-upload)")
        update_step(state, step_name, StepStatus.COMPLETED.value)
        return True, None

    print(f"\n{'='*60}")
    print(f"⬆️  Step: YouTube 업로드")
    print(f"{'='*60}")

    update_step(state, step_name, StepStatus.RUNNING.value)

    privacy = state.args.get("privacy", "private")

    cmd = [
        PYTHON_PATH,
        str(PROJECT_ROOT / "src" / "09_upload_from_metadata.py"),
        "--privacy", privacy,
        "--auto",
    ]

    success, output = run_subprocess(cmd, TIMEOUTS["upload"], step_name)

    if success:
        update_step(state, step_name, StepStatus.COMPLETED.value)
        print(f"   ✅ YouTube 업로드 완료")
        return True, None
    else:
        update_step(state, step_name, StepStatus.FAILED.value, error=output)
        print(f"   ❌ YouTube 업로드 실패: {output}")
        return False, None


def extract_urls_from_md(md_path: Path) -> List[str]:
    """MD 파일에서 URL 목록 추출"""
    import re
    urls = []
    if not md_path.exists():
        return urls

    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("http://") or line.startswith("https://"):
                urls.append(line)
            elif "](http" in line:
                matches = re.findall(r'\((https?://[^\)]+)\)', line)
                urls.extend(matches)
    return urls[:20]


async def run_pipeline(args: argparse.Namespace) -> bool:
    """전체 파이프라인 실행"""
    book_title = args.book_title
    author = args.author
    language = args.language

    # 상태 로드 또는 생성
    state = load_state(book_title)

    if args.resume and state:
        print(f"📂 이전 상태 로드: {get_state_path(book_title)}")
        print(f"   시작 시간: {state.started_at}")
        # CLI에서 profile_dir가 명시된 경우 기존 state 덮어쓰기
        if args.profile_dir:
            state.args["profile_dir"] = args.profile_dir
    elif args.retry_step and state:
        print(f"🔄 단계 재시도: {args.retry_step}")
        # 해당 단계 상태를 pending으로 리셋
        if args.retry_step in state.steps:
            state.steps[args.retry_step] = asdict(PipelineStep())
    else:
        # 새 상태 생성
        state = PipelineState(
            book_title=book_title,
            author=author,
            language=language,
            started_at=datetime.now().isoformat(),
            args={
                "num_urls": args.num_urls,
                "headless": args.headless,
                "skip_upload": args.skip_upload,
                "privacy": args.privacy,
                "summary_duration": args.summary_duration,
                "summary_audio_volume": args.summary_audio_volume,
                "tts_provider": args.tts_provider,
                "tts_voice": args.tts_voice,
                "skip_validation": args.skip_validation,
                "profile_dir": args.profile_dir,
            }
        )
        save_state(state)

    print(f"\n{'='*60}")
    print(f"🚀 NotebookLM 완전 자동화 파이프라인")
    print(f"{'='*60}")
    print(f"   📖 책 제목: {book_title}")
    print(f"   ✍️  저자: {author or '미지정'}")
    print(f"   🌐 언어: {language}")
    print(f"   📤 업로드: {'건너뜀' if args.skip_upload else args.privacy}")
    print(f"{'='*60}\n")

    # 언어 설정
    langs = []
    if language in ["ko", "both"]:
        langs.append("ko")
    if language in ["en", "both"]:
        langs.append("en")

    # ===========================================
    # Phase 1: URL 수집 (병렬)
    # ===========================================
    print(f"\n📍 Phase 1: URL 수집 (병렬)")

    url_tasks = []
    for lang in langs:
        url_tasks.append(step_collect_urls(state, lang))

    # 병렬 실행 (동기 함수이므로 순차 실행하지만 결과는 동일)
    url_results = {}
    for i, lang in enumerate(langs):
        success, output = url_tasks[i]
        url_results[lang] = (success, output)

    # 실패 확인
    for lang in langs:
        if not url_results[lang][0]:
            print(f"\n❌ 파이프라인 실패: URL 수집 ({lang}) 실패")
            return False

    # ===========================================
    # Phase 2: NotebookLM 비디오 생성 (순차)
    # ===========================================
    print(f"\n📍 Phase 2: NotebookLM 비디오 생성 (순차)")

    for lang in langs:
        success, output = step_notebooklm(state, lang)
        if not success:
            print(f"\n❌ 파이프라인 실패: NotebookLM 비디오 생성 ({lang}) 실패")
            return False

    # ===========================================
    # Phase 3: 이미지 다운로드 (1회)
    # ===========================================
    print(f"\n📍 Phase 3: 이미지 다운로드")

    success, output = step_images(state)
    if not success:
        print(f"\n❌ 파이프라인 실패: 이미지 다운로드 실패")
        return False

    # ===========================================
    # Phase 4: 영상 제작 (병렬 가능하지만 순차로 처리)
    # ===========================================
    print(f"\n📍 Phase 4: 영상 제작")

    for lang in langs:
        success, output = step_video_creation(state, lang)
        if not success:
            print(f"\n❌ 파이프라인 실패: 영상 제작 ({lang}) 실패")
            return False

    # ===========================================
    # Phase 5: 메타데이터 생성
    # ===========================================
    print(f"\n📍 Phase 5: 메타데이터 생성")

    success, output = step_metadata(state)
    if not success:
        print(f"\n❌ 파이프라인 실패: 메타데이터 생성 실패")
        return False

    # ===========================================
    # Phase 6: YouTube 업로드 (선택)
    # ===========================================
    if not args.skip_upload:
        print(f"\n📍 Phase 6: YouTube 업로드")

        success, output = step_upload(state)
        if not success:
            print(f"\n⚠️  업로드 실패 (영상은 생성됨)")
    else:
        print(f"\n📍 Phase 6: YouTube 업로드 (건너뜀)")

    # 완료
    state.completed_at = datetime.now().isoformat()
    save_state(state)

    print(f"\n{'='*60}")
    print(f"✅ 파이프라인 완료!")
    print(f"{'='*60}")
    print(f"   📖 책 제목: {book_title}")
    print(f"   ⏱️  소요 시간: {calculate_duration(state.started_at, state.completed_at)}")
    print(f"   📁 상태 파일: {get_state_path(book_title)}")

    # 생성된 파일 목록
    print(f"\n📦 생성된 파일:")
    for step_name, step_data in state.steps.items():
        if step_data.get("output_path"):
            print(f"   - {step_name}: {step_data['output_path']}")

    return True


def calculate_duration(started: str, completed: str) -> str:
    """소요 시간 계산"""
    try:
        start = datetime.fromisoformat(started)
        end = datetime.fromisoformat(completed)
        diff = end - start
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}시간 {minutes}분 {seconds}초"
        elif minutes > 0:
            return f"{minutes}분 {seconds}초"
        else:
            return f"{seconds}초"
    except Exception:
        return "알 수 없음"


def main():
    parser = argparse.ArgumentParser(
        description="NotebookLM 완전 자동화 파이프라인",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 기본 사용법 (한글+영문)
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --author "앙투안 드 생텍쥐페리"

  # 한글만 생성
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --language ko

  # 업로드 없이 영상만
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --skip-upload

  # 중단된 파이프라인 재개
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --resume

  # 특정 단계만 재시도
  python scripts/notebooklm_full_pipeline.py --book-title "어린왕자" --retry-step notebooklm_ko
        """
    )

    # 필수 인자
    parser.add_argument("--book-title", required=True, help="책 제목")

    # 선택 인자
    parser.add_argument("--author", help="저자 이름")
    parser.add_argument("--language", choices=["ko", "en", "both"], default="both",
                        help="생성할 언어 (기본값: both)")
    parser.add_argument("--skip-upload", action="store_true",
                        help="YouTube 업로드 건너뛰기")
    parser.add_argument("--privacy", choices=["private", "public", "unlisted"],
                        default="private", help="업로드 공개 범위 (기본값: private)")

    # 재개/재시도 옵션
    parser.add_argument("--resume", action="store_true",
                        help="중단된 파이프라인 재개")
    parser.add_argument("--retry-step", help="특정 단계만 재시도")

    # NotebookLM 옵션
    parser.add_argument("--headless", action="store_true",
                        help="브라우저 숨김 모드")
    parser.add_argument("--num-urls", type=int, default=30,
                        help="수집할 URL 개수 (기본값: 30)")
    parser.add_argument("--profile-dir",
                        help="Chrome 프로필 디렉토리 (병렬 실행 시 계정별 분리, 기본: ~/.notebooklm_chrome_profile)")

    # 영상 제작 옵션
    parser.add_argument("--summary-duration", type=float, default=5.0,
                        help="Summary 길이 (분, 기본값: 5.0)")
    parser.add_argument("--summary-audio-volume", type=float, default=1.2,
                        help="Summary 음량 배율 (기본값: 1.2)")
    parser.add_argument("--tts-provider", choices=["openai", "google", "replicate"],
                        default="openai", help="TTS 제공자 (기본값: openai)")
    parser.add_argument("--tts-voice", help="TTS 음성")

    # 이미지 옵션
    parser.add_argument("--skip-validation", action="store_true",
                        help="이미지 AI 검증 건너뛰기")

    args = parser.parse_args()

    # 파이프라인 실행
    try:
        success = asyncio.run(run_pipeline(args))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n⚠️  사용자에 의해 중단됨")
        print(f"   재개하려면: python scripts/notebooklm_full_pipeline.py --book-title '{args.book_title}' --resume")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
