"""
요약 포함 영상 제작 파이프라인
1. 책 요약 생성 (한글/영문)
2. TTS로 요약 음성 생성
3. 요약 음성 + NotebookLM 리뷰 음성 연결
4. 영상 제작
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 숫자로 시작하는 모듈은 importlib 사용
import importlib.util

# 08_generate_summary 모듈 로드
spec1 = importlib.util.spec_from_file_location("generate_summary", Path(__file__).parent / "08_generate_summary.py")
generate_summary_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(generate_summary_module)
SummaryGenerator = generate_summary_module.SummaryGenerator

# 09_text_to_speech 모듈 로드
spec2 = importlib.util.spec_from_file_location("text_to_speech", Path(__file__).parent / "09_text_to_speech.py")
text_to_speech_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(text_to_speech_module)
TTSEngine = text_to_speech_module.TTSEngine

# 03_make_video 모듈 로드
spec3 = importlib.util.spec_from_file_location("make_video", Path(__file__).parent / "03_make_video.py")
make_video_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(make_video_module)
VideoMaker = make_video_module.VideoMaker

load_dotenv()


class VideoWithSummaryPipeline:
    """요약 포함 영상 제작 파이프라인"""
    
    def __init__(self):
        self.summary_generator = SummaryGenerator()
        self.tts_engine = TTSEngine()
        self.video_maker = VideoMaker(resolution=(1920, 1080), fps=30)
    
    def create_video_with_summary(
        self,
        book_title: str,
        author: str = None,
        review_audio_path: str = None,
        language: str = "ko",
        summary_duration_minutes: float = 5.0,
        image_dir: str = None,
        output_path: str = None,
        skip_summary: bool = False
    ) -> str:
        """
        요약 포함 영상 제작
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            review_audio_path: NotebookLM 리뷰 오디오 경로
            language: 언어 ('ko' 또는 'en')
            summary_duration_minutes: 요약 길이 (분 단위)
            image_dir: 이미지 디렉토리
            output_path: 출력 영상 경로
            skip_summary: 요약 생성을 건너뛰기 (이미 생성된 경우)
            
        Returns:
            생성된 영상 파일 경로
        """
        from utils.file_utils import safe_title
        from utils.translations import translate_book_title, translate_author_name
        
        # 영문 영상 생성 시 영어 제목과 영어 작가 이름 사용
        if language == "en":
            en_book_title = translate_book_title(book_title)
            en_author = translate_author_name(author) if author else None
            # 요약 생성과 메타데이터 생성을 위해 영어 제목/작가 사용
            summary_book_title = en_book_title
            summary_author = en_author
            display_book_title = f"{book_title} ({en_book_title})"
            display_author = f"{author} ({en_author})" if author and en_author else (author or "알 수 없음")
        else:
            summary_book_title = book_title
            summary_author = author
            display_book_title = book_title
            display_author = author or "알 수 없음"
        
        safe_title_str = safe_title(book_title)
        
        print("=" * 60)
        print("🎬 요약 포함 영상 제작 파이프라인 시작")
        print("=" * 60)
        print(f"책 제목: {display_book_title}")
        print(f"저자: {display_author}")
        print(f"언어: {language}")
        print()
        
        # 1. 요약 생성 (건너뛰지 않는 경우)
        summary_audio_path = None
        if not skip_summary:
            print("=" * 60)
            print("📚 1단계: 책 요약 생성")
            print("=" * 60)
            print()
            
            try:
                summary_text = self.summary_generator.generate_summary(
                    book_title=summary_book_title,
                    author=summary_author,
                    language=language,
                    duration_minutes=summary_duration_minutes,
                    use_engaging_opening=True  # Hook → Summary → Bridge 구조 사용
                )
                
                # 요약 텍스트 저장
                summary_text_path = self.summary_generator.save_summary(
                    summary=summary_text,
                    book_title=book_title,
                    language=language
                )
                print()
                
                # 2. TTS로 요약 음성 생성
                print("=" * 60)
                print("🎤 2단계: TTS 요약 음성 생성")
                print("=" * 60)
                print()
                
                lang_suffix = "ko" if language == "ko" else "en"
                summary_audio_path = f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3"
                
                # 한국어는 nova (더 자연스러운 여성 음성), 영어는 alloy 추천
                voice = "nova" if language == "ko" else "alloy"
                
                self.tts_engine.generate_speech(
                    text=summary_text,
                    output_path=summary_audio_path,
                    voice=voice,
                    language=language,
                    model="tts-1-hd"  # 고품질 모델 사용
                )
                print()
                
            except Exception as e:
                print(f"❌ 요약 생성 실패: {e}")
                print("⚠️ 요약 없이 리뷰만으로 영상을 제작합니다.")
                summary_audio_path = None
        else:
            # 이미 생성된 요약 오디오 찾기
            lang_suffix = "ko" if language == "ko" else "en"
            summary_audio_path = f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3"
            if not Path(summary_audio_path).exists():
                print(f"⚠️ 요약 오디오를 찾을 수 없습니다: {summary_audio_path}")
                summary_audio_path = None
        
        # 3. 리뷰 오디오 경로 확인
        if review_audio_path is None:
            # 자동으로 리뷰 오디오 찾기
            lang_suffix = "ko" if language == "ko" else "en"
            # _ko, _kr, _en 등 다양한 패턴 시도
            possible_names = [
                f"{safe_title_str}_review_{lang_suffix}",
                f"{safe_title_str}_review_kr" if language == "ko" else f"{safe_title_str}_review_en",
                f"{safe_title_str}_review"
            ]
            
            review_audio_path = None
            for name in possible_names:
                for ext in ['.m4a', '.mp3', '.wav']:
                    test_path = f"assets/audio/{name}{ext}"
                    if Path(test_path).exists():
                        review_audio_path = test_path
                        break
                if review_audio_path:
                    break
            
            if not review_audio_path:
                raise FileNotFoundError(f"리뷰 오디오를 찾을 수 없습니다: assets/audio/{safe_title_str}_review_*")
        
        if not Path(review_audio_path).exists():
            raise FileNotFoundError(f"리뷰 오디오를 찾을 수 없습니다: {review_audio_path}")
        
        # 4. 이미지 디렉토리 확인
        if image_dir is None:
            image_dir = f"assets/images/{safe_title_str}"
        
        if not Path(image_dir).exists():
            raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
        
        # 5. 출력 경로 설정
        if output_path is None:
            lang_suffix = "ko" if language == "ko" else "en"
            output_path = f"output/{safe_title_str}_review_with_summary_{lang_suffix}.mp4"
        
        # 6. 영상 제작
        print("=" * 60)
        print("🎬 3단계: 영상 제작")
        print("=" * 60)
        print()
        
        final_video_path = self.video_maker.create_video(
            audio_path=review_audio_path,
            image_dir=image_dir,
            output_path=output_path,
            add_subtitles_flag=False,
            language=language,
            summary_audio_path=summary_audio_path
        )
        
        print()
        print("=" * 60)
        print("✅ 요약 포함 영상 제작 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {final_video_path}")
        print()
        
        return final_video_path


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='요약 포함 영상 제작')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--review-audio', type=str, help='NotebookLM 리뷰 오디오 경로')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--summary-duration', type=float, default=5.0, help='요약 길이 (분 단위, 기본값: 5.0)')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    parser.add_argument('--output', type=str, help='출력 영상 경로')
    parser.add_argument('--skip-summary', action='store_true', help='요약 생성을 건너뛰기 (이미 생성된 경우)')
    
    args = parser.parse_args()
    
    pipeline = VideoWithSummaryPipeline()
    
    try:
        pipeline.create_video_with_summary(
            book_title=args.book_title,
            author=args.author,
            review_audio_path=args.review_audio,
            language=args.language,
            summary_duration_minutes=args.summary_duration,
            image_dir=args.image_dir,
            output_path=args.output,
            skip_summary=args.skip_summary
        )
        return 0
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

