#!/usr/bin/env python3
"""
NotebookLM 계정별 Chrome 프로필 로그인 도우미

사용법:
  # 계정 2번 프로필 로그인
  NOTEBOOKLM_PROFILE_DIR=~/.notebooklm_chrome_profile_2 \
    python scripts/login_notebooklm_profile.py

  # 또는 --profile-dir 인자 사용
  python scripts/login_notebooklm_profile.py --profile-dir ~/.notebooklm_chrome_profile_2

설명:
  병렬 파이프라인 실행을 위해 각 Google 계정별로 별도의 Chrome 프로필을 생성합니다.
  이 스크립트는 브라우저를 열어 로그인할 수 있도록 합니다.
"""

import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="NotebookLM 계정 프로필 로그인")
    parser.add_argument(
        "--profile-dir",
        help="Chrome 프로필 디렉토리 (기본: NOTEBOOKLM_PROFILE_DIR 환경변수 또는 ~/.notebooklm_chrome_profile_2)",
    )
    parser.add_argument(
        "--account-num", type=int, default=2,
        help="계정 번호 (기본: 2). --profile-dir 미지정 시 ~/.notebooklm_chrome_profile_{N} 사용",
    )
    args = parser.parse_args()

    # 프로필 디렉토리 결정
    if args.profile_dir:
        profile_dir = Path(args.profile_dir).expanduser()
    elif os.environ.get("NOTEBOOKLM_PROFILE_DIR"):
        profile_dir = Path(os.environ["NOTEBOOKLM_PROFILE_DIR"])
    else:
        profile_dir = Path.home() / f".notebooklm_chrome_profile_{args.account_num}"

    print(f"🔐 NotebookLM 프로필 로그인")
    print(f"   프로필 경로: {profile_dir}")
    print(f"   브라우저에서 Google 계정으로 로그인하세요.")
    print()

    # NOTEBOOKLM_PROFILE_DIR 환경변수 설정 후 automator --login 실행
    os.environ["NOTEBOOKLM_PROFILE_DIR"] = str(profile_dir)

    # automator의 login 함수 직접 호출
    import importlib.util
    automator_path = PROJECT_ROOT / "scripts" / "notebooklm_automator.py"
    spec = importlib.util.spec_from_file_location("notebooklm_automator", automator_path)
    automator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(automator)

    automator.login(headless=False)


if __name__ == "__main__":
    main()
