#!/usr/bin/env python3
"""
기존 YouTube 영상에 제휴 링크 일괄 업데이트 스크립트

채널의 모든 영상을 가져와서 description에 제휴 링크가 없는 경우 자동으로 추가합니다.
안전장치로 --dry-run이 기본이며, --apply 플래그를 명시해야 실제로 업데이트됩니다.
"""

import os
import sys
import json
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

from src.utils.affiliate_links import generate_affiliate_section
from src.utils.translations import translate_book_title, translate_author_name, is_english_title

load_dotenv()

# YouTube API 스코프 (영상 메타데이터 수정 권한 필요)
SCOPES = ['https://www.googleapis.com/auth/youtube']

# 제휴 링크 마커 (description에 이미 있는지 확인용)
AFFILIATE_MARKERS = [
    "📖 이 책 구매하기:",
    "📖 Get this book:"
]


class AffiliateLinksUpdater:
    """YouTube 영상에 제휴 링크를 일괄 업데이트하는 클래스"""

    def __init__(self, dry_run: bool = True, delay: float = 1.0):
        """
        Args:
            dry_run: True면 미리보기만, False면 실제 업데이트
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

    def has_affiliate_links(self, description: str) -> bool:
        """
        Description에 이미 제휴 링크가 있는지 확인

        Args:
            description: YouTube 영상 설명

        Returns:
            제휴 링크가 있으면 True
        """
        for marker in AFFILIATE_MARKERS:
            if marker in description:
                return True
        return False

    def extract_book_info_from_description(self, description: str, title: str) -> Optional[Dict]:
        """
        Description과 제목에서 책 정보 추출

        Args:
            description: YouTube 영상 설명
            title: YouTube 영상 제목

        Returns:
            {"book_title_ko": "...", "book_title_en": "...", "author_ko": "...", "author_en": "..."}
            또는 None
        """
        # 제목에서 책 제목 추출 (패턴: [핵심 요약] 책제목: 작가 또는 [한국어] 책제목 책 리뷰)
        # 예: "[핵심 요약] 노인과 바다: 어니스트 헤밍웨이"
        # 예: "[한국어] 노르웨이의 숲 책 리뷰 무라카미 하루키 | [Korean] Norwegian Wood Book Review"

        book_title_ko = ""
        book_title_en = ""
        author_ko = ""
        author_en = ""

        # 패턴 1: [핵심 요약] 또는 [한국어] 형식
        match = re.search(r'\[(?:핵심 요약|한국어|English)\]\s*([^:|\[]+)', title)
        if match:
            extracted = match.group(1).strip()
            # "책 리뷰", "Book Review" 제거
            extracted = re.sub(r'\s*책\s*리뷰\s*', '', extracted)
            extracted = re.sub(r'\s*Book\s*Review\s*', '', extracted)

            # 한글인지 영문인지 판단
            if is_english_title(extracted):
                book_title_en = extracted
            else:
                book_title_ko = extracted

        # 패턴 2: description에서 "✍️ 작가:" 또는 "✍️ Author:" 찾기
        author_match_ko = re.search(r'✍️\s*작가:\s*([^\n]+)', description)
        if author_match_ko:
            author_ko = author_match_ko.group(1).strip()

        author_match_en = re.search(r'✍️\s*Author:\s*([^\n]+)', description)
        if author_match_en:
            author_en = author_match_en.group(1).strip()

        # 책 제목이나 작가 중 하나라도 있으면 반환
        if book_title_ko or book_title_en or author_ko or author_en:
            return {
                "book_title_ko": book_title_ko,
                "book_title_en": book_title_en,
                "author_ko": author_ko,
                "author_en": author_en
            }

        return None

    def insert_affiliate_links(self, description: str, book_info: Dict, language: str) -> str:
        """
        Description에 제휴 링크 삽입 (해시태그 앞)

        Args:
            description: 기존 YouTube 영상 설명
            book_info: 책 정보 딕셔너리
            language: 'ko' 또는 'en'

        Returns:
            제휴 링크가 삽입된 description
        """
        # 해시태그 위치 찾기
        hashtag_pattern = r'#[^\s#]+'
        matches = list(re.finditer(hashtag_pattern, description))

        if not matches:
            # 해시태그가 없으면 맨 뒤에 추가
            insert_pos = len(description)
        else:
            # 첫 번째 해시태그 위치
            insert_pos = matches[0].start()

        # 제휴 링크 생성
        affiliate_section = generate_affiliate_section(
            book_title_ko=book_info.get("book_title_ko", ""),
            book_title_en=book_info.get("book_title_en", ""),
            author_ko=book_info.get("author_ko", ""),
            author_en=book_info.get("author_en", ""),
            language=language
        )

        if not affiliate_section:
            return description  # 제휴 ID가 없으면 원본 그대로

        # 삽입
        new_description = description[:insert_pos] + affiliate_section + "\n" + description[insert_pos:]
        return new_description

    def update_video_description(self, video_id: str, new_description: str, title: str, tags: List[str]) -> bool:
        """
        YouTube 영상 description 업데이트

        Args:
            video_id: YouTube 영상 ID
            new_description: 새 description
            title: 영상 제목 (변경하지 않지만 API 요청에 필요)
            tags: 영상 태그 (변경하지 않지만 API 요청에 필요)

        Returns:
            성공 여부
        """
        if self.dry_run:
            print("   🔍 [DRY RUN] 실제로 업데이트하지 않습니다.")
            return True

        try:
            self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': {
                        'title': title,
                        'description': new_description,
                        'tags': tags,
                        'categoryId': '27'  # Education
                    }
                }
            ).execute()

            print("   ✅ 업데이트 완료")
            return True

        except HttpError as e:
            print(f"   ❌ 업데이트 실패: {e}")
            return False

    def process_videos(self, video_ids: Optional[List[str]] = None, limit: Optional[int] = None):
        """
        영상들을 처리하여 제휴 링크 추가

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
        print(f"처리 모드: {'🔍 DRY RUN (미리보기)' if self.dry_run else '✏️ APPLY (실제 업데이트)'}")
        print(f"처리 대상: {len(videos)}개 영상")
        print(f"{'='*60}\n")

        updated_count = 0
        skipped_count = 0
        error_count = 0

        for idx, video in enumerate(videos, 1):
            video_id = video['video_id']
            video_title = video['title']

            print(f"\n[{idx}/{len(videos)}] 🎬 {video_title}")
            print(f"   📹 Video ID: {video_id}")

            try:
                # 영상 상세 정보 가져오기
                video_response = self.youtube.videos().list(
                    part='snippet',
                    id=video_id
                ).execute()

                if not video_response.get('items'):
                    print("   ⚠️ 영상을 찾을 수 없습니다. (삭제되었거나 비공개)")
                    skipped_count += 1
                    continue

                snippet = video_response['items'][0]['snippet']
                current_description = snippet.get('description', '')
                current_title = snippet.get('title', video_title)
                current_tags = snippet.get('tags', [])

                # 1. 이미 제휴 링크가 있는지 확인
                if self.has_affiliate_links(current_description):
                    print("   ✅ 이미 제휴 링크가 있습니다. (건너뜀)")
                    skipped_count += 1
                    continue

                # 2. 책 정보 추출
                book_info = self.extract_book_info_from_description(current_description, current_title)
                if not book_info:
                    print("   ⚠️ 책 정보를 추출할 수 없습니다. (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📚 책 정보: {book_info}")

                # 3. 언어 감지 (한글/영문)
                if book_info.get("book_title_ko"):
                    language = "ko"
                elif book_info.get("book_title_en"):
                    language = "en"
                else:
                    print("   ⚠️ 언어를 감지할 수 없습니다. (건너뜀)")
                    skipped_count += 1
                    continue

                # 4. 제휴 링크 삽입
                new_description = self.insert_affiliate_links(current_description, book_info, language)

                if new_description == current_description:
                    print("   ⚠️ 제휴 링크 생성 실패 (제휴 ID 미설정?). (건너뜀)")
                    skipped_count += 1
                    continue

                print(f"   📝 새 description 길이: {len(new_description)}자 (기존: {len(current_description)}자)")

                # 5. 업데이트
                if self.update_video_description(video_id, new_description, current_title, current_tags):
                    updated_count += 1
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
        print(f"   - 업데이트: {updated_count}개")
        print(f"   - 건너뜀: {skipped_count}개")
        print(f"   - 오류: {error_count}개")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="기존 YouTube 영상에 제휴 링크 일괄 업데이트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 미리보기 (기본)
  python src/24_batch_update_affiliate_links.py --dry-run

  # 실제 적용 (50개 제한)
  python src/24_batch_update_affiliate_links.py --apply --limit 50

  # 특정 영상만 업데이트
  python src/24_batch_update_affiliate_links.py --video-id VIDEO_ID --apply

  # API 호출 간격 조절 (초)
  python src/24_batch_update_affiliate_links.py --apply --delay 2.0

주의사항:
  - YouTube API 일일 쿼터: videos.update 1건 = 50 units (일 10,000 units 제한 → 약 200건/일)
  - --apply 플래그 없이는 미리보기만 수행됩니다.
  - 이미 제휴 링크가 있는 영상은 건너뜁니다 (멱등성).
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='미리보기만 수행 (실제 업데이트 안 함, 기본값)'
    )

    parser.add_argument(
        '--apply',
        action='store_true',
        help='실제로 업데이트 적용 (이 플래그가 있어야 업데이트됨)'
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
        print("⚠️ 실제 업데이트 모드입니다. 5초 후 시작합니다...")
        time.sleep(5)

    try:
        updater = AffiliateLinksUpdater(dry_run=dry_run, delay=args.delay)
        updater.process_videos(video_ids=args.video_id, limit=args.limit)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
