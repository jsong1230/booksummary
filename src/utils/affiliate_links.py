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
    author_ko: str = "",
    author_en: str = "",
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

    # 검색어 생성 (책 제목 + 저자명)
    if language == "ko":
        search_term = book_title_ko
        if author_ko:
            search_term += f" {author_ko}"
    else:
        search_term = book_title_en
        if author_en:
            search_term += f" {author_en}"

    # URL 인코딩
    encoded_term = quote_plus(search_term)

    links = []
    header = ""
    footer = ""

    # 한글 영상: 알라딘 + Yes24 + Amazon
    if language == "ko":
        if aladin_id:
            aladin_url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={encoded_term}&partner={aladin_id}"
            links.append(f"  알라딘: {aladin_url}")

        if yes24_id:
            yes24_url = f"https://www.yes24.com/Product/Search?domain=ALL&query={encoded_term}&partner={yes24_id}"
            links.append(f"  Yes24: {yes24_url}")

        if amazon_tag:
            amazon_url = f"https://www.amazon.com/s?k={encoded_term}&tag={amazon_tag}"
            links.append(f"  Amazon: {amazon_url}")

        if links:
            header = "📖 이 책 구매하기:"
            footer = "(위 링크를 통해 구매하시면 채널 운영에 도움이 됩니다)"

    # 영문 영상: Amazon만
    else:
        if amazon_tag:
            amazon_url = f"https://www.amazon.com/s?k={encoded_term}&tag={amazon_tag}"
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
