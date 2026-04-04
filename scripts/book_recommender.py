#!/usr/bin/env python3
"""
책 선정 자동화 스크립트
- 알라딘 베스트셀러 크롤링 (Top 100)
- uploaded_books.csv 중복 제거
- Claude API로 채널 스타일에 맞는 Top 5 추천

Usage:
    python scripts/book_recommender.py
    python scripts/book_recommender.py --output data/book_recommendations.md
    python scripts/book_recommender.py --limit 10
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent


def get_uploaded_books() -> set[str]:
    """이미 업로드된 책 제목 목록 (한글 + 영문)"""
    uploaded = set()
    csv_path = PROJECT_ROOT / "data" / "uploaded_books.csv"
    if csv_path.exists():
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("title_ko"):
                    uploaded.add(row["title_ko"].strip())
                if row.get("title_en"):
                    uploaded.add(row["title_en"].strip().lower())
    return uploaded


def fetch_aladin_bestsellers(limit: int = 100) -> list[dict]:
    """알라딘 베스트셀러 크롤링 (API 또는 HTML)"""
    api_key = os.getenv("ALADIN_TTB_KEY")

    if api_key:
        return _fetch_aladin_api(api_key, limit)
    else:
        return _fetch_aladin_scrape(limit)


def _fetch_aladin_api(api_key: str, limit: int) -> list[dict]:
    """알라딘 Open API 사용 (TTB 키 필요)"""
    books = []
    # 알라딘 API: 최대 50개씩
    for start in range(1, min(limit, 200), 50):
        url = "http://www.aladin.co.kr/ttb/api/ItemList.aspx"
        params = {
            "ttbkey": api_key,
            "QueryType": "Bestseller",
            "MaxResults": min(50, limit - len(books)),
            "start": start,
            "SearchTarget": "Book",
            "output": "js",
            "Version": "20131101",
            "CategoryId": 0,  # 전체
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            for item in data.get("item", []):
                books.append({
                    "title": item.get("title", "").split(" - ")[0].strip(),
                    "author": item.get("author", ""),
                    "rank": len(books) + 1,
                    "category": item.get("categoryName", ""),
                    "source": "aladin_api",
                })
            if len(books) >= limit:
                break
        except Exception as e:
            print(f"알라딘 API 오류: {e}", file=sys.stderr)
            break

    return books


def _fetch_aladin_scrape(limit: int) -> list[dict]:
    """알라딘 베스트셀러 페이지 크롤링 (API 키 없을 때)"""
    books = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    # 종합 베스트셀러 (국내도서 + 외국도서)
    urls = [
        "https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=Bestseller&BranchType=1&CID=0&start=1",
        "https://www.aladin.co.kr/shop/common/wbest.aspx?BestType=Bestseller&BranchType=1&CID=0&start=51",
    ]

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            # 책 제목 파싱 (알라딘 HTML 구조 기반)
            titles = re.findall(
                r'class="bo3"[^>]*>\s*<a[^>]*>([^<]+)</a>', resp.text
            )
            authors = re.findall(
                r'class="ss_author"[^>]*>([^<]+)</a>', resp.text
            )
            for i, title in enumerate(titles):
                if len(books) >= limit:
                    break
                books.append({
                    "title": title.strip(),
                    "author": authors[i].strip() if i < len(authors) else "",
                    "rank": len(books) + 1,
                    "category": "베스트셀러",
                    "source": "aladin_scrape",
                })
            if len(books) >= limit:
                break
        except Exception as e:
            print(f"알라딘 크롤링 오류: {e}", file=sys.stderr)

    # 크롤링 실패 시 교보문고 시도
    if not books:
        books = _fetch_kyobo_scrape(limit)

    return books


def _fetch_kyobo_scrape(limit: int) -> list[dict]:
    """교보문고 베스트셀러 크롤링 (백업)"""
    books = []
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://product.kyobobook.co.kr/best?period=002&type=001&gbCode=TOT&pageSize=100"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r'"book_name"\s*:\s*"([^"]+)"', resp.text)
        authors = re.findall(r'"author"\s*:\s*"([^"]+)"', resp.text)
        for i, title in enumerate(titles[:limit]):
            books.append({
                "title": title.strip(),
                "author": authors[i].strip() if i < len(authors) else "",
                "rank": i + 1,
                "category": "베스트셀러",
                "source": "kyobo_scrape",
            })
    except Exception as e:
        print(f"교보문고 크롤링 오류: {e}", file=sys.stderr)
    return books


def filter_already_uploaded(books: list[dict], uploaded: set[str]) -> list[dict]:
    """이미 업로드된 책 제거"""
    filtered = []
    for book in books:
        title = book["title"]
        if title not in uploaded and title.lower() not in uploaded:
            filtered.append(book)
    return filtered


def get_claude_recommendations(
    books: list[dict], uploaded_sample: list[str], top_n: int = 5
) -> str:
    """Claude API로 채널 스타일에 맞는 책 추천"""
    try:
        import anthropic
    except ImportError:
        return _simple_recommendation(books, top_n)

    client = anthropic.Anthropic()

    book_list = "\n".join(
        f"{i+1}. {b['title']} - {b['author']} (순위: {b['rank']})"
        for i, b in enumerate(books[:50])
    )

    uploaded_list = "\n".join(f"- {t}" for t in uploaded_sample[:30])

    prompt = f"""당신은 책 요약 YouTube 채널의 큐레이터입니다.
이 채널의 특성:
- 한국어/영어 책 요약 영상 제작 (이미 업로드한 책 147권)
- 철학, 문학, 역사, 사회과학, 자기계발 등 폭넓은 장르
- 영상 제목 포맷: "[일당백] 책제목: 저자명" 또는 "Summary+Video" 스타일
- 이미 업로드한 책 예시:
{uploaded_list}

현재 베스트셀러 목록 (아직 업로드 안 된 책들):
{book_list}

위 베스트셀러 중에서 이 채널에 가장 적합한 책 {top_n}권을 추천해주세요.

선정 기준:
1. 채널 기존 컨텐츠와 어울리는 주제 (너무 같거나 너무 다르지 않게)
2. 한국 독자에게 잘 알려진 책 (번역서 포함)
3. 영상화하기 좋은 스토리텔링 요소 있는 책
4. 현재 화제성/시의성

각 책에 대해 다음 형식으로 답변:
## 1. [책 제목]
- **저자**: [저자명]
- **베스트셀러 순위**: [순위]위
- **추천 이유**: [2-3문장, 채널 스타일과 맞는 이유 + 현재 화제성]
- **예상 썸네일 훅**: [시청자 관심 끌 한 줄 문장]
- **스타일 추천**: [일당백 / summary+video 중 어느 게 더 적합한지]"""

    try:
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        print(f"Claude API 오류: {e}", file=sys.stderr)
        return _simple_recommendation(books, top_n)


def _simple_recommendation(books: list[dict], top_n: int) -> str:
    """Claude API 없을 때 간단한 순위 기반 추천"""
    result = []
    for i, book in enumerate(books[:top_n]):
        result.append(f"## {i+1}. {book['title']}\n- 저자: {book['author']}\n- 베스트셀러 {book['rank']}위")
    return "\n\n".join(result)


def save_recommendations(content: str, output_path: Path, books_fetched: int, books_filtered: int):
    """추천 결과를 마크다운으로 저장"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md = f"""# 주간 책 추천 리스트

생성일: {now}
베스트셀러 수집: {books_fetched}권 → 미업로드: {books_filtered}권

---

{content}

---

> 이 리스트는 `python scripts/book_recommender.py`로 자동 생성됩니다.
> 최종 선정은 사용자가 결정합니다.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"추천 리스트 저장: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="책 선정 자동화 스크립트")
    parser.add_argument("--output", default="data/book_recommendations.md", help="출력 파일 경로")
    parser.add_argument("--limit", type=int, default=100, help="베스트셀러 수집 개수")
    parser.add_argument("--top", type=int, default=5, help="추천 책 수")
    parser.add_argument("--dry-run", action="store_true", help="Claude API 호출 없이 크롤링만")
    args = parser.parse_args()

    print("📚 베스트셀러 수집 중...")
    books = fetch_aladin_bestsellers(args.limit)
    if not books:
        print("❌ 베스트셀러 수집 실패. 네트워크 확인 또는 ALADIN_TTB_KEY 설정 필요")
        sys.exit(1)
    print(f"✅ {len(books)}권 수집 완료")

    print("🔍 업로드 이력 확인 중...")
    uploaded = get_uploaded_books()
    filtered = filter_already_uploaded(books, uploaded)
    print(f"✅ 미업로드 책: {len(filtered)}권")

    if not filtered:
        print("모든 베스트셀러가 이미 업로드됨")
        sys.exit(0)

    if args.dry_run:
        print("\n--- 미업로드 베스트셀러 (상위 10위) ---")
        for book in filtered[:10]:
            print(f"{book['rank']}위: {book['title']} - {book['author']}")
        return

    print(f"🤖 Claude가 Top {args.top} 추천 중...")
    uploaded_sample = list(uploaded)[:30]
    recommendations = get_claude_recommendations(filtered, uploaded_sample, args.top)

    output_path = PROJECT_ROOT / args.output
    save_recommendations(recommendations, output_path, len(books), len(filtered))

    print("\n" + "="*50)
    print(recommendations)


if __name__ == "__main__":
    main()
