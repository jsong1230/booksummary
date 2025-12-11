# BookReview-AutoMaker 프로젝트 히스토리

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
- **`src/10_create_video_with_summary.py`**:
  - 기존 Summary 파일 자동 감지 및 사용 (`assets/summaries/` 폴더 확인)
  - Summary 파일이 있으면 TTS만 생성하고 요약 생성은 건너뛰기
  - Summary 오디오가 이미 있으면 재생성하지 않음

#### 문서 업데이트
- README.md에 "방법 1: Downloads 폴더에서 자동 준비 (권장)" 섹션 추가
- 전체 워크플로우 설명 개선
- 파일 네이밍 규칙 상세 설명 추가

## 2025-12-01

### NotebookLM 비디오 통합 기능 추가
- **영상 구성 변경**: Summary → NotebookLM Video → Audio 순서로 영상 생성
  - Summary 부분: 요약 오디오 + 이미지 슬라이드쇼
  - NotebookLM Video 부분: NotebookLM에서 생성한 비디오 자동 삽입
  - Audio 부분: 리뷰 오디오 + 이미지 슬라이드쇼
- **NotebookLM 비디오 자동 검색 기능**:
  - `assets/video/` 폴더에서 자동으로 비디오 파일 검색
  - 파일명 기반 언어 자동 감지 (한글 파일명 → 한글 비디오, 영문 파일명 → 영어 비디오)
  - 명시적 언어 표시 (`_ko`, `_en`) 우선 인식
- **코드 변경사항**:
  - `src/03_make_video.py`: `create_video` 메서드에 `notebooklm_video_path` 파라미터 추가
  - `src/10_create_video_with_summary.py`: NotebookLM 비디오 자동 검색 및 전달 로직 추가
  - `--notebooklm-video` CLI 옵션 추가
- **폴더 구조**:
  - `assets/video/` 폴더 생성 (NotebookLM 비디오 저장용)
- **문서 업데이트**:
  - README.md에 NotebookLM 비디오 사용법 추가

## 2024-11-23

### 초기 프로젝트 설정
- 프로젝트 디렉토리 구조 생성
- Phase 1: 자료 수집 자동화 코드 작성
  - `01_search_urls.py`: 책 관련 URL 수집 스크립트
    - 위키백과, 온라인 서점, 뉴스 리뷰 타겟 검색
    - NotebookLM용 텍스트 파일 출력
    - CSV/JSON 파일로 일괄 처리 지원
  - `02_get_images.py`: 이미지 다운로드 스크립트
    - Google Books API로 책 표지 다운로드
    - Pexels/Unsplash API로 무드 이미지 다운로드 (5~10장)
    - assets/images/{책제목}/ 폴더에 정리

### 환경 설정
- requirements.txt 작성
- .env 파일 설정 (모든 API 키 포함)
- 가상환경 설정 스크립트 작성
- 실행 스크립트 작성 (가상환경 자동 활성화)

### API 키 설정
- GOOGLE_BOOKS_API_KEY: 설정 완료
- PEXELS_API_KEY: 설정 완료
- UNSPLASH_ACCESS_KEY: 설정 완료
- OPENAI_API_KEY: 설정 완료
- CLAUDE_API_KEY: 설정 완료

### 패키지 설치
- python-dotenv, requests, beautifulsoup4, lxml
- googlesearch-python
- google-api-python-client
- pexels-api
- moviepy, pydub (Phase 4용)

### 프로젝트 문서화
- README.md 작성 (설치 방법, 사용법, API 키 발급 방법)
- TODO 파일 생성
- HISTORY 파일 생성
- RULES 파일 생성 (예정)

### Git 설정
- .gitignore 설정
- 자동 커밋/푸시 스크립트 작성

## 다음 작업
- Phase 4: 영상 합성 및 편집 기능 구현
- 테스트 및 버그 수정


## 2025-11-23

### YouTube 업로드 완료
- 업로드된 책: 노르웨이의_숲
- 업로드된 영상 수: 2개
- [1] [English] Norwegian Wood Book Review | [영어] 노르웨이의 숲 책 리뷰 | Auto-Generated
  - URL: https://www.youtube.com/watch?v=6L2zcTHfMXg
- [2] [한국어] 노르웨이의 숲 책 리뷰 | [Korean] Norwegian Wood Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=w4D-PVE3Aa0

## 2025-11-24

### 영상 생성 최적화
- **줌인/줌아웃 효과 제거**: 정적 이미지 + 페이드 전환만 사용하도록 변경
- **비트레이트 조정**: 1500k로 낮춰서 정적 이미지 영상에 최적화
- **MoviePy API 수정**: `resized` → `resize` 메서드 변경 (호환성 개선)
- **파일 크기 최적화**: 15.7분 영상 기준 약 172MB (이전 725MB에서 대폭 감소)

### 1984 영상 생성 진행 중
- **한글 영상**: ✅ 완료
  - 파일: `output/1984_review_ko.mp4`
  - 크기: 183MB
  - 길이: 15.7분 (940초)
  - 생성 시간: 2025-11-24 00:38
  - 이미지: 21개 (cover 1개 + mood 20개)
  - 설정: 정적 이미지 + 페이드 전환, 비트레이트 1500k
- **영문 영상**: ⏳ 대기 중 (영문 오디오 파일 필요)
- **썸네일**: ⏳ 대기 중
- **메타데이터**: ⏳ 대기 중

### URL 수집 배치 작업 진행 중
- **백그라운드 프로세스**: 실행 중 (PID: 78980)
- **진행률**: 59% (167/283개 완료)
- **총 항목**: 283개
  - 책: 83개 (노르웨이의 숲 제외)
  - 주제: 200개
- **생성된 파일**: 167개 MD 파일 (`assets/urls/` 폴더)
- **최근 생성**: 2025-11-24 08:50 (프리랜서_경제Gig_Economy의_구조_notebooklm.md)
- **예상 완료 시간**: 약 40-50분 후 (남은 116개 항목)

### 노르웨이의 숲 관련 파일 삭제
- 오디오 파일 삭제
- 이미지 파일 삭제 (20개)
- URL MD 파일 삭제
- CSV에서 제외

### 코드 개선
- URL 수집 스크립트 개선: DuckDuckGo 검색 + YouTube API 통합
- 배치 URL 수집 스크립트 추가 (`scripts/batch_collect_urls.py`)
- 전체 파이프라인 스크립트 추가 (`src/12_full_pipeline.py`)
- 유틸리티 모듈 추가 (`src/utils/`)
- 썸네일 생성 및 업로드 스크립트 추가 (`src/10_generate_thumbnail.py`, `src/11_upload_thumbnails.py`)

### Git 커밋
- 커밋 해시: `5d4ac07`
- 메시지: "feat: 영상 생성 최적화 - 줌인 효과 제거 및 비트레이트 조정"
- 변경: 47개 파일, 3,864줄 추가, 248줄 삭제

## 2024-11-24 (후반)

### 요약 및 TTS 기능 추가 ✅
- **AI 기반 책 요약 생성** (`src/08_generate_summary.py`)
  - Claude API 또는 OpenAI API 사용
  - 한글/영문 지원
  - 인트로/아웃트로 자동 추가
  - 한글 존댓말 강제 적용
  - 최소 단어 수 보장 로직

- **TTS 음성 생성** (`src/09_text_to_speech.py`)
  - OpenAI TTS API 사용
  - 한글: 'nova' 음성 (자연스러운 여성 음성)
  - 영어: 'alloy' 음성
  - 긴 텍스트 자동 분할 (4096자 제한 대응)
  - 문장 단위 분할 및 오디오 병합

- **요약 포함 영상 제작** (`src/10_create_video_with_summary.py`)
  - 요약 오디오와 리뷰 오디오 자동 연결
  - 3초 간격 추가 (자연스러운 전환)
  - 페이드 인/아웃 효과

### 영상 생성 개선 ✅
- **이미지 순환 반복**: 최대 100개 이미지를 영상 길이에 맞춰 순환 반복
- **페이드 전환**: fade in/out 효과로 자연스러운 전환
- **오디오 연결**: 요약 오디오 + 3초 간격 + 리뷰 오디오

### 썸네일 생성 기능 ✅
- **자동 썸네일 생성** (`src/10_generate_thumbnail.py`)
  - 책 제목, 작가 정보 포함
  - 한글/영문 버전 지원
  - DALL-E 배경 이미지 옵션
  - YouTube 권장 크기 (1280x720)
  - 그라데이션 배경 지원

### 1984 영상 생성 완료
- **한글 영상**: ✅ 완료
  - 파일: `output/1984_review_with_summary_ko.mp4`
  - 크기: 232MB
  - 길이: 19분 53초
  - 구성: 요약 (2.8분) + 3초 간격 + 리뷰 (17분)
  - 이미지: 100개 순환 반복
  - 썸네일: `output/1984_thumbnail_ko.jpg` (201K)

- **영어 영상**: ⚠️ 요약 미포함 (나중에 재생성 예정)
  - 파일: `output/1984_review_with_summary_en.mp4`
  - 크기: 454MB
  - 길이: 38분 38초
  - 썸네일: `output/1984_thumbnail_en.jpg` (206K)

### 코드 개선
- 텍스트 분할 로직 개선 (TTS API 제한 대응)
- 오디오 연결 로직 개선 (fade 효과, 간격 추가)
- 이미지 순환 로직 개선 (100개 이미지 순환 반복)
- 인트로/아웃트로 중복 제거 로직 개선
- 메타데이터에 요약/리뷰 정보 포함

### Git 커밋 준비
- README 업데이트 (새로운 기능 추가)
- history 파일 업데이트
- 임시 파일 정리

## 2025-11-25

### YouTube 업로드 완료
- 업로드된 책: 1984_with_summary_en, 1984_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] 1984 Book Review | [영어] 1984 책 리뷰 | Auto-Generated
  - URL: https://www.youtube.com/watch?v=cRd7BWQV4S8
- [2] [한국어] 1984 책 리뷰 | [Korean] 1984 Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=_dhn1O7BWNs

## 2025-11-28

### YouTube 업로드 완료
- 업로드된 책: 호밀밭의_파수꾼_with_summary_ko, 호밀밭의_파수꾼_with_summary_en
- 업로드된 영상 수: 2개
- [1] [English] The Catcher in the Rye Book Review | [영어] 호밀밭의 파수꾼 책 리뷰 | Auto-Generated
  - URL: https://www.youtube.com/watch?v=Je7tPM-5k-s
- [2] [한국어] 호밀밭의 파수꾼 책 리뷰 | [Korean] The Catcher in the Rye Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=kxiAn0TW0_s

### 유튜브 채널에서 CSV 자동 업데이트 기능 추가
- **새 스크립트**: `src/13_update_csv_from_youtube.py`
  - 유튜브 채널에 업로드된 책 정보를 자동으로 CSV에 반영
  - YouTube Data API를 사용하여 채널의 모든 비디오 검색
  - 비디오 제목과 책 제목 매칭 (별칭 지원: "노르웨이의 숲" = "상실의 시대")
  - Shorts 비디오 자동 제외
  - `status`, `youtube_uploaded`, `video_created` 필드 자동 업데이트

### 깊이 있는 URL 수집 기능 추가
- **새 스크립트**: `src/14_collect_deep_urls_for_notebooklm.py`
  - 유튜브 롱폼 북튜브를 위한 깊이 있는 자료 수집
  - YouTube 영상(30분 이상) 우선 수집 (전체의 50% 목표)
  - PDF 파일, 논문, 학술 사이트 검색 지원
  - 특정 YouTube 채널 우선순위 검색
    - 최우선: @1DANG100 (일당백)
    - 한글 우선순위: @thewinterbookstore, @chaegiljji, @humanitylearning, @mkkimtv
    - 영어 우선순위: @BTFC, @ClimbtheStacks, @JackEdwards, @arielbissett
  - 학술 사이트: academia.edu, researchgate.net, jstor.org, dbpia.co.kr, kci.go.kr, riss.kr 등
  - 결과 저장: `assets/urls/{책제목}_notebooklm.md` (URL만 저장)

### URL 수집 프롬프트 문서 작성
- **새 문서**: `docs/URL_COLLECTION_PROMPT.md`
  - GPT/Gemini에게 직접 사용할 수 있는 프롬프트 템플릿
  - 검색 쿼리, 검증 규칙, 채널 우선순위 등 상세 가이드 포함
  - 예시 프롬프트 제공

### 프로젝트 규칙 업데이트
- `.cursorrules`에 CSV 업데이트 규칙 추가
  - 커밋 전 필수 작업에 `ildangbaek_books.csv` 업데이트 항목 추가
  - 유튜브 채널 업로드 정보 반영 방법 명시

## 2025-11-29

### YouTube 업로드 완료
- 업로드된 책: Animal_Farm_with_summary_en, 동물농장_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] 동물농장 Book Review | [영어] 동물농장 책 리뷰 | Auto-Generated
  - URL: https://www.youtube.com/watch?v=VJevqE1i5eY
- [2] [한국어] 동물농장 책 리뷰 | [Korean] 동물농장 Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=7kKPZNp7Vqc

## 2025-11-30

### YouTube 업로드 완료
- 업로드된 책: 동물농장_with_summary_ko
- 업로드된 영상 수: 1개
- [1] [한국어] 동물농장 책 리뷰 | [Korean] 동물농장 Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=v3HWKy3I384

## 2025-11-30

### 동물농장 영상 제작 및 업로드
- **한글 영상 재생성**: 요약 오디오 포함 버전으로 재생성
  - 파일: `output/동물농장_review_with_summary_ko.mp4` (219MB, 약 18.7분)
  - 구성: 요약(3.9분) + 3초 간격 + 리뷰(14.8분)
  - YouTube 업로드: https://www.youtube.com/watch?v=v3HWKy3I384

### 햄릿 영상 제작 및 업로드
- **요약 생성**: 한글/영어 요약 텍스트 생성 (MD 파일 기반)
- **TTS 오디오 생성**: 한글(nova), 영어(alloy) 음성 생성
- **이미지 다운로드**: 82개 무드 이미지 수집
- **영상 제작**:
  - 한글: `output/햄릿_review_with_summary_ko.mp4` (205MB, 약 17.5분)
  - 영어: `output/Hamlet_review_with_summary_en.mp4` (188MB, 약 16분)
- **썸네일 생성**: PNG 파일을 썸네일 크기로 리사이즈하여 교체 (2MB 이하로 압축)
- **YouTube 업로드**: 2개 영상 업로드 완료
  - [1] [English] Hamlet Book Review: https://www.youtube.com/watch?v=BcNpf_bYNNI
  - [2] [한국어] 햄릿 책 리뷰: https://www.youtube.com/watch?v=pe4LYzG_2ts

### 태그 생성 기능 개선
- **추천 기관 태그 추가** (`src/08_create_and_preview_videos.py`, `src/05_auto_upload.py`)
  - 세계적/국내기관 및 미디어: 뉴욕타임즈, 아마존, 타임지, CNN, 뉴스위크
  - 주요 서점: 교보문고, 알라딘, YES24
  - 주요 도서관: 국립중앙도서관, 서울도서관
  - 정부기관: 문화체육관광부, 한국출판문화산업진흥원
  - 유명 대학: 서울대학교, 고려대학교, 연세대학교, 하버드대학교, 시카고대학교, 도쿄대학교, 베이징대학교, 미국대학위원회
  - 문학상: 노벨문학상, 퓰리처상, 맨부커상, 공쿠르상, 르노도상
  - 기타: 출판저널, 학교도서관저널, 서평지, 독서운동, 환경책선정위원회
  - 우선순위에 따라 선택적으로 추가 (YouTube 태그 제한 고려)

## 2025-11-30

### 벅아이(Buckeye) 영상 제작 및 업로드 완료
- **책 정보**: Buckeye (Patrick Ryan 저)
- **작업 내용**:
  - 한글 요약 생성 (5분 목표)
  - 요약 TTS 오디오 생성 (한글/영어)
  - 이미지 다운로드 (96개 무드 이미지)
  - 한글/영어 영상 제작 (요약 + 리뷰 오디오)
  - 썸네일 생성 및 PNG 파일로 교체 (2MB 이하 압축)
  - 메타데이터 생성 (한글/영어)
- **YouTube 업로드**:
  - 업로드된 영상 수: 2개
  - [1] [English] Buckeye Book Review | [영어] 벅아이 책 리뷰 | Auto-Generated
    - URL: https://www.youtube.com/watch?v=YTkz7T-r7OU
    - 파일 크기: 161.26 MB
  - [2] [한국어] 벅아이 책 리뷰 | [Korean] Buckeye Book Review | 일당백 스타일
    - URL: https://www.youtube.com/watch?v=0t_VwtyyDN8
    - 파일 크기: 163.62 MB
- **CSV 업데이트**: data/ildangbaek_books.csv에 벅아이 정보 추가

### 메타데이터 생성 로직 개선
- **문제**: 영어 메타데이터의 한글 부분에 영어 제목이 그대로 들어가는 문제
- **해결**: 
  - `translate_book_title_to_korean` 함수에 "Buckeye" → "벅아이" 매핑 추가
  - `translate_book_title` 함수에 "벅아이" → "Buckeye" 매핑 추가
  - `generate_title` 함수에서 번역 실패 시 발음 변환 매핑 사용
  - `src/08_create_and_preview_videos.py`와 `src/05_auto_upload.py` 모두 수정
- **결과**: 
  - 영어 메타데이터: `[English] Buckeye Book Review | [영어] 벅아이 책 리뷰`
  - 한글 메타데이터: `[한국어] 벅아이 책 리뷰 | [Korean] Buckeye Book Review`

## 2025-11-30

### 선라이즈 온 더 리핑(Sunrise on the Reaping) 영상 제작 및 업로드 완료
- **책 정보**: Sunrise on the Reaping (Suzanne Collins 저)
- **작업 내용**:
  - 한글/영어 요약 생성 (5분 목표)
  - 요약 TTS 오디오 생성 (한글/영어)
  - 이미지 다운로드 (100개 무드 이미지)
  - 한글/영어 영상 제작 (요약 + 리뷰 오디오)
  - 썸네일 생성 및 PNG 파일로 교체 (2MB 이하 압축)
  - 메타데이터 생성 (한글/영어)
- **YouTube 업로드**:
  - 업로드된 영상 수: 2개
  - [1] [English] Sunrise on the Reaping Book Review | [영어] 선라이즈 온 더 리핑 책 리뷰 | Auto-Generated
    - URL: https://www.youtube.com/watch?v=YifDjwcQKi8
    - 파일 크기: 194.27 MB
  - [2] [한국어] 선라이즈 온 더 리핑 책 리뷰 | [Korean] Sunrise on the Reaping Book Review | 일당백 스타일
    - URL: https://www.youtube.com/watch?v=QcmWjHj93fA
    - 파일 크기: 174.14 MB
- **CSV 업데이트**: data/ildangbaek_books.csv에 선라이즈 온 더 리핑 정보 추가

## 2025-12-01

### 썸네일 생성 방식 변경
- **변경 사항**: 썸네일을 Nano Banana에서 수동으로 만든 PNG 파일을 기반으로 처리하도록 변경
  - `process_png_thumbnails` 메서드 개선: `_kr`, `_ko`, `_en` 등으로 구분된 PNG 파일 자동 인식
  - `generate_thumbnail` 메서드: 자동 생성 비활성화, 경고 메시지만 출력
  - `08_create_and_preview_videos.py`: PNG 파일 우선 처리, 없으면 경고만 출력
  - 파일명 예시: `{책제목}_kr.png`, `{책제목}_ko.png`, `{책제목}_en.png`

### 메타데이터 제목 형식 변경
- **변경 사항**: 제목에서 불필요한 접미사 제거
  - 한글 제목: `[한국어] 불안 세대 책 리뷰 | [Korean] The Anxious Generation Book Review` (일당백 스타일 제거)
  - 영어 제목: `[English] The Anxious Generation Book Review | [영어] 불안 세대 책 리뷰` (Auto-Generated 제거)
  - `src/08_create_and_preview_videos.py`의 `generate_title` 함수 수정
  - `src/05_auto_upload.py`의 `generate_title` 메서드 수정

### PNG to JPG 변환 스크립트 추가
- **추가 파일**: `convert_png_to_jpg.py`
  - output 폴더의 PNG 파일을 JPG로 변환하여 롱폼 썸네일로 사용 가능하게 함
  - 4K 해상도 (3840x2160)로 리사이즈
  - 2MB 이하로 압축

## 2025-12-01

### YouTube 업로드 완료
- 업로드된 책: 불안_세대_with_summary_en, 불안_세대_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] The Anxious Generation Book Review | [영어] 불안 세대 책 리뷰 | Auto-Generated
  - URL: https://www.youtube.com/watch?v=YxzRHyImr_Y
- [2] [한국어] 불안 세대 책 리뷰 | [Korean] The Anxious Generation Book Review | 일당백 스타일
  - URL: https://www.youtube.com/watch?v=XU92ENg3eiI

### 썸네일 검색 로직 개선
- **문제**: 썸네일 파일명이 정확히 일치하지 않으면 찾지 못하는 문제
- **해결**: 다양한 파일명 패턴을 지원하도록 검색 로직 개선
  - 책 제목 변형 생성 (공백 제거, 언더스코어 변환 등)
  - 언어 패턴 확장 (`_ko`, `_kr`, `_en` 등 다양한 형식 지원)
  - 다양한 파일명 패턴 시도 (`{책제목}_thumbnail_{lang}.jpg`, `{책제목}_{lang}_thumbnail.jpg` 등)
  - 유사도 매칭 (output 폴더의 모든 썸네일 파일 검색, 책 제목과 유사한 이름 찾기)
  - 최근 파일 우선 선택 (여러 매칭이 있을 경우)
- **수정 파일**: `src/09_upload_from_metadata.py`

### Downloads 폴더 PNG 변환 스크립트 추가
- **추가 파일**: `convert_downloads_png.py`
  - Downloads 폴더의 PNG 파일을 JPG로 변환하여 롱폼 썸네일로 사용 가능하게 함
  - 4K 해상도 (3840x2160)로 리사이즈
  - 2MB 이하로 압축
  - output 폴더로 변환된 파일 저장
  - 언어 선택 기능 (한글/영어/둘 다)

## 2025-12-01

### 영상 구조 개선 및 기능 추가

#### 영상 구조 변경
- **새로운 영상 구조**: Summary → 3초 silence → NotebookLM Video → 3초 silence → Audio
- 각 섹션 사이에 3초 검은 화면(silence) 추가로 자연스러운 전환
- `src/03_make_video.py`의 `create_video` 함수 수정

#### Summary 오디오 음량 조정 기능
- Summary 오디오 음량 조정 기능 추가 (기본값: 1.2배, 20% 증가)
- `--summary-audio-volume` 파라미터로 조정 가능
- `src/03_make_video.py`, `src/10_create_video_with_summary.py` 수정

#### 썸네일 파일 이름 표준화
- 표준 네이밍 규칙 적용: `{책제목}_thumbnail_{lang}.jpg`
- 예시: `Sunrise_on_the_Reaping_thumbnail_ko.jpg`, `Sunrise_on_the_Reaping_thumbnail_en.jpg`

#### 메타데이터 자동 썸네일 경로 찾기
- 메타데이터 생성 시 썸네일 경로를 자동으로 찾아서 포함
- `find_thumbnail_for_video` 함수 추가
- `src/08_create_and_preview_videos.py`의 `save_metadata` 함수 개선

### YouTube 업로드 완료
- 업로드된 책: Sunrise on the Reaping
- 업로드된 영상 수: 2개
- [1] [English] Sunrise on the Reaping Book Review | [영어] 선라이즈 온 더 리핑 책 리뷰
  - URL: https://www.youtube.com/watch?v=fqhQF3uheEg
- [2] [한국어] 선라이즈 온 더 리핑 책 리뷰 | [Korean] Sunrise on the Reaping Book Review
  - URL: https://www.youtube.com/watch?v=vsqgSAgIdC4

### 문서 업데이트
- README.md 업데이트: 
  - 영상 구조 상세 설명 추가 (프로젝트 개요 섹션)
  - 오디오/비디오 파일 네이밍 규칙 명확화
  - 워크플로우에 파일 경로 및 형식 추가
  - 환경 변수 설명 추가 (PIXABAY_API_KEY 포함)
  - 파일 네이밍 규칙 요약 섹션 추가
  - 이미지 다운로드 소스 우선순위 설명 (Pexels → Pixabay → Unsplash)

### 파일 구조 정리
- 루트 디렉토리의 유틸리티 스크립트를 scripts/ 폴더로 이동
  - convert_downloads_png.py
  - convert_png_to_jpg.py
  - download_pexels_images.py
  - generate_summary_audio.py
- 이동된 스크립트의 import 경로 수정 (scripts/ 폴더에서 실행 가능하도록)
- .env.example에 PIXABAY_API_KEY 추가

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
  - 제목에 괄호가 포함된 경우 (예: "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)") 자동 처리

- **`src/09_upload_from_metadata.py`**:
  - 태그 검증 및 정리 기능 추가 (`_validate_and_clean_tags` 메서드)
  - YouTube 태그 규칙 준수 (최대 30자, 특수문자 제거)
  - 30자 초과 태그 자동 제거 및 경고 메시지 출력

- **`src/utils/translations.py`**:
  - "The Loneliness of Sonia and Sunny" 책 제목 매핑 추가
  - 영어/한글 제목 상호 변환 지원

#### 문서 업데이트
- README.md에 NotebookLM 비디오 업데이트 스크립트 사용법 추가
- README.md에 이미지 다운로드 개선 사항 설명 추가
- README.md에 메타데이터 timestamp 기능 설명 추가
- markdownlint 오류 48개 모두 수정 완료

### YouTube 업로드 완료
- **업로드된 책**: The Loneliness of Sonia and Sunny (소니아와 써니의 고독)
- **업로드된 영상 수**: 2개
- **[1] 영어 영상**: [English] The Loneliness of Sonia and Sunny Book Review | [영어] 소니아와 써니의 고독 책 리뷰
  - URL: https://www.youtube.com/watch?v=ysghav2OokY
  - 크기: 178.82 MB
  - Timestamp 포함: ✅ (0:00 - Summary, 1:27 - NotebookLM Detailed Analysis, 9:08 - Audio Review)
- **[2] 한국어 영상**: [한국어] 소니아와 써니의 고독 책 리뷰 | [Korean] The Loneliness of Sonia and Sunny Book Review
  - URL: https://www.youtube.com/watch?v=9ZAI9ZibZ_0
  - 크기: 155.25 MB
  - Timestamp 포함: ✅ (0:00 - 요약, 1:35 - NotebookLM 상세 분석, 8:18 - 오디오 리뷰)
- **태그 검증**: 30자 초과 태그 자동 제거 (44개 → 38개)
- **CSV 및 History 파일 자동 업데이트 완료**

## 2025-12-03

### YouTube 업로드 완료
- 업로드된 책: Guns_Germs_and_Steel_총_균_쇠_with_summary_en, Guns_Germs_and_Steel_총_균_쇠_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] Guns, Germs, and Steel Book Review | [영어] Guns, Germs, and Steel 책 리뷰
  - URL: https://www.youtube.com/watch?v=-YbD5f_e8SA
- [2] [한국어] Guns, Germs, and Steel 책 리뷰 | [Korean] Guns, Germs, and Steel Book Review
  - URL: https://www.youtube.com/watch?v=XhcYsMr4NuU

## 2025-12-03

### 크리스마스 캐럴 (A Christmas Carol) 영상 제작 완료
- **책 정보**: A Christmas Carol (크리스마스 캐럴) - 찰스 디킨스
- **작업 내용**:
  - Downloads 폴더에서 파일 준비 (오디오, 요약, 썸네일, 비디오)
  - 이미지 다운로드 (100개 무드 이미지, Pixabay API 사용)
  - 요약 텍스트 로드 (기존 파일 사용)
  - TTS 요약 오디오 생성 (한글/영어)
  - 한글/영어 영상 제작 (요약 + NotebookLM Video + 리뷰 오디오)
  - 썸네일 변환 (PNG → JPG, 4K 해상도, 2MB 이하 압축)
  - 메타데이터 생성 (한글/영어, timestamp 포함)
- **생성된 파일**:
  - 한글 영상: `A_Christmas_Carol_크리스마스_캐럴_review_with_summary_ko.mp4` (293MB, 약 24.6분)
  - 영어 영상: `A_Christmas_Carol_크리스마스_캐럴_review_with_summary_en.mp4` (320MB, 약 24.6분)
  - 한글 썸네일: `A_Christmas_Carol_크리스마스_캐럴_thumbnail_ko.jpg` (1.4MB)
  - 영어 썸네일: `A_Christmas_Carol_크리스마스_캐럴_thumbnail_en.jpg` (1.4MB)
  - 메타데이터: 한글/영어 각각 JSON 파일 생성
- **영상 구성**:
  - Summary (요약 오디오 + 이미지 슬라이드쇼, 약 2분 18초)
  - 3초 silence
  - NotebookLM Video (상세 분석, 약 11분 15초)
  - 3초 silence
  - Audio Review (리뷰 오디오 + 이미지 슬라이드쇼, 약 11분)
- **참고**: 영상은 생성되었으나 아직 YouTube에 업로드하지 않음

### YouTube 업로드 완료
- 업로드된 책: A_Christmas_Carol_크리스마스_캐럴_with_summary_en, A_Christmas_Carol_크리스마스_캐럴_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] A Christmas Carol Book Review | [영어] A Christmas Carol 책 리뷰
  - URL: https://www.youtube.com/watch?v=NmhhK8ZIjG4
- [2] [한국어] A Christmas Carol 책 리뷰 | [Korean] A Christmas Carol Book Review
  - URL: https://www.youtube.com/watch?v=ynHSTn_ZLJs

## 2025-12-03

### The Polar Express 영상 제작 및 YouTube 업로드 완료
- **책 정보**: The Polar Express (크리스 반 알스버그, 1985년 아동 도서)
- **작업 내용**:
  - Downloads 폴더에서 파일 준비 (오디오, 요약, 썸네일, 비디오)
  - 이미지 다운로드 (100개 무드 이미지, Pixabay API 사용)
  - 요약 텍스트 로드 (기존 파일 사용)
  - TTS 요약 오디오 생성 (한글/영어)
  - 한글/영어 영상 제작 (요약 + NotebookLM Video + 리뷰 오디오)
  - 썸네일 변환 (PNG → JPG, 4K 해상도, 2MB 이하 압축)
  - 메타데이터 생성 (한글/영어, timestamp 포함)
- **생성된 파일**:
  - 한글 영상: `The_Polar_Express_review_with_summary_ko.mp4` (285MB, 약 24분)
  - 영어 영상: `The_Polar_Express_review_with_summary_en.mp4` (283MB, 약 24분)
  - 한글 썸네일: `The_Polar_Express_thumbnail_ko.jpg` (1.9MB)
  - 영어 썸네일: `The_Polar_Express_thumbnail_en.jpg` (1.4MB)
  - 메타데이터: 한글/영어 각각 JSON 파일 생성
- **영상 구성**:
  - Summary (요약 오디오 + 이미지 슬라이드쇼, 약 3분)
  - 3초 silence
  - NotebookLM Video (상세 분석, 약 7-8분)
  - 3초 silence
  - Audio Review (리뷰 오디오 + 이미지 슬라이드쇼, 약 12-13분)
- **YouTube 업로드**:
  - 업로드된 영상 수: 2개
  - [1] [English] The Polar Express Book Review | [영어] The Polar Express 책 리뷰
    - URL: https://www.youtube.com/watch?v=RIgWEWUKMv0
  - [2] [한국어] The Polar Express 책 리뷰 | [Korean] The Polar Express Book Review
    - URL: https://www.youtube.com/watch?v=CSzIegUu-e8

### 코드 개선
- **`src/10_create_video_with_summary.py`**:
  - 오디오 파일 확장자 지원 확대 (`.mp4` 추가)
  - 기존: `.m4a`, `.mp3`, `.wav`만 지원
  - 개선: `.mp4` 확장자도 오디오 파일로 인식하도록 추가
  - Downloads 폴더에서 `.mp4` 형식의 오디오 파일도 자동 처리 가능

## 2025-12-04

### 사탄탱고(Sátántangó) 영상 제작 및 YouTube 업로드 완료
- **책 정보**: Sátántangó (사탄탱고) - 라슬로 크라스나호르카이
- **작업 내용**:
  - input 폴더에서 파일 준비 (오디오, 요약, 썸네일, 비디오)
  - 이미지 다운로드 (100개 무드 이미지, 기존 이미지 사용)
  - 요약 텍스트 로드 (기존 파일 사용)
  - TTS 요약 오디오 생성 (한글/영어)
  - 한글/영어 영상 제작 (요약 + NotebookLM Video + 리뷰 오디오)
  - 썸네일 변환 (PNG → JPG, 4K 해상도, 2MB 이하 압축)
  - 메타데이터 생성 (한글/영어, timestamp 포함)
- **생성된 파일**:
  - 한글 영상: `Sátántangó_사탄탱고_review_with_summary_ko.mp4` (255MB, 약 21.5분)
  - 영어 영상: `Sátántangó_사탄탱고_review_with_summary_en.mp4` (256MB, 약 21.5분)
  - 한글 썸네일: `Sátántangó_사탄탱고_thumbnail_ko.jpg` (1.6MB)
  - 영어 썸네일: `Sátántangó_사탄탱고_thumbnail_en.jpg` (1.6MB)
  - 메타데이터: 한글/영어 각각 JSON 파일 생성
- **영상 구성**:
  - Summary (요약 오디오 + 이미지 슬라이드쇼, 약 2분)
  - 3초 silence
  - NotebookLM Video (상세 분석, 약 6-7분)
  - 3초 silence
  - Audio Review (리뷰 오디오 + 이미지 슬라이드쇼, 약 12-13분)
- **YouTube 업로드**:
  - 업로드된 영상 수: 2개 (비공개)
  - [1] [English] Sátántangó Book Review | [영어] 사탄탱고 책 리뷰
    - URL: https://www.youtube.com/watch?v=jOSE-rVyZI0
  - [2] [한국어] 사탄탱고 책 리뷰 | [Korean] Sátántangó Book Review
    - URL: https://www.youtube.com/watch?v=pH7vLSLrSnw

### 코드 개선 및 버그 수정

#### 제목 형식 수정
- **문제**: 영어 제목에 한글 제목이 표시되지 않는 문제 (예: "[English] Sátántangó Book Review | [영어] Sátántangó 책 리뷰")
- **해결**: 
  - `generate_title` 함수 개선: 괄호에서 한글 제목 자동 추출 기능 추가
  - 영어 제목에는 한글 제목, 한글 제목에는 영어 제목이 표시되도록 수정
  - 예: "[English] Sátántangó Book Review | [영어] 사탄탱고 책 리뷰"
- **수정 파일**: `src/08_create_and_preview_videos.py`, `src/utils/translations.py`
- **추가 매핑**: "Sátántangó" → "사탄탱고" 매핑 추가

#### 책 소개(description) 가져오기 로직 개선
- **문제**: book_info.json에 description이 없으면 메타데이터에 책 소개가 포함되지 않음
- **해결**: 
  - `load_book_info` 함수 개선: description이 없거나 빈 문자열이면 Google Books API에서 다시 가져오기
  - 메타데이터 생성 시 자동으로 description 확인 및 업데이트
- **수정 파일**: `src/utils/file_utils.py`, `src/08_create_and_preview_videos.py`

#### Downloads 폴더를 input 폴더로 변경
- **변경 사항**: 모든 스크립트에서 `~/Downloads` 폴더 대신 프로젝트 루트의 `input/` 폴더 사용
- **수정된 스크립트**:
  - `scripts/prepare_files_from_downloads.py`: input 폴더에서 파일 찾기
  - `scripts/update_notebooklm_video.py`: input 폴더에서 비디오 파일 찾기
  - `scripts/convert_downloads_png.py`: input 폴더에서 PNG 파일 찾기
  - `scripts/run_full_pipeline_from_downloads.py`: input 폴더 기반 파이프라인 실행
- **비디오 파일 패턴 매칭 개선**: 
  - 점(.) 형식도 지원: `{prefix}_video.en.mp4`, `{prefix}_video.kr.mp4`
  - 기존 언더스코어 형식도 계속 지원: `{prefix}_video_en.mp4`, `{prefix}_video_kr.mp4`

#### 문서 업데이트
- README.md에 input 폴더 사용법 반영
- 모든 "Downloads 폴더" 언급을 "input 폴더"로 변경

## 2025-12-05

### YouTube 업로드 완료
- 업로드된 책: 연금술사_with_summary_ko, 연금술사_with_summary_en
- 업로드된 영상 수: 2개
- [1] [English] The Alchemist Book Review | [영어] 연금술사 책 리뷰
  - URL: https://www.youtube.com/watch?v=kbFDkhoQFq4
- [2] [한국어] 연금술사 책 리뷰 | [Korean] The Alchemist Book Review
  - URL: https://www.youtube.com/watch?v=Iju325kSvSI
## 2025-12-06

### 스티브 잡스(Steve Jobs) 영상 제작 및 YouTube 업로드 완료
- **책 정보**: 스티브 잡스 (Steve Jobs) - 월터 아이작슨 (Walter Isaacson)
- **작업 내용**:
  - input 폴더에서 파일 준비 (오디오, 요약, 썸네일, 비디오)
  - 이미지 다운로드 (100개 무드 이미지, Pixabay API 사용)
  - 책 정보 다운로드 (Google Books API, book_info.json 생성)
  - 요약 텍스트 로드 (기존 파일 사용)
  - 롱폼 TTS 오디오 생성 (한글/영어, tts-1-hd 모델 사용)
  - 한글/영어 영상 제작 (요약 + NotebookLM Video + 리뷰 오디오)
  - 썸네일 변환 (PNG → JPG, 4K 해상도, 2MB 이하 압축)
  - 메타데이터 생성 (한글/영어, timestamp 포함)
- **생성된 파일**:
  - 한글 영상: `스티브_잡스_review_with_summary_ko.mp4` (907MB, 약 23.76분)
  - 영어 영상: `스티브_잡스_review_with_summary_en.mp4` (776MB, 약 20.29분)
  - 한글 롱폼 오디오: `스티브_잡스_summary_ko.mp3` (nova 음성)
  - 영어 롱폼 오디오: `스티브_잡스_summary_en.mp3` (alloy 음성)
  - 한글 썸네일: `스티브_잡스_thumbnail_ko.jpg`
  - 영어 썸네일: `스티브_잡스_thumbnail_en.jpg`
  - 메타데이터: 한글/영어 각각 JSON 파일 생성
- **영상 구성**:
  - Summary (요약 오디오 + 이미지 슬라이드쇼, 한글: 127초, 영문: 116초)
  - 3초 silence
  - NotebookLM Video (상세 분석, 한글: 476초, 영문: 392초)
  - 3초 silence
  - Audio Review (리뷰 오디오 + 이미지 슬라이드쇼, 한글: 816초, 영문: 703초)
- **YouTube 업로드**:
  - 업로드된 영상 수: 2개 (비공개)
  - [1] [English] Steve Jobs Book Review | [영어] 스티브 잡스 책 리뷰
    - URL: https://www.youtube.com/watch?v=d2PWE8z_44s
  - [2] [한국어] 스티브 잡스 책 리뷰 | [Korean] Steve Jobs Book Review
    - URL: https://www.youtube.com/watch?v=Qms01mzXrpk

### 메타데이터 개선

#### 작가 이름 표시 언어 분리
- **문제**: 메타데이터에서 작가 이름이 한글/영어 모두 표시되어 중복되거나 잘못 표시되는 문제
  - 예: "✍️ Author: 월터아이작슨 | ✍️ 작가: 월터아이작슨"
- **해결**:
  - 한글 메타데이터: 한글 작가 이름만 표시 (`✍️ 작가: 월터 아이작슨`)
  - 영문 메타데이터: 영문 작가 이름만 표시 (`✍️ Author: Walter Isaacson`)
  - `_generate_description_ko`: 한글 작가 이름만 표시하도록 수정
  - `_generate_description_en`: 영문 작가 이름만 표시하도록 수정
  - `_generate_description_en_with_ko`: 한글 부분은 한글만, 영어 부분은 영어만 표시하도록 수정
  - `book_info`가 없을 때도 `author` 파라미터를 올바르게 처리하도록 개선
- **수정 파일**: `src/08_create_and_preview_videos.py`

#### 책 소개(description) 언어 분리 개선
- **문제**: 한글 메타데이터에 영문 책 소개가 포함되고, 영문 메타데이터에 한글 책 소개가 포함되는 문제
- **해결**:
  - 한글 메타데이터: 한글 description만 사용 (영어 description 제외)
  - 영문 메타데이터: 영문 description만 사용 (한글 description 제외)
  - `is_english_title` 함수를 사용하여 description의 언어를 판단
  - 처음 100자를 확인하여 언어 판단
- **수정 파일**: `src/08_create_and_preview_videos.py`

### 번역 매핑 추가
- **`src/utils/translations.py`**:
  - 책 제목 매핑 추가:
    - "스티브 잡스" → "Steve Jobs"
    - "스티브_잡스" → "Steve Jobs"
  - 작가 이름 매핑 추가:
    - "월터 아이작슨" → "Walter Isaacson"
    - "Walter Isaacson" → "Walter Isaacson"

## 2025-12-07

### YouTube 업로드 완료
- 업로드된 책: 어린왕자_with_summary_en, 어린왕자_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] The Little Prince Book Review | [영어] 어린왕자 책 리뷰
  - URL: https://www.youtube.com/watch?v=tbgQklS3KvQ
- [2] [한국어] 어린왕자 책 리뷰 | [Korean] The Little Prince Book Review
  - URL: https://www.youtube.com/watch?v=txZ71km8Dxc

## 2025-12-08

### YouTube 업로드 완료
- 업로드된 책: 내_이름은_빨강_with_summary_en, 내_이름은_빨강_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] My Name is Red Book Review | [영어] 내 이름은 빨강 책 리뷰
  - URL: https://www.youtube.com/watch?v=3YkuMcVDn0w
- [2] [한국어] 내 이름은 빨강 책 리뷰 | [Korean] My Name is Red Book Review
  - URL: https://www.youtube.com/watch?v=42v-dRrYjLQ

## 2025-12-08

### 돈의 심리학 (The Psychology of Money) 영상 제작 및 업로드

#### 번역 매핑 추가
- **`src/utils/translations.py`**:
  - "돈의 심리학" → "The Psychology of Money" 매핑 추가
  - "모건 하우설" → "Morgan Housel" 매핑 추가
  - 한글/영문 제목 상호 변환 지원

#### 영상 제작 완료
- 이미지 다운로드: 무드 이미지 100개 다운로드 완료
- TTS 오디오 생성: 한글/영문 롱폼 오디오 생성 완료
- 영상 제작: 한글/영문 영상 생성 완료
  - 한글 영상: `output/돈의_심리학_review_with_summary_ko.mp4` (1044.36 MB)
  - 영문 영상: `output/돈의_심리학_review_with_summary_en.mp4` (755.86 MB)
- 메타데이터 생성: YouTube 업로드용 메타데이터 생성 완료

#### YouTube 업로드 완료
- 업로드된 책: 돈의_심리학_with_summary_en, 돈의_심리학_with_summary_ko
- 업로드된 영상 수: 2개 (비공개)
- [1] [English] The Psychology of Money Book Review | [영어] 돈의 심리학 책 리뷰
  - URL: https://www.youtube.com/watch?v=CeA8OMkzeis
- [2] [한국어] 돈의 심리학 책 리뷰 | [Korean] The Psychology of Money Book Review
  - URL: https://www.youtube.com/watch?v=NLRoYFn_ahs

## 2025-12-09

### Git 관련 작업
- **커밋 및 푸시**:
  - 커밋 해시: `7d713ce`
  - 메시지: "docs: 돈의 심리학 영상 제작 및 업로드 완료"
  - `origin/main`으로 변경사항 푸시 완료
  - 업데이트된 파일:
    - `history.md`: "돈의 심리학" 영상 제작 및 업로드 내역 추가
    - `src/utils/translations.py`: "돈의 심리학" 및 "모건 하우설" 번역 매핑 추가

## 2025-12-09

### 작은 아씨들 (Little Women) 영상 제작 완료

- **번역 매핑 추가**: `src/utils/translations.py`에 "작은 아씨들" 및 "루이자 메이 올콧" 매핑 추가
- **영상 제작 완료**:
  - 한글 영상: `output/작은_아씨들_review_with_summary_ko.mp4` (926MB)
  - 영문 영상: `output/작은_아씨들_review_with_summary_en.mp4` (821MB)
- **메타데이터 생성 완료**:
  - 한글: `작은_아씨들_review_with_summary_ko.metadata.json`
  - 영문: `작은_아씨들_review_with_summary_en.metadata.json`

## 2025-12-10

### YouTube 업로드 완료
- 업로드된 책: 인간관계론_with_summary_ko, 인간관계론_with_summary_en
- 업로드된 영상 수: 2개
- [1] [English] How to Win Friends and Influence People Book Review | [영어] 인간관계론 책 리뷰
  - URL: https://www.youtube.com/watch?v=fnzJ5zVk0Ls
- [2] [한국어] 인간관계론 책 리뷰 | [Korean] How to Win Friends and Influence People Book Review
  - URL: https://www.youtube.com/watch?v=0q7zOY_zbKU

## 2025-12-11

### 사마천의 사기 롱폼 영상 제작 완료
- **책 제목**: 사기 (Records of the Grand Historian)
- **저자**: 사마천 (Sima Qian)
- **생성된 파일**:
  - 영상: `output/사기_review_with_summary_ko.mp4` (835.19 MB), `output/사기_review_with_summary_en.mp4` (909.21 MB)
  - 썸네일: `output/사기_thumbnail_ko.jpg`, `output/사기_thumbnail_en.jpg`
  - 메타데이터: `사기_review_with_summary_ko.metadata.json`, `사기_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료

### 번역 매핑 추가
- **`src/utils/translations.py`**:
  - "사기" → "Records of the Grand Historian" / "Shiji" 매핑 추가
  - "사마천" → "Sima Qian" 매핑 추가
  - 한글/영문 양방향 번역 지원

### 코드 개선: longform/summary 파일 중복 문제 해결
- **문제**: TTS 오디오 생성 시 `longform` 이름으로 생성했지만, 영상 제작 스크립트는 `summary` 이름만 인식하여 중복 생성 발생
- **해결**:
  - **`src/10_create_video_with_summary.py`**:
    - `summary`와 `longform` 파일 모두 인식하도록 수정
    - `longform` 파일 발견 시 자동으로 `summary`로 이름 변경 (일관성 유지)
  - **`src/08_create_and_preview_videos.py`**:
    - 메타데이터 생성 시 `summary`와 `longform` 파일 모두 확인하도록 수정
- **효과**: 중복 생성 방지 및 파일명 일관성 유지

### YouTube 업로드 완료
- 업로드된 책: 사기 (Records of the Grand Historian)
- 업로드된 영상 수: 2개 (비공개)
- [1] [English] Records of the Grand Historian Book Review | [영어] 사기 책 리뷰
  - URL: https://www.youtube.com/watch?v=vraC0u4ybkM
- [2] [한국어] 사기 책 리뷰 | [Korean] Records of the Grand Historian Book Review
  - URL: https://www.youtube.com/watch?v=P-75PxfYUX0

### YouTube 채널 선택 기능 추가
- **문제**: 같은 계정의 다른 채널로 업로드하려면 채널 ID가 필요
- **해결**:
  - **`src/09_upload_from_metadata.py`**:
    - `--channel-id` 명령줄 인자 추가
    - `YOUTUBE_CHANNEL_ID` 환경 변수 지원
    - book summary 채널 ID (`UCxOcO_x_yW6sfg_FPUQVqYA`) 기본값으로 설정
    - `upload_video()` 메서드에 `channel_id` 파라미터 추가
    - 업로드 시 채널 ID를 request body에 포함
  - **`scripts/get_youtube_refresh_token.py`** (신규):
    - OAuth2 인증을 통해 refresh token 생성 스크립트 추가
    - 특정 채널에 대한 refresh token 생성 지원
    - `client_secret.json` 파일을 사용하여 OAuth 플로우 실행
- **효과**: 같은 계정의 여러 채널 중 원하는 채널로 업로드 가능
