#!/usr/bin/env python3
"""
썸네일 프롬프트 txt 파일들을 읽어 Gemini Imagen 3로 일괄 이미지 생성
사용법: python scripts/generate_thumbnails.py [--output-dir output/thumbnails]
"""

import os
import glob
import argparse
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def generate_thumbnails(prompt_dir: str = "output", output_dir: str = "output/thumbnails"):
    """프롬프트 txt 파일들을 읽어 이미지 생성"""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY가 .env에 없습니다")
        return

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("❌ google-genai 패키지 설치 필요: pip install google-genai")
        return

    client = genai.Client(api_key=api_key)

    os.makedirs(output_dir, exist_ok=True)

    prompt_files = sorted(glob.glob(os.path.join(prompt_dir, "*_thumbnail_prompt_*.txt")))

    if not prompt_files:
        print(f"❌ 프롬프트 파일이 없습니다: {prompt_dir}/*_thumbnail_prompt_*.txt")
        return

    print(f"📸 {len(prompt_files)}개 썸네일 생성 시작\n")

    success = 0
    fail = 0

    for i, prompt_file in enumerate(prompt_files, 1):
        filename = Path(prompt_file).stem  # e.g., The_Vegetarian_thumbnail_prompt_ko
        output_path = os.path.join(output_dir, f"{filename}.png")

        if os.path.exists(output_path):
            print(f"[{i}/{len(prompt_files)}] ⏭️ 이미 존재: {output_path}")
            success += 1
            continue

        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read().strip()

        print(f"[{i}/{len(prompt_files)}] 🎨 생성 중: {filename}")

        try:
            response = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="16:9",
                    safety_filter_level="BLOCK_ONLY_HIGH",
                ),
            )

            if response.generated_images:
                image = response.generated_images[0]
                with open(output_path, "wb") as f:
                    f.write(image.image.image_bytes)
                print(f"  ✅ 저장: {output_path}")
                success += 1
            else:
                print(f"  ❌ 이미지 생성 실패 (빈 응답)")
                fail += 1

        except Exception as e:
            print(f"  ❌ 에러: {e}")
            fail += 1

        # rate limit 방지
        if i < len(prompt_files):
            time.sleep(2)

    print(f"\n📊 결과: {success}성공 / {fail}실패 (총 {len(prompt_files)}개)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="썸네일 일괄 생성")
    parser.add_argument("--prompt-dir", default="output", help="프롬프트 파일 디렉토리")
    parser.add_argument("--output-dir", default="output/thumbnails", help="출력 디렉토리")
    args = parser.parse_args()

    generate_thumbnails(args.prompt_dir, args.output_dir)
