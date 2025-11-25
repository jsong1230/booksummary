# BookReview-AutoMaker

NotebookLM 기반 책 리뷰 영상 자동 생성기

## 프로젝트 개요

이 프로젝트는 NotebookLM을 활용하여 책 리뷰 영상을 자동으로 생성하는 파이프라인입니다.

## 주요 기능

### Phase 1: 자료 수집 자동화 ✅

- 책 관련 URL 수집 (위키백과, 온라인 서점, 뉴스 리뷰)
- NotebookLM용 URL 리스트 생성
- Google Books API로 책 표지 다운로드
- Unsplash/Pexels API로 무드 이미지 다운로드

### Phase 2: NotebookLM 오디오 생성 (수동)

- NotebookLM에 URL 입력
- Audio Overview 생성
- 오디오 파일 다운로드

### Phase 3: 이미지 자산 확보 ✅

- AI 기반 키워드 생성: 책 내용/설명을 분석하여 구체적인 검색 키워드 생성
- 무드 이미지 다운로드 (저작권 없는 이미지, 10~20장)
- `assets/images/{책제목}/` 폴더에 저장
- ⚠️ 책 표지 이미지는 저작권 문제로 영상에 사용하지 않습니다

### Phase 4: 영상 합성 및 편집 ✅

- 오디오와 이미지 결합
- 페이드 전환 효과 (fade in/out)
- 이미지 순환 반복 (최대 100개 이미지)
- 자막 생성 (OpenAI Whisper, 선택사항)
- 1080p, 30fps MP4 출력

### Phase 4.5: 요약 및 TTS 생성 ✅

- AI 기반 책 요약 생성 (Claude/OpenAI)
- TTS 음성 생성 (OpenAI TTS)
- 요약 오디오와 리뷰 오디오 자동 연결
- 한글/영문 지원

### Phase 5: 썸네일 생성 ✅

- 자동 썸네일 생성 (책 제목, 작가 정보 포함)
- 한글/영문 버전 지원
- DALL-E 배경 이미지 옵션
- 작가/책 이미지 자동 검색 (Unsplash/Pexels, 저작권 없는 이미지)
- YouTube 권장 크기 (1280x720)
- 영어 폰트 깨짐 문제 해결

### Phase 6: YouTube 업로드 ✅

- 자동 YouTube 업로드
- 한글/영문 제목/설명/태그 지원
- 썸네일 자동 업로드

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

필요한 API 키:

- `GOOGLE_BOOKS_API_KEY`: Google Books API
- `PEXELS_API_KEY`: Pexels API
- `UNSPLASH_ACCESS_KEY`: Unsplash API
- `OPENAI_API_KEY`: OpenAI API (TTS, Whisper 자막, DALL-E 썸네일용)
- `CLAUDE_API_KEY`: Claude API (요약 생성, YouTube 검색 쿼리 생성용)
- `YOUTUBE_API_KEY`: YouTube Data API v3
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`: YouTube 업로드용

## 사용 방법

### 1. 책 목록 수집

```bash
./run_collect_books.sh
```

### 2. URL 수집 (NotebookLM용)

```bash
./run_youtube_search.sh --title "책제목" --author "저자명"
```

또는:

```bash
source venv/bin/activate
python scripts/collect_urls_for_notebooklm.py --title "책제목" --author "저자명" --num 25
```

### 3. 이미지 다운로드

```bash
./run_images.sh --title "책제목" --author "저자명" --keywords "키워드1" "키워드2" --num-mood 10
```

### 4. NotebookLM에서 오디오 생성 (수동)

1. `assets/urls/{책제목}_notebooklm.md` 파일의 URL을 NotebookLM에 복사
2. NotebookLM에서 Audio Overview 생성
3. 오디오 다운로드 후 `assets/audio/` 폴더에 저장

### 5. 영상 제작

**요약 포함 영상 제작 (권장):**

```bash
source venv/bin/activate
python src/10_create_video_with_summary.py \
  --book-title "책제목" \
  --author "저자명" \
  --language ko \
  --summary-duration 5.0
```

**기존 요약 오디오 사용:**

```bash
python src/10_create_video_with_summary.py \
  --book-title "책제목" \
  --author "저자명" \
  --language ko \
  --skip-summary
```

**썸네일 생성:**

```bash
# 기본 (작가/책 이미지 자동 검색)
python src/10_generate_thumbnail.py \
  --book-title "책제목" \
  --author "저자명" \
  --lang both

# 작가/책 이미지 사용 안 함
python src/10_generate_thumbnail.py \
  --book-title "책제목" \
  --author "저자명" \
  --lang both \
  --no-author-image

# DALL-E 배경 이미지 사용
python src/10_generate_thumbnail.py \
  --book-title "책제목" \
  --author "저자명" \
  --lang both \
  --use-dalle
```

### 6. YouTube 업로드

```bash
python src/09_upload_from_metadata.py
```

## 프로젝트 구조

```text
booksummary/
├── assets/
│   ├── audio/          # NotebookLM에서 다운로드한 오디오 파일
│   ├── images/          # 책 표지 및 무드 이미지
│   │   └── {책제목}/
│   │       ├── cover.jpg
│   │       ├── mood_*.jpg
│   │       └── book_info.json
│   └── urls/            # NotebookLM용 URL 리스트
├── data/                # 데이터 파일 (Git에 포함)
│   └── ildangbaek_books.csv  # 책 목록 관리
├── output/              # 생성된 영상 파일 (Git에 포함하지 않음)
├── scripts/             # 유틸리티 스크립트
├── src/                 # 메인 소스 코드
│   ├── 00_collect_books.py
│   ├── 02_get_images.py
│   ├── 03_make_video.py
│   ├── 05_auto_upload.py
│   ├── 06_search_youtube.py
│   ├── 07_make_videos_both_languages.py
│   ├── 08_generate_summary.py      # AI 기반 책 요약 생성
│   ├── 09_text_to_speech.py        # TTS 음성 생성
│   ├── 09_upload_from_metadata.py  # 메타데이터 기반 업로드
│   ├── 10_create_video_with_summary.py  # 요약 포함 영상 제작
│   ├── 10_generate_thumbnail.py    # 썸네일 생성
│   ├── 11_upload_thumbnails.py     # 썸네일 업로드
│   ├── 12_full_pipeline.py          # 전체 파이프라인
│   └── 13_complete_pipeline.py      # 완전 자동화 파이프라인 (권장)
├── .env                 # API 키 (git에 포함하지 않음)
├── .env.example         # 환경 변수 템플릿
├── requirements.txt     # Python 패키지 목록
├── todo                 # 작업 목록
├── history              # 프로젝트 히스토리
└── README.md            # 이 파일
```

## 주요 스크립트

### 자동화 파이프라인 (권장)

- `run_complete_pipeline.sh`: 완전 자동화 파이프라인 (영상 생성 + 메타데이터 + 썸네일)

```bash
./run_complete_pipeline.sh "책 제목" [저자 이름]
```

### 개별 스크립트

- `run_collect_books.sh`: 책 목록 수집
- `run_images.sh`: 이미지 다운로드
- `run_make_video.sh`: 영상 제작
- `run_make_videos_both.sh`: 한글/영문 오디오 각각 영상 제작
- `run_upload.sh`: YouTube 업로드
- `run_youtube_search.sh`: YouTube 영상 검색

## 문서

- `NOTEBOOKLM_GUIDE.md`: NotebookLM 사용 가이드
- `NOTEBOOKLM_PROMPTS.md`: NotebookLM 프롬프트 예시
- `YOUTUBE_SEARCH_GUIDE.md`: YouTube 검색 가이드
- `AFTER_AUDIO_GUIDE.md`: 오디오 생성 후 가이드

## 작업 이어가기

다른 머신이나 IDE에서 작업을 이어가려면:

1. 저장소 클론
2. 가상환경 설정 및 패키지 설치
3. `.env` 파일 설정 (API 키)
4. `todo`, `history`, `README.md` 파일 확인하여 현재 상태 파악

## 라이선스

MIT License