# BookReview-AutoMaker

NotebookLM 기반 책 리뷰 영상 자동 생성기

## 프로젝트 개요

이 프로젝트는 NotebookLM을 활용하여 책 리뷰 영상을 자동으로 생성하는 파이프라인입니다.
사용자가 NotebookLM에서 생성한 오디오 파일(및 선택적으로 비디오 파일)을 업로드하면, AI가 자동으로 요약을 생성하고 이미지를 합성하여 유튜브 영상을 제작합니다.

**생성되는 영상 구조:**
- Summary (요약 오디오 + 이미지 슬라이드쇼)
- 3초 silence (검은 화면)
- NotebookLM Video (선택사항, 있으면 자동 포함)
- 3초 silence (검은 화면)
- Audio (리뷰 오디오 + 이미지 슬라이드쇼)

## 전체 워크플로우 (6단계)

1.  **NotebookLM 오디오/비디오 준비**: 
   - 리뷰 오디오 파일을 `assets/audio/{책제목}_review_{언어}.{확장자}` 형식으로 저장
   - NotebookLM 비디오(선택사항)를 `assets/video/{책제목}_notebooklm_{언어}.{확장자}` 형식으로 저장
2.  **관련 이미지 확보**: 책 제목과 관련된 고품질 무드 이미지를 **100개** 자동으로 수집합니다. (`assets/images/{책제목}/` 폴더)
3.  **Summary 오디오 생성**: 5분 분량의 책 요약(한글/영문)을 생성하고 TTS로 MP3 변환합니다. 생성된 Summary 오디오는 `assets/audio/{책제목}_summary_{언어}.mp3` 형식으로 저장됩니다.
4.  **영상 합성**: Summary 오디오 + 3초 silence + NotebookLM Video (선택사항) + 3초 silence + 리뷰 오디오 순서로 영상을 생성합니다. 생성된 영상은 `output/{책제목}_review_with_summary_{언어}.mp4` 형식으로 저장됩니다.
5.  **배포 준비**: 썸네일과 메타데이터를 생성합니다. 썸네일은 자동으로 찾아서 메타데이터에 포함됩니다.
6.  **유튜브 업로드**: 메타데이터 파일을 기반으로 유튜브에 자동 업로드합니다.

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd booksummary
```

### 2. 가상환경 설정

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 API 키를 설정하세요.

**필수 API 키:**
- `GOOGLE_BOOKS_API_KEY`: 책 표지 이미지 다운로드용
- `PEXELS_API_KEY`: 무드 이미지 다운로드용 (1순위)
- `PIXABAY_API_KEY`: 무드 이미지 다운로드용 (2순위, 선택사항)
- `UNSPLASH_ACCESS_KEY`: 무드 이미지 다운로드용 (3순위, 선택사항)
- `OPENAI_API_KEY`: Summary 생성 및 TTS용
- `CLAUDE_API_KEY`: Summary 생성용 (선택사항)
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`: YouTube 업로드용

## 사용 방법

### 방법 1: Downloads 폴더에서 자동 준비 (권장)

**가장 간편한 방법입니다.** `~/Downloads` 폴더에 파일을 준비하고 한 번에 처리합니다.

1. **Downloads 폴더에 파일 준비:**
   - `{prefix}_audio_en.m4a` / `{prefix}_audio_kr.m4a` - 리뷰 오디오
   - `{prefix}_summary_en.md` / `{prefix}_summary_kr.md` - 요약 텍스트 (선택사항)
   - `{prefix}_thumbnail_en.png` / `{prefix}_thumbnail_kr.png` - 썸네일 원본
   - `{prefix}_video_en.mp4` / `{prefix}_video_kr.mp4` - NotebookLM 비디오 (선택사항)

2. **전체 파이프라인 실행:**
   ```bash
   python scripts/run_full_pipeline_from_downloads.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --prefix "파일명접두사" \
     --language both
   ```
   
   예시:
   ```bash
   python scripts/run_full_pipeline_from_downloads.py \
     --book-title "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)" \
     --author "키란 데사이" \
     --prefix "lonliness" \
     --language both
   ```

3. **파일만 준비하고 싶은 경우:**
   ```bash
   python scripts/prepare_files_from_downloads.py \
     --book-title "책 제목" \
     --author "저자 이름" \
     --prefix "파일명접두사"
   ```

### 방법 2: 수동으로 파일 준비

**오디오 파일:**
NotebookLM에서 생성한 리뷰 오디오 파일을 `assets/audio/` 폴더에 위치시킵니다.

**파일명 규칙 (표준 네이밍):**
- 한글 오디오: `{책제목}_review_ko.{확장자}` (예: `Sunrise_on_the_Reaping_review_ko.m4a`)
- 영어 오디오: `{영문제목}_review_en.{확장자}` (예: `Sunrise_on_the_Reaping_review_en.m4a`)
- 지원 확장자: `.m4a`, `.mp3`, `.wav`

**비디오 파일 (선택사항):**
NotebookLM에서 생성한 비디오 파일을 `assets/video/` 폴더에 위치시킵니다.

**파일명 규칙 (표준 네이밍):**
- 한글 비디오: `{책제목}_notebooklm_ko.{확장자}` (예: `Sunrise_on_the_Reaping_notebooklm_ko.mp4`)
- 영어 비디오: `{영문제목}_notebooklm_en.{확장자}` (예: `Sunrise_on_the_Reaping_notebooklm_en.mp4`)
- 지원 확장자: `.mp4`, `.mov`, `.avi`, `.mkv`

**Summary 파일 (선택사항):**
요약 텍스트 파일을 `assets/summaries/` 폴더에 위치시킵니다.
- 한글: `{책제목}_summary_ko.md`
- 영어: `{책제목}_summary_en.md`

**썸네일 파일:**
PNG 파일을 `output/` 폴더에 위치시키고 JPG로 변환합니다.
- 한글: `{책제목}_thumbnail_ko.jpg`
- 영어: `{책제목}_thumbnail_en.jpg`

**참고:** Summary 오디오는 자동으로 생성되며 `{책제목}_summary_{언어}.mp3` 형식으로 저장됩니다.

### 2. 전체 파이프라인 실행
다음 명령어로 2~6단계 과정을 한 번에 실행할 수 있습니다.

```bash
./run_complete_pipeline.sh "책 제목" "저자 이름"
```

예시:
```bash
./run_complete_pipeline.sh "The Boy is Coming" "Han Kang"
```

### 개별 단계 실행 (고급 사용자용)

**이미지 다운로드:**
```bash
./run_images.sh --title "책 제목" --author "저자 이름"
```

**요약 생성 및 영상 제작:**
```bash
python src/10_create_video_with_summary.py \
  --book-title "책 제목" \
  --author "저자 이름" \
  --language ko \
  --summary-duration 5.0 \
  --summary-audio-volume 1.2
```

**메타데이터만 생성 (영상이 이미 있는 경우):**
```bash
python src/08_create_and_preview_videos.py \
  --book-title "책 제목" \
  --metadata-only
```
메타데이터 생성 시 썸네일 경로를 자동으로 찾아서 포함합니다.

**파일 네이밍 규칙 요약:**
- **리뷰 오디오**: `assets/audio/{책제목}_review_{언어}.{확장자}`
- **Summary 오디오**: `assets/audio/{책제목}_summary_{언어}.mp3` (자동 생성)
- **NotebookLM 비디오**: `assets/video/{책제목}_notebooklm_{언어}.{확장자}` (선택사항)
- **생성된 영상**: `output/{책제목}_review_with_summary_{언어}.mp4`
- **썸네일**: `output/{책제목}_thumbnail_{언어}.jpg`
- **메타데이터**: `output/{책제목}_review_with_summary_{언어}.metadata.json`

**영상 구성:**
- **Summary** (이미지 슬라이드쇼 + 요약 오디오, 음량 1.2배 조정)
- **3초 silence** (검은 화면)
- **NotebookLM Video** (선택사항, 있으면 자동 포함)
- **3초 silence** (검은 화면)
- **Audio** (이미지 슬라이드쇼 + 리뷰 오디오)

**Summary 오디오 음량 조정:**
- 기본값: 1.2배 (20% 증가)
- 조정 가능: `--summary-audio-volume 1.5` (50% 증가) 또는 `--summary-audio-volume 1.0` (원본)

**유튜브 업로드:**
```bash
python src/09_upload_from_metadata.py
```

## 프로젝트 구조

```text
booksummary/
├── assets/
│   ├── audio/          # NotebookLM 오디오 및 생성된 요약 오디오
│   ├── images/         # 책 표지 및 무드 이미지
│   ├── video/          # NotebookLM 비디오 파일 (선택사항)
│   └── summaries/      # 생성된 요약 텍스트
├── docs/               # 문서
│   └── SUMMARY_TEMPLATE.md  # 유튜브 롱폼 영상용 요약 템플릿 (Hook → Summary → Bridge)
├── output/             # 생성된 영상 및 썸네일
├── scripts/            # 유틸리티 스크립트
│   ├── prepare_files_from_downloads.py  # Downloads 폴더에서 파일 준비 및 표준 네이밍
│   ├── run_full_pipeline_from_downloads.py  # Downloads 폴더 기반 전체 파이프라인 실행
│   ├── convert_downloads_png.py    # Downloads 폴더 PNG를 JPG 썸네일로 변환
│   ├── convert_png_to_jpg.py       # PNG를 JPG로 변환
│   ├── download_pexels_images.py  # Pexels API 이미지 다운로드 테스트
│   ├── generate_summary_audio.py   # Summary 오디오 생성
│   └── ...
├── src/                # 소스 코드
│   ├── 08_generate_summary.py      # 요약 텍스트 생성 (Hook → Summary → Bridge 구조)
│   ├── 09_text_to_speech.py        # TTS 변환
│   ├── 10_create_video_with_summary.py  # 영상 합성 (요약+리뷰)
│   └── ...
└── README.md           # 이 파일
```

## 요약 템플릿

유튜브 롱폼 영상용 5분 분량 오프닝 서머리는 다음 구조로 생성됩니다:

- **[HOOK]**: 강력한 첫 문장 (3초 만에 시청자 몰입)
- **[SUMMARY]**: 5분 분량 핵심 요약 (주제, 주요 아이디어, 예시/일화)
- **[BRIDGE]**: NotebookLM 상세 분석으로 자연스럽게 연결

자세한 템플릿 가이드는 `docs/SUMMARY_TEMPLATE.md`를 참고하세요.

## 주요 기능

### 고해상도 썸네일 생성
- **4K 해상도 (3840x2160)** 지원으로 고품질 썸네일 생성
- 한국어/영어 폰트 자동 감지 및 최적화
- DALL-E 3를 활용한 AI 배경 이미지 생성 옵션

### 스마트 이미지 키워드 생성
- 책의 summary 파일을 분석하여 주제에 맞는 이미지 키워드 자동 생성
- AI 기반 키워드 추출로 더 정확한 무드 이미지 수집
- 다중 이미지 소스 지원: **Pexels (1순위) → Pixabay (2순위) → Unsplash (3순위)**
- 각 API의 장점을 활용하여 최대 100개의 고품질 무드 이미지 수집

### 유튜브 채널에서 CSV 자동 업데이트
- 유튜브 채널에 업로드된 책 정보를 자동으로 CSV에 반영
- `python src/13_update_csv_from_youtube.py` 실행
- 비디오 제목과 책 제목 자동 매칭 (별칭 지원)

### 깊이 있는 URL 수집
- 유튜브 롱폼 북튜브를 위한 깊이 있는 자료 수집
- YouTube 영상(30분 이상), PDF, 논문, 학술 사이트 검색
- 특정 YouTube 채널 우선순위 검색 (일당백 최우선)
- `python src/14_collect_deep_urls_for_notebooklm.py --csv` 실행

### 스마트 태그 생성
- 책 정보 기반 자동 태그 생성
- 추천 기관 태그 자동 포함:
  - 세계적 미디어: 뉴욕타임즈, 아마존, 타임지, CNN, 뉴스위크
  - 주요 서점: 교보문고, 알라딘, YES24
  - 유명 대학: 서울대학교, 하버드대학교, 도쿄대학교 등
  - 문학상: 노벨문학상, 퓰리처상, 맨부커상 등
- YouTube 태그 제한(500자)을 고려한 우선순위 기반 선택

## 라이선스

MIT License
