#!/usr/bin/env python3
"""
썸네일 A/B 테스트 관리 스크립트

영상별 2개 썸네일 변형(A/B)을 관리합니다.
- 변형 A로 업로드 후 48시간 경과 시 CTR 확인
- CTR 3% 미만이면 변형 B로 자동 교체
- 결과를 data/thumbnail_ab_test.csv에 기록

사용법:
  # 새 A/B 테스트 등록 (썸네일 A 업로드 포함)
  python src/29_thumbnail_ab_test.py register \
    --video-id VIDEO_ID \
    --thumbnail-a output/book_thumbnail_ko_A.jpg \
    --thumbnail-b output/book_thumbnail_ko_B.jpg \
    --book-title "책 제목"

  # CTR 확인 및 필요 시 B로 전환 (cron 또는 수동 실행)
  python src/29_thumbnail_ab_test.py check

  # 현재 테스트 목록 보기
  python src/29_thumbnail_ab_test.py list

  # 특정 테스트 결과 적용 (수동으로 B로 전환)
  python src/29_thumbnail_ab_test.py switch --video-id VIDEO_ID
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

AB_TEST_CSV = project_root / "data" / "thumbnail_ab_test.csv"
AB_TEST_CSV_FIELDS = [
    "video_id", "book_title", "language",
    "thumbnail_a", "thumbnail_b",
    "current_variant",  # "A" or "B"
    "start_date",       # ISO datetime A 업로드 시점
    "check_date",       # ISO datetime 언제 확인했는지
    "ctr_a",            # A 썸네일 CTR (%)
    "ctr_b",            # B 썸네일 CTR (%)
    "status",           # "testing" | "switched_to_b" | "kept_a" | "manual"
    "notes",
]
CTR_THRESHOLD = 3.0       # CTR 3% 미만이면 B로 전환
CHECK_DELAY_HOURS = 48    # A 업로드 후 48시간 후 확인


def _load_youtube_api():
    """YouTube Data API 클라이언트 로드"""
    credentials_path = project_root / "secrets" / "credentials.json"
    if not credentials_path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/youtube"],
        )
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"  ⚠️ YouTube API 초기화 실패: {e}")
        return None


def _load_analytics_api():
    """YouTube Analytics API 클라이언트 로드"""
    credentials_path = project_root / "secrets" / "credentials.json"
    if not credentials_path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(
            str(credentials_path),
            scopes=[
                "https://www.googleapis.com/auth/youtube",
                "https://www.googleapis.com/auth/yt-analytics.readonly",
            ],
        )
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return build("youtubeAnalytics", "v2", credentials=creds)
    except Exception as e:
        print(f"  ⚠️ Analytics API 초기화 실패: {e}")
        return None


def _load_ab_tests() -> List[Dict]:
    """A/B 테스트 CSV 로드"""
    if not AB_TEST_CSV.exists():
        return []
    rows = []
    with open(AB_TEST_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def _save_ab_tests(rows: List[Dict]):
    """A/B 테스트 CSV 저장"""
    AB_TEST_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(AB_TEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AB_TEST_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _get_video_ctr(analytics, video_id: str, start_date: str, end_date: str) -> Optional[float]:
    """YouTube Analytics에서 CTR 조회 (%)"""
    try:
        response = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="impressions,impressionClickThroughRate",
            dimensions="video",
            filters=f"video=={video_id}",
        ).execute()
        rows = response.get("rows", [])
        if rows:
            # impressionClickThroughRate는 0~1 사이 값 (YouTube Analytics 반환)
            ctr_raw = float(rows[0][2])
            return round(ctr_raw * 100, 2)
    except Exception as e:
        print(f"  ⚠️ CTR 조회 실패 ({video_id}): {e}")
    return None


def _set_thumbnail(youtube, video_id: str, thumbnail_path: str) -> bool:
    """YouTube 썸네일 업로드"""
    thumb_path = Path(thumbnail_path)
    if not thumb_path.exists():
        print(f"  ❌ 썸네일 파일 없음: {thumbnail_path}")
        return False
    try:
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(str(thumb_path), mimetype="image/jpeg")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=media,
        ).execute()
        print(f"  ✅ 썸네일 업로드 완료: {thumb_path.name}")
        return True
    except Exception as e:
        print(f"  ❌ 썸네일 업로드 실패: {e}")
        return False


def cmd_register(args):
    """새 A/B 테스트 등록 및 썸네일 A 업로드"""
    logger = get_logger(__name__)
    rows = _load_ab_tests()

    # 중복 확인
    existing = [r for r in rows if r["video_id"] == args.video_id]
    if existing:
        print(f"  ⚠️ 이미 등록된 테스트: {args.video_id}")
        return

    if not args.dry_run:
        youtube = _load_youtube_api()
        if youtube:
            print(f"📸 썸네일 A 업로드 중: {args.thumbnail_a}")
            _set_thumbnail(youtube, args.video_id, args.thumbnail_a)
        else:
            print("  ⚠️ YouTube API 없음, 썸네일 업로드 건너뜀")
    else:
        print(f"[DRY-RUN] 썸네일 A 업로드: {args.thumbnail_a} → video {args.video_id}")

    new_row = {
        "video_id": args.video_id,
        "book_title": args.book_title or "",
        "language": args.language,
        "thumbnail_a": args.thumbnail_a,
        "thumbnail_b": args.thumbnail_b,
        "current_variant": "A",
        "start_date": datetime.now().isoformat(),
        "check_date": "",
        "ctr_a": "",
        "ctr_b": "",
        "status": "testing",
        "notes": args.notes or "",
    }
    rows.append(new_row)
    _save_ab_tests(rows)
    print(f"\n✅ A/B 테스트 등록 완료")
    print(f"   영상: {args.video_id}")
    print(f"   책: {args.book_title}")
    print(f"   확인 예정: {(datetime.now() + timedelta(hours=CHECK_DELAY_HOURS)).strftime('%Y-%m-%d %H:%M')}")


def cmd_check(args):
    """48시간 경과 테스트의 CTR 확인 및 필요 시 B로 전환"""
    logger = get_logger(__name__)
    rows = _load_ab_tests()
    now = datetime.now()
    analytics = _load_analytics_api() if not args.dry_run else None
    youtube = _load_youtube_api() if not args.dry_run else None
    updated = False

    for row in rows:
        if row["status"] not in ("testing",):
            continue

        start = datetime.fromisoformat(row["start_date"])
        elapsed_hours = (now - start).total_seconds() / 3600

        if elapsed_hours < CHECK_DELAY_HOURS:
            remaining = CHECK_DELAY_HOURS - elapsed_hours
            print(f"⏳ {row['video_id']} ({row['book_title']}): 확인까지 {remaining:.0f}시간 남음")
            continue

        print(f"\n🔍 CTR 확인: {row['video_id']} ({row['book_title']})")

        # A 변형 CTR 조회
        start_str = start.strftime("%Y-%m-%d")
        end_str = now.strftime("%Y-%m-%d")
        ctr_a = None
        if analytics:
            ctr_a = _get_video_ctr(analytics, row["video_id"], start_str, end_str)

        if ctr_a is None:
            print(f"  ⚠️ CTR 조회 실패 (Analytics API 확인 필요)")
            if args.dry_run:
                print(f"  [DRY-RUN] 가상 CTR: 2.1%")
                ctr_a = 2.1
            else:
                continue

        row["ctr_a"] = str(ctr_a)
        row["check_date"] = now.isoformat()
        print(f"  📊 변형 A CTR: {ctr_a}%  (기준: {CTR_THRESHOLD}%)")

        if ctr_a < CTR_THRESHOLD:
            print(f"  📉 CTR {ctr_a}% < {CTR_THRESHOLD}% → 변형 B로 전환")
            if not args.dry_run and youtube:
                success = _set_thumbnail(youtube, row["video_id"], row["thumbnail_b"])
                if success:
                    row["current_variant"] = "B"
                    row["status"] = "switched_to_b"
                    updated = True
            else:
                print(f"  [DRY-RUN] 썸네일 B 업로드: {row['thumbnail_b']} → video {row['video_id']}")
                row["current_variant"] = "B"
                row["status"] = "switched_to_b"
                updated = True
        else:
            print(f"  ✅ CTR {ctr_a}% ≥ {CTR_THRESHOLD}% → 변형 A 유지")
            row["status"] = "kept_a"
            updated = True

    if updated:
        _save_ab_tests(rows)
        print(f"\n✅ 테스트 결과 저장 완료: {AB_TEST_CSV}")


def cmd_list(args):
    """현재 A/B 테스트 목록 표시"""
    rows = _load_ab_tests()
    if not rows:
        print("등록된 A/B 테스트가 없습니다.")
        return

    print(f"\n{'='*70}")
    print(f"{'영상ID':<20} {'책제목':<20} {'변형':<6} {'CTR-A':<8} {'상태':<15}")
    print(f"{'='*70}")
    for row in rows:
        ctr_display = f"{row['ctr_a']}%" if row['ctr_a'] else "-"
        print(f"{row['video_id']:<20} {row['book_title'][:18]:<20} {row['current_variant']:<6} {ctr_display:<8} {row['status']:<15}")
    print(f"{'='*70}")
    print(f"총 {len(rows)}개 테스트 | CTR 기준: {CTR_THRESHOLD}% | 확인 주기: {CHECK_DELAY_HOURS}시간")


def cmd_switch(args):
    """수동으로 B 변형으로 전환"""
    rows = _load_ab_tests()
    for row in rows:
        if row["video_id"] == args.video_id:
            if not args.dry_run:
                youtube = _load_youtube_api()
                if youtube:
                    _set_thumbnail(youtube, args.video_id, row["thumbnail_b"])
            else:
                print(f"[DRY-RUN] 썸네일 B 업로드: {row['thumbnail_b']}")
            row["current_variant"] = "B"
            row["status"] = "manual"
            row["check_date"] = datetime.now().isoformat()
            _save_ab_tests(rows)
            print(f"✅ {args.video_id} → 변형 B로 전환 완료")
            return
    print(f"❌ 테스트를 찾을 수 없음: {args.video_id}")


def main():
    parser = argparse.ArgumentParser(description="썸네일 A/B 테스트 관리")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="미리보기 (기본값, 실제 변경 없음)")
    parser.add_argument("--apply", action="store_true",
                        help="실제 적용 (썸네일 업로드/변경)")

    subparsers = parser.add_subparsers(dest="command")

    # register
    reg = subparsers.add_parser("register", help="새 A/B 테스트 등록")
    reg.add_argument("--video-id", required=True, help="YouTube 영상 ID")
    reg.add_argument("--thumbnail-a", required=True, help="변형 A 썸네일 경로 (질문형)")
    reg.add_argument("--thumbnail-b", required=True, help="변형 B 썸네일 경로 (진술형)")
    reg.add_argument("--book-title", default="", help="책 제목")
    reg.add_argument("--language", default="ko", help="언어 (ko/en)")
    reg.add_argument("--notes", default="", help="메모")

    # check
    subparsers.add_parser("check", help="CTR 확인 및 자동 전환")

    # list
    subparsers.add_parser("list", help="테스트 목록 보기")

    # switch
    sw = subparsers.add_parser("switch", help="수동으로 B로 전환")
    sw.add_argument("--video-id", required=True, help="YouTube 영상 ID")

    args = parser.parse_args()

    # --apply가 있으면 dry_run=False
    if hasattr(args, "apply") and args.apply:
        args.dry_run = False

    if not args.command:
        parser.print_help()
        return

    if args.command == "register":
        cmd_register(args)
    elif args.command == "check":
        cmd_check(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "switch":
        cmd_switch(args)


if __name__ == "__main__":
    main()
