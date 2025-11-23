"""
배치 URL 수집 스크립트
CSV의 책 목록과 topics_seeds.txt의 주제들을 모두 수집합니다.
"""

import os
import sys
import csv
import time
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 직접 import
import importlib.util
spec = importlib.util.spec_from_file_location(
    "collect_urls_for_notebooklm",
    project_root / "scripts" / "collect_urls_for_notebooklm.py"
)
collect_urls_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect_urls_module)
NotebookLMURLCollector = collect_urls_module.NotebookLMURLCollector

def load_books_from_csv(csv_path: str) -> List[Tuple[str, str]]:
    """CSV에서 책 목록 로드 (노르웨이의 숲 제외)"""
    books = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title'].strip()
            author = row['author'].strip() if row['author'] else None
            
            # 노르웨이의 숲 제외
            if '노르웨이의 숲' in title or '노르웨이의_숲' in title:
                continue
            
            # 빈 제목 제외
            if not title:
                continue
            
            books.append((title, author))
    
    return books

def load_topics_from_txt(txt_path: str) -> List[str]:
    """텍스트 파일에서 주제 목록 로드"""
    topics = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 빈 줄 제외
            if line:
                topics.append(line)
    
    return topics

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='배치 URL 수집 스크립트')
    parser.add_argument('--auto', action='store_true', help='자동 실행 (확인 없이 진행)')
    parser.add_argument('--books-only', action='store_true', help='책만 수집')
    parser.add_argument('--topics-only', action='store_true', help='주제만 수집')
    parser.add_argument('--limit', type=int, help='최대 처리 개수 (테스트용)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📚 배치 URL 수집 스크립트")
    print("=" * 80)
    print()
    
    # 경로 설정
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "data" / "ildangbaek_books.csv"
    topics_path = base_dir / "data" / "topics_seeds.txt"
    
    # 책 목록 로드
    print("📖 책 목록 로드 중...")
    books = load_books_from_csv(str(csv_path))
    if args.limit and not args.topics_only:
        books = books[:args.limit]
    print(f"   ✅ {len(books)}개의 책 발견")
    
    # 주제 목록 로드
    print("\n📋 주제 목록 로드 중...")
    topics = load_topics_from_txt(str(topics_path))
    if args.limit and not args.books_only:
        topics = topics[:args.limit]
    print(f"   ✅ {len(topics)}개의 주제 발견")
    
    # 필터링
    if args.books_only:
        topics = []
    if args.topics_only:
        books = []
    
    print(f"\n📊 총 작업량: {len(books)}개 책 + {len(topics)}개 주제 = {len(books) + len(topics)}개")
    print()
    
    # 사용자 확인 (--auto 플래그가 없을 때만)
    if not args.auto:
        try:
            response = input("계속 진행하시겠습니까? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ 취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 입력 오류. --auto 플래그를 사용하세요.")
            return
    
    collector = NotebookLMURLCollector()
    
    # 통계
    success_count = 0
    fail_count = 0
    total = len(books) + len(topics)
    
    # 책 URL 수집
    print("\n" + "=" * 80)
    print("📚 책 URL 수집 시작")
    print("=" * 80)
    print()
    
    for i, (title, author) in enumerate(books, 1):
        print(f"\n[{i}/{len(books)}] {title}" + (f" - {author}" if author else ""))
        print("-" * 80)
        
        try:
            ko_urls, en_urls = collector.search_urls_bilingual(
                book_title=title,
                author=author,
                total_results=30,
                en_title=None
            )
            
            # URL이 0개여도 파일 저장 (최소한 빈 파일이라도 생성)
            collector.save_urls_bilingual(
                book_title=title,
                ko_urls=ko_urls,
                en_urls=en_urls,
                author=author
            )
            if ko_urls or en_urls:
                success_count += 1
                print(f"✅ 완료: {title} (한글 {len(ko_urls)}개, 영어 {len(en_urls)}개)")
            else:
                fail_count += 1
                print(f"⚠️ URL 수집 실패: {title} (빈 파일 생성됨)")
            
            # 요청 간 대기 (API 제한 방지)
            if i < len(books):  # 마지막이 아니면 대기
                time.sleep(3)
            
        except Exception as e:
            fail_count += 1
            print(f"❌ 오류 발생: {title} - {str(e)}")
            continue
    
    # 주제 URL 수집
    print("\n" + "=" * 80)
    print("📋 주제 URL 수집 시작")
    print("=" * 80)
    print()
    
    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}/{len(topics)}] {topic}")
        print("-" * 80)
        
        try:
            # 주제는 책이 아니므로 author 없이 수집
            ko_urls, en_urls = collector.search_urls_bilingual(
                book_title=topic,
                author=None,
                total_results=30,
                en_title=None
            )
            
            # URL이 0개여도 파일 저장 (최소한 빈 파일이라도 생성)
            collector.save_urls_bilingual(
                book_title=topic,
                ko_urls=ko_urls,
                en_urls=en_urls,
                author=None
            )
            if ko_urls or en_urls:
                success_count += 1
                print(f"✅ 완료: {topic} (한글 {len(ko_urls)}개, 영어 {len(en_urls)}개)")
            else:
                fail_count += 1
                print(f"⚠️ URL 수집 실패: {topic} (빈 파일 생성됨)")
            
            # 요청 간 대기
            if i < len(topics):  # 마지막이 아니면 대기
                time.sleep(3)
            
        except Exception as e:
            fail_count += 1
            print(f"❌ 오류 발생: {topic} - {str(e)}")
            continue
    
    # 최종 결과
    print("\n" + "=" * 80)
    print("✅ 배치 URL 수집 완료!")
    print("=" * 80)
    print(f"\n📊 결과:")
    print(f"   성공: {success_count}개")
    print(f"   실패: {fail_count}개")
    print(f"   총계: {total}개")
    print(f"\n📁 저장 위치: assets/urls/")
    print()

if __name__ == "__main__":
    main()

