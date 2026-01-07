#!/usr/bin/env python3
"""
Pexels API로 추가 이미지 다운로드
"""
import os
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 경로에 추가 (scripts/ 폴더에서 실행 시)
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pexels_api import API as PexelsAPI
    PEXELS_AVAILABLE = True
except ImportError:
    PEXELS_AVAILABLE = False
    print("⚠️ pexels-api 패키지가 설치되지 않았습니다. pip install pexels-api")

load_dotenv()

def download_pexels_images(book_title: str, target_count: int = 100, query: str = None):
    """Pexels API로 무드 이미지 다운로드"""
    from src.utils.file_utils import safe_title
    
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    if not pexels_api_key:
        print("❌ PEXELS_API_KEY가 설정되지 않았습니다.")
        return
    
    if not PEXELS_AVAILABLE:
        print("❌ Pexels API를 사용할 수 없습니다.")
        return
    
    safe_title_str = safe_title(book_title)
    output_dir = Path("assets/images") / safe_title_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 이미지 개수 확인
    existing_images = list(output_dir.glob("mood_*.jpg"))
    current_count = len(existing_images)
    print(f"📊 현재 이미지 개수: {current_count}개")
    
    if current_count >= target_count:
        print(f"✅ 이미 목표 개수({target_count}개)에 도달했습니다.")
        return
    
    remaining = target_count - current_count
    print(f"📥 추가로 {remaining}개 이미지 다운로드 필요")
    print()
    
    # 키워드 리스트 (책 내용 기반)
    if query:
        keywords = [k.strip() for k in query.split(',')]
    else:
        # 기본값 (하드코딩된 리스트 대신 제목 사용 등)
        keywords = [book_title]
    
    pexels = PexelsAPI(pexels_api_key)
    downloaded = []
    
    print("=" * 60)
    print("📸 Pexels API로 이미지 다운로드 시작")
    print("=" * 60)
    print()
    
    for keyword in keywords:
        if len(downloaded) >= remaining:
            break
        
        try:
            print(f"🔍 검색: {keyword}")
            
            # Pexels API 검색
            try:
                search_results = pexels.search(keyword, page=1, results_per_page=min(15, remaining - len(downloaded)))
            except TypeError:
                search_results = pexels.search(keyword, page=1)
            except Exception as e:
                print(f"   ❌ Pexels API 오류: {e}")
                continue
            
            if not search_results.get('photos'):
                print(f"   ⚠️ 검색 결과 없음")
                continue
            
            for photo in search_results['photos']:
                if len(downloaded) >= remaining:
                    break
                
                # 고화질 이미지 URL
                image_url = photo.get('src', {}).get('large') or photo.get('src', {}).get('original')
                
                if not image_url:
                    continue
                
                # 이미지 다운로드
                try:
                    img_response = requests.get(image_url, timeout=10)
                    img_response.raise_for_status()
                    
                    # 저장 (기존 이미지 번호 다음부터)
                    filename = f"mood_{current_count + len(downloaded) + 1:02d}_{keyword.replace(' ', '_')}.jpg"
                    output_path = output_dir / filename
                    
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    
                    downloaded.append(str(output_path))
                    print(f"   ✅ {filename}")
                    
                    time.sleep(0.5)  # API rate limit 방지
                    
                except Exception as e:
                    print(f"   ❌ 다운로드 오류: {e}")
                    continue
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            continue
    
    print()
    print("=" * 60)
    print(f"✅ 다운로드 완료: {len(downloaded)}개 추가")
    print(f"📊 총 이미지 개수: {current_count + len(downloaded)}개")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Pexels API로 추가 이미지 다운로드')
    parser.add_argument('--title', type=str, default='Sunrise on the Reaping', help='책 제목')
    parser.add_argument('--target', type=int, default=100, help='목표 이미지 개수')
    parser.add_argument('--query', type=str, help='검색 키워드 (콤마로 구분)')
    
    args = parser.parse_args()
    
    download_pexels_images(args.title, args.target, args.query)
