# BookReview-AutoMaker

NotebookLM 기반 책 리뷰 영상 자동 생성기

## 프로젝트 개요

이 프로젝트는 NotebookLM을 활용하여 책 리뷰 영상을 자동으로 생성하는 파이프라인입니다.
사용자가 NotebookLM에서 생성한 오디오 파일을 업로드하면, AI가 자동으로 요약을 생성하고 이미지를 합성하여 유튜브 영상을 제작합니다.

## 전체 워크플로우 (6단계)

1.  **NotebookLM 오디오 업로드**: 사용자가 NotebookLM에서 생성한 오디오 파일을 `assets/audio/` 폴더에 업로드합니다.
2.  **관련 이미지 확보**: 책 제목과 관련된 고품질 무드 이미지를 **100개** 자동으로 수집합니다. (`assets/images/{책제목}/` 폴더)
3.  **오디오 서머리 생성**: 5분 분량의 책 요약(한글/영문)을 생성하고 TTS로 MP3 변환합니다. 생성된 서머리 오디오는 `assets/audio/`로 이동됩니다.
4.  **오디오 합성**: `오디오 서머리 MP3` + `3초 정적(Pause)` + `NotebookLM 오디오`를 자동으로 연결합니다.
5.  **영상 합성**: 연결된 오디오와 100개의 이미지를 자연스럽게 합성하여 MP4 영상을 생성합니다. (`output/` 폴더)
6.  **배포 준비 및 업로드**: 썸네일과 메타데이터를 생성하고, 사용자의 허가 하에 유튜브에 업로드합니다.

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

## 사용 방법

### 1. NotebookLM 오디오 준비
NotebookLM에서 생성한 오디오 파일을 `assets/audio/` 폴더에 위치시킵니다.
파일명 예시: `The_Boy_is_Coming_review_en.m4a`

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
  --summary-duration 5.0
```

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
│   └── summaries/      # 생성된 요약 텍스트
├── docs/               # 문서
│   └── SUMMARY_TEMPLATE.md  # 유튜브 롱폼 영상용 요약 템플릿 (Hook → Summary → Bridge)
├── output/             # 생성된 영상 및 썸네일
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
- Unsplash/Pexels API를 통한 고품질 이미지 다운로드

## 라이선스

MIT License
