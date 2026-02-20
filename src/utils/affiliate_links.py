"""
제휴 링크(Affiliate Link) 생성 모듈

YouTube 영상 description에 자동으로 제휴 구매 링크를 삽입합니다.
Amazon Associates, 알라딘 파트너스를 지원합니다.
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


def generate_affiliate_section(
    book_title_ko: str,
    book_title_en: str,
    author_ko: str = "",  # Reserved for future use
    author_en: str = "",  # Reserved for future use
    language: str = "ko",
    isbn_ko: str = "",
    isbn_en: str = ""
) -> str:
    """
    제휴 링크 섹션을 생성합니다.

    Args:
        book_title_ko: 한글 책 제목
        book_title_en: 영문 책 제목
        author_ko: 한글 저자명 (선택)
        author_en: 영문 저자명 (선택)
        language: 언어 ('ko' 또는 'en')
        isbn_ko: 한국판 ISBN-13 또는 ISBN-10 (알라딘 직접 링크용)
        isbn_en: 영문판 ISBN-13 또는 ISBN-10 (Amazon 직접 검색용)

    Returns:
        포맷된 제휴 링크 섹션 문자열. 제휴 ID가 없으면 빈 문자열 반환.
    """
    # 제휴 ID 로드
    amazon_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "").strip()
    aladin_id = os.getenv("ALADIN_PARTNER_ID", "").strip()

    # 제휴 ID가 하나도 없으면 빈 문자열 반환
    if not amazon_tag and not aladin_id:
        return ""

    # ISBN 정규화 (하이픈 제거)
    isbn_ko_clean = isbn_ko.replace("-", "").strip() if isbn_ko else ""
    isbn_en_clean = isbn_en.replace("-", "").strip() if isbn_en else ""

    links = []
    header = ""
    footer = ""

    # 한글 영상: 알라딘 + Amazon
    if language == "ko":
        # 알라딘: 한국판 ISBN → 영문판 ISBN → 한글 제목 검색 순으로 시도
        if aladin_id:
            if isbn_ko_clean:
                aladin_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ISBN={isbn_ko_clean}&partner={aladin_id}"
            elif isbn_en_clean:
                aladin_url = f"https://www.aladin.co.kr/shop/wproduct.aspx?ISBN={isbn_en_clean}&partner={aladin_id}"
            elif book_title_ko:
                encoded_korean = quote_plus(book_title_ko)
                aladin_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={encoded_korean}&partner={aladin_id}"
            else:
                aladin_url = None
            if aladin_url:
                links.append(f"  알라딘: {aladin_url}")

        # Amazon: 영문판 ISBN 검색 또는 영문/한글 제목 검색
        if amazon_tag:
            if isbn_en_clean:
                amazon_search_term = isbn_en_clean
            elif book_title_en and book_title_en.strip():
                amazon_search_term = book_title_en
            elif book_title_ko:
                amazon_search_term = book_title_ko
            else:
                amazon_search_term = None
            if amazon_search_term:
                encoded_amazon = quote_plus(amazon_search_term)
                amazon_url = f"https://www.amazon.com/s?k={encoded_amazon}&tag={amazon_tag}"
                links.append(f"  Amazon: {amazon_url}")

        if links:
            header = "📖 이 책 구매하기:"
            footer = "(위 링크를 통해 구매하시면 채널 운영에 도움이 됩니다)"

    # 영문 영상: Amazon만 (영문판 ISBN 우선)
    else:
        if amazon_tag:
            if isbn_en_clean:
                amazon_search_term = isbn_en_clean
            elif book_title_en and book_title_en.strip():
                amazon_search_term = book_title_en
            elif book_title_ko:
                amazon_search_term = book_title_ko
            else:
                amazon_search_term = None
            if amazon_search_term:
                encoded_amazon = quote_plus(amazon_search_term)
                amazon_url = f"https://www.amazon.com/s?k={encoded_amazon}&tag={amazon_tag}"
                links.append(f"  Amazon: {amazon_url}")

        if links:
            header = "📖 Get this book:"
            footer = "(Purchasing through this link supports our channel)"

    # 링크가 없으면 빈 문자열 반환
    if not links:
        return ""

    # 최종 포맷
    section = f"\n{header}\n"
    section += "\n".join(links)
    section += f"\n{footer}\n"

    return section
