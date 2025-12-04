# BookReview-AutoMaker 프로젝트 TODO

## 🚧 진행 중인 작업
_현재 진행 중인 작업이 없습니다_

## 📋 다음 작업 (우선순위별)

### 🔴 높은 우선순위
_현재 높은 우선순위 작업이 없습니다_

### 🟡 중간 우선순위
- [ ] CI/CD 파이프라인 구축 (선택사항)

### 🟢 낮은 우선순위
_현재 낮은 우선순위 작업이 없습니다_

## 🐛 알려진 이슈
_현재 알려진 이슈가 없습니다_

## 🔮 향후 계획

### Phase 8: 품질 개선 및 최적화
- [ ] 영상 품질 향상 (해상도, 비트레이트 최적화)
- [ ] 처리 속도 최적화 (병렬 처리, 캐싱)
- [ ] 에러 핸들링 개선 (재시도 로직, 상세한 에러 메시지)
- [ ] 로깅 시스템 개선 (구조화된 로그, 로그 레벨 관리)

### Phase 9: 분석 및 모니터링
- [ ] YouTube Analytics API 연동
- [ ] 조회수, 좋아요, 댓글 등 메트릭 수집
- [ ] 성능 대시보드 구축
- [ ] 주간/월간 리포트 자동 생성

### Phase 10: 콘텐츠 다양화
- [ ] 다양한 영상 스타일 템플릿 추가
- [ ] 배경 음악 자동 추가 기능
- [ ] 챕터 마커 자동 생성
- [ ] 다국어 지원 확대 (일본어, 중국어 등)

---

## ✅ 완료된 Phase

### Phase 1: 자료 수집 자동화 (완료: 2025-11)
- [x] 책 제목 입력 (단일/일괄 처리 지원)
- [x] URL 탐색 (위키백과, 온라인 서점, 뉴스 리뷰 타겟)
- [x] 텍스트 파일 출력 (NotebookLM용)
- [x] 표지 이미지 다운로드 ([Google Books API](src/01_download_cover_image.py))
- [x] 무드 이미지 다운로드 ([Pexels/Unsplash API](src/02_download_mood_images.py), 5~10장)
- [x] 가상환경 설정 및 패키지 설치
- [x] 실행 스크립트 작성

### Phase 2: NotebookLM 오디오 생성 (완료: 2025-11)
- [x] 사용자 가이드 작성 ([NOTEBOOKLM_GUIDE.md](NOTEBOOKLM_GUIDE.md))
- [x] NotebookLM 사용법 문서화

### Phase 3: 이미지 자산 확보 (완료: 2025-11)
- [x] 표지 이미지: Google Books API로 고화질 표지 다운로드
- [x] 무드 이미지: 키워드 기반으로 5~10장 다운로드
- [x] 저장: `assets/images/{책제목}/` 폴더에 정리

### Phase 4: 영상 합성 및 편집 (완료: 2025-11)
- [x] 오디오 로드: `assets/audio/`의 오디오 파일 로드
- [x] 이미지 시퀀스: 오디오 길이에 맞춰 이미지 배분
- [x] Ken Burns 효과: 줌인/패닝 효과 구현
- [x] 전환 효과: 이미지 간 페이드 효과
- [x] Summary audio와 Review audio 자동 연결
- [x] 자막 (옵션): OpenAI Whisper로 자막 추출 및 오버레이
- [x] 렌더링: 1080p, 30fps MP4 출력

### Phase 5: 메타데이터 및 썸네일 (완료: 2025-11)
- [x] en/kr 언어별 메타데이터 자동 생성 (title, description, tags)
- [x] 메타데이터 JSON 파일 저장
- [x] 썸네일 자동 생성 (한글/영문 버전)
- [x] 썸네일 업로드 기능

### Phase 6: 완전 자동화 파이프라인 (완료: 2025-11)
- [x] Summary/Review 오디오 자동 탐지
- [x] en/kr 언어별 영상 자동 생성 (summary 포함)
- [x] en/kr 언어별 메타데이터 자동 생성 및 저장
- [x] en/kr 언어별 썸네일 자동 생성
- [x] 통합 파이프라인 스크립트 ([13_complete_pipeline.py](src/13_complete_pipeline.py))
- [x] 실행 스크립트 ([run_complete_pipeline.sh](run_complete_pipeline.sh))

### Phase 7: YouTube 업로드 (완료: 2025-11)
- [x] 메타데이터 기반 자동 업로드
- [x] 썸네일 자동 업로드
- [x] 업로드 로그 관리 (JSON, CSV, TXT)
- [x] CSV 파일 자동 업데이트

### 프로젝트 관리 (완료: 2025-11)
- [x] 프로젝트 문서화 ([README](README.md), [TODO](TODO.md), [HISTORY](history.md), [RULES](.cursorrules))
- [x] Git 자동 커밋/푸시 설정
- [x] 커밋 전 필수 작업 규칙 추가 ([.cursorrules](.cursorrules))

---

## 📅 최근 완료 작업 (최근 2주)

### 2025-12-04

#### 프로젝트 관리
- [x] **todo 파일을 TODO.md로 변경**
  - todo 파일을 TODO.md로 표준화
  - .cursorrules에서 "todo 파일"을 "TODO.md 파일"로 업데이트
  - Git에서 todo 파일 삭제 및 TODO.md 추가
- [x] **.cursorrules 최신화 및 정리**
  - 불필요한 중복 내용 제거 (문서 업데이트 규칙 섹션 통합)
  - README.md와 TODO.md 항상 현행화 및 커밋/푸시 규칙 추가
  - README.md와 TODO.md는 변경사항이 있으면 반드시 커밋/푸시하도록 명시

#### 영상 제작
- [x] **사탄탱고(Sátántangó)** 영상 제작 및 YouTube 업로드 완료
  - 라슬로 크라스나호르카이의 걸작 사탄탱고 영상 제작
  - 한글/영어 영상 생성 (요약 포함, 각 약 21.5분)
  - 이미지 다운로드 (100개 무드 이미지)
  - 썸네일 생성 및 변환 (PNG → JPG, 4K 해상도)
  - 메타데이터 생성 (한글/영어)
  - YouTube 비공개 업로드 완료 (한글/영어 2개)

#### 기능 개선
- [x] **제목 형식 수정 및 개선**
  - 괄호에서 한글 제목 자동 추출 기능 추가
  - 영어 제목에는 한글 제목, 한글 제목에는 영어 제목 표시 형식으로 수정
  - Sátántangó → 사탄탱고 매핑 추가
- [x] **책 소개(description) 가져오기 로직 개선**
  - `load_book_info` 함수 개선: description이 없으면 Google Books API에서 다시 가져오기
  - 메타데이터 생성 시 자동으로 description 확인 및 업데이트
- [x] **Downloads 폴더를 input 폴더로 변경**
  - 모든 스크립트에서 Downloads 폴더 대신 input 폴더 사용하도록 변경
  - `prepare_files_from_downloads.py`, `update_notebooklm_video.py`, `convert_downloads_png.py`, `run_full_pipeline_from_downloads.py` 수정
  - 비디오 파일 패턴 매칭 개선 (점(.) 형식도 지원: `satan_video.en.mp4`)

### 2025-12-03

#### 영상 제작
- [x] **크리스마스 캐럴 (A Christmas Carol)** 영상 제작 완료
  - 찰스 디킨스의 불멸의 고전 크리스마스 캐럴 영상 제작
  - 한글/영어 영상 생성 (요약 포함, 각 약 24.6분)
  - 이미지 다운로드 (100개 무드 이미지)
  - 썸네일 생성 및 변환 (PNG → JPG, 4K 해상도)
  - 메타데이터 생성 (한글/영어)
- [x] **The Polar Express** 영상 제작 및 YouTube 업로드 완료
  - 크리스 반 알스버그의 1985년 아동 도서 The Polar Express 영상 제작
  - 한글/영어 영상 생성 (요약 포함, 각 약 24분)
  - 이미지 다운로드 (100개 무드 이미지)
  - 썸네일 생성 및 변환 (PNG → JPG, 4K 해상도)
  - 메타데이터 생성 (한글/영어)
  - YouTube 업로드 완료 (한글/영어 2개)

#### 기능 개선
- [x] **영상 생성 스크립트 개선** (.mp4 확장자 지원 추가)
  - `src/10_create_video_with_summary.py`에 .mp4 확장자 지원 추가
  - 오디오 파일이 .mp4 형식일 때도 자동 인식

### 2025-12-02

#### 스크립트 추가
- [x] NotebookLM 비디오 업데이트 스크립트 추가 ([scripts/update_notebooklm_video.py](scripts/update_notebooklm_video.py))

#### 기능 개선
- [x] 이미지 다운로드 개선 (기존 이미지 100개 이상이면 건너뛰기)
- [x] 이미지 리사이즈 오류 수정 (numpy import, RGB 변환 강화)
- [x] 메타데이터 timestamp 기능 추가 (한국어/영어 모두)
- [x] YouTube 업로드 태그 검증 기능 추가 (30자 초과 태그 자동 제거)

#### 영상 제작
- [x] **The Loneliness of Sonia and Sunny** 영상 제작 및 YouTube 업로드 (한글/영어 2개)

#### 문서화
- [x] README.md에 빠른 시작 가이드 섹션 추가
- [x] 문서 업데이트 (history, README.md)

### 2025-12-01

#### 기능 개선
- [x] 썸네일 생성 방식 변경 (Nano Banana PNG 파일 기반 처리)
- [x] 메타데이터 제목 형식 변경 (일당백 스타일, Auto-Generated 제거)
- [x] PNG to JPG 변환 스크립트 추가
- [x] 썸네일 검색 로직 개선 (다양한 파일명 패턴 지원)
- [x] Downloads 폴더 PNG 변환 스크립트 추가 ([convert_downloads_png.py](scripts/convert_downloads_png.py))
- [x] 영상 구조 개선: Summary → 3초 silence → NotebookLM Video → 3초 silence → Audio
- [x] Summary 오디오 음량 조정 기능 추가 (기본값 1.2배)
- [x] 썸네일 파일 이름 표준화 (`{책제목}_thumbnail_{lang}.jpg`)
- [x] 메타데이터 자동 썸네일 경로 찾기 기능 추가
- [x] CSV 업데이트 로직 개선 (`_review_with_summary` 패턴 지원)

#### 영상 제작
- [x] **불안 세대** 영상 YouTube 업로드 (한글/영어 2개)
- [x] **선라이즈 온 더 리핑** 영상 재생성 및 YouTube 업로드 (한글/영어 2개)

#### 프로젝트 구조
- [x] 파일 구조 정리 (루트 디렉토리 스크립트를 `scripts/` 폴더로 이동)
- [x] `.env.example`에 `PIXABAY_API_KEY` 추가

### 2025-11-30

#### 영상 제작
- [x] **동물농장** 한글 영상 재생성 (요약 포함)
- [x] **햄릿** 영상 제작 (한글/영어, 요약 포함)
  - 썸네일 생성 및 PNG 파일로 교체 (2MB 이하 압축)
  - YouTube 업로드 (2개 영상)
- [x] **벅아이(Buckeye)** 영상 제작 (한글/영어, 요약 포함)
  - 썸네일 생성 및 PNG 파일로 교체 (2MB 이하 압축)
  - YouTube 업로드 (2개 영상)
  - CSV에 벅아이 정보 추가
- [x] **선라이즈 온 더 리핑(Sunrise on the Reaping)** 영상 제작 (한글/영어, 요약 포함)
  - 썸네일 생성 및 PNG 파일로 교체 (2MB 이하 압축)
  - YouTube 업로드 (2개 영상)
  - CSV에 선라이즈 온 더 리핑 정보 추가

#### 기능 개선
- [x] 태그 생성 기능 개선 (추천 기관 목록 추가)
- [x] 메타데이터 생성 로직 개선 (한글/영어 제목 혼용 문제 해결)

---

## 📚 참고 문서
- [README.md](README.md) - 프로젝트 개요 및 사용법
- [HISTORY.md](history.md) - 상세 작업 이력
- [NOTEBOOKLM_GUIDE.md](NOTEBOOKLM_GUIDE.md) - NotebookLM 사용 가이드
- [.cursorrules](.cursorrules) - 프로젝트 규칙 및 가이드라인
- [docs/URL_COLLECTION_PROMPT.md](docs/URL_COLLECTION_PROMPT.md) - URL 수집 프롬프트
