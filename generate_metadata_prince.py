#!/usr/bin/env python3
"""군주론 영상 메타데이터 생성 스크립트"""

import sys
import json
import importlib.util
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 모듈 로드
spec = importlib.util.spec_from_file_location('create_videos', Path('src') / '08_create_and_preview_videos.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

generate_title = module.generate_title
generate_description = module.generate_description
generate_tags = module.generate_tags
save_metadata = module.save_metadata

# 책 정보 로드
book_info_path = Path('assets/images/군주론/book_info.json')
book_info = None
if book_info_path.exists():
    with open(book_info_path, 'r', encoding='utf-8') as f:
        book_info = json.load(f)

# 한글 메타데이터 생성
video_path_ko = Path('output/군주론_review_with_summary_ko.mp4')
thumbnail_path_ko = Path('output/군주론_thumbnail_ko.jpg')

print("📋 한글 메타데이터 생성 중...")
title_ko = generate_title('군주론', lang='ko')
description_ko = generate_description(book_info, lang='ko', book_title='군주론')
tags_ko = generate_tags(book_title='군주론', book_info=book_info, lang='ko')

save_metadata(
    video_path_ko,
    title_ko,
    description_ko,
    tags_ko,
    'ko',
    book_info,
    str(thumbnail_path_ko) if thumbnail_path_ko.exists() else None
)

# 영문 메타데이터 생성
video_path_en = Path('output/군주론_review_with_summary_en.mp4')
thumbnail_path_en = Path('output/군주론_thumbnail_en.jpg')

print("📋 영문 메타데이터 생성 중...")
title_en = generate_title('군주론', lang='en')
description_en = generate_description(book_info, lang='en', book_title='군주론')
tags_en = generate_tags(book_title='군주론', book_info=book_info, lang='en')

save_metadata(
    video_path_en,
    title_en,
    description_en,
    tags_en,
    'en',
    book_info,
    str(thumbnail_path_en) if thumbnail_path_en.exists() else None
)

print('✅ 메타데이터 생성 완료!')
