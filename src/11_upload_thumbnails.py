"""
기존 YouTube 영상에 썸네일 업로드 스크립트
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

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class ThumbnailUploader:
    """썸네일 업로더"""
    
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
    
    def upload_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """썸네일 업로드"""
        import time
        
        if not os.path.exists(thumbnail_path):
            print(f"❌ 썸네일 파일을 찾을 수 없습니다: {thumbnail_path}")
            return False
        
        max_retries = 3
        retry = 0
        
        while retry < max_retries:
            try:
                print(f"   📸 썸네일 업로드 중: {Path(thumbnail_path).name}")
                self.youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(thumbnail_path)
                ).execute()
                print("   ✅ 썸네일 업로드 완료")
                return True
            except HttpError as e:
                error_status = e.resp.status if hasattr(e.resp, 'status') else None
                if error_status in [500, 502, 503, 504]:
                    retry += 1
                    if retry < max_retries:
                        print(f"   ⚠️ 썸네일 업로드 재시도 중... ({retry}/{max_retries})")
                        time.sleep(2 * retry)
                        continue
                print(f"   ❌ 썸네일 업로드 실패: {e}")
                if error_status == 403:
                    print("   권한이 없습니다. OAuth2 스코프를 확인하세요.")
                elif error_status == 404:
                    print("   영상을 찾을 수 없습니다. video_id를 확인하세요.")
                return False
            except Exception as e:
                retry += 1
                if retry < max_retries:
                    print(f"   ⚠️ 썸네일 업로드 재시도 중... ({retry}/{max_retries})")
                    time.sleep(2 * retry)
                    continue
                print(f"   ❌ 썸네일 업로드 실패: {e}")
                return False
        
        return False


def load_upload_log() -> list:
    """업로드 로그 로드"""
    log_file = Path("output/upload_log.json")
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def find_thumbnail_for_video(video_path: str, lang: str = None) -> Optional[str]:
    """영상 파일에 맞는 썸네일 찾기"""
    video_path_obj = Path(video_path)
    video_dir = video_path_obj.parent
    video_stem = video_path_obj.stem
    
    # 언어 감지
    if lang is None:
        if '_ko' in video_stem or 'review_ko' in video_stem:
            lang = 'ko'
        elif '_en' in video_stem or 'review_en' in video_stem:
            lang = 'en'
        else:
            lang = 'ko'  # 기본값
    
    # 책 제목 추출 (review_ko, review_en 제거)
    book_title = video_stem.replace('_review_ko', '').replace('_review_en', '').replace('_review', '')
    
    # 1순위: 언어별 썸네일 (책제목_thumbnail_ko.jpg 형식)
    lang_suffix = "_ko" if lang == "ko" else "_en"
    thumbnail_path = video_dir / f"{book_title}_thumbnail{lang_suffix}.jpg"
    
    if thumbnail_path.exists():
        return str(thumbnail_path)
    
    # 2순위: 영상 파일명 기반 썸네일
    thumbnail_path2 = video_dir / f"{video_stem}_thumbnail{lang_suffix}.jpg"
    if thumbnail_path2.exists():
        return str(thumbnail_path2)
    
    # 3순위: 언어 구분 없는 썸네일
    thumbnail_path_alt = video_dir / f"{book_title}_thumbnail.jpg"
    if thumbnail_path_alt.exists():
        return str(thumbnail_path_alt)
    
    return None


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='기존 YouTube 영상에 썸네일 업로드')
    parser.add_argument('--video-id', type=str, help='특정 영상 ID (지정하지 않으면 로그에서 모든 영상 처리)')
    parser.add_argument('--thumbnail', type=str, help='썸네일 파일 경로 (지정하지 않으면 자동 찾기)')
    
    args = parser.parse_args()
    
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("🖼️ YouTube 썸네일 업로드")
    print("=" * 60)
    print()
    
    try:
        uploader = ThumbnailUploader()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 특정 영상 ID가 지정된 경우
    if args.video_id:
        if not args.thumbnail:
            print("❌ --video-id를 사용할 때는 --thumbnail도 지정해야 합니다.")
            return
        
        success = uploader.upload_thumbnail(args.video_id, args.thumbnail)
        if success:
            print(f"\n✅ 썸네일 업로드 완료: {args.video_id}")
        else:
            print(f"\n❌ 썸네일 업로드 실패: {args.video_id}")
        return
    
    # 업로드 로그에서 영상 목록 가져오기
    upload_log = load_upload_log()
    if not upload_log:
        print("📭 업로드 로그를 찾을 수 없습니다.")
        print("   output/upload_log.json 파일이 있는지 확인하세요.")
        return
    
    print(f"📋 발견된 영상: {len(upload_log)}개\n")
    
    # 각 영상에 썸네일 업로드
    success_count = 0
    fail_count = 0
    
    for i, entry in enumerate(upload_log, 1):
        video_id = entry.get('video_id', '')
        video_path = entry.get('video_path', '')
        title = entry.get('title', 'N/A')
        
        if not video_id:
            print(f"[{i}/{len(upload_log)}] ⚠️ video_id가 없습니다. 건너뜁니다.")
            continue
        
        print(f"[{i}/{len(upload_log)}] {title}")
        print(f"   영상 ID: {video_id}")
        
        # 썸네일 찾기
        if args.thumbnail:
            thumbnail_path = args.thumbnail
        else:
            # 언어 감지
            lang = None
            if '_ko' in video_path:
                lang = 'ko'
            elif '_en' in video_path:
                lang = 'en'
            
            thumbnail_path = find_thumbnail_for_video(video_path, lang)
        
        if not thumbnail_path:
            print(f"   ⚠️ 썸네일을 찾을 수 없습니다.")
            fail_count += 1
            print()
            continue
        
        # 썸네일 업로드
        success = uploader.upload_thumbnail(video_id, thumbnail_path)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        print()
    
    # 결과 요약
    print("=" * 60)
    print("📊 업로드 결과")
    print("=" * 60)
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📋 전체: {len(upload_log)}개")


if __name__ == "__main__":
    main()

