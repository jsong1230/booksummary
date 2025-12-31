#!/usr/bin/env python3
"""
메타데이터 파일에서 복사-붙여넣기용 txt 파일 생성 스크립트
"""

import json
from pathlib import Path
from typing import List, Tuple


def generate_copy_paste_file(metadata_path: Path, output_path: Path, lang: str = "ko") -> bool:
    """메타데이터 파일에서 복사-붙여넣기용 txt 파일 생성"""
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        title = data.get('title', '')
        description = data.get('description', '')
        tags = data.get('tags', [])
        
        lang_name = "한글" if lang == "ko" else "영문"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('=' * 80 + '\n')
            f.write(f'📋 YouTube Studio 복사-붙여넣기용 메타데이터 ({lang_name})\n')
            f.write('=' * 80 + '\n')
            f.write('\n')
            f.write('━' * 80 + '\n')
            f.write('1️⃣ 제목 (Title) - 아래 내용을 복사하세요:\n')
            f.write('━' * 80 + '\n')
            f.write('\n')
            f.write(title + '\n')
            f.write('\n')
            f.write('\n')
            f.write('━' * 80 + '\n')
            f.write('2️⃣ 설명 (Description) - 아래 내용을 복사하세요:\n')
            f.write('━' * 80 + '\n')
            f.write('\n')
            f.write(description + '\n')
            f.write('\n')
            f.write('\n')
            f.write('━' * 80 + '\n')
            f.write('3️⃣ 태그 (Tags) - 아래 내용을 복사하세요:\n')
            f.write('━' * 80 + '\n')
            f.write('\n')
            f.write(', '.join(tags) + '\n')
            f.write('\n')
            f.write('━' * 80 + '\n')
            f.write('💡 사용 방법:\n')
            f.write('1. YouTube Studio (https://studio.youtube.com) 접속\n')
            f.write(f'2. 콘텐츠 → "{title[:50]}..." 영상 찾기\n')
            f.write('3. 편집 클릭\n')
            f.write('4. 각 섹션별로 위의 내용을 복사해서 붙여넣기\n')
            f.write('   - 제목: 1️⃣ 제목 섹션 내용\n')
            f.write('   - 설명: 2️⃣ 설명 섹션 내용\n')
            f.write('   - 태그: 3️⃣ 태그 섹션 내용 (쉼표로 구분된 태그)\n')
            f.write('━' * 80 + '\n')
        
        return True
    except Exception as e:
        print(f"❌ 오류 발생 ({metadata_path.name}): {e}")
        return False


def find_metadata_files_after_sixth_extinction() -> List[Tuple[Path, str]]:
    """The Sixth Extinction 이후 업로드된 영상의 메타데이터 파일 찾기"""
    # The Sixth Extinction 이후 업로드된 영상 목록 (history.md 기준)
    # The Sixth Extinction은 2025-12-23에 업로드됨
    books_after = [
        ("Thus_Spoke_Zarathustra", "차라투스트라는 이렇게 말했다"),
        ("The_Old_Man_and_the_Sea", "노인과 바다"),
        ("The_Stranger", "이방인"),
        ("The_Metamorphosis", "변신"),
        ("Jane_Eyre", "제인 에어"),
        ("Frankenstein", "프랑켄슈타인"),
        ("The_Sorrows_of_Young_Werther", "젊은 베르테르의 슬픔"),
        ("No_Excuses_The_Power_of_Self_Discipline", "행동하지 않으면 인생은 바뀌지 않는다"),
        ("Snow_Country", "설국"),
        ("Rich_Dad_Poor_Dad", "부자 아빠 가난한 아빠"),
        ("The_Intelligent_Investor", "현명한 투자자"),
        ("Gödel_Escher_Bach_An_Eternal_Golden_Braid", "괴델, 에셔, 바흐"),
        ("Hitchhikers_Guide_to_the_Galaxy", "은하수를 여행하는 히치하이커를 위한 안내서"),
        ("Factfulness", "팩트풀니스"),
        ("Essentialism", "에센셜리즘"),
        ("Capital_in_the_Twenty_First_Century", "21세기 자본"),
        ("The_Gene", "유전자"),
        ("The_Nutcracker", "호두까기 인형"),
        ("The_Snowman", "스노우맨"),
        ("The_Gift_of_the_Magi", "크리스마스 선물"),
        ("I_Will_Teach_You_to_Be_Rich", "나는 오늘도 경제적 자유를 꿈꾼다"),
        ("Elon_Musk", "일론 머스크"),
        ("The_Almanack_of_Naval_Ravikant", "부에 대한 연감"),
        ("The_Millionaire_Fastlane", "부의 추월차선"),
        ("The_Subtle_Art_of_Not_Giving_a_F*ck", "신경 끄기의 기술"),
        ("The_Remains_of_the_Day", "남아 있는 나날"),
        ("The_Life_Cycle_Completed", "인간의 위대한 여정"),
        ("Thinking_Fast_and_Slow", "생각에 관한 생각"),
        ("Meditations", "명상록"),
        ("Fooled_by_Randomness", "랜덤워크에 속지 마라"),
    ]
    
    metadata_files = []
    output_dir = Path("output")
    
    for safe_title, _ in books_after:
        # 한글 메타데이터
        kr_file = output_dir / f"{safe_title}_kr.metadata.json"
        if kr_file.exists():
            metadata_files.append((kr_file, "ko"))
        
        # 영문 메타데이터
        en_file = output_dir / f"{safe_title}_en.metadata.json"
        if en_file.exists():
            metadata_files.append((en_file, "en"))
    
    return metadata_files


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("📋 복사-붙여넣기용 메타데이터 파일 생성")
    print("=" * 80)
    print()
    
    # The Sixth Extinction 이후 영상 메타데이터 파일 찾기
    metadata_files = find_metadata_files_after_sixth_extinction()
    
    if not metadata_files:
        print("❌ The Sixth Extinction 이후 업로드된 영상의 메타데이터 파일을 찾을 수 없습니다.")
        return
    
    print(f"📹 발견된 메타데이터 파일: {len(metadata_files)}개\n")
    
    success_count = 0
    for metadata_path, lang in metadata_files:
        # 출력 파일명 생성
        base_name = metadata_path.stem.replace('_metadata', '')
        output_file = metadata_path.parent / f"{base_name}_COPY_PASTE.txt"
        
        print(f"📝 생성 중: {output_file.name}")
        
        if generate_copy_paste_file(metadata_path, output_file, lang):
            success_count += 1
            print(f"   ✅ 완료")
        else:
            print(f"   ❌ 실패")
        print()
    
    print("=" * 80)
    print(f"✅ 생성 완료: {success_count}/{len(metadata_files)}개")
    print("=" * 80)
    print()
    print("📁 생성된 파일 위치: output/ 폴더")
    print("   파일명 형식: {책제목}_{kr|en}_COPY_PASTE.txt")


if __name__ == "__main__":
    main()

