"""
책 리뷰 영상 자동 생성 및 YouTube 업로드 통합 스크립트
output/ 폴더의 영상을 자동으로 YouTube에 업로드합니다.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

# 환경 변수 로드
load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class AutoYouTubeUploader:
    """자동 YouTube 업로더"""
    
    def __init__(self):
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")
        
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다.")
        
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth2 인증"""
        try:
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            credentials.refresh(Request())
            self.youtube = build('youtube', 'v3', credentials=credentials)
            print("✅ YouTube API 인증 성공")
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise
    
    def find_videos(self, output_dir: str = "output") -> list:
        """output 디렉토리에서 업로드할 영상 찾기"""
        output_path = Path(output_dir)
        if not output_path.exists():
            return []
        
        videos = []
        for video_file in output_path.glob("*.mp4"):
            # 이미 업로드된 영상인지 확인 (메타데이터 파일)
            metadata_file = video_file.with_suffix('.json')
            if not metadata_file.exists():
                videos.append(video_file)
        
        return videos
    
    def detect_language_from_filename(self, filename: str) -> str:
        """파일명에서 언어 감지"""
        filename_lower = filename.lower()
        
        if '_ko' in filename_lower or '_korean' in filename_lower:
            return "ko"
        elif '_en' in filename_lower or '_english' in filename_lower or '_eng' in filename_lower:
            return "en"
        else:
            # 한글 포함 여부로 판단
            has_korean = any(ord(c) > 127 for c in filename)
            return "ko" if has_korean else "en"
    
    def load_book_info(self, video_path: Path) -> Optional[Dict]:
        """책 정보 로드 (assets/images/{책제목}/book_info.json)"""
        video_name = video_path.stem
        # 영상 이름에서 책 제목 추출 (예: "사피엔스_review_ko.mp4" -> "사피엔스")
        book_title = video_name.replace('_review_ko', '').replace('_review_en', '').replace('_review', '').replace('_Review', '')
        
        book_info_path = Path("assets/images") / book_title / "book_info.json"
        if book_info_path.exists():
            with open(book_info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def generate_title(self, book_title: str, lang: str = "both") -> str:
        """
        영상 제목 생성 (한글/영문 지원)
        
        Args:
            book_title: 책 제목
            lang: 언어 설정 ("ko", "en", "both")
        """
        if lang == "ko":
            return f"{book_title} 책 리뷰 | 일당백 스타일"
        elif lang == "en":
            return f"{book_title} Book Review | Auto-Generated"
        else:  # both
            return f"{book_title} 책 리뷰 | Book Review | 일당백 스타일"
    
    def generate_description(self, book_info: Optional[Dict] = None, lang: str = "both") -> str:
        """
        영상 설명 생성 (한글/영문 지원)
        
        Args:
            book_info: 책 정보 딕셔너리
            lang: 언어 설정 ("ko", "en", "both")
        """
        if lang == "ko":
            return self._generate_description_ko(book_info)
        elif lang == "en":
            return self._generate_description_en(book_info)
        else:  # both
            ko_desc = self._generate_description_ko(book_info)
            en_desc = self._generate_description_en(book_info)
            return f"{ko_desc}\n\n{'='*60}\n\n{en_desc}"
    
    def _generate_description_ko(self, book_info: Optional[Dict] = None) -> str:
        """한글 설명 생성"""
        description = """📚 책 리뷰 영상

이 영상은 NotebookLM과 AI를 활용하여 자동으로 생성되었습니다.

"""
        if book_info:
            if book_info.get('description'):
                description += f"📖 책 소개:\n{book_info['description'][:500]}...\n\n"
            if book_info.get('authors'):
                description += f"✍️ 작가: {', '.join(book_info['authors'])}\n"
            if book_info.get('publishedDate'):
                description += f"📅 출간일: {book_info['publishedDate']}\n"
        
        description += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 구독과 좋아요는 영상 제작에 큰 힘이 됩니다!
💬 댓글로 여러분의 생각을 공유해주세요.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#책리뷰 #독서 #북튜버 #책추천 #BookReview #Reading
"""
        return description
    
    def _generate_description_en(self, book_info: Optional[Dict] = None) -> str:
        """영문 설명 생성"""
        description = """📚 Book Review Video

This video was automatically generated using NotebookLM and AI.

"""
        if book_info:
            if book_info.get('description'):
                description += f"📖 Book Introduction:\n{book_info['description'][:500]}...\n\n"
            if book_info.get('authors'):
                description += f"✍️ Author: {', '.join(book_info['authors'])}\n"
            if book_info.get('publishedDate'):
                description += f"📅 Published: {book_info['publishedDate']}\n"
        
        description += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe and like to support video creation!
💬 Share your thoughts in the comments.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BookReview #Reading #BookTube #BookRecommendation #책리뷰 #독서
"""
        return description
    
    def generate_tags(self, lang: str = "both") -> list:
        """
        태그 생성 (한글/영문 지원)
        
        Args:
            lang: 언어 설정 ("ko", "en", "both")
        """
        ko_tags = ['책리뷰', '독서', '북튜버', '책추천', '일당백', '독서법', '책읽기']
        en_tags = ['BookReview', 'Reading', 'BookTube', 'BookRecommendation', 'BookReview', 'ReadingTips', 'Books']
        
        if lang == "ko":
            return ko_tags
        elif lang == "en":
            return en_tags
        else:  # both
            return ko_tags + en_tags
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        privacy_status: str = "private",
        thumbnail_path: Optional[str] = None,
        lang: str = "both"
    ) -> Optional[Dict]:
        """영상 업로드"""
        if not os.path.exists(video_path):
            return None
        
        video_file = Path(video_path)
        file_size = video_file.stat().st_size
        
        print(f"📤 업로드 중: {title}")
        print(f"   파일 크기: {file_size / (1024*1024):.2f} MB")
        
        # 태그가 없으면 언어에 맞게 생성
        if not tags:
            tags = self.generate_tags(lang)
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        try:
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            insert_request = self.youtube.videos().insert(
                part=','.join(['snippet', 'status']),
                body=body,
                media_body=media
            )
            
            response = self._resumable_upload(insert_request)
            video_id = response['id']
            
            # 썸네일 업로드
            if thumbnail_path and os.path.exists(thumbnail_path):
                self.upload_thumbnail(video_id, thumbnail_path)
            elif video_file.parent / f"{video_file.stem}_thumbnail.jpg".exists():
                thumbnail = video_file.parent / f"{video_file.stem}_thumbnail.jpg"
                self.upload_thumbnail(video_id, str(thumbnail))
            
            # 업로드 정보 저장
            metadata = {
                'video_id': video_id,
                'title': title,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'privacy_status': privacy_status,
                'uploaded_at': str(Path(video_path).stat().st_mtime)
            }
            metadata_file = video_file.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 업로드 완료: {metadata['url']}")
            return metadata
            
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return None
    
    def _resumable_upload(self, insert_request):
        """재개 가능한 업로드"""
        response = None
        retry = 0
        
        while response is None:
            try:
                print("   진행 중...", end='\r')
                status, response = insert_request.next_chunk()
                if response and 'id' in response:
                    print("   완료!      ")
                    return response
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    retry += 1
                    if retry > 3:
                        raise
                    print(f"   재시도 중... ({retry}/3)")
                else:
                    raise
        
        return response
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """썸네일 업로드"""
        try:
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path)
            ).execute()
            print("   ✅ 썸네일 업로드 완료")
        except Exception as e:
            print(f"   ⚠️ 썸네일 업로드 실패: {e}")


def main():
    """메인 실행 함수"""
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("🚀 YouTube 자동 업로드")
    print("=" * 60)
    print()
    
    try:
        uploader = AutoYouTubeUploader()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 업로드할 영상 찾기
    videos = uploader.find_videos()
    
    if not videos:
        print("📭 업로드할 영상이 없습니다.")
        print("   output/ 폴더에 .mp4 파일이 있는지 확인하세요.")
        return
    
    print(f"📹 발견된 영상: {len(videos)}개\n")
    
    # 업로드 설정
    privacy = input("공개 설정 (private/unlisted/public, 기본값: private): ").strip().lower()
    if privacy not in ['private', 'unlisted', 'public']:
        privacy = 'private'
    
    lang = input("언어 설정 (ko/en/both/auto, 기본값: auto): ").strip().lower()
    if lang not in ['ko', 'en', 'both', 'auto']:
        lang = 'auto'
    
    auto_upload = input("자동으로 모든 영상을 업로드하시겠습니까? (y/n, 기본값: y): ").strip().lower()
    auto_upload = auto_upload != 'n'
    
    print()
    
    # 영상 업로드
    uploaded = []
    for i, video_path in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video_path.name}")
        
        # 책 정보 로드
        book_info = uploader.load_book_info(video_path)
        book_title = video_path.stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '').replace('_Review', '')
        
        # 파일명에서 언어 자동 감지 (lang이 지정되지 않았으면)
        if lang == "auto":
            detected_lang = uploader.detect_language_from_filename(video_path.stem)
            print(f"   📝 언어 자동 감지: {detected_lang}")
            lang = detected_lang
        
        # 제목 및 설명 생성 (언어 설정 반영)
        title = uploader.generate_title(book_title, lang=lang)
        description = uploader.generate_description(book_info, lang=lang)
        tags = uploader.generate_tags(lang=lang)
        
        if not auto_upload:
            confirm = input(f"  '{title}' 업로드하시겠습니까? (y/n): ").strip().lower()
            if confirm != 'y':
                print("  ⏭️ 건너뜀\n")
                continue
        
        # 썸네일 경로 확인
        # ⚠️ 책 표지는 저작권 문제로 썸네일로 사용하지 않습니다.
        # 대신 무드 이미지 중 하나를 사용하거나 썸네일을 생성해야 합니다.
        thumbnail = None
        # cover_path = Path("assets/images") / book_title / "cover.jpg"
        # if cover_path.exists():
        #     thumbnail = str(cover_path)
        # 
        # 대신 무드 이미지 중 첫 번째를 썸네일로 사용할 수 있습니다:
        mood_images = sorted((Path("assets/images") / book_title).glob("mood_*.jpg"))
        if mood_images:
            thumbnail = str(mood_images[0])
            print(f"   📸 썸네일: {mood_images[0].name} (저작권 없는 이미지)")
        
        # 업로드
        result = uploader.upload_video(
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy,
            thumbnail_path=thumbnail,
            lang=lang
        )
        
        if result:
            uploaded.append(result)
        
        print()
    
    # 결과 요약
    print("=" * 60)
    print(f"✅ 업로드 완료: {len(uploaded)}/{len(videos)}개")
    print("=" * 60)
    for result in uploaded:
        print(f"  • {result['title']}")
        print(f"    {result['url']}")


if __name__ == "__main__":
    main()

