#!/usr/bin/env python3
"""
input 폴더에서 파일을 찾아 표준 네이밍 규칙으로 변경하고 적절한 위치로 이동

파일 패턴:
- {prefix}_audio_{lang}.{ext} → assets/audio/{safe_title}_review_{lang}.{ext}
- {prefix}_summary_{lang}.md → assets/summaries/{safe_title}_summary_{lang}.md
- {prefix}_thumbnail_{lang}.png → output/{safe_title}_thumbnail_{lang}.jpg (JPG 변환)
- {prefix}_video_{lang}.{ext} → assets/video/{safe_title}_notebooklm_{lang}.{ext}
"""

import sys
from pathlib import Path
from PIL import Image
import shutil

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.file_utils import get_standard_safe_title

# YouTube 롱폼 썸네일 크기 (16:9 비율)
THUMBNAIL_SIZE = (3840, 2160)  # 4K 해상도
MAX_SIZE_MB = 2.0

def resize_and_crop(img: Image.Image, target_size: tuple) -> Image.Image:
    """이미지를 목표 크기에 맞게 리사이즈 및 크롭"""
    target_width, target_height = target_size
    img_width, img_height = img.size
    
    # 비율 계산
    target_ratio = target_width / target_height
    img_ratio = img_width / img_height
    
    if img_ratio > target_ratio:
        # 이미지가 더 넓음 - 높이 기준으로 리사이즈
        new_height = target_height
        new_width = int(target_height * img_ratio)
    else:
        # 이미지가 더 높음 - 너비 기준으로 리사이즈
        new_width = target_width
        new_height = int(target_width / img_ratio)
    
    # 리사이즈
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 중앙 크롭
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height
    
    return img.crop((left, top, right, bottom))

def convert_png_to_jpg(input_path: Path, output_path: Path) -> bool:
    """PNG 파일을 JPG로 변환"""
    try:
        img = Image.open(input_path)
        
        # RGBA를 RGB로 변환 (PNG 투명도 처리)
        if img.mode == 'RGBA':
            # 흰색 배경에 합성
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # alpha 채널을 마스크로 사용
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 리사이즈 (비율 유지하며 크롭)
        img = resize_and_crop(img, THUMBNAIL_SIZE)
        
        # 압축 (품질 조정하여 2MB 이하로)
        quality = 95
        while quality >= 50:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            
            if file_size_mb <= MAX_SIZE_MB:
                return True
            
            quality -= 5
        
        # 최소 품질로도 2MB를 넘으면 경고
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            # 해상도를 90%로 줄여서 재시도
            new_size = (int(THUMBNAIL_SIZE[0] * 0.9), int(THUMBNAIL_SIZE[1] * 0.9))
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            img_resized = img_resized.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            quality = 85
            while quality >= 50:
                img_resized.save(output_path, 'JPEG', quality=quality, optimize=True)
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                if file_size_mb <= MAX_SIZE_MB:
                    return True
                quality -= 5
        
        return output_path.exists()
        
    except Exception as e:
        print(f"   ❌ PNG 변환 오류: {e}")
        return False

def find_files_in_downloads(prefix: str, book_title: str) -> dict:
    """
    input 폴더에서 파일 찾기
    
    Args:
        prefix: 파일명 접두사 (예: "lonliness")
        book_title: 책 제목 (표준 네이밍용)
        
    Returns:
        찾은 파일들의 딕셔너리
    """
    downloads_dir = Path("input")
    # 표준 영문 제목으로 통일
    safe_title_str = get_standard_safe_title(book_title)
    
    files = {
        'audio': {'en': None, 'ko': None},
        'summary': {'en': None, 'ko': None},
        'thumbnail': {'en': None, 'ko': None},
        'video': {'en': None, 'ko': None}
    }
    
    # 오디오 파일 찾기
    for lang in ['en', 'kr', 'ko']:
        lang_key = 'ko' if lang in ['kr', 'ko'] else 'en'
        # 이미 찾았으면 건너뛰기
        if files['audio'][lang_key] is not None:
            continue
        for ext in ['.m4a', '.mp3', '.wav']:
            pattern = f"{prefix}_audio_{lang}{ext}"
            file_path = downloads_dir / pattern
            if file_path.exists():
                files['audio'][lang_key] = file_path
                break
    
    # Summary 파일 찾기
    for lang in ['en', 'kr', 'ko']:
        lang_key = 'ko' if lang in ['kr', 'ko'] else 'en'
        # 이미 찾았으면 건너뛰기
        if files['summary'][lang_key] is not None:
            continue
        pattern = f"{prefix}_summary_{lang}.md"
        file_path = downloads_dir / pattern
        if file_path.exists():
            files['summary'][lang_key] = file_path
    
    # 썸네일 파일 찾기
    for lang in ['en', 'kr', 'ko']:
        lang_key = 'ko' if lang in ['kr', 'ko'] else 'en'
        # 이미 찾았으면 건너뛰기
        if files['thumbnail'][lang_key] is not None:
            continue
        pattern = f"{prefix}_thumbnail_{lang}.png"
        file_path = downloads_dir / pattern
        if file_path.exists():
            files['thumbnail'][lang_key] = file_path
    
    # 비디오 파일 찾기
    for lang in ['en', 'kr', 'ko']:
        lang_key = 'ko' if lang in ['kr', 'ko'] else 'en'
        # 이미 찾았으면 건너뛰기
        if files['video'][lang_key] is not None:
            continue
        for ext in ['.mp4', '.mov', '.avi', '.mkv']:
            # 패턴 1: {prefix}_video_{lang}.{ext} (언더스코어)
            pattern = f"{prefix}_video_{lang}{ext}"
            file_path = downloads_dir / pattern
            if file_path.exists():
                files['video'][lang_key] = file_path
                break
            # 패턴 2: {prefix}_video.{lang}{ext} (점)
            pattern = f"{prefix}_video.{lang}{ext}"
            file_path = downloads_dir / pattern
            if file_path.exists():
                files['video'][lang_key] = file_path
                break
    
    return files, safe_title_str

def prepare_files(book_title: str, author: str = None, prefix: str = None) -> dict:
    """
    input 폴더에서 파일을 찾아 표준 네이밍으로 변경하고 이동
    
    Args:
        book_title: 책 제목
        author: 저자 이름
        prefix: 파일명 접두사 (None이면 자동 추정)
        
    Returns:
        준비된 파일들의 경로 딕셔너리
    """
    print("=" * 60)
    print("📁 input 폴더에서 파일 준비")
    print("=" * 60)
    print()
    
    downloads_dir = Path("input")
    # 표준 영문 제목으로 통일
    safe_title_str = get_standard_safe_title(book_title)
    
    # prefix가 없으면 safe_title의 첫 부분으로 추정
    if prefix is None:
        # input 폴더에서 패턴 매칭으로 찾기
        possible_prefixes = []
        for file in downloads_dir.glob("*_audio_*.m4a"):
            stem = file.stem
            if '_audio_' in stem:
                possible_prefixes.append(stem.split('_audio_')[0])
        
        if possible_prefixes:
            prefix = possible_prefixes[0]
            print(f"🔍 자동 감지된 접두사: {prefix}")
        else:
            # safe_title의 첫 단어를 소문자로 사용
            prefix = safe_title_str.lower().split('_')[0]
            print(f"⚠️ 접두사를 찾을 수 없어 기본값 사용: {prefix}")
    
    print(f"📖 책 제목: {book_title}")
    print(f"📝 표준 제목: {safe_title_str}")
    print(f"🔖 접두사: {prefix}")
    print()
    
    # 파일 찾기
    files, safe_title_str = find_files_in_downloads(prefix, book_title)
    
    prepared_files = {
        'audio': {'en': None, 'ko': None},
        'summary': {'en': None, 'ko': None},
        'thumbnail': {'en': None, 'ko': None},
        'video': {'en': None, 'ko': None}
    }
    
    # 오디오 파일 처리
    print("🎵 오디오 파일 처리:")
    for lang in ['en', 'ko']:
        if files['audio'][lang]:
            src_file = files['audio'][lang]
            lang_suffix = 'en' if lang == 'en' else 'kr'  # 한국어는 kr로 통일
            ext = src_file.suffix
            dst_file = Path("assets/audio") / f"{safe_title_str}_review_{lang_suffix}{ext}"
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"   {lang.upper()}: {src_file.name} → {dst_file.name}")
            shutil.copy2(src_file, dst_file)
            prepared_files['audio'][lang] = str(dst_file)
            print(f"      ✅ 이동 완료: {dst_file}")
        else:
            print(f"   {lang.upper()}: 파일 없음")
    print()
    
    # Summary 파일 처리
    print("📄 Summary 파일 처리:")
    for lang in ['en', 'ko']:
        if files['summary'][lang]:
            src_file = files['summary'][lang]
            lang_suffix = 'en' if lang == 'en' else 'kr'  # 한국어는 kr로 통일
            dst_file = Path("assets/summaries") / f"{safe_title_str}_summary_{lang_suffix}.md"
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"   {lang.upper()}: {src_file.name} → {dst_file.name}")
            shutil.copy2(src_file, dst_file)
            prepared_files['summary'][lang] = str(dst_file)
            print(f"      ✅ 이동 완료: {dst_file}")
        else:
            print(f"   {lang.upper()}: 파일 없음")
    print()
    
    # 썸네일 파일 처리 (PNG → JPG 변환)
    print("🖼️ 썸네일 파일 처리 (PNG → JPG):")
    for lang in ['en', 'ko']:
        if files['thumbnail'][lang]:
            src_file = files['thumbnail'][lang]
            lang_suffix = 'en' if lang == 'en' else 'kr'  # 한국어는 kr로 통일
            dst_file = Path("output") / f"{safe_title_str}_thumbnail_{lang_suffix}.jpg"
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"   {lang.upper()}: {src_file.name} → {dst_file.name}")
            if convert_png_to_jpg(src_file, dst_file):
                prepared_files['thumbnail'][lang] = str(dst_file)
                print(f"      ✅ 변환 완료: {dst_file}")
            else:
                print(f"      ❌ 변환 실패: {src_file.name}")
        else:
            print(f"   {lang.upper()}: 파일 없음")
    print()
    
    # 비디오 파일 처리
    print("🎬 비디오 파일 처리:")
    for lang in ['en', 'ko']:
        if files['video'][lang]:
            src_file = files['video'][lang]
            lang_suffix = 'en' if lang == 'en' else 'kr'  # 한국어는 kr로 통일
            ext = src_file.suffix
            dst_file = Path("assets/video") / f"{safe_title_str}_notebooklm_{lang_suffix}{ext}"
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"   {lang.upper()}: {src_file.name} → {dst_file.name}")
            shutil.copy2(src_file, dst_file)
            prepared_files['video'][lang] = str(dst_file)
            print(f"      ✅ 이동 완료: {dst_file}")
        else:
            print(f"   {lang.upper()}: 파일 없음")
    print()
    
    print("=" * 60)
    print("✅ 파일 준비 완료")
    print("=" * 60)
    
    return prepared_files


def validate_input_folder(
    input_dir: Path = None,
    prefix: str = None,
    style: str = "summary"
) -> dict:
    """
    input 폴더의 파일을 검증합니다.

    Args:
        input_dir: 검증할 폴더 경로 (기본값: Path("input"))
        prefix: 파일명 접두사 (None이면 자동 감지)
        style: 영상 스타일 ("summary" 또는 "episode")

    Returns:
        {
            'valid': bool,
            'warnings': list[str],
            'errors': list[str],
            'detected_files': dict
        }
    """
    if input_dir is None:
        input_dir = Path("input")

    result = {
        'valid': True,
        'warnings': [],
        'errors': [],
        'detected_files': {}
    }

    print("=" * 60)
    print(f"🔍 input 폴더 유효성 검증 ({style} 스타일)")
    print("=" * 60)

    if not input_dir.exists():
        result['errors'].append(f"input 폴더가 존재하지 않습니다: {input_dir}")
        result['valid'] = False
        _print_validation_result(result)
        return result

    all_files = list(input_dir.iterdir())
    recognized_files = []
    unrecognized_files = []

    # 언어 마커 패턴
    lang_markers = ['_kr', '_ko', '_en']

    for f in all_files:
        if not f.is_file():
            continue
        name = f.name.lower()
        has_lang_marker = any(marker in name for marker in lang_markers)
        # 알려진 타입 키워드 포함 여부
        known_keywords = ['audio', 'summary', 'thumbnail', 'video', 'part1', 'part2', 'info']
        has_known_keyword = any(kw in name for kw in known_keywords)

        if has_lang_marker and has_known_keyword:
            recognized_files.append(f)
        else:
            unrecognized_files.append(f)

    result['detected_files']['recognized'] = [str(f) for f in recognized_files]

    # 인식 불가 파일 경고
    for uf in unrecognized_files:
        result['warnings'].append(f"인식 불가 파일: {uf.name} (언어 마커 또는 타입 키워드 없음)")

    if style == "summary":
        # Summary 스타일: audio 2개, summary(MD) 2개, thumbnail(PNG) 2개 기대
        _validate_summary_style(input_dir, prefix, result)
    elif style == "episode":
        # Episode 스타일: video(MP4) 4개, infographic(PNG) 4개, thumbnail 2개 기대
        _validate_episode_style(input_dir, prefix, result)
    else:
        result['warnings'].append(f"알 수 없는 스타일: {style}. 'summary' 또는 'episode'만 지원됩니다.")

    if result['errors']:
        result['valid'] = False

    _print_validation_result(result)
    return result


def _validate_summary_style(input_dir: Path, prefix: str, result: dict) -> None:
    """Summary+Video 스타일 파일 검증

    Summary 오디오는 파이프라인이 TTS로 summary MD에서 자동 생성합니다.
    NotebookLM 비디오(.mp4)는 필수입니다.
    """
    lang_variants = [
        ('ko', ['_kr', '_ko']),
        ('en', ['_en']),
    ]

    for lang_key, markers in lang_variants:
        # NotebookLM 비디오 파일 확인 (필수)
        video_found = False
        for ext in ['.mp4', '.mov', '.avi', '.mkv']:
            for marker in markers:
                pattern = f"*video*{marker}*{ext}"
                if list(input_dir.glob(pattern)):
                    video_found = True
                    break
                if prefix:
                    specific = input_dir / f"{prefix}_video_{marker.strip('_')}{ext}"
                    if specific.exists():
                        video_found = True
                        break
            if video_found:
                break

        if not video_found:
            result['errors'].append(
                f"[{lang_key.upper()}] NotebookLM 비디오 파일 없음 (필수): "
                f"*video*{'|'.join(markers)}*.mp4"
            )

        # Summary MD 파일 확인 (선택, 없으면 경고)
        summary_found = False
        for marker in markers:
            pattern = f"*summary*{marker}*.md"
            if list(input_dir.glob(pattern)):
                summary_found = True
                break
            if prefix:
                specific = input_dir / f"{prefix}_summary_{marker.strip('_')}.md"
                if specific.exists():
                    summary_found = True
                    break
        if not summary_found:
            result['warnings'].append(
                f"[{lang_key.upper()}] Summary MD 파일 없음 (선택): AI가 자동 생성합니다."
            )

        # 썸네일 PNG 확인 (선택, 없으면 경고)
        thumbnail_found = False
        for ext in ['.png', '.jpg', '.jpeg']:
            for marker in markers:
                pattern = f"*thumbnail*{marker}*{ext}"
                if list(input_dir.glob(pattern)):
                    thumbnail_found = True
                    break
            if thumbnail_found:
                break
        if not thumbnail_found:
            result['warnings'].append(
                f"[{lang_key.upper()}] 썸네일 파일 없음 (선택): 업로드 전 필요합니다."
            )


def _validate_episode_style(input_dir: Path, prefix: str, result: dict) -> None:
    """일당백(Episode) 스타일 파일 검증"""
    lang_variants = [
        ('ko', ['_kr', '_ko']),
        ('en', ['_en']),
    ]
    part_nums = [1, 2]

    for lang_key, markers in lang_variants:
        for part_num in part_nums:
            # 비디오 파일 확인
            video_found = False
            for ext in ['.mp4', '.mov', '.avi', '.mkv']:
                for marker in markers:
                    pattern = f"*part{part_num}*video*{marker}*{ext}"
                    if list(input_dir.glob(pattern)):
                        video_found = True
                        break
                    pattern2 = f"*video*part{part_num}*{marker}*{ext}"
                    if list(input_dir.glob(pattern2)):
                        video_found = True
                        break
                if video_found:
                    break
            if not video_found:
                result['errors'].append(
                    f"[{lang_key.upper()}] Part {part_num} 비디오 파일 없음 (필수): "
                    f"*part{part_num}*video*{'|'.join(markers)}*.mp4"
                )

            # 인포그래픽 PNG 확인
            info_found = False
            for ext in ['.png', '.jpg', '.jpeg']:
                for marker in markers:
                    for kw in ['info', 'infographic']:
                        pattern = f"*part{part_num}*{kw}*{marker}*{ext}"
                        if list(input_dir.glob(pattern)):
                            info_found = True
                            break
                    if info_found:
                        break
                if info_found:
                    break
            if not info_found:
                result['warnings'].append(
                    f"[{lang_key.upper()}] Part {part_num} 인포그래픽 파일 없음 (선택): "
                    f"*part{part_num}*info*{'|'.join(markers)}*.png"
                )

        # 썸네일 확인
        thumbnail_found = False
        for ext in ['.png', '.jpg', '.jpeg']:
            for marker in markers:
                pattern = f"*thumbnail*{marker}*{ext}"
                if list(input_dir.glob(pattern)):
                    thumbnail_found = True
                    break
            if thumbnail_found:
                break
        if not thumbnail_found:
            result['warnings'].append(
                f"[{lang_key.upper()}] 썸네일 파일 없음 (선택): 업로드 전 필요합니다."
            )


def _print_validation_result(result: dict) -> None:
    """검증 결과를 출력합니다."""
    print()
    if result['errors']:
        print(f"❌ 오류 {len(result['errors'])}개:")
        for err in result['errors']:
            print(f"   • {err}")
    else:
        print("✅ 필수 파일 모두 확인됨")

    if result['warnings']:
        print(f"\n⚠️ 경고 {len(result['warnings'])}개:")
        for warn in result['warnings']:
            print(f"   • {warn}")

    print()
    status = "✅ 유효" if result['valid'] else "❌ 유효하지 않음"
    print(f"검증 결과: {status}")
    print("=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="input 폴더에서 파일을 준비하고 표준 네이밍으로 변경")
    parser.add_argument("--book-title", required=True, help="책 제목")
    parser.add_argument("--author", help="저자 이름")
    parser.add_argument("--prefix", help="파일명 접두사 (자동 감지 시 생략 가능)")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="검증만 실행하고 파일을 이동하지 않음"
    )
    parser.add_argument(
        "--style",
        default="summary",
        choices=["summary", "episode"],
        help="영상 스타일 (기본값: summary)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="검증 오류가 있어도 강제 진행"
    )

    args = parser.parse_args()

    # 검증 실행
    validation = validate_input_folder(
        input_dir=Path("input"),
        prefix=args.prefix,
        style=args.style
    )

    if args.validate_only:
        return 0 if validation['valid'] else 1

    # 오류가 있으면 --force 없이는 중단
    if not validation['valid'] and not args.force:
        print(
            "\n❌ 검증 실패: 필수 파일이 없습니다.\n"
            "   오류를 해결하거나 --force 옵션으로 강제 진행하세요."
        )
        return 1

    prepared_files = prepare_files(
        book_title=args.book_title,
        author=args.author,
        prefix=args.prefix
    )

    print("\n📋 준비된 파일 요약:")
    for file_type in ['audio', 'summary', 'thumbnail', 'video']:
        print(f"\n{file_type.upper()}:")
        for lang in ['en', 'ko']:
            if prepared_files[file_type][lang]:
                print(f"  {lang.upper()}: {prepared_files[file_type][lang]}")
            else:
                print(f"  {lang.upper()}: 없음")

    return 0


if __name__ == "__main__":
    main()
