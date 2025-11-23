"""
YouTube에 영상을 자동으로 업로드하는 스크립트
OAuth2를 사용하여 인증하고, 영상 메타데이터를 설정하여 업로드합니다.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("⚠️ google-api-python-client가 설치되지 않았습니다.")

# 환경 변수 로드
load_dotenv()

# YouTube API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeUploader:
    """YouTube에 영상을 업로드하는 클래스"""
    
    def __init__(self):
        """YouTube API 클라이언트 초기화"""
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")
        
        self.client_id = os.getenv("YOUTUBE_CLIENT_ID")
        self.client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("YouTube API 자격증명이 .env 파일에 설정되지 않았습니다.")
        
        self.youtube = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth2 인증 및 YouTube API 클라이언트 생성"""
        try:
            # Refresh token을 사용하여 Credentials 생성
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=SCOPES
            )
            
            # Access token 갱신
            credentials.refresh(Request())
            
            # YouTube API 클라이언트 생성
            self.youtube = build('youtube', 'v3', credentials=credentials)
            print("✅ YouTube API 인증 성공")
            
        except Exception as e:
            print(f"❌ YouTube API 인증 실패: {e}")
            raise
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list = None,
        category_id: str = "22",  # People & Blogs
        privacy_status: str = "private",  # private, unlisted, public
        thumbnail_path: Optional[str] = None,
        lang: str = "both"  # "ko", "en", "both"
    ) -> Optional[Dict]:
        """
        YouTube에 영상을 업로드합니다.
        
        Args:
            video_path: 업로드할 영상 파일 경로
            title: 영상 제목
            description: 영상 설명
            tags: 태그 리스트
            category_id: 카테고리 ID (기본값: 22 - People & Blogs)
            privacy_status: 공개 설정 (private, unlisted, public)
            thumbnail_path: 썸네일 이미지 경로 (선택사항)
            
        Returns:
            업로드된 영상 정보 딕셔너리
        """
        if not os.path.exists(video_path):
            print(f"❌ 영상 파일을 찾을 수 없습니다: {video_path}")
            return None
        
        video_file = Path(video_path)
        file_size = video_file.stat().st_size
        
        print(f"📤 YouTube 업로드 시작: {title}")
        print(f"   파일: {video_path}")
        print(f"   크기: {file_size / (1024*1024):.2f} MB")
        
        # 영상 메타데이터 설정
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': privacy_status,
                'selfDeclaredMadeForKids': False
            }
        }
        
        try:
            # 영상 업로드
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
            
            # 업로드 실행
            response = self._resumable_upload(insert_request)
            
            video_id = response['id']
            print(f"✅ 업로드 완료!")
            print(f"   영상 ID: {video_id}")
            print(f"   URL: https://www.youtube.com/watch?v={video_id}")
            
            # 썸네일 업로드 (선택사항)
            if thumbnail_path and os.path.exists(thumbnail_path):
                print(f"🖼️ 썸네일 업로드 중...")
                self.upload_thumbnail(video_id, thumbnail_path)
            
            return {
                'video_id': video_id,
                'title': title,
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'privacy_status': privacy_status
            }
            
        except HttpError as e:
            print(f"❌ YouTube API 오류: {e}")
            if e.resp.status == 403:
                print("   권한이 없습니다. OAuth2 스코프를 확인하세요.")
            return None
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return None
    
    def _resumable_upload(self, insert_request):
        """재개 가능한 업로드 실행"""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                print("   업로드 진행 중...", end='\r')
                status, response = insert_request.next_chunk()
                if response is not None:
                    if 'id' in response:
                        print("   업로드 완료!      ")
                        return response
                    else:
                        raise Exception(f"업로드 실패: {response}")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"재시도 가능한 오류 ({e.resp.status}): {e}"
                else:
                    raise
            except Exception as e:
                error = f"업로드 오류: {e}"
            
            if error is not None:
                print(f"   {error}")
                retry += 1
                if retry > 3:
                    raise Exception("업로드 재시도 횟수 초과")
                print(f"   재시도 중... ({retry}/3)")
        
        return response
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str):
        """영상 썸네일 업로드"""
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
        print("❌ google-api-python-client가 설치되지 않았습니다.")
        print("   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return
    
    print("=" * 60)
    print("📺 YouTube 자동 업로드")
    print("=" * 60)
    print()
    
    try:
        uploader = YouTubeUploader()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 영상 파일 경로 입력
    video_path = input("업로드할 영상 파일 경로: ").strip()
    if not video_path or not os.path.exists(video_path):
        print("❌ 영상 파일을 찾을 수 없습니다.")
        return
    
    # 언어 설정
    lang = input("언어 설정 (ko/en/both, 기본값: both): ").strip().lower()
    if lang not in ['ko', 'en', 'both']:
        lang = 'both'
    
    # 영상 정보 입력
    if lang == "both":
        title_ko = input("영상 제목 (한글): ").strip()
        title_en = input("영상 제목 (영문, 선택사항): ").strip()
        title = f"{title_ko} | {title_en}" if title_en else title_ko
    elif lang == "ko":
        title = input("영상 제목 (한글): ").strip()
    else:  # en
        title = input("영상 제목 (영문): ").strip()
    
    if not title:
        print("❌ 영상 제목을 입력해주세요.")
        return
    
    if lang == "both":
        description_ko = input("영상 설명 (한글, 선택사항): ").strip()
        description_en = input("영상 설명 (영문, 선택사항): ").strip()
        if description_ko and description_en:
            description = f"{description_ko}\n\n{'='*60}\n\n{description_en}"
        elif description_ko:
            description = description_ko
        elif description_en:
            description = description_en
        else:
            description = ""
    else:
        description = input("영상 설명 (선택사항): ").strip()
    
    tags_input = input("태그 (쉼표로 구분, 선택사항): ").strip()
    if tags_input:
        tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
    else:
        # 기본 태그 생성
        if lang == "ko":
            tags = ['책리뷰', '독서', '북튜버', '책추천']
        elif lang == "en":
            tags = ['BookReview', 'Reading', 'BookTube', 'BookRecommendation']
        else:  # both
            tags = ['책리뷰', '독서', '북튜버', '책추천', 'BookReview', 'Reading', 'BookTube', 'BookRecommendation']
    
    privacy = input("공개 설정 (private/unlisted/public, 기본값: private): ").strip().lower()
    if privacy not in ['private', 'unlisted', 'public']:
        privacy = 'private'
    
    thumbnail_path = input("썸네일 이미지 경로 (선택사항): ").strip() or None
    
    print()
    
    # 업로드 실행
    result = uploader.upload_video(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        privacy_status=privacy,
        thumbnail_path=thumbnail_path,
        lang=lang
    )
    
    if result:
        print()
        print("=" * 60)
        print("✅ 업로드 완료!")
        print("=" * 60)
        print(f"영상 URL: {result['url']}")
        print(f"영상 ID: {result['video_id']}")
    else:
        print()
        print("❌ 업로드 실패")


if __name__ == "__main__":
    main()

