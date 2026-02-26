"""
구매 링크 유효성 검사 모듈

알라딘 / Amazon 구매 링크가 실제로 유효한지 HTTP 요청으로 확인합니다.
- 알라딘 ISBN URL: 실제 책 존재 여부 확인 (리디렉션 체인 분석)
- Amazon URL: HTTP 접근 가능 여부 확인
- 검색 URL: 기본 접근 가능 여부 확인
"""

import re
import time
import logging
from typing import Dict, List, Tuple

import requests

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

_URL_RE = re.compile(r"https?://[^\s\n\)\"\'>< ]+")

# 구매 섹션 패턴 — 링크 줄이 하나도 없는 경우(헤더 바로 뒤 푸터)만 매치하여 제거
_EMPTY_SECTION_KO = re.compile(
    r"📖 이 책 구매하기:\n\(위 링크를 통해 구매하시면 채널 운영에 도움이 됩니다\)\n?",
)
_EMPTY_SECTION_EN = re.compile(
    r"📖 Get this book:\n\(Purchasing through this link supports our channel\)\n?",
)


# ---------------------------------------------------------------------------
# 개별 URL 검사
# ---------------------------------------------------------------------------

def validate_aladin_url(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    알라딘 URL 유효성 검사.

    - `wproduct.aspx?ISBN=...` 형식: 실제 책 페이지인지 확인
      * 최종 URL이 `wproduct.aspx`로 유지 → 책 존재 (유효)
      * `wsearchresult` 등으로 리디렉션 → 책 없음 (무효)
    - 검색 URL(`wsearchresult`): 접근 가능 여부만 확인
    """
    is_isbn_direct = "wproduct.aspx" in url and "ISBN=" in url

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
    except requests.Timeout:
        return False, "Timeout"
    except requests.ConnectionError:
        return False, "Connection error"
    except Exception as e:  # noqa: BLE001
        return False, str(e)

    if resp.status_code >= 400:
        return False, f"HTTP {resp.status_code}"

    if is_isbn_direct:
        final = resp.url
        if "wproduct.aspx" in final:
            return True, "Book page found"
        if "wsearchresult" in final or "/search/" in final.lower():
            return False, "Book not found on Aladin (redirected to search)"
        # 기타 리디렉션 - 상태 코드 기준
        return True, f"HTTP {resp.status_code}"

    return True, f"HTTP {resp.status_code}"


def validate_amazon_url(url: str, timeout: int = 8) -> Tuple[bool, str]:
    """
    Amazon URL 유효성 검사.

    Amazon은 bot 방지(Cloudfront)로 requests에 항상 503을 반환합니다.
    따라서 HTTP 상태 코드가 아닌 URL 형식으로 유효성을 판단합니다:
    - URL에 &amp; 또는 HTML 태그 잔재가 있으면 → 잘못 인코딩된 URL (무효)
    - 정상적인 https://www.amazon.com/... 형식이면 → 유효
    """
    if "&amp;" in url or "<" in url:
        return False, "HTML-encoded URL (malformed)"
    if not url.startswith("https://www.amazon.com/"):
        return False, "Unexpected Amazon URL format"
    return True, "URL format OK"


def validate_purchase_url(url: str, delay: float = 0.0) -> Tuple[bool, str]:
    """
    단일 구매 링크 유효성 검사.

    알라딘/Amazon URL 여부에 따라 적합한 검사기를 선택합니다.
    """
    url = url.rstrip(".,;)\"'")
    if not url.startswith(("http://", "https://")):
        return False, "Invalid URL format"

    if delay > 0:
        time.sleep(delay)

    if "aladin.co.kr" in url:
        return validate_aladin_url(url)
    if "amazon.com" in url:
        return validate_amazon_url(url)

    # 기타 URL - HEAD로 간단 확인
    try:
        resp = requests.head(url, headers=_HEADERS, timeout=8, allow_redirects=True)
        return resp.status_code < 400, f"HTTP {resp.status_code}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


# ---------------------------------------------------------------------------
# 댓글 전체 링크 검사
# ---------------------------------------------------------------------------

def validate_purchase_links_in_comment(
    comment_text: str,
    delay: float = 0.5,
) -> Dict[str, Dict]:
    """
    댓글 텍스트 내 알라딘·Amazon 구매 링크를 모두 추출하여 유효성 검사.

    Returns:
        {url: {'valid': bool, 'reason': str}}
    """
    raw_urls = _URL_RE.findall(comment_text)
    results: Dict[str, Dict] = {}

    for raw in raw_urls:
        url = raw.rstrip(".,;)\"'")
        if "aladin.co.kr" not in url and "amazon.com" not in url:
            continue
        if url in results:
            continue

        is_valid, reason = validate_purchase_url(url, delay=delay)
        results[url] = {"valid": is_valid, "reason": reason}
        logger.debug("  URL %s → %s (%s)", url, "OK" if is_valid else "INVALID", reason)

    return results


# ---------------------------------------------------------------------------
# 댓글에서 무효 링크 제거
# ---------------------------------------------------------------------------

def remove_invalid_links_from_comment(
    comment_text: str,
    validation_results: Dict[str, Dict],
) -> Tuple[str, List[str]]:
    """
    댓글에서 유효하지 않은 링크가 포함된 줄을 제거합니다.

    - 줄 단위로 처리: 해당 줄의 URL이 무효이면 그 줄만 제거
    - 구매 섹션의 모든 링크가 제거된 경우 헤더·푸터도 함께 제거
    - 연속된 빈 줄 정리 (최대 2줄)

    Returns:
        (updated_comment, removed_urls)
    """
    removed: List[str] = []
    new_lines: List[str] = []

    for line in comment_text.split("\n"):
        line_urls = [u.rstrip(".,;)\"'") for u in _URL_RE.findall(line)]
        invalid_in_line = [
            u for u in line_urls
            if u in validation_results and not validation_results[u]["valid"]
        ]

        if invalid_in_line:
            removed.extend(invalid_in_line)
            # 줄 전체 제거
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)
    result = _clean_empty_affiliate_section(result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip(), removed


def _clean_empty_affiliate_section(text: str) -> str:
    """링크가 모두 제거되어 헤더·푸터만 남은 빈 구매 섹션을 제거합니다."""
    text = _EMPTY_SECTION_KO.sub("", text)
    text = _EMPTY_SECTION_EN.sub("", text)
    return text


# ---------------------------------------------------------------------------
# 일괄 검사 + 제거 (편의 함수)
# ---------------------------------------------------------------------------

def audit_and_clean_comment(
    comment_text: str,
    delay: float = 0.5,
    verbose: bool = True,
) -> Tuple[str, Dict[str, Dict], List[str]]:
    """
    댓글의 구매 링크를 검사하고 무효 링크를 제거한 댓글을 반환합니다.

    Returns:
        (cleaned_comment, validation_results, removed_urls)
    """
    validation = validate_purchase_links_in_comment(comment_text, delay=delay)

    if not validation:
        return comment_text, {}, []

    if verbose:
        for url, info in validation.items():
            status = "✅" if info["valid"] else "❌"
            print(f"   {status} {url[:80]}  ({info['reason']})")

    invalid_count = sum(1 for v in validation.values() if not v["valid"])
    if invalid_count == 0:
        return comment_text, validation, []

    cleaned, removed = remove_invalid_links_from_comment(comment_text, validation)
    return cleaned, validation, removed
