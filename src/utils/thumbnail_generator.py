"""
Flux 기반 썸네일 자동 생성 유틸리티
GPU 서버(192.168.0.151:9001)의 Flux API 호출
텍스트 오버레이는 PIL로 처리 (Flux는 한글 렌더링 불가)
프롬프트/훅 생성은 외부(Claude Code)에서 받아서 처리

Usage:
    from src.utils.thumbnail_generator import generate_thumbnail

    output_path = generate_thumbnail(
        book_title="죽음의 수용소에서",
        author="빅터 프랭클",
        language="ko",
        hook="극한의 고통 속에서 의미를 찾다",
        image_prompt="A lone man in a dark concentration camp...",
        output_dir="output/",
    )

CLI:
    python src/utils/thumbnail_generator.py \\
        --title-ko "죽음의 수용소에서" --title-en "Man's Search for Meaning" \\
        --author-ko "빅터 프랭클" --author-en "Viktor Frankl" \\
        --hook-ko "극한의 고통 속에서 의미를 찾다" \\
        --hook-en "Find meaning in suffering" \\
        --image-prompt-ko "A lone prisoner silhouette..." \\
        --image-prompt-en "A lone prisoner silhouette..."
"""

import base64
import os
import re
import sys
import time
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont
import io

FLUX_SERVER = os.getenv("FLUX_SERVER_URL", "http://192.168.0.151:9001")
FLUX_TIMEOUT = int(os.getenv("FLUX_TIMEOUT", "120"))

# 폰트 경로 (우선순위 순)
FONT_PATHS_BOLD = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_PATHS_REGULAR = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(paths: list[str], size: int) -> ImageFont.FreeTypeFont:
    for p in paths:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _build_flux_prompt(image_prompt: str) -> str:
    """Flux용 최종 프롬프트: 순수 배경 이미지 (텍스트 없음)"""
    return (
        f"{image_prompt} "
        "YouTube thumbnail, 16:9 widescreen. "
        "Left side darker for text overlay area. "
        "Blue geometric accent lines on frame edges (#1A73E8). "
        "Cinematic lighting. Soft watercolor + fine ink pen style. "
        "NO text, NO letters, NO watermark, NOT photorealistic."
    )


def overlay_text(
    img: Image.Image,
    hook: str,
    author: str,
    book_title: str,
    language: str,
) -> Image.Image:
    """PIL로 이미지 위에 텍스트 오버레이"""
    W, H = img.size
    is_ko = language in ("ko", "kr")

    font_hook = _load_font(FONT_PATHS_BOLD, int(H * 0.088))
    font_author = _load_font(FONT_PATHS_BOLD, int(H * 0.050))
    font_title = _load_font(FONT_PATHS_REGULAR, int(H * 0.038))
    font_tag = _load_font(FONT_PATHS_BOLD, int(H * 0.030))

    # 좌측 그라데이션 어두운 오버레이
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    # 좌측 60%를 점진적으로 어둡게
    for x in range(int(W * 0.60)):
        alpha = int(170 * (1 - x / (W * 0.60)))
        ov_draw.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 파란 강조선
    accent = "#1A73E8"
    draw.rectangle([(0, 0), (W, int(H * 0.007))], fill=accent)
    draw.rectangle([(0, H - int(H * 0.007)), (W, H)], fill=accent)
    draw.rectangle([(0, 0), (int(W * 0.005), H)], fill=accent)

    pad_x = int(W * 0.045)
    pad_y = int(H * 0.07)

    def draw_text_shadow(pos, text, font, fill, shadow_offset=3):
        x, y = pos
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill="#000000AA")
        draw.text((x, y), text, font=font, fill=fill)

    # 저자명
    draw_text_shadow((pad_x, pad_y), author, font_author, "#FFD700")

    # 책 제목
    title_y = pad_y + int(H * 0.068)
    draw_text_shadow((pad_x, title_y), book_title, font_title, "#DDDDDD")

    # 구분선
    sep_y = title_y + int(H * 0.058)
    draw.rectangle([(pad_x, sep_y), (pad_x + int(W * 0.12), sep_y + 3)], fill=accent)

    # 훅 문장 (메인 카피)
    max_chars = 10 if is_ko else 16
    lines = textwrap.wrap(hook, width=max_chars)
    hook_y = int(H * 0.42)
    line_h = int(H * 0.108)

    for line in lines[:3]:
        draw_text_shadow((pad_x, hook_y), line, font_hook, "#FFFFFF", shadow_offset=4)
        hook_y += line_h

    # 채널 태그
    tag = "[일당백]" if is_ko else "[1DANG100]"
    draw_text_shadow((pad_x, H - int(H * 0.072)), tag, font_tag, accent)

    return img


def check_server_health() -> bool:
    try:
        resp = requests.get(f"{FLUX_SERVER}/health", timeout=5)
        return resp.json().get("status") == "ok"
    except Exception:
        return False


def generate_thumbnail(
    book_title: str,
    author: str,
    language: str,
    hook: str,
    image_prompt: str,
    output_dir: str | Path = "output",
    width: int = 1920,
    height: int = 1080,
    steps: int = 4,
    seed: int = -1,
    force: bool = False,
) -> Path | None:
    """
    썸네일 생성 메인 함수

    Args:
        hook: 썸네일 메인 카피 (짧고 강렬하게, Claude Code가 생성)
        image_prompt: 배경 이미지 묘사 (영문, Claude Code가 생성)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_title = re.sub(r'[^\w가-힣]', '_', book_title).strip('_')
    lang_suffix = "ko" if language in ("ko", "kr") else "en"
    output_path = output_dir / f"{safe_title}_thumbnail_{lang_suffix}.jpg"

    if output_path.exists() and not force:
        print(f"썸네일 이미 존재: {output_path}")
        return output_path

    print(f"Flux 서버 확인 중 ({FLUX_SERVER})...")
    if not check_server_health():
        print(f"❌ Flux 서버 연결 불가: {FLUX_SERVER}", file=sys.stderr)
        return None

    flux_prompt = _build_flux_prompt(image_prompt)
    print(f"🎨 배경 이미지 생성 중... (hook: {hook})")

    start = time.time()
    try:
        resp = requests.post(
            f"{FLUX_SERVER}/generate",
            json={"prompt": flux_prompt, "width": width, "height": height,
                  "steps": steps, "seed": seed},
            timeout=FLUX_TIMEOUT,
        )
        resp.raise_for_status()
        result = resp.json()
    except requests.Timeout:
        print(f"❌ 타임아웃 ({FLUX_TIMEOUT}초)", file=sys.stderr)
        return None
    except Exception as e:
        print(f"❌ 생성 실패: {e}", file=sys.stderr)
        return None

    img_b64 = result.get("image_base64", "")
    if not img_b64:
        print("❌ 응답에 이미지 없음", file=sys.stderr)
        return None

    img = Image.open(io.BytesIO(base64.b64decode(img_b64)))
    img = overlay_text(img, hook=hook, author=author,
                       book_title=book_title, language=language)
    img.save(output_path, format="JPEG", quality=95)

    elapsed = time.time() - start
    print(f"✅ 썸네일 저장: {output_path} ({elapsed:.1f}s, seed={result.get('seed', -1)})")
    return output_path


def generate_both_languages(
    book_title_ko: str,
    book_title_en: str,
    author_ko: str,
    author_en: str,
    hook_ko: str,
    hook_en: str,
    image_prompt_ko: str,
    image_prompt_en: str,
    output_dir: str | Path = "output",
    force: bool = False,
) -> dict[str, Path | None]:
    results = {}
    print("\n=== 한국어 썸네일 생성 ===")
    results["ko"] = generate_thumbnail(
        book_title=book_title_ko, author=author_ko, language="ko",
        hook=hook_ko, image_prompt=image_prompt_ko,
        output_dir=output_dir, force=force,
    )
    print("\n=== 영문 썸네일 생성 ===")
    results["en"] = generate_thumbnail(
        book_title=book_title_en, author=author_en, language="en",
        hook=hook_en, image_prompt=image_prompt_en,
        output_dir=output_dir, force=force,
    )
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Flux 썸네일 생성기")
    parser.add_argument("--title-ko", required=True)
    parser.add_argument("--title-en", required=True)
    parser.add_argument("--author-ko", default="")
    parser.add_argument("--author-en", default="")
    parser.add_argument("--hook-ko", required=True, help="한국어 훅 문장 (짧고 강렬하게)")
    parser.add_argument("--hook-en", required=True, help="영문 훅 문장")
    parser.add_argument("--image-prompt-ko", required=True, help="한국어판 배경 이미지 묘사 (영문)")
    parser.add_argument("--image-prompt-en", required=True, help="영문판 배경 이미지 묘사 (영문)")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--language", choices=["ko", "en", "both"], default="both")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.language == "both":
        results = generate_both_languages(
            args.title_ko, args.title_en,
            args.author_ko, args.author_en,
            args.hook_ko, args.hook_en,
            args.image_prompt_ko, args.image_prompt_en,
            args.output_dir, force=args.force,
        )
        for lang, path in results.items():
            print(f"{lang}: {path}")
    else:
        title = args.title_ko if args.language == "ko" else args.title_en
        author = args.author_ko if args.language == "ko" else args.author_en
        hook = args.hook_ko if args.language == "ko" else args.hook_en
        img_prompt = args.image_prompt_ko if args.language == "ko" else args.image_prompt_en
        path = generate_thumbnail(title, author, args.language, hook, img_prompt,
                                  args.output_dir, force=args.force)
        print(f"결과: {path}")
