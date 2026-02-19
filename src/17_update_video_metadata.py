"""
기존 YouTube 영상의 메타데이터 업데이트 스크립트
- 메타데이터 파일을 읽어서 YouTube에 업로드된 영상의 제목, 설명, 태그를 업데이트
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
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

load_dotenv()

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]


class YouTubeMetadataUpdater:
    """YouTube 영상 메타데이터 업데이터"""
    
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
    
    def _validate_and_clean_tags(self, tags: list) -> list:
        """태그 검증 및 정리 (YouTube 규칙 준수)"""
        MAX_TAG_LENGTH = 30
        MAX_TAGS = 500
        
        cleaned_tags = []
        for tag in tags:
            if not tag or not isinstance(tag, str):
                continue
            
            tag = tag.strip()
            if not tag:
                continue
            
            if len(tag) > MAX_TAG_LENGTH:
                print(f"   ⚠️ 태그 길이 초과 (30자): '{tag[:50]}...' (건너뜀)")
                continue
            
            import re
            if any(c in tag for c in ['<', '>', '&', '"', "'", '\n', '\r', '\t']):
                tag = re.sub(r'[<>&"\'\\n\\r\\t]', '', tag)
                if not tag.strip():
                    continue
            
            cleaned_tags.append(tag)
            
            if len(cleaned_tags) >= MAX_TAGS:
                break
        
        return cleaned_tags
    
    def _clean_description(self, description: str) -> str:
        """Description 정리"""
        MAX_DESCRIPTION_LENGTH = 5000
        if len(description) > MAX_DESCRIPTION_LENGTH:
            print(f"   ⚠️ Description이 너무 깁니다 ({len(description)}자). {MAX_DESCRIPTION_LENGTH}자로 자릅니다.")
            description = description[:MAX_DESCRIPTION_LENGTH]
        
        import re
        import unicodedata
        
        description = description.replace('\x00', '')
        description = description.replace('\r\n', '\n')
        description = description.replace('\r', '\n')
        description = description.replace('━', '-')
        description = description.replace('─', '-')
        
        cleaned_chars = []
        for char in description:
            code_point = ord(char)
            if code_point < 0xD800 or code_point > 0xDFFF:
                if code_point < 0x20 and char not in ['\n', '\t']:
                    continue
                if code_point <= 0x10FFFF:
                    cleaned_chars.append(char)
        description = ''.join(cleaned_chars)
        
        description = re.sub(r'[━─]{3,}', '---', description)
        description = re.sub(r'\n{4,}', '\n\n\n', description)
        description = description.strip()
        
        if not description or len(description.strip()) == 0:
            print("   ⚠️ Description이 비어있습니다. 기본 설명을 사용합니다.")
            description = "책 리뷰 영상입니다."
        
        return description
    
    def find_video_id_by_title(self, title: str) -> Optional[str]:
        """제목으로 video_id 찾기"""
        try:
            # 채널의 영상 목록 가져오기
            channel_id = os.getenv('YOUTUBE_CHANNEL_ID', 'UCxOcO_x_yW6sfg_FPUQVqYA')
            
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_response.get('items'):
                print(f"❌ 채널을 찾을 수 없습니다: {channel_id}")
                return None
            
            upload_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 플레이리스트에서 영상 검색
            next_page_token = None
            max_pages = 10  # 최대 10페이지 검색 (500개 영상)
            
            for page in range(max_pages):
                request_params = {
                    'part': 'snippet',
                    'playlistId': upload_playlist_id,
                    'maxResults': 50
                }
                
                if next_page_token:
                    request_params['pageToken'] = next_page_token
                
                playlist_response = self.youtube.playlistItems().list(**request_params).execute()
                
                for item in playlist_response.get('items', []):
                    video_title = item['snippet']['title']
                    if title in video_title or video_title in title:
                        video_id = item['snippet']['resourceId']['videoId']
                        print(f"   ✅ 영상 찾음: {video_title}")
                        print(f"   📺 Video ID: {video_id}")
                        return video_id
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            print(f"   ⚠️ 제목으로 영상을 찾을 수 없습니다: {title[:50]}...")
            return None
            
        except Exception as e:
            print(f"   ❌ 영상 검색 실패: {e}")
            return None
    
    def update_video_metadata(
        self,
        video_id: str,
        title: str,
        description: str,
        tags: list
    ) -> bool:
        """영상 메타데이터 업데이트"""
        try:
            # 태그 검증 및 정리
            original_tag_count = len(tags)
            tags = self._validate_and_clean_tags(tags)
            if len(tags) < original_tag_count:
                print(f"   ⚠️ 태그 정리: {original_tag_count}개 → {len(tags)}개")
            
            # Description 정리
            description = self._clean_description(description)
            
            print(f"   📝 Description 길이: {len(description)}자")
            print(f"   🏷️ 태그 개수: {len(tags)}개")
            
            # YouTube API 업데이트 요청
            body = {
                'id': video_id,
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22'  # People & Blogs
                }
            }
            
            response = self.youtube.videos().update(
                part='snippet',
                body=body
            ).execute()
            
            print(f"   ✅ 메타데이터 업데이트 완료!")
            print(f"   🔗 URL: https://www.youtube.com/watch?v={video_id}")
            return True
            
        except HttpError as e:
            print(f"   ❌ YouTube API 오류: {e}")
            if e.resp.status == 403:
                print("   💡 권한이 없습니다. YouTube API 스코프를 확인하세요.")
            return False
        except Exception as e:
            print(f"   ❌ 업데이트 실패: {e}")
            return False


def load_metadata(metadata_path: Path) -> Optional[Dict]:
    """메타데이터 파일 로드"""
    if not metadata_path.exists():
        return None
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube 영상 메타데이터 업데이트')
    parser.add_argument('--metadata-file', type=str, required=True, help='메타데이터 JSON 파일 경로')
    parser.add_argument('--video-id', type=str, help='YouTube Video ID (제목으로 자동 검색하지 않으려면 지정)')
    
    args = parser.parse_args()
    
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("🔄 YouTube 영상 메타데이터 업데이트")
    print("=" * 60)
    print()
    
    # 메타데이터 파일 로드
    metadata_path = Path(args.metadata_file)
    if not metadata_path.exists():
        print(f"❌ 메타데이터 파일을 찾을 수 없습니다: {metadata_path}")
        return
    
    metadata = load_metadata(metadata_path)
    if not metadata:
        print(f"❌ 메타데이터 로드 실패: {metadata_path}")
        return
    
    title = metadata.get('title', '')
    description = metadata.get('description', '')
    tags = metadata.get('tags', [])
    
    print(f"📋 메타데이터 파일: {metadata_path.name}")
    print(f"📌 제목: {title}")
    print(f"📝 설명 길이: {len(description)}자")
    print(f"🏷️ 태그 개수: {len(tags)}개")
    print()
    
    try:
        updater = YouTubeMetadataUpdater()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # Video ID 찾기
    video_id = args.video_id
    if not video_id:
        print("🔍 제목으로 영상 검색 중...")
        video_id = updater.find_video_id_by_title(title)
        if not video_id:
            print("❌ 영상을 찾을 수 없습니다.")
            print("   💡 --video-id 옵션으로 직접 지정하세요.")
            return
        print()
    
    # 메타데이터 업데이트
    print("📤 메타데이터 업데이트 중...")
    success = updater.update_video_metadata(video_id, title, description, tags)
    
    if success:
        print()
        print("=" * 60)
        print("✅ 업데이트 완료!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ 업데이트 실패")
        print("=" * 60)


if __name__ == "__main__":
    main()

