# BookSummary 프로젝트 구조

## 전체 디렉토리 트리

```
booksummary/
├── .claude/                    # Claude Code 설정 (MoAI-ADK)
│   ├── skills/                 # 커스텀 스킬 정의
│   ├── agents/                 # 커스텀 에이전트 정의
│   ├── rules/                  # 프로젝트 규칙
│   └── hooks/                  # 라이프사이클 훅
│
├── .moai/                      # MoAI-ADK 프로젝트 메타데이터
│   ├── project/                # 프로젝트 문서 (본 파일 위치)
│   │   ├── product.md          # 프로덕트 개요
│   │   ├── structure.md        # 프로젝트 구조 (본 파일)
│   │   └── tech.md             # 기술 스택
│   ├── specs/                  # SPEC 문서
│   ├── docs/                   # 생성된 문서
│   ├── config/                 # 설정 파일
│   └── memory/                 # 에이전트 메모리
│
├── input/                      # 사용자 준비 파일
│   ├── *.m4a                   # NotebookLM 리뷰 오디오
│   ├── *_summary_kr.md         # 요약 텍스트 (선택)
│   ├── *_summary_en.md         # 요약 텍스트 (선택)
│   ├── *_thumbnail_kr.png      # 썸네일 원본
│   ├── *_thumbnail_en.png      # 썸네일 원본
│   ├── *_video_kr.mp4          # NotebookLM 비디오 (선택)
│   └── *_video_en.mp4          # NotebookLM 비디오 (선택)
│
├── data/                       # 데이터 파일
│   └── source/                 # YouTube 자막 텍스트
│       ├── {비디오ID}_part1_author.txt
│       ├── {비디오ID}_part2_novel.txt
│       └── ...
│
├── assets/                     # 생성된 자산
│   ├── audio/                  # TTS 생성 오디오
│   │   ├── {책제목}_summary_ko.mp3
│   │   ├── {책제목}_summary_en.mp3
│   │   ├── {책제목}_review_ko.m4a
│   │   └── {책제목}_review_en.m4a
│   │
│   ├── images/                 # 책 관련 이미지
│   │   ├── {책제목}/
│   │   │   ├── cover.jpg       # 책 커버
│   │   │   ├── book_info.json  # 책 정보 메타데이터
│   │   │   ├── mood_001.jpg    # 무드 이미지
│   │   │   ├── mood_002.jpg
│   │   │   └── ... (100개)
│   │   └── {다른책}/
│   │
│   ├── summaries/              # 책 요약 마크다운
│   │   ├── {책제목}_summary_ko.md
│   │   └── {책제목}_summary_en.md
│   │
│   └── video/                  # NotebookLM 비디오
│       ├── {책제목}/
│       │   ├── ko/
│       │   │   ├── part1_video_ko.mp4
│       │   │   ├── part1_info_ko.png
│       │   │   ├── part2_video_ko.mp4
│       │   │   └── part2_info_ko.png
│       │   └── en/
│       │       ├── part1_video_en.mp4
│       │       ├── part1_info_en.png
│       │       ├── part2_video_en.mp4
│       │       └── part2_info_en.png
│       └── {다른책}/
│
├── output/                     # 최종 생성 영상 및 썸네일
│   ├── {책제목}_full_ko.mp4    # Summary+Video 한글
│   ├── {책제목}_full_en.mp4    # Summary+Video 영문
│   ├── {책제목}_episode_ko.mp4 # 일당백 한글
│   ├── {책제목}_episode_en.mp4 # 일당백 영문
│   ├── {책제목}_thumbnail_ko.jpg
│   └── {책제목}_thumbnail_en.jpg
│
├── scripts/                    # 유틸리티 스크립트 (27개)
│   ├── prepare_files_from_downloads.py
│   ├── fetch_separate_scripts.py
│   ├── generate_book_info.py
│   ├── validate_files.py
│   └── ... (더 많은 스크립트)
│
├── src/                        # 메인 파이프라인 모듈 (27개 + utils/)
│   ├── 01_prepare_assets.py    # [STAGE 1] 자산 준비
│   ├── 02_get_images.py        # [STAGE 2] 이미지 다운로드
│   ├── 08_generate_summary.py  # [STAGE 3] 요약 생성
│   ├── 09_text_to_speech_multi.py # [STAGE 4] TTS 오디오
│   ├── 10_create_video_with_summary.py # [STAGE 5] Summary+Video 제작
│   ├── 20_create_full_episode.py # [STAGE 6] 일당백 영상 제작
│   ├── 08_create_and_preview_videos.py # [STAGE 7] 메타데이터 생성
│   ├── 09_upload_from_metadata.py # [STAGE 8] YouTube 업로드
│   ├── 13_update_csv_from_youtube.py # [STAGE 9] CSV 업데이트
│   ├── 25_batch_add_pinned_comments.py # [STAGE 10] 댓글 추가
│   │
│   └── utils/                  # 유틸리티 모듈
│       ├── translations.py     # 한글↔영문 책/저자 매핑 (200+ 항목)
│       ├── affiliate_links.py  # 제휴 링크 생성
│       ├── video_utils.py      # 영상 편집 유틸리티
│       ├── api_utils.py        # API 통합 함수
│       ├── error_handlers.py   # 에러 처리
│       └── config_loader.py    # 설정 로더
│
├── secrets/                    # API 키 및 인증 정보 (절대 커밋 금지)
│   ├── client_secret.json      # YouTube API 클라이언트 보안 비밀
│   ├── credentials.json        # YouTube API 인증 토큰
│   ├── google-cloud-tts-key.json # Google Cloud TTS 서비스 계정
│   ├── openai-key.txt          # OpenAI API 키
│   ├── anthropic-key.txt       # Anthropic API 키
│   └── replicate-token.txt     # Replicate API 토큰
│
├── tests/                      # 유닛 테스트
│   ├── test_translations.py    # 번역 매핑 테스트
│   ├── test_affiliate_links.py # 제휴 링크 테스트
│   ├── test_video_utils.py     # 영상 유틸리티 테스트
│   └── test_integration.py     # 통합 테스트
│
├── .env                        # 환경 변수 설정 (프로젝트 루트)
├── .env.example                # 환경 변수 예제
├── .gitignore                  # Git 무시 파일
├── README.md                   # 프로젝트 개요
├── TODO.md                     # 작업 목록
├── CLAUDE.md                   # Claude Code 프로젝트 가이드
├── history.md                  # 변경 이력
├── ildangbaek_books.csv        # 유튜브 업로드 책 목록
├── requirements.txt            # Python 의존성
└── pyproject.toml              # 프로젝트 설정
```

## 각 디렉토리의 용도

### 입력 디렉토리 (`input/`)

**목적:** 사용자가 준비한 파일들을 임시 저장

**파일 패턴:**
- `{prefix}_audio_{언어}.m4a` - NotebookLM 리뷰 오디오 (필수)
- `{prefix}_summary_{언어}.md` - 요약 텍스트 (선택, 없으면 AI 생성)
- `{prefix}_thumbnail_{언어}.png` - 썸네일 원본 (선택, AI 생성 가능)
- `{prefix}_video_{언어}.mp4` - NotebookLM 비디오 (선택)

**예시:** `노인과바다_audio_kr.m4a`, `노인과바다_summary_en.md`

**중요:** 모든 영상 제작 작업은 input/ 폴더 확인부터 시작해야 합니다.

### 데이터 소스 디렉토리 (`data/source/`)

**목적:** YouTube 자막 텍스트 저장소

**생성 방법:** `scripts/fetch_separate_scripts.py` 실행

**파일 형식:**
- `{비디오ID}_part1_author.txt` - Part 1: 작가와 배경
- `{비디오ID}_part2_novel.txt` - Part 2: 소설 줄거리
- 추가 파트: `part3_*.txt`, `part4_*.txt` 등

### 자산 디렉토리 (`assets/`)

#### `assets/audio/` - TTS 생성 오디오
- `{책제목}_summary_ko.mp3` - 한글 요약 오디오 (5분)
- `{책제목}_summary_en.mp3` - 영문 요약 오디오
- 생성자: `src/09_text_to_speech_multi.py`
- 제공자: OpenAI / Google Cloud / Replicate

#### `assets/images/{책제목}/` - 이미지 저장소
- `cover.jpg` - 책 커버 (Google Books API 또는 사용자 제공)
- `book_info.json` - 책 정보 메타데이터 (제목, 저자, 설명 등)
- `mood_001.jpg` ~ `mood_100.jpg` - 무드 이미지 (100개)
- 생성자: `src/02_get_images.py`
- 출처: Pexels, Pixabay, Unsplash

#### `assets/summaries/` - 책 요약 텍스트
- `{책제목}_summary_ko.md` - 한글 요약 (500-750단어, 5분 분량)
- `{책제목}_summary_en.md` - 영문 요약
- 생성자: `src/08_generate_summary.py`
- 포맷: Hook/Body/Bridge 구조, HTML 주석으로 메타데이터 처리

#### `assets/video/{책제목}/{언어}/` - NotebookLM 비디오
- `part1_video_ko.mp4` - Part 1 비디오
- `part1_info_ko.png` - Part 1 인포그래픽
- `part2_video_ko.mp4` - Part 2 비디오
- `part2_info_ko.png` - Part 2 인포그래픽
- 용도: 일당백 스타일 영상 제작용

### 출력 디렉토리 (`output/`)

**목적:** 최종 생성 영상 및 썸네일

**파일 형식:**
- `{책제목}_full_ko.mp4` - Summary+Video 스타일 최종 영상 (한글)
- `{책제목}_episode_ko.mp4` - 일당백 스타일 최종 영상 (한글)
- `{책제목}_thumbnail_ko.jpg` - YouTube 썸네일 (JPG, PNG→JPG 자동 변환)

**생성자:**
- `src/10_create_video_with_summary.py` - Summary+Video 스타일
- `src/20_create_full_episode.py` - 일당백 스타일

### 스크립트 디렉토리 (`scripts/`)

**목적:** 유틸리티 및 헬퍼 스크립트 (27개)

**주요 스크립트:**
- `prepare_files_from_downloads.py` - input/ 폴더의 파일을 표준 네이밍으로 변환
- `fetch_separate_scripts.py` - YouTube URL에서 자막 다운로드
- `cookies.txt` - YouTube 자막 다운로드 IP 차단 우회용

### 메인 파이프라인 (`src/`)

**전체 모듈:** 27개의 순차 처리 모듈 + utils/

**파이프라인 단계:**

| 단계 | 모듈 | 입력 | 출력 |
|------|------|------|------|
| 1 | `01_prepare_assets.py` | input/ | assets/images/ |
| 2 | `02_get_images.py` | 책 제목/저자 | assets/images/{책}/mood_*.jpg |
| 3 | `08_generate_summary.py` | 책 제목/저자 | assets/summaries/{책}_summary.md |
| 4 | `09_text_to_speech_multi.py` | 요약 텍스트 | assets/audio/{책}_summary.mp3 |
| 5 | `10_create_video_with_summary.py` | 이미지+오디오 | output/{책}_full.mp4 |
| 6 | `20_create_full_episode.py` | 비디오+인포그래픽 | output/{책}_episode.mp4 |
| 7 | `08_create_and_preview_videos.py` | 영상 파일 | metadata.json |
| 8 | `09_upload_from_metadata.py` | metadata.json | YouTube URL |
| 9 | `13_update_csv_from_youtube.py` | YouTube | ildangbaek_books.csv |
| 10 | `25_batch_add_pinned_comments.py` | YouTube | 고정 댓글 |

**utils/ 모듈:**

| 모듈 | 기능 | LOC |
|------|------|-----|
| `translations.py` | 한글↔영문 책/저자 매핑 | 1,096 |
| `affiliate_links.py` | 제휴 링크 URL 생성 | 200+ |
| `video_utils.py` | 영상 편집 유틸리티 | 300+ |
| `api_utils.py` | API 통합 함수 | 250+ |
| `error_handlers.py` | 에러 처리 | 200+ |
| `config_loader.py` | 설정 로더 | 150+ |

### 테스트 디렉토리 (`tests/`)

**테스트 범위:** ~40-50% 코드 커버리지

**테스트 파일:**
- `test_translations.py` - 한글↔영문 매핑
- `test_affiliate_links.py` - 제휴 링크 생성
- `test_video_utils.py` - 영상 유틸리티
- `test_integration.py` - 통합 테스트

**실행:** `pytest`

### 보안 및 인증 (`secrets/`)

**중요:** 모든 파일은 `.gitignore`로 보호됨

**필수 파일:**

| 파일 | 용도 | API |
|------|------|-----|
| `client_secret.json` | YouTube 클라이언트 ID/비밀 | YouTube Data API v3 |
| `credentials.json` | YouTube 인증 토큰 | YouTube Data API v3 |
| `google-cloud-tts-key.json` | Google Cloud 서비스 계정 | Google Cloud TTS |
| `openai-key.txt` | OpenAI API 키 | OpenAI (GPT, TTS) |
| `anthropic-key.txt` | Anthropic API 키 | Claude API |
| `replicate-token.txt` | Replicate API 토큰 | Replicate xtts-v2 |

**설정 방법:**
1. `secrets/` 폴더 생성
2. 각 API에서 키 발급
3. 해당 파일에 저장
4. `.gitignore`에 `secrets/` 포함 (기본 포함됨)

## 핵심 파일 위치

### 프로젝트 루트 설정 파일

| 파일 | 용도 |
|------|------|
| `.env` | 환경 변수 (API 키, 설정값) |
| `.env.example` | 환경 변수 예제 |
| `CLAUDE.md` | Claude Code 프로젝트 가이드 |
| `README.md` | 프로젝트 개요 및 사용법 |
| `requirements.txt` | Python 의존성 목록 |
| `pyproject.toml` | 프로젝트 메타데이터 |
| `ildangbaek_books.csv` | YouTube 업로드 책 목록 및 메타데이터 |

### 메타데이터 매핑

**파일:** `src/utils/translations.py`

**목적:** 한글↔영문 책 제목 및 저자 자동 매핑

**구성:**
- `translate_book_title()` - 책 제목 매핑 (예: "죽음의 수용소에서" ↔ "Man's Search for Meaning")
- `translate_author_name()` - 저자 이름 매핑 (예: "빅터 프랭클" ↔ "Viktor Frankl")
- 200+ 책/저자 쌍 매핑

## 파일 네이밍 규칙

### 입력 파일 패턴
```
{prefix}_타입_{언어}.{확장자}

예시:
- 노인과바다_audio_kr.m4a
- 노인과바다_summary_en.md
- 노인과바다_thumbnail_kr.png
- 노인과바다_video_en.mp4
```

### 출력 파일 패턴
```
{책제목}_{유형}_{언어}.{확장자}

예시:
- 노인과바다_full_ko.mp4 (Summary+Video 한글)
- 노인과바다_episode_en.mp4 (일당백 영문)
- 노인과바다_thumbnail_ko.jpg (썸네일)
```

### 언어 코드
- `kr` / `ko` - 한국어
- `en` - 영어

## 주요 진입점

| 시나리오 | 스크립트 | 설명 |
|---------|---------|------|
| 새로운 책 시작 | `scripts/prepare_files_from_downloads.py` | input/ 파일 정렬 |
| 이미지 다운로드 | `src/02_get_images.py` | Pexels/Pixabay/Unsplash에서 100개 |
| 요약 생성 | `src/08_generate_summary.py` | Claude API로 5분 요약 |
| TTS 생성 | `src/09_text_to_speech_multi.py` | OpenAI/Google/Replicate |
| Summary+Video | `src/10_create_video_with_summary.py` | 최종 영상 합성 |
| 일당백 스타일 | `src/20_create_full_episode.py` | 에피소드 영상 |
| YouTube 업로드 | `src/09_upload_from_metadata.py` | 최종 업로드 |
| 댓글 추가 | `src/25_batch_add_pinned_comments.py` | 제휴 링크 댓글 |

---

문서 생성 완료: 2026-02-19
