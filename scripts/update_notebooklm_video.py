#!/usr/bin/env python3
"""
Downloads 폴더에서 새로운 NotebookLM 비디오 파일을 찾아 교체하고 한국어 영상 재생성

사용법:
    python scripts/update_notebooklm_video.py --book-title "책 제목" --prefix "파일_접두사" --language ko
"""

import sys
import argparse
from pathlib import Path
import shutil
import subprocess

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.file_utils import safe_title

def find_notebooklm_video_in_downloads(prefix: str, lang: str = "ko") -> Path:
    """Downloads 폴더에서 NotebookLM 비디오 파일 찾기"""
    downloads_dir = Path.home() / "Downloads"
    
    # 언어 접미사 매핑
    lang_suffixes = {
        "ko": ["kr", "ko"],
        "en": ["en"]
    }
    
    suffixes = lang_suffixes.get(lang, [lang])
    extensions = ['.mp4', '.mov', '.avi', '.mkv']
    
    for lang_suffix in suffixes:
        for ext in extensions:
            pattern = f"{prefix}_video_{lang_suffix}{ext}"
            file_path = downloads_dir / pattern
            if file_path.exists():
                return file_path
    
    return None

def update_notebooklm_video(book_title: str, prefix: str, lang: str = "ko"):
    """NotebookLM 비디오 파일 교체 및 한국어 영상 재생성"""
    print("=" * 60)
    print(f"🔄 NotebookLM 비디오 업데이트 ({lang.upper()})")
    print("=" * 60)
    print()
    
    # 1. Downloads 폴더에서 새 비디오 파일 찾기
    print("📁 Downloads 폴더에서 새 비디오 파일 검색 중...")
    new_video = find_notebooklm_video_in_downloads(prefix, lang)
    
    if not new_video:
        print(f"❌ Downloads 폴더에서 {prefix}_video_{lang} 파일을 찾을 수 없습니다.")
        print(f"   찾는 패턴: {prefix}_video_kr.mp4, {prefix}_video_ko.mp4 등")
        return False
    
    print(f"✅ 새 비디오 파일 발견: {new_video.name}")
    print()
    
    # 2. 기존 비디오 파일 경로 확인
    safe_title_str = safe_title(book_title)
    video_dir = Path("assets/video")
    video_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 파일 찾기 (여러 확장자 확인)
    existing_video = None
    for ext in ['.mp4', '.mov', '.avi', '.mkv']:
        candidate = video_dir / f"{safe_title_str}_notebooklm_{lang}{ext}"
        if candidate.exists():
            existing_video = candidate
            break
    
    # 3. 기존 파일 백업 (선택사항)
    if existing_video:
        backup_path = existing_video.with_suffix(existing_video.suffix + '.backup')
        print(f"📦 기존 파일 백업: {existing_video.name} → {backup_path.name}")
        shutil.copy2(existing_video, backup_path)
        print(f"   ✅ 백업 완료")
        print()
    
    # 4. 새 파일로 교체
    lang_suffix = "ko" if lang == "ko" else "en"
    ext = new_video.suffix
    target_path = video_dir / f"{safe_title_str}_notebooklm_{lang_suffix}{ext}"
    
    print(f"🔄 비디오 파일 교체 중...")
    print(f"   소스: {new_video.name}")
    print(f"   대상: {target_path.name}")
    
    # 기존 파일이 있으면 삭제
    if target_path.exists():
        target_path.unlink()
    
    # 새 파일 복사
    shutil.copy2(new_video, target_path)
    print(f"   ✅ 교체 완료")
    print()
    
    # 5. 한국어 영상 재생성
    print("=" * 60)
    print(f"🎬 {lang.upper()} 영상 재생성")
    print("=" * 60)
    print()
    
    video_script = Path(__file__).parent.parent / "src" / "10_create_video_with_summary.py"
    
    cmd = [
        sys.executable,
        str(video_script),
        "--book-title", book_title,
        "--language", lang,
        "--summary-duration", "5.0",
        "--summary-audio-volume", "1.2",
        "--skip-summary"  # Summary는 이미 있으므로 건너뛰기
    ]
    
    print(f"실행 명령: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, check=False)
    
    if result.returncode == 0:
        print()
        print("=" * 60)
        print(f"✅ {lang.upper()} 영상 재생성 완료!")
        print("=" * 60)
        return True
    else:
        print()
        print("=" * 60)
        print(f"❌ {lang.upper()} 영상 재생성 실패")
        print("=" * 60)
        return False

def main():
    parser = argparse.ArgumentParser(description='NotebookLM 비디오 업데이트 및 영상 재생성')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--prefix', type=str, required=True, help='Downloads 폴더의 파일 접두사')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    
    args = parser.parse_args()
    
    success = update_notebooklm_video(
        book_title=args.book_title,
        prefix=args.prefix,
        lang=args.language
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
