#!/usr/bin/env python3
"""
YouTube 커뮤니티 탭 자동 포스팅 스크립트

채널 커뮤니티 탭에 책 인용구, 투표, 근황 포스트를 자동으로 생성합니다.

생성 포스트 유형:
  1. 책 인용구 포스트 - 무드 이미지 + 핵심 인용구
  2. 다음 리뷰 투표 - 시청자가 다음 리뷰할 책 선택
  3. 근황 포스트 - 채널 업데이트 및 소식

사용법:
  # 미리보기 (기본값)
  python src/28_community_posts.py --type quote --book-title "책 제목"

  # 실제 포스팅
  python src/28_community_posts.py --apply --type quote --book-title "책 제목"

  # 투표 포스트
  python src/28_community_posts.py --apply --type vote --candidates "책1,책2,책3,책4"

  # 근황 포스트
  python src/28_community_posts.py --apply --type update --message "다음 주에 새 영상 업로드 예정입니다!"

주의사항:
  - YouTube Data API v3의 communityPosts 엔드포인트 사용
  - youtube.force-ssl 스코프가 필요합니다
  - 현재 API가 제한적으로 제공되므로 일부 기능은 제한될 수 있습니다
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, List

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
    from src.utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        is_english_title,
    )
except ImportError:
    from utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        is_english_title,
    )

try:
    from src.utils.file_utils import get_standard_safe_title
except ImportError:
    from utils.file_utils import get_standard_safe_title

FULL_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _extract_quotes_from_summary(book_title: str, language: str = "ko", count: int = 3) -> List[str]:
    """Summary 파일에서 핵심 인용구 추출"""
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "ko" if language == "ko" else "en"

    candidates = [
        Path(f"assets/summaries/{safe_title}_summary_{lang_suffix}.md"),
        Path(f"output/{safe_title}_summary_{lang_suffix}.md"),
    ]

    summary_text = ""
    for path in candidates:
        if path.exists():
            summary_text = path.read_text(encoding="utf-8")
            summary_text = re.sub(r'<!--.*?-->', '', summary_text, flags=re.DOTALL).strip()
            break

    if not summary_text:
        return []

    # [SUMMARY] 섹션 추출
    summary_match = re.search(r'\[SUMMARY\]\s*(.*?)(?=\[BRIDGE\]|\Z)', summary_text, re.DOTALL)
    body = summary_match.group(1).strip() if summary_match else summary_text

    # 문장 분리 및 필터링
    if language == "ko":
        sentences = re.split(r'(?<=[다습니었])\.?\s+', body)
    else:
        sentences = re.split(r'(?<=[.!?])\s+', body)

    candidates_sents = [s.strip() for s in sentences if 30 <= len(s.strip()) <= 150]

    if len(candidates_sents) <= count:
        return candidates_sents

    step = len(candidates_sents) // count
    return [candidates_sents[i * step] for i in range(count)]


def _build_quote_post_text(
    book_title: str,
    quote: str,
    language: str = "ko",
    author: Optional[str] = None,
) -> str:
    """인용구 커뮤니티 포스트 텍스트 생성"""
    if is_english_title(book_title):
        en_title = book_title
        ko_title = translate_book_title_to_korean(book_title) or book_title
    else:
        ko_title = book_title
        en_title = translate_book_title(book_title) or book_title

    if language == "ko":
        title_display = ko_title
        author_line = f"— {author}" if author else f"— {ko_title}"
        post = f'📖 오늘의 책 한 구절\n\n"{quote}"\n{author_line}\n\n'
        post += f"✨ {ko_title} 리뷰가 궁금하다면 채널 영상을 확인하세요!\n"
        post += "#독서 #책 #명언 #독서스타그램 #북스타그램"
    else:
        title_display = en_title
        author_line = f"— {author}" if author else f"— {en_title}"
        post = f'📖 Book Quote of the Day\n\n"{quote}"\n{author_line}\n\n'
        post += f"✨ Check out the full review of {en_title} on the channel!\n"
        post += "#Reading #Books #BookQuote #BookReview #BookTube"

    return post


def _build_vote_post_text(
    candidates: List[str],
    language: str = "ko",
) -> Dict:
    """투표 커뮤니티 포스트 텍스트 생성"""
    if language == "ko":
        question = "📚 다음에 어떤 책을 리뷰하길 원하시나요?\n여러분의 선택이 다음 영상을 결정합니다!"
    else:
        question = "📚 Which book would you like me to review next?\nYour vote determines the next video!"

    return {
        "question": question,
        "choices": candidates[:4],  # YouTube 투표 최대 4개 선택지
    }


def _build_update_post_text(message: str, language: str = "ko") -> str:
    """근황 커뮤니티 포스트 텍스트 생성"""
    if language == "ko":
        post = f"📢 채널 소식\n\n{message}\n\n"
        post += "항상 응원해주시는 구독자 여러분께 감사드립니다! 🙏\n"
        post += "좋아요와 댓글로 많은 응원 부탁드려요 💕"
    else:
        post = f"📢 Channel Update\n\n{message}\n\n"
        post += "Thank you to all our subscribers for your continued support! 🙏\n"
        post += "Like and comment to show your support 💕"
    return post


class CommunityPostManager:
    """YouTube 커뮤니티 탭 포스트 관리자"""

    def __init__(self, dry_run: bool = True):
        self.logger = get_logger(__name__)
        self.dry_run = dry_run
        self.youtube = None

        if not dry_run:
            if not GOOGLE_API_AVAILABLE:
                raise ImportError(
                    "google-api-python-client가 필요합니다.\n"
                    "pip install google-api-python-client google-auth-oauthlib"
                )
            self._authenticate()

    def _authenticate(self):
        """YouTube OAuth2 인증"""
        credentials_path = Path("secrets/credentials.json")
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"인증 파일이 없습니다: {credentials_path}\n"
                "python scripts/reauth_youtube.py 실행 후 다시 시도하세요."
            )

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

    def post_quote(
        self,
        book_title: str,
        language: str = "ko",
        author: Optional[str] = None,
        image_path: Optional[str] = None,
    ) -> bool:
        """
        책 인용구 커뮤니티 포스트 게시

        Args:
            book_title: 책 제목
            language: 언어
            author: 저자 이름
            image_path: 첨부 이미지 경로 (선택)

        Returns:
            성공 여부
        """
        quotes = _extract_quotes_from_summary(book_title, language, count=3)
        if not quotes:
            safe_title = get_standard_safe_title(book_title)
            if language == "ko":
                quotes = [f"{book_title}은(는) 우리 삶에 깊은 통찰을 제공합니다."]
            else:
                en_t = translate_book_title(book_title) if not is_english_title(book_title) else book_title
                quotes = [f"{en_t} provides profound insights into our lives."]

        import random
        quote = random.choice(quotes)
        post_text = _build_quote_post_text(book_title, quote, language, author)

        self.logger.info(f"\n📝 인용구 포스트 미리보기:")
        print("─" * 60)
        print(post_text)
        print("─" * 60)

        if self.dry_run:
            self.logger.info("  [dry-run] 실제 포스팅 스킵")
            return True

        try:
            # YouTube Community Posts API (communityPosts.insert)
            # 참고: 현재 공식 API가 제한적으로 제공됨
            body = {
                "snippet": {
                    "type": "textPost",
                    "textOriginal": post_text,
                }
            }
            resp = self.youtube.communityPosts().insert(part="snippet", body=body).execute()
            post_id = resp.get("id", "unknown")
            self.logger.info(f"✅ 포스트 게시 완료: {post_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 포스트 게시 실패: {e}")
            self.logger.info(
                "💡 Note: YouTube Community Posts API는 일부 채널에만 제한적으로 제공됩니다.\n"
                "   채널이 커뮤니티 탭 활성화 조건(구독자 500명 이상)을 충족해야 합니다."
            )
            return False

    def post_vote(
        self,
        candidates: List[str],
        language: str = "ko",
    ) -> bool:
        """
        다음 리뷰 투표 포스트 게시

        Args:
            candidates: 투표 선택지 (최대 4개)
            language: 언어

        Returns:
            성공 여부
        """
        vote_data = _build_vote_post_text(candidates[:4], language)

        self.logger.info(f"\n📊 투표 포스트 미리보기:")
        print("─" * 60)
        print(vote_data["question"])
        for i, choice in enumerate(vote_data["choices"], 1):
            print(f"  {i}. {choice}")
        print("─" * 60)

        if self.dry_run:
            self.logger.info("  [dry-run] 실제 포스팅 스킵")
            return True

        try:
            body = {
                "snippet": {
                    "type": "pollPost",
                    "textOriginal": vote_data["question"],
                    "pollOptions": [
                        {"text": choice} for choice in vote_data["choices"]
                    ],
                }
            }
            resp = self.youtube.communityPosts().insert(part="snippet", body=body).execute()
            post_id = resp.get("id", "unknown")
            self.logger.info(f"✅ 투표 포스트 게시 완료: {post_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 투표 포스트 게시 실패: {e}")
            return False

    def post_update(self, message: str, language: str = "ko") -> bool:
        """
        근황/소식 포스트 게시

        Args:
            message: 포스트 메시지
            language: 언어

        Returns:
            성공 여부
        """
        post_text = _build_update_post_text(message, language)

        self.logger.info(f"\n📢 근황 포스트 미리보기:")
        print("─" * 60)
        print(post_text)
        print("─" * 60)

        if self.dry_run:
            self.logger.info("  [dry-run] 실제 포스팅 스킵")
            return True

        try:
            body = {
                "snippet": {
                    "type": "textPost",
                    "textOriginal": post_text,
                }
            }
            resp = self.youtube.communityPosts().insert(part="snippet", body=body).execute()
            post_id = resp.get("id", "unknown")
            self.logger.info(f"✅ 근황 포스트 게시 완료: {post_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 근황 포스트 게시 실패: {e}")
            return False

    def generate_weekly_posts(
        self,
        csv_path: str = "ildangbaek_books.csv",
        language: str = "ko",
    ) -> List[Dict]:
        """
        주간 커뮤니티 포스트 계획 생성

        CSV에서 최근 업로드된 책을 기반으로 주 3회 포스트 계획을 생성합니다.
        월: 책 인용구, 수: 다음 리뷰 투표, 금: 근황

        Returns:
            주간 포스트 계획 리스트
        """
        import csv
        from datetime import datetime, timedelta

        posts_plan = []

        try:
            recent_books = []
            upcoming_books = []

            csv_file = Path(csv_path)
            if csv_file.exists():
                with open(csv_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        title = row.get("title", row.get("book_title", ""))
                        status = row.get("status", "")
                        if title and status == "uploaded":
                            recent_books.append(title)
                        elif title and status not in ("uploaded", "skipped"):
                            upcoming_books.append(title)

            today = datetime.now()
            # 이번 주 월요일 계산
            monday = today - timedelta(days=today.weekday())

            if recent_books:
                # 월: 최근 업로드 책 인용구 포스트
                book = recent_books[-1]
                quotes = _extract_quotes_from_summary(book, language)
                quote = quotes[0] if quotes else f"{book}의 핵심 메시지를 확인하세요."
                posts_plan.append({
                    "date": monday.strftime("%Y-%m-%d (월)"),
                    "type": "quote",
                    "book": book,
                    "content": _build_quote_post_text(book, quote, language),
                })

            # 수: 다음 리뷰 투표
            vote_candidates = upcoming_books[:4] if upcoming_books else ["추천 책을 댓글로 알려주세요!"]
            if vote_candidates:
                wednesday = monday + timedelta(days=2)
                vote_data = _build_vote_post_text(vote_candidates, language)
                posts_plan.append({
                    "date": wednesday.strftime("%Y-%m-%d (수)"),
                    "type": "vote",
                    "content": vote_data["question"],
                    "choices": vote_data["choices"],
                })

            # 금: 근황 포스트
            friday = monday + timedelta(days=4)
            if language == "ko":
                update_msg = f"이번 주도 열심히 준비 중입니다! 다음 영상도 기대해주세요 📚"
            else:
                update_msg = "Working hard this week! Stay tuned for the next video 📚"
            posts_plan.append({
                "date": friday.strftime("%Y-%m-%d (금)"),
                "type": "update",
                "content": _build_update_post_text(update_msg, language),
            })

        except Exception as e:
            self.logger.error(f"주간 포스트 계획 생성 실패: {e}")

        return posts_plan


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 커뮤니티 탭 자동 포스팅",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--apply", action="store_true", help="실제로 포스트를 게시합니다 (기본값: dry-run)")
    parser.add_argument(
        "--type",
        choices=["quote", "vote", "update", "weekly"],
        default="quote",
        help="포스트 유형 (기본값: quote)",
    )
    parser.add_argument("--book-title", help="책 제목 (quote 유형에 필요)")
    parser.add_argument("--author", help="저자 이름 (선택)")
    parser.add_argument("--language", default="ko", choices=["ko", "en"], help="언어 (기본값: ko)")
    parser.add_argument(
        "--candidates",
        help="투표 선택지 (쉼표로 구분, vote 유형에 필요). 예: \"책1,책2,책3,책4\"",
    )
    parser.add_argument("--message", help="근황 메시지 (update 유형에 필요)")
    parser.add_argument("--csv", default="ildangbaek_books.csv", help="책 목록 CSV 경로")

    args = parser.parse_args()

    dry_run = not args.apply
    manager = CommunityPostManager(dry_run=dry_run)

    if dry_run:
        print("🔍 Dry-run 모드: 실제 포스팅 없이 미리보기만 표시합니다.")
        print("  실제 포스팅하려면 --apply 플래그를 추가하세요.\n")

    if args.type == "quote":
        if not args.book_title:
            print("❌ --book-title을 지정해야 합니다.")
            sys.exit(1)
        manager.post_quote(args.book_title, args.language, args.author)

    elif args.type == "vote":
        if not args.candidates:
            print("❌ --candidates를 지정해야 합니다. (쉼표로 구분)")
            sys.exit(1)
        candidates = [c.strip() for c in args.candidates.split(",")]
        manager.post_vote(candidates, args.language)

    elif args.type == "update":
        if not args.message:
            print("❌ --message를 지정해야 합니다.")
            sys.exit(1)
        manager.post_update(args.message, args.language)

    elif args.type == "weekly":
        plans = manager.generate_weekly_posts(args.csv, args.language)
        print(f"\n📅 이번 주 커뮤니티 포스트 계획 ({len(plans)}개):")
        for plan in plans:
            print(f"\n{'─'*60}")
            print(f"📆 {plan['date']} ({plan['type']})")
            print(plan.get("content", ""))
            if "choices" in plan:
                for i, c in enumerate(plan["choices"], 1):
                    print(f"  {i}. {c}")


if __name__ == "__main__":
    main()
