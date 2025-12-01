#!/usr/bin/env python3
"""
output 폴더의 PNG 파일을 JPG로 변환하여 롱폼 썸네일로 사용 가능하게 함
"""

from pathlib import Path
from PIL import Image

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
        print(f"   📖 이미지 로드 중: {input_path.name}")
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
        print(f"   🔄 리사이즈 중: {img.size} -> {THUMBNAIL_SIZE}")
        img = resize_and_crop(img, THUMBNAIL_SIZE)
        
        # 압축 (품질 조정하여 2MB 이하로)
        print(f"   💾 압축 중...")
        quality = 95
        while quality >= 50:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"      품질 {quality}: {file_size_mb:.2f} MB")
            
            if file_size_mb <= MAX_SIZE_MB:
                print(f"   ✅ 압축 완료: {file_size_mb:.2f} MB (품질: {quality})")
                return True
            
            quality -= 5
        
        # 최소 품질로도 2MB를 넘으면 경고
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_SIZE_MB:
            print(f"   ⚠️ 경고: 파일 크기가 {file_size_mb:.2f} MB로 2MB를 초과합니다.")
            print(f"      해상도를 낮춰서 다시 시도합니다...")
            
            # 해상도를 90%로 줄여서 재시도
            new_size = (int(THUMBNAIL_SIZE[0] * 0.9), int(THUMBNAIL_SIZE[1] * 0.9))
            img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
            # 다시 원래 크기로 확대 (약간의 품질 손실)
            img_resized = img_resized.resize(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            quality = 85
            while quality >= 50:
                img_resized.save(output_path, 'JPEG', quality=quality, optimize=True)
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                if file_size_mb <= MAX_SIZE_MB:
                    print(f"   ✅ 압축 완료 (해상도 조정): {file_size_mb:.2f} MB (품질: {quality})")
                    return True
                quality -= 5
        
        # 성공적으로 저장된 경우
        if output_path.exists():
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ 변환 완료: {file_size_mb:.2f} MB (품질: {quality})")
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    output_dir = Path("output")
    
    # PNG 파일 찾기
    png_files = list(output_dir.glob("*.png"))
    
    if not png_files:
        print("❌ output 폴더에 PNG 파일이 없습니다.")
        return
    
    print(f"📁 발견된 PNG 파일: {len(png_files)}개")
    for png_file in png_files:
        print(f"   - {png_file.name}")
    
    # 각 PNG 파일을 JPG로 변환
    for png_file in png_files:
        print(f"\n{'='*60}")
        print(f"🔄 처리 중: {png_file.name}")
        print(f"{'='*60}")
        
        # 파일명에서 언어 추측
        filename_lower = png_file.name.lower()
        if 'anxious' in filename_lower or '_en' in filename_lower or 'english' in filename_lower:
            # 영어용으로 추정
            output_path = output_dir / f"{png_file.stem}_thumbnail_en.jpg"
        elif '불안' in png_file.name or '_ko' in filename_lower or 'korean' in filename_lower or '한글' in filename_lower:
            # 한글용으로 추정
            output_path = output_dir / f"{png_file.stem}_thumbnail_ko.jpg"
        else:
            # 파일명 그대로 사용
            output_path = output_dir / f"{png_file.stem}_thumbnail.jpg"
        
        # PNG를 JPG로 변환
        success = convert_png_to_jpg(png_file, output_path)
        
        if success:
            print(f"✅ 변환 완료: {output_path.name}")
            # 원본 PNG 파일 삭제
            try:
                png_file.unlink()
                print(f"   🗑️ 원본 PNG 파일 삭제: {png_file.name}")
            except Exception as e:
                print(f"   ⚠️ 원본 PNG 파일 삭제 실패: {e}")
        else:
            print(f"❌ 변환 실패: {png_file.name}")
    
    print(f"\n{'='*60}")
    print("✅ 모든 PNG 파일 처리 완료")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
