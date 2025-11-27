"""
완전 자동화 파이프라인 스크립트
- summary audio와 review audio를 자동으로 찾아서 영상 생성
- en/kr 언어별 metadata (title, description, tags) 생성 및 파일 저장
- thumbnail 생성 및 업로드
- 전체 프로세스를 한 번에 자동 실행
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Tuple, List

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# 필요한 모듈 import
import importlib.util

# 03_make_video.py
video_spec = importlib.util.spec_from_file_location("make_video", Path(__file__).parent / "03_make_video.py")
video_module = importlib.util.module_from_spec(video_spec)
video_spec.loader.exec_module(video_module)
VideoMaker = video_module.VideoMaker

# 08_create_and_preview_videos.py (metadata 생성용)
metadata_spec = importlib.util.spec_from_file_location("create_videos", Path(__file__).parent / "08_create_and_preview_videos.py")
metadata_module = importlib.util.module_from_spec(metadata_spec)
metadata_spec.loader.exec_module(metadata_module)
generate_title = metadata_module.generate_title
generate_description = metadata_module.generate_description
generate_tags = metadata_module.generate_tags
save_metadata = metadata_module.save_metadata

# 10_generate_thumbnail.py
thumbnail_spec = importlib.util.spec_from_file_location("generate_thumbnail", Path(__file__).parent / "10_generate_thumbnail.py")
thumbnail_module = importlib.util.module_from_spec(thumbnail_spec)
thumbnail_spec.loader.exec_module(thumbnail_module)
ThumbnailGenerator = thumbnail_module.ThumbnailGenerator

# 11_upload_thumbnails.py
upload_thumbnail_spec = importlib.util.spec_from_file_location("upload_thumbnails", Path(__file__).parent / "11_upload_thumbnails.py")
upload_thumbnail_module = importlib.util.module_from_spec(upload_thumbnail_spec)
upload_thumbnail_spec.loader.exec_module(upload_thumbnail_module)
ThumbnailUploader = upload_thumbnail_module.ThumbnailUploader

# 공통 유틸리티
from utils.file_utils import safe_title, load_book_info
from utils.translations import translate_book_title, translate_author_name

# 08_generate_summary.py (요약 생성용)
summary_spec = importlib.util.spec_from_file_location("generate_summary", Path(__file__).parent / "08_generate_summary.py")
summary_module = importlib.util.module_from_spec(summary_spec)
summary_spec.loader.exec_module(summary_module)
SummaryGenerator = summary_module.SummaryGenerator

# 09_text_to_speech.py (TTS용)
tts_spec = importlib.util.spec_from_file_location("text_to_speech", Path(__file__).parent / "09_text_to_speech.py")
tts_module = importlib.util.module_from_spec(tts_spec)
tts_spec.loader.exec_module(tts_module)
TTSEngine = tts_module.TTSEngine


class CompletePipeline:
    """완전 자동화 파이프라인 클래스"""
    
    def __init__(self):
        self.book_title = None
        self.author = None
        self.safe_title = None
        self.book_info = None
        self.summary_generator = SummaryGenerator()
        self.tts_engine = TTSEngine()
    
    def find_audio_files(self, book_title: str, audio_dir: str = "assets/audio") -> Dict[str, Dict[str, Optional[Path]]]:
        """
        summary audio와 review audio 파일 찾기
        
        Returns:
            {
                'ko': {
                    'summary': Path or None,
                    'review': Path or None
                },
                'en': {
                    'summary': Path or None,
                    'review': Path or None
                }
            }
        """
        audio_path = Path(audio_dir)
        safe_title_str = safe_title(book_title)
        safe_title_lower = safe_title_str.lower()
        
        print(f"   [DEBUG] book_title: {book_title}")
        print(f"   [DEBUG] safe_title_str: {safe_title_str}")
        print(f"   [DEBUG] safe_title_lower: {safe_title_lower}")
        
        result = {
            'ko': {'summary': None, 'review': None},
            'en': {'summary': None, 'review': None}
        }
        
        # 모든 오디오 파일 찾기
        audio_files = list(audio_path.glob("*.m4a")) + list(audio_path.glob("*.wav")) + list(audio_path.glob("*.mp3"))
        print(f"   [DEBUG] 총 오디오 파일 수: {len(audio_files)}")
        
        # 1순위: 정확한 패턴 매칭 ({book_title}_{type}_{lang}.{ext})
        for audio_file in audio_files:
            filename = audio_file.stem.lower()
            stem = audio_file.stem
            
            # 책 제목이 파일명에 포함되어 있는지 확인
            title_match = False
            if safe_title_lower and len(safe_title_lower) > 1:
                if safe_title_lower in filename or safe_title_lower in stem:
                    title_match = True
            # 한글 제목의 경우 원본 제목도 확인
            if book_title and book_title in stem:
                title_match = True
            # 영어 제목의 경우 (Three Kingdoms 등)
            if book_title and book_title.lower().replace(' ', '_') in filename:
                title_match = True
            # 특수 케이스: 삼국지 <-> Three Kingdoms 매칭
            if book_title == "삼국지" and ("three_kingdoms" in filename or "three_kingdom" in filename):
                title_match = True
            
            if not title_match:
                continue
            
            # summary 파일 찾기
            if 'summary' in filename:
                if 'ko' in filename or 'kr' in filename:
                    result['ko']['summary'] = audio_file
                elif 'en' in filename:
                    result['en']['summary'] = audio_file
                continue
            
            # review 파일 찾기
            if 'review' in filename:
                if 'ko' in filename or 'kr' in filename:
                    result['ko']['review'] = audio_file
                elif 'en' in filename:
                    result['en']['review'] = audio_file
                continue
            
            # review/summary가 없지만 책 제목이 포함된 경우, 언어 감지로 분류
            # 한글이 파일명에 포함되어 있으면 ko로 간주
            if any(ord(c) > 127 for c in stem) and not result['ko']['review']:
                print(f"   [DEBUG] KO review로 매칭: {audio_file.name}")
                result['ko']['review'] = audio_file
            # 영어만 있고 한글이 없으면 en으로 간주
            elif any(c.isalpha() and ord(c) < 128 for c in stem) and not any(ord(c) > 127 for c in stem) and not result['en']['review']:
                print(f"   [DEBUG] EN review로 매칭: {audio_file.name}")
                result['en']['review'] = audio_file
        
        # 2순위: 패턴 매칭 (책 제목 없이도 시도)
        for audio_file in audio_files:
            filename = audio_file.stem.lower()
            
            # 이미 찾은 파일은 건너뛰기
            if 'summary' in filename:
                if ('ko' in filename or 'kr' in filename) and not result['ko']['summary']:
                    # 한글이 파일명에 포함되어 있으면 ko로 간주
                    if any(ord(c) > 127 for c in audio_file.stem):
                        result['ko']['summary'] = audio_file
                elif 'en' in filename and not result['en']['summary']:
                    result['en']['summary'] = audio_file
            
            elif 'review' in filename:
                if ('ko' in filename or 'kr' in filename) and not result['ko']['review']:
                    # 한글이 파일명에 포함되어 있으면 ko로 간주
                    if any(ord(c) > 127 for c in audio_file.stem):
                        result['ko']['review'] = audio_file
                elif 'en' in filename and not result['en']['review']:
                    result['en']['review'] = audio_file
        
        return result
    
    def create_video_with_summary(
        self,
        lang: str,
        review_audio: Path,
        summary_audio: Optional[Path],
        image_dir: str,
        output_path: str
    ) -> bool:
        """summary audio를 포함한 영상 생성"""
        print(f"\n🎬 {lang.upper()} 영상 생성 중...")
        print(f"   Review 오디오: {review_audio.name}")
        if summary_audio:
            print(f"   Summary 오디오: {summary_audio.name}")
        else:
            print(f"   Summary 오디오: 없음 (review만 사용)")
        
        try:
            maker = VideoMaker(resolution=(1920, 1080), fps=30)
            
            # summary audio가 있으면 포함, 없으면 review만 사용
            summary_audio_path = str(summary_audio) if summary_audio else None
            
            maker.create_video(
                audio_path=str(review_audio),
                image_dir=image_dir,
                output_path=output_path,
                add_subtitles_flag=False,
                language=lang,
                summary_audio_path=summary_audio_path
            )
            
            print(f"✅ {lang.upper()} 영상 생성 완료: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ {lang.upper()} 영상 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_and_save_metadata(
        self,
        video_path: Path,
        lang: str,
        thumbnail_path: Optional[str] = None
    ) -> Optional[Path]:
        """metadata 생성 및 저장"""
        print(f"\n📋 {lang.upper()} 메타데이터 생성 중...")
        
        try:
            # 메타데이터 생성
            title = generate_title(self.book_title, lang=lang)
            description = generate_description(self.book_info, lang=lang, book_title=self.book_title)
            tags = generate_tags(book_title=self.book_title, book_info=self.book_info, lang=lang)
            
            # 메타데이터 저장
            metadata_path = save_metadata(
                video_path,
                title,
                description,
                tags,
                lang,
                self.book_info,
                thumbnail_path
            )
            
            print(f"✅ {lang.upper()} 메타데이터 저장 완료: {metadata_path.name}")
            return metadata_path
            
        except Exception as e:
            print(f"❌ {lang.upper()} 메타데이터 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_thumbnail(
        self,
        lang: str,
        use_dalle: bool = False,
        background_image_path: Optional[str] = None
    ) -> Optional[str]:
        """thumbnail 생성"""
        print(f"\n🖼️ {lang.upper()} 썸네일 생성 중...")
        
        try:
            generator = ThumbnailGenerator(use_dalle=use_dalle)
            
            # 배경 이미지 찾기
            if not background_image_path and not use_dalle:
                image_dir = Path("assets/images") / self.safe_title
                if image_dir.exists():
                    mood_images = sorted(image_dir.glob("mood_*.jpg"))
                    if mood_images:
                        background_image_path = str(mood_images[0])
            
            # 썸네일 제목 설정
            book_title = self.book_title
            author = self.author or ""
            
            if lang == "en":
                # 영어 제목으로 변환
                book_title = translate_book_title(self.book_title)
            
            output_path = f"output/{self.safe_title}_thumbnail_{lang}.jpg"
            
            thumbnail_path = generator.generate_thumbnail(
                book_title=book_title,
                author=author,
                lang=lang,
                background_image_path=background_image_path,
                output_path=output_path
            )
            
            print(f"✅ {lang.upper()} 썸네일 생성 완료: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            print(f"❌ {lang.upper()} 썸네일 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """thumbnail 업로드"""
        try:
            uploader = ThumbnailUploader()
            return uploader.upload_thumbnail(video_id, thumbnail_path)
        except Exception as e:
            print(f"⚠️ 썸네일 업로드 실패 (나중에 수동으로 업로드 가능): {e}")
            return False
    
    def run_complete_pipeline(
        self,
        book_title: str,
        author: Optional[str] = None,
        skip_video: bool = False,
        skip_thumbnail: bool = False,
        skip_thumbnail_upload: bool = True,  # 기본값: 업로드 안 함 (사용자가 나중에 할 수 있도록)
        use_dalle_thumbnail: bool = False,
        languages: List[str] = None
    ):
        """
        전체 파이프라인 실행
        
        Args:
            book_title: 책 제목
            author: 작가 이름 (선택사항)
            skip_video: 영상 생성 건너뛰기
            skip_thumbnail: 썸네일 생성 건너뛰기
            skip_thumbnail_upload: 썸네일 업로드 건너뛰기 (기본값: True, 업로드는 나중에)
            use_dalle_thumbnail: DALL-E를 사용하여 썸네일 배경 생성
            languages: 처리할 언어 리스트 (None이면 자동 감지)
        """
        self.book_title = book_title
        self.author = author
        
        # 안전한 파일명 생성
        self.safe_title = safe_title(book_title)
        
        # 책 정보 로드
        self.book_info = load_book_info(book_title)
        if self.book_info and not author:
            authors = self.book_info.get('authors', [])
            if authors:
                self.author = ', '.join(authors)
        
        print("=" * 60)
        print("🚀 완전 자동화 파이프라인 시작")
        print("=" * 60)
        print(f"📚 책: {book_title}")
        if self.author:
            print(f"✍️ 저자: {self.author}")
        print()
        
        # 오디오 파일 찾기
        print("🔍 오디오 파일 찾는 중...")
        audio_files = self.find_audio_files(book_title)
        
        # 디버깅: 찾은 파일 출력
        print(f"   찾은 파일:")
        print(f"   KO - Review: {audio_files['ko']['review']}")
        print(f"   KO - Summary: {audio_files['ko']['summary']}")
        print(f"   EN - Review: {audio_files['en']['review']}")
        print(f"   EN - Summary: {audio_files['en']['summary']}")
        
        # 처리할 언어 결정
        if languages is None:
            languages = []
            if audio_files['ko']['review'] or audio_files['ko']['summary']:
                languages.append('ko')
            if audio_files['en']['review'] or audio_files['en']['summary']:
                languages.append('en')
        
        if not languages:
            print("❌ 처리할 오디오 파일을 찾을 수 없습니다.")
            print("   assets/audio/ 폴더에 오디오 파일이 있는지 확인하세요.")
            return
        
        print(f"✅ 발견된 언어: {', '.join(languages)}")
        print()
        
        # 이미지 디렉토리
        image_dir = f"assets/images/{self.safe_title}"
        if not Path(image_dir).exists():
            print(f"⚠️ 이미지 디렉토리를 찾을 수 없습니다: {image_dir}")
            print("   이미지가 없어도 영상 생성은 가능하지만, 이미지가 없으면 검은 화면이 표시됩니다.")
        
        results = {
            'ko': {'video': None, 'metadata': None, 'thumbnail': None},
            'en': {'video': None, 'metadata': None, 'thumbnail': None}
        }
        
        # 각 언어별로 처리
        for lang in languages:
            print("\n" + "=" * 60)
            print(f"🌐 {lang.upper()} 언어 처리 시작")
            print("=" * 60)
            
            review_audio = audio_files[lang]['review']
            summary_audio = audio_files[lang]['summary']
            
            if not review_audio:
                print(f"⚠️ {lang.upper()} review 오디오를 찾을 수 없습니다. 건너뜁니다.")
                continue
            
            # Summary 오디오가 없으면 자동 생성
            if not summary_audio:
                print(f"\n📚 {lang.upper()} Summary 오디오가 없습니다. 자동 생성합니다...")
                try:
                    # 언어별 책 제목과 저자 설정
                    if lang == "en":
                        summary_book_title = translate_book_title(self.book_title)
                        summary_author = translate_author_name(self.author) if self.author else None
                    else:
                        summary_book_title = self.book_title
                        summary_author = self.author
                    
                    # 요약 텍스트 생성 (Hook → Summary → Bridge 구조)
                    print(f"   📝 요약 텍스트 생성 중...")
                    summary_text = self.summary_generator.generate_summary(
                        book_title=summary_book_title,
                        author=summary_author,
                        language=lang,
                        duration_minutes=5.0,
                        use_engaging_opening=True  # Hook → Summary → Bridge 구조 사용
                    )
                    
                    # 요약 텍스트 저장
                    summary_text_path = self.summary_generator.save_summary(
                        summary=summary_text,
                        book_title=self.book_title,
                        language=lang
                    )
                    
                    # TTS로 요약 음성 생성
                    print(f"   🎤 TTS 요약 음성 생성 중...")
                    lang_suffix = "ko" if lang == "ko" else "en"
                    summary_audio_path = f"assets/audio/{self.safe_title}_summary_{lang_suffix}.mp3"
                    
                    # 한국어는 nova, 영어는 alloy
                    voice = "nova" if lang == "ko" else "alloy"
                    
                    self.tts_engine.generate_speech(
                        text=summary_text,
                        output_path=summary_audio_path,
                        voice=voice,
                        language=lang,
                        model="tts-1-hd"
                    )
                    
                    summary_audio = Path(summary_audio_path)
                    print(f"   ✅ Summary 오디오 생성 완료: {summary_audio.name}")
                    
                except Exception as e:
                    print(f"   ❌ Summary 생성 실패: {e}")
                    print(f"   ⚠️ Summary 없이 review만 사용하여 영상을 제작합니다.")
                    summary_audio = None
            
            # 영상 생성
            if not skip_video:
                # 출력 파일명 결정 (summary 포함 여부에 따라)
                if summary_audio:
                    output_filename = f"{self.safe_title}_review_with_summary_{lang}.mp4"
                else:
                    output_filename = f"{self.safe_title}_review_{lang}.mp4"
                
                output_path = f"output/{output_filename}"
                
                success = self.create_video_with_summary(
                    lang=lang,
                    review_audio=review_audio,
                    summary_audio=summary_audio,
                    image_dir=image_dir,
                    output_path=output_path
                )
                
                if success:
                    results[lang]['video'] = Path(output_path)
            else:
                # 영상 생성 건너뛰기 - 기존 영상 찾기
                possible_names = [
                    f"{self.safe_title}_review_with_summary_{lang}.mp4",
                    f"{self.safe_title}_review_{lang}.mp4"
                ]
                for name in possible_names:
                    video_path = Path(f"output/{name}")
                    if video_path.exists():
                        results[lang]['video'] = video_path
                        print(f"✅ 기존 영상 발견: {video_path.name}")
                        break
            
            # 썸네일 생성
            thumbnail_path = None
            if not skip_thumbnail:
                thumbnail_path = self.generate_thumbnail(
                    lang=lang,
                    use_dalle=use_dalle_thumbnail
                )
                results[lang]['thumbnail'] = thumbnail_path
            
            # 메타데이터 생성 및 저장
            if results[lang]['video']:
                metadata_path = self.generate_and_save_metadata(
                    video_path=results[lang]['video'],
                    lang=lang,
                    thumbnail_path=thumbnail_path
                )
                results[lang]['metadata'] = metadata_path
            
            # 썸네일 업로드 (선택사항, 기본값: 건너뛰기)
            if not skip_thumbnail_upload and thumbnail_path and results[lang].get('video_id'):
                print(f"\n📤 {lang.upper()} 썸네일 업로드 중...")
                self.upload_thumbnail(results[lang]['video_id'], thumbnail_path)
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 파이프라인 실행 결과")
        print("=" * 60)
        
        for lang in languages:
            print(f"\n🌐 {lang.upper()}:")
            if results[lang]['video']:
                print(f"   ✅ 영상: {results[lang]['video'].name}")
            else:
                print(f"   ⚠️ 영상: 생성되지 않음")
            
            if results[lang]['metadata']:
                print(f"   ✅ 메타데이터: {results[lang]['metadata'].name}")
            else:
                print(f"   ⚠️ 메타데이터: 생성되지 않음")
            
            if results[lang]['thumbnail']:
                print(f"   ✅ 썸네일: {Path(results[lang]['thumbnail']).name}")
            else:
                print(f"   ⚠️ 썸네일: 생성되지 않음")
        
        print("\n" + "=" * 60)
        print("✅ 파이프라인 완료!")
        print("=" * 60)
        print("\n📝 다음 단계:")
        print("   1. 생성된 metadata 파일을 확인하세요: output/*.metadata.json")
        print("   2. 영상이 마음에 들면 업로드하세요: python src/09_upload_from_metadata.py")
        print("   3. 썸네일이 없으면 업로드하세요: python src/11_upload_thumbnails.py")
        print()


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='완전 자동화 파이프라인 (영상 생성 + 메타데이터 + 썸네일)')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--skip-video', action='store_true', help='영상 생성 건너뛰기 (메타데이터만 생성)')
    parser.add_argument('--skip-thumbnail', action='store_true', help='썸네일 생성 건너뛰기')
    parser.add_argument('--skip-thumbnail-upload', action='store_true', default=True, help='썸네일 업로드 건너뛰기 (기본값: True)')
    parser.add_argument('--upload-thumbnail', action='store_true', help='썸네일 업로드 (video_id 필요, 업로드 후 사용)')
    parser.add_argument('--use-dalle-thumbnail', action='store_true', help='DALL-E를 사용하여 썸네일 배경 생성')
    parser.add_argument('--languages', nargs='+', choices=['ko', 'en'], help='처리할 언어 (지정하지 않으면 자동 감지)')
    
    args = parser.parse_args()
    
    # 썸네일 업로드 옵션 처리
    skip_thumbnail_upload = not args.upload_thumbnail
    
    pipeline = CompletePipeline()
    pipeline.run_complete_pipeline(
        book_title=args.book_title,
        author=args.author,
        skip_video=args.skip_video,
        skip_thumbnail=args.skip_thumbnail,
        skip_thumbnail_upload=skip_thumbnail_upload,
        use_dalle_thumbnail=args.use_dalle_thumbnail,
        languages=args.languages
    )


if __name__ == "__main__":
    main()




