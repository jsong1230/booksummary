# YouTube 메타데이터 생성 가이드

이 문서는 BookReview-AutoMaker 프로젝트에서 YouTube 영상용 SEO 최적화 메타데이터(제목, 설명, 태그)를 생성하는 방법을 설명합니다.

## 1. 개요

메타데이터는 JSON 형식(`*.metadata.json`)으로 생성되며, 이는 업로드 스크립트(`src/09_upload_from_metadata.py`)에서 사용됩니다. 메타데이터 생성에는 두 가지 주요 스타일이 있습니다.

1.  **서머리(Summary) 스타일**: 일반적인 5분 AI 요약 영상용.
2.  **에피소드(Episode) 스타일 (일당백)**: NotebookLM 파트와 인포그래픽을 결합한 롱폼 영상용.

---

## 2. 에피소드 스타일 메타데이터 (일당백)

롱폼 에피소드 영상의 경우 `src/20_create_episode_metadata.py`를 사용합니다.

### 기본 사용법
```bash
# 한글 메타데이터 생성
python src/20_create_episode_metadata.py --title "책제목" --language ko

# 영문 메타데이터 생성
python src/20_create_episode_metadata.py --title "Book Title" --language en
```

### 주요 기능
-   **동적 파트 감지**: `assets/notebooklm/` 폴더를 확인하여 영상에 포함된 파트(Part 1, Part 2 등) 개수를 자동으로 감지합니다.
-   **스마트 타임스탬프**: 실제 영상 파일의 길이를 바탕으로 정확한 타임스탬프를 생성합니다.
-   **장르 감지**: 책 제목과 정보를 분석하여 소설, 시, 수필 또는 일반 작품으로 자동 분류합니다.
-   **제목 형식**:
    - 한글: `{한글제목} 책 리뷰{작가명}`
    - 영문: `{영문제목} Book Review{작가명}`
-   **SEO 태그 최적화**:
    -   현재 연도(예: 2026)를 포함한 트렌드 태그를 포함합니다.
    -   영문 메타데이터의 경우 글로벌 SEO를 위해 한글 문자를 자동으로 필터링합니다.
-   **글자 수 제한**: YouTube 제목 제한인 100자 이내로 제목을 유지합니다.
-   **다국어 메타데이터 지원**: 양쪽 언어의 제목과 설명을 `localizations` 필드에 저장하여 YouTube의 다국어 메타데이터 기능을 활용합니다.

### 주요 인자(Arguments)
-   `--title`: 책 제목 (필수).
-   `--language`: `ko` 또는 `en` (기본값: `ko`).
-   `--video-path`: 영상 파일 경로 수동 지정.
-   `--thumbnail-path`: 썸네일 경로 수동 지정.
-   `--preview`: 파일로 저장하지 않고 콘솔에 미리보기만 출력.

---

## 3. 서머리 스타일 메타데이터

일반 서머리 메타데이터는 대개 `src/08_create_and_preview_videos.py` 영상 생성 과정에서 함께 생성됩니다.

### 기본 사용법
영상 생성 스크립트 실행 시:
```bash
python src/08_create_and_preview_videos.py --title "책제목" --lang both
```

### 주요 기능
-   **채널명**: "1DANG100" (일당백)으로 설정.
-   **제목 형식**: 
    - 한글: `[핵심 요약] {한글제목} 핵심 정리{작가명}`
    - 영문: `[Summary] {영문제목} Book Review{작가명}`
-   **자동 번역**: `src/utils/translations.py`를 사용하여 한글/영문 제목 및 저자명을 매핑합니다.
-   **다국어 메타데이터 지원**: 양쪽 언어의 제목과 설명을 `localizations` 필드에 저장하여 YouTube의 다국어 메타데이터 기능을 활용합니다.

---

## 4. 메타데이터 파일 형식

생성된 JSON 파일은 다음과 같은 구조를 가집니다:

```json
{
  "video_path": "output/Book_Title_full_episode_ko.mp4",
  "title": "책제목 책 리뷰",
  "description": "0:00 - Part 1: 작가와 배경\n...",
  "tags": ["일당백", "책리뷰", "2026", ...],
  "language": "ko",
  "book_title": "책제목",
  "thumbnail_path": "output/Book_Title_thumbnail_ko.jpg",
  "video_duration": 827.49,
  "localizations": {
    "ko": {
      "title": "책제목 책 리뷰",
      "description": "0:00 - Part 1: 작가와 배경\n..."
    },
    "en": {
      "title": "Book Title Book Review",
      "description": "0:00 - Part 1: Author & Background\n..."
    }
  }
}
```

### 다국어 메타데이터 (`localizations`)

-   **자동 생성**: 메타데이터 생성 시 양쪽 언어(한글/영문)의 제목과 설명이 자동으로 생성되어 `localizations` 필드에 저장됩니다.
-   **YouTube 자동 표시**: YouTube는 시청자의 언어 설정에 따라 해당 언어의 제목과 설명을 자동으로 표시합니다.
-   **한국 시청자**: 한국어 제목과 설명만 표시됩니다.
-   **영어권 시청자**: 영어 제목과 설명만 표시됩니다.

---

## 5. 트러블슈팅

-   **썸네일을 찾을 수 없음**: 썸네일이 `output/` 폴더에 있는지, 그리고 `{표준제목}_thumbnail_{ko/en}.jpg` 명명 규칙을 따르는지 확인하세요.
-   **메타데이터 불일치**: 영상 길이가 변경된 경우, 타임스탬프의 정확성을 위해 메타데이터를 다시 생성하십시오.
-   **제목이 너무 긴 경우**: 100자를 초과하면 스크립트가 자동으로 제목 끝을 "..."으로 자릅니다.

---

## 6. 다음 단계: 업로드

메타데이터가 준비되면 다음 명령어로 업로드합니다:
```bash
python src/09_upload_from_metadata.py --privacy private --auto
```
