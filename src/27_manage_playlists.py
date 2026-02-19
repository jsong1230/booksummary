#!/usr/bin/env python3
"""
YouTube 플레이리스트 자동 관리 스크립트

채널의 모든 영상을 장르별로 분류하고 플레이리스트를 자동 생성/업데이트합니다.
신규 업로드 시 적절한 플레이리스트에 자동으로 추가합니다.

사용법:
  # 미리보기 (기본값, 실제 변경 없음)
  python src/27_manage_playlists.py

  # 실제 적용
  python src/27_manage_playlists.py --apply

  # 특정 영상 ID를 적절한 플레이리스트에 추가
  python src/27_manage_playlists.py --apply --video-id VIDEO_ID

  # 장르 감지 결과만 확인 (dry-run)
  python src/27_manage_playlists.py --list-genres
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Google API 임포트
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

try:
    from src.utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

try:
    from src.utils.title_generator import generate_hashtags
except ImportError:
    from utils.title_generator import generate_hashtags

FULL_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# 장르별 플레이리스트 정의
PLAYLIST_DEFINITIONS = {
    "philosophy": {
        "ko": {"title": "📚 철학 & 인문학 책 리뷰", "description": "철학, 인문학, 삶의 지혜에 관한 책 리뷰 모음"},
        "en": {"title": "📚 Philosophy & Humanities Book Reviews", "description": "Book reviews on philosophy, humanities, and wisdom of life"},
        "keywords_ko": ["철학", "인문학", "아포리즘", "쇼펜하우어", "니체", "플라톤"],
        "keywords_en": ["philosophy", "humanities", "wisdom", "aristotle", "plato", "nietzsche"],
    },
    "psychology": {
        "ko": {"title": "🧠 심리학 & 자기계발 책 리뷰", "description": "심리학, 자기계발, 마인드셋에 관한 책 리뷰 모음"},
        "en": {"title": "🧠 Psychology & Self-Help Book Reviews", "description": "Book reviews on psychology, self-help, and personal growth"},
        "keywords_ko": ["심리학", "자기계발", "습관", "마인드", "성장"],
        "keywords_en": ["psychology", "self-help", "mindset", "habits", "growth"],
    },
    "business": {
        "ko": {"title": "💼 경제 & 경영 책 리뷰", "description": "경제, 경영, 투자, 비즈니스에 관한 책 리뷰 모음"},
        "en": {"title": "💼 Business & Economics Book Reviews", "description": "Book reviews on business, economics, and investment"},
        "keywords_ko": ["경제", "경영", "투자", "비즈니스", "부자"],
        "keywords_en": ["business", "economics", "investment", "finance", "wealth"],
    },
    "fiction": {
        "ko": {"title": "📖 소설 & 문학 책 리뷰", "description": "소설, 문학 작품에 관한 책 리뷰 모음"},
        "en": {"title": "📖 Fiction & Literature Book Reviews", "description": "Book reviews on fiction and literary works"},
        "keywords_ko": ["소설", "문학", "이야기", "노벨"],
        "keywords_en": ["fiction", "novel", "literature", "story"],
    },
    "history": {
        "ko": {"title": "🏛️ 역사 & 사회 책 리뷰", "description": "역사, 사회, 문화에 관한 책 리뷰 모음"},
        "en": {"title": "🏛️ History & Society Book Reviews", "description": "Book reviews on history, society, and culture"},
        "keywords_ko": ["역사", "사회", "문화", "전쟁", "문명"],
        "keywords_en": ["history", "society", "culture", "war", "civilization"],
    },
    "science": {
        "ko": {"title": "🔬 과학 & 기술 책 리뷰", "description": "과학, 기술, 자연에 관한 책 리뷰 모음"},
        "en": {"title": "🔬 Science & Technology Book Reviews", "description": "Book reviews on science, technology, and nature"},
        "keywords_ko": ["과학", "기술", "우주", "물리", "생물"],
        "keywords_en": ["science", "technology", "space", "physics", "biology"],
    },
    "general": {
        "ko": {"title": "📚 인기 책 리뷰 모음", "description": "다양한 장르의 인기 책 리뷰 모음"},
        "en": {"title": "📚 Popular Book Reviews Collection", "description": "Collection of popular book reviews across genres"},
        "keywords_ko": [],
        "keywords_en": [],
    },
}


def _detect_genre_from_title(title: str) -> str:
    """영상 제목에서 장르 감지"""
    title_lower = title.lower()

    # 철학/인문학 키워드
    phil_kw = ["철학", "인문", "아포리즘", "지혜", "philosophy", "humanit", "wisdom", "aphorism"]
    if any(k in title_lower for k in phil_kw):
        return "philosophy"

    # 심리학/자기계발
    psych_kw = ["심리", "자기계발", "습관", "마인드", "psychology", "self-help", "habit", "mindset", "growth"]
    if any(k in title_lower for k in psych_kw):
        return "psychology"

    # 경제/경영
    biz_kw = ["경제", "경영", "투자", "부자", "돈", "business", "economics", "investment", "wealth", "finance"]
    if any(k in title_lower for k in biz_kw):
        return "business"

    # 역사/사회
    hist_kw = ["역사", "사회", "문명", "전쟁", "history", "society", "civilization", "war"]
    if any(k in title_lower for k in hist_kw):
        return "history"

    # 과학
    sci_kw = ["과학", "우주", "물리", "생물", "science", "physics", "biology", "space"]
    if any(k in title_lower for k in sci_kw):
        return "science"

    # 소설/문학 키워드
    fic_kw = ["소설", "문학", "novel", "fiction", "literature"]
    if any(k in title_lower for k in fic_kw):
        return "fiction"

    return "general"


class PlaylistManager:
    """YouTube 플레이리스트 관리자"""

    def __init__(self, dry_run: bool = True):
        self.logger = get_logger(__name__)
        self.dry_run = dry_run
        self.youtube = None

        if not dry_run:
            if not GOOGLE_API_AVAILABLE:
                raise ImportError("google-api-python-client가 필요합니다: pip install google-api-python-client google-auth-oauthlib")
            self._authenticate()

    def _authenticate(self):
        """YouTube OAuth2 인증"""
        credentials_path = Path("secrets/credentials.json")
        client_secret_path = Path("secrets/client_secret.json")

        if not credentials_path.exists():
            raise FileNotFoundError(f"인증 파일이 없습니다: {credentials_path}\npython scripts/reauth_youtube.py 실행 후 다시 시도하세요.")

        with open(credentials_path, "r") as f:
            creds_data = json.load(f)

        creds = Credentials(
            token=creds_data.get("token"),
            refresh_token=creds_data.get("refresh_token"),
            token_uri=creds_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=creds_data.get("client_id"),
            client_secret=creds_data.get("client_secret"),
            scopes=creds_data.get("scopes", FULL_SCOPES),
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())

        self.youtube = build("youtube", "v3", credentials=creds)
        self.logger.info("✅ YouTube API 인증 성공")

    def get_channel_videos(self, max_results: int = 200) -> List[Dict]:
        """채널의 모든 업로드 영상 목록 조회"""
        if self.dry_run:
            self.logger.info("  (dry-run) 채널 영상 목록 조회 스킵")
            return []

        try:
            # 채널 ID 조회
            channel_resp = self.youtube.channels().list(part="contentDetails", mine=True).execute()
            uploads_playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            videos = []
            page_token = None

            while True:
                resp = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=page_token,
                ).execute()

                for item in resp.get("items", []):
                    snippet = item["snippet"]
                    videos.append({
                        "video_id": snippet["resourceId"]["videoId"],
                        "title": snippet["title"],
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", ""),
                    })

                page_token = resp.get("nextPageToken")
                if not page_token or len(videos) >= max_results:
                    break

            self.logger.info(f"  📹 채널 영상 {len(videos)}개 조회 완료")
            return videos

        except HttpError as e:
            self.logger.error(f"채널 영상 조회 실패: {e}")
            return []

    def get_existing_playlists(self) -> Dict[str, str]:
        """기존 플레이리스트 목록 조회 (제목 → playlist_id 매핑)"""
        if self.dry_run:
            return {}

        try:
            playlists = {}
            page_token = None

            while True:
                resp = self.youtube.playlists().list(
                    part="snippet",
                    mine=True,
                    maxResults=50,
                    pageToken=page_token,
                ).execute()

                for item in resp.get("items", []):
                    title = item["snippet"]["title"]
                    playlists[title] = item["id"]

                page_token = resp.get("nextPageToken")
                if not page_token:
                    break

            self.logger.info(f"  📋 기존 플레이리스트 {len(playlists)}개 조회 완료")
            return playlists

        except HttpError as e:
            self.logger.error(f"플레이리스트 조회 실패: {e}")
            return {}

    def create_playlist(self, title: str, description: str, language: str = "ko") -> Optional[str]:
        """새 플레이리스트 생성"""
        if self.dry_run:
            self.logger.info(f"  [dry-run] 플레이리스트 생성: {title}")
            return f"FAKE_PLAYLIST_{title[:8]}"

        try:
            resp = self.youtube.playlists().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": title,
                        "description": description,
                        "defaultLanguage": language,
                    },
                    "status": {"privacyStatus": "public"},
                },
            ).execute()

            playlist_id = resp["id"]
            self.logger.info(f"  ✅ 플레이리스트 생성: {title} ({playlist_id})")
            return playlist_id

        except HttpError as e:
            self.logger.error(f"플레이리스트 생성 실패 ({title}): {e}")
            return None

    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """영상을 플레이리스트에 추가"""
        if self.dry_run:
            self.logger.info(f"  [dry-run] 영상 추가: {video_id} → {playlist_id}")
            return True

        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            self.logger.info(f"  ✅ 영상 추가: {video_id} → {playlist_id}")
            return True

        except HttpError as e:
            if "duplicate" in str(e).lower() or "409" in str(e):
                self.logger.info(f"  ℹ️ 이미 플레이리스트에 있음: {video_id}")
                return True
            self.logger.error(f"영상 추가 실패 ({video_id}): {e}")
            return False

    def organize_channel_videos(self, language: str = "ko") -> Dict[str, List[str]]:
        """
        채널 영상을 장르별 플레이리스트로 자동 정리

        Returns:
            장르별 영상 ID 매핑
        """
        self.logger.info(f"\n📋 채널 영상 플레이리스트 자동 정리 시작 (language={language})")
        lang_key = "ko" if language == "ko" else "en"

        # 채널 영상 목록 조회
        videos = self.get_channel_videos()
        existing_playlists = self.get_existing_playlists()

        # 장르별 분류
        genre_video_map: Dict[str, List[str]] = {g: [] for g in PLAYLIST_DEFINITIONS}

        for video in videos:
            genre = _detect_genre_from_title(video["title"])
            genre_video_map[genre].append(video["video_id"])
            self.logger.info(f"  [{genre:12s}] {video['title'][:60]}")

        # 플레이리스트 생성 또는 조회 후 영상 추가
        for genre, video_ids in genre_video_map.items():
            if not video_ids:
                continue

            playlist_def = PLAYLIST_DEFINITIONS[genre][lang_key]
            playlist_title = playlist_def["title"]
            playlist_desc = playlist_def["description"]

            # 기존 플레이리스트 확인
            playlist_id = existing_playlists.get(playlist_title)
            if not playlist_id:
                playlist_id = self.create_playlist(playlist_title, playlist_desc, language)

            if playlist_id:
                self.logger.info(f"\n  📂 {playlist_title}: {len(video_ids)}개 영상")
                for vid_id in video_ids:
                    self.add_video_to_playlist(vid_id, playlist_id)

        return genre_video_map

    def add_single_video(self, video_id: str, video_title: str, language: str = "ko") -> bool:
        """
        단일 영상을 적절한 플레이리스트에 자동 추가

        Args:
            video_id: YouTube 영상 ID
            video_title: 영상 제목 (장르 감지용)
            language: 언어

        Returns:
            성공 여부
        """
        genre = _detect_genre_from_title(video_title)
        lang_key = "ko" if language == "ko" else "en"
        playlist_def = PLAYLIST_DEFINITIONS[genre][lang_key]
        playlist_title = playlist_def["title"]

        self.logger.info(f"  🎯 장르 감지: {genre} → 플레이리스트: {playlist_title}")

        existing = self.get_existing_playlists()
        playlist_id = existing.get(playlist_title)

        if not playlist_id:
            playlist_id = self.create_playlist(
                playlist_title, playlist_def["description"], language
            )

        if playlist_id:
            return self.add_video_to_playlist(video_id, playlist_id)

        return False

    def list_genre_classification(self, csv_path: str = "ildangbaek_books.csv") -> None:
        """CSV 파일 기반 장르 분류 결과 출력"""
        csv_file = Path(csv_path)
        if not csv_file.exists():
            self.logger.warning(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            return

        import csv
        genre_count: Dict[str, int] = {}

        print(f"\n{'='*70}")
        print(f"{'장르':<15} {'책 제목':<40} {'YouTube 상태':<15}")
        print(f"{'='*70}")

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get("title", row.get("book_title", ""))
                if not title:
                    continue
                genre = _detect_genre_from_title(title)
                status = row.get("status", "unknown")
                genre_count[genre] = genre_count.get(genre, 0) + 1
                print(f"  {genre:<13} {title[:38]:<40} {status:<15}")

        print(f"\n{'='*70}")
        print("📊 장르별 통계:")
        for genre, count in sorted(genre_count.items(), key=lambda x: -x[1]):
            playlist_title = PLAYLIST_DEFINITIONS.get(genre, PLAYLIST_DEFINITIONS["general"])["ko"]["title"]
            print(f"  {genre:<15}: {count}개  →  {playlist_title}")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 플레이리스트 자동 관리",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true", help="실제로 플레이리스트를 생성/수정합니다 (기본값: dry-run)")
    parser.add_argument("--video-id", help="특정 영상 ID를 플레이리스트에 추가")
    parser.add_argument("--video-title", help="영상 제목 (--video-id와 함께 사용)")
    parser.add_argument("--language", default="ko", choices=["ko", "en"], help="플레이리스트 언어 (기본값: ko)")
    parser.add_argument("--list-genres", action="store_true", help="CSV 기반 장르 분류 결과만 출력")
    parser.add_argument("--csv", default="ildangbaek_books.csv", help="책 목록 CSV 파일 경로")

    args = parser.parse_args()

    dry_run = not args.apply
    manager = PlaylistManager(dry_run=dry_run)

    if args.list_genres:
        manager.list_genre_classification(args.csv)
        return

    if args.video_id:
        # 단일 영상 추가
        if not args.video_title:
            print("❌ --video-id와 함께 --video-title을 지정해야 합니다.")
            sys.exit(1)
        manager.add_single_video(args.video_id, args.video_title, args.language)
    else:
        # 전체 채널 정리
        if dry_run:
            print("🔍 Dry-run 모드: 실제 변경 없이 분류 결과만 표시합니다.")
            print("  실제 적용하려면 --apply 플래그를 추가하세요.\n")
        genre_map = manager.organize_channel_videos(args.language)

        print("\n📊 장르별 분류 결과:")
        for genre, video_ids in genre_map.items():
            if video_ids:
                playlist_title = PLAYLIST_DEFINITIONS[genre]["ko"]["title"]
                print(f"  {playlist_title}: {len(video_ids)}개 영상")


if __name__ == "__main__":
    main()
