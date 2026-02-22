#!/usr/bin/env python3
"""
YouTube Shorts 자동 생성 스크립트

Summary 파일의 HOOK 섹션 및 핵심 인용구를 기반으로
9:16 세로 포맷(1080x1920) YouTube Shorts 영상을 자동 생성합니다.

생성되는 Shorts 유형:
  Short 1: HOOK 섹션 기반 (요약 첫 30초)
  Short 2: 핵심 인용구 + 무드 이미지
  Short 3: 한 줄 요약 + 배경 이미지

사용법:
  python src/26_generate_shorts.py --book-title "책 제목" --language ko
  python src/26_generate_shorts.py --book-title "Book Title" --language en --author "Author Name"
"""

import argparse
import os
import re
import sys
import random
from pathlib import Path
from typing import Optional, List, Tuple

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from src.utils.logger import get_logger
except ImportError:
    from utils.logger import get_logger

try:
    from src.utils.file_utils import get_standard_safe_title
except ImportError:
    from utils.file_utils import get_standard_safe_title

try:
    from src.utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        translate_author_name,
        translate_author_name_to_korean,
        is_english_title,
    )
except ImportError:
    from utils.translations import (
        translate_book_title,
        translate_book_title_to_korean,
        translate_author_name,
        translate_author_name_to_korean,
        is_english_title,
    )

SHORTS_RESOLUTION = (1080, 1920)  # 9:16 세로 포맷
SHORTS_FPS = 30
SHORTS_MAX_DURATION = 59  # YouTube Shorts 최대 59초


def _parse_hook_section(summary_text: str) -> str:
    """Summary 파일에서 [HOOK] 섹션 추출"""
    hook_match = re.search(r'\[HOOK\]\s*(.*?)(?=\[SUMMARY\]|\[BRIDGE\]|\Z)', summary_text, re.DOTALL)
    if hook_match:
        return hook_match.group(1).strip()
    # HOOK 태그 없으면 처음 300자
    return summary_text[:300].strip()


def _parse_summary_section(summary_text: str) -> str:
    """Summary 파일에서 [SUMMARY] 섹션 추출"""
    summary_match = re.search(r'\[SUMMARY\]\s*(.*?)(?=\[BRIDGE\]|\Z)', summary_text, re.DOTALL)
    if summary_match:
        return summary_match.group(1).strip()
    return summary_text.strip()


def _extract_key_quotes(summary_text: str, language: str = "ko", count: int = 3) -> List[str]:
    """Summary 본문에서 핵심 인용구 추출 (문장 단위)"""
    body = _parse_summary_section(summary_text)
    # 문장 분리
    if language == "ko":
        sentences = re.split(r'(?<=[다습니었])\.?\s+', body)
    else:
        sentences = re.split(r'(?<=[.!?])\s+', body)

    # 30~100자 범위 문장 필터링
    candidates = [s.strip() for s in sentences if 30 <= len(s.strip()) <= 150]

    if len(candidates) <= count:
        return candidates

    # 균등 분포로 선택 (첫/중간/끝)
    step = len(candidates) // count
    selected = [candidates[i * step] for i in range(count)]
    return selected


def _find_summary_file(book_title: str, language: str) -> Optional[Path]:
    """Summary MD 파일 경로 탐색"""
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "ko" if language == "ko" else "en"
    candidates = [
        Path(f"assets/summaries/{safe_title}_summary_{lang_suffix}.md"),
        Path(f"assets/summaries/{safe_title}_summary_{language}.md"),
        Path(f"output/{safe_title}_summary_{lang_suffix}.md"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _find_mood_images(book_title: str, count: int = 5) -> List[Path]:
    """무드 이미지 경로 탐색"""
    safe_title = get_standard_safe_title(book_title)
    image_dir = Path(f"assets/images/{safe_title}")
    if not image_dir.exists():
        return []
    images = sorted(image_dir.glob("mood_*.jpg"))
    if not images:
        images = sorted(image_dir.glob("*.jpg"))
    if len(images) > count:
        images = random.sample(images, count)
    return images[:count]


def _generate_short_tts(text: str, language: str, output_path: Path, provider: str = "openai") -> bool:
    """Shorts용 TTS 오디오 생성"""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "text_to_speech_multi",
            Path(__file__).parent / "09_text_to_speech_multi.py"
        )
        tts_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tts_module)
        engine = tts_module.MultiTTSEngine(provider=provider)

        voice = "nova" if language == "ko" else "alloy"
        result = engine.text_to_speech(
            text=text,
            output_path=str(output_path),
            language=language,
            voice=voice
        )
        return bool(result)
    except Exception as e:
        print(f"  ⚠️ TTS 생성 실패: {e}")
        return False


def _create_short_video(
    images: List[Path],
    audio_path: Optional[Path],
    output_path: Path,
    text_overlay: Optional[str],
    language: str,
    duration: float = SHORTS_MAX_DURATION,
    cta_text: Optional[str] = None,
) -> bool:
    """Shorts 영상 생성 (9:16 포맷)"""
    try:
        from moviepy.editor import (
            ImageClip, AudioFileClip, CompositeVideoClip,
            concatenate_videoclips, TextClip, ColorClip
        )
        import numpy as np
        from PIL import Image as PILImage

        target_w, target_h = SHORTS_RESOLUTION

        # 오디오 로드 및 실제 재생 길이 결정
        audio_clip = None
        actual_duration = duration
        if audio_path and audio_path.exists():
            audio_clip = AudioFileClip(str(audio_path))
            actual_duration = min(audio_clip.duration, SHORTS_MAX_DURATION)

        # 이미지 슬라이드쇼 생성
        if not images:
            # 이미지 없으면 검은 배경
            bg = ColorClip(size=(target_w, target_h), color=(20, 20, 20), duration=actual_duration)
            video = bg
        else:
            per_img = actual_duration / len(images)
            clips = []
            for img_path in images:
                img = PILImage.open(img_path).convert("RGB")
                # 9:16 크롭: 중앙 크롭
                iw, ih = img.size
                aspect = target_w / target_h
                img_aspect = iw / ih
                if img_aspect > aspect:
                    # 이미지가 더 넓음 → 좌우 크롭
                    new_w = int(ih * aspect)
                    left = (iw - new_w) // 2
                    img = img.crop((left, 0, left + new_w, ih))
                else:
                    # 이미지가 더 좁음 → 상하 크롭
                    new_h = int(iw / aspect)
                    top = (ih - new_h) // 2
                    img = img.crop((0, top, iw, top + new_h))
                img = img.resize((target_w, target_h), PILImage.Resampling.LANCZOS)
                clip = ImageClip(np.array(img), duration=per_img)
                clips.append(clip)
            video = concatenate_videoclips(clips, method="compose")

        # 텍스트 오버레이 추가
        composite_clips = [video]
        if text_overlay:
            try:
                font = "NanumGothic" if language == "ko" else "Arial"
                # 상단 제목 배너
                txt_clip = (
                    TextClip(
                        text_overlay,
                        fontsize=52,
                        color="white",
                        font=font,
                        method="caption",
                        size=(target_w - 80, None),
                        align="center",
                    )
                    .with_position(("center", 120))
                    .with_duration(actual_duration)
                )
                composite_clips.append(txt_clip)
            except Exception as e:
                print(f"  ⚠️ 텍스트 오버레이 생성 실패: {e}")

        # CTA 오버레이 (마지막 10초 동안 하단 표시)
        cta_duration = min(10.0, actual_duration * 0.25)  # 최대 10초 또는 전체의 25%
        cta_start = max(0.0, actual_duration - cta_duration)
        if cta_text and actual_duration > 5:
            try:
                font_cta = "NanumGothic" if language == "ko" else "Arial"
                # 반투명 검은 배경 + CTA 텍스트
                cta_bg = (
                    ColorClip(size=(target_w, 120), color=(0, 0, 0))
                    .with_opacity(0.6)
                    .with_start(cta_start)
                    .with_duration(cta_duration)
                    .with_position(("center", target_h - 200))
                )
                cta_clip = (
                    TextClip(
                        cta_text,
                        fontsize=44,
                        color="white",
                        font=font_cta,
                        method="caption",
                        size=(target_w - 80, None),
                        align="center",
                    )
                    .with_start(cta_start)
                    .with_duration(cta_duration)
                    .with_position(("center", target_h - 190))
                )
                composite_clips.extend([cta_bg, cta_clip])
            except Exception as e:
                print(f"  ⚠️ CTA 오버레이 생성 실패: {e}")

        # Shorts 워터마크 (#Shorts 해시태그)
        try:
            hashtag_clip = (
                TextClip(
                    "#Shorts",
                    fontsize=40,
                    color="rgba(255,255,255,180)",
                    font="Arial",
                )
                .with_position(("center", target_h - 160))
                .with_duration(actual_duration)
            )
            composite_clips.append(hashtag_clip)
        except Exception:
            pass

        final = CompositeVideoClip(composite_clips, size=(target_w, target_h))

        if audio_clip:
            final = final.with_audio(audio_clip.subclip(0, actual_duration))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final.write_videofile(
            str(output_path),
            fps=SHORTS_FPS,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            logger=None,
        )
        print(f"  ✅ Shorts 생성 완료: {output_path.name} ({actual_duration:.1f}초)")
        return True

    except Exception as e:
        print(f"  ❌ Shorts 영상 생성 실패: {e}")
        return False


def generate_shorts(
    book_title: str,
    language: str = "ko",
    author: Optional[str] = None,
    tts_provider: str = "openai",
    output_dir: Optional[str] = None,
) -> List[Path]:
    """
    책 1권에서 YouTube Shorts 3개 자동 생성

    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        author: 저자 이름 (선택)
        tts_provider: TTS 제공자 ('openai' 또는 'google')
        output_dir: 출력 디렉토리 (기본: output/shorts/)

    Returns:
        생성된 Shorts 파일 경로 리스트
    """
    logger = get_logger(__name__)
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "ko" if language == "ko" else "en"

    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path(f"output/shorts/{safe_title}")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 한글/영문 제목 결정
    if is_english_title(book_title):
        en_title = book_title
        ko_title = translate_book_title_to_korean(book_title) or book_title
    else:
        ko_title = book_title
        en_title = translate_book_title(book_title) or book_title

    display_title = ko_title if language == "ko" else en_title

    logger.info(f"📱 YouTube Shorts 생성 시작: {display_title} ({language})")

    # Summary 파일 로드
    summary_path = _find_summary_file(book_title, language)
    if not summary_path:
        logger.warning(f"⚠️ Summary 파일을 찾을 수 없습니다. HOOK/인용구 없이 진행합니다.")
        summary_text = ""
    else:
        logger.info(f"  📄 Summary 파일: {summary_path}")
        summary_text = summary_path.read_text(encoding="utf-8")
        # HTML 주석 제거
        summary_text = re.sub(r'<!--.*?-->', '', summary_text, flags=re.DOTALL).strip()

    # 무드 이미지 로드
    mood_images = _find_mood_images(book_title, count=9)
    if not mood_images:
        logger.warning("⚠️ 무드 이미지를 찾을 수 없습니다.")

    # CTA 텍스트 (모든 Shorts 하단에 마지막 10초간 표시)
    cta = "전체 리뷰는 채널에서 ↑" if language == "ko" else "Full Review on the Channel ↑"

    generated = []

    # ─── Short 1: HOOK 섹션 ───────────────────────────────────────
    logger.info("🎬 Short 1: HOOK 섹션 기반 Shorts 생성")
    hook_text = _parse_hook_section(summary_text) if summary_text else ""
    if not hook_text:
        if language == "ko":
            hook_text = f"{display_title}의 핵심을 지금 확인하세요!"
        else:
            hook_text = f"Discover the key insights of {display_title}!"

    short1_audio = out_dir / f"short1_hook_{lang_suffix}.mp3"
    short1_video = out_dir / f"short1_hook_{lang_suffix}.mp4"

    logger.info(f"  🎤 Hook TTS 생성 중...")
    has_audio = _generate_short_tts(hook_text, language, short1_audio, tts_provider)

    images_for_s1 = mood_images[:3] if mood_images else []
    success = _create_short_video(
        images=images_for_s1,
        audio_path=short1_audio if has_audio else None,
        output_path=short1_video,
        text_overlay=display_title,
        language=language,
        duration=30.0,
        cta_text=cta,
    )
    if success:
        generated.append(short1_video)

    # ─── Short 2: 핵심 인용구 ─────────────────────────────────────
    logger.info("🎬 Short 2: 핵심 인용구 Shorts 생성")
    quotes = _extract_key_quotes(summary_text, language, count=3) if summary_text else []
    if not quotes:
        if language == "ko":
            quotes = [f"{display_title}에서 배운 가장 중요한 교훈"]
        else:
            quotes = [f"The most important lesson from {display_title}"]

    quote_text = "\n\n".join(f'"{q}"' for q in quotes[:2])

    short2_audio = out_dir / f"short2_quotes_{lang_suffix}.mp3"
    short2_video = out_dir / f"short2_quotes_{lang_suffix}.mp4"

    logger.info(f"  🎤 인용구 TTS 생성 중...")
    has_audio2 = _generate_short_tts(quote_text, language, short2_audio, tts_provider)

    images_for_s2 = mood_images[3:6] if len(mood_images) > 3 else mood_images[:3]
    success2 = _create_short_video(
        images=images_for_s2,
        audio_path=short2_audio if has_audio2 else None,
        output_path=short2_video,
        text_overlay=f'"{display_title}"',
        language=language,
        duration=45.0,
        cta_text=cta,
    )
    if success2:
        generated.append(short2_video)

    # ─── Short 3: 한 줄 요약 ──────────────────────────────────────
    logger.info("🎬 Short 3: 한 줄 요약 Shorts 생성")
    if language == "ko":
        oneliner = f"📚 {display_title}을(를) 한 문장으로 정리하면: 이 책은 우리 삶의 본질적인 질문에 답합니다."
    else:
        oneliner = f"📚 {display_title} in one sentence: This book answers the most essential questions of our lives."

    short3_audio = out_dir / f"short3_oneliner_{lang_suffix}.mp3"
    short3_video = out_dir / f"short3_oneliner_{lang_suffix}.mp4"

    logger.info(f"  🎤 한 줄 요약 TTS 생성 중...")
    has_audio3 = _generate_short_tts(oneliner, language, short3_audio, tts_provider)

    images_for_s3 = mood_images[6:9] if len(mood_images) > 6 else mood_images[:3]
    success3 = _create_short_video(
        images=images_for_s3,
        audio_path=short3_audio if has_audio3 else None,
        output_path=short3_video,
        text_overlay=display_title,
        language=language,
        duration=20.0,
        cta_text=cta,
    )
    if success3:
        generated.append(short3_video)

    # ─── 결과 요약 ────────────────────────────────────────────────
    logger.info(f"\n✅ Shorts 생성 완료: {len(generated)}/3개")
    for p in generated:
        logger.info(f"  📱 {p}")

    return generated


def _generate_shorts_hook_ko(ko_title: str, author: Optional[str] = None, book_info: Optional[dict] = None) -> str:
    """한글 Shorts용 훅 카피 생성 (책별 맞춤, 궁금증 유발)"""
    # 장르 감지
    genre = "general"
    if book_info:
        cats = book_info.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        desc = (book_info.get("description") or "").lower()
        text = (" ".join(cats) + " " + desc).lower()
        if any(k in text for k in ["philosophy", "철학"]):
            genre = "philosophy"
        elif any(k in text for k in ["psychology", "self-help", "자기계발", "심리"]):
            genre = "psychology"
        elif any(k in text for k in ["business", "economics", "경제", "경영"]):
            genre = "business"
        elif any(k in text for k in ["history", "역사"]):
            genre = "history"
        elif any(k in text for k in ["fiction", "novel", "소설"]):
            genre = "fiction"

    # 조사 처리: 받침 없으면 "가", 있으면 "이"
    def _i_ga(word: str) -> str:
        if not word:
            return "이"
        last = word[-1]
        code = ord(last) - 0xAC00
        if 0 <= code < 11172 and code % 28 == 0:
            return "가"
        return "이"

    hooks = {
        "philosophy": f"{ko_title}이 알려준 삶의 진실",
        "psychology": f"{ko_title}으로 본 인간의 심리",
        "business":   f"{ko_title}의 핵심 전략 한 가지",
        "history":    f"{ko_title}에서 발견한 역사의 교훈",
        "fiction":    f"{ko_title}이 보여준 인간의 민낯",
        "general":    f"{ko_title}에서 가장 충격적인 한 문장",
    }
    hook = hooks.get(genre, hooks["general"])
    if author:
        # 조사 처리 적용, "{저자}이/가 말한 {책제목}의 핵심" 포맷 사용
        particle = _i_ga(author)
        hook = f"{author}{particle} 말한 {ko_title}의 핵심"
    return hook


def _generate_shorts_hook_en(en_title: str, author: Optional[str] = None, book_info: Optional[dict] = None) -> str:
    """영문 Shorts용 훅 카피 생성 (책별 맞춤, 궁금증 유발)"""
    genre = "general"
    if book_info:
        cats = book_info.get("categories") or []
        if isinstance(cats, str):
            cats = [cats]
        desc = (book_info.get("description") or "").lower()
        text = (" ".join(cats) + " " + desc).lower()
        if any(k in text for k in ["philosophy", "철학"]):
            genre = "philosophy"
        elif any(k in text for k in ["psychology", "self-help"]):
            genre = "psychology"
        elif any(k in text for k in ["business", "economics"]):
            genre = "business"
        elif any(k in text for k in ["history"]):
            genre = "history"
        elif any(k in text for k in ["fiction", "novel"]):
            genre = "fiction"

    hooks = {
        "philosophy": f"The Truth {en_title} Reveals About Life",
        "psychology": f"What {en_title} Tells Us About Human Nature",
        "business":   f"One Strategy That Makes {en_title} a Must-Read",
        "history":    f"The History Lesson Hidden in {en_title}",
        "fiction":    f"The Human Truth {en_title} Exposes",
        "general":    f"The Most Shocking Line in {en_title}",
    }
    hook = hooks.get(genre, hooks["general"])
    if author:
        hook = f"What {author} Really Wanted Us to Know"
    return hook


def generate_shorts_metadata(
    book_title: str,
    language: str = "ko",
    author: Optional[str] = None,
    output_dir: Optional[str] = None,
    book_info: Optional[dict] = None,
) -> List[dict]:
    """
    Shorts 메타데이터(제목/설명/태그) 생성

    Args:
        book_title: 책 제목
        language: 'ko' 또는 'en'
        author: 저자 이름 (선택)
        output_dir: 출력 디렉토리 (선택)
        book_info: Google Books 정보 딕셔너리 (선택, 장르 감지에 사용)

    Returns:
        Shorts별 메타데이터 딕셔너리 리스트
    """
    if is_english_title(book_title):
        en_title = book_title
        ko_title = translate_book_title_to_korean(book_title) or book_title
    else:
        ko_title = book_title
        en_title = translate_book_title(book_title) or book_title

    display_title = ko_title if language == "ko" else en_title  # noqa: F841

    try:
        from src.utils.title_generator import generate_hashtags
        hashtags = generate_hashtags(language, book_title, author=author, content_type="summary_video")
    except Exception:
        hashtags = "#Shorts #책리뷰 #BookReview" if language == "ko" else "#Shorts #BookReview #BookSummary"

    # 조사 처리: "을" vs "를"
    def _eul_reul(word: str) -> str:
        if not word:
            return "을"
        last = word[-1]
        code = ord(last) - 0xAC00
        if 0 <= code < 11172 and code % 28 != 0:
            return "을"
        return "를"

    metadatas = []
    if language == "ko":
        hook_copy = _generate_shorts_hook_ko(ko_title, author, book_info)
        eul = _eul_reul(ko_title)
        metadatas = [
            {
                "type": "hook",
                "title": f"{hook_copy} #Shorts",
                "description": f"📚 {ko_title} 핵심 포인트\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "책리뷰", "독서", ko_title, "북튜브", "책추천"],
            },
            {
                "type": "quotes",
                "title": f"{ko_title}의 핵심 명언 #Shorts",
                "description": f"📖 {ko_title} 핵심 인용구\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "명언", "독서", ko_title, "인생명언", "책추천"],
            },
            {
                "type": "oneliner",
                "title": f"{ko_title}{eul} 한 문장으로 #Shorts",
                "description": f"📚 {ko_title} 한 줄 요약\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "책요약", "독서", ko_title, "핵심요약", "북리뷰"],
            },
        ]
    else:
        hook_copy = _generate_shorts_hook_en(en_title, author, book_info)
        metadatas = [
            {
                "type": "hook",
                "title": f"{hook_copy} #Shorts",
                "description": f"📚 Key points from {en_title}\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "BookReview", "Reading", en_title, "BookTube", "BookRecommendation"],
            },
            {
                "type": "quotes",
                "title": f"Best Quotes from {en_title} #Shorts",
                "description": f"📖 Key quotes from {en_title}\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "Quotes", "Reading", en_title, "LifeQuotes", "BookRecommendation"],
            },
            {
                "type": "oneliner",
                "title": f"{en_title} in One Sentence #Shorts",
                "description": f"📚 {en_title} one-line summary\n\n{hashtags} #Shorts",
                "tags": ["Shorts", "BookSummary", "Reading", en_title, "CoreSummary", "BookReview"],
            },
        ]

    # 메타데이터 JSON 저장
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "ko" if language == "ko" else "en"
    if output_dir:
        out_dir = Path(output_dir)
    else:
        out_dir = Path(f"output/shorts/{safe_title}")
    out_dir.mkdir(parents=True, exist_ok=True)

    import json
    meta_path = out_dir / f"shorts_metadata_{lang_suffix}.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)
    print(f"  📋 메타데이터 저장: {meta_path}")

    return metadatas


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts 자동 생성 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--book-title", required=True, help="책 제목")
    parser.add_argument("--author", help="저자 이름 (선택)")
    parser.add_argument("--language", default="ko", choices=["ko", "en"], help="언어 (기본값: ko)")
    parser.add_argument("--tts-provider", default="openai", choices=["openai", "google"], help="TTS 제공자")
    parser.add_argument("--output-dir", help="출력 디렉토리 (기본: output/shorts/{book_title}/)")
    parser.add_argument("--metadata-only", action="store_true", help="영상 생성 없이 메타데이터만 생성")
    parser.add_argument("--both-languages", action="store_true", help="한글+영문 모두 생성")

    args = parser.parse_args()

    if args.both_languages:
        for lang in ["ko", "en"]:
            print(f"\n{'='*60}")
            print(f"🌏 언어: {lang}")
            print(f"{'='*60}")
            if not args.metadata_only:
                generate_shorts(
                    book_title=args.book_title,
                    language=lang,
                    author=args.author,
                    tts_provider=args.tts_provider,
                    output_dir=args.output_dir,
                )
            generate_shorts_metadata(
                book_title=args.book_title,
                language=lang,
                author=args.author,
                output_dir=args.output_dir,
            )
    else:
        if not args.metadata_only:
            generate_shorts(
                book_title=args.book_title,
                language=args.language,
                author=args.author,
                tts_provider=args.tts_provider,
                output_dir=args.output_dir,
            )
        generate_shorts_metadata(
            book_title=args.book_title,
            language=args.language,
            author=args.author,
            output_dir=args.output_dir,
        )


if __name__ == "__main__":
    main()
