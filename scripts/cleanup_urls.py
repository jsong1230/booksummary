"""
마크다운 파일에서 해당 책과 관련 없는 URL 제거 스크립트
"""

import re
from pathlib import Path

def cleanup_urls(file_path: str, book_title: str, author: str = None):
    """마크다운 파일에서 관련 없는 URL 제거"""
    
    file = Path(file_path)
    if not file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return
    
    # 파일 읽기
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # URL 추출 및 검증
    valid_urls = []
    removed_count = 0
    
    # 다른 책 제목 목록 (예시)
    unrelated_keywords = [
        "82년생 김지영", "김지영", "조남주",
        # 필요시 더 추가
    ]
    
    book_title_lower = book_title.lower()
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('https://'):
            # 관련 없는 책 제목이 포함되어 있는지 확인
            is_unrelated = False
            
            for keyword in unrelated_keywords:
                if keyword.lower() in line_stripped.lower() and keyword.lower() not in book_title_lower:
                    is_unrelated = True
                    print(f"  ⚠️ 제거: {line_stripped[:80]}... (다른 책 관련)")
                    removed_count += 1
                    break
            
            if not is_unrelated:
                valid_urls.append(line_stripped)
        else:
            # URL이 아닌 줄은 그대로 유지
            pass
    
    # URL 블록 찾기 및 교체
    new_lines = []
    in_url_block = False
    url_block_start = None
    
    for i, line in enumerate(lines):
        if '```' in line and not in_url_block:
            in_url_block = True
            url_block_start = i
            new_lines.append(line)
            # URL 추가
            for url in valid_urls:
                new_lines.append(url + '\n')
        elif '```' in line and in_url_block:
            in_url_block = False
            new_lines.append(line)
        elif not in_url_block:
            new_lines.append(line)
        # URL 블록 안의 기존 URL은 건너뜀
    
    # 파일 저장
    with open(file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ 정리 완료:")
    print(f"   - 제거된 URL: {removed_count}개")
    print(f"   - 유효한 URL: {len(valid_urls)}개")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("사용법: python scripts/cleanup_urls.py <파일경로> <책제목> [저자]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    book_title = sys.argv[2]
    author = sys.argv[3] if len(sys.argv) > 3 else None
    
    cleanup_urls(file_path, book_title, author)

