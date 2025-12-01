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
from utils.translations import translate_book_title, translate_author_name, translate_book_title_to_korean, is_english_title, translate_author_name_to_korean
from utils.file_utils import safe_title, load_book_info

load_dotenv()

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ThumbnailGenerator:
    """썸네일 생성 클래스"""
    
    # YouTube 썸네일 권장 크기 (최대 해상도)
    # 옵션: (1280, 720) 기본, (1920, 1080) Full HD, (2560, 1440) 2K, (3840, 2160) 4K
    THUMBNAIL_SIZE = (3840, 2160)  # 16:9 비율, 4K 해상도
    
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
                        fonts['ko_title'] = ImageFont.truetype(path, 240, index=0)  # 4K 해상도에 맞춰 폰트 크기 증가
                        fonts['ko_subtitle'] = ImageFont.truetype(path, 150, index=0)
                    else:
                        fonts['ko_title'] = ImageFont.truetype(path, 240)  # 4K 해상도에 맞춰 폰트 크기 증가
                        fonts['ko_subtitle'] = ImageFont.truetype(path, 150)
                    
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
        
        # 영어 제목 폰트 (더 많은 폰트 경로 시도)
        en_font_paths = [
            '/System/Library/Fonts/Supplemental/Arial Bold.ttf',  # 가장 확실한 폰트 우선
            '/System/Library/Fonts/Supplemental/Arial Black.ttf',
            '/System/Library/Fonts/Supplemental/Arial.ttf',
            '/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf',
            '/System/Library/Fonts/Supplemental/Times New Roman.ttf',
            '/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ]
        
        for path in en_font_paths:
            if os.path.exists(path):
                try:
                    # TTC 파일인 경우 인덱스 지정
                    if path.endswith('.ttc'):
                        test_font = ImageFont.truetype(path, 240, index=0)
                    else:
                        test_font = ImageFont.truetype(path, 240)
                    
                    # 실제 렌더링 테스트로 폰트가 제대로 작동하는지 확인
                    test_img = Image.new('RGB', (200, 100), 'white')
                    test_draw = ImageDraw.Draw(test_img)
                    try:
                        test_draw.text((10, 10), 'Farewell', font=test_font, fill='black')
                        # 테스트 성공 - 폰트 사용
                        fonts['en_title'] = ImageFont.truetype(path, 240, index=0) if path.endswith('.ttc') else ImageFont.truetype(path, 240)
                        fonts['en_subtitle'] = ImageFont.truetype(path, 150, index=0) if path.endswith('.ttc') else ImageFont.truetype(path, 150)
                        print(f"   📝 영어 폰트 로드: {os.path.basename(path)}")
                        break
                    except Exception as render_error:
                        # 렌더링 실패 - 다음 폰트 시도
                        continue
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
    
    def _search_author_or_book_image(self, book_title: str, author: str = "", lang: str = "ko") -> Optional[str]:
        """작가나 책 관련 이미지를 Unsplash/Pexels에서 검색"""
        try:
            from utils.translations import translate_book_title, translate_author_name, translate_book_title_to_korean, is_english_title, translate_author_name_to_korean
            
            # book_title이 영어인지 한글인지 판단
            if is_english_title(book_title):
                # 영어 제목이 들어온 경우
                en_title = book_title
                ko_title = translate_book_title_to_korean(book_title)
            else:
                # 한글 제목이 들어온 경우
                ko_title = book_title
                en_title = translate_book_title(book_title)
            
            # 항상 영어 키워드로 검색 (Unsplash/Pexels는 영어 검색이 더 잘 됨)
            en_author = translate_author_name(author) if author else None
            
            search_keywords = []
            
            # 작가 이름을 먼저 추가 (작가 이미지가 더 관련성이 높을 수 있음)
            if en_author and en_author != author:
                # 작가 이름 관련 키워드 우선
                search_keywords.append(f"{en_author} portrait")  # 작가 초상화 검색 (가장 관련성 높음)
                search_keywords.append(en_author)
                search_keywords.append(f"{en_author} author")  # "Hermann Hesse author" 같은 키워드 추가
                search_keywords.append(f"{en_author} writer")  # "Hermann Hesse writer"
                search_keywords.append(f"{en_author} novelist")  # "Hermann Hesse novelist"
                # 성만 사용한 검색도 추가
                if " " in en_author:
                    last_name = en_author.split()[-1]  # "Hesse"
                    search_keywords.append(f"{last_name} author")
                    search_keywords.append(last_name)
            elif author and lang == "en":
                # 이미 영어인 경우
                search_keywords.append(f"{author} portrait")
                search_keywords.append(author)
                search_keywords.append(f"{author} author")
                search_keywords.append(f"{author} writer")
                search_keywords.append(f"{author} novelist")
                if " " in author:
                    last_name = author.split()[-1]
                    search_keywords.append(f"{last_name} author")
                    search_keywords.append(last_name)
            
            # 책 제목 추가 (작가 이미지를 찾지 못한 경우를 대비)
            if en_title and en_title != book_title:
                search_keywords.append(f"{en_title} book")  # "Demian book" 같은 키워드 추가
                search_keywords.append(f"{en_title} novel")  # "Demian novel"
                search_keywords.append(en_title)  # 마지막에 일반 제목
            elif lang == "en":
                # 이미 영어인 경우
                search_keywords.append(f"{book_title} book")
                search_keywords.append(f"{book_title} novel")
                search_keywords.append(book_title)
            else:
                # 한글인 경우 영어 제목이 없으면 원본 사용
                search_keywords.append(book_title)
            
            # 이미지 디렉토리 확인
            from utils.file_utils import safe_title
            safe_title_str = safe_title(book_title)
            image_dir = Path("assets/images") / safe_title_str
            
            # 이미지 다운로더 사용
            import importlib.util
            images_path = Path(__file__).parent / "02_get_images.py"
            spec = importlib.util.spec_from_file_location("get_images", images_path)
            images_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(images_module)
            downloader = images_module.ImageDownloader()
            
            # 작가나 책 관련 이미지 검색 (저작권 없는 이미지)
            print(f"   🔍 작가/책 이미지 검색 중: {', '.join(search_keywords)}")
            
            # 이미지 디렉토리 생성
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # 추가 일반적인 키워드 (작가/책 관련 이미지를 찾지 못한 경우)
            if en_author:
                search_keywords.extend([
                    "German literature",
                    "classic literature",
                    "vintage book",
                    "old book"
                ])
            
            # Unsplash에서 검색 시도 - 모든 키워드를 순차적으로 시도
            if downloader.unsplash_access_key:
                try:
                    # 작가나 책 제목으로 검색
                    for keyword in search_keywords:
                        if not keyword:
                            continue
                        print(f"  🔍 Unsplash 검색: {keyword}")
                        result = downloader.download_mood_images_unsplash([keyword], 1, image_dir)
                        if result:
                            print(f"  ✅ 이미지 다운로드 완료: {result[0]}")
                            return result[0]
                except Exception as e:
                    print(f"    ⚠️ 오류: {e}")
                    pass
            
            # Pexels에서 검색 시도 - 모든 키워드를 순차적으로 시도
            if downloader.pexels:
                try:
                    for keyword in search_keywords:
                        if not keyword:
                            continue
                        print(f"  🔍 Pexels 검색: {keyword}")
                        result = downloader.download_mood_images_pexels([keyword], 1, image_dir)
                        if result:
                            print(f"  ✅ 이미지 다운로드 완료: {result[0]}")
                            return result[0]
                except Exception as e:
                    print(f"    ⚠️ 오류: {e}")
                    pass
            
            return None
        except Exception as e:
            print(f"   ⚠️ 작가/책 이미지 검색 실패: {e}")
            return None
    
    def generate_thumbnail(
        self,
        book_title: str,
        author: str = "",
        lang: str = "ko",
        background_image_path: Optional[str] = None,
        output_path: Optional[str] = None,
        use_author_image: bool = True
    ) -> Optional[str]:
        """
        썸네일 생성 (더 이상 자동 생성하지 않음 - PNG 파일 우선 처리)
        
        주의: 이 메서드는 더 이상 사용되지 않습니다. 
        대신 process_png_thumbnails()를 사용하여 Nano Banana에서 만든 PNG 파일을 처리하세요.
        
        Args:
            book_title: 책 제목
            author: 작가 이름
            lang: 언어 ("ko" 또는 "en")
            background_image_path: 배경 이미지 경로 (사용 안 함)
            output_path: 출력 경로 (사용 안 함)
            use_author_image: 작가/책 이미지 사용 여부 (사용 안 함)
        
        Returns:
            None (경고 메시지만 출력)
        """
        print("   ⚠️ 썸네일 자동 생성은 더 이상 지원되지 않습니다.")
        print("   💡 Nano Banana에서 썸네일을 만들어서 output 폴더에 넣어주세요.")
        print("      파일명 예시: {책제목}_kr.png, {책제목}_en.png")
        print("      그 후 process_png_thumbnails() 메서드를 사용하세요.")
        return None
        
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
        
        # 3순위: 작가/책 이미지 검색 (저작권 없는 이미지)
        if not bg and use_author_image:
            author_image_path = self._search_author_or_book_image(book_title, author, lang)
            if author_image_path and os.path.exists(author_image_path):
                bg = Image.open(author_image_path)
                # 썸네일 크기에 맞게 리사이즈 및 크롭
                bg = self._resize_and_crop(bg, self.THUMBNAIL_SIZE)
                # 약간 어둡게 (텍스트 가독성 향상)
                enhancer = ImageEnhance.Brightness(bg)
                bg = enhancer.enhance(0.7)
                # 약간 블러 처리
                bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
                print("   🎨 작가/책 이미지 사용")
        
        # 4순위: 그라데이션 배경 생성
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
        # book_title이 영어인지 한글인지 판단
        if is_english_title(book_title):
            # 영어 제목이 들어온 경우
            en_title = book_title
            ko_title = translate_book_title_to_korean(book_title)
        else:
            # 한글 제목이 들어온 경우
            ko_title = book_title
            en_title = translate_book_title(book_title)
        
        if lang == "ko":
            # 한글 썸네일: 한글 제목 사용
            main_text = ko_title if ko_title and not is_english_title(ko_title) else book_title
            # 작가 이름도 한글인지 확인
            if author:
                if is_english_title(author):
                    # 영어 작가 이름인 경우 한글로 변환
                    ko_author = translate_author_name_to_korean(author)
                    sub_text = f"작가: {ko_author}"
                else:
                    sub_text = f"작가: {author}"
            else:
                sub_text = "책 리뷰"
            bottom_text = "일당백 스타일"  # 이모지 제거
        else:
            # 영어 썸네일: 영어 제목 사용
            main_text = en_title if en_title and is_english_title(en_title) else book_title
            # 작가 이름도 영어로 변환
            if author:
                if is_english_title(author):
                    en_author = author
                else:
                    en_author = translate_author_name(author)
                sub_text = f"Author: {en_author}" if en_author else "Book Review"
            else:
                sub_text = "Book Review"
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
                title_lines = self._wrap_text(main_text, title_font, self.THUMBNAIL_SIZE[0] - 600)  # 4K 해상도에 맞춰 여백 증가
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
        line_height = 300 if title_font else 240  # 4K 해상도에 맞춰 증가
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
                    text_width = len(line) * 180 if lang == "ko" else len(line) * 120  # 4K 해상도에 맞춰 증가
                    text_height = 240
            else:
                # 폰트가 없으면 대략적인 너비 계산
                text_width = len(line) * 150  # 4K 해상도에 맞춰 증가
                text_height = 240
            
            x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
            y = y_start + i * line_height
            
            # 텍스트 그리기 (폰트가 있으면 외곽선 포함)
            if title_font:
                try:
                    # 직접 텍스트 그리기 (외곽선 포함)
                    # 외곽선 (4K 해상도에 맞춰 증가)
                    for adj_x in range(-8, 9):
                        for adj_y in range(-8, 9):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), line, font=title_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    try:
                        draw.text((x, y), line, font=title_font, fill=(255, 255, 255))
                    except Exception as text_error:
                        # 텍스트 렌더링 실패 시 상세 로그
                        print(f"   ⚠️ 제목 텍스트 렌더링 실패 (텍스트: '{line}', 폰트: {title_font}): {text_error}")
                        import traceback
                        traceback.print_exc()
                        # 폰트 없이 재시도
                        draw.text((x, y), line, fill=(255, 255, 255))
                except Exception as e:
                    # 폰트 렌더링 실패 시 기본 텍스트
                    print(f"   ⚠️ 제목 텍스트 렌더링 실패 (전체): {e}")
                    import traceback
                    traceback.print_exc()
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
                    y = y_start + len(title_lines) * line_height + 90  # 4K 해상도에 맞춰 증가
                    
                    # 외곽선 (4K 해상도에 맞춰 증가)
                    for adj_x in range(-6, 7):
                        for adj_y in range(-6, 7):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), sub_text, font=subtitle_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    try:
                        draw.text((x, y), sub_text, font=subtitle_font, fill=(220, 220, 220))
                    except Exception as text_error:
                        # 텍스트 렌더링 실패 시 상세 로그
                        print(f"   ⚠️ 작가 이름 텍스트 렌더링 실패 (텍스트: '{sub_text}', 폰트: {subtitle_font}): {text_error}")
                        import traceback
                        traceback.print_exc()
                        # 폰트 없이 재시도
                        x = (self.THUMBNAIL_SIZE[0] - len(sub_text) * 60) // 2
                        y = y_start + len(title_lines) * line_height + 60
                        draw.text((x, y), sub_text, fill=(220, 220, 220))
                except Exception as e:
                    print(f"   ⚠️ 작가 이름 렌더링 실패 (전체): {e}")
                    import traceback
                    traceback.print_exc()
                    x = (self.THUMBNAIL_SIZE[0] - len(sub_text) * 90) // 2  # 4K 해상도에 맞춰 증가
                    y = y_start + len(title_lines) * line_height + 90  # 4K 해상도에 맞춰 증가
                    draw.text((x, y), sub_text, fill=(220, 220, 220))
            else:
                # 폰트가 없으면 기본 텍스트
                x = (self.THUMBNAIL_SIZE[0] - len(sub_text) * 60) // 2  # 해상도 2배에 맞춰 증가
                y = y_start + len(title_lines) * line_height + 60  # 해상도 2배에 맞춰 증가
                draw.text((x, y), sub_text, fill=(220, 220, 220))
        
        # 하단 텍스트 (작은 크기)
        if bottom_text:
            if subtitle_font:
                try:
                    bbox = subtitle_font.getbbox(bottom_text)
                    text_width = bbox[2] - bbox[0]
                    x = (self.THUMBNAIL_SIZE[0] - text_width) // 2
                    y = self.THUMBNAIL_SIZE[1] - 240  # 4K 해상도에 맞춰 증가
                    
                    # 외곽선 (4K 해상도에 맞춰 증가)
                    for adj_x in range(-6, 7):
                        for adj_y in range(-6, 7):
                            if adj_x != 0 or adj_y != 0:
                                try:
                                    draw.text((x + adj_x, y + adj_y), bottom_text, font=subtitle_font, fill=(0, 0, 0))
                                except:
                                    pass
                    # 메인 텍스트
                    draw.text((x, y), bottom_text, font=subtitle_font, fill=(200, 200, 200))
                except Exception as e:
                    print(f"   ⚠️ 하단 텍스트 렌더링 실패: {e}")
                    x = (self.THUMBNAIL_SIZE[0] - len(bottom_text) * 75) // 2  # 4K 해상도에 맞춰 증가
                    y = self.THUMBNAIL_SIZE[1] - 240  # 4K 해상도에 맞춰 증가
                    draw.text((x, y), bottom_text, fill=(200, 200, 200))
            else:
                # 폰트가 없으면 기본 텍스트
                x = (self.THUMBNAIL_SIZE[0] - len(bottom_text) * 50) // 2  # 해상도 2배에 맞춰 증가
                y = self.THUMBNAIL_SIZE[1] - 160  # 해상도 2배에 맞춰 증가
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
        
        # 저장 (고품질)
        final.save(output_path, 'JPEG', quality=98, optimize=True)
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
    
    def process_png_thumbnails(
        self,
        book_title: str,
        output_dir: Path = None
    ) -> Dict[str, Optional[str]]:
        """
        output 폴더의 PNG 썸네일 파일을 찾아서 리사이즈 및 압축하여 JPG로 변환
        (Nano Banana에서 수동으로 만든 PNG 파일 처리)
        
        Args:
            book_title: 책 제목
            output_dir: output 폴더 경로 (기본값: output/)
            
        Returns:
            {'ko': 한글 썸네일 경로, 'en': 영어 썸네일 경로}
        """
        if output_dir is None:
            output_dir = Path("output")
        
        safe_title_str = safe_title(book_title)
        
        # output 폴더에서 PNG 파일 찾기
        png_files = list(output_dir.glob("*.png"))
        
        if not png_files:
            print("   📭 output 폴더에 PNG 파일이 없습니다.")
            print("   💡 Nano Banana에서 만든 썸네일 PNG 파일을 output 폴더에 넣어주세요.")
            print("      파일명 예시: {책제목}_kr.png, {책제목}_en.png 또는 {책제목}_ko.png, {책제목}_en.png")
            return {'ko': None, 'en': None}
        
        print(f"   📁 발견된 PNG 파일: {len(png_files)}개")
        for png_file in png_files:
            print(f"      - {png_file.name}")
        
        # 썸네일 파일명 패턴
        thumbnail_ko_path = output_dir / f"{safe_title_str}_thumbnail_ko.jpg"
        thumbnail_en_path = output_dir / f"{safe_title_str}_thumbnail_en.jpg"
        
        result = {'ko': None, 'en': None}
        
        # PNG 파일을 언어별로 구분 (kr, ko, en 등으로 구분)
        ko_png_files = []
        en_png_files = []
        unknown_png_files = []
        
        for png_file in png_files:
            filename_lower = png_file.name.lower()
            # 파일명에 언어 표시가 있는지 확인 (kr, ko, en 등)
            if '_kr' in filename_lower or '_ko' in filename_lower or 'korean' in filename_lower or '한글' in filename_lower or '한국어' in filename_lower:
                ko_png_files.append(png_file)
            elif '_en' in filename_lower or 'english' in filename_lower or '영어' in filename_lower or '영문' in filename_lower:
                en_png_files.append(png_file)
            else:
                unknown_png_files.append(png_file)
        
        # PNG 파일을 썸네일로 변환
        if len(ko_png_files) > 0 and len(en_png_files) > 0:
            # 파일명으로 구분 가능한 경우
            print(f"   ✅ 파일명으로 언어 구분: 한글 {len(ko_png_files)}개, 영어 {len(en_png_files)}개")
            
            if thumbnail_ko_path.parent.exists() and ko_png_files:
                ko_path = self._resize_and_compress_png(ko_png_files[0], thumbnail_ko_path)
                if ko_path:
                    result['ko'] = str(ko_path)
            
            if thumbnail_en_path.parent.exists() and en_png_files:
                en_path = self._resize_and_compress_png(en_png_files[0], thumbnail_en_path)
                if en_path:
                    result['en'] = str(en_path)
        
        elif len(ko_png_files) > 0:
            # 한글용만 있는 경우
            print(f"   ✅ 한글 썸네일만 발견: {len(ko_png_files)}개")
            if thumbnail_ko_path.parent.exists() and ko_png_files:
                ko_path = self._resize_and_compress_png(ko_png_files[0], thumbnail_ko_path)
                if ko_path:
                    result['ko'] = str(ko_path)
        
        elif len(en_png_files) > 0:
            # 영어용만 있는 경우
            print(f"   ✅ 영어 썸네일만 발견: {len(en_png_files)}개")
            if thumbnail_en_path.parent.exists() and en_png_files:
                en_path = self._resize_and_compress_png(en_png_files[0], thumbnail_en_path)
                if en_path:
                    result['en'] = str(en_path)
        
        elif len(png_files) == 1:
            # 하나의 PNG를 두 썸네일에 모두 사용
            png_file = png_files[0]
            print(f"   📝 단일 PNG 파일을 두 썸네일에 적용합니다.")
            
            if thumbnail_ko_path.parent.exists():
                ko_path = self._resize_and_compress_png(png_file, thumbnail_ko_path)
                if ko_path:
                    result['ko'] = str(ko_path)
            
            if thumbnail_en_path.parent.exists():
                en_path = self._resize_and_compress_png(png_file, thumbnail_en_path)
                if en_path:
                    result['en'] = str(en_path)
        
        elif len(png_files) >= 2:
            # 두 개 이상의 PNG 파일이 있으면 수정 시간 순서로 매칭
            # (구분 불가능한 경우)
            if unknown_png_files:
                png_files_sorted = sorted(unknown_png_files, key=lambda x: x.stat().st_mtime, reverse=True)
                print(f"   ⚠️ 파일명으로 언어를 구분할 수 없습니다. 수정 시간 순서로 매칭합니다.")
                print(f"      (최신 파일 → 영어, 그 다음 → 한글)")
                print(f"   💡 파일명에 _kr, _ko, _en 등을 포함하여 언어를 구분해주세요.")
                
                # 첫 번째 파일을 영어용으로
                if thumbnail_en_path.parent.exists() and len(png_files_sorted) > 0:
                    en_path = self._resize_and_compress_png(png_files_sorted[0], thumbnail_en_path)
                    if en_path:
                        result['en'] = str(en_path)
                
                # 두 번째 파일을 한글용으로
                if thumbnail_ko_path.parent.exists() and len(png_files_sorted) > 1:
                    ko_path = self._resize_and_compress_png(png_files_sorted[1], thumbnail_ko_path)
                    if ko_path:
                        result['ko'] = str(ko_path)
            else:
                # 일부는 구분 가능하고 일부는 불가능한 경우
                if ko_png_files and thumbnail_ko_path.parent.exists():
                    ko_path = self._resize_and_compress_png(ko_png_files[0], thumbnail_ko_path)
                    if ko_path:
                        result['ko'] = str(ko_path)
                
                if en_png_files and thumbnail_en_path.parent.exists():
                    en_path = self._resize_and_compress_png(en_png_files[0], thumbnail_en_path)
                    if en_path:
                        result['en'] = str(en_path)
        
        return result
    
    def _resize_and_compress_png(
        self,
        input_path: Path,
        output_path: Path,
        max_size_mb: float = 2.0
    ) -> Optional[Path]:
        """
        PNG 파일을 리사이즈하고 압축하여 JPG로 저장
        
        Args:
            input_path: 입력 PNG 파일 경로
            output_path: 출력 JPG 파일 경로
            max_size_mb: 최대 파일 크기 (MB)
            
        Returns:
            생성된 파일 경로 (None이면 실패)
        """
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
            print(f"   🔄 리사이즈 중: {img.size} -> {self.THUMBNAIL_SIZE}")
            img = self._resize_and_crop(img, self.THUMBNAIL_SIZE)
            
            # 압축 (품질 조정하여 2MB 이하로)
            print(f"   💾 압축 중...")
            quality = 95
            while quality >= 50:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                print(f"      품질 {quality}: {file_size_mb:.2f} MB")
                
                if file_size_mb <= max_size_mb:
                    print(f"   ✅ 압축 완료: {file_size_mb:.2f} MB (품질: {quality})")
                    # 원본 PNG 파일 삭제
                    try:
                        input_path.unlink()
                        print(f"   🗑️ 원본 PNG 파일 삭제: {input_path.name}")
                    except Exception as e:
                        print(f"   ⚠️ 원본 PNG 파일 삭제 실패: {e}")
                    return output_path
                
                quality -= 5
            
            # 최소 품질로도 2MB를 넘으면 경고
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                print(f"   ⚠️ 경고: 파일 크기가 {file_size_mb:.2f} MB로 2MB를 초과합니다.")
                print(f"      해상도를 낮춰서 다시 시도합니다...")
                
                # 해상도를 90%로 줄여서 재시도
                new_size = (int(self.THUMBNAIL_SIZE[0] * 0.9), int(self.THUMBNAIL_SIZE[1] * 0.9))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                # 다시 원래 크기로 확대 (약간의 품질 손실)
                img_resized = img_resized.resize(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                quality = 85
                while quality >= 50:
                    img_resized.save(output_path, 'JPEG', quality=quality, optimize=True)
                    file_size_mb = output_path.stat().st_size / (1024 * 1024)
                    if file_size_mb <= max_size_mb:
                        print(f"   ✅ 압축 완료 (해상도 조정): {file_size_mb:.2f} MB (품질: {quality})")
                        # 원본 PNG 파일 삭제
                        try:
                            input_path.unlink()
                            print(f"   🗑️ 원본 PNG 파일 삭제: {input_path.name}")
                        except Exception as e:
                            print(f"   ⚠️ 원본 PNG 파일 삭제 실패: {e}")
                        return output_path
                    quality -= 5
            
            # 성공적으로 저장된 경우에도 원본 삭제
            if output_path.exists():
                try:
                    input_path.unlink()
                    print(f"   🗑️ 원본 PNG 파일 삭제: {input_path.name}")
                except Exception as e:
                    print(f"   ⚠️ 원본 PNG 파일 삭제 실패: {e}")
            
            return output_path
            
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return None


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
    parser.add_argument('--use-author-image', action='store_true', default=True, help='작가/책 이미지 사용 (Unsplash/Pexels에서 검색, 기본값: True)')
    parser.add_argument('--no-author-image', dest='use_author_image', action='store_false', help='작가/책 이미지 사용 안 함')
    
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
    # 작가/책 이미지를 사용하는 경우도 무드 이미지를 우선 사용하지 않음
    background_image = args.background
    if not args.use_dalle and not background_image and not args.use_author_image:
        safe_title_str = safe_title(args.book_title)
        image_dir = Path("assets/images") / safe_title_str
        if image_dir.exists():
            mood_images = sorted(image_dir.glob("mood_*.jpg"))
            if mood_images:
                background_image = str(mood_images[0])
                print(f"📸 배경 이미지 사용: {mood_images[0].name}")
    
    generator = ThumbnailGenerator(use_dalle=args.use_dalle)
    
    # 작가/책 이미지를 사용하는 경우 background_image를 None으로 설정
    if args.use_author_image:
        background_image = None
    
    # 썸네일 생성
    if args.lang == "both":
        # 한글 버전
        ko_path = generator.generate_thumbnail(
            book_title=args.book_title,
            author=args.author,
            lang="ko",
            background_image_path=background_image,
            use_author_image=args.use_author_image,
            output_path=f"{args.output_dir}/{args.book_title.replace(' ', '_')}_thumbnail_ko.jpg"
        )
        
        # 영어 버전
        # book_title이 영어인지 한글인지 판단
        if is_english_title(args.book_title):
            # 영어 제목이 들어온 경우
            en_title = args.book_title
        else:
            # 한글 제목이 들어온 경우 영어로 변환
            en_title = translate_book_title(args.book_title)
        
        # 영어 작가 이름도 변환
        en_author = args.author
        if args.author:
            if is_english_title(args.author):
                en_author = args.author
            else:
                en_author = translate_author_name(args.author)
        
        en_path = generator.generate_thumbnail(
            book_title=en_title,
            author=en_author,
            lang="en",
            background_image_path=background_image,
            use_author_image=args.use_author_image,
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
            # book_title이 영어인지 한글인지 판단
            if is_english_title(args.book_title):
                book_title = args.book_title
            else:
                book_title = translate_book_title(args.book_title)
            # 영어 작가 이름도 변환
            if author:
                if is_english_title(author):
                    author = author
                else:
                    author = translate_author_name(author)
        
        path = generator.generate_thumbnail(
            book_title=book_title,
            author=author,
            lang=args.lang,
            background_image_path=background_image,
            use_author_image=args.use_author_image,
            output_path=f"{args.output_dir}/{args.book_title.replace(' ', '_')}_thumbnail_{args.lang}.jpg"
        )
        
        print()
        print(f"✅ 썸네일 생성 완료: {path}")


if __name__ == "__main__":
    main()

