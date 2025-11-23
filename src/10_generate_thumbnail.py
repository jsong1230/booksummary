"""
썸네일 자동 생성 스크립트
- 책 제목, 작가 정보가 포함된 YouTube 썸네일 생성
- 한글/영문 버전 각각 생성
- 무드 이미지, 그라데이션 배경, 또는 DALL-E 생성 이미지 사용
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
from dotenv import load_dotenv

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 공통 유틸리티 import
from utils.translations import translate_book_title, translate_author_name
from utils.file_utils import safe_title, load_book_info

load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ThumbnailGenerator:
    """썸네일 생성 클래스"""
    
    # YouTube 썸네일 권장 크기
    THUMBNAIL_SIZE = (1280, 720)  # 16:9 비율
    
    def __init__(self, use_dalle: bool = False):
        self.fonts = self._load_fonts()
        self.use_dalle = use_dalle
        self.openai_client = None
        
        if use_dalle and OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                print("✅ DALL-E API 준비 완료")
            else:
                print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. DALL-E를 사용할 수 없습니다.")
                self.use_dalle = False
    
    def _load_fonts(self) -> Dict[str, Optional[ImageFont.FreeTypeFont]]:
        """시스템 폰트 로드"""
        fonts = {
            'ko_title': None,
            'ko_subtitle': None,
            'en_title': None,
            'en_subtitle': None
        }
        
        # macOS 시스템 폰트 경로 (한글 지원 우선)
        font_paths = {
            'ko_title': [
                '/System/Library/Fonts/Supplemental/AppleSDGothicNeo-Bold.ttf',
                '/System/Library/Fonts/Supplemental/AppleSDGothicNeo-Regular.ttf',
                '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                '/Library/Fonts/AppleGothic.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/System/Library/Fonts/AppleGothic.ttc',  # TTC 파일도 시도
            ],
            'en_title': [
                '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial.ttf',
            ]
        }
        
        # 한글 제목 폰트 (큰 크기)
        for path in font_paths['ko_title']:
            if os.path.exists(path):
                try:
                    # TTC 파일인 경우 인덱스 지정
                    if path.endswith('.ttc'):
                        fonts['ko_title'] = ImageFont.truetype(path, 80, index=0)
                        fonts['ko_subtitle'] = ImageFont.truetype(path, 50, index=0)
                    else:
                        fonts['ko_title'] = ImageFont.truetype(path, 80)
                        fonts['ko_subtitle'] = ImageFont.truetype(path, 50)
                    
                    # 폰트 테스트 (한글 지원 확인)
                    try:
                        test_bbox = fonts['ko_title'].getbbox('가')
                        if test_bbox and (test_bbox[2] - test_bbox[0]) > 0:
                            print(f"   📝 한글 폰트 로드: {os.path.basename(path)}")
                            break
                        else:
                            fonts['ko_title'] = None
                            fonts['ko_subtitle'] = None
                    except:
                        # getbbox 실패해도 폰트는 사용 가능할 수 있음
                        print(f"   📝 한글 폰트 로드: {os.path.basename(path)}")
                        break
                except Exception as e:
                    print(f"   ⚠️ 폰트 로드 실패 ({os.path.basename(path)}): {e}")
                    continue
        
        # 영어 제목 폰트
        for path in font_paths['en_title']:
            if os.path.exists(path):
                try:
                    fonts['en_title'] = ImageFont.truetype(path, 80)
                    fonts['en_subtitle'] = ImageFont.truetype(path, 50)
                    print(f"   📝 영어 폰트 로드: {os.path.basename(path)}")
                    break
                except Exception as e:
                    continue
        
        # 폰트를 찾지 못한 경우 기본 폰트 사용
        if not fonts['ko_title']:
            try:
                fonts['ko_title'] = ImageFont.load_default()
                fonts['ko_subtitle'] = ImageFont.load_default()
            except:
                pass
        
        if not fonts['en_title']:
            try:
                fonts['en_title'] = ImageFont.load_default()
                fonts['en_subtitle'] = ImageFont.load_default()
            except:
                pass
        
        return fonts
    
    def _create_gradient_background(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> Image.Image:
        """그라데이션 배경 생성"""
        img = Image.new('RGB', self.THUMBNAIL_SIZE, color1)
        draw = ImageDraw.Draw(img)
        
        # 수직 그라데이션
        for y in range(self.THUMBNAIL_SIZE[1]):
            ratio = y / self.THUMBNAIL_SIZE[1]
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.line([(0, y), (self.THUMBNAIL_SIZE[0], y)], fill=(r, g, b))
        
        return img
    
    def _add_text_with_outline(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font: ImageFont.FreeTypeFont,
        fill: Tuple[int, int, int] = (255, 255, 255),
        outline_color: Tuple[int, int, int] = (0, 0, 0),
        outline_width: int = 3
    ):
        """외곽선이 있는 텍스트 추가 (한글 지원 개선)"""
        x, y = position
        
        # 폰트가 None이면 기본 텍스트 그리기
        if font is None:
            draw.text(position, text, fill=fill)
            return
        
        # 외곽선 그리기 (더 부드러운 효과를 위해)
        for adj in range(-outline_width, outline_width + 1):
            for adj2 in range(-outline_width, outline_width + 1):
                if adj != 0 or adj2 != 0:
                    try:
                        draw.text((x + adj, y + adj2), text, font=font, fill=outline_color)
                    except Exception:
                        # 폰트 렌더링 실패 시 건너뜀
                        pass
        
        # 메인 텍스트
        try:
            draw.text(position, text, font=font, fill=fill)
        except Exception as e:
            # 폰트 렌더링 실패 시 기본 텍스트
            print(f"   ⚠️ 텍스트 렌더링 실패, 기본 폰트 사용: {e}")
            draw.text(position, text, fill=fill)
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
        """텍스트를 여러 줄로 나누기"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_dalle_prompt(self, book_title: str, author: str = "", lang: str = "ko") -> str:
        """DALL-E용 프롬프트 생성"""
        if lang == "ko":
            prompt = f"""YouTube 썸네일용 고품질 일러스트레이션. 
책 "{book_title}"의 분위기를 담은 아트워크.
"""
            if author:
                prompt += f"작가: {author}. "
            
            prompt += """세련되고 현대적인 디자인, 부드러운 색감, 
텍스트를 배치할 공간이 있는 깔끔한 배경.
16:9 비율, 고해상도, 전문적인 일러스트레이션 스타일."""
        else:
            prompt = f"""High-quality illustration for YouTube thumbnail.
Artwork capturing the atmosphere of the book "{book_title}".
"""
            if author:
                prompt += f"Author: {author}. "
            
            prompt += """Sophisticated and modern design, soft color palette,
clean background with space for text placement.
16:9 aspect ratio, high resolution, professional illustration style."""
        
        return prompt
    
    def _generate_background_with_dalle(
        self,
        book_title: str,
        author: str = "",
        lang: str = "ko"
    ) -> Optional[Image.Image]:
        """DALL-E를 사용하여 배경 이미지 생성"""
        if not self.openai_client:
            return None
        
        try:
            print("🎨 DALL-E로 배경 이미지 생성 중...")
            
            prompt = self._generate_dalle_prompt(book_title, author, lang)
            
            # DALL-E 3 사용 (1024x1024 생성 후 리사이즈)
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            # 이미지 다운로드
            import requests
            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()
            
            # PIL Image로 변환
            from io import BytesIO
            img = Image.open(BytesIO(img_response.content))
            
            # 썸네일 크기에 맞게 리사이즈 및 크롭
            img = self._resize_and_crop(img, self.THUMBNAIL_SIZE)
            
            print("✅ DALL-E 이미지 생성 완료")
            return img
            
        except Exception as e:
            print(f"⚠️ DALL-E 이미지 생성 실패: {e}")
            return None
    
    def generate_thumbnail(
        self,
        book_title: str,
        author: str = "",
        lang: str = "ko",
        background_image_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        썸네일 생성
        
        Args:
            book_title: 책 제목
            author: 작가 이름
            lang: 언어 ("ko" 또는 "en")
            background_image_path: 배경 이미지 경로 (None이면 그라데이션 사용)
            output_path: 출력 경로 (None이면 자동 생성)
        
        Returns:
            생성된 썸네일 파일 경로
        """
        # 배경 이미지 로드 또는 생성
        bg = None
        
        # 1순위: DALL-E 생성 (옵션이 켜져 있는 경우)
        if self.use_dalle:
            bg = self._generate_background_with_dalle(book_title, author, lang)
            if bg:
                print("   🎨 DALL-E 생성 이미지 사용")
        
        # 2순위: 제공된 배경 이미지 사용 (DALL-E가 실패하거나 사용하지 않는 경우)
        if not bg and background_image_path and os.path.exists(background_image_path):
            bg = Image.open(background_image_path)
            # 썸네일 크기에 맞게 리사이즈 및 크롭
            bg = self._resize_and_crop(bg, self.THUMBNAIL_SIZE)
            # 약간 어둡게 (텍스트 가독성 향상)
            enhancer = ImageEnhance.Brightness(bg)
            bg = enhancer.enhance(0.7)
            # 약간 블러 처리
            bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
        
        # 3순위: 그라데이션 배경 생성
        if not bg:
            if lang == "ko":
                # 한글 버전: 어두운 파란색 그라데이션
                color1 = (30, 50, 80)
                color2 = (50, 80, 120)
            else:
                # 영어 버전: 어두운 보라색 그라데이션
                color1 = (60, 40, 80)
                color2 = (100, 70, 120)
            bg = self._create_gradient_background(color1, color2)
        
        # 텍스트 오버레이를 위한 이미지 생성
        overlay = Image.new('RGBA', self.THUMBNAIL_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 폰트 선택
        title_font = self.fonts.get(f'{lang}_title')
        subtitle_font = self.fonts.get(f'{lang}_subtitle')
        
        # 폰트가 없으면 기본 폰트 시도
        if not title_font:
            # 한글/영어 폰트 중 하나라도 있으면 사용
            title_font = self.fonts.get('ko_title') or self.fonts.get('en_title')
        
        if not subtitle_font:
            subtitle_font = self.fonts.get('ko_subtitle') or self.fonts.get('en_subtitle')
        
        # 여전히 없으면 기본 폰트 (한글 지원 안 될 수 있음)
        if not title_font:
            try:
                title_font = ImageFont.load_default()
            except:
                title_font = None
        
        if not subtitle_font:
            try:
                subtitle_font = ImageFont.load_default()
            except:
                subtitle_font = None
        
        # 폰트가 없으면 에러
        if not title_font:
            raise ValueError("폰트를 로드할 수 없습니다. 시스템 폰트를 확인하세요.")
        
        # 텍스트 준비
        if lang == "ko":
            main_text = book_title
            sub_text = f"작가: {author}" if author else "책 리뷰"
            bottom_text = "일당백 스타일"  # 이모지 제거
        else:
            # 영어 제목으로 변환 (간단한 변환, 필요시 개선)
            main_text = book_title  # 실제로는 번역 필요
            sub_text = f"Author: {author}" if author else "Book Review"
            bottom_text = "Auto-Generated"  # 이모지 제거
        
        # 제목 텍스트 줄바꿈
        if lang == "ko":
            # 한글은 글자 단위로 줄바꿈
            title_lines = []
            max_chars_per_line = 10  # 한 줄에 최대 글자 수
            for i in range(0, len(main_text), max_chars_per_line):
                title_lines.append(main_text[i:i+max_chars_per_line])
        else:
            # 영어는 단어 단위로 줄바꿈
            if title_font:
                title_lines = self._wrap_text(main_text, title_font, self.THUMBNAIL_SIZE[0] - 200)
            else:
                # 폰트가 없으면 단순 분할
                words = main_text.split()
                title_lines = []
                current_line = []
                for word in words:
                    if len(' '.join(current_line + [word])) <= 30:
                        current_line.append(word)
                    else:
                        if current_line:
                            title_lines.append(' '.join(current_line))
                        current_line = [word]
                if current_line:
                    title_lines.append(' '.join(current_line))
        
        # 텍스트 위치 계산 (중앙 정렬)
        line_height = 100 if title_font else 80
        y_start = self.THUMBNAIL_SIZE[1] // 2 - (len(title_lines) * line_height) // 2
        
        # 제목 그리기
        for i, line in enumerate(title_lines):
            if title_font:
                try:
                    bbox = title_font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                except:
                    # getbbox 실패 시 대략적인 계산
                    text_width = len(line) * 60 if lang == "ko" else len(line) * 40
                    text_height = 80
            else:
                # 폰트가 없으면 대략적인 너비 계산
                text_width = len(line) * 50
                text_height = 80
            
            x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
            y = y_start + i * line_height
            
            # 텍스트 그리기 (폰트가 있으면 외곽선 포함)
            if title_font:
                try:
                    # 직접 텍스트 그리기 (외곽선 포함)
                    # 외곽선
                    for adj_x in range(-4, 5):
                        for adj_y in range(-4, 5):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), line, font=title_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    draw.text((x, y), line, font=title_font, fill=(255, 255, 255))
                except Exception as e:
                    # 폰트 렌더링 실패 시 기본 텍스트
                    print(f"   ⚠️ 제목 텍스트 렌더링 실패: {e}")
                    draw.text((x, y), line, fill=(255, 255, 255))
            else:
                # 폰트가 없으면 기본 텍스트 그리기
                draw.text((x, y), line, fill=(255, 255, 255))
        
        # 작가 이름 그리기 (제목 아래)
        if sub_text:
            if subtitle_font:
                try:
                    bbox = subtitle_font.getbbox(sub_text)
                    text_width = bbox[2] - bbox[0]
                    x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
                    y = y_start + len(title_lines) * line_height + 30
                    
                    # 외곽선
                    for adj_x in range(-2, 3):
                        for adj_y in range(-2, 3):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), sub_text, font=subtitle_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    draw.text((x, y), sub_text, font=subtitle_font, fill=(220, 220, 220))
                except Exception as e:
                    print(f"   ⚠️ 작가 이름 렌더링 실패: {e}")
                    x = (self.THUMBNAIL_SIZE[0] - len(sub_text) * 30) // 2
                    y = y_start + len(title_lines) * line_height + 30
                    draw.text((x, y), sub_text, fill=(220, 220, 220))
            else:
                # 폰트가 없으면 기본 텍스트
                x = (self.THUMBNAIL_SIZE[0] - len(sub_text) * 30) // 2
                y = y_start + len(title_lines) * line_height + 30
                draw.text((x, y), sub_text, fill=(220, 220, 220))
        
        # 하단 텍스트 (작은 크기)
        if bottom_text:
            if subtitle_font:
                try:
                    bbox = subtitle_font.getbbox(bottom_text)
                    text_width = bbox[2] - bbox[0]
                    x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
                    y = self.THUMBNAIL_SIZE[1] - 80
                    
                    # 외곽선
                    for adj_x in range(-2, 3):
                        for adj_y in range(-2, 3):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), bottom_text, font=subtitle_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    draw.text((x, y), bottom_text, font=subtitle_font, fill=(200, 200, 200))
                except Exception as e:
                    print(f"   ⚠️ 하단 텍스트 렌더링 실패: {e}")
                    x = (self.THUMBNAIL_SIZE[0] - len(bottom_text) * 25) // 2
                    y = self.THUMBNAIL_SIZE[1] - 80
                    draw.text((x, y), bottom_text, fill=(200, 200, 200))
            else:
                # 폰트가 없으면 기본 텍스트
                x = (self.THUMBNAIL_SIZE[0] - len(bottom_text) * 25) // 2
                y = self.THUMBNAIL_SIZE[1] - 80
                draw.text((x, y), bottom_text, fill=(200, 200, 200))
        
        # 배경과 오버레이 합성
        bg_rgba = bg.convert('RGBA')
        final = Image.alpha_composite(bg_rgba, overlay)
        final = final.convert('RGB')
        
        # 출력 경로 설정
        if not output_path:
            safe_title_str = safe_title(book_title)
            output_path = f"output/{safe_title_str}_thumbnail_{lang}.jpg"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 저장
        final.save(output_path, 'JPEG', quality=95)
        print(f"✅ 썸네일 생성 완료: {output_path}")
        
        return str(output_path)
    
    def _resize_and_crop(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
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


# load_book_info는 utils.file_utils에서 import됨


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='썸네일 자동 생성')
    parser.add_argument('--book-title', type=str, required=True, help='책 제목')
    parser.add_argument('--author', type=str, default='', help='작가 이름')
    parser.add_argument('--lang', type=str, choices=['ko', 'en', 'both'], default='both', help='언어 (기본값: both)')
    parser.add_argument('--background', type=str, help='배경 이미지 경로 (선택사항)')
    parser.add_argument('--output-dir', type=str, default='output', help='출력 디렉토리')
    parser.add_argument('--use-dalle', action='store_true', help='DALL-E를 사용하여 배경 이미지 생성')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🖼️ 썸네일 자동 생성")
    print("=" * 60)
    print()
    
    # 책 정보 로드
    book_info = load_book_info(args.book_title)
    if book_info and not args.author:
        authors = book_info.get('authors', [])
        if authors:
            args.author = ', '.join(authors)
    
    # 배경 이미지 찾기 (무드 이미지 중 하나)
    # DALL-E를 사용하는 경우 배경 이미지를 사용하지 않음
    background_image = args.background
    if not args.use_dalle and not background_image:
        safe_title_str = safe_title(args.book_title)
        image_dir = Path("assets/images") / safe_title_str
        if image_dir.exists():
            mood_images = sorted(image_dir.glob("mood_*.jpg"))
            if mood_images:
                background_image = str(mood_images[0])
                print(f"📸 배경 이미지 사용: {mood_images[0].name}")
    
    generator = ThumbnailGenerator(use_dalle=args.use_dalle)
    
    # 썸네일 생성
    if args.lang == "both":
        # 한글 버전
        ko_path = generator.generate_thumbnail(
            book_title=args.book_title,
            author=args.author,
            lang="ko",
            background_image_path=background_image,
            output_path=f"{args.output_dir}/{args.book_title.replace(' ', '_')}_thumbnail_ko.jpg"
        )
        
        # 영어 버전
        en_title = translate_book_title(args.book_title)
        # 영어 작가 이름도 변환 (간단한 매핑)
        en_author = args.author
        if args.author:
            # 무라카미 하루키 -> Haruki Murakami
            author_translations = {
                "무라카미 하루키": "Haruki Murakami",
            }
            en_author = author_translations.get(args.author, args.author)
        
        en_path = generator.generate_thumbnail(
            book_title=en_title,
            author=en_author,
            lang="en",
            background_image_path=background_image,
            output_path=f"{args.output_dir}/{args.book_title.replace(' ', '_')}_thumbnail_en.jpg"
        )
        
        print()
        print("✅ 썸네일 생성 완료:")
        print(f"   한글: {ko_path}")
        print(f"   영어: {en_path}")
    else:
        # 단일 언어 버전
        book_title = args.book_title
        author = args.author
        
        if args.lang == "en":
            book_title = translate_book_title(args.book_title)
            # 영어 작가 이름도 변환
            if author:
                author_translations = {
                    "무라카미 하루키": "Haruki Murakami",
                }
                author = author_translations.get(author, author)
        
        path = generator.generate_thumbnail(
            book_title=book_title,
            author=author,
            lang=args.lang,
            background_image_path=background_image,
            output_path=f"{args.output_dir}/{args.book_title.replace(' ', '_')}_thumbnail_{args.lang}.jpg"
        )
        
        print()
        print(f"✅ 썸네일 생성 완료: {path}")


if __name__ == "__main__":
    main()

