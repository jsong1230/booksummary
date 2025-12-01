#!/usr/bin/env python3
"""
Summary 오디오 생성 스크립트
"""
import sys
from pathlib import Path
import importlib.util

# 프로젝트 루트를 경로에 추가 (scripts/ 폴더에서 실행 시)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.file_utils import safe_title

# TTS 모듈 동적 로드
tts_path = Path(__file__).parent.parent / "src" / "09_text_to_speech.py"
spec = importlib.util.spec_from_file_location("text_to_speech", tts_path)
tts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tts_module)
TTSEngine = tts_module.TTSEngine

def generate_summary_audio(book_title: str, language: str = "ko"):
    """Summary 오디오 생성"""
    safe_title_str = safe_title(book_title)
    
    # Summary 파일 읽기 (다양한 파일명 패턴 시도)
    if language == "ko":
        # 여러 패턴 시도
        possible_paths = [
            Path(f"assets/summaries/{safe_title_str}_summary_kr.md"),
            Path(f"assets/summaries/{safe_title_str.lower()}_summary_kr.md"),
            Path(f"assets/summaries/sunrise_summary_kr.md"),  # 실제 파일명
        ]
        output_path = f"assets/audio/{safe_title_str}_summary_ko.mp3"
        voice = "nova"
    else:
        possible_paths = [
            Path(f"assets/summaries/{safe_title_str}_summary_en.md"),
            Path(f"assets/summaries/{safe_title_str.lower()}_summary_en.md"),
            Path(f"assets/summaries/sunrise_summary_en.md"),  # 실제 파일명
        ]
        output_path = f"assets/audio/{safe_title_str}_summary_en.mp3"
        voice = "alloy"
    
    summary_path = None
    for path in possible_paths:
        if path.exists():
            summary_path = path
            break
    
    if not summary_path.exists():
        print(f"❌ Summary 파일을 찾을 수 없습니다: {summary_path}")
        return None
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary_text = f.read()
    
    print(f"📚 Summary 텍스트 길이: {len(summary_text)}자")
    print()
    
    # TTS 생성
    tts = TTSEngine()
    
    print(f"🎤 {language.upper()} Summary 오디오 생성 중...")
    tts.generate_speech(
        text=summary_text,
        output_path=output_path,
        voice=voice,
        language=language,
        model="tts-1-hd"
    )
    print(f"✅ 생성 완료: {output_path}")
    return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Summary 오디오 생성')
    parser.add_argument('--title', type=str, default='Sunrise on the Reaping', help='책 제목')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어')
    
    args = parser.parse_args()
    
    generate_summary_audio(args.title, args.language)
