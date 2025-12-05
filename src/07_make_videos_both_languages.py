"""
한글/영문 오디오에 대해 각각 영상 제작 스크립트
- 한글 오디오 → 한글 메타데이터 영상
- 영문 오디오 → 영문 메타데이터 영상
"""

import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 03_make_video.py import
import importlib.util
spec = importlib.util.spec_from_file_location("make_video", Path(__file__).parent / "03_make_video.py")
make_video_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(make_video_module)
VideoMaker = make_video_module.VideoMaker


def find_audio_files(audio_dir: str = "assets/audio"):
    """한글/영문 오디오 파일 찾기"""
    audio_path = Path(audio_dir)
    audio_files = list(audio_path.glob("*.m4a")) + list(audio_path.glob("*.wav")) + list(audio_path.glob("*.mp3"))
    
    korean_audio = None
    english_audio = None
    
    for audio_file in audio_files:
        filename = audio_file.stem
        # 한글 포함 여부 확인
        has_korean = any(ord(c) > 127 for c in filename)
        
        if has_korean:
            korean_audio = audio_file
        else:
            english_audio = audio_file
    
    return korean_audio, english_audio


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='한글/영문 오디오에 대해 각각 영상 제작')
    parser.add_argument('--book-title', type=str, default="노르웨이의 숲", help='책 제목')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    
    args = parser.parse_args()
    
    # 오디오 파일 찾기
    korean_audio, english_audio = find_audio_files()
    
    print("=" * 60)
    print("🎬 다국어 영상 제작 시작")
    print("=" * 60)
    print()
    
    if not korean_audio and not english_audio:
        print("❌ 오디오 파일을 찾을 수 없습니다.")
        return
    
    # 이미지 디렉토리 설정
    from utils.file_utils import safe_title
    safe_title_str = safe_title(args.book_title)
    if args.image_dir is None:
        args.image_dir = f"assets/images/{safe_title_str}"
    
    maker = VideoMaker(
        resolution=(1920, 1080), 
        fps=30,
        bitrate="5000k",
        audio_bitrate="320k"
    )
    
    # 한글 영상 제작
    if korean_audio:
        print(f"🇰🇷 한글 영상 제작")
        print(f"   오디오: {korean_audio.name}")
        print()
        
        output_path = f"output/{safe_title_str}_review_ko.mp4"
        
        maker.create_video(
            audio_path=str(korean_audio),
            image_dir=args.image_dir,
            output_path=output_path,
            add_subtitles_flag=False,
            language="ko"
        )
        print()
    
    # 영문 영상 제작
    if english_audio:
        print(f"🇺🇸 영문 영상 제작")
        print(f"   오디오: {english_audio.name}")
        print()
        
        output_path = f"output/{safe_title_str}_review_en.mp4"
        
        maker.create_video(
            audio_path=str(english_audio),
            image_dir=args.image_dir,
            output_path=output_path,
            add_subtitles_flag=False,
            language="en"
        )
        print()
    
    print("=" * 60)
    print("✅ 모든 영상 제작 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()

