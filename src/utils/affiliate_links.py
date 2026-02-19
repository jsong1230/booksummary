"""
제휴 링크(Affiliate Link) 생성 모듈

YouTube 영상 description에 자동으로 제휴 구매 링크를 삽입합니다.
Amazon Associates, 알라딘 파트너스, Yes24 제휴 프로그램을 지원합니다.
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
    language: str = "ko"
) -> str:
    """
    제휴 링크 섹션을 생성합니다.

    Args:
        book_title_ko: 한글 책 제목
        book_title_en: 영문 책 제목
        author_ko: 한글 저자명 (선택)
        author_en: 영문 저자명 (선택)
        language: 언어 ('ko' 또는 'en')

    Returns:
        포맷된 제휴 링크 섹션 문자열. 제휴 ID가 없으면 빈 문자열 반환.
    """
    # 제휴 ID 로드
    amazon_tag = os.getenv("AMAZON_ASSOCIATE_TAG", "").strip()
    aladin_id = os.getenv("ALADIN_PARTNER_ID", "").strip()
    yes24_id = os.getenv("YES24_PARTNER_ID", "").strip()

    # 제휴 ID가 하나도 없으면 빈 문자열 반환
    if not amazon_tag and not aladin_id and not yes24_id:
        return ""

    # Note: author_ko and author_en params are kept for API compatibility but not used
    # in search terms - title-only search produces better results

    # 검색어 생성 (책 제목만 사용 - 작가명 포함 시 검색 정확도 저하)

    # Amazon용 영문 검색어 (책 제목만 사용 - 작가명 제외하면 검색 정확도 향상)
    amazon_search_term = ""
    if book_title_en and book_title_en.strip():
        amazon_search_term = book_title_en
    elif book_title_ko:  # 영문 제목이 없으면 한글 사용 (폴백)
        amazon_search_term = book_title_ko

    # 알라딘/Yes24용 한글 검색어 (책 제목만 사용 - 작가명 제외하면 검색 정확도 향상)
    korean_search_term = ""
    if book_title_ko:
        korean_search_term = book_title_ko

    links = []
    header = ""
    footer = ""

    # 한글 영상: 알라딘 + Yes24 + Amazon
    if language == "ko":
        # 알라딘: 한글 검색어
        if aladin_id and korean_search_term:
            encoded_korean = quote_plus(korean_search_term)
            aladin_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={encoded_korean}&partner={aladin_id}"
            links.append(f"  알라딘: {aladin_url}")

        # Yes24: 한글 검색어
        if yes24_id and korean_search_term:
            encoded_korean = quote_plus(korean_search_term)
            yes24_url = f"https://www.yes24.com/Product/Search?domain=ALL&query={encoded_korean}&partner={yes24_id}"
            links.append(f"  Yes24: {yes24_url}")

        # Amazon: 영문 검색어
        if amazon_tag and amazon_search_term:
            encoded_amazon = quote_plus(amazon_search_term)
            amazon_url = f"https://www.amazon.com/s?k={encoded_amazon}&tag={amazon_tag}"
            links.append(f"  Amazon: {amazon_url}")

        if links:
            header = "📖 이 책 구매하기:"
            footer = "(위 링크를 통해 구매하시면 채널 운영에 도움이 됩니다)"

    # 영문 영상: Amazon만 (영문 검색어)
    else:
        if amazon_tag and amazon_search_term:
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
