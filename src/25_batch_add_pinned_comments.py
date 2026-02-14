#!/usr/bin/env python3
"""
기존 YouTube 영상에 제휴 링크가 포함된 고정 댓글 일괄 추가 스크립트

채널의 모든 영상에 챕터 타임스탬프와 제휴 링크가 포함된 고정 댓글을 추가합니다.
안전장치로 --dry-run이 기본이며, --apply 플래그를 명시해야 실제로 추가됩니다.
"""

import os
import sys
import time
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("❌ google-api-python-client가 설치되지 않았습니다.")
    print("   pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

from src.utils.pinned_comment import generate_pinned_comment
from src.utils.translations import translate_book_title, translate_author_name, is_english_title

load_dotenv()

# YouTube API 스코프 (댓글 작성 및 고정 권한 필요)
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# 제휴 링크 마커 (고정 댓글에 이미 있는지 확인용)
AFFILIATE_MARKERS = [
    "📖 이 책 구매하기:",
    "📖 Get this book:"
]


class PinnedCommentAdder:
    """YouTube 영상에 제휴 링크가 포함된 고정 댓글을 일괄 추가하는 클래스"""

    def __init__(self, dry_run: bool = True, delay: float = 1.0):
        """
        Args:
            dry_run: True면 미리보기만, False면 실제 추가
            delay: API 호출 간 대기 시간 (초)
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("google-api-python-client가 필요합니다.")

        self.dry_run = dry_run
        self.delay = delay
        self.youtube = None
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

    def get_channel_videos(self, max_results: Optional[int] = None) -> List[Dict]:
        """
        채널의 모든 영상 목록 가져오기

        Args:
            max_results: 최대 영상 개수 (None이면 전체)

        Returns:
            영상 정보 목록 [{"video_id": "...", "title": "..."}, ...]
        """
        print(f"\n📋 채널 영상 목록 가져오는 중... (채널 ID: {self.channel_id})")

        videos = []

        try:
            # 1. 채널의 uploads 재생목록 ID 가져오기
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=self.channel_id
            ).execute()

            if not channel_response.get('items'):
                print("❌ 채널을 찾을 수 없습니다.")
                return videos

            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            print(f"   📂 Uploads 재생목록 ID: {uploads_playlist_id}")

            # 2. 재생목록의 모든 영상 가져오기
            next_page_token = None
            page = 1

            while True:
                playlist_response = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=50,  # 페이지당 최대 50개
                    pageToken=next_page_token
                ).execute()

                items = playlist_response.get('items', [])
                print(f"   📄 Page {page}: {len(items)}개 영상")

                for item in items:
                    video_id = item['snippet']['resourceId']['videoId']
                    title = item['snippet']['title']
                    videos.append({
                        'video_id': video_id,
                        'title': title
                    })

                    if max_results and len(videos) >= max_results:
                        break

                if max_results and len(videos) >= max_results:
                    break

                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break

                page += 1
                time.sleep(self.delay)  # API 호출 간 대기

            print(f"✅ 총 {len(videos)}개 영상 발견")
            return videos

        except HttpError as e:
            print(f"❌ API 오류: {e}")
            return videos

    def get_pinned_comment(self, video_id: str) -> Optional[Dict]:
        """
        영상의 고정 댓글 가져오기

        Args:
            video_id: YouTube 영상 ID

        Returns:
            고정 댓글 정보 (없으면 None)
        """
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
                if top_comment.get('authorChannelId', {}).get('value') == self.channel_id:
                    return {
                        'comment_id': item['id'],
                        'text': top_comment['textDisplay']
                    }

            return None

        except HttpError as e:
            if e.resp.status == 403:
                # 댓글이 비활성화된 영상
                return None
            print(f"   ⚠️ 댓글 조회 오류: {e}")
            return None

    def has_affiliate_links(self, comment_text: str) -> bool:
        """
        댓글에 이미 제휴 링크가 있는지 확인

        Args:
            comment_text: 댓글 텍스트

        Returns:
            제휴 링크가 있으면 True
        """
        for marker in AFFILIATE_MARKERS:
            if marker in comment_text:
                return True
        return False

    def extract_book_info_from_title(self, title: str) -> Optional[Dict]:
        """
        제목에서 책 정보 추출

        Args:
            title: YouTube 영상 제목

        Returns:
            {"book_title": "...", "author": "...", "language": "ko/en"}
            또는 None
        """
        book_title = ""
        author = ""
        language = "ko"

        # 패턴 1: [핵심 요약] 책제목: 저자
        match = re.search(r'\[핵심 요약\]\s*([^:]+):\s*([^(|]+)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip()
            language = "ko"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 2: [Summary] 책제목: 저자
        match = re.search(r'\[Summary\]\s*([^:]+):\s*([^(|]+)', title)
        if match:
            book_title = match.group(1).strip()
            author = match.group(2).strip()
            language = "en"
            return {"book_title": book_title, "author": author, "language": language}

        # 패턴 3: [한국어] 책제목 책 리뷰
        match = re.search(r'\[한국어\]\s*([^책]+)책\s*리뷰', title)
        if match:
            book_title = match.group(1).strip()
            language = "ko"
            return {"book_title": book_title, "author": "", "language": language}

        # 패턴 4: [English] 책제목 Book Review
        match = re.search(r'\[English\]\s*([^B]+)Book\s*Review', title)
        if match:
            book_title = match.group(1).strip()
            language = "en"
            return {"book_title": book_title, "author": "", "language": language}

        return None

    def add_pinned_comment(self, video_id: str, comment_text: str) -> bool:
        """
        영상에 고정 댓글 추가

        Args:
            video_id: YouTube 영상 ID
            comment_text: 댓글 텍스트

        Returns:
            성공 여부
        """
        if self.dry_run:
            print("   🔍 [DRY RUN] 실제로 댓글을 추가하지 않습니다.")
            return True

        try:
            # 댓글 추가
            comment_response = self.youtube.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': video_id,
                        'topLevelComment': {
                            'snippet': {
                                'textOriginal': comment_text
                            }
                        }
                    }
                }
            ).execute()

            comment_id = comment_response['id']

            # 댓글 고정 (setModerationStatus API 사용)
            # 참고: 채널 소유자의 댓글만 고정 가능
            # YouTube Studio에서 수동으로 고정해야 함 (API로는 불가능)

            print(f"   ✅ 댓글 추가 완료 (YouTube Studio에서 수동 고정 필요)")
            print(f"   📝 댓글 ID: {comment_id}")
            return True

        except HttpError as e:
            print(f"   ❌ 댓글 추가 실패: {e}")
            return False

    def process_videos(self, video_ids: Optional[List[str]] = None, limit: Optional[int] = None):
        """
        영상들을 처리하여 고정 댓글 추가

        Args:
            video_ids: 처리할 영상 ID 목록 (None이면 전체 채널)
            limit: 최대 처리 개수
        """
        if video_ids:
            # 특정 영상만 처리
            videos = [{"video_id": vid, "title": "Unknown"} for vid in video_ids]
        else:
            # 채널 전체 영상 가져오기
            videos = self.get_channel_videos(max_results=limit)

        if not videos:
            print("처리할 영상이 없습니다.")
            return

        print(f"\n{'='*60}")
        print(f"처리 모드: {'🔍 DRY RUN (미리보기)' if self.dry_run else '✏️ APPLY (실제 추가)'}")
        print(f"처리 대상: {len(videos)}개 영상")
        print(f"{'='*60}\n")

        added_count = 0
        skipped_count = 0
        error_count = 0

        for idx, video in enumerate(videos, 1):
            video_id = video['video_id']
            video_title = video['title']

            print(f"\n[{idx}/{len(videos)}] 🎬 {video_title}")
            print(f"   📹 Video ID: {video_id}")

            try:
                # 1. 기존 고정 댓글 확인
                existing_comment = self.get_pinned_comment(video_id)

                if existing_comment:
                    if self.has_affiliate_links(existing_comment['text']):
                        print("   ✅ 이미 제휴 링크가 있는 댓글이 있습니다. (건너뜀)")
                        skipped_count += 1
                        continue
                    else:
                        print("   ⚠️ 기존 댓글이 있지만 제휴 링크가 없습니다.")

                # 2. 책 정보 추출
                book_info = self.extract_book_info_from_title(video_title)
                if not book_info:
                    print("   ⚠️ 제목에서 책 정보를 추출할 수 없습니다. (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📚 책 정보: {book_info}")

                # 3. 고정 댓글 생성
                comment_text = generate_pinned_comment(
                    book_title=book_info['book_title'],
                    timestamps=None,  # 타임스탬프는 영상마다 다르므로 생략
                    language=book_info['language'],
                    author=book_info['author'] if book_info['author'] else None
                )

                if not comment_text:
                    print("   ⚠️ 고정 댓글 생성 실패. (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📝 댓글 길이: {len(comment_text)}자")

                # 4. 댓글 추가
                if self.add_pinned_comment(video_id, comment_text):
                    added_count += 1
                else:
                    error_count += 1

                # API 호출 간 대기
                time.sleep(self.delay)

            except HttpError as e:
                print(f"   ❌ API 오류: {e}")
                error_count += 1
                time.sleep(self.delay)
            except Exception as e:
                print(f"   ❌ 예외 발생: {e}")
                error_count += 1
                time.sleep(self.delay)

        # 최종 결과
        print(f"\n{'='*60}")
        print(f"✅ 처리 완료:")
        print(f"   - 추가: {added_count}개")
        print(f"   - 건너뜀: {skipped_count}개")
        print(f"   - 오류: {error_count}개")
        print(f"{'='*60}")

        if not self.dry_run and added_count > 0:
            print(f"\n⚠️ 중요: YouTube Studio에서 댓글을 수동으로 고정해야 합니다!")
            print(f"   https://studio.youtube.com/")


def main():
    parser = argparse.ArgumentParser(
        description="기존 YouTube 영상에 제휴 링크가 포함된 고정 댓글 일괄 추가",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 미리보기 (기본)
  python src/25_batch_add_pinned_comments.py --dry-run

  # 실제 적용 (50개 제한)
  python src/25_batch_add_pinned_comments.py --apply --limit 50

  # 특정 영상만 처리
  python src/25_batch_add_pinned_comments.py --video-id VIDEO_ID --apply

  # API 호출 간격 조절 (초)
  python src/25_batch_add_pinned_comments.py --apply --delay 2.0

주의사항:
  - YouTube API 일일 쿼터: commentThreads.insert 1건 = 50 units (일 10,000 units 제한 → 약 200건/일)
  - --apply 플래그 없이는 미리보기만 수행됩니다.
  - 이미 제휴 링크가 있는 댓글은 건너뜁니다 (멱등성).
  - 댓글 추가 후 YouTube Studio에서 수동으로 고정해야 합니다!
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='미리보기만 수행 (실제 추가 안 함, 기본값)'
    )

    parser.add_argument(
        '--apply',
        action='store_true',
        help='실제로 댓글 추가 (이 플래그가 있어야 추가됨)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='처리할 최대 영상 개수'
    )

    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='API 호출 간 대기 시간 (초, 기본값: 1.0)'
    )

    parser.add_argument(
        '--video-id',
        action='append',
        help='처리할 특정 영상 ID (여러 개 지정 가능)'
    )

    args = parser.parse_args()

    # --apply 플래그가 있으면 dry_run=False
    dry_run = not args.apply

    if not dry_run:
        print("⚠️ 실제 추가 모드입니다. 5초 후 시작합니다...")
        time.sleep(5)

    try:
        adder = PinnedCommentAdder(dry_run=dry_run, delay=args.delay)
        adder.process_videos(video_ids=args.video_id, limit=args.limit)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
