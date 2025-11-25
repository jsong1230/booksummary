"""
CSV의 모든 책에 대해 URL 파일 생성/업데이트 스크립트
기존 파일이 있으면 건너뛰고, 없으면 생성합니다.
"""

import csv
import sys
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# collect_urls_for_notebooklm 모듈 import
import importlib.util
spec = importlib.util.spec_from_file_location(
    "collect_urls_for_notebooklm",
    project_root / "scripts" / "collect_urls_for_notebooklm.py"
)
collect_urls_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collect_urls_module)
NotebookLMURLCollector = collect_urls_module.NotebookLMURLCollector

def load_books_from_csv(csv_path: str) -> List[Tuple[str, str]]:
    """CSV에서 책 목록 로드"""
    books = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title'].strip()
            author = row['author'].strip() if row.get('author') else None
            
            # 빈 제목 제외
            if not title:
                continue
            
            books.append((title, author))
    
    return books

def check_existing_url_file(book_title: str) -> bool:
    """URL 파일이 이미 존재하는지 확인"""
    from utils.file_utils import safe_title
    safe_title_str = safe_title(book_title)
    url_file = project_root / "assets" / "urls" / f"{safe_title_str}_notebooklm.md"
    return url_file.exists()

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='CSV 기반 URL 파일 생성/업데이트')
    parser.add_argument('--skip-existing', action='store_true', help='기존 파일이 있으면 건너뛰기')
    parser.add_argument('--limit', type=int, help='최대 처리 개수 (테스트용)')
    parser.add_argument('--force', action='store_true', help='기존 파일이 있어도 다시 생성')
    parser.add_argument('--auto', action='store_true', help='자동 실행 (확인 없이 진행)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("📚 CSV 기반 URL 파일 생성/업데이트")
    print("=" * 80)
    print()
    
    # 경로 설정
    csv_path = project_root / "data" / "ildangbaek_books.csv"
    urls_dir = project_root / "assets" / "urls"
    urls_dir.mkdir(parents=True, exist_ok=True)
    
    # 책 목록 로드
    print("📖 책 목록 로드 중...")
    books = load_books_from_csv(str(csv_path))
    if args.limit:
        books = books[:args.limit]
    print(f"   ✅ {len(books)}개의 책 발견")
    
    # 기존 파일 확인
    if args.skip_existing:
        existing_count = 0
        filtered_books = []
        for title, author in books:
            if check_existing_url_file(title):
                existing_count += 1
            else:
                filtered_books.append((title, author))
        books = filtered_books
        print(f"   ⏭️ {existing_count}개는 이미 존재하여 건너뜀")
        print(f"   📝 {len(books)}개 처리 예정")
    
    print(f"\n📊 총 작업량: {len(books)}개")
    print()
    
    # 사용자 확인 (--auto 플래그가 없을 때만)
    if not args.auto and len(books) > 10:
        try:
            response = input(f"{len(books)}개의 책에 대해 URL 파일을 생성하시겠습니까? (y/n): ").strip().lower()
            if response != 'y':
                print("❌ 취소되었습니다.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            return
    
    collector = NotebookLMURLCollector()
    
    # 통계
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 책 URL 수집
    print("\n" + "=" * 80)
    print("📚 URL 파일 생성 시작")
    print("=" * 80)
    print()
    
    for i, (title, author) in enumerate(books, 1):
        print(f"\n[{i}/{len(books)}] {title}" + (f" - {author}" if author else ""))
        print("-" * 80)
        
        # 기존 파일 확인 (--force가 아닐 때)
        if not args.force and check_existing_url_file(title):
            print("   ⏭️ 기존 파일이 있어 건너뜀 (--force 옵션으로 강제 생성 가능)")
            skip_count += 1
            continue
        
        try:
            ko_urls, en_urls = collector.search_urls_bilingual(
                book_title=title,
                author=author,
                total_results=30,
                en_title=None
            )
            
            # URL 파일 저장
            collector.save_urls_bilingual(
                book_title=title,
                ko_urls=ko_urls,
                en_urls=en_urls,
                author=author
            )
            
            if ko_urls or en_urls:
                success_count += 1
                print(f"   ✅ 완료: 한글 {len(ko_urls)}개 + 영어 {len(en_urls)}개 = 총 {len(ko_urls) + len(en_urls)}개")
            else:
                fail_count += 1
                print(f"   ⚠️ URL을 찾지 못했지만 파일은 생성됨")
            
            # 요청 간 대기 (API 제한 방지)
            time.sleep(2)
            
        except Exception as e:
            fail_count += 1
            print(f"   ❌ 오류: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 작업 완료 요약")
    print("=" * 80)
    print(f"✅ 성공: {success_count}개")
    print(f"⏭️ 건너뜀: {skip_count}개")
    print(f"❌ 실패: {fail_count}개")
    print(f"📝 총 처리: {len(books)}개")
    print()

if __name__ == "__main__":
    import time
    main()
