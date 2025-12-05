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
from typing import Optional

try:
    from dotenv import load_dotenv  # type: ignore[import-untyped]
except ImportError:
    def load_dotenv() -> None:  # dotenv가 없어도 동작하도록
        pass

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
        self.video_maker = VideoMaker(
            resolution=(1920, 1080), 
            fps=30,
            bitrate="5000k",
            audio_bitrate="320k"
        )
    
    def create_video_with_summary(
        self,
        book_title: str,
        author: str = None,
        review_audio_path: str = None,
        language: str = "ko",
        summary_duration_minutes: float = 5.0,
        image_dir: str = None,
        output_path: str = None,
        skip_summary: bool = False,
        notebooklm_video_path: Optional[str] = None,
        summary_audio_volume: float = 1.2
    ) -> str:
        """
        요약 포함 영상 제작 (Summary → NotebookLM Video → Audio 순서)
        
        Args:
            book_title: 책 제목
            author: 저자 이름
            review_audio_path: NotebookLM 리뷰 오디오 경로
            language: 언어 ('ko' 또는 'en')
            summary_duration_minutes: 요약 길이 (분 단위)
            image_dir: 이미지 디렉토리
            output_path: 출력 영상 경로
            skip_summary: 요약 생성을 건너뛰기 (이미 생성된 경우)
            notebooklm_video_path: NotebookLM 비디오 파일 경로 (선택사항)
            summary_audio_volume: Summary 오디오 음량 배율 (기본값: 1.2, 20% 증가)
            
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
        lang_suffix = "ko" if language == "ko" else "en"
        
        # 기존 Summary 파일 확인
        summary_file_path = Path("assets/summaries") / f"{safe_title_str}_summary_{lang_suffix}.md"
        existing_summary_text = None
        
        if summary_file_path.exists():
            print("=" * 60)
            print("📚 기존 Summary 파일 발견")
            print("=" * 60)
            print(f"   파일: {summary_file_path}")
            print()
            try:
                with open(summary_file_path, 'r', encoding='utf-8') as f:
                    existing_summary_text = f.read()
                print("✅ 기존 Summary 파일 로드 완료")
                print()
            except Exception as e:
                print(f"⚠️ Summary 파일 읽기 실패: {e}")
                existing_summary_text = None
        
        if not skip_summary and existing_summary_text is None:
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
                existing_summary_text = summary_text
                
            except Exception as e:
                print(f"❌ 요약 생성 실패: {e}")
                print("⚠️ 요약 없이 리뷰만으로 영상을 제작합니다.")
                existing_summary_text = None
        
        # 2. TTS로 요약 음성 생성 (Summary 텍스트가 있는 경우)
        if existing_summary_text:
            # 요약 오디오가 이미 있는지 확인
            summary_audio_path = f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3"
            
            if not Path(summary_audio_path).exists():
                print("=" * 60)
                print("🎤 2단계: TTS 요약 음성 생성")
                print("=" * 60)
                print()
                
                # 한국어는 nova (더 자연스러운 여성 음성), 영어는 alloy 추천
                voice = "nova" if language == "ko" else "alloy"
                
                self.tts_engine.generate_speech(
                    text=existing_summary_text,
                    output_path=summary_audio_path,
                    voice=voice,
                    language=language,
                    model="tts-1-hd"  # 고품질 모델 사용
                )
                print()
            else:
                print("=" * 60)
                print("🎤 기존 Summary 오디오 사용")
                print("=" * 60)
                print(f"   파일: {summary_audio_path}")
                print()
        else:
            print("⚠️ Summary 텍스트가 없어 요약 오디오를 생성하지 않습니다.")
            summary_audio_path = None
        
        # 3. 리뷰 오디오 경로 확인 (일관된 네이밍 규칙 사용)
        if review_audio_path is None:
            lang_suffix = "ko" if language == "ko" else "en"
            audio_dir = Path("assets/audio")
            
            if not audio_dir.exists():
                raise FileNotFoundError(f"오디오 디렉토리를 찾을 수 없습니다: {audio_dir}")
            
            # 표준 네이밍 규칙: {책제목}_review_{언어}.{확장자}
            review_audio_path = None
            for ext in ['.m4a', '.mp3', '.wav', '.mp4']:
                test_path = audio_dir / f"{safe_title_str}_review_{lang_suffix}{ext}"
                if test_path.exists():
                    review_audio_path = str(test_path)
                    print(f"🎵 리뷰 오디오 발견: {test_path.name}")
                    break
            
            if not review_audio_path:
                raise FileNotFoundError(f"리뷰 오디오를 찾을 수 없습니다: assets/audio/{safe_title_str}_review_{lang_suffix}.*")
        
        if not Path(review_audio_path).exists():
            raise FileNotFoundError(f"리뷰 오디오를 찾을 수 없습니다: {review_audio_path}")
        
        # 4. 이미지 디렉토리 확인
        if image_dir is None:
            image_dir = f"assets/images/{safe_title_str}"
        
        if not Path(image_dir).exists():
            raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
        
        # 5. NotebookLM 비디오 파일 찾기 (일관된 네이밍 규칙 사용)
        if notebooklm_video_path is None:
            lang_suffix = "ko" if language == "ko" else "en"
            video_dir = Path("assets/video")
            
            if video_dir.exists():
                # 표준 네이밍 규칙: {책제목}_notebooklm_{언어}.{확장자}
                for ext in ['.mp4', '.mov', '.avi', '.mkv']:
                    test_path = video_dir / f"{safe_title_str}_notebooklm_{lang_suffix}{ext}"
                    if test_path.exists():
                        notebooklm_video_path = str(test_path)
                        print(f"📹 NotebookLM 비디오 발견: {test_path.name}")
                        break
        
        # 6. 출력 경로 설정
        if output_path is None:
            lang_suffix = "ko" if language == "ko" else "en"
            output_path = f"output/{safe_title_str}_review_with_summary_{lang_suffix}.mp4"
        
        # 7. 요약 오디오 최종 확인
        if summary_audio_path is None:
            print("=" * 60)
            print("❌ 요약 오디오가 없습니다!")
            print("=" * 60)
            print("   요약이 포함된 영상을 생성하려면 요약 오디오가 필요합니다.")
            print("   요약 없이 영상을 생성하면 나중에 다시 만들어야 합니다.")
            print()
            try:
                user_input = input("요약 없이 계속 진행하시겠습니까? (y/n): ").strip().lower()
                if user_input != 'y':
                    raise ValueError("영상 생성을 취소했습니다. 요약 오디오를 준비한 후 다시 시도하세요.")
            except (EOFError, KeyboardInterrupt):
                raise ValueError("영상 생성이 취소되었습니다. 요약 오디오를 준비한 후 다시 시도하세요.")
        
        # 8. 영상 제작
        print("=" * 60)
        print("🎬 3단계: 영상 제작")
        print("=" * 60)
        print()
        
        if notebooklm_video_path:
            print(f"📹 NotebookLM 비디오 사용: {Path(notebooklm_video_path).name}")
            print()
        
        final_video_path = self.video_maker.create_video(
            audio_path=review_audio_path,
            image_dir=image_dir,
            output_path=output_path,
            add_subtitles_flag=False,
            language=language,
            summary_audio_path=summary_audio_path,
            notebooklm_video_path=notebooklm_video_path,
            summary_audio_volume=summary_audio_volume
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
    
    parser = argparse.ArgumentParser(description='요약 포함 영상 제작 (Summary → NotebookLM Video → Audio)')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--review-audio', type=str, help='NotebookLM 리뷰 오디오 경로')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--summary-duration', type=float, default=5.0, help='요약 길이 (분 단위, 기본값: 5.0)')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    parser.add_argument('--output', type=str, help='출력 영상 경로')
    parser.add_argument('--skip-summary', action='store_true', help='요약 생성을 건너뛰기 (이미 생성된 경우)')
    parser.add_argument('--notebooklm-video', type=str, help='NotebookLM 비디오 파일 경로 (선택사항, 자동 검색도 지원)')
    parser.add_argument('--summary-audio-volume', type=float, default=1.2, help='Summary 오디오 음량 배율 (기본값: 1.2, 20%% 증가)')
    
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
            skip_summary=args.skip_summary,
            notebooklm_video_path=args.notebooklm_video,
            summary_audio_volume=args.summary_audio_volume
        )
        return 0
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

