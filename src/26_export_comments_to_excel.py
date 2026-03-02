#!/usr/bin/env python3
"""
내 YouTube 채널의 영상에 작성한 댓글을 Excel로 내보내는 스크립트

채널의 모든 영상을 순회하며 채널 소유자가 작성한 댓글을 찾아
영상 제목, URL, 댓글 내용을 Excel 파일로 저장합니다.
"""

import os
import sys
import time
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    import pandas as pd
    GOOGLE_API_AVAILABLE = True
except ImportError as e:
    print(f"필요한 라이브러리가 없습니다: {e}")
    print("pip install google-api-python-client pandas openpyxl")
    GOOGLE_API_AVAILABLE = False

load_dotenv()

# YouTube API 스코프
SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]


class CommentExporter:
    """YouTube 채널의 댓글을 Excel로 내보내는 클래스"""

    def __init__(self, output_file: str = None, limit: int = None, delay: float = 1.0):
        """
        Args:
            output_file: 출력 Excel 파일 경로
            limit: 처리할 최대 영상 개수
            delay: API 호출 간 대기 시간 (초)
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client, pandas, openpyxl이 필요합니다.")

        self.output_file = output_file or f"output/my_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        self.limit = limit
        self.delay = delay
        self.youtube: Any = None
        self.channel_id = os.getenv("YOUTUBE_CHANNEL_ID")

        if not self.channel_id:
            raise ValueError("YOUTUBE_CHANNEL_ID가 설정되지 않았습니다.")

        self._authenticate()

    def _authenticate(self):
        """OAuth2 인증"""
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")

        if not all([client_id, client_secret, refresh_token]):
            raise ValueError("YouTube API 자격증명이 설정되지 않았습니다.")

        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=SCOPES
            )

            credentials.refresh(Request())
            self.youtube = build('youtube', 'v3', credentials=credentials)
            print("✅ YouTube API 인증 성공")
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise

    def get_channel_videos(self) -> List[Dict]:
        """
        채널의 모든 영상 목록 가져오기

        Returns:
            영상 정보 목록 [{"video_id": "...", "title": "...", "published_at": "..."}, ...]
        """
        print(f"\n📋 채널 영상 목록 가져오는 중... (채널 ID: {self.channel_id})")

        videos = []

        try:
            # 1. 채널의 uploads 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails,snippet',
                id=self.channel_id
            ).execute()

            if not channel_response.get('items'):
                print("❌ 채널을 찾을 수 없습니다.")
                return videos

            channel_title = channel_response['items'][0]['snippet'].get('title', 'Unknown')
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            print(f"   📺 채널명: {channel_title}")
            print(f"   📂 Uploads 재생목록 ID: {uploads_playlist_id}")

            # 2. 재생목록의 모든 영상 가져오기
            next_page_token = None
            page = 1

            while True:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                ).execute()

                items = playlist_response.get('items', [])

                for item in items:
                    video_id = item['snippet']['resourceId']['videoId']
                    title = item['snippet']['title']
                    published_at = item['snippet'].get('publishedAt', '')
                    videos.append({
                        'video_id': video_id,
                        'title': title,
                        'published_at': published_at
                    })

                    if self.limit and len(videos) >= self.limit:
                        break

                print(f"   📄 Page {page}: {len(items)}개 영상 누적 (총 {len(videos)}개)")

                if self.limit and len(videos) >= self.limit:
                    break

                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

                page += 1
                time.sleep(self.delay)

            print(f"✅ 총 {len(videos)}개 영상 발견")
            return videos

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            return videos

    def get_my_comments(self, video_id: str) -> List[Dict]:
        """
        특정 영상에서 채널 소유자가 작성한 댓글 가져오기

        Args:
            video_id: YouTube 영상 ID

        Returns:
            댓글 목록 [{"comment_id": "...", "text": "...", "published_at": "..."}, ...]
        """
        comments = []

        try:
            response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=100,
                order='relevance'
            ).execute()

            for item in response.get('items', []):
                snippet = item['snippet']
                top_comment = snippet['topLevelComment']['snippet']

                # 채널 소유자의 댓글인지 확인
                author_channel_id = top_comment.get('authorChannelId', {})
                if isinstance(author_channel_id, dict):
                    author_id = author_channel_id.get('value', '')
                else:
                    author_id = author_channel_id

                if author_id == self.channel_id:
                    # textOriginal: 원본 텍스트 (HTML 엔티티 없음)
                    # textDisplay: YouTube가 HTML로 변환한 형태 - 폴백용
                    text = top_comment.get('textOriginal') or top_comment.get('textDisplay', '')
                    published_at = top_comment.get('publishedAt', '')
                    updated_at = top_comment.get('updatedAt', '')

                    comments.append({
                        'comment_id': item['id'],
                        'text': text,
                        'published_at': published_at,
                        'updated_at': updated_at
                    })

            return comments

        except HttpError as e:
            if e.resp.status == 403:
                # 댓글이 비활성화된 영상
                return []
            print(f"   ⚠️ 댓글 조회 오류: {e}")
            return []

    def export_to_excel(self):
        """모든 영상의 내 댓글을 Excel로 내보내기"""
        # 영상 목록 가져오기
        videos = self.get_channel_videos()

        if not videos:
            print("처리할 영상이 없습니다.")
            return

        print(f"\n{'='*60}")
        print(f"🔍 {len(videos)}개 영상에서 내 댓글 검색 중...")
        print(f"{'='*60}\n")

        # 결과 데이터 수집
        results = []
        videos_with_comments = 0
        total_comments = 0

        for idx, video in enumerate(videos, 1):
            video_id = video['video_id']
            video_title = video['title']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_published = video.get('published_at', '')

            print(f"[{idx}/{len(videos)}] 🎬 {video_title[:50]}...")

            try:
                # 내 댓글 찾기
                my_comments = self.get_my_comments(video_id)

                if my_comments:
                    videos_with_comments += 1
                    total_comments += len(my_comments)
                    print(f"   ✅ 댓글 {len(my_comments)}개 발견")

                    for comment in my_comments:
                        results.append({
                            '영상 제목': video_title,
                            '영상 URL': video_url,
                            '영상 ID': video_id,
                            '영상 게시일': video_published,
                            '댓글 내용': comment['text'],
                            '댓글 ID': comment['comment_id'],
                            '댓글 작성일': comment['published_at'],
                            '댓글 수정일': comment['updated_at']
                        })
                else:
                    print(f"   ℹ️ 내 댓글 없음")

                # API 호출 간 대기
                time.sleep(self.delay)

            except Exception as e:
                print(f"   ❌ 오류: {e}")
                time.sleep(self.delay)

        # Excel 파일로 저장
        if results:
            df = pd.DataFrame(results)

            # 출력 디렉토리 생성
            output_path = Path(self.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Excel 파일로 저장
            df.to_excel(output_path, index=False, engine='openpyxl')

            print(f"\n{'='*60}")
            print(f"✅ 내보내기 완료!")
            print(f"   📊 총 영상 수: {len(videos)}개")
            print(f"   💬 댓글 있는 영상: {videos_with_comments}개")
            print(f"   📝 총 댓글 수: {total_comments}개")
            print(f"   📁 저장 위치: {output_path.absolute()}")
            print(f"{'='*60}")
        else:
            print("\n⚠️ 내 댓글이 없습니다.")


def main():
    parser = argparse.ArgumentParser(
        description="내 YouTube 채널의 영상에 작성한 댓글을 Excel로 내보내기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 기본 실행 (모든 영상 검색)
  python src/26_export_comments_to_excel.py

  # 출력 파일 지정
  python src/26_export_comments_to_excel.py --output my_comments.xlsx

  # 영상 개수 제한
  python src/26_export_comments_to_excel.py --limit 50

  # API 호출 간격 조절
  python src/26_export_comments_to_excel.py --delay 2.0
        """
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='출력 Excel 파일 경로 (기본값: output/my_comments_YYYYMMDD_HHMMSS.xlsx)'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='처리할 최대 영상 개수'
    )

    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=1.0,
        help='API 호출 간 대기 시간 (초, 기본값: 1.0)'
    )

    args = parser.parse_args()

    try:
        exporter = CommentExporter(
            output_file=args.output,
            limit=args.limit,
            delay=args.delay
        )
        exporter.export_to_excel()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
