#!/usr/bin/env python3
"""
메타데이터의 publish_at 필드를 사용해 YouTube 예약 업로드
"""
import sys
import json
import importlib.util
import argparse
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# YouTubeUploader 동적 로드
spec = importlib.util.spec_from_file_location(
    "upload_mod",
    ROOT / "src" / "09_upload_from_metadata.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
YouTubeUploader = mod.YouTubeUploader

from src.utils.translations import translate_book_title, translate_book_title_to_korean
from src.utils.file_utils import safe_title


def find_thumbnail(video_path: Path, lang: str) -> str | None:
    """영상에 맞는 썸네일 파일 탐색"""
    video_dir = video_path.parent
    stem = video_path.stem  # e.g. Mindset_kr

    # 책 제목 추출 (stem에서 _kr/_en 제거)
    base_stem = stem.replace('_kr', '').replace('_en', '')  # e.g. Mindset, Lessons_in_Chemistry

    lang_suffixes = ['_ko', '_kr'] if lang == 'ko' else ['_en']

    # 1순위: 직접 매칭 (영문 stem 기반)
    candidates = []
    for ls in lang_suffixes:
        candidates.append(video_dir / f"{base_stem}_thumbnail{ls}.jpg")

    for c in candidates:
        if c.exists():
            return str(c)

    # 2순위: KO 영상이면, 한글 제목 파일 탐색
    # translations.py의 ko→en 매핑을 역방향으로 활용
    if lang == 'ko':
        # 모든 *_thumbnail_ko.jpg 파일 중에서 역방향 매칭
        ko_thumbs = list(video_dir.glob("*_thumbnail_ko.jpg")) + list(video_dir.glob("*_thumbnail_kr.jpg"))
        for thumb in ko_thumbs:
            # 파일명에서 제목 추출: 마인드셋_thumbnail_ko.jpg → 마인드셋
            thumb_title_ko = thumb.name.split('_thumbnail_')[0]  # e.g. 마인드셋
            # 이 한글 제목이 현재 base_stem의 영문 제목과 매칭되는지 확인
            en_of_thumb = translate_book_title(thumb_title_ko)  # 마인드셋 → Mindset
            en_normalized = en_of_thumb.replace(' ', '_')  # Lessons in Chemistry → Lessons_in_Chemistry
            if en_normalized == base_stem or en_of_thumb == base_stem.replace('_', ' '):
                return str(thumb)

    return None


def main():
    parser = argparse.ArgumentParser(description="예약 업로드")
    parser.add_argument('metadata_files', nargs='+', help='메타데이터 JSON 파일 경로들')
    parser.add_argument('--channel-id', default='UCxOcO_x_yW6sfg_FPUQVqYA')
    parser.add_argument('--dry-run', action='store_true', help='실제 업로드 없이 확인만')
    args = parser.parse_args()

    uploader = YouTubeUploader()

    for meta_path_str in args.metadata_files:
        meta_path = Path(meta_path_str)
        if not meta_path.exists():
            print(f'❌ 파일 없음: {meta_path}')
            continue

        data = json.loads(meta_path.read_text())
        title = data.get('title', '')
        publish_at = data.get('publish_at')
        video_path_str = data.get('video_path') or str(meta_path).replace('.metadata.json', '.mp4')
        video_path = ROOT / video_path_str if not Path(video_path_str).is_absolute() else Path(video_path_str)
        tags = data.get('tags', [])
        description = data.get('description', '')
        localizations = data.get('localizations')
        lang = data.get('language', 'ko')

        # 썸네일 탐색
        thumbnail_path = find_thumbnail(video_path, lang)

        print(f"\n📤 업로드 예정:")
        print(f"   제목: {title}")
        print(f"   영상: {video_path}")
        print(f"   썸네일: {thumbnail_path}")
        print(f"   예약: {publish_at or '즉시(private)'}")

        if args.dry_run:
            print("   [DRY RUN - 실제 업로드 안 함]")
            continue

        if not video_path.exists():
            print(f"   ❌ 영상 파일 없음: {video_path}")
            continue

        result = uploader.upload_video(
            channel_id=args.channel_id,
            video_path=str(video_path),
            title=title,
            description=description,
            tags=tags,
            privacy_status='private',
            publish_at=publish_at,
            thumbnail_path=thumbnail_path,
            localizations=localizations,
        )

        if result:
            vid_id = result.get('video_id', '')
            print(f"   ✅ 업로드 완료: https://youtu.be/{vid_id}")
        else:
            print(f"   ❌ 업로드 실패")


if __name__ == '__main__':
    main()
