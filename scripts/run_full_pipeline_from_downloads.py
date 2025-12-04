#!/usr/bin/env python3
"""
input 폴더에서 파일을 준비하고 전체 영상 제작 파이프라인 실행

워크플로우:
1. input 폴더에서 파일 준비 (표준 네이밍으로 변경 및 이동)
2. 이미지 다운로드 (100개)
3. 영상 생성 (한글/영어)
"""

import sys
from pathlib import Path
import subprocess

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.prepare_files_from_downloads import prepare_files
from src.utils.file_utils import safe_title

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="input 폴더에서 파일을 준비하고 전체 영상 제작 파이프라인 실행"
    )
    parser.add_argument("--book-title", required=True, help="책 제목")
    parser.add_argument("--author", required=True, help="저자 이름")
    parser.add_argument("--prefix", help="파일명 접두사 (자동 감지 시 생략 가능)")
    parser.add_argument("--skip-images", action="store_true", help="이미지 다운로드 건너뛰기")
    parser.add_argument("--skip-prepare", action="store_true", help="파일 준비 단계 건너뛰기")
    parser.add_argument("--language", choices=["ko", "en", "both"], default="both", help="생성할 언어 (기본값: both)")
    parser.add_argument("--summary-duration", type=float, default=5.0, help="요약 길이 (분 단위, 기본값: 5.0)")
    parser.add_argument("--summary-audio-volume", type=float, default=1.2, help="Summary 오디오 음량 배율 (기본값: 1.2)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 전체 영상 제작 파이프라인 시작")
    print("=" * 60)
    print(f"📖 책 제목: {args.book_title}")
    print(f"✍️ 저자: {args.author}")
    print()
    
    safe_title_str = safe_title(args.book_title)
    
    # 1단계: 파일 준비
    if not args.skip_prepare:
        print("\n" + "=" * 60)
        print("1️⃣ 파일 준비 단계")
        print("=" * 60)
        prepared_files = prepare_files(
            book_title=args.book_title,
            author=args.author,
            prefix=args.prefix
        )
        print()
    else:
        print("⏭️ 파일 준비 단계 건너뛰기")
        prepared_files = {
            'audio': {'en': None, 'ko': None},
            'summary': {'en': None, 'ko': None},
            'thumbnail': {'en': None, 'ko': None},
            'video': {'en': None, 'ko': None}
        }
    
    # 2단계: 이미지 다운로드
    if not args.skip_images:
        print("\n" + "=" * 60)
        print("2️⃣ 이미지 다운로드 단계")
        print("=" * 60)
        print()
        
        # 이미지 다운로드 스크립트 실행
        image_script = Path(__file__).parent.parent / "src" / "02_get_images.py"
        result = subprocess.run(
            [
                sys.executable,
                str(image_script),
                "--title", args.book_title,
                "--author", args.author,
                "--num-mood", "100"
            ],
            check=False
        )
        
        if result.returncode != 0:
            print("⚠️ 이미지 다운로드 중 오류 발생 (계속 진행)")
        print()
    else:
        print("⏭️ 이미지 다운로드 단계 건너뛰기")
    
    # 3단계: 영상 생성
    languages = []
    if args.language == "both":
        languages = ["ko", "en"]
    else:
        languages = [args.language]
    
    for lang in languages:
        print("\n" + "=" * 60)
        print(f"3️⃣ 영상 생성 단계 ({lang.upper()})")
        print("=" * 60)
        print()
        
        video_script = Path(__file__).parent.parent / "src" / "10_create_video_with_summary.py"
        
        cmd = [
            sys.executable,
            str(video_script),
            "--book-title", args.book_title,
            "--author", args.author,
            "--language", lang,
            "--summary-duration", str(args.summary_duration),
            "--summary-audio-volume", str(args.summary_audio_volume)
        ]
        
        # Summary 파일이 이미 있으면 skip-summary 옵션 추가
        if prepared_files['summary'][lang]:
            cmd.append("--skip-summary")
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"❌ {lang.upper()} 영상 생성 실패")
            continue
        
        print(f"✅ {lang.upper()} 영상 생성 완료")
        print()
    
    # 4단계: 메타데이터 생성
    print("\n" + "=" * 60)
    print("4️⃣ 메타데이터 생성 단계")
    print("=" * 60)
    print()
    
    for lang in languages:
        metadata_script = Path(__file__).parent.parent / "src" / "08_create_and_preview_videos.py"
        result = subprocess.run(
            [
                sys.executable,
                str(metadata_script),
                "--book-title", args.book_title,
                "--metadata-only"
            ],
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ {lang.upper()} 메타데이터 생성 완료")
        else:
            print(f"⚠️ {lang.upper()} 메타데이터 생성 중 오류 발생")
    
    print()
    print("=" * 60)
    print("✅ 전체 파이프라인 완료!")
    print("=" * 60)
    print()
    print("📋 다음 단계:")
    print("   1. 생성된 영상 확인: output/ 폴더")
    print("   2. 메타데이터 확인: output/*.metadata.json")
    print("   3. 유튜브 업로드: python src/09_upload_from_metadata.py")
    print()

if __name__ == "__main__":
    main()
