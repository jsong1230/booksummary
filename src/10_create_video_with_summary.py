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

# 로깅 시스템 import
from utils.logger import get_logger

# 숫자로 시작하는 모듈은 importlib 사용
import importlib.util

# 08_generate_summary 모듈 로드
spec1 = importlib.util.spec_from_file_location("generate_summary", Path(__file__).parent / "08_generate_summary.py")
generate_summary_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(generate_summary_module)
SummaryGenerator = generate_summary_module.SummaryGenerator

# 09_text_to_speech_multi 모듈 로드
spec2 = importlib.util.spec_from_file_location("text_to_speech_multi", Path(__file__).parent / "09_text_to_speech_multi.py")
text_to_speech_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(text_to_speech_module)
MultiTTSEngine = text_to_speech_module.MultiTTSEngine

# 03_make_video 모듈 로드
spec3 = importlib.util.spec_from_file_location("make_video", Path(__file__).parent / "03_make_video.py")
make_video_module = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(make_video_module)
VideoMaker = make_video_module.VideoMaker

load_dotenv()


class VideoWithSummaryPipeline:
    """요약 포함 영상 제작 파이프라인"""

    def __init__(self, tts_provider: str = "openai"):
        self.logger = get_logger(__name__)
        self.summary_generator = SummaryGenerator()
        # TTS 엔진 (MultiTTSEngine)
        self.tts_engine = MultiTTSEngine(provider=tts_provider)
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
        summary_audio_volume: float = 1.2,
        add_subtitles: Optional[bool] = None,  # None이면 언어에 따라 자동 결정
        tts_voice: Optional[str] = None  # TTS 음성 선택
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
            add_subtitles: Summary 부분에 자막 추가 여부 (None이면 언어에 따라 자동: ko=False, en=True)
            
        Returns:
            생성된 영상 파일 경로
        """
        from utils.file_utils import get_standard_safe_title
        from utils.translations import translate_book_title, translate_author_name

        # 언어 정규화 (kr → ko)
        if language == "kr":
            language = "ko"

        # 언어에 따라 자막 기본값 설정 (기본: 자막 없음)
        if add_subtitles is None:
            add_subtitles = False  # 기본적으로 자막 없음
        
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
        
        safe_title_str = get_standard_safe_title(book_title)
        
        self.logger.info("=" * 60)
        self.logger.info("🎬 요약 포함 영상 제작 파이프라인 시작")
        self.logger.info("=" * 60)
        self.logger.info(f"책 제목: {display_book_title}")
        self.logger.info(f"저자: {display_author}")
        self.logger.info(f"언어: {language}")
        self.logger.info("")
        
        # 1. 요약 생성 (건너뛰지 않는 경우)
        summary_audio_path = None
        lang_suffix = "kr" if language == "ko" else "en"
        
        # 기존 Summary 파일 확인 (여러 패턴 시도)
        summary_file_path = None
        possible_paths = [
            Path("assets/summaries") / f"{safe_title_str}_summary_{lang_suffix}.md",
            Path("assets/summaries") / f"{safe_title_str}_summary_ko.md" if lang_suffix == "kr" else None,
            Path("assets/summaries") / f"{safe_title_str}_summary_{lang_suffix}.txt",
            Path("assets/summaries") / f"{safe_title_str}_summary_ko.txt" if lang_suffix == "kr" else None,
        ]
        
        # None 제거
        possible_paths = [p for p in possible_paths if p is not None]
        
        # 한글 제목으로도 시도 (safe_title_str이 영문으로 변환된 경우)
        from src.utils.file_utils import safe_title
        korean_safe_title = safe_title(book_title)
        if korean_safe_title != safe_title_str:
            possible_paths.extend([
                Path("assets/summaries") / f"{korean_safe_title}_summary_{lang_suffix}.md",
                Path("assets/summaries") / f"{korean_safe_title}_summary_ko.md" if lang_suffix == "kr" else None,
                Path("assets/summaries") / f"{korean_safe_title}_summary_{lang_suffix}.txt",
                Path("assets/summaries") / f"{korean_safe_title}_summary_ko.txt" if lang_suffix == "kr" else None,
            ])
            possible_paths = [p for p in possible_paths if p is not None]
        
        # 존재하는 파일 찾기
        for path in possible_paths:
            if path.exists():
                summary_file_path = path
                break

        existing_summary_text = None
        
        if summary_file_path is not None and summary_file_path.exists():
            print("=" * 60)
            print("📚 기존 Summary 파일 발견")
            print("=" * 60)
            print(f"   파일: {summary_file_path}")
            print()
            try:
                with open(summary_file_path, 'r', encoding='utf-8') as f:
                    existing_summary_text = f.read()
                
                # TTS 생성을 위해 summary 파일 정리 및 저장
                cleaned_summary_text = self._clean_markdown_for_tts(existing_summary_text)
                
                # 정리된 버전을 파일에 저장 (원본 백업은 하지 않음, 덮어쓰기)
                with open(summary_file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_summary_text)
                
                print("✅ 기존 Summary 파일 로드 및 정리 완료")
                print("   (마크다운 태그 제거 및 TTS 최적화)")
                print()
                existing_summary_text = cleaned_summary_text
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
                    duration_minutes=summary_duration_minutes
                )
                
                # 요약 텍스트 저장
                summary_text_path = self.summary_generator.save_summary(
                    summary=summary_text,
                    book_title=book_title,
                    author=summary_author,
                    language=language,
                    duration_minutes=summary_duration_minutes
                )
                print()
                existing_summary_text = summary_text
                
            except Exception as e:
                print(f"❌ 요약 생성 실패: {e}")
                print("⚠️ 요약 없이 리뷰만으로 영상을 제작합니다.")
                existing_summary_text = None
        
        # 2. TTS로 요약 음성 생성 (Summary 텍스트가 있는 경우)
        if existing_summary_text:
            # 요약 오디오가 이미 있는지 확인 (summary 또는 longform 파일 모두 확인)
            summary_audio_path = None
            possible_paths = [
                f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3",
                f"assets/audio/{safe_title_str}_longform_{lang_suffix}.mp3",
                # 호환성을 위해 _ko.mp3도 확인
                f"assets/audio/{safe_title_str}_summary_ko.mp3" if lang_suffix == "kr" else None,
                f"assets/audio/{safe_title_str}_longform_ko.mp3" if lang_suffix == "kr" else None,
            ]
            
            # None 제거
            possible_paths = [p for p in possible_paths if p is not None]
            
            for path in possible_paths:
                if Path(path).exists():
                    summary_audio_path = path
                    break
            
            if summary_audio_path is None:
                print("=" * 60)
                print("🎤 2단계: TTS 요약 음성 생성")
                print("=" * 60)
                print()
                
                # 출력 경로 설정
                summary_audio_path = f"assets/audio/{safe_title_str}_summary_{lang_suffix}.mp3"
                
                # summary 파일은 이미 정리되었으므로 그대로 사용
                # TTS 음성 설정: tts_voice가 있으면 사용, 없으면 기본값
                if tts_voice:
                    voice = tts_voice
                else:
                    # 한국어는 nova (더 자연스러운 여성 음성), 영어는 alloy 추천
                    voice = "nova" if language == "ko" else "alloy"

                try:
                    self.tts_engine.generate_speech(
                        text=existing_summary_text,
                        output_path=summary_audio_path,
                        voice=voice,
                        language=language,
                        model="tts-1-hd"  # 고품질 모델
                    )
                except Exception as e:
                    raise ValueError(
                        f"TTS 요약 오디오 생성 실패: {e}\n"
                        f"- 해결: OPENAI_API_KEY 설정 확인 또는 TTS 제공자 설정 확인\n"
                        f"- 또는 요약 오디오 파일을 직접 준비: {summary_audio_path}"
                    )
                print()
            else:
                print("=" * 60)
                print("🎤 기존 Summary 오디오 사용")
                print("=" * 60)
                print(f"   파일: {summary_audio_path}")
                # longform 파일이면 summary로 이름 변경 (일관성 유지)
                if "_longform_" in summary_audio_path:
                    new_path = summary_audio_path.replace("_longform_", "_summary_")
                    Path(summary_audio_path).rename(new_path)
                    summary_audio_path = new_path
                    print(f"   → {Path(summary_audio_path).name}로 이름 변경됨")
                print()
        else:
            print("⚠️ Summary 텍스트가 없어 요약 오디오를 생성하지 않습니다.")
            summary_audio_path = None
        
        # 3. 리뷰 오디오 경로 확인 (선택사항, 최신 구조에서는 사용하지 않음)
        if review_audio_path is None:
            lang_suffix = "kr" if language == "ko" else "en"
            audio_dir = Path("assets/audio")
            
            if audio_dir.exists():
                # 표준 네이밍 규칙: {책제목}_review_{언어}.{확장자}
                for ext in ['.m4a', '.mp3', '.wav', '.mp4']:
                    test_path = audio_dir / f"{safe_title_str}_review_{lang_suffix}{ext}"
                    if test_path.exists():
                        review_audio_path = str(test_path)
                        print(f"🎵 리뷰 오디오 발견: {test_path.name} (선택사항, 사용하지 않음)")
                        break
        
        # 리뷰 오디오는 선택사항이므로 없어도 계속 진행
        
        # 4. 이미지 디렉토리 확인
        if image_dir is None:
            image_dir = f"assets/images/{safe_title_str}"
        
        if not Path(image_dir).exists():
            raise FileNotFoundError(f"이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
        
        # 5. NotebookLM 비디오 파일 찾기 (일관된 네이밍 규칙 사용)
        if notebooklm_video_path is None:
            lang_suffix = "kr" if language == "ko" else "en"
            video_dir = Path("assets/video")
            
            if video_dir.exists():
                # 여러 패턴 시도 (영문 제목, 한글 제목 모두 확인)
                from src.utils.file_utils import safe_title
                korean_safe_title = safe_title(book_title)
                possible_paths = []
                
                # 영문 제목으로 시도
                for ext in ['.mp4', '.mov', '.avi', '.mkv']:
                    possible_paths.append(video_dir / f"{safe_title_str}_notebooklm_{lang_suffix}{ext}")
                    possible_paths.append(video_dir / f"{safe_title_str}_notebooklm_ko.mp4" if lang_suffix == "kr" else None)
                    possible_paths.append(video_dir / f"{safe_title_str}_notebooklm_en.mp4" if lang_suffix == "en" else None)
                
                # 한글 제목으로도 시도
                if korean_safe_title != safe_title_str:
                    for ext in ['.mp4', '.mov', '.avi', '.mkv']:
                        possible_paths.append(video_dir / f"{korean_safe_title}_notebooklm_{lang_suffix}{ext}")
                        possible_paths.append(video_dir / f"{korean_safe_title}_notebooklm_ko.mp4" if lang_suffix == "kr" else None)
                        possible_paths.append(video_dir / f"{korean_safe_title}_notebooklm_en.mp4" if lang_suffix == "en" else None)
                
                # None 제거
                possible_paths = [p for p in possible_paths if p is not None]
                
                # 존재하는 파일 찾기
                for test_path in possible_paths:
                    if test_path.exists():
                        notebooklm_video_path = str(test_path)
                        print(f"📹 NotebookLM 비디오 발견: {test_path.name}")
                        break
        
        # 6. 출력 경로 설정
        if output_path is None:
            lang_suffix = "kr" if language == "ko" else "en"
            output_path = f"output/{safe_title_str}_{lang_suffix}.mp4"
        
        # 7. 요약 오디오 최종 확인 (필수)
        # - Summary+Video는 Summary 오디오가 핵심이므로, 없으면 즉시 중단합니다.
        # - 비대화형 환경에서도 멈추지 않도록 input()은 사용하지 않습니다.
        if summary_audio_path is None:
            raise ValueError(
                "요약 오디오가 없습니다. Summary+Video 제작을 중단합니다.\n"
                "- 해결: Summary 텍스트(assets/summaries/...)가 존재하는지 확인\n"
                "- 해결: TTS가 정상 동작하도록 OPENAI_API_KEY 등 환경 변수 확인\n"
                "- 또는 assets/audio/에 요약 오디오(mp3)를 미리 준비하세요."
            )
        
        # 8. 영상 제작
        print("=" * 60)
        print("🎬 3단계: 영상 제작")
        print("=" * 60)
        print()
        
        if notebooklm_video_path:
            print(f"📹 NotebookLM 비디오 사용: {Path(notebooklm_video_path).name}")
            print()
        
        # 자막 추가를 위한 summary_text 준비
        summary_text_for_subtitles = existing_summary_text if add_subtitles else None
        print(f"🔍 자막 설정 확인: add_subtitles={add_subtitles}, summary_text={'있음' if summary_text_for_subtitles else '없음'}")
        if summary_text_for_subtitles:
            print(f"   Summary 텍스트 길이: {len(summary_text_for_subtitles)} 문자")
        
        final_video_path = self.video_maker.create_video(
            audio_path=review_audio_path,
            image_dir=image_dir,
            output_path=output_path,
            add_subtitles_flag=add_subtitles,
            language=language,
            summary_audio_path=summary_audio_path,
            notebooklm_video_path=notebooklm_video_path,
            summary_audio_volume=summary_audio_volume,
            summary_text=summary_text_for_subtitles
        )
        
        print()
        print("=" * 60)
        print("✅ 요약 포함 영상 제작 완료!")
        print("=" * 60)
        print(f"📁 저장 위치: {final_video_path}")
        print()
        
        return final_video_path
    
    def _clean_markdown_for_tts(self, text: str) -> str:
        """
        TTS 생성을 위해 마크다운 태그 및 문법 정리
        구조적 태그([HOOK], [SUMMARY], [BRIDGE]) 제거 및 마크다운 문법 정리로 자연스러운 음성 흐름 확보
        메타데이터(책 제목, 저자, "TTS 기준..." 등) 자동 제거
        """
        import re
        
        # HTML 주석 제거 (<!-- -->)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # 파일 시작 부분의 메타데이터 제거
        # 패턴: 책 제목, 저자, "TTS 기준..." 같은 설명 라인
        lines = text.split('\n')
        cleaned_lines = []
        skip_metadata = True
        metadata_patterns = [
            r'^📘',  # 책 이모지
            r'^📖',  # 책 이모지
            r'^TTS 기준',
            r'^서머리 스크립트',
            r'^Summary script',
            r'^TTS 기준.*서머리',
            r'^TTS 기준.*스크립트',
            r'^.*약.*분.*서머리',
            r'^.*약.*분.*스크립트',
        ]
        
        for i, line in enumerate(lines):
            # 빈 줄이 나오면 메타데이터 구간 종료로 간주
            if skip_metadata and line.strip() == '':
                # 빈 줄 다음에 실제 내용이 시작되는 것으로 간주
                if i + 1 < len(lines) and lines[i + 1].strip():
                    skip_metadata = False
                    continue
            
            # 메타데이터 구간에서는 패턴 매칭하여 제거
            if skip_metadata:
                is_metadata = False
                for pattern in metadata_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        is_metadata = True
                        break
                
                # 첫 3줄 내에서 저자 이름이나 책 제목만 있는 경우도 메타데이터로 간주
                if i < 3 and line.strip() and not any(tag in line for tag in ['[HOOK]', '[SUMMARY]', '[BRIDGE]', '[CLOSING]']):
                    # 한글이나 영문만 있는 짧은 라인은 메타데이터일 가능성 높음
                    if len(line.strip()) < 50 and not line.strip().startswith('['):
                        is_metadata = True
                
                if is_metadata:
                    continue
            
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # 구조적 태그 제거
        text = re.sub(r'\[HOOK\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[HOOK\]', '', text)
        text = re.sub(r'\[SUMMARY\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[SUMMARY\]', '', text)
        text = re.sub(r'\[BRIDGE\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[BRIDGE\]', '', text)
        text = re.sub(r'\[CLOSING\s*–?\s*[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\[CLOSING\]', '', text)
        
        # 기타 구조적 태그 제거 (예: [핵심 장면], [상징과 의미] 등)
        text = re.sub(r'\[[^\]]+\]\s*$', '', text, flags=re.MULTILINE)
        
        # 헤더 제거
        text = re.sub(r'#+\s*', '', text)
        # 볼드 제거
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # 이탤릭 제거
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # 구분선 제거
        text = re.sub(r'---+\s*', '\n', text)
        # 번호 기호 제거
        text = re.sub(r'^\s*[①-⑳]\s*', '', text, flags=re.MULTILINE)
        # 번호 리스트 제거
        text = re.sub(r'^\s*[0-9]+\.\s*', '', text, flags=re.MULTILINE)
        # 리스트 마커 제거
        text = re.sub(r'^\s*[-*]\s*', '', text, flags=re.MULTILINE)
        # 『』를 ""로 변환
        text = re.sub(r'『([^』]+)』', r'"\1"', text)
        # 「」를 ""로 변환
        text = re.sub(r'「([^」]+)」', r'"\1"', text)
        # 연속된 빈 줄 정리
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text.strip()


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='요약 포함 영상 제작 (Summary → NotebookLM Video → Audio)')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--review-audio', type=str, help='NotebookLM 리뷰 오디오 경로')
    parser.add_argument('--language', type=str, default='ko', choices=['ko', 'kr', 'en'], help='언어 (기본값: ko)')
    parser.add_argument('--summary-duration', type=float, default=5.0, help='요약 길이 (분 단위, 기본값: 5.0)')
    parser.add_argument('--image-dir', type=str, help='이미지 디렉토리')
    parser.add_argument('--output', type=str, help='출력 영상 경로')
    parser.add_argument('--skip-summary', action='store_true', help='요약 생성을 건너뛰기 (이미 생성된 경우)')
    parser.add_argument('--notebooklm-video', type=str, help='NotebookLM 비디오 파일 경로 (선택사항, 자동 검색도 지원)')
    parser.add_argument('--summary-audio-volume', type=float, default=1.2, help='Summary 오디오 음량 배율 (기본값: 1.2, 20%% 증가)')
    parser.add_argument('--no-subtitles', action='store_true', help='Summary 부분 자막 추가 안 함 (언어 기본값 무시)')
    parser.add_argument('--subtitles', action='store_true', help='Summary 부분 자막 추가 (언어 기본값 무시)')
    parser.add_argument('--tts-provider', type=str, default='openai', choices=['openai', 'google'], help='TTS 제공자 (기본값: openai)')
    parser.add_argument('--tts-voice', type=str, help='TTS 음성 선택 (제공자별로 다름)')
    parser.add_argument('--prefix', type=str, help='input 폴더의 파일명 접두사 (파일 찾기용)')

    args = parser.parse_args()

    # TTS 제공자 매핑 (google → google_cloud)
    tts_provider_map = {
        'openai': 'openai',
        'google': 'google'
    }
    tts_provider = tts_provider_map.get(args.tts_provider, 'openai')

    pipeline = VideoWithSummaryPipeline(tts_provider=tts_provider)
    
    # 자막 설정: 플래그가 있으면 우선, 없으면 언어에 따라 자동 (None 전달)
    add_subtitles = None
    if args.no_subtitles:
        add_subtitles = False
    elif args.subtitles:
        add_subtitles = True
    # 둘 다 없으면 None (언어에 따라 자동 결정)
    
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
            summary_audio_volume=args.summary_audio_volume,
            add_subtitles=add_subtitles,
            tts_voice=args.tts_voice
        )
        return 0
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

