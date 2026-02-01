# BookReview-AutoMaker 프로젝트 TODO

## 🚧 진행 중인 작업

_현재 진행 중인 작업이 없습니다_

## 📋 다음 작업 (우선순위별)

### 🔴 높은 우선순위

_현재 높은 우선순위 작업이 없습니다_

### 🟡 중간 우선순위

- [x] CI/CD 파이프라인 구축 (선택사항)

### 🟢 낮은 우선순위

_현재 낮은 우선순위 작업이 없습니다_

## 🐛 알려진 이슈

_현재 알려진 이슈가 없습니다_

## 🔮 향후 계획

### Phase 8: 품질 개선 및 최적화

- [x] 영상 품질 향상 (해상도, 비트레이트 최적화)
- [x] 처리 속도 최적화 (병렬 처리, 캐싱)
- [x] 에러 핸들링 개선 (재시도 로직, 상세한 에러 메시지)
- [x] 로깅 시스템 개선 (구조화된 로그, 로그 레벨 관리)
  - [x] 로깅 유틸리티 모듈 생성 (`src/utils/logger.py`)
  - [x] 로그 레벨 관리 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - [x] 파일 로그와 콘솔 로그 분리
  - [x] 로그 파일 로테이션 (크기 기반, 최대 10MB, 5개 백업)
  - [x] 환경 변수로 로그 레벨 설정 가능 (`LOG_LEVEL`)
  - [x] 컬러 콘솔 출력 및 이모지 지원
  - [ ] 주요 스크립트에 로깅 시스템 적용 (점진적 업데이트)

### Phase 9: 분석 및 모니터링

- [x] YouTube Analytics API 연동
  - [x] YouTube Analytics API v2 연동 모듈 생성 (`src/15_youtube_analytics.py`)
  - [x] 채널 및 영상 메트릭 수집 기능 구현
  - [x] 조회수, 좋아요, 댓글, 시청 시간 등 메트릭 수집
  - [x] 메트릭 데이터를 JSON/CSV 형식으로 저장
  - [x] 주간/월간 리포트 자동 생성 (Markdown 형식)
- [x] 성능 대시보드 구축
  - [x] HTML 기반 대시보드 생성 (`src/16_dashboard.py`)
  - [x] 채널 통계 카드 (총 영상 수, 조회수, 좋아요, 댓글 수 등)
  - [x] 조회수 상위 10개 영상 테이블
  - [x] 조회수 분포 차트 (Chart.js 사용)
  - [x] 최근 업로드 영상 목록
  - [x] Analytics 코드 점검 및 개선 (스코프 문제 처리)

### Phase 10: 콘텐츠 다양화

- [ ] 다양한 영상 스타일 템플릿 추가
- [x] 배경 음악 자동 추가 기능
  - [x] 일당백 스타일 영상에 배경음악 자동 탐지 및 다운로드 기능 추가
  - [x] Pixabay Music에서 자동 다운로드 기능 통합
  - [x] 인포그래픽 클립에 배경음악 자동 적용
- [x] 챕터 마커 자동 생성
  - [x] YouTube 챕터 마커 자동 생성 기능 구현
  - [x] 메타데이터의 timestamp를 YouTube 챕터 형식으로 변환
  - [x] description 맨 앞에 챕터 마커 자동 추가
- [x] 영상 시각화 개선 (Summary+Video 파이프라인)
  - [x] 동적 자막(Kinetic Typography): 키워드 추출 + Whisper 타이밍, 팝 효과
  - [x] 파형(Waveform) 시각화: 오디오 스펙트럼 하단 시각화(실시간 스크롤)
  - [x] Pexels API 푸티지: 키워드 기반 관련 영상 검색·다운로드 (`PEXELS_API_KEY` 사용)
- [x] 제목 전략 개선: AI 언급 대신 가치·인간적 호기심 강조 (`src/utils/title_generator.py`)
- [x] 제목 부제(괄호) SEO 키워드 자동 생성 (장르 기반 템플릿)
- [x] 제목 100자 제한 강화: 부제 우선 축소 후 절단
- [x] 고정 댓글 활용: 챕터 타임스탬프 + 참여 유도 질문 자동 생성, 업로드 시 댓글 등록 (`src/utils/pinned_comment.py`, 수동 고정은 YouTube UI에서)
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

- [x] NotebookLM 사용법 문서화 (README.md에 통합)

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

### Phase 8: 파이프라인 표준화 및 이미지 다양성 개선 (완료: 2025-12)

- [x] 언어 접미사 표준화 (`ko` -> `kr`) 및 영문 표준 제목 기반 디렉토리 통합
- [x] 이미지 다양성 향상 (AI 키워드 파싱 버그 수정, Fallback 리스트 확장)
- [x] CI 테스트 안정화 (`pytest.ini` 설정) 및 `.cursorrules` 검증 프로세스 추가
- [x] 유튜브 업로드 프로세스 표준화 대응 및 썸네일 용량 최적화 (`.jpg` 변환)

### 프로젝트 관리 (완료: 2025-11)

- [x] 프로젝트 문서화 ([README](README.md), [TODO](TODO.md), [HISTORY](history.md), [RULES](.cursorrules))
- [x] Git 자동 커밋/푸시 설정
- [x] 커밋 전 필수 작업 규칙 추가 ([.cursorrules](.cursorrules))
- [x] TODO.md에서 history 성 데이터 제거
  - "최근 완료 작업 (최근 2주)" 섹션 전체 제거
  - TODO.md는 현재 작업과 향후 계획만 관리하도록 정리
- [x] 코드 리팩토링 및 파일 정리
  - src/09_text_to_speech.py 삭제 및 src/09_text_to_speech_multi.py로 통합
  - 민감한 인증 정보들을 secrets/ 폴더로 이동 및 관리
  - 불필요한 테스트 스크립트 삭제

---

## 📚 참고 문서

- [README.md](README.md) - 프로젝트 개요 및 사용법
- [HISTORY.md](history.md) - 상세 작업 이력
- [.cursorrules](.cursorrules) - 프로젝트 규칙 및 가이드라인
- [docs/URL_COLLECTION_PROMPT.md](docs/URL_COLLECTION_PROMPT.md) - URL 수집 프롬프트
