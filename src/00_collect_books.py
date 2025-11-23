"""
책 목록 수집 및 관리 스크립트
- 일당백 팟캐스트에서 다룬 책 목록
- 명작으로 불리는 책들
- 대학 추천 도서 리스트
시즌1부터 현재까지의 모든 책과 저자 정보를 수집하여 CSV 파일로 저장합니다.
"""

import os
import csv
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from googlesearch import search
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class BookCollector:
    """일당백 팟캐스트 책 목록 수집 클래스"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.books = []
    
    def search_university_booklists(self) -> List[Dict]:
        """대학 추천 도서 리스트 검색"""
        print("🔍 대학 추천 도서 리스트 검색 중...")
        
        search_queries = [
            "하버드 추천 도서",
            "서울대 필독서",
            "연세대 추천 도서",
            "고려대 추천 도서",
            "대학 필독서 리스트",
            "명문대 추천 도서",
            "대학생 필독서",
            "대학 교양 필독서",
        ]
        
        urls = []
        seen_urls = set()
        
        for query in search_queries:
            try:
                print(f"  검색 중: {query}")
                results = search(query, num_results=5, lang='ko')
                
                for url in results:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(2)  # 요청 간 대기 시간
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        print(f"\n✅ {len(urls)}개의 URL을 찾았습니다.\n")
        return urls
    
    def search_masterpiece_books(self) -> List[Dict]:
        """명작 도서 리스트 검색"""
        print("🔍 명작 도서 리스트 검색 중...")
        
        search_queries = [
            "세계 명작 소설",
            "인생 필독서",
            "고전 명작 소설",
            "세계 문학 명작",
            "한국 문학 명작",
            "20세기 명작 소설",
            "21세기 명작 소설",
            "노벨문학상 수상작",
        ]
        
        urls = []
        seen_urls = set()
        
        for query in search_queries:
            try:
                print(f"  검색 중: {query}")
                results = search(query, num_results=5, lang='ko')
                
                for url in results:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(2)  # 요청 간 대기 시간
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        print(f"\n✅ {len(urls)}개의 URL을 찾았습니다.\n")
        return urls
    
    def search_ildangbaek_episodes(self) -> List[Dict]:
        """
        일당백 팟캐스트 에피소드 정보 검색
        다양한 플랫폼에서 에피소드 정보를 수집합니다.
        """
        print("🔍 일당백 팟캐스트 에피소드 검색 중...")
        
        # 검색 쿼리들
        search_queries = [
            "일당백 팟캐스트 에피소드 목록",
            "일당백 팟캐스트 책 리스트",
            "일당백 팟캐스트 시즌1",
            "일당백 팟캐스트 시즌2",
            "일당백 팟캐스트 시즌3",
            "일당백 팟캐스트 시즌4",
            "일당백 팟캐스트 시즌5",
            "일당백 팟캐스트 책 추천",
            "일당백 팟캐스트 다룬 책",
        ]
        
        episode_urls = []
        seen_urls = set()
        
        for query in search_queries:
            try:
                print(f"  검색 중: {query}")
                results = search(query, num_results=5, lang='ko')
                
                for url in results:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        episode_urls.append(url)
                        print(f"    ✓ {url}")
                
                time.sleep(2)  # 요청 간 대기 시간
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        print(f"\n✅ {len(episode_urls)}개의 URL을 찾았습니다.\n")
        return episode_urls
    
    def extract_book_info_from_url(self, url: str) -> List[Dict]:
        """URL에서 책 정보 추출"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            books = []
            
            # 다양한 패턴으로 책 정보 추출 시도
            # 제목, 저자, 출판사 등을 찾는 로직
            # 실제 웹사이트 구조에 따라 수정 필요
            
            return books
        except Exception as e:
            print(f"  ⚠️ URL 처리 실패 ({url}): {e}")
            return []
    
    def add_book_manually(self, title: str, author: str = "", 
                          category: str = "ildangbaek",
                          season: str = "", episode: str = "",
                          source: str = "", status: str = "not_processed",
                          notes: str = "") -> Dict:
        """
        수동으로 책 정보 추가
        
        Args:
            title: 책 제목
            author: 저자
            category: 카테고리 (ildangbaek, masterpiece, university)
            season: 시즌 번호 (일당백용)
            episode: 에피소드 번호 (일당백용)
            source: 출처 (예: "하버드 추천", "서울대 필독서" 등)
            status: 상태 (not_processed, processing, completed)
            notes: 메모
        """
        book = {
            'title': title,
            'author': author,
            'category': category,
            'season': season,
            'episode': episode,
            'source': source,
            'status': status,
            'notes': notes,
            'added_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.books.append(book)
        return book
    
    def load_books_from_csv(self, csv_path: str) -> List[Dict]:
        """CSV 파일에서 책 목록 로드"""
        if not os.path.exists(csv_path):
            return []
        
        books = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                books.append(row)
        
        return books
    
    def save_books_to_csv(self, csv_path: str, books: List[Dict] = None):
        """책 목록을 CSV 파일로 저장"""
        if books is None:
            books = self.books
        
        # 필드명 정의
        fieldnames = ['title', 'author', 'category', 'season', 'episode', 
                     'source', 'status', 'video_created', 'youtube_uploaded', 
                     'notes', 'added_at']
        
        # 기존 파일이 있으면 로드
        existing_books = self.load_books_from_csv(csv_path)
        existing_titles = {book['title']: book for book in existing_books}
        
        # 새 책 추가 (중복 제거)
        for book in books:
            title = book.get('title', '')
            if title and title not in existing_titles:
                existing_books.append(book)
                existing_titles[title] = book
        
        # CSV 저장
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for book in existing_books:
                # 필드가 없으면 빈 값으로 채우기
                row = {field: book.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"💾 책 목록을 저장했습니다: {csv_path}")
        print(f"   총 {len(existing_books)}권의 책")


def main():
    """메인 실행 함수"""
    collector = BookCollector()
    
    print("=" * 60)
    print("📚 일당백 팟캐스트 책 목록 수집기")
    print("=" * 60)
    print()
    
    csv_path = "data/ildangbaek_books.csv"
    
    # 기존 책 목록 로드
    existing_books = collector.load_books_from_csv(csv_path)
    if existing_books:
        print(f"📖 기존 책 목록: {len(existing_books)}권")
        print()
    
    # 모드 선택
    print("작업 모드를 선택하세요:")
    print("  1) 수동으로 책 추가")
    print("  2) 웹에서 일당백 에피소드 정보 검색 (실험적)")
    print("  3) 웹에서 대학 추천 도서 리스트 검색 (실험적)")
    print("  4) 웹에서 명작 도서 리스트 검색 (실험적)")
    print("  5) 책 목록 보기")
    print("  6) 책 상태 업데이트")
    print("  7) 카테고리별 통계 보기")
    
    mode = input("\n선택 (1-7, 기본값: 1): ").strip() or "1"
    
    if mode == "1":
        # 수동 추가 모드
        print("\n📝 수동으로 책 추가")
        print("-" * 60)
        
        while True:
            title = input("\n책 제목 (종료: 엔터): ").strip()
            if not title:
                break
            
            author = input("저자 (선택사항): ").strip()
            
            print("\n카테고리 선택:")
            print("  1) 일당백 팟캐스트")
            print("  2) 명작")
            print("  3) 대학 추천 도서")
            category_choice = input("선택 (1-3, 기본값: 1): ").strip() or "1"
            category_map = {"1": "ildangbaek", "2": "masterpiece", "3": "university"}
            category = category_map.get(category_choice, "ildangbaek")
            
            season = ""
            episode = ""
            source = ""
            
            if category == "ildangbaek":
                season = input("시즌 번호 (선택사항): ").strip()
                episode = input("에피소드 번호 (선택사항): ").strip()
            elif category == "university":
                source = input("출처 (예: 하버드, 서울대, 연세대 등): ").strip()
            elif category == "masterpiece":
                source = input("출처/분류 (예: 세계문학, 한국문학, 노벨문학상 등): ").strip()
            
            status = input("상태 (not_processed/processing/completed, 기본값: not_processed): ").strip() or "not_processed"
            notes = input("메모 (선택사항): ").strip()
            
            collector.add_book_manually(title, author, category, season, episode, source, status, notes)
            print(f"✅ '{title}' 추가 완료")
        
        # 저장
        collector.save_books_to_csv(csv_path)
        
    elif mode == "2":
        # 일당백 웹 검색 모드
        print("\n🔍 웹에서 일당백 에피소드 정보 검색")
        print("-" * 60)
        print("⚠️ 이 기능은 실험적입니다. 수동으로 확인이 필요합니다.")
        
        episode_urls = collector.search_ildangbaek_episodes()
        print(f"\n📋 발견된 URL: {len(episode_urls)}개")
        print("   수동으로 확인하여 책 정보를 추가해주세요.")
        
    elif mode == "3":
        # 대학 추천 도서 검색
        print("\n🔍 웹에서 대학 추천 도서 리스트 검색")
        print("-" * 60)
        print("⚠️ 이 기능은 실험적입니다. 수동으로 확인이 필요합니다.")
        
        urls = collector.search_university_booklists()
        print(f"\n📋 발견된 URL: {len(urls)}개")
        print("   수동으로 확인하여 책 정보를 추가해주세요.")
        print("   카테고리: university, 출처에 대학명을 입력하세요.")
        
    elif mode == "4":
        # 명작 도서 검색
        print("\n🔍 웹에서 명작 도서 리스트 검색")
        print("-" * 60)
        print("⚠️ 이 기능은 실험적입니다. 수동으로 확인이 필요합니다.")
        
        urls = collector.search_masterpiece_books()
        print(f"\n📋 발견된 URL: {len(urls)}개")
        print("   수동으로 확인하여 책 정보를 추가해주세요.")
        print("   카테고리: masterpiece, 출처에 분류를 입력하세요.")
        
    elif mode == "5":
        # 목록 보기
        print("\n📖 책 목록")
        print("-" * 60)
        
        if not existing_books:
            print("등록된 책이 없습니다.")
        else:
            # 상태별로 그룹화
            not_processed = [b for b in existing_books if b.get('status') == 'not_processed']
            processing = [b for b in existing_books if b.get('status') == 'processing']
            completed = [b for b in existing_books if b.get('status') == 'completed']
            
            print(f"\n📌 미처리: {len(not_processed)}권")
            for book in not_processed[:10]:  # 최대 10개만 표시
                print(f"  • {book.get('title', 'N/A')} - {book.get('author', 'N/A')}")
            if len(not_processed) > 10:
                print(f"  ... 외 {len(not_processed) - 10}권")
            
            print(f"\n🔄 처리 중: {len(processing)}권")
            for book in processing:
                print(f"  • {book.get('title', 'N/A')} - {book.get('author', 'N/A')}")
            
            print(f"\n✅ 완료: {len(completed)}권")
            for book in completed:
                print(f"  • {book.get('title', 'N/A')} - {book.get('author', 'N/A')}")
    
    elif mode == "6":
        # 상태 업데이트
        print("\n🔄 책 상태 업데이트")
        print("-" * 60)
        
        if not existing_books:
            print("등록된 책이 없습니다.")
        else:
            print("\n책 목록:")
            for i, book in enumerate(existing_books, 1):
                status_icon = {
                    'not_processed': '📌',
                    'processing': '🔄',
                    'completed': '✅'
                }.get(book.get('status', 'not_processed'), '❓')
                category_icon = {
                    'ildangbaek': '📻',
                    'masterpiece': '📚',
                    'university': '🎓'
                }.get(book.get('category', 'ildangbaek'), '📖')
                print(f"  {i}. {status_icon} {category_icon} {book.get('title', 'N/A')} - {book.get('author', 'N/A')}")
            
            try:
                index = int(input("\n업데이트할 책 번호: ").strip()) - 1
                if 0 <= index < len(existing_books):
                    book = existing_books[index]
                    print(f"\n현재 상태: {book.get('status', 'not_processed')}")
                    new_status = input("새 상태 (not_processed/processing/completed): ").strip()
                    if new_status in ['not_processed', 'processing', 'completed']:
                        book['status'] = new_status
                        collector.save_books_to_csv(csv_path, existing_books)
                        print("✅ 상태가 업데이트되었습니다.")
                    else:
                        print("❌ 잘못된 상태입니다.")
                else:
                    print("❌ 잘못된 번호입니다.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
    
    elif mode == "7":
        # 카테고리별 통계
        print("\n📊 카테고리별 통계")
        print("-" * 60)
        
        if not existing_books:
            print("등록된 책이 없습니다.")
        else:
            # 카테고리별 통계
            categories = {}
            for book in existing_books:
                cat = book.get('category', 'ildangbaek')
                if cat not in categories:
                    categories[cat] = {'total': 0, 'not_processed': 0, 'processing': 0, 'completed': 0}
                categories[cat]['total'] += 1
                status = book.get('status', 'not_processed')
                if status in categories[cat]:
                    categories[cat][status] += 1
            
            cat_names = {
                'ildangbaek': '📻 일당백 팟캐스트',
                'masterpiece': '📚 명작',
                'university': '🎓 대학 추천 도서'
            }
            
            for cat, stats in categories.items():
                name = cat_names.get(cat, cat)
                print(f"\n{name}: 총 {stats['total']}권")
                print(f"  📌 미처리: {stats['not_processed']}권")
                print(f"  🔄 처리 중: {stats['processing']}권")
                print(f"  ✅ 완료: {stats['completed']}권")
            
            # 전체 통계
            total = len(existing_books)
            not_processed = len([b for b in existing_books if b.get('status') == 'not_processed'])
            processing = len([b for b in existing_books if b.get('status') == 'processing'])
            completed = len([b for b in existing_books if b.get('status') == 'completed'])
            
            print(f"\n{'='*60}")
            print(f"📊 전체 통계: 총 {total}권")
            print(f"  📌 미처리: {not_processed}권 ({not_processed/total*100:.1f}%)")
            print(f"  🔄 처리 중: {processing}권 ({processing/total*100:.1f}%)")
            print(f"  ✅ 완료: {completed}권 ({completed/total*100:.1f}%)")
    
    print("\n✅ 작업 완료!")


if __name__ == "__main__":
    main()

