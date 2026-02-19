"""
제휴 링크 생성 모듈 테스트
"""

import os
import pytest
from unittest.mock import patch
from src.utils.affiliate_links import generate_affiliate_section


class TestAffiliateLinks:
    """제휴 링크 생성 테스트"""

    def test_no_affiliate_ids_returns_empty_string(self):
        """제휴 ID가 없을 때 빈 문자열 반환"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "",
            "ALADIN_PARTNER_ID": "",
            "YES24_PARTNER_ID": ""
        }, clear=True):
            result = generate_affiliate_section(
                book_title_ko="테스트 책",
                book_title_en="Test Book",
                language="ko"
            )
            assert result == ""

    def test_korean_section_has_all_three_links(self):
        """한글 섹션에 알라딘/Yes24/Amazon 포함"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20",
            "ALADIN_PARTNER_ID": "test-aladin",
            "YES24_PARTNER_ID": "test-yes24"
        }):
            result = generate_affiliate_section(
                book_title_ko="테스트 책",
                book_title_en="Test Book",
                author_ko="테스트 저자",
                author_en="Test Author",
                language="ko"
            )
            assert "📖 이 책 구매하기:" in result
            assert "알라딘:" in result
            assert "Yes24:" in result
            assert "Amazon:" in result
            assert "aladin.co.kr" in result
            assert "yes24.com" in result
            assert "amazon.com" in result
            assert "위 링크를 통해 구매하시면" in result

    def test_english_section_has_amazon_only(self):
        """영문 섹션에 Amazon만 포함"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20",
            "ALADIN_PARTNER_ID": "test-aladin",
            "YES24_PARTNER_ID": "test-yes24"
        }):
            result = generate_affiliate_section(
                book_title_ko="테스트 책",
                book_title_en="Test Book",
                author_ko="테스트 저자",
                author_en="Test Author",
                language="en"
            )
            assert "📖 Get this book:" in result
            assert "Amazon:" in result
            assert "amazon.com" in result
            assert "Purchasing through this link" in result
            # 영문 섹션에는 알라딘/Yes24가 없어야 함
            assert "알라딘:" not in result
            assert "Yes24:" not in result
            assert "aladin.co.kr" not in result
            assert "yes24.com" not in result

    def test_url_encoding_works(self):
        """URL 인코딩이 정상 동작 (Amazon은 영문 제목만 사용, 작가명 제외)"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20"
        }):
            result = generate_affiliate_section(
                book_title_ko="테스트 책 제목",
                book_title_en="Test Book Title",
                author_ko="저자 이름",
                author_en="Author Name",
                language="ko"
            )
            # Amazon은 영문 제목으로만 검색 (작가명은 제외)
            assert "Test+Book+Title" in result or "Test%20Book%20Title" in result
            # 공백이 + 또는 %20으로 인코딩되어야 함
            assert "+" in result or "%20" in result

    def test_partial_affiliate_ids(self):
        """일부 제휴 ID만 있을 때 해당 링크만 포함"""
        # Amazon만 있는 경우
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20",
            "ALADIN_PARTNER_ID": "",
            "YES24_PARTNER_ID": ""
        }):
            result = generate_affiliate_section(
                book_title_ko="테스트 책",
                book_title_en="Test Book",
                language="ko"
            )
            assert "Amazon:" in result
            assert "알라딘:" not in result
            assert "Yes24:" not in result

    def test_with_author_names(self):
        """저자명이 포함된 데이터 (Amazon은 영문 제목만 사용, 작가명 제외)"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20"
        }):
            result = generate_affiliate_section(
                book_title_ko="노인과 바다",
                book_title_en="The Old Man and the Sea",
                author_ko="어니스트 헤밍웨이",
                author_en="Ernest Hemingway",
                language="ko"
            )
            # Amazon은 영문 제목만으로 검색 (작가명은 제외)
            assert "The+Old+Man+and+the+Sea" in result or "The%20Old%20Man%20and%20the%20Sea" in result

    def test_without_author_names(self):
        """저자명이 없을 때도 정상 동작"""
        with patch.dict(os.environ, {
            "AMAZON_ASSOCIATE_TAG": "test-amazon-20"
        }):
            result = generate_affiliate_section(
                book_title_ko="노인과 바다",
                book_title_en="The Old Man and the Sea",
                language="en"
            )
            # 책 제목만 URL에 포함되어야 함
            assert "The+Old+Man+and+the+Sea" in result or "The%20Old%20Man%20and%20the%20Sea" in result
            assert result != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
