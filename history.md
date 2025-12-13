# BookReview-AutoMaker 프로젝트 히스토리

## 2025-12-14

### 비디오 파이프라인 개선
- **롱폼 영상 구성 변경**:
  - NotebookLM audio review 부분 제거
  - 최종 구성: Summary + NotebookLM Video만 포함
  - 영상 길이 단축 및 제작 시간 개선
- **Pause 시간 단축**:
  - 섹션 간 pause: 3초 → 2초로 변경
  - `src/03_make_video.py`: `gap_duration`, `silence_duration` 기본값 변경
  - `src/08_create_and_preview_videos.py`: timestamp 계산 로직 업데이트
- **코드 수정**:
  - `src/03_make_video.py`:
    - `VideoMaker.create_video()` 메서드에서 Audio Review 부분 제거 (27줄 삭제)
    - Docstring 업데이트 (Summary → NotebookLM Video 순서)
    - Cleanup 코드 수정 (`review_audio.close()` 제거)
  - `src/08_create_and_preview_videos.py`:
    - 메타데이터 설명에서 "오디오 리뷰" 관련 문구 제거
    - 한글/영문 설명 모두 업데이트
    - 미사용 `review_duration` 변수 제거
- **README.md 업데이트**:
  - 영상 구조 설명 업데이트 (Audio Review 제거, Pause 3초 → 2초)
  - 프로젝트 개요에서 리뷰 오디오 파일 언급 제거
  - 워크플로우에서 리뷰 오디오 준비 단계 제거
  - 파일 준비 가이드에서 리뷰 오디오 관련 설명 제거
  - 영상 구성 섹션 및 timestamp 예시 업데이트

### 신경 끄기의 기술 영상 제작 및 업로드
- **책 제목**: 신경 끄기의 기술 (The Subtle Art of Not Giving a F*ck)
- **저자**: 마크 맨슨 (Mark Manson)
- **생성된 파일**:
  - 영상: `output/신경_끄기의_기술_review_with_summary_ko.mp4` (309MB), `output/신경_끄기의_기술_review_with_summary_en.mp4` (323MB)
  - 썸네일: `output/신경_끄기의_기술_thumbnail_ko.jpg`, `output/신경_끄기의_기술_thumbnail_en.jpg`
  - 메타데이터: `신경_끄기의_기술_review_with_summary_ko.metadata.json`, `신경_끄기의_기술_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
- **YouTube 업로드 완료**:
  - [1] [English] The Subtle Art of Not Giving a F*ck Book Review | [영어] 신경 끄기의 기술 책 리뷰
    - URL: https://www.youtube.com/watch?v=Mh77zAIt7OQ
  - [2] [한국어] 신경 끄기의 기술 책 리뷰 | [Korean] The Subtle Art of Not Giving a F*ck Book Review
    - URL: https://www.youtube.com/watch?v=Jzn154gb7qM

### 코드 개선: TTS 오류 수정 및 리뷰 오디오 선택사항화
- **문제**: TTS 생성 시 `summary_audio_path`가 None으로 전달되어 오류 발생
- **해결**:
  - **`src/10_create_video_with_summary.py`**:
    - TTS 생성 전 `summary_audio_path` 경로를 먼저 설정하도록 수정
    - 리뷰 오디오 검사를 선택사항으로 변경 (최신 구조에서는 리뷰 오디오가 필요 없음)
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "신경 끄기의 기술" → "The Subtle Art of Not Giving a F*ck" 매핑 추가
    - "마크 맨슨" → "Mark Manson" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-13

### 프로젝트 규칙 정리 및 최적화
- **`.cursorrules` 정리**:
  - 중복된 섹션("Video Production Pipeline Rules", "Date Recording Rules") 제거
  - 핵심 제약 사항을 "Standard Workflow Execution Order" 주석으로 통합하여 가독성 개선

### 이미지 검색 로직 개선
- **지리적/역사적 정확성 강화** (`src/02_get_images.py`):
  - AI 키워드 생성 프롬프트 수정
  - 책의 배경이 되는 국가/도시와 무관한 키워드(예: 한국, 태극기 등) 제외 로직 추가
  - 책의 설정(Setting)을 분석하여 해당 지역/시대에 맞는 키워드만 생성하도록 강제

### YouTube 업로드 기능 개선
- **강제 업로드 옵션 추가** (`src/09_upload_from_metadata.py`):
  - `--force` 플래그 추가
  - 이미 업로드된 영상이라도 중복 체크를 건너뛰고 재업로드할 수 있는 기능 구현
  - 사용자가 수동으로 영상을 삭제한 경우 유용

### Peter Lynch "One Up On Wall Street" 영상 제작 및 업로드
- **작업 내용**:
  - 파일 준비 (prefix: `peter`)
  - 이미지 다운로드 (100개, AI 키워드 + 기본 키워드)
  - 롱폼 TTS 생성 (한글/영어)
  - 영상 제작 (24분 분량)
  - YouTube 업로드 (비공개, 재업로드 포함)
- **업로드 결과**:
  - [한국어] One Up On Wall Street 책 리뷰: https://www.youtube.com/watch?v=BSbsebZK9lA
  - [English] One Up On Wall Street Book Review: https://www.youtube.com/watch?v=tro2UrHUu1E

## 2025-12-05

### Phase 8: 품질 개선 및 최적화

#### 영상 품질 향상
- **비트레이트 설정 개선** (`src/03_make_video.py`):
  - 비디오 비트레이트: 1500k → 5000k (3.3배 증가)
  - 오디오 비트레이트: 320k로 설정
  - CLI 인자로 비트레이트 조정 가능 (`--bitrate`, `--audio-bitrate`)
- **관련 스크립트 업데이트**:
  - `src/07_make_videos_both_languages.py`: 고품질 설정 적용
  - `src/10_create_video_with_summary.py`: 고품질 설정 적용

#### 처리 속도 최적화
- **병렬 이미지 다운로드** (`src/02_get_images.py`):
  - `ThreadPoolExecutor` 사용 (max_workers=5)
  - Unsplash, Pexels, Pixabay API 모두 병렬 처리 적용
  - 다운로드 속도 대폭 향상

#### 에러 처리 개선
- **재시도 로직 구현** (`src/utils/retry_utils.py`):
  - `retry_with_backoff` 데코레이터 추가
  - 지수 백오프 방식 (exponential backoff) 적용
  - 최대 3회 재시도, 초기 대기 시간 1-2초
- **적용 범위**:
  - `src/02_get_images.py`: 이미지 다운로드 및 API 요청
  - `src/09_text_to_speech.py`: OpenAI TTS API 호출
  - 네트워크 오류 및 일시적 API 장애 대응 강화

## 2025-12-02

### NotebookLM 비디오 업데이트 기능 추가

#### 새로운 스크립트
- **`scripts/update_notebooklm_video.py`**: Downloads 폴더에서 새로운 NotebookLM 비디오 파일을 찾아 교체하고 영상 재생성
  - Downloads 폴더에서 새 비디오 파일 자동 검색 (`{prefix}_video_{lang}.{ext}`)
  - 기존 비디오 파일 자동 백업 (`.backup` 확장자)
  - 새 파일로 교체 후 해당 언어의 영상 자동 재생성
  - 사용법: `python scripts/update_notebooklm_video.py --book-title "책 제목" --prefix "파일접두사" --language ko`

#### 코드 개선
- **`src/02_get_images.py`**:
  - 기존 이미지가 100개 이상이면 다운로드 건너뛰기 기능 추가
  - 기존 이미지 개수 확인 후 부족한 경우에만 추가 다운로드
  - 불필요한 API 호출 및 시간 절약

- **`src/03_make_video.py`**:
  - 이미지 리사이즈 오류 수정 (numpy import 추가)
  - RGB 모드 변환 강화 (RGBA, Grayscale 등 다양한 형식 지원)
  - ImageClip 생성 시 크기 명시적 지정으로 fade 효과 오류 해결
  - 이미지 shape 검증 및 자동 수정 로직 추가

- **`src/08_create_and_preview_videos.py`**:
  - 한국어 메타데이터에도 timestamp 자동 포함 기능 추가
  - 영어/한국어 모두 Video Chapters 섹션에 timestamp 자동 생성
  - `calculate_timestamps_from_video` 함수로 각 섹션 길이 자동 계산

- **`src/utils/translations.py`**:
  - "The Loneliness of Sonia and Sunny" 책 제목 매핑 추가
  - 영어/한글 제목 상호 변환 지원

- **`src/08_create_and_preview_videos.py`**:
  - 제목에 괄호가 포함된 경우 (예: "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)") 자동 처리
  - 괄호 안의 한글 제거 후 영어 제목으로 인식

- **`src/09_upload_from_metadata.py`**:
  - 태그 검증 및 정리 기능 추가 (`_validate_and_clean_tags` 메서드)
  - YouTube 태그 규칙 준수 (최대 30자, 특수문자 제거)
  - 30자 초과 태그 자동 제거 및 경고 메시지 출력
  - 업로드 실패 방지를 위한 태그 검증 강화

#### 문서 업데이트
- README.md에 **"빠른 시작 가이드"** 섹션 추가
  - 초보자를 위한 단계별 작업 가이드 제공
  - Downloads 폴더 파일 준비 방법 상세 설명
  - 전체 파이프라인 실행 예시 포함
  - 결과 확인 및 YouTube 업로드 가이드
  - 처음 사용 시 팁 제공
- README.md에 NotebookLM 비디오 업데이트 스크립트 사용법 추가
- README.md에 이미지 다운로드 개선 사항 설명 추가
- README.md에 메타데이터 timestamp 기능 설명 추가
- markdownlint 오류 48개 모두 수정 완료

## 2025-12-02 (이전)

### Downloads 폴더에서 자동 파일 준비 기능 추가

#### 새로운 워크플로우
- **Downloads 폴더 기반 작업 시작**: `~/Downloads` 폴더에 파일을 준비하고 자동으로 표준 네이밍으로 변경하여 적절한 위치로 이동
- **지원 파일 타입**:
  - 오디오: `{prefix}_audio_{lang}.{ext}` → `assets/audio/{safe_title}_review_{lang}.{ext}`
  - Summary: `{prefix}_summary_{lang}.md` → `assets/summaries/{safe_title}_summary_{lang}.md`
  - 썸네일: `{prefix}_thumbnail_{lang}.png` → `output/{safe_title}_thumbnail_{lang}.jpg` (PNG → JPG 변환)
  - 비디오: `{prefix}_video_{lang}.{ext}` → `assets/video/{safe_title}_notebooklm_{lang}.{ext}`

#### 새로 추가된 스크립트
- **`scripts/prepare_files_from_downloads.py`**: Downloads 폴더에서 파일을 찾아 표준 네이밍으로 변경하고 이동
  - 자동 접두사 감지 기능
  - 언어 자동 인식 (`_en`, `_kr`, `_ko` 지원)
  - PNG → JPG 변환 (4K 해상도, 2MB 이하 압축)
- **`scripts/run_full_pipeline_from_downloads.py`**: 전체 파이프라인을 한 번에 실행
  - 파일 준비 → 이미지 다운로드 → 영상 생성 (한글/영어) → 메타데이터 생성

#### 코드 개선


## 이전 히스토리

이전 작업 내역은 [docs/history_archive.md](docs/history_archive.md)에서 확인할 수 있습니다.

## 2025-12-14

### YouTube 업로드 완료
- 업로드된 책: 신경_끄기의_기술_with_summary_en, 신경_끄기의_기술_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] The Subtle Art of Not Giving a F*ck Book Review | [영어] 신경 끄기의 기술 책 리뷰
  - URL: https://www.youtube.com/watch?v=Mh77zAIt7OQ
- [2] [한국어] 신경 끄기의 기술 책 리뷰 | [Korean] The Subtle Art of Not Giving a F*ck Book Review
  - URL: https://www.youtube.com/watch?v=Jzn154gb7qM
