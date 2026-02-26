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
    isbn_en: str = "",
    validate: bool = False,
    validate_delay: float = 0.5,
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
        validate: True면 생성된 URL의 유효성을 HTTP 요청으로 검사 후 무효 링크 제외
        validate_delay: 링크 검사 요청 간 대기 시간 (초)

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

    # 검색어 정제: `:` 이후 저자명 제거 (예: "인간 실격: 다자이 오사무" → "인간 실격")
    search_ko = book_title_ko.split(':')[0].strip() if book_title_ko else ""
    search_en = book_title_en.split(':')[0].strip() if book_title_en else ""

    links = []
    header = ""
    footer = ""

    # 한글 영상: 알라딘 + Amazon
    if language == "ko":
        # 알라딘: 한글 책 제목으로만 검색
        if aladin_id:
            if search_ko:
                encoded_korean = quote_plus(search_ko)
                aladin_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={encoded_korean}&partner={aladin_id}"
            else:
                aladin_url = None
            if aladin_url:
                links.append(f"  알라딘: {aladin_url}")

        # Amazon: 영문 책 제목으로만 검색 (없으면 한글 제목)
        if amazon_tag:
            if search_en:
                amazon_search_term = search_en
            elif search_ko:
                amazon_search_term = search_ko
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
        # 영문 영상: Amazon만 (영문 책 제목으로만 검색)
        if amazon_tag:
            if search_en:
                amazon_search_term = search_en
            elif search_ko:
                amazon_search_term = search_ko
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

    # 유효성 검사: validate=True인 경우 HTTP 요청으로 각 URL 확인
    if validate:
        from src.utils.link_validator import validate_purchase_url
        import re as _re
        _url_re = _re.compile(r"https?://[^\s]+")
        validated_links = []
        for line in links:
            urls = _url_re.findall(line)
            if not urls:
                validated_links.append(line)
                continue
            url = urls[0].rstrip(".,;)\"'")
            is_valid, reason = validate_purchase_url(url, delay=validate_delay)
            if is_valid:
                validated_links.append(line)
            else:
                print(f"   ⚠️ 유효하지 않은 링크 제외: {url} ({reason})")
        links = validated_links

    if not links:
        return ""

    # 최종 포맷
    section = f"\n{header}\n"
    section += "\n".join(links)
    section += f"\n{footer}\n"

    return section
