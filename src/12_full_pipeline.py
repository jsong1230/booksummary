"""
전체 파이프라인 통합 스크립트
책 제목을 받아서 URL 수집 → 이미지 다운로드 → 영상 생성 → 썸네일 생성까지 자동 실행
(업로드는 제외)
"""

import sys
import os
from pathlib import Path
from typing import Optional

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


class FullPipeline:
    """전체 파이프라인 실행 클래스"""
    
    def __init__(self):
        self.book_title = None
        self.author = None
        self.safe_title = None
        
    def run_step_1_collect_urls(self, num_urls: int = 30) -> bool:
        """1단계: URL 수집 (한글/영어 반반)"""
        print("\n" + "=" * 60)
        print("📚 1단계: NotebookLM용 URL 수집 (한글/영어 반반)")
        print("=" * 60)
        
        try:
            # NotebookLM URL 수집 모듈 import
            import importlib.util
            collector_path = Path(__file__).parent.parent / "scripts" / "collect_urls_for_notebooklm.py"
            spec = importlib.util.spec_from_file_location("collect_urls", collector_path)
            collector_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(collector_module)
            
            collector = collector_module.NotebookLMURLCollector()
            ko_urls, en_urls = collector.search_urls_bilingual(
                self.book_title, 
                self.author, 
                num_urls
            )
            
            if ko_urls or en_urls:
                result = collector.save_urls_bilingual(
                    self.book_title,
                    ko_urls,
                    en_urls,
                    author=self.author
                )
                print(f"✅ URL 수집 완료: {result['md_path']}")
                return True
            else:
                print("⚠️ 수집된 URL이 없습니다.")
                return False
                
        except Exception as e:
            print(f"❌ URL 수집 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_step_2_download_images(self, num_mood_images: int = 20) -> bool:
        """2단계: 이미지 다운로드"""
        print("\n" + "=" * 60)
        print("🖼️ 2단계: 이미지 다운로드")
        print("=" * 60)
        
        try:
            # 이미지 다운로드 모듈 import
            import importlib.util
            images_path = Path(__file__).parent / "02_get_images.py"
            spec = importlib.util.spec_from_file_location("get_images", images_path)
            images_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(images_module)
            
            downloader = images_module.ImageDownloader()
            result = downloader.download_all(
                book_title=self.book_title,
                author=self.author,
                keywords=None,  # AI가 자동 생성
                num_mood_images=num_mood_images,
                skip_cover=False
            )
            
            if result.get('mood_images'):
                print(f"✅ 이미지 다운로드 완료: {len(result['mood_images'])}개")
                return True
            else:
                print("⚠️ 다운로드된 이미지가 없습니다.")
                return False
                
        except Exception as e:
            print(f"❌ 이미지 다운로드 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_step_3_create_videos(self, skip_thumbnail: bool = False, use_dalle: bool = False) -> bool:
        """3단계: 영상 생성 (한글/영어 각각) 및 썸네일 생성"""
        print("\n" + "=" * 60)
        print("🎬 3단계: 영상 생성 및 썸네일 생성")
        print("=" * 60)
        
        try:
            # 영상 생성 모듈 import
            import importlib.util
            video_path = Path(__file__).parent / "08_create_and_preview_videos.py"
            spec = importlib.util.spec_from_file_location("create_videos", video_path)
            video_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(video_module)
            
            # 오디오 파일 찾기
            korean_audio, english_audio = video_module.find_audio_files()
            
            if not korean_audio and not english_audio:
                print("⚠️ 오디오 파일을 찾을 수 없습니다.")
                print("   NotebookLM에서 오디오를 생성하고 assets/audio/ 폴더에 저장해주세요.")
                return False
            
            # 책 정보 로드
            book_info = video_module.load_book_info(self.book_title)
            
            # 이미지 디렉토리
            image_dir = f"assets/images/{self.safe_title}"
            
            videos_created = []
            
            # 한글 영상 제작
            if korean_audio:
                print(f"\n🇰🇷 한글 영상 생성 중...")
                print(f"   오디오: {korean_audio.name}")
                
                output_path = f"output/{self.safe_title}_review_ko.mp4"
                
                # 영상 생성
                maker = video_module.VideoMaker(resolution=(1920, 1080), fps=30)
                maker.create_video(
                    audio_path=str(korean_audio),
                    image_dir=image_dir,
                    output_path=output_path,
                    add_subtitles_flag=False,
                    language="ko"
                )
                videos_created.append(output_path)
                
                # 메타데이터 생성
                title = video_module.generate_title(self.book_title, lang="ko")
                description = video_module.generate_description(book_info, lang="ko", book_title=self.book_title)
                tags = video_module.generate_tags(self.book_title, book_info, lang="ko")
                
                # 썸네일 생성
                thumbnail_path = None
                if not skip_thumbnail:
                    thumbnail_path = self.run_step_4_generate_thumbnail("ko", use_dalle)
                
                # 메타데이터 저장
                metadata_path = video_module.save_metadata(
                    Path(output_path),
                    title,
                    description,
                    tags,
                    "ko",
                    book_info,
                    thumbnail_path
                )
                print(f"✅ 한글 영상 완료: {output_path}")
                print(f"   메타데이터: {metadata_path}")
            
            # 영어 영상 제작
            if english_audio:
                print(f"\n🇺🇸 영어 영상 생성 중...")
                print(f"   오디오: {english_audio.name}")
                
                output_path = f"output/{self.safe_title}_review_en.mp4"
                
                # 영상 생성
                maker = video_module.VideoMaker(resolution=(1920, 1080), fps=30)
                maker.create_video(
                    audio_path=str(english_audio),
                    image_dir=image_dir,
                    output_path=output_path,
                    add_subtitles_flag=False,
                    language="en"
                )
                videos_created.append(output_path)
                
                # 메타데이터 생성
                title = video_module.generate_title(self.book_title, lang="en")
                description = video_module.generate_description(book_info, lang="en", book_title=self.book_title)
                tags = video_module.generate_tags(self.book_title, book_info, lang="en")
                
                # 썸네일 생성
                thumbnail_path = None
                if not skip_thumbnail:
                    thumbnail_path = self.run_step_4_generate_thumbnail("en", use_dalle)
                
                # 메타데이터 저장
                metadata_path = video_module.save_metadata(
                    Path(output_path),
                    title,
                    description,
                    tags,
                    "en",
                    book_info,
                    thumbnail_path
                )
                print(f"✅ 영어 영상 완료: {output_path}")
                print(f"   메타데이터: {metadata_path}")
            
            if videos_created:
                print(f"\n✅ 총 {len(videos_created)}개의 영상 생성 완료")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ 영상 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_step_4_generate_thumbnail(self, lang: str, use_dalle: bool = False) -> Optional[str]:
        """4단계: 썸네일 생성"""
        try:
            # 썸네일 생성 모듈 import
            import importlib.util
            thumbnail_path = Path(__file__).parent / "10_generate_thumbnail.py"
            spec = importlib.util.spec_from_file_location("generate_thumbnail", thumbnail_path)
            thumbnail_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(thumbnail_module)
            
            # 배경 이미지 찾기 (무드 이미지 중 하나)
            background_image = None
            if not use_dalle:
                image_dir = Path("assets/images") / self.safe_title
                if image_dir.exists():
                    mood_images = sorted(image_dir.glob("mood_*.jpg"))
                    if mood_images:
                        background_image = str(mood_images[0])
            
            generator = thumbnail_module.ThumbnailGenerator(use_dalle=use_dalle)
            output_path = f"output/{self.safe_title}_thumbnail_{lang}.jpg"
            
            thumbnail_path = generator.generate_thumbnail(
                book_title=self.book_title,
                author=self.author or "",
                lang=lang,
                background_image_path=background_image,
                output_path=output_path
            )
            
            if thumbnail_path:
                print(f"   ✅ 썸네일 생성 완료: {thumbnail_path}")
                return thumbnail_path
            else:
                print(f"   ⚠️ 썸네일 생성 실패")
                return None
                
        except Exception as e:
            print(f"   ⚠️ 썸네일 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_full_pipeline(
        self,
        book_title: str,
        author: Optional[str] = None,
        num_urls: int = 30,
        num_mood_images: int = 20,
        skip_urls: bool = False,
        skip_images: bool = False,
        skip_videos: bool = False,
        skip_thumbnail: bool = False,
        use_dalle_thumbnail: bool = False
    ):
        """전체 파이프라인 실행"""
        self.book_title = book_title
        self.author = author
        
        # 안전한 파일명 생성
        from utils.file_utils import safe_title
        self.safe_title = safe_title(book_title)
        
        print("=" * 60)
        print("🚀 전체 파이프라인 시작")
        print("=" * 60)
        print(f"📚 책: {book_title}")
        if author:
            print(f"✍️ 저자: {author}")
        print()
        
        results = {
            'urls': False,
            'images': False,
            'videos': False
        }
        
        # 1단계: URL 수집
        if not skip_urls:
            results['urls'] = self.run_step_1_collect_urls(num_urls)
        else:
            print("\n⏭️ URL 수집 건너뛰기")
        
        # 2단계: 이미지 다운로드
        if not skip_images:
            results['images'] = self.run_step_2_download_images(num_mood_images)
        else:
            print("\n⏭️ 이미지 다운로드 건너뛰기")
        
        # 3단계: 영상 생성 및 썸네일
        if not skip_videos:
            results['videos'] = self.run_step_3_create_videos(
                skip_thumbnail=skip_thumbnail,
                use_dalle=use_dalle_thumbnail
            )
        else:
            print("\n⏭️ 영상 생성 건너뛰기")
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 파이프라인 실행 결과")
        print("=" * 60)
        print(f"✅ URL 수집: {'성공' if results['urls'] else '건너뛰기/실패'}")
        print(f"✅ 이미지 다운로드: {'성공' if results['images'] else '건너뛰기/실패'}")
        print(f"✅ 영상 생성: {'성공' if results['videos'] else '건너뛰기/실패'}")
        print()
        
        if all(results.values()):
            print("🎉 전체 파이프라인 완료!")
        else:
            print("⚠️ 일부 단계가 실패했거나 건너뛰었습니다.")
        print()


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='전체 파이프라인 통합 실행 (업로드 제외)')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--num-urls', type=int, default=30, help='수집할 URL 개수 (기본값: 30)')
    parser.add_argument('--num-mood-images', type=int, default=20, help='무드 이미지 개수 (기본값: 20)')
    parser.add_argument('--skip-urls', action='store_true', help='URL 수집 건너뛰기')
    parser.add_argument('--skip-images', action='store_true', help='이미지 다운로드 건너뛰기')
    parser.add_argument('--skip-videos', action='store_true', help='영상 생성 건너뛰기')
    parser.add_argument('--skip-thumbnail', action='store_true', help='썸네일 생성 건너뛰기')
    parser.add_argument('--use-dalle-thumbnail', action='store_true', help='DALL-E를 사용하여 썸네일 배경 생성')
    
    args = parser.parse_args()
    
    pipeline = FullPipeline()
    pipeline.run_full_pipeline(
        book_title=args.book_title,
        author=args.author,
        num_urls=args.num_urls,
        num_mood_images=args.num_mood_images,
        skip_urls=args.skip_urls,
        skip_images=args.skip_images,
        skip_videos=args.skip_videos,
        skip_thumbnail=args.skip_thumbnail,
        use_dalle_thumbnail=args.use_dalle_thumbnail
    )


if __name__ == "__main__":
    main()

