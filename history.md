# BookReview-AutoMaker 프로젝트 히스토리

## 2026-01-19

### 칼 세이건 코스모스 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 칼 세이건 "코스모스" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 영상과 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - Crossfade 효과 및 배경음악 추가
  - YouTube 업로드 완료 (비공개)
- **생성된 영상**:
  - 한글: `output/Cosmos_full_episode_ko.mp4` (582MB, 15.46분)
  - 영문: `output/Cosmos_full_episode_en.mp4` (463MB, 14.60분)
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 코스모스 책 리뷰 | [Korean] Cosmos Book Review
    - URL: https://www.youtube.com/watch?v=YzI7EZmaOc8
  - [2] [English] Cosmos Book Review | [영어] 코스모스 책 리뷰
    - URL: https://www.youtube.com/watch?v=L1WYsstVHN8
- **작업 파일**:
  - `assets/notebooklm/Cosmos/ko/`: 한글 Part 1, Part 2 영상 및 인포그래픽
  - `assets/notebooklm/Cosmos/en/`: 영문 Part 1, Part 2 영상 및 인포그래픽
  - `output/Cosmos_full_episode_ko.metadata.json`: 한글 메타데이터
  - `output/Cosmos_full_episode_en.metadata.json`: 영문 메타데이터
  - `output/Cosmos_thumbnail_ko.jpg`, `output/Cosmos_thumbnail_en.jpg`: 썸네일

### 모건 하우절 - 불변의 법칙 (Same as Ever) summary+video 스타일 영상 제작
- **작업 내용**:
  - 모건 하우절 "불변의 법칙 (Same as Ever)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - Summary + NotebookLM Video 형태로 영상 생성 (OpenAI TTS 사용)
  - 한글/영문 메타데이터 생성 완료
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "불변의 법칙" ↔ "Same as Ever", "모건 하우절" ↔ "Morgan Housel" 매핑 추가
- **생성된 영상**:
  - 한글: `output/Same_as_Ever_kr.mp4` (12.35분)
  - 영문: `output/Same_as_Ever_en.mp4` (10.28분)
- **수정된 파일**:
  - `src/utils/translations.py`: 불변의 법칙, 모건 하우절 번역 매핑 추가
  - `history.md`: 작업 내용 업데이트

## 2026-01-19

### 프로젝트 구조 리팩토링 및 환경 설정 관리 개선
- **작업 내용**:
  - 프로젝트의 보안성과 유지보수성을 높이기 위해 불필요한 파일을 정리하고 자격 증명 관리 방식을 개선했습니다.
  - 다중 엔진 TTS 기능을 `src/09_text_to_speech_multi.py`로 단일화하고 기존 중복 스크립트를 제거했습니다.
  - 모든 문서를 최신 코드 구조에 맞게 업데이트하여 사용자 편의성을 높였습니다.
- **주요 수정사항**:
  - **자격 증명 관리**:
    - `secrets/` 디렉토리를 생성하여 `client_secret.json`, `credentials.json`, `google-cloud-tts-key.json` 등 민감한 파일을 이동.
    - `.gitignore`를 업데이트하여 `secrets/` 폴더를 Git 추적에서 제외.
  - **스크립트 통합**:
    - `src/09_text_to_speech.py` 삭제 및 `src/09_text_to_speech_multi.py`로 모든 TTS 작업 통합.
    - `scripts/generate_summary_audio.py`가 `MultiTTSEngine`을 사용하도록 업데이트.
  - **문서화 업데이트**:
    - `README.md`: 프로젝트 구조, 환경 변수, OAuth 설정 등 최신 정보 반영.
    - `TODO.md`: 완료된 리팩토링 항목 반영 및 참고 문서 정리.
    - `.env.example`: `OPENROUTER_API_KEY` 추가 및 자격 증명 경로 안내 업데이트.
  - **기타 정리**:
    - 사용하지 않는 테스트 스크립트 삭제 (`verify_openai_api.py`, `test_logging.py`, `test_analytics.py`).
- **수정된 파일**:
  - `README.md`, `TODO.md`, `.env.example`, `.gitignore`, `history.md`
  - `src/09_text_to_speech_multi.py`, `scripts/generate_summary_audio.py`, `scripts/get_youtube_refresh_token.py`

## 2026-01-16

### 일당백 스타일 영상 Part 1 시간 정보 정확도 개선
- **작업 내용**:
  - 일당백 스타일 영상 제작 시 part1 video와 infographic의 종료 시간을 정확하게 계산하여 metadata에 기록하는 기능 개선
  - Crossfade 효과가 적용된 실제 클립 duration을 사용하여 정확한 시간 계산
- **주요 수정사항**:
  - **`src/create_full_episode.py`**:
    - 각 클립의 실제 duration 추적 (`part_clip_info` 리스트 추가)
    - Crossfade 효과 적용 후 실제 duration 업데이트
    - Part 1 video와 infographic의 종료 시간 계산 및 `.timing.json` 파일로 저장
    - Part 1 시간 정보를 로그에 출력
  - **`src/20_create_episode_metadata.py`**:
    - `get_actual_part_durations()` 함수 개선: 우선순위로 `.timing.json` 파일에서 읽기 (가장 정확)
    - Fallback: 원본 비디오 파일의 duration 사용 (하위 호환성)
    - `create_episode_metadata()` 함수에서 timing.json 파일을 읽어 metadata에 `part1_video_end_time`과 `part1_info_end_time` 필드 자동 추가
- **개선 효과**:
  - Part 1 video와 infographic의 종료 시간이 Crossfade 효과를 반영한 정확한 값으로 계산됨
  - Metadata에 정확한 시간 정보가 자동으로 포함됨
  - YouTube chapter markers나 타임스탬프 생성 시 정확도 향상
- **수정된 파일**:
  - `src/create_full_episode.py`: Part 1 시간 정보 계산 및 저장 로직 추가
  - `src/20_create_episode_metadata.py`: timing.json 파일 읽기 및 metadata에 시간 정보 추가

### 레이 커즈와일 - 특이점이 온다 (The Singularity Is Near) summary+video 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 레이 커즈와일 "특이점이 온다 (The Singularity Is Near)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - Summary + NotebookLM Video 형태로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "특이점이 온다" ↔ "The Singularity Is Near", "레이 커즈와일" ↔ "Ray Kurzweil" 매핑 추가
- **생성된 영상**:
  - 한글: `output/The_Singularity_Is_Near_kr.mp4` (208.68 MB)
  - 영문: `output/The_Singularity_Is_Near_en.mp4` (165.25 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=1r_oGXMMbKY
  - 영문: https://www.youtube.com/watch?v=zphxWm6olYc
- **수정된 파일**:
  - `src/utils/translations.py`: 특이점이 온다, 레이 커즈와일 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 특이점이 온다 업로드 정보 업데이트

## 2026-01-15

### 조너던 스위프트 - 걸리버 여행기 (Gulliver's Travels) 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 조너던 스위프트 "걸리버 여행기 (Gulliver's Travels)" 한글/영문 일당백 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "걸리버 여행기" ↔ "Gulliver's Travels", "조너던 스위프트" ↔ "Jonathan Swift" 매핑 추가
- **생성된 영상**:
  - 한글: `output/Gullivers_Travels_full_episode_ko.mp4` (597.01 MB, 16.67분)
  - 영문: `output/Gullivers_Travels_full_episode_en.mp4` (540.60 MB, 14.52분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=42zz0RtDDyw
  - 영문: https://www.youtube.com/watch?v=clUULPkveh0
- **수정된 파일**:
  - `src/utils/translations.py`: 걸리버 여행기, 조너던 스위프트 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 걸리버 여행기 업로드 정보 업데이트

### 알베르 카뮈 - 이방인 (The Stranger) 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 알베르 카뮈 "이방인 (The Stranger)" 한글/영문 일당백 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 확인**: `src/utils/translations.py`에 이미 "이방인" ↔ "The Stranger", "알베르 카뮈" ↔ "Albert Camus" 매핑이 존재함
- **생성된 영상**:
  - 한글: `output/The_Stranger_full_episode_ko.mp4` (555.39 MB, 15.10분)
  - 영문: `output/The_Stranger_full_episode_en.mp4` (469.54 MB, 12.62분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=vBO4lEBmaao
  - 영문: https://www.youtube.com/watch?v=fWtO5G1Pswg
- **수정된 파일**:
  - `data/ildangbaek_books.csv`: 이방인 업로드 정보 업데이트

### 에드거 앨런 포 호러 단편선 + 포와 포송령의 동서양 판타지 콜라보 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - "에드거 앨런 포 호러 단편선 + 포와 포송령의 동서양 판타지 콜라보" 한글/영문 일당백 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "에드거 앨런 포 호러 단편선" ↔ "Edgar Allan Poe Horror Stories", "포와 포송령의 동서양 판타지 콜라보" ↔ "Poe and Pu Songling's East-West Fantasy Collaboration", "에드거 앨런 포" ↔ "Edgar Allan Poe" 매핑 추가
  - **제목 자동 축약 기능 추가**: `src/09_upload_from_metadata.py`에 YouTube 100자 제한을 초과하는 제목을 자동으로 축약하는 기능 추가
- **생성된 영상**:
  - 한글: `output/Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration_full_episode_ko.mp4` (432.78 MB)
  - 영문: `output/Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration_full_episode_en.mp4` (526.12 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=1dKsiVS6gP0 (제목 자동 축약: 161자 → 77자)
  - 영문: https://www.youtube.com/watch?v=NqnA36-IH04 (제목 자동 축약: 161자 → 88자)
- **수정된 파일**:
  - `src/utils/translations.py`: 에드거 앨런 포 호러 단편선, 포와 포송령의 동서양 판타지 콜라보, 에드거 앨런 포 번역 매핑 추가
  - `src/09_upload_from_metadata.py`: 제목 자동 축약 기능 추가 (100자 제한 초과 시 자동 축약)
  - `data/ildangbaek_books.csv`: 에드거 앨런 포 호러 단편선 + 포와 포송령의 동서양 판타지 콜라보 업로드 정보 업데이트

### 로버트 그린 - 권력의 법칙 (The 48 Laws of Power) summary+video 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 로버트 그린 "권력의 법칙 (The 48 Laws of Power)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - Summary + NotebookLM Video 형태로 영상 생성
  - 한글 서머리 파일 수정 후 오디오 재생성 및 영상 재생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "권력의 법칙" ↔ "The 48 Laws of Power", "로버트 그린" ↔ "Robert Greene" 매핑 추가
- **생성된 영상**:
  - 한글: `output/The_48_Laws_of_Power_kr.mp4` (340.53 MB)
  - 영문: `output/The_48_Laws_of_Power_en.mp4` (337.61 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=HlTaXreLw7c (재업로드)
  - 영문: https://www.youtube.com/watch?v=J1dnrH8ZMR0 (재업로드)
- **수정된 파일**:
  - `src/utils/translations.py`: 권력의 법칙, 로버트 그린 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 권력의 법칙 업로드 정보 업데이트

## 2026-01-13

### 앤절라 더크워스 - 그릿(Grit) summary+video 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 앤절라 더크워스 "그릿 (Grit)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - TTS 오디오 생성 (한글/영문)
  - Summary + NotebookLM Video 형태로 영상 생성
  - 한글 영상 재생성 (오디오 파일 재생성)
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "그릿" ↔ "Grit", "앤절라 더크워스" ↔ "Angela Duckworth" 매핑 추가
  - **썸네일 검색 로직 개선**: `src/09_upload_from_metadata.py`에서 한글/영문 제목 양방향 검색 기능 추가
    - 메타데이터의 `book_title`이 영문이면 한글 번역도 자동 추가
    - 한글이면 영문 번역도 자동 추가
    - 한글 파일명 직접 검색 로직 강화 (한글 유니코드 범위 확인)
    - 유사도 매칭 개선 (언더스코어, 공백, 하이픈 무시)
- **생성된 영상**:
  - 한글: `output/Grit_kr.mp4`
  - 영문: `output/Grit_en.mp4`
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=NpvOHPpFnb0
  - 영문: https://www.youtube.com/watch?v=PWjeUx3Rv40
- **수정된 파일**:
  - `src/utils/translations.py`: 그릿, 앤절라 더크워스 번역 매핑 추가
  - `src/09_upload_from_metadata.py`: 썸네일 검색 로직 개선 (한글/영문 제목 양방향 검색)
  - `data/ildangbaek_books.csv`: 그릿 업로드 정보 업데이트

## 2026-01-12

### 올더스 헉슬리 - 멋진 신세계 summary+video 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 올더스 헉슬리 "멋진 신세계 (Brave New World)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - TTS 오디오 생성 (한글/영문)
  - Summary + NotebookLM Video 형태로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "멋진 신세계" ↔ "Brave New World", "올더스 헉슬리" ↔ "Aldous Huxley" 매핑 추가
- **생성된 영상**:
  - 한글: `output/Brave_New_World_kr.mp4` (302.07 MB)
  - 영문: `output/Brave_New_World_en.mp4` (291.25 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=iZ9rOZbLxxM
  - 영문: https://www.youtube.com/watch?v=jUBZBe7dxIM
- **수정된 파일**:
  - `src/utils/translations.py`: 멋진 신세계, 올더스 헉슬리 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 멋진 신세계 업로드 정보 업데이트

## 2026-01-11

### 막스 베버 - 프로테스탄티즘의 윤리와 자본주의 정신 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 막스 베버 "프로테스탄티즘의 윤리와 자본주의 정신 (The Protestant Ethic and the Spirit of Capitalism)" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "프로테스탄티즘의 윤리와 자본주의 정신" ↔ "The Protestant Ethic and the Spirit of Capitalism", "막스 베버" ↔ "Max Weber" 매핑 추가
  - **제목 길이 제한 처리**: YouTube 100자 제한에 맞춰 제목 축약 ("The Protestant Ethic and the Spirit of Capitalism" → "Protestant Ethic & Capitalism")
- **생성된 영상**:
  - 한글: `output/The_Protestant_Ethic_and_the_Spirit_of_Capitalism_full_episode_kr.mp4` (224.32 MB, 12.32분)
  - 영문: `output/The_Protestant_Ethic_and_the_Spirit_of_Capitalism_full_episode_en.mp4` (456.59 MB, 13.08분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=Y05T3AebwVQ
  - 영문: https://www.youtube.com/watch?v=eL05LOss05k
- **수정된 파일**:
  - `src/utils/translations.py`: 프로테스탄티즘의 윤리와 자본주의 정신, 막스 베버 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 프로테스탄티즘의 윤리와 자본주의 정신 업로드 정보 업데이트

### 레비스트로스 - 슬픈 열대 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 클로드 레비스트로스 "레비스트로스 - 슬픈 열대 (Tristes Tropiques)" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **생성된 영상**:
  - 한글: `output/Tristes_Tropiques_full_episode_kr.mp4` (297.08 MB, 14.57분)
  - 영문: `output/Tristes_Tropiques_full_episode_en.mp4` (349.27 MB, 14.01분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=nYHyS1q5sTY
  - 영문: https://www.youtube.com/watch?v=ruhMqnEL0Wo
- **수정된 파일**:
  - `data/ildangbaek_books.csv`: 슬픈 열대 업로드 정보 업데이트

### YouTube 자막 스크립트 생성
- **작업 내용**:
  - YouTube URL에서 자막을 다운로드하여 스크립트 파일 생성
  - 두 개의 YouTube 영상에서 자막 추출 (Part 1, Part 2)
- **생성된 파일**:
  - `data/source/Vx26Eom_lY0_part1_author.txt` (21,355자, 706개 세그먼트)
  - `data/source/GAZyWcG9nSc_part2_novel.txt` (25,577자, 850개 세그먼트)
- **사용 스크립트**:
  - `scripts/fetch_separate_scripts.py`: YouTube 자막 추출 및 분리 저장

### 메타데이터 타임스탬프 생성 로직 개선
- **작업 내용**:
  - 일당백 스타일 영상의 메타데이터 타임스탬프 생성 로직 개선
  - 실제 Part 비디오 파일의 길이를 기반으로 정확한 타임스탬프 생성
- **주요 수정사항**:
  - **`get_actual_part_durations()` 함수 추가**: 실제 Part 비디오 파일의 길이를 계산하여 각 Part의 총 길이 반환 (비디오 길이 + 인포그래픽 30초)
  - **타임스탬프 생성 로직 개선**: 
    - 기존: 전체 영상 길이의 35%로 Part 1을 고정 계산 (부정확)
    - 개선: 실제 Part 비디오 파일 길이를 우선 사용, 파일을 찾을 수 없을 때만 비율 계산 (하위 호환성)
  - `input/` 또는 `assets/notebooklm/` 폴더에서 원본 Part 비디오 파일을 찾아 실제 길이 확인
  - 인포그래픽 길이(30초)를 고려하여 정확한 타임스탬프 생성
  - 한글/영문 메타데이터 모두에 적용
- **수정된 파일**:
  - `src/20_create_episode_metadata.py`: 타임스탬프 생성 로직 개선

## 2026-01-09

### 로미오와 줄리엣 - 셰익스피어 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 셰익스피어 "로미오와 줄리엣 (Romeo and Juliet)" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **일당백 스타일 영상 생성 스크립트 개선**: `scripts/concatenate_videos_from_input.py` 수정
    - 인포그래픽 표시 시간 기본값 변경: 10초 → **30초**
    - 백그라운드 음악 처리 기능 추가 (인포그래픽에만 적용)
    - 배경음악 자동 탐지 기능 추가 (`input/` 또는 `assets/music/` 폴더에서 자동 탐지)
    - 음량 조절 및 fadeout 효과 적용
  - **번역 매핑**: 이미 "로미오와 줄리엣" ↔ "Romeo and Juliet" 매핑 존재
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 처리
- **생성된 영상**:
  - 한글: `output/Romeo_and_Juliet_full_episode_kr.mp4` (423.30 MB, 14.14분)
  - 영문: `output/Romeo_and_Juliet_full_episode_en.mp4` (465.40 MB, 14.11분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=ppsrfEzbOYo
  - 영문: https://www.youtube.com/watch?v=tOTLB-dxmls
- **수정된 파일**:
  - `scripts/concatenate_videos_from_input.py`: 인포그래픽 30초 유지 및 백그라운드 음악 기능 추가
  - `data/ildangbaek_books.csv`: 로미오와 줄리엣 업로드 정보 업데이트

### 햄릿 - 셰익스피어 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 셰익스피어 "햄릿 (Hamlet)" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "햄릿" ↔ "Hamlet", "로미오와 줄리엣" ↔ "Romeo and Juliet" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 처리
- **생성된 영상**:
  - 한글: `output/Hamlet_full_episode_kr.mp4` (415.71 MB, 13.48분)
  - 영문: `output/Hamlet_full_episode_en.mp4` (457.93 MB, 13.44분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=ZkINbHIM3lM
  - 영문: https://www.youtube.com/watch?v=A3UWIsFrmQU
- **수정된 파일**:
  - `src/utils/translations.py`: 햄릿, 로미오와 줄리엣 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 햄릿 업로드 정보 업데이트

### 슬픈 열대 - 클로드 레비스트로스 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 클로드 레비스트로스 "슬픈 열대 (Tristes Tropiques)" 한글/영문 일당백 스타일 영상 제작
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "슬픈 열대" ↔ "Tristes Tropiques", "클로드 레비스트로스" ↔ "Claude Lévi-Strauss" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 처리
- **생성된 영상**:
  - 한글: `output/Tristes_Tropiques_full_episode_kr.mp4` (289.45 MB, 13.91분)
  - 영문: `output/Tristes_Tropiques_full_episode_en.mp4` (341.97 MB, 13.34분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=50k9QSc2-vE
  - 영문: https://www.youtube.com/watch?v=eV3hj5E_8d8
- **수정된 파일**:
  - `src/utils/translations.py`: 슬픈 열대, 클로드 레비스트로스 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 슬픈 열대 업로드 정보 업데이트

### 불안의 서 - 페르난두 페소아 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 페르난두 페소아 "불안의 서 (The Book of Disquiet)" 한글/영문 영상 제작 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "불안의 서" ↔ "The Book of Disquiet", "페르난두 페소아" ↔ "Fernando Pessoa" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료 (Pexels 90개, Unsplash 10개, Pixabay API 오류 발생)
  - **TTS 오디오 생성**: 한글/영문 Summary TTS 오디오 생성 완료
- **생성된 영상**:
  - 한글: `output/The_Book_of_Disquiet_kr.mp4` (311.02 MB)
  - 영문: `output/The_Book_of_Disquiet_en.mp4` (288.16 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=4-EOxscKOrU
  - 영문: https://www.youtube.com/watch?v=XuYZc6J44mM
- **수정된 파일**:
  - `src/utils/translations.py`: 불안의 서, 페르난두 페소아 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 불안의 서 업로드 정보 업데이트

### 이키가이 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - "이키가이 (Ikigai)" 한글/영문 영상 제작 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "이키가이" ↔ "Ikigai" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료 (이미지 다운로드 로직 개선: 지연 최소화)
  - **TTS 오디오 생성**: 한글/영문 Summary TTS 오디오 생성 완료
- **생성된 영상**:
  - 한글: `output/Ikigai_kr.mp4` (266.72 MB)
  - 영문: `output/Ikigai_en.mp4` (218.40 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=Hj1ySsg3tn0
  - 영문: https://www.youtube.com/watch?v=mSkAQrep1yE
- **수정된 파일**:
  - `src/utils/translations.py`: 이키가이 번역 매핑 추가
  - `src/02_get_images.py`: 이미지 다운로드 로직 개선 (지연 최소화)
  - `src/20_create_episode_metadata.py`: 일당백 영상 제목 포맷 규칙 명시 (주석 추가)
  - `.cursorrules`: 일당백 영상 제목 포맷 규칙 추가 (명시적 요청 없이 변경 금지)
  - `data/ildangbaek_books.csv`: 이키가이 업로드 정보 업데이트

### 세일즈맨의 죽음 - 아서 밀러 영상 재생성 및 YouTube 재업로드
- **작업 내용**:
  - 아서 밀러 "세일즈맨의 죽음 (Death of a Salesman)" 한글/영문 영상 재생성 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 재생성
  - YouTube 재업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환 (video 파일명 수정 반영)
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료 (기존 이미지 재사용)
  - **TTS 오디오 생성**: 한글/영문 Summary TTS 오디오 재생성 완료
- **생성된 영상**:
  - 한글: `output/Death_of_a_Salesman_kr.mp4` (448.13 MB)
  - 영문: `output/Death_of_a_Salesman_en.mp4` (302.21 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=cR0QYWgWlaY
  - 영문: https://www.youtube.com/watch?v=YeiN06mKKug
- **수정된 파일**:
  - `data/ildangbaek_books.csv`: 세일즈맨의 죽음 재업로드 정보 업데이트

### 세일즈맨의 죽음 - 아서 밀러 영상 제작 및 YouTube 업로드 (초기)
- **작업 내용**:
  - 아서 밀러 "세일즈맨의 죽음 (Death of a Salesman)" 한글/영문 영상 제작 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "세일즈맨의 죽음" ↔ "Death of a Salesman", "아서 밀러" ↔ "Arthur Miller" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료 (Pixabay API 오류 발생, Unsplash로 대체)
  - **TTS 오디오 생성**: 한글/영문 Summary TTS 오디오 생성 완료
- **생성된 영상**:
  - 한글: `output/Death_of_a_Salesman_kr.mp4` (257.09 MB)
  - 영문: `output/Death_of_a_Salesman_en.mp4` (238.03 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=Mmd9TY1we84
  - 영문: https://www.youtube.com/watch?v=8cSwlqDiVcg
- **수정된 파일**:
  - `src/utils/translations.py`: 세일즈맨의 죽음, 아서 밀러 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 세일즈맨의 죽음 업로드 정보 업데이트

### 4000주 - 올리버 버크먼 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 올리버 버크먼 "4000주 (Four Thousand Weeks)" 한글/영문 영상 제작 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "4000주" ↔ "Four Thousand Weeks", "올리버 버크먼" ↔ "Oliver Burkeman" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료 (Pixabay API 오류 발생, Unsplash로 대체)
  - **TTS 오디오 생성**: 한글/영문 Summary TTS 오디오 생성 완료
- **생성된 영상**:
  - 한글: `output/Four_Thousand_Weeks_kr.mp4` (209.52 MB)
  - 영문: `output/Four_Thousand_Weeks_en.mp4` (207.66 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=fBzBt7W39jY
  - 영문: https://www.youtube.com/watch?v=ZnIvEcReSLU
- **수정된 파일**:
  - `src/utils/translations.py`: 4000주, 올리버 버크먼 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 4000주 업로드 정보 업데이트

## 2026-01-08

### 무라카미 하루키 상실의 시대 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 무라카미 하루키 "상실의 시대 (Norwegian Wood)" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 및 영상 합성 완료
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "상실의 시대" ↔ "Norwegian Wood" 매핑 추가
  - **파일 구조화**: `input/` 폴더 내 파일을 `assets/notebooklm/Norwegian_Wood/`로 이동 및 표준화
- **생성된 영상**:
  - 한글: `output/Norwegian_Wood_full_episode_ko.mp4` (807.57초, 약 13.46분, 433MB)
  - 영문: `output/Norwegian_Wood_full_episode_en.mp4` (675.12초, 약 11.25분, 423MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=GDnnnuT6T28
  - 영문: https://www.youtube.com/watch?v=9DV5Zl7BAZg
- **수정된 파일**:
  - `src/utils/translations.py`: 상실의 시대 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 상실의 시대 업로드 정보 업데이트

### 일연 삼국유사 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 일연 "삼국유사" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 및 영상 합성 완료
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **파일 구조화**: `input/` 폴더 내 파일을 `assets/notebooklm/일연_삼국유사/`로 이동 및 표준화
- **생성된 영상**:
  - 한글: `output/일연_삼국유사_full_episode_ko.mp4` (904.12초, 약 15.07분)
  - 영문: `output/일연_삼국유사_full_episode_en.mp4` (876.60초, 약 14.61분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=f2LRK6GARS8
  - 영문: https://www.youtube.com/watch?v=jDM1h4QxVUI
- **수정된 파일**:
  - `data/ildangbaek_books.csv`: 삼국유사 업로드 정보 업데이트

### 최인훈 광장 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 최인훈 "광장" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 및 영상 합성 완료
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "광장" ↔ "The Square", "최인훈" ↔ "Choi In-hoon" 매핑 추가
  - **파일 구조화**: `input/` 폴더 내 파일을 `assets/notebooklm/The_Square/`로 이동 및 표준화
- **생성된 영상**:
  - 한글: `output/The_Square_full_episode_ko.mp4` (685.04초, 약 11.42분)
  - 영문: `output/The_Square_full_episode_en.mp4` (750.61초, 약 12.51분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=I0IQXtDebIg
  - 영문: https://www.youtube.com/watch?v=2GfBPumLF5Y
- **수정된 파일**:
  - `src/utils/translations.py`: 광장, 최인훈 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 광장 업로드 정보 업데이트

### 국부론 - 애덤 스미스 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 애덤 스미스 "국부론" 한글/영문 영상 제작 (Summary 스타일)
  - Summary(5분) + NotebookLM + Review 구조로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "국부론" ↔ "Wealth of Nations", "애덤 스미스" ↔ "Adam Smith" 매핑 추가
  - **파일 준비**: `input/` 폴더의 파일을 표준 위치로 이동 및 변환
  - **이미지 다운로드**: 100개 무드 이미지 다운로드 완료
- **생성된 영상**:
  - 한글: `output/Wealth_of_Nations_kr.mp4` (205.10 MB)
  - 영문: `output/Wealth_of_Nations_en.mp4` (275.36 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=1zACX8Hsd6g
  - 영문: https://www.youtube.com/watch?v=_R9hVoxOLGs
- **수정된 파일**:
  - `src/utils/translations.py`: 국부론, 애덤 스미스 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 국부론 업로드 정보 업데이트

## 2026-01-07

### 어니스트 헤밍웨이 "무기여 잘 있거라" 일당백 스타일 영상 제작
- **작업 내용**:
  - 어니스트 헤밍웨이 "무기여 잘 있거라" 일당백 스타일 한글/영문 롱폼 영상 제작
  - 인포그래픽 표시 시간 30초로 설정 (사용자 요청 반영)
  - Part 2개 자동 처리 및 영상 합성 완료
  - 한글/영문 메타데이터 및 썸네일(JPG) 생성 완료
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "무기여 잘 있거라" ↔ "A Farewell to Arms" 매핑 추가
  - **파일 구조화**: `input/` 폴더 내 파일을 `assets/notebooklm/A_Farewell_to_Arms/`로 이동 및 표준화
- **생성된 영상**:
  - 한글: `output/A_Farewell_to_Arms_full_episode_ko.mp4` (827.49초, 약 13.79분)
  - 영문: `output/A_Farewell_to_Arms_full_episode_en.mp4` (887.79초, 약 14.80분)
- **생성된 메타데이터**:
  - 한글: `output/A_Farewell_to_Arms_full_episode_ko.metadata.json`
  - 영문: `output/A_Farewell_to_Arms_full_episode_en.metadata.json`

## 2026-01-07

### 세르반테스 돈키호테 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 세르반테스 "돈키호테 : 세상의 모든 소설들은 무릎꿇고 경의를 표하시오!!" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 세르반테스 돈키호테 번역 매핑 추가
    - "세르반테스 돈키호테" ↔ "Don Quixote"
- **생성된 영상**:
  - 한글: `output/Don_Quixote_full_episode_ko.mp4` (934.60초, 약 15.58분)
  - 영문: `output/Don_Quixote_full_episode_en.mp4` (909.02초, 약 15.15분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=Nr7GaQHbK9Q
  - 영문: https://www.youtube.com/watch?v=ta9Jr2axTu8
- **수정된 파일**:
  - `src/utils/translations.py`: 세르반테스 돈키호테 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 돈키호테 업로드 정보 업데이트

### 장르 자동 감지 로직 개선
- **작업 내용**:
  - 장르 감지 시 오탐지 문제 해결 (예: "경의를 표하시오"에서 "시"로 잘못 감지)
- **주요 수정사항**:
  - **장르 감지 우선순위 개선**: `src/20_create_episode_metadata.py`의 `detect_book_genre()` 함수 수정
    - "소설"을 우선 체크하도록 순서 변경 (다른 단어에 포함될 수 있는 "시"보다 우선)
    - "시" 감지는 "시집", "시인", "시선", "시화" 등 명확한 패턴만 매칭
    - "경의", "시각" 등은 제외하여 오탐지 방지
- **문제 해결**:
  - "세상의 모든 소설들은 무릎꿇고 경의를 표하시오"에서 "시"로 잘못 감지되던 문제 해결
  - 이제 "소설"이 포함된 경우 정확히 "소설"로 감지됨

### 미시마 유키오 우국, 금각사 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 미시마 유키오 "우국, 금각사 : 아름답게 죽어라는 일본, 어떻게든 살아라는 한국" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 미시마 유키오 우국 금각사 번역 매핑 추가
    - "미시마 유키오 우국, 금각사" ↔ "Yukio Mishima: Patriotism and The Temple of the Golden Pavilion"
- **생성된 영상**:
  - 한글: `output/Yukio_Mishima_Patriotism_and_The_Temple_of_the_Golden_Pavilion_full_episode_ko.mp4` (913.01초, 약 15.22분)
  - 영문: `output/Yukio_Mishima_Patriotism_and_The_Temple_of_the_Golden_Pavilion_full_episode_en.mp4` (835.59초, 약 13.93분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=SwtiS91WQCQ
  - 영문: https://www.youtube.com/watch?v=irJaMfCmaHA
- **수정된 파일**:
  - `src/utils/translations.py`: 미시마 유키오 우국 금각사 번역 매핑 추가
  - `output/Yukio_Mishima_Patriotism_and_The_Temple_of_the_Golden_Pavilion_full_episode_en.metadata.json`: 제목 길이 100자 제한에 맞게 수정 (122자 → 88자)
  - `data/ildangbaek_books.csv`: 미시마 유키오 우국 금각사 업로드 정보 업데이트

### 메타데이터 생성 시 장르 자동 감지 기능 추가
- **작업 내용**:
  - 메타데이터 생성 시 모든 책을 "소설"로 표기하던 문제 해결
  - 장르(소설, 시, 수필, 논픽션 등)를 자동으로 감지하여 적절한 용어 사용
- **주요 수정사항**:
  - **장르 감지 함수 추가**: `src/20_create_episode_metadata.py`에 `detect_book_genre()` 함수 추가
    - `book_info.json`의 `categories` 필드에서 장르 확인
    - 책 제목에서 키워드로 장르 추정 ("시", "수필", "소설" 등)
    - 장르별 용어 매핑: 소설→"소설"/"Novel", 시→"시"/"Poetry", 수필→"수필"/"Essay", 기타→"작품"/"Work"
  - **메타데이터 생성 함수 수정**:
    - `generate_episode_title()`: 제목에서 장르 용어 사용
    - `generate_episode_description()`: 설명 전체에서 장르 용어 사용 (Part 설명, 타임스탬프, 해시태그 등)
- **적용 범위**:
  - 제목: "작가와 배경부터 {장르} 줄거리까지"
  - Part 설명: "Part 2: {장르} 줄거리"
  - 타임스탬프: "Part 2: {장르} 줄거리"
  - 해시태그: "#{장르}"
- **수정된 파일**:
  - `src/20_create_episode_metadata.py`: 장르 자동 감지 및 용어 적용 로직 추가

## 2026-01-03

### 시의 본질과 거장들: 한국시에 대하여 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 시의 본질과 거장들: 한국시에 대하여 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 3개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 시의 본질과 거장들 번역 매핑 추가
    - "시의 본질과 거장들: 한국시에 대하여" ↔ "The Essence of Poetry and Masters: On Korean Poetry"
- **생성된 영상**:
  - 한글: `output/The_Essence_of_Poetry_and_Masters_On_Korean_Poetry_full_episode_ko.mp4` (1267.67초, 약 21.13분)
  - 영문: `output/The_Essence_of_Poetry_and_Masters_On_Korean_Poetry_full_episode_en.mp4` (1214.07초, 약 20.23분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=s9QJEcOq74Q
  - 영문: https://www.youtube.com/watch?v=L4MM0kjUgFk
- **수정된 파일**:
  - `src/utils/translations.py`: 시의 본질과 거장들 번역 매핑 추가
  - `output/The_Essence_of_Poetry_and_Masters_On_Korean_Poetry_full_episode_en.metadata.json`: 제목 길이 100자 제한에 맞게 수정 (110자 → 83자)
  - `data/ildangbaek_books.csv`: 시의 본질과 거장들 업로드 정보 업데이트

### 카를 마르크스 자본론 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 카를 마르크스 "자본론 : 뭉치면 살고 흩어지면 죽는다" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 3개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **YouTube 태그 검증 개선**: `src/09_upload_from_metadata.py`에서 태그 공백을 언더스코어로 변환하도록 수정
    - YouTube 태그 규칙에 맞게 공백을 언더스코어로 자동 변환
    - "Das Kapital" → "Das_Kapital"로 변환하여 태그 오류 해결
  - **번역 매핑 추가**: `src/utils/translations.py`에 카를 마르크스 및 자본론 번역 매핑 추가
- **생성된 영상**:
  - 한글: `output/Das_Kapital_full_episode_ko.mp4` (1330.92초, 약 22.18분)
  - 영문: `output/Das_Kapital_full_episode_en.mp4` (1381.14초, 약 23.02분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=QP4LlM0sy2Y
  - 영문: https://www.youtube.com/watch?v=aeUoPueRi4M
- **수정된 파일**:
  - `src/09_upload_from_metadata.py`: 태그 공백을 언더스코어로 변환하는 로직 추가
  - `src/utils/translations.py`: 카를 마르크스 및 자본론 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 자본론 업로드 정보 업데이트

## 2026-01-02

### 위대한 개츠비 일당백 스타일 영상 제작 및 메타데이터 동적 Part 감지 기능 추가
- **작업 내용**:
  - 위대한 개츠비 "가난한 청년은 부잣집 딸과 결혼할 수 없는가?" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **메타데이터 동적 Part 감지**: `src/20_create_episode_metadata.py`에서 Part 개수를 동적으로 감지하여 설명과 타임스탬프 자동 생성
    - Part 1, 2만 하드코딩되어 있던 것을 동적 감지로 변경
    - Part 개수에 따라 설명과 타임스탬프 자동 생성 (Part 1, 2, 3 이상 모두 지원)
    - `detect_part_count()` 함수 추가: `assets/notebooklm` 폴더에서 Part 파일 자동 탐지
  - **번역 매핑 추가**: `src/utils/translations.py`에 위대한 개츠비 및 스콧 피츠제럴드 번역 매핑 추가
- **생성된 영상**:
  - 한글: `output/The_Great_Gatsby_full_episode_ko.mp4` (871.36초, 약 14.52분)
  - 영문: `output/The_Great_Gatsby_full_episode_en.mp4` (858.14초, 약 14.30분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=2_aMxbFUBLQ
  - 영문: https://www.youtube.com/watch?v=y5GvpwX1jdc
- **수정된 파일**:
  - `src/20_create_episode_metadata.py`: Part 개수 동적 감지 및 설명/타임스탬프 자동 생성 로직 추가
  - `src/utils/translations.py`: 위대한 개츠비 및 스콧 피츠제럴드 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 위대한 개츠비 업로드 정보 업데이트

### 플라톤 대화편 일당백 스타일 영상 제작 및 배경음악 문제 수정
- **작업 내용**:
  - 플라톤 "대화편 : 철학은 사랑이다" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 3개 자동 처리 확인 및 검증
  - 배경음악이 인포그래픽에 적용되지 않는 문제 수정
- **주요 수정사항**:
  - **배경음악 오디오 보존**: Crossfade 효과 적용 시 배경음악 오디오가 손실되는 문제 해결
    - Crossfade 효과 적용 전에 배경음악 추가
    - Crossfade 효과 적용 시 기존 오디오를 보존하도록 수정
  - **인포그래픽 클립 인덱스 관리 개선**: 클립 참조 방식에서 인덱스 기반 접근으로 변경하여 안정성 향상
- **번역 매핑 추가**:
  - `src/utils/translations.py`: 플라톤 "대화편 : 철학은 사랑이다" 및 "플라톤" 번역 매핑 추가
- **생성된 영상**:
  - 한글: `output/Platos_Dialogues_Philosophy_is_Love_full_episode_ko.mp4` (1310.37초, 약 21.84분)
  - 영문: `output/Platos_Dialogues_Philosophy_is_Love_full_episode_en.mp4` (1333.20초, 약 22.22분)
- **수정된 파일**:
  - `src/create_full_episode.py`: 배경음악 오디오 보존 로직 추가, 인포그래픽 클립 인덱스 관리 개선
  - `src/utils/translations.py`: 플라톤 대화편 번역 매핑 추가

## 2026-01-02

### 일당백 스타일 영상 제작 기능 개선
- **작업 내용**:
  - `src/create_full_episode.py`: Part 3개 이상 자동 지원 기능 추가
  - 배경음악 자동 탐지 및 다운로드 기능 추가
  - 인포그래픽에 배경음악 자동 적용 로직 개선
  - `.cursorrules`: 일당백 스타일 영상 제작 규칙 추가
- **주요 개선사항**:
  - **동적 Part 탐지**: Part 1, 2만 처리하던 것을 Part 번호를 증가시키며 자동 탐지
  - **배경음악 자동 처리**: 
    - `input/` 폴더와 `assets/music/` 폴더에서 자동 탐지
    - 없으면 Pixabay Music에서 책 분위기에 맞는 배경음악 자동 다운로드
    - 인포그래픽 클립에만 배경음악 자동 추가
    - 배경음악 길이를 인포그래픽 길이에 맞춰 자동 조정 (반복 또는 자르기)
  - **오디오 처리 개선**: 배경음악 오디오 길이를 정확히 클립 길이에 맞추는 로직 추가
- **번역 매핑 추가**:
  - `src/utils/translations.py`: 조세희 "난장이가 쏘아올린 작은 공" 번역 매핑 추가
- **수정된 파일**:
  - `src/create_full_episode.py`: Part 3개 이상 지원, 배경음악 자동 탐지 및 다운로드
  - `src/utils/translations.py`: 조세희와 난장이가 쏘아올린 작은 공 번역 매핑 추가
  - `.cursorrules`: 일당백 스타일 영상 제작 규칙 추가
- **문서 업데이트**:
  - `README.md`: Part 3개 이상 지원 및 배경음악 자동 처리 설명 추가

## 2026-01-02

### 리처드 도킨스 "만들어진 신" 일당백 스타일 영상 제작 및 업로드
- **작업 내용**:
  - 리처드 도킨스의 "만들어진 신 : 그래서 인간은 종교를 창조했다" 일당백 스타일 한글/영문 롱폼 영상 제작
  - 번역 매핑 추가: "만들어진 신" → "The God Delusion", "리처드 도킨스" → "Richard Dawkins"
  - Part 1/Part 2 영상 및 인포그래픽 합성하여 전체 에피소드 영상 생성
  - 한글/영문 메타데이터 생성 및 YouTube 업로드 완료
- **생성된 영상**:
  - 한글: https://www.youtube.com/watch?v=Igfe76gOXGY (293MB, 14분 11초)
  - 영문: https://www.youtube.com/watch?v=F2CZD4l8LXM (338MB)
- **수정된 파일**:
  - `src/utils/translations.py`: 리처드 도킨스와 만들어진 신 번역 매핑 추가
  - `src/09_upload_from_metadata.py`: 들여쓰기 오류 수정 (if 문 블록)
- **업데이트된 파일**:
  - `data/ildangbaek_books.csv`: 만들어진 신 상태를 "uploaded"로 업데이트

### Analytics 기반 채널 개선 제안 기능 추가
- **작업 내용**:
  - `src/22_analytics_recommendations.py`: Analytics 데이터를 분석하여 채널 개선 제안을 자동 생성하는 스크립트 추가
  - 채널 성과 분석: 조회수, 좋아요, 댓글, 참여율 등 종합 분석
  - 영상별 성과 분석: 저성과/고성과 영상 자동 식별
  - 개선 제안 생성: 우선순위별(높음/중간/낮음) 구체적인 액션 아이템 제안
  - 리포트 자동 생성: Markdown 형식의 상세 분석 리포트
- **분석 항목**:
  - 저성과 영상 식별 및 개선 제안
  - 고성과 영상 분석 및 전략 제안
  - 참여율 분석 및 개선 방안
  - 업로드 빈도 분석 및 일정 제안
  - 조회수 분포 및 일관성 분석
  - 콘텐츠 전략 제안
- **새로 생성된 파일**:
  - `src/22_analytics_recommendations.py`: Analytics 기반 개선 제안 스크립트
- **문서 업데이트**:
  - `README.md`: Analytics 기반 채널 개선 제안 섹션 추가

## 2026-01-02

### YouTube 자막 추출 스크립트 개선
- **작업 내용**:
  - `scripts/fetch_separate_scripts.py`: 여러 URL을 처리할 수 있도록 개선
  - `--urls` 옵션 추가: 3개 이상의 영상 URL을 한 번에 처리 가능
  - 기존 `--url1`, `--url2` 옵션은 하위 호환성을 위해 유지
  - Part 3 이상의 파일명 자동 생성 기능 추가
- **수정된 파일**:
  - `scripts/fetch_separate_scripts.py`: 여러 URL 처리 로직 추가, `save_transcript` 함수 개선
- **사용 예시**:
  ```bash
  # 3개 영상 처리
  python scripts/fetch_separate_scripts.py \
    --urls "URL1" "URL2" "URL3" \
    --title "책제목" \
    --cookies "scripts/cookies.txt"
  ```

## 2025-12-31

### 일당백 에피소드 제작 워크플로우 구현
- **작업 내용**:
  - YouTube 자막 추출 스크립트: 일당백 채널의 Part 1/Part 2 영상에서 자막 추출 기능 구현
  - 에피소드 영상 합성: NotebookLM에서 생성한 Part 1/Part 2 영상과 인포그래픽을 하나의 에피소드로 합성
  - 배경음악 자동 다운로드: 책 분위기에 맞는 라이센스 없는 배경음악 자동 다운로드 (Freesound API, Pixabay)
  - 에피소드 메타데이터 생성: 일당백 스타일 에피소드용 메타데이터 생성 (제목, 설명, 태그)
  - 영문 메타데이터 개선: 영문 메타데이터에서 한글 제거, 채널명을 1DANG100으로 통일
  - 인포그래픽 표시 시간 조정: 5초 → 30초로 증가
  - 배경음악 fadeout 효과 추가
- **수정된 파일**:
  - `src/09_upload_from_metadata.py`: sys.path 추가, 제목 검증 로직 추가, 채널 ID 처리 개선
  - `src/20_create_episode_metadata.py`: 영문 메타데이터에서 한글 제거, 1DANG100으로 통일
  - `src/utils/translations.py`: 마키아벨리 군주론 번역 매핑 추가
- **새로 생성된 파일**:
  - `scripts/fetch_separate_scripts.py`: YouTube 자막 추출 (Part 1/Part 2 분리 저장)
  - `scripts/fetch_youtube_script.py`: YouTube 자막 추출 (통합 저장)
  - `src/create_full_episode.py`: 에피소드 영상 합성 스크립트
  - `src/20_create_episode_metadata.py`: 에피소드 메타데이터 생성 스크립트
  - `src/21_download_background_music.py`: 배경음악 다운로드 스크립트
  - `run_episode_maker.py`: 에피소드 제작 워크플로우 통합 스크립트
- **생성된 영상**:
  - 마키아벨리 군주론: 깨어있는 시민을 위한 필요악 (한글/영문)
    - 한글: https://www.youtube.com/watch?v=UVMpO5zZE-E (15분 11초, 506.99MB)
    - 영문: https://www.youtube.com/watch?v=HchRMda0H0s (15분 0초, 548.03MB)
- **문서 업데이트**:
  - `README.md`: 일당백 에피소드 제작 워크플로우 섹션 추가
  - `requirements.txt`: youtube-transcript-api, selenium, webdriver-manager, Pillow 추가

### YouTube 채널 개선사항 구현
- **작업 내용**:
  - 좋아요 유도 문구 중간 삽입: 설명란 중간 부분에 좋아요 유도 문구 추가 (알고리즘 영향 설명 포함)
  - 자막 품질 향상: 폰트 크기 60→70, 테두리 두께 2→3, 배경 반투명 박스 추가, 줄 간격 증가, 위치 조정
  - 전환 효과 강화: 섹션 전환 시 페이드 인/아웃 효과 강화, 전환 시간 최적화 (2초→1.5초)
  - 최적 업로드 시간대 분석: Analytics 기반 요일별/시간대별 업로드 성과 분석 스크립트 구현
  - 정기 업로드 일정 수립: 최적 시간대 기반 정기 업로드 일정 생성 및 관리 스크립트 구현
- **수정된 파일**:
  - `src/08_create_and_preview_videos.py`: 좋아요 유도 문구 중간 삽입 로직 추가
  - `src/03_make_video.py`: 자막 품질 향상 (폰트, 테두리, 배경 박스), 전환 효과 강화 (페이드 인/아웃)
  - `src/09_text_to_speech.py`: 로깅 시스템 적용 (print → logger)
  - `src/02_get_images.py`: 로깅 시스템 적용
- **새로 생성된 파일**:
  - `src/18_analyze_optimal_upload_time.py`: 최적 업로드 시간대 분석 스크립트
  - `src/19_upload_schedule.py`: 정기 업로드 일정 수립 스크립트
  - `docs/CHANNEL_IMPROVEMENT_ANALYSIS.md`: 채널 개선 분석 리포트
  - `docs/IMPROVEMENT_IMPLEMENTATION.md`: 개선사항 구현 문서
- **문서 업데이트**:
  - `README.md`: 최적 업로드 시간대 분석 및 정기 업로드 일정 수립 사용법 추가
  - `docs/CHANNEL_IMPROVEMENT_ANALYSIS.md`: 구현 완료 항목 업데이트

## 2025-12-31

### Summary 파일 메타데이터 주석 처리 기능 추가
- **작업 내용**:
  - Summary 파일 생성 시 메타데이터를 HTML 주석으로 자동 처리
  - TTS 생성 시 메타데이터 자동 필터링 기능 추가
  - 한글/영문 모두 지원
- **수정된 파일**:
  - `src/08_generate_summary.py`: `save_summary()` 메서드에 메타데이터 주석 처리 로직 추가
  - `src/09_text_to_speech.py`: `_clean_markdown_for_tts()` 메서드에 HTML 주석 및 메타데이터 필터링 추가
  - `src/10_create_video_with_summary.py`: 동일한 필터링 로직 적용
  - `src/03_make_video.py`: 자막 생성 시 메타데이터 필터링 추가
- **메타데이터 형식**:
  - 한글: `<!-- 📘 노인과 바다 -->`, `<!-- 어니스트 헤밍웨이 -->`, `<!-- TTS 기준 약 5분 서머리 스크립트 (Korean) -->`
  - 영문: `<!-- 📘 The Old Man and the Sea -->`, `<!-- Ernest Hemingway -->`, `<!-- TTS 기준 about 5 minutes summary script (English) -->`
- **영상 업로드 워크플로우 개선**:
  - `.cursorrules`에 YouTube 업로드 승인 절차 규칙 추가
  - 영상 생성 요청 시 업로드까지 자동 진행하지 않음
  - 사용자 명시적 요청 시에만 업로드 진행

### 노인과 바다 영상 제작 및 업로드
- **책 제목**: 노인과 바다 (The Old Man and the Sea)
- **저자**: 어니스트 헤밍웨이 (Ernest Hemingway)
- **생성된 파일**:
  - 영상: `output/The_Old_Man_and_the_Sea_kr.mp4` (264.09MB), `output/The_Old_Man_and_the_Sea_en.mp4` (280.78MB)
  - 썸네일: `output/The_Old_Man_and_the_Sea_thumbnail_kr.jpg`, `output/The_Old_Man_and_the_Sea_thumbnail_en.jpg`
  - 메타데이터: `output/The_Old_Man_and_the_Sea_kr.metadata.json`, `output/The_Old_Man_and_the_Sea_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/The_Old_Man_and_the_Sea_notebooklm_kr.mp4`, `assets/video/The_Old_Man_and_the_Sea_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 노인과 바다 책 리뷰 | [Korean] The Old Man and the Sea Book Review
    - URL: https://www.youtube.com/watch?v=cRcf2WF8iqo
  - [2] [English] The Old Man and the Sea Book Review | [영어] 노인과 바다 책 리뷰
    - URL: https://www.youtube.com/watch?v=_AqE6HnRJfc
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "노인과 바다" ↔ "The Old Man and the Sea" 매핑 추가
    - "헤밍웨이" ↔ "Ernest Hemingway" 매핑 (이미 존재)

### 이방인 영상 제작 및 업로드
- **책 제목**: 이방인 (The Stranger)
- **저자**: 알베르 카뮈 (Albert Camus)
- **생성된 파일**:
  - 영상: `output/The_Stranger_kr.mp4` (242.09MB), `output/The_Stranger_en.mp4` (182.51MB)
  - 썸네일: `output/The_Stranger_thumbnail_kr.jpg`, `output/The_Stranger_thumbnail_en.jpg`
  - 메타데이터: `output/The_Stranger_kr.metadata.json`, `output/The_Stranger_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/The_Stranger_notebooklm_kr.mp4`, `assets/video/The_Stranger_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 이방인 책 리뷰 | [Korean] The Stranger Book Review
    - URL: https://www.youtube.com/watch?v=Tkto3zlCbpI
  - [2] [English] The Stranger Book Review | [영어] 이방인 책 리뷰
    - URL: https://www.youtube.com/watch?v=I_Y9XgI3bq4
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "이방인" ↔ "The Stranger" 매핑 추가
    - "알베르 카뮈" ↔ "Albert Camus" 매핑 추가

### 변신 영상 제작 및 업로드
- **책 제목**: 변신 (The Metamorphosis)
- **저자**: 프란츠 카프카 (Franz Kafka)
- **생성된 파일**:
  - 영상: `output/The_Metamorphosis_kr.mp4` (353.49MB), `output/The_Metamorphosis_en.mp4` (306.81MB)
  - 썸네일: `output/The_Metamorphosis_thumbnail_kr.jpg`, `output/The_Metamorphosis_thumbnail_en.jpg`
  - 메타데이터: `output/The_Metamorphosis_kr.metadata.json`, `output/The_Metamorphosis_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/The_Metamorphosis_notebooklm_kr.mp4`, `assets/video/The_Metamorphosis_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 변신 책 리뷰 | [Korean] The Metamorphosis Book Review
    - URL: https://www.youtube.com/watch?v=pUdbmweOY0s
  - [2] [English] The Metamorphosis Book Review | [영어] 변신 책 리뷰
    - URL: https://www.youtube.com/watch?v=6shKy3oZHeM
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "변신" ↔ "The Metamorphosis" 매핑 추가
    - "프란츠 카프카" ↔ "Franz Kafka" 매핑 추가

### 제인 에어 영상 제작 및 업로드
- **책 제목**: 제인 에어 (Jane Eyre)
- **저자**: 샬럿 브론테 (Charlotte Brontë)
- **생성된 파일**:
  - 영상: `output/Jane_Eyre_kr.mp4` (282.02MB), `output/Jane_Eyre_en.mp4` (283.98MB)
  - 썸네일: `output/Jane_Eyre_thumbnail_kr.jpg`, `output/Jane_Eyre_thumbnail_en.jpg`
  - 메타데이터: `output/Jane_Eyre_kr.metadata.json`, `output/Jane_Eyre_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/Jane_Eyre_notebooklm_kr.mp4`, `assets/video/Jane_Eyre_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 제인 에어 책 리뷰 | [Korean] Jane Eyre Book Review
    - URL: https://www.youtube.com/watch?v=bnSKi6eURFM
  - [2] [English] Jane Eyre Book Review | [영어] 제인 에어 책 리뷰
    - URL: https://www.youtube.com/watch?v=bEYUYAxR0Bo
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "제인 에어" ↔ "Jane Eyre" 매핑 추가
    - "샬럿 브론테" ↔ "Charlotte Brontë" 매핑 추가

## 2025-12-27

### 팩트풀니스 영문 영상 재생성 및 재업로드
- **책 제목**: 팩트풀니스 (Factfulness)
- **저자**: 한스 로슬링 (Hans Rosling)
- **작업 내용**:
  - input 폴더에서 파일 준비:
    - `fact_summary_en.md` → `assets/summaries/Factfulness_summary_en.md`
    - `fact_thumbnail_en.png` → `output/Factfulness_thumbnail_en.jpg` (PNG→JPG 변환)
    - `fact_video_en.mp4` → `assets/video/Factfulness_notebooklm_en.mp4`
  - 영문 롱폼 영상 재생성: `output/Factfulness_en.mp4` (189.93MB)
  - 영문 메타데이터 재생성: `output/Factfulness_en.metadata.json`
    - 한글 태그 제거 (YouTube 태그 규칙 준수)
    - 문제가 될 수 있는 태그 수정 (공백 추가)
- **YouTube 재업로드 완료 (비공개)**:
  - [English] Factfulness Book Review | [영어] 팩트풀니스 책 리뷰
    - URL: https://www.youtube.com/watch?v=rz5EpYOZCsI
    - 새 영상 ID: `rz5EpYOZCsI` (기존 영상과 다른 새 영상으로 업로드됨)

### 프랑켄슈타인 영상 제작 및 업로드
- **책 제목**: 프랑켄슈타인 (Frankenstein)
- **저자**: 메리 셸리 (Mary Shelley)
- **생성된 파일**:
  - 영상: `output/Frankenstein_kr.mp4` (411MB), `output/Frankenstein_en.mp4` (294MB)
  - 썸네일: `output/Frankenstein_thumbnail_kr.jpg`, `output/Frankenstein_thumbnail_en.jpg`
  - 메타데이터: `output/Frankenstein_kr.metadata.json`, `output/Frankenstein_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/Frankenstein_notebooklm_kr.mp4`, `assets/video/Frankenstein_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 프랑켄슈타인 책 리뷰 | [Korean] Frankenstein Book Review
    - URL: https://www.youtube.com/watch?v=Rx7RpKTkjaY
  - [2] [English] Frankenstein Book Review | [영어] 프랑켄슈타인 책 리뷰
    - URL: https://www.youtube.com/watch?v=3JrwQ45fngk
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "프랑켄슈타인" ↔ "Frankenstein" 매핑 추가
    - "메리 셸리" ↔ "Mary Shelley" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 프랑켄슈타인 한글 영상 재생성 및 재업로드
- **책 제목**: 프랑켄슈타인 (Frankenstein)
- **저자**: 메리 셸리 (Mary Shelley)
- **작업 내용**:
  - 한글 롱폼 영상 재생성: `output/Frankenstein_kr.mp4` (333.45MB)
  - 한글 메타데이터 재생성: `output/Frankenstein_kr.metadata.json`
- **YouTube 재업로드 완료 (비공개)**:
  - [한국어] 프랑켄슈타인 책 리뷰 | [Korean] Frankenstein Book Review
    - URL: https://www.youtube.com/watch?v=KsoVW_dHzN4
    - 새 영상 ID: `KsoVW_dHzN4` (기존 영상과 다른 새 영상으로 업로드됨)

### 젊은 베르테르의 슬픔 영상 제작 및 업로드
- **책 제목**: 젊은 베르테르의 슬픔 (The Sorrows of Young Werther)
- **저자**: 괴테 (Johann Wolfgang von Goethe)
- **생성된 파일**:
  - 영상: `output/The_Sorrows_of_Young_Werther_kr.mp4` (265MB), `output/The_Sorrows_of_Young_Werther_en.mp4` (306MB)
  - 썸네일: `output/The_Sorrows_of_Young_Werther_thumbnail_kr.jpg`, `output/The_Sorrows_of_Young_Werther_thumbnail_en.jpg`
  - 메타데이터: `output/The_Sorrows_of_Young_Werther_kr.metadata.json`, `output/The_Sorrows_of_Young_Werther_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - NotebookLM 비디오: `assets/video/The_Sorrows_of_Young_Werther_notebooklm_kr.mp4`, `assets/video/The_Sorrows_of_Young_Werther_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 젊은 베르테르의 슬픔 책 리뷰 | [Korean] The Sorrows of Young Werther Book Review
    - URL: https://www.youtube.com/watch?v=l7Zw32e_u0A
  - [2] [English] The Sorrows of Young Werther Book Review | [영어] 젊은 베르테르의 슬픔 책 리뷰
    - URL: https://www.youtube.com/watch?v=rf1R09G4hnw
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "젊은 베르테르의 슬픔" ↔ "The Sorrows of Young Werther" 매핑 추가
    - "괴테" ↔ "Johann Wolfgang von Goethe" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-26

### 행동하지 않으면 인생은 바뀌지 않는다 영상 제작 및 업로드
- **책 제목**: 행동하지 않으면 인생은 바뀌지 않는다 (No Excuses!: The Power of Self-Discipline)
- **저자**: 브라이언 트레이시 (Brian Tracy)
- **생성된 파일**:
  - 영상: `output/No_Excuses_The_Power_of_Self_Discipline_kr.mp4` (224MB), `output/No_Excuses_The_Power_of_Self_Discipline_en.mp4` (307MB)
  - 썸네일: `output/No_Excuses_The_Power_of_Self_Discipline_thumbnail_kr.jpg`, `output/No_Excuses_The_Power_of_Self_Discipline_thumbnail_en.jpg`
  - 메타데이터: `output/No_Excuses_The_Power_of_Self_Discipline_kr.metadata.json`, `output/No_Excuses_The_Power_of_Self_Discipline_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/No_Excuses_The_Power_of_Self_Discipline_notebooklm_kr.mp4`, `assets/video/No_Excuses_The_Power_of_Self_Discipline_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 행동하지 않으면 인생은 바뀌지 않는다 책 리뷰 | [Korean] No Excuses!: The Power of Self-Discipline Book Review
    - URL: https://www.youtube.com/watch?v=cnMPYf727lk
  - [2] [English] No Excuses!: The Power of Self-Discipline Book Review | [영어] 행동하지 않으면 인생은 바뀌지 않는다 책 리뷰
    - URL: https://www.youtube.com/watch?v=XMr661ly1UU
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "행동하지 않으면 인생은 바뀌지 않는다" ↔ "No Excuses!: The Power of Self-Discipline" 매핑 추가
    - "브라이언 트레이시" ↔ "Brian Tracy" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 설국 영상 제작 및 업로드
- **책 제목**: 설국 (Snow Country)
- **저자**: 가와바타 야스나리 (Yasunari Kawabata)
- **생성된 파일**:
  - 영상: `output/Snow_Country_kr.mp4` (271MB), `output/Snow_Country_en.mp4` (282MB)
  - 썸네일: `output/Snow_Country_thumbnail_kr.jpg`, `output/Snow_Country_thumbnail_en.jpg`
  - 메타데이터: `output/Snow_Country_kr.metadata.json`, `output/Snow_Country_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Snow_Country_notebooklm_kr.mp4`, `assets/video/Snow_Country_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 설국 책 리뷰 | [Korean] Snow Country Book Review
    - URL: https://www.youtube.com/watch?v=x2qoMiJ02Xw
  - [2] [English] Snow Country Book Review | [영어] 설국 책 리뷰
    - URL: https://www.youtube.com/watch?v=MlXg0nvIziE
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "설국" ↔ "Snow Country" 매핑 추가
    - "가와바타 야스나리" ↔ "Yasunari Kawabata" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-24

### 부자 아빠 가난한 아빠 영상 제작 및 업로드
- **책 제목**: 부자 아빠 가난한 아빠 (Rich Dad Poor Dad)
- **저자**: 로버트 기요사키 (Robert Kiyosaki)
- **생성된 파일**:
  - 영상: `output/Rich_Dad_Poor_Dad_kr.mp4` (229MB), `output/Rich_Dad_Poor_Dad_en.mp4` (197MB)
  - 썸네일: `output/Rich_Dad_Poor_Dad_thumbnail_kr.jpg`, `output/Rich_Dad_Poor_Dad_thumbnail_en.jpg`
  - 메타데이터: `output/Rich_Dad_Poor_Dad_kr.metadata.json`, `output/Rich_Dad_Poor_Dad_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Rich_Dad_Poor_Dad_notebooklm_kr.mp4`, `assets/video/Rich_Dad_Poor_Dad_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 부자 아빠 가난한 아빠 책 리뷰 | [Korean] Rich Dad Poor Dad Book Review
    - URL: https://www.youtube.com/watch?v=Qf9ftpgh2Zk
  - [2] [English] Rich Dad Poor Dad Book Review | [영어] 부자 아빠 가난한 아빠 책 리뷰
    - URL: https://www.youtube.com/watch?v=9yGHSygpNN8
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "부자 아빠 가난한 아빠" ↔ "Rich Dad Poor Dad" 매핑 추가
    - "로버트 기요사키" ↔ "Robert Kiyosaki" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 세로형 이미지 처리 로직 개선
- **`src/03_make_video.py`**:
  - 세로형 이미지(높이가 더 긴 이미지) 처리 로직 개선
  - 세로형 이미지는 원본 비율 유지하며 높이에 맞춰 배치
  - 좌우는 검은색(letterbox)으로 처리하여 늘리지 않음
  - `create_image_clip_with_ken_burns` 및 `create_image_sequence` 메서드에 적용
  - Ken Burns 효과는 세로형 이미지에 적용하지 않음

## 2025-12-23

### 현명한 투자자 영상 제작 및 업로드
- **책 제목**: 현명한 투자자 (The Intelligent Investor)
- **저자**: 벤저민 그레이엄 (Benjamin Graham)
- **생성된 파일**:
  - 영상: `output/The_Intelligent_Investor_kr.mp4` (245MB), `output/The_Intelligent_Investor_en.mp4` (191MB)
  - 썸네일: `output/The_Intelligent_Investor_thumbnail_kr.jpg`, `output/The_Intelligent_Investor_thumbnail_en.jpg`
  - 메타데이터: `output/The_Intelligent_Investor_kr.metadata.json`, `output/The_Intelligent_Investor_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Intelligent_Investor_notebooklm_kr.mp4`, `assets/video/The_Intelligent_Investor_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 현명한 투자자 책 리뷰 | [Korean] The Intelligent Investor Book Review
    - URL: https://www.youtube.com/watch?v=eRLZ-aOE61E
  - [2] [English] The Intelligent Investor Book Review | [영어] 현명한 투자자 책 리뷰
    - URL: https://www.youtube.com/watch?v=mG0xEQ1hPm0
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "현명한 투자자" ↔ "The Intelligent Investor" 매핑 추가
    - "벤저민 그레이엄" ↔ "Benjamin Graham" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 여섯 번째 대멸종 영상 제작 및 업로드
- **책 제목**: 여섯 번째 대멸종 (The Sixth Extinction)
- **저자**: 엘리자베스 콜버트 (Elizabeth Kolbert)
- **생성된 파일**:
  - 영상: `output/The_Sixth_Extinction_kr.mp4` (410MB), `output/The_Sixth_Extinction_en.mp4` (335MB)
  - 썸네일: `output/The_Sixth_Extinction_thumbnail_kr.jpg`, `output/The_Sixth_Extinction_thumbnail_en.jpg`
  - 메타데이터: `output/The_Sixth_Extinction_kr.metadata.json`, `output/The_Sixth_Extinction_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Sixth_Extinction_notebooklm_kr.mp4`, `assets/video/The_Sixth_Extinction_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 여섯 번째 대멸종 책 리뷰 | [Korean] The Sixth Extinction Book Review
    - URL: https://www.youtube.com/watch?v=v6Xet3dhrZk
  - [2] [English] The Sixth Extinction Book Review | [영어] 여섯 번째 대멸종 책 리뷰
    - URL: https://www.youtube.com/watch?v=fD7RBmbf-Bc
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "여섯 번째 대멸종" ↔ "The Sixth Extinction" 매핑 추가
    - "엘리자베스 콜버트" ↔ "Elizabeth Kolbert" 매핑 추가
    - 한글/영문 양방향 번역 지원

### Summary 파일 없을 때 오류 수정
- **`src/10_create_video_with_summary.py`**:
  - `summary_file_path`가 `None`일 때 `exists()` 호출 오류 수정
  - `summary_file_path is not None and summary_file_path.exists()` 조건 추가
  - Summary 파일이 없어도 AI가 자동 생성하도록 개선

## 2025-12-22

### 괴델, 에셔, 바흐 영상 제작 및 업로드
- **책 제목**: 괴델, 에셔, 바흐 (Gödel, Escher, Bach: An Eternal Golden Braid)
- **저자**: 더글러스 호프스태터 (Douglas Hofstadter)
- **생성된 파일**:
  - 영상: `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_kr.mp4` (247MB), `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_en.mp4` (256MB)
  - 썸네일: `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_thumbnail_kr.jpg`, `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_thumbnail_en.jpg`
  - 메타데이터: `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_kr.metadata.json`, `output/Gödel_Escher_Bach_An_Eternal_Golden_Braid_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Gödel_Escher_Bach_An_Eternal_Golden_Braid_notebooklm_kr.mp4`, `assets/video/Gödel_Escher_Bach_An_Eternal_Golden_Braid_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 괴델, 에셔, 바흐 책 리뷰 | [Korean] Gödel, Escher, Bach: An Eternal Golden Braid Book Review
    - URL: https://www.youtube.com/watch?v=cA-U5OXTugE
  - [2] [English] Gödel, Escher, Bach: An Eternal Golden Braid Book Review | [영어] 괴델, 에셔, 바흐 책 리뷰
    - URL: https://www.youtube.com/watch?v=5Pe8jgivfYM
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "괴델, 에셔, 바흐" ↔ "Gödel, Escher, Bach: An Eternal Golden Braid" 매핑 추가
    - "더글러스 호프스태터" ↔ "Douglas Hofstadter" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 은하수를 여행하는 히치하이커를 위한 안내서 영상 제작 및 업로드
- **책 제목**: 은하수를 여행하는 히치하이커를 위한 안내서 (Hitchhiker's Guide to the Galaxy)
- **저자**: 더글라스 애덤스 (Douglas Adams)
- **생성된 파일**:
  - 영상: `output/Hitchhikers_Guide_to_the_Galaxy_kr.mp4` (350MB), `output/Hitchhikers_Guide_to_the_Galaxy_en.mp4` (273MB)
  - 썸네일: `output/Hitchhikers_Guide_to_the_Galaxy_thumbnail_kr.jpg`, `output/Hitchhikers_Guide_to_the_Galaxy_thumbnail_en.jpg`
  - 메타데이터: `output/Hitchhikers_Guide_to_the_Galaxy_kr.metadata.json`, `output/Hitchhikers_Guide_to_the_Galaxy_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Hitchhikers_Guide_to_the_Galaxy_notebooklm_kr.mp4`, `assets/video/Hitchhikers_Guide_to_the_Galaxy_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 은하수를 여행하는 히치하이커를 위한 안내서 책 리뷰 | [Korean] Hitchhiker's Guide to the Galaxy Book Review
    - URL: https://www.youtube.com/watch?v=7E51amuXo68
  - [2] [English] Hitchhiker's Guide to the Galaxy Book Review | [영어] 은하수를 여행하는 히치하이커를 위한 안내서 책 리뷰
    - URL: https://www.youtube.com/watch?v=-qHCZQdDUdY
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "은하수를 여행하는 히치하이커를 위한 안내서" ↔ "Hitchhiker's Guide to the Galaxy" 매핑 추가
    - "더글라스 애덤스" ↔ "Douglas Adams" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 자막 생성 로직 개선
- **`src/03_make_video.py`**:
  - Whisper 자막 생성 시 첫 세그먼트 시작 시간 보정 로직 추가
  - 자막 타이밍 검증 및 보정 메서드 추가 (`_validate_and_adjust_subtitle_timing`)
  - 오디오 파일 존재 확인 및 오류 처리 개선
  - 자막 타이밍이 오디오 길이를 초과하지 않도록 보정
  - 중복 제거 및 겹치는 자막 병합 로직 추가
  - 중복 자막 생성 부분 제거 (Summary 부분에만 자막 추가)

### 영문 영상 자막 기본값 변경
- **`src/10_create_video_with_summary.py`**:
  - 영문 영상의 자막 기본값을 비활성화로 변경 (기본적으로 자막 없음)
  - 자막이 필요한 경우 `--subtitles` 플래그로 명시적으로 추가 가능

## 2025-12-21

### 팩트풀니스 영상 제작 및 업로드
- **책 제목**: 팩트풀니스 (Factfulness)
- **저자**: 한스 로슬링 (Hans Rosling)
- **생성된 파일**:
  - 영상: `output/Factfulness_kr.mp4` (226MB), `output/Factfulness_en.mp4` (176MB)
  - 썸네일: `output/Factfulness_thumbnail_kr.jpg`, `output/Factfulness_thumbnail_en.jpg`
  - 메타데이터: `output/Factfulness_kr.metadata.json`, `output/Factfulness_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Factfulness_notebooklm_kr.mp4`, `assets/video/Factfulness_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 팩트풀니스 책 리뷰 | [Korean] Factfulness Book Review
    - URL: https://www.youtube.com/watch?v=iQVuIDkI_kY
  - [2] [English] Factfulness Book Review | [영어] 팩트풀니스 책 리뷰
    - URL: https://www.youtube.com/watch?v=gQRQcLZcscM
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "팩트풀니스" ↔ "Factfulness" 매핑 추가
    - "한스 로슬링" ↔ "Hans Rosling" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 에센셜리즘 영상 제작 및 업로드
- **책 제목**: 에센셜리즘 (Essentialism)
- **저자**: 그렉 맥커운 (Greg McKeown)
- **생성된 파일**:
  - 영상: `output/Essentialism_kr.mp4` (190MB), `output/Essentialism_en.mp4` (163MB)
  - 썸네일: `output/Essentialism_thumbnail_kr.jpg`, `output/Essentialism_thumbnail_en.jpg`
  - 메타데이터: `output/Essentialism_kr.metadata.json`, `output/Essentialism_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Essentialism_notebooklm_kr.mp4`, `assets/video/Essentialism_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 에센셜리즘 책 리뷰 | [Korean] Essentialism Book Review
    - URL: https://www.youtube.com/watch?v=w_7cQGX-hJU
  - [2] [English] Essentialism Book Review | [영어] 에센셜리즘 책 리뷰
    - URL: https://www.youtube.com/watch?v=FeahbmeAqrQ
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "에센셜리즘" ↔ "Essentialism" 매핑 추가
    - "그렉 맥커운" ↔ "Greg McKeown" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 21세기 자본 영상 제작 및 업로드
- **책 제목**: 21세기 자본 (Capital in the Twenty-First Century)
- **저자**: 토마 피케티 (Thomas Piketty)
- **생성된 파일**:
  - 영상: `output/Capital_in_the_Twenty_First_Century_kr.mp4` (213MB), `output/Capital_in_the_Twenty_First_Century_en.mp4` (170MB)
  - 썸네일: `output/Capital_in_the_Twenty_First_Century_thumbnail_kr.jpg`, `output/Capital_in_the_Twenty_First_Century_thumbnail_en.jpg`
  - 메타데이터: `output/Capital_in_the_Twenty_First_Century_kr.metadata.json`, `output/Capital_in_the_Twenty_First_Century_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Capital_in_the_Twenty_First_Century_notebooklm_kr.mp4`, `assets/video/Capital_in_the_Twenty_First_Century_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 21세기 자본 책 리뷰 | [Korean] Capital in the Twenty-First Century Book Review
    - URL: https://www.youtube.com/watch?v=yfWUCESAK-Y
  - [2] [English] Capital in the Twenty-First Century Book Review | [영어] 21세기 자본 책 리뷰
    - URL: https://www.youtube.com/watch?v=EJc2t41JZjg
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "21세기 자본" ↔ "Capital in the Twenty-First Century" 매핑 추가
    - "토마 피케티" ↔ "Thomas Piketty" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 유전자 영상 제작 및 업로드
- **책 제목**: 유전자 (The Gene)
- **저자**: 시다르타 무케르지 (Siddhartha Mukherjee)
- **생성된 파일**:
  - 영상: `output/The_Gene_kr.mp4` (284MB), `output/The_Gene_en.mp4` (255MB)
  - 썸네일: `output/The_Gene_thumbnail_kr.jpg`, `output/The_Gene_thumbnail_en.jpg`
  - 메타데이터: `output/The_Gene_kr.metadata.json`, `output/The_Gene_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Gene_notebooklm_kr.mp4`, `assets/video/The_Gene_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 유전자 책 리뷰 | [Korean] The Gene Book Review
    - URL: https://www.youtube.com/watch?v=t6AnvCfs7oY
  - [2] [English] The Gene Book Review | [영어] 유전자 책 리뷰
    - URL: https://www.youtube.com/watch?v=78yfOUFfftQ
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "유전자" ↔ "The Gene" 매핑 추가
    - "시다르타 무케르지" ↔ "Siddhartha Mukherjee" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 코드 개선
- **`src/09_upload_from_metadata.py`**:
  - YouTube API description 오류 해결을 위한 유니코드 문자 정리 로직 개선
  - 서로게이트 페어 및 제어 문자 제거 로직 추가
  - description 길이 제한 로직 추가 (4500자)

## 2025-12-20

### 호두까기 인형 영상 제작 및 업로드
- **책 제목**: 호두까기 인형 (The Nutcracker)
- **저자**: E.T.A. 호프만 (E.T.A. Hoffmann)
- **생성된 파일**:
  - 영상: `output/The_Nutcracker_kr.mp4` (309MB), `output/The_Nutcracker_en.mp4` (279MB)
  - 썸네일: `output/The_Nutcracker_thumbnail_kr.jpg`, `output/The_Nutcracker_thumbnail_en.jpg`
  - 메타데이터: `output/The_Nutcracker_kr.metadata.json`, `output/The_Nutcracker_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Nutcracker_notebooklm_kr.mp4`, `assets/video/The_Nutcracker_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 호두까기 인형 책 리뷰 | [Korean] The Nutcracker Book Review
    - URL: https://www.youtube.com/watch?v=4ICPrIDNWHo
  - [2] [English] The Nutcracker Book Review | [영어] 호두까기 인형 책 리뷰
    - URL: https://www.youtube.com/watch?v=R-kWXvnBQjo
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "호두까기 인형" ↔ "The Nutcracker" 매핑 추가
    - "E.T.A. 호프만" ↔ "E.T.A. Hoffmann" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 스노우맨 영상 제작 및 업로드
- **책 제목**: 스노우맨 (The Snowman)
- **저자**: 레이먼드 브릭스 (Raymond Briggs)
- **생성된 파일**:
  - 영상: `output/The_Snowman_kr.mp4` (277MB), `output/The_Snowman_en.mp4` (234MB)
  - 썸네일: `output/The_Snowman_thumbnail_kr.jpg`, `output/The_Snowman_thumbnail_en.jpg`
  - 메타데이터: `output/The_Snowman_kr.metadata.json`, `output/The_Snowman_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Snowman_notebooklm_kr.mp4`, `assets/video/The_Snowman_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 스노우맨 책 리뷰 | [Korean] The Snowman Book Review
    - URL: https://www.youtube.com/watch?v=KGfmy7aNzvE
  - [2] [English] The Snowman Book Review | [영어] 스노우맨 책 리뷰
    - URL: https://www.youtube.com/watch?v=dZwrTIh-cKA
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "스노우맨" ↔ "The Snowman" 매핑 추가
    - "레이먼드 브릭스" ↔ "Raymond Briggs" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 크리스마스 선물 영상 제작 및 업로드
- **책 제목**: 크리스마스 선물 (The Gift of the Magi)
- **저자**: 오 헨리 (O. Henry)
- **생성된 파일**:
  - 영상: `output/The_Gift_of_the_Magi_kr.mp4` (308MB), `output/The_Gift_of_the_Magi_en.mp4` (312MB)
  - 썸네일: `output/크리스마스_선물_thumbnail_ko.jpg`, `output/크리스마스_선물_thumbnail_en.jpg`
  - 메타데이터: `output/The_Gift_of_the_Magi_kr.metadata.json`, `output/The_Gift_of_the_Magi_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/The_Gift_of_the_Magi_notebooklm_kr.mp4`, `assets/video/The_Gift_of_the_Magi_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 크리스마스 선물 책 리뷰 | [Korean] The Gift of the Magi Book Review
    - URL: https://www.youtube.com/watch?v=4ICPrIDNWHo
  - [2] [English] The Gift of the Magi Book Review | [영어] 크리스마스 선물 책 리뷰
    - URL: https://www.youtube.com/watch?v=R-kWXvnBQjo
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "크리스마스 선물" ↔ "The Gift of the Magi" 매핑 추가
    - "오 헨리" ↔ "O. Henry" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 코드 개선 및 버그 수정
- **TTS 생성 전 Summary 파일 포맷 정리 기능 추가**:
  - `src/09_text_to_speech.py`: `_clean_markdown_for_tts` 메서드 추가
  - TTS 생성 전에 summary 파일의 마크다운 태그 자동 정리
  - 구조적 태그(`[HOOK]`, `[SUMMARY]`, `[BRIDGE]`), 헤더, 볼드/이탤릭, 리스트 마커 등 제거
  - 정리된 텍스트를 원본 파일에 저장하여 일관성 유지
- **Summary 파일 처리 개선**:
  - `src/10_create_video_with_summary.py`: `_clean_markdown_for_tts` 메서드 추가로 마크다운 태그 제거 및 TTS 최적화
  - Summary 파일 경로 매칭 로직 개선: 영문/한글 제목, `.md`/`.txt` 확장자, `_ko`/`_kr` 접미사 모두 지원
  - NotebookLM 비디오 파일 경로 매칭 로직 개선: 다양한 네이밍 패턴 지원
- **파일 저장 형식 표준화**:
  - `src/08_generate_summary.py`: Summary 파일 저장 형식을 `.txt`에서 `.md`로 변경하여 일관성 확보
- **썸네일 파일 경로 매칭 개선**:
  - `src/09_upload_from_metadata.py`: 한글 제목 기반 썸네일 파일 자동 검색 지원 추가
  - 메타데이터의 책 제목을 활용하여 한글/영문 제목 모두 검색 가능하도록 개선
- **파일 네이밍 표준화**:
  - `scripts/prepare_files_from_downloads.py`: 표준 네이밍 규칙 적용 (영문 제목, `kr` 접미사 통일)
  - `get_standard_safe_title` 함수 사용으로 일관된 파일명 생성
- **Import 경로 수정**:
  - `src/utils/file_utils.py`: `get_standard_safe_title` 함수의 import 경로 수정 (상대 경로 지원 추가)

## 2025-12-19

### 한국어 TTS(OpenAI Nova) 최적화 및 오디오 생성

- **TTS 최적화 및 MP3 제작**:
  - `input/life_summary_kr.md` 파일을 OpenAI Nova 음성에 최적화하여 `assets/summaries/인간의_위대한_여정_summary_ko.md`로 이동 및 저장
  - 구조적 태그(`[HOOK]`, `[SUMMARY]`, `[BRIDGE]`) 제거 및 마크다운 문법 정리로 자연스러운 음성 흐름 확보
  - `scripts/generate_summary_audio.py`를 사용하여 `assets/audio/인간의_위대한_여정_summary_ko.mp3` 생성 완료

- **코드 개선 및 버그 수정**:
  - `src/09_text_to_speech.py`: `utils.retry_utils` 임포트 시 경로 문제 해결을 위한 try-except 구문 추가
  - `scripts/generate_summary_audio.py`: 한국어 요약 파일 검색 시 `_ko.md` 접미사 지원 추가

- **이미지 다양성 개선 및 AI 파싱 수정**:
  - `src/02_get_images.py`: AI 응답 파싱 로직을 개선하여 쉼표(`,`)와 줄바꿈(`\n`)이 혼용된 리스트를 완벽하게 지원 (기존 키워드 누락 해결)
  - `_generate_keywords` (Fallback): AI 실패 시에도 시각적 다양성을 확보할 수 있도록 스웨덴 마을, 빈티지 자동차, 도구함, 추상적 분위기 등 30개 이상의 구체적인 키워드로 목록 확장
  - 필터링 조건 최적화: 'saab'와 같은 구체적이고 유효한 짧은 키워드 허용
  - "오베라는 남자" 이미지를 개선된 로직으로 재수집하여 영상 시각 품질 향상

- **파이프라인 표준화 및 CI 테스트 오류 해결**:
  - `pytest.ini`: `scripts/` 디렉토리를 테스트 수집에서 제외하여 CI 실패 해결
  - `src/utils/file_utils.py`: `get_standard_safe_title` 도입으로 한글/영문 제목에 관계없이 영문 표준 제목으로 디렉토리 관리
  - 파일 접미사 표준화: 한글 `ko` -> `kr`로 통일 (파일명 일관성 확보)
  - `src/10_create_video_with_summary.py` & `src/02_get_images.py`: 표준 명칭 규칙 적용하여 에셋 공유 및 관리 효율화
  - "오베라는 남자" 관련 모든 에셋(요약, 오디오, 영상)을 `A_Man_Called_Ove_[kr/en]` 규칙에 맞춰 일괄 변경


- **다중 TTS 엔진 지원 구현**:
  - `src/09_text_to_speech_multi.py`: OpenAI, Google Cloud TTS, ElevenLabs, Replicate 지원
  - Google Cloud TTS (Neural2) 통합: 빠른 처리 속도 (OpenAI 대비 6-10배), 작은 파일 크기
  - ElevenLabs Multilingual v2 지원 (직접 API 사용)
  - Replicate xtts-v2 지원 (영어 전용, 한글 미지원)

- **TTS 테스트 스크립트 추가**:
  - `scripts/test_tts_providers.py`: 모든 TTS 제공자 비교 테스트
  - `scripts/test_korean_tts.py`: 한글 TTS 음질 비교 테스트
  - `scripts/test_openai_korean_voices.py`: OpenAI TTS 모든 음성 옵션 테스트

- **테스트 결과**:
  - OpenAI TTS: `nova` 음성 사용 중 (한글 자연스러움 우수)
  - Google Cloud TTS Neural2: 매우 빠른 속도, 작은 파일 크기, 한글 완벽 지원
  - OpenAI TTS 음성 옵션: `nova`, `shimmer`, `alloy`, `echo`, `fable`, `onyx` 모두 테스트 완료

- **문서 업데이트**:
  - README.md에 다중 TTS 엔진 지원 섹션 추가
  - 환경 변수 섹션에 TTS 관련 API 키 정보 추가
  - `.gitignore`에 `test_outputs/` 폴더 추가 (테스트 파일 Git 제외)

## 2025-12-16

### 나는 오늘도 경제적 자유를 꿈꾼다 영상 제작 및 업로드
- **책 제목**: 나는 오늘도 경제적 자유를 꿈꾼다 (I Will Teach You to Be Rich)
- **저자**: 람릿 세티 (Ramit Sethi)
- **생성된 파일**:
  - 영상: `output/나는_오늘도_경제적_자유를_꿈꾼다_review_with_summary_ko.mp4` (217MB), `output/나는_오늘도_경제적_자유를_꿈꾼다_review_with_summary_en.mp4` (170MB)
  - 썸네일: `output/나는_오늘도_경제적_자유를_꿈꾼다_thumbnail_ko.jpg`, `output/나는_오늘도_경제적_자유를_꿈꾼다_thumbnail_en.jpg`
  - 메타데이터: `나는_오늘도_경제적_자유를_꿈꾼다_review_with_summary_ko.metadata.json`, `나는_오늘도_경제적_자유를_꿈꾼다_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/나는_오늘도_경제적_자유를_꿈꾼다_notebooklm_ko.mp4`, `assets/video/나는_오늘도_경제적_자유를_꿈꾼다_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] I Will Teach You to Be Rich Book Review | [영어] 나는 오늘도 경제적 자유를 꿈꾼다 책 리뷰
    - URL: https://www.youtube.com/watch?v=N1kzH1BGWoQ
  - [2] [한국어] 나는 오늘도 경제적 자유를 꿈꾼다 책 리뷰 | [Korean] I Will Teach You to Be Rich Book Review
    - URL: https://www.youtube.com/watch?v=SukZxCNZi0U
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "나는 오늘도 경제적 자유를 꿈꾼다" → "I Will Teach You to Be Rich" 매핑 추가
    - "람릿 세티" → "Ramit Sethi" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 일론 머스크 영상 제작 및 업로드
- **책 제목**: 일론 머스크 (Elon Musk)
- **저자**: 월터 아이작슨 (Walter Isaacson)
- **생성된 파일**:
  - 영상: `output/일론_머스크_review_with_summary_ko.mp4` (313MB), `output/일론_머스크_review_with_summary_en.mp4` (280MB)
  - 썸네일: `output/일론_머스크_thumbnail_ko.jpg`, `output/일론_머스크_thumbnail_en.jpg`
  - 메타데이터: `일론_머스크_review_with_summary_ko.metadata.json`, `일론_머스크_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/일론_머스크_notebooklm_ko.mp4`, `assets/video/일론_머스크_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] Elon Musk Book Review | [영어] 일론 머스크 책 리뷰
    - URL: https://www.youtube.com/watch?v=9jYhmK3xscw
  - [2] [한국어] 일론 머스크 책 리뷰 | [Korean] Elon Musk Book Review
    - URL: https://www.youtube.com/watch?v=SJCY1NHKF_E
- **번역 매핑**:
  - **`src/utils/translations.py`**:
    - "일론 머스크" ↔ "Elon Musk" 매핑 이미 존재
    - "월터 아이작슨" ↔ "Walter Isaacson" 매핑 이미 존재
    - 한글/영문 양방향 번역 지원

## 2025-12-15

### 부에 대한 연감 영상 제작 및 업로드
- **책 제목**: 부에 대한 연감 (The Almanack of Naval Ravikant)
- **저자**: 나발 라비칸트 (Naval Ravikant)
- **생성된 파일**:
  - 영상: `output/부에_대한_연감_review_with_summary_ko.mp4` (224MB), `output/부에_대한_연감_review_with_summary_en.mp4` (189MB)
  - 썸네일: `output/부에_대한_연감_thumbnail_ko.jpg`, `output/부에_대한_연감_thumbnail_en.jpg`
  - 메타데이터: `부에_대한_연감_review_with_summary_ko.metadata.json`, `부에_대한_연감_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/부에_대한_연감_notebooklm_ko.mp4`, `assets/video/부에_대한_연감_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] The Almanack of Naval Ravikant Book Review | [영어] 부에 대한 연감 책 리뷰
    - URL: https://www.youtube.com/watch?v=CRiseHhVzBo
  - [2] [한국어] 부에 대한 연감 책 리뷰 | [Korean] The Almanack of Naval Ravikant Book Review
    - URL: https://www.youtube.com/watch?v=XD6qGEPd9VQ
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "부에 대한 연감" → "The Almanack of Naval Ravikant" 매핑 추가
    - "나발 라비칸트" → "Naval Ravikant" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 부의 추월차선 영상 제작 및 업로드
- **책 제목**: 부의 추월차선 (The Millionaire Fastlane)
- **저자**: 엠제이 드마코 (MJ DeMarco)
- **생성된 파일**:
  - 영상: `output/부의_추월차선_review_with_summary_ko.mp4` (200MB), `output/부의_추월차선_review_with_summary_en.mp4` (197MB)
  - 썸네일: `output/부의_추월차선_thumbnail_ko.jpg`, `output/부의_추월차선_thumbnail_en.jpg`
  - 메타데이터: `부의_추월차선_review_with_summary_ko.metadata.json`, `부의_추월차선_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/부의_추월차선_notebooklm_ko.mp4`, `assets/video/부의_추월차선_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] The Millionaire Fastlane Book Review | [영어] 부의 추월차선 책 리뷰
    - URL: https://www.youtube.com/watch?v=mGNH6Zq1Iqk
  - [2] [한국어] 부의 추월차선 책 리뷰 | [Korean] The Millionaire Fastlane Book Review
    - URL: https://www.youtube.com/watch?v=Ox7sxfgXE5k
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "부의 추월차선" → "The Millionaire Fastlane" 매핑 추가
    - "엠제이 드마코" → "MJ DeMarco" 매핑 추가
    - 한글/영문 양방향 번역 지원

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

### 자막 기능 개선: Whisper 단어 단위 타이밍 및 언어별 자동 설정
- **Whisper 단어 단위 타이밍 구현**:
  - **`src/03_make_video.py`**:
    - `generate_subtitles_from_text()` 메서드에 `audio_path` 파라미터 추가
    - Whisper의 `word_timestamps=True` 옵션으로 단어 단위 타임스탬프 사용
    - `_align_words_to_sentences()` 메서드 추가: 원본 문장의 단어를 Whisper 단어 타임스탬프와 매칭
    - 단어 단위 정렬 알고리즘으로 정확한 타이밍 계산
    - 폴백 메커니즘: 단어 타임스탬프 실패 시 세그먼트 단위, 그 실패 시 텍스트 기반 방식으로 전환
- **언어별 자동 자막 설정**:
  - **`src/10_create_video_with_summary.py`**:
    - 언어에 따라 자막 기본값 자동 설정
    - 한글 (`ko`): 자막 없음 (기본값)
    - 영어 (`en`): 자막 있음 (기본값)
    - `--no-subtitles`, `--subtitles` 옵션으로 수동 제어 가능
- **의존성 추가**:
  - `openai-whisper` 패키지 설치 필요 (단어 단위 타이밍 사용)
- **영상 제작 결과**:
  - 영어 버전: 21개의 자막 생성 완료 (Whisper 단어 단위 타이밍 사용)
  - 한글 버전: 기존 파일 유지 (자막 포함 버전)

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

## 2025-12-15

### YouTube 업로드 완료
- 업로드된 책: 부에_대한_연감_with_summary_en, 부에_대한_연감_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] The Almanack of Naval Ravikant Book Review | [영어] 부에 대한 연감 책 리뷰
  - URL: https://www.youtube.com/watch?v=CRiseHhVzBo
- [2] [한국어] 부에 대한 연감 책 리뷰 | [Korean] The Almanack of Naval Ravikant Book Review
  - URL: https://www.youtube.com/watch?v=XD6qGEPd9VQ

## 2025-12-15

### YouTube 업로드 완료
- 업로드된 책: 부의_추월차선_with_summary_en, 부의_추월차선_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] The Millionaire Fastlane Book Review | [영어] 부의 추월차선 책 리뷰
  - URL: https://www.youtube.com/watch?v=mGNH6Zq1Iqk
- [2] [한국어] 부의 추월차선 책 리뷰 | [Korean] The Millionaire Fastlane Book Review
  - URL: https://www.youtube.com/watch?v=Ox7sxfgXE5k

## 2025-12-16

### YouTube 업로드 완료
- 업로드된 책: 나는_오늘도_경제적_자유를_꿈꾼다_with_summary_en, 나는_오늘도_경제적_자유를_꿈꾼다_with_summary_ko
- 업로드된 영상 수: 2개
- [1] [English] I Will Teach You to Be Rich Book Review | [영어] 나는 오늘도 경제적 자유를 꿈꾼다 책 리뷰
  - URL: https://www.youtube.com/watch?v=N1kzH1BGWoQ
- [2] [한국어] 나는 오늘도 경제적 자유를 꿈꾼다 책 리뷰 | [Korean] I Will Teach You to Be Rich Book Review
  - URL: https://www.youtube.com/watch?v=SukZxCNZi0U

## 2025-12-16

### YouTube 업로드 완료
- 업로드된 책: 일론_머스크_with_summary_ko, 일론_머스크_with_summary_en
- 업로드된 영상 수: 2개
- [1] [English] Elon Musk Book Review | [영어] 일론 머스크 책 리뷰
  - URL: https://www.youtube.com/watch?v=9jYhmK3xscw
- [2] [한국어] 일론 머스크 책 리뷰 | [Korean] Elon Musk Book Review
  - URL: https://www.youtube.com/watch?v=SJCY1NHKF_E

## 2025-12-18

### 남아 있는 나날 영상 제작 및 업로드
- **책 제목**: 남아 있는 나날 (The Remains of the Day)
- **저자**: 가즈오 이시구로 (Kazuo Ishiguro)
- **생성된 파일**:
  - 영상: `output/남아_있는_나날_review_with_summary_ko.mp4` (310.58MB), `output/남아_있는_나날_review_with_summary_en.mp4` (291.63MB)
  - 썸네일: `output/남아_있는_나날_thumbnail_ko.jpg`, `output/남아_있는_나날_thumbnail_en.jpg`
  - 메타데이터: `남아_있는_나날_review_with_summary_ko.metadata.json`, `남아_있는_나날_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/남아_있는_나날_notebooklm_ko.mp4`, `assets/video/남아_있는_나날_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] The Remains of the Day Book Review | [영어] 남아 있는 나날 책 리뷰
    - URL: https://www.youtube.com/watch?v=yl9qJnCwLe0
  - [2] [한국어] 남아 있는 나날 책 리뷰 | [Korean] The Remains of the Day Book Review
    - URL: https://www.youtube.com/watch?v=97pm29WSdGg
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "남아 있는 나날" → "The Remains of the Day" 매핑 추가
    - "가즈오 이시구로" → "Kazuo Ishiguro" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-18

### 남아 있는 나날 영상 제작 및 업로드
- **책 제목**: 남아 있는 나날 (The Remains of the Day)
- **저자**: 가즈오 이시구로 (Kazuo Ishiguro)
- **생성된 파일**:
  - 영상: `output/남아_있는_나날_review_with_summary_ko.mp4` (310.58MB), `output/남아_있는_나날_review_with_summary_en.mp4` (291.63MB)
  - 썸네일: `output/남아_있는_나날_thumbnail_ko.jpg`, `output/남아_있는_나날_thumbnail_en.jpg`
  - 메타데이터: `남아_있는_나날_review_with_summary_ko.metadata.json`, `남아_있는_나날_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/남아_있는_나날_notebooklm_ko.mp4`, `assets/video/남아_있는_나날_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] The Remains of the Day Book Review | [영어] 남아 있는 나날 책 리뷰
    - URL: https://www.youtube.com/watch?v=yl9qJnCwLe0
  - [2] [한국어] 남아 있는 나날 책 리뷰 | [Korean] The Remains of the Day Book Review
    - URL: https://www.youtube.com/watch?v=97pm29WSdGg
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "남아 있는 나날" → "The Remains of the Day" 매핑 추가
    - "가즈오 이시구로" → "Kazuo Ishiguro" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 인간의 위대한 여정 영상 제작 및 업로드
- **책 제목**: 인간의 위대한 여정 (The Life Cycle Completed)
- **저자**: 에릭 에릭슨 (Erik Erikson)
- **생성된 파일**:
  - 영상: `output/인간의_위대한_여정_review_with_summary_ko.mp4` (265.94MB), `output/인간의_위대한_여정_review_with_summary_en.mp4` (200.40MB)
  - 썸네일: `output/인간의_위대한_여정_thumbnail_ko.jpg`, `output/인간의_위대한_여정_thumbnail_en.jpg`
  - 메타데이터: `인간의_위대한_여정_review_with_summary_ko.metadata.json`, `인간의_위대한_여정_review_with_summary_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/인간의_위대한_여정_notebooklm_ko.mp4`, `assets/video/인간의_위대한_여정_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [English] The Life Cycle Completed Book Review | [영어] 인간의 위대한 여정 책 리뷰
    - URL: https://www.youtube.com/watch?v=fONzPiWlCnA
  - [2] [한국어] 인간의 위대한 여정 책 리뷰 | [Korean] The Life Cycle Completed Book Review
    - URL: https://www.youtube.com/watch?v=naDfKUkRARY
- **번역 매핑 추가**:
- **`src/utils/translations.py`**:
    - "인간의 위대한 여정" → "The Life Cycle Completed" 매핑 추가
    - "에릭 에릭슨" → "Erik Erikson" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-19

### YouTube 업로드 완료 (오베라는 남자)
- **책**: [오베라는 남자](https://www.youtube.com/watch?v=Mzg-8-i2XcM) (프레드릭 배크만)
- **변경 사항**: 
  - 파이프라인 표준화(영문 제목 디렉토리, `kr` 접미사) 적용
  - 이미지 다양성 로직(AI 파싱 수정, Fallback 확장) 적용
  - 썸네일 용량 최적화 및 `.jpg` 변환 적용
- **업로드 된 영상**:
  - [한국어] https://www.youtube.com/watch?v=Mzg-8-i2XcM
  - [영어] https://www.youtube.com/watch?v=4NjPhyS-0_w

## 2025-12-20

### YouTube 업로드 완료
- 업로드된 책: The_Gift_of_the_Magi
- 업로드된 영상 수: 2개
- [1] [English] The Gift of the Magi Book Review | [영어] 크리스마스 선물 책 리뷰
  - URL: https://www.youtube.com/watch?v=R-kWXvnBQjo
- [2] [한국어] 크리스마스 선물 책 리뷰 | [Korean] The Gift of the Magi Book Review
  - URL: https://www.youtube.com/watch?v=4ICPrIDNWHo

## 2025-12-20

### YouTube 업로드 완료
- 업로드된 책: The_Nutcracker
- 업로드된 영상 수: 2개
- [1] [English] The Nutcracker Book Review | [영어] 호두까기 인형 책 리뷰
  - URL: https://www.youtube.com/watch?v=hqTB3WtSUv0
- [2] [한국어] 호두까기 인형 책 리뷰 | [Korean] The Nutcracker Book Review
  - URL: https://www.youtube.com/watch?v=5t6s17HK04k

## 2025-12-20

### YouTube 업로드 완료
- 업로드된 책: The_Snowman
- 업로드된 영상 수: 2개
- [1] [English] The Snowman Book Review | [영어] 스노우맨 책 리뷰
  - URL: https://www.youtube.com/watch?v=dZwrTIh-cKA
- [2] [한국어] 스노우맨 책 리뷰 | [Korean] The Snowman Book Review
  - URL: https://www.youtube.com/watch?v=KGfmy7aNzvE

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Essentialism
- 업로드된 영상 수: 2개
- [1] [English] Essentialism Book Review | [영어] 에센셜리즘 책 리뷰
  - URL: https://www.youtube.com/watch?v=FeahbmeAqrQ
- [2] [한국어] 에센셜리즘 책 리뷰 | [Korean] Essentialism Book Review
  - URL: https://www.youtube.com/watch?v=w_7cQGX-hJU

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Factfulness
- 업로드된 영상 수: 2개
- [1] [English] Factfulness Book Review | [영어] 팩트풀니스 책 리뷰
  - URL: https://www.youtube.com/watch?v=gQRQcLZcscM
- [2] [한국어] 팩트풀니스 책 리뷰 | [Korean] Factfulness Book Review
  - URL: https://www.youtube.com/watch?v=iQVuIDkI_kY

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Capital_in_the_Twenty_First_Century
- 업로드된 영상 수: 1개
- [1] [English] Capital in the Twenty-First Century Book Review | [영어] 21세기 자본 책 리뷰
  - URL: https://www.youtube.com/watch?v=ovaV8KnqySA

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Capital_in_the_Twenty_First_Century
- 업로드된 영상 수: 1개
- [1] [English] Capital in the Twenty-First Century Book Review | [영어] 21세기 자본 책 리뷰
  - URL: https://www.youtube.com/watch?v=vD2-PhO9rcs

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Capital_in_the_Twenty_First_Century
- 업로드된 영상 수: 1개
- [1] [English] Capital in the Twenty-First Century Book Review | [영어] 21세기 자본 책 리뷰
  - URL: https://www.youtube.com/watch?v=sKQP1GhTBvQ

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: Capital_in_the_Twenty_First_Century
  - 업로드된 영상 수: 2개
- [1] [English] Capital in the Twenty-First Century Book Review | [영어] 21세기 자본 책 리뷰
  - URL: https://www.youtube.com/watch?v=EJc2t41JZjg
- [2] [한국어] 21세기 자본 책 리뷰 | [Korean] Capital in the Twenty-First Century Book Review
  - URL: https://www.youtube.com/watch?v=yfWUCESAK-Y

## 2025-12-21

### YouTube 업로드 완료
- 업로드된 책: The_Gene
  - 업로드된 영상 수: 2개
- [1] [English] The Gene Book Review | [영어] 유전자 책 리뷰
  - URL: https://www.youtube.com/watch?v=78yfOUFfftQ
- [2] [한국어] 유전자 책 리뷰 | [Korean] The Gene Book Review
  - URL: https://www.youtube.com/watch?v=t6AnvCfs7oY

## 2025-12-22

### YouTube 업로드 완료
- 업로드된 책: Hitchhikers_Guide_to_the_Galaxy
- 업로드된 영상 수: 2개
- [1] [English] Hitchhiker's Guide to the Galaxy Book Review | [영어] 은하수를 여행하는 히치하이커를 위한 안내서 책 리뷰
  - URL: https://www.youtube.com/watch?v=-qHCZQdDUdY
- [2] [한국어] 은하수를 여행하는 히치하이커를 위한 안내서 책 리뷰 | [Korean] Hitchhiker's Guide to the Galaxy Book Review
  - URL: https://www.youtube.com/watch?v=7E51amuXo68

## 2025-12-22

### YouTube 업로드 완료
- 업로드된 책: Gödel_Escher_Bach_An_Eternal_Golden_Braid
- 업로드된 영상 수: 2개
- [1] [English] Gödel, Escher, Bach: An Eternal Golden Braid Book Review | [영어] 괴델, 에셔, 바흐 책 리뷰
  - URL: https://www.youtube.com/watch?v=5Pe8jgivfYM
- [2] [한국어] 괴델, 에셔, 바흐 책 리뷰 | [Korean] Gödel, Escher, Bach: An Eternal Golden Braid Book Review
  - URL: https://www.youtube.com/watch?v=cA-U5OXTugE

## 2025-12-23

### YouTube 업로드 완료
- 업로드된 책: The_Sixth_Extinction
- 업로드된 영상 수: 2개
- [1] [English] The Sixth Extinction Book Review | [영어] 여섯 번째 대멸종 책 리뷰
  - URL: https://www.youtube.com/watch?v=fD7RBmbf-Bc
- [2] [한국어] 여섯 번째 대멸종 책 리뷰 | [Korean] The Sixth Extinction Book Review
  - URL: https://www.youtube.com/watch?v=v6Xet3dhrZk

## 2025-12-23

### YouTube 업로드 완료
- 업로드된 책: The_Intelligent_Investor
- 업로드된 영상 수: 2개
- [1] [English] The Intelligent Investor Book Review | [영어] 현명한 투자자 책 리뷰
  - URL: https://www.youtube.com/watch?v=mG0xEQ1hPm0
- [2] [한국어] 현명한 투자자 책 리뷰 | [Korean] The Intelligent Investor Book Review
  - URL: https://www.youtube.com/watch?v=eRLZ-aOE61E

## 2025-12-24

### YouTube 업로드 완료
- 업로드된 책: Rich_Dad_Poor_Dad
- 업로드된 영상 수: 2개
- [1] [English] Rich Dad Poor Dad Book Review | [영어] 부자 아빠 가난한 아빠 책 리뷰
  - URL: https://www.youtube.com/watch?v=9yGHSygpNN8
- [2] [한국어] 부자 아빠 가난한 아빠 책 리뷰 | [Korean] Rich Dad Poor Dad Book Review
  - URL: https://www.youtube.com/watch?v=Qf9ftpgh2Zk

## 2025-12-24

### YouTube 업로드 완료
- 업로드된 책: Deep_Work
- 업로드된 영상 수: 2개
- [1] [English] Deep Work Book Review | [영어] 딥 워크 책 리뷰
  - URL: https://www.youtube.com/watch?v=aPo9cZ1JH8k
- [2] [한국어] 딥 워크 책 리뷰 | [Korean] Deep Work Book Review
  - URL: https://www.youtube.com/watch?v=i4zgz6zT_G8

## 2025-12-24

### YouTube 업로드 완료
- 업로드된 책: The_Almanack_of_Naval_Ravikant
- 업로드된 영상 수: 2개
- [1] [English] The Almanack of Naval Ravikant Book Review | [영어] 네이벌 라비칸트 연감 책 리뷰
  - URL: https://www.youtube.com/watch?v=n_Yfo41vuRc
- [2] [한국어] 네이벌 라비칸트 연감 책 리뷰 | [Korean] The Almanack of Naval Ravikant Book Review
  - URL: https://www.youtube.com/watch?v=6FE_pZDtePM

## 2025-12-25

### 생각에 관한 생각 영상 제작 및 업로드
- **책 제목**: 생각에 관한 생각 (Thinking, Fast and Slow)
- **저자**: 대니얼 카너먼 (Daniel Kahneman)
- **생성된 파일**:
  - 영상: `output/Thinking_Fast_and_Slow_kr.mp4` (235MB), `output/Thinking_Fast_and_Slow_en.mp4` (208MB)
  - 썸네일: `output/Thinking_Fast_and_Slow_thumbnail_kr.jpg`, `output/Thinking_Fast_and_Slow_thumbnail_en.jpg`
  - 메타데이터: `output/Thinking_Fast_and_Slow_kr.metadata.json`, `output/Thinking_Fast_and_Slow_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Thinking_Fast_and_Slow_notebooklm_kr.mp4`, `assets/video/Thinking_Fast_and_Slow_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 생각에 관한 생각 책 리뷰 | [Korean] Thinking, Fast and Slow Book Review
    - URL: https://www.youtube.com/watch?v=EDfOZfYtCbI
  - [2] [English] Thinking, Fast and Slow Book Review | [영어] 생각에 관한 생각 책 리뷰
    - URL: https://www.youtube.com/watch?v=GNTBUL9ic5k
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "생각에 관한 생각" ↔ "Thinking, Fast and Slow" 매핑 추가
    - "대니얼 카너먼" ↔ "Daniel Kahneman" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-26

### 명상록 영상 제작 및 업로드
- **책 제목**: 명상록 (Meditations)
- **저자**: 마르쿠스 아우렐리우스 (Marcus Aurelius)
- **생성된 파일**:
  - 영상: `output/Meditations_kr.mp4` (321MB), `output/Meditations_en.mp4` (264MB)
  - 썸네일: `output/Meditations_thumbnail_kr.jpg`, `output/Meditations_thumbnail_en.jpg`
  - 메타데이터: `output/Meditations_kr.metadata.json`, `output/Meditations_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Meditations_notebooklm_kr.mp4`, `assets/video/Meditations_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 명상록 책 리뷰 | [Korean] Meditations Book Review
    - URL: https://www.youtube.com/watch?v=-mt0I3u9XPE
  - [2] [English] Meditations Book Review | [영어] 명상록 책 리뷰
    - URL: https://www.youtube.com/watch?v=vbbKT1nrdko
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "명상록" ↔ "Meditations" 매핑 추가
    - "마르쿠스 아우렐리우스" ↔ "Marcus Aurelius" 매핑 추가
    - 한글/영문 양방향 번역 지원

### 랜덤워크에 속지 마라 영상 제작 및 업로드
- **책 제목**: 랜덤워크에 속지 마라 (Fooled by Randomness)
- **저자**: 나심 탈레브 (Nassim Taleb)
- **생성된 파일**:
  - 영상: `output/Fooled_by_Randomness_kr.mp4` (246MB), `output/Fooled_by_Randomness_en.mp4` (197MB)
  - 썸네일: `output/Fooled_by_Randomness_thumbnail_kr.jpg`, `output/Fooled_by_Randomness_thumbnail_en.jpg`
  - 메타데이터: `output/Fooled_by_Randomness_kr.metadata.json`, `output/Fooled_by_Randomness_en.metadata.json`
  - 이미지: 100개 무드 이미지 다운로드 완료
  - 오디오: 요약 오디오 (한글/영문) 생성 완료
  - NotebookLM 비디오: `assets/video/Fooled_by_Randomness_notebooklm_kr.mp4`, `assets/video/Fooled_by_Randomness_notebooklm_en.mp4`
- **YouTube 업로드 완료 (비공개)**:
  - [1] [한국어] 랜덤워크에 속지 마라 책 리뷰 | [Korean] Fooled by Randomness Book Review
    - URL: https://www.youtube.com/watch?v=g2CMGEZIiKk
  - [2] [English] Fooled by Randomness Book Review | [영어] 랜덤워크에 속지 마라 책 리뷰
    - URL: https://www.youtube.com/watch?v=58kWvjPhs1M
- **번역 매핑 추가**:
  - **`src/utils/translations.py`**:
    - "랜덤워크에 속지 마라" ↔ "Fooled by Randomness" 매핑 추가
    - "나심 탈레브" ↔ "Nassim Taleb" 매핑 추가
    - 한글/영문 양방향 번역 지원

## 2025-12-26

### YouTube 업로드 완료
- 업로드된 책: No_Excuses_The_Power_of_Self_Discipline
- 업로드된 영상 수: 2개
- [1] [English] No Excuses!: The Power of Self-Discipline Book Review | [영어] 행동하지 않으면 인생은 바뀌지 않는다 책 리뷰
  - URL: https://www.youtube.com/watch?v=XMr661ly1UU
- [2] [한국어] 행동하지 않으면 인생은 바뀌지 않는다 책 리뷰 | [Korean] No Excuses!: The Power of Self-Discipline Book Review
  - URL: https://www.youtube.com/watch?v=cnMPYf727lk

## 2025-12-26

### YouTube 업로드 완료
- 업로드된 책: Snow_Country
- 업로드된 영상 수: 2개
- [1] [English] Snow Country Book Review | [영어] 설국 책 리뷰
  - URL: https://www.youtube.com/watch?v=MlXg0nvIziE
- [2] [한국어] 설국 책 리뷰 | [Korean] Snow Country Book Review
  - URL: https://www.youtube.com/watch?v=x2qoMiJ02Xw

## 2025-12-27

### YouTube 업로드 완료
- 업로드된 책: Factfulness
- 업로드된 영상 수: 1개
- [1] [English] Factfulness Book Review | [영어] 팩트풀니스 책 리뷰
  - URL: https://www.youtube.com/watch?v=cxUJc-Cp-Ds

## 2025-12-27

### YouTube 업로드 완료
- 업로드된 책: Factfulness
- 업로드된 영상 수: 1개
- [1] [English] Factfulness Book Review | [영어] 팩트풀니스 책 리뷰
  - URL: https://www.youtube.com/watch?v=rz5EpYOZCsI

## 2025-12-27

### YouTube 업로드 완료
- 업로드된 책: Frankenstein
- 업로드된 영상 수: 2개
- [1] [English] Frankenstein Book Review | [영어] 프랑켄슈타인 책 리뷰
  - URL: https://www.youtube.com/watch?v=3JrwQ45fngk
- [2] [한국어] 프랑켄슈타인 책 리뷰 | [Korean] Frankenstein Book Review
  - URL: https://www.youtube.com/watch?v=Rx7RpKTkjaY

## 2025-12-27

### YouTube 업로드 완료
- 업로드된 책: The_Sorrows_of_Young_Werther
- 업로드된 영상 수: 2개
- [1] [English] The Sorrows of Young Werther Book Review | [영어] 젊은 베르테르의 슬픔 책 리뷰
  - URL: https://www.youtube.com/watch?v=rf1R09G4hnw
- [2] [한국어] 젊은 베르테르의 슬픔 책 리뷰 | [Korean] The Sorrows of Young Werther Book Review
  - URL: https://www.youtube.com/watch?v=l7Zw32e_u0A

## 2025-12-27

### YouTube 업로드 완료
- 업로드된 책: Frankenstein
- 업로드된 영상 수: 1개
- [1] [한국어] 프랑켄슈타인 책 리뷰 | [Korean] Frankenstein Book Review
  - URL: https://www.youtube.com/watch?v=KsoVW_dHzN4

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: Thus_Spoke_Zarathustra
- 업로드된 영상 수: 2개
- [1] [English] Thus Spoke Zarathustra Book Review | [영어] 차라투스트라는 이렇게 말했다 책 리뷰
  - URL: https://www.youtube.com/watch?v=CN2t7vtRbSQ
- [2] [한국어] 차라투스트라는 이렇게 말했다 책 리뷰 | [Korean] Thus Spoke Zarathustra Book Review
  - URL: https://www.youtube.com/watch?v=kHapabFebCk

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: The_Old_Man_and_the_Sea
- 업로드된 영상 수: 2개
- [1] [English] The Old Man and the Sea Book Review | [영어] 노인과 바다 책 리뷰
  - URL: https://www.youtube.com/watch?v=_AqE6HnRJfc
- [2] [한국어] 노인과 바다 책 리뷰 | [Korean] The Old Man and the Sea Book Review
  - URL: https://www.youtube.com/watch?v=cRcf2WF8iqo

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: The_Stranger
- 업로드된 영상 수: 2개
- [1] [English] The Stranger Book Review | [영어] 이방인 책 리뷰
  - URL: https://www.youtube.com/watch?v=I_Y9XgI3bq4
- [2] [한국어] 이방인 책 리뷰 | [Korean] The Stranger Book Review
  - URL: https://www.youtube.com/watch?v=Tkto3zlCbpI

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: The_Metamorphosis
- 업로드된 영상 수: 2개
- [1] [English] The Metamorphosis Book Review | [영어] 변신 책 리뷰
  - URL: https://www.youtube.com/watch?v=6shKy3oZHeM
- [2] [한국어] 변신 책 리뷰 | [Korean] The Metamorphosis Book Review
  - URL: https://www.youtube.com/watch?v=pUdbmweOY0s

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: Jane_Eyre
- 업로드된 영상 수: 2개
- [1] [English] Jane Eyre Book Review | [영어] 제인 에어 책 리뷰
  - URL: https://www.youtube.com/watch?v=bEYUYAxR0Bo
- [2] [한국어] 제인 에어 책 리뷰 | [Korean] Jane Eyre Book Review
  - URL: https://www.youtube.com/watch?v=bnSKi6eURFM

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: 마키아벨리_군주론_깨어있는_시민을_위한_필요악_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 마키아벨리 군주론: 깨어있는 시민을 위한 필요악 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=UVMpO5zZE-E

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: 마키아벨리_군주론_깨어있는_시민을_위한_필요악_full_episode
- 업로드된 영상 수: 1개
- [1] The Prince: A Necessary Evil for Awakened Citizens
  - URL: https://www.youtube.com/watch?v=HchRMda0H0s

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: 솔로몬의_반지_full_episode_ko, 솔로몬의_반지_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to King Solomon's Ring | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=e6ERsEe7PQI
- [2] [일당백] 솔로몬의 반지 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=Gqkn2b9VFPQ

## 2025-12-31

### YouTube 업로드 완료
- 업로드된 책: 오이디푸스_왕_full_episode_ko, 오이디푸스_왕_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to 오이디푸스 왕 | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=Q5ivHLSi_TA
- [2] [일당백] 오이디푸스 왕 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=NSQxPSsz3hA

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: Crime_and_Punishment_full_episode_ko, Crime_and_Punishment_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to Crime and Punishment | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=QAL6D7FNj60
- [2] [일당백] 죄와 벌 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=NLnM6QLxQgM

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: 톰_소여의_모험_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 톰 소여의 모험 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=cLBsSAYMaqw

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: 톰_소여의_모험_full_episode
- 업로드된 영상 수: 1개
- [1] Complete Guide to The Adventures of Tom Sawyer | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=8NSM-7CNui8

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: 두_개의_한국_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 두 개의 한국 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=S7DbsMrD7R0

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: The_Two_Koreas_full_episode
- 업로드된 영상 수: 1개
- [1] Complete Guide to The Two Koreas | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=GXtwQzzG3P4

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: 아라비안_나이트_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 아라비안 나이트 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=x1yNhaTYQaI

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: Arabian_Nights_full_episode
- 업로드된 영상 수: 1개
- [1] Complete Guide to Arabian Nights | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=U84k0BSLQ-o

## 2026-01-01

### YouTube 업로드 완료
- 업로드된 책: The_Art_of_War_full_episode, 손자병법_full_episode_ko
- 업로드된 영상 수: 2개
- [1] Complete Guide to The Art of War | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=AzSmjYsNR1U
- [2] [일당백] 손자병법 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=u263sE-Veq8

## 2026-01-01

### 일당백 스타일 에피소드 영상 제작 및 업로드
- **작업 내용**:
  - 일당백 스타일 에피소드 영상 제작 워크플로우를 사용하여 여러 책의 한글/영문 영상 생성 및 업로드
  - 번역 매핑 추가: 죄와 벌, 톰 소여의 모험, 두 개의 한국, 아라비안 나이트, 손자병법, 제4차산업혁명
  - 영문 메타데이터 개선: 소설이 아닌 책(비소설)의 경우 태그 및 설명 수정 (Novel → Book, story → concepts)
- **수정된 파일**:
  - `src/utils/translations.py`: 번역 매핑 추가
    - "죄와 벌" ↔ "Crime and Punishment"
    - "톰 소여의 모험" ↔ "The Adventures of Tom Sawyer"
    - "두 개의 한국" ↔ "The Two Koreas"
    - "아라비안 나이트" ↔ "Arabian Nights"
    - "손자병법" ↔ "The Art of War"
    - "제4차산업혁명" ↔ "The Fourth Industrial Revolution"
- **생성 및 업로드된 영상**:
  - 죄와 벌 (Crime and Punishment)
    - 한글: https://www.youtube.com/watch?v=NLnM6QLxQgM (14분 27초, 518.35MB)
    - 영문: https://www.youtube.com/watch?v=QAL6D7FNj60 (15분 39초, 572.65MB)
  - 톰 소여의 모험 (The Adventures of Tom Sawyer)
    - 한글: https://www.youtube.com/watch?v=cLBsSAYMaqw (16분 16초, 584.78MB)
    - 영문: https://www.youtube.com/watch?v=8NSM-7CNui8 (12분 52초, 476.72MB)
  - 두 개의 한국 (The Two Koreas)
    - 한글: https://www.youtube.com/watch?v=S7DbsMrD7R0 (15분 7초, 466.06MB)
    - 영문: https://www.youtube.com/watch?v=GXtwQzzG3P4 (14분 36초, 484.88MB)
  - 아라비안 나이트 (Arabian Nights)
    - 한글: https://www.youtube.com/watch?v=x1yNhaTYQaI (14분 6초, 542.66MB)
    - 영문: https://www.youtube.com/watch?v=U84k0BSLQ-o (13분 38초, 513.74MB)
  - 손자병법 (The Art of War)
    - 한글: https://www.youtube.com/watch?v=u263sE-Veq8 (15분 53초, 505.07MB)
    - 영문: https://www.youtube.com/watch?v=AzSmjYsNR1U (13분 34초, 467.60MB)
  - 제4차산업혁명 (The Fourth Industrial Revolution)
    - 한글: https://www.youtube.com/watch?v=6ioZEQkdkj0 (15분 57초, 348.76MB)
    - 영문: https://www.youtube.com/watch?v=s5xtSOl1l6E (12분 30초, 355.26MB)

### YouTube 자막 추출 스크립트 개선 (쿠키 지원 추가)
- **작업 내용**:
  - `scripts/fetch_separate_scripts.py`에 쿠키 지원 기능 추가
  - IP 차단 우회를 위한 쿠키 파일 사용 기능 구현
  - `MozillaCookieJar`를 사용하여 Netscape 쿠키 형식 파일 로드
  - `requests.Session`에 쿠키 추가 및 `YouTubeTranscriptApi`에 전달
  - User-Agent 헤더 추가로 브라우저처럼 보이도록 개선
- **수정된 파일**:
  - `scripts/fetch_separate_scripts.py`: 쿠키 지원 기능 추가
    - `load_cookies_into_session()` 함수 추가: 쿠키 파일을 로드하여 `requests.Session`에 추가
    - `fetch_transcript()` 함수에 `cookies_path` 파라미터 추가
    - `--cookies` 명령줄 인자 추가
    - 에러 메시지 개선 (에러 타입 및 상세 메시지 출력)
  - `.gitignore`: `scripts/cookies.txt` 추가 (개인 정보 보호)
- **사용 방법**:
  ```bash
  # 쿠키 파일 준비:
  # 1. Chrome 확장프로그램 "Get cookies.txt LOCALLY" 설치
  # 2. YouTube에 로그인한 상태에서 쿠키를 cookies.txt로 다운로드
  # 3. scripts/ 폴더에 cookies.txt 저장
  
  # 쿠키 사용 (자동 감지):
  python scripts/fetch_separate_scripts.py \
    --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \
    --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \
    --title "책 제목"
  
  # 쿠키 파일 경로 지정:
  python scripts/fetch_separate_scripts.py \
    --url1 "https://www.youtube.com/watch?v=VIDEO_ID_1" \
    --url2 "https://www.youtube.com/watch?v=VIDEO_ID_2" \
    --title "책 제목" \
    --cookies "scripts/cookies.txt"
  ```
- **참고사항**:
  - 쿠키 파일이 `scripts/cookies.txt`에 있으면 자동으로 사용됨
  - 쿠키를 사용해도 IP 차단이 발생할 수 있음 (YouTube의 정책에 따라)
  - IP 차단 시 VPN 사용 또는 다른 네트워크에서 시도 권장

## 2026-01-02

### YouTube 업로드 완료
- 업로드된 책: The_God_Delusion_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 만들어진 신 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=Igfe76gOXGY

## 2026-01-02

### YouTube 업로드 완료
- 업로드된 책: The_God_Delusion_full_episode
- 업로드된 영상 수: 1개
- [1] Complete Guide to The God Delusion | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=F2CZD4l8LXM

## 2026-01-02

### YouTube 업로드 완료
- 업로드된 책: A_Small_Ball_Shot_Up_by_a_Dwarf_full_episode_ko, A_Small_Ball_Shot_Up_by_a_Dwarf_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to A Small Ball Shot Up by a Dwarf | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=c_MM0EBuzZo
- [2] [일당백] 난장이가 쏘아올린 작은 공 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=gnDFPNAH7s0

## 2026-01-02

### YouTube 업로드 완료
- 업로드된 책: Platos_Dialogues_Philosophy_is_Love_full_episode, Platos_Dialogues_Philosophy_is_Love_full_episode_ko
- 업로드된 영상 수: 2개
- [1] Complete Guide to Plato's Dialogues: Philosophy is Love | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=fdlOWCGa5po
- [2] [일당백] 플라톤 대화편 : 철학은 사랑이다 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=0HDaR9ZwXMA

## 2026-01-02

### YouTube 업로드 완료
- 업로드된 책: The_Great_Gatsby_full_episode_ko, The_Great_Gatsby_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to The Great Gatsby | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=y5GvpwX1jdc
- [2] [일당백] 위대한 개츠비 : 가난한 청년은 부잣집 딸과 결혼할 수 없는가? 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=2_aMxbFUBLQ

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: Das_Kapital_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 카를 마르크스 자본론 : 뭉치면 살고 흩어지면 죽는다 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=QP4LlM0sy2Y

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: Das_Kapital_full_episode
- 업로드된 영상 수: 1개
- [1] Complete Guide to Das Kapital | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=aeUoPueRi4M

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: The_Essence_of_Poetry_and_Masters_On_Korean_Poetry_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 시의 본질과 거장들: 한국시에 대하여 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=s9QJEcOq74Q

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: The_Essence_of_Poetry_and_Masters_On_Korean_Poetry_full_episode
- 업로드된 영상 수: 1개
- [1] The Essence of Poetry and Masters: Complete Guide | Author, Background & Full Story
  - URL: https://www.youtube.com/watch?v=L4MM0kjUgFk

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: Yukio_Mishima_Patriotism_and_The_Temple_of_the_Golden_Pavilion_full_episode_ko
- 업로드된 영상 수: 1개
- [1] [일당백] 미시마 유키오 우국, 금각사 : 아름답게 죽어라는 일본, 어떻게든 살아라는 한국 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=SwtiS91WQCQ

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: Yukio_Mishima_Patriotism_and_The_Temple_of_the_Golden_Pavilion_full_episode
- 업로드된 영상 수: 1개
- [1] Yukio Mishima: Patriotism and The Golden Pavilion | Complete Guide | Author & Full Story
  - URL: https://www.youtube.com/watch?v=irJaMfCmaHA

## 2026-01-03

### YouTube 업로드 완료
- 업로드된 책: Don_Quixote_full_episode, Don_Quixote_full_episode_ko
- 업로드된 영상 수: 2개
- [1] Complete Guide to Don Quixote | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=ta9Jr2axTu8
- [2] [일당백] 세르반테스 돈키호테 : 세상의 모든 소설들은 무릎꿇고 경의를 표하시오!! 완전정복 | 작가와 배경부터 시 줄거리까지
  - URL: https://www.youtube.com/watch?v=Nr7GaQHbK9Q

## 2026-01-04

### 시몬 드 보부아르 제2의 성 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 시몬 드 보부아르 "제2의 성 : 여성은 태어나지 않고 만들어진다" 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 시몬 드 보부아르 제2의 성 번역 매핑 추가
    - "시몬 드 보부아르 제2의 성" ↔ "The Second Sex"
- **생성된 영상**:
  - 한글: `output/The_Second_Sex_full_episode_ko.mp4` (816.28초, 약 13.60분)
  - 영문: `output/The_Second_Sex_full_episode_en.mp4` (868.08초, 약 14.47분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=DjuwhWtrzFY
  - 영문: https://www.youtube.com/watch?v=4xKtR72RFoM
- **수정된 파일**:
  - `src/utils/translations.py`: 시몬 드 보부아르 제2의 성 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 시몬 드 보부아르 제2의 성 업로드 정보 업데이트

## 2026-01-05

### 몽테뉴 수상록 롱폼 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 몽테뉴 "수상록" 롱폼 한글/영문 영상 제작
  - Summary 오디오 + NotebookLM 비디오 합성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 몽테뉴 수상록 번역 매핑 추가
    - "몽테뉴 수상록" ↔ "Essays"
    - "수상록" ↔ "Essays"
  - **코드 버그 수정**:
    - `src/03_make_video.py`: 들여쓰기 오류 수정 (clip 변수 초기화 문제 해결)
    - `src/10_create_video_with_summary.py`: 들여쓰기 오류 수정
- **생성된 영상**:
  - 한글: `output/Essays_kr.mp4` (약 287MB)
  - 영문: `output/Essays_en.mp4` (약 283MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=YAXj6EFCZ04
  - 영문: https://www.youtube.com/watch?v=scfN0JT-4ss
- **수정된 파일**:
  - `src/utils/translations.py`: 몽테뉴 수상록 번역 매핑 추가 및 수정
  - `src/03_make_video.py`: 들여쓰기 오류 수정
  - `src/10_create_video_with_summary.py`: 들여쓰기 오류 수정
  - `data/ildangbaek_books.csv`: 수상록 업로드 정보 업데이트

### 공자 논어 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 공자 논어(論語) 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 공자 논어 번역 매핑 추가
    - "공자 논어(論語)" ↔ "The Analects"
    - "논어" ↔ "The Analects"
    - "공자" ↔ "Confucius"
- **생성된 영상**:
  - 한글: `output/The_Analects_full_episode_ko.mp4` (536MB, 약 15.20분)
  - 영문: `output/The_Analects_full_episode_en.mp4` (485MB, 약 13.46분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=t17dN0cqJeE
  - 영문: https://www.youtube.com/watch?v=xAwFEtF78i4
- **수정된 파일**:
  - `src/utils/translations.py`: 공자 논어 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 논어 업로드 정보 업데이트

### 스토너 롱폼 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 존 윌리엄스 "스토너" 롱폼 한글/영문 영상 제작
  - Summary 오디오 + NotebookLM 비디오 합성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 스토너 번역 매핑 추가
    - "스토너" ↔ "Stoner"
    - "존 윌리엄스" ↔ "John Williams"
- **생성된 영상**:
  - 한글: `output/Stoner_kr.mp4` (251MB)
  - 영문: `output/Stoner_en.mp4` (295MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=RbESiTBNhn8
  - 영문: https://www.youtube.com/watch?v=m5PvzWsdWqA
- **수정된 파일**:
  - `src/utils/translations.py`: 스토너 및 존 윌리엄스 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 스토너 업로드 정보 업데이트

### 푸틴-권력의 논리 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 푸틴-권력의 논리 일당백 스타일 한글/영문 롱폼 영상 제작
  - Part 2개 자동 처리 확인 및 검증
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 푸틴 및 관련 번역 매핑 추가
    - "푸틴-권력의 논리" ↔ "Putin: The Logic of Power"
    - "권력의 논리" ↔ "The Logic of Power"
    - "푸틴" ↔ "Putin"
    - "마이클 울프" ↔ "Michael Wolff"
- **생성된 영상**:
  - 한글: `output/Putin_The_Logic_of_Power_full_episode_ko.mp4` (405MB, 약 14.61분)
  - 영문: `output/Putin_The_Logic_of_Power_full_episode_en.mp4` (301MB, 약 12.67분)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=vOmpo_L2Ot4
  - 영문: https://www.youtube.com/watch?v=sdoiM8Sa3Cw
- **수정된 파일**:
  - `src/utils/translations.py`: 푸틴 및 마이클 울프 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 푸틴 업로드 정보 업데이트

### 싯다르타 – 헤르만 헤세 롱폼 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 싯다르타 – 헤르만 헤세 한글/영문 롱폼 영상 제작
  - Summary(5분) + NotebookLM Video + Review 구조로 제작
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 싯다르타 번역 매핑 추가
    - "싯다르타" ↔ "Siddhartha"
- **생성된 영상**:
  - 한글: `output/Siddhartha_kr.mp4` (299MB)
  - 영문: `output/Siddhartha_en.mp4` (259MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=pBbcaP74Ilw
  - 영문: https://www.youtube.com/watch?v=iWotek3rcTM
- **수정된 파일**:
  - `src/utils/translations.py`: 싯다르타 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 싯다르타 업로드 정보 업데이트

## 2026-01-07

### YouTube 업로드 완료
- 업로드된 책: 칼_세이건_코스모스_광활한_우주에서_나는_어떤_존재인가_full_episode_ko, 칼_세이건_코스모스_광활한_우주에서_나는_어떤_존재인가_full_episode
- 업로드된 영상 수: 2개
- [1] Complete Guide to 칼 세이건 코스모스 : 광활한 우주에서 나는 어떤 존재인가? | From Author & Background to Full Story
  - URL: https://www.youtube.com/watch?v=473jUt3IwFk
- [2] [일당백] 칼 세이건 코스모스 : 광활한 우주에서 나는 어떤 존재인가? 완전정복 | 작가와 배경부터 소설 줄거리까지
  - URL: https://www.youtube.com/watch?v=e86Z9pdsj5M

## 2026-01-07

### 굿모닝 미드나잇 – 진 리스 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 진 리스 "굿모닝 미드나잇" 한글/영문 롱폼 영상 제작
  - Summary 포함 영상 구조 (Summary + NotebookLM + Review)
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 굿모닝 미드나잇, 진 리스 번역 매핑 추가
    - "굿모닝 미드나잇" ↔ "Good Morning, Midnight"
    - "진 리스" ↔ "Jean Rhys"
- **생성된 영상**:
  - 한글: `output/Good_Morning_Midnight_kr.mp4` (278MB)
  - 영문: `output/Good_Morning_Midnight_en.mp4` (302MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=OHhq_CxQO2E
  - 영문: https://www.youtube.com/watch?v=8icEOU60Unc
- **수정된 파일**:
  - `src/utils/translations.py`: 굿모닝 미드나잇, 진 리스 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 굿모닝 미드나잇 업로드 정보 업데이트

### 메타데이터 생성 시 오디오 리뷰 타임스탬프 제거
- **작업 내용**:
  - 영상 제작 시 오디오 리뷰가 포함되지 않으므로 메타데이터에서 오디오 리뷰 타임스탬프 제거
- **주요 수정사항**:
  - **타임스탬프 섹션 수정**: `src/08_create_and_preview_videos.py`의 `_generate_timestamps_section()` 함수 수정
    - "오디오 리뷰 (Audio Review)" 타임스탬프 제거
    - 이제 Summary와 NotebookLM Video 타임스탬프만 포함
  - **YouTube 챕터 수정**: `_generate_youtube_chapters()` 함수 수정
    - "오디오 리뷰" 챕터 제거
    - Summary와 NotebookLM Video 챕터만 포함
- **변경 전/후**:
  - 변경 전: `0:00 - 요약`, `1:42 - NotebookLM 상세 분석`, `8:09 - 오디오 리뷰`
  - 변경 후: `0:00 - 요약`, `1:42 - NotebookLM 상세 분석` (오디오 리뷰 제거)
- **수정된 파일**:
  - `src/08_create_and_preview_videos.py`: 오디오 리뷰 타임스탬프 제거 로직 추가

### YouTube 영상 검색 최적화 기능 추가
- **작업 내용**:
  - 해시태그, 제목, 메타데이터를 검색에 최적화하도록 개선
  - 장르별 특화 태그 자동 감지 및 추가
  - 검색량 높은 키워드 우선 배치
  - 트렌딩 키워드 자동 추가
- **주요 개선사항**:
  - **해시태그 최적화**:
    - 장르별 특화 태그 자동 감지 (소설, 논픽션, 철학, 과학, 역사, 심리학, 자기계발, 시)
    - 검색량 높은 기본 태그 우선 배치 (책리뷰, 독서, 북튜버, 책추천 등)
    - 트렌딩 키워드 자동 추가 (책추천2024, 독서챌린지, 독서모임 등)
    - 기관 태그 최적화 (뉴욕타임즈, 하버드, 노벨문학상 등)
  - **제목 최적화**:
    - 작가 이름 자동 포함으로 검색 범위 확대
    - 검색량 높은 키워드 앞쪽 배치
    - 대체 제목 포함으로 검색 가능성 증가
  - **메타데이터(설명) 최적화**:
    - 설명 첫 부분에 검색 키워드 자연스럽게 포함
    - 책 소개에 관련 키워드 자연스럽게 배치
    - 검색 알고리즘 최적화를 위한 키워드 밀도 조정
- **새로운 함수**:
  - `detect_genre_tags()`: 책의 장르를 감지하여 장르별 특화 태그 생성
- **수정된 함수**:
  - `generate_tags()`: 장르별 태그, 트렌딩 태그 추가, 우선순위 최적화
  - `generate_title()`: 작가 이름 파라미터 추가, 작가 이름 자동 포함
  - `_generate_description_ko()`: 검색 키워드 자연스럽게 포함
  - `_generate_description_en()`: 검색 키워드 자연스럽게 포함
- **새로운 문서**:
  - `docs/SEARCH_OPTIMIZATION_GUIDE.md`: 검색 최적화 가이드 문서 추가
    - 해시태그 최적화 방법
    - 제목 최적화 방법
    - 메타데이터 최적화 방법
    - 검색 최적화 체크리스트
    - 수동 최적화 팁
- **수정된 파일**:
  - `src/08_create_and_preview_videos.py`: 검색 최적화 기능 추가
  - `docs/SEARCH_OPTIMIZATION_GUIDE.md`: 검색 최적화 가이드 문서 (신규)

## 2026-01-07

### YouTube 업로드 완료
- 업로드된 책: Security_Analysis
- 업로드된 영상 수: 2개
- [1] [Summary] Security Analysis Book Review Benjamin Graham & David Dodd | [핵심 요약] Security Analysis ...
  - URL: https://www.youtube.com/watch?v=rqxvqqMimYw
- [2] [핵심 요약] Security Analysis 핵심 정리 Benjamin Graham & David Dodd | [Summary] Security Analysis Book R...
  - URL: https://www.youtube.com/watch?v=LlISSjlhWOA

## 2026-01-07

### YouTube 업로드 완료
- 업로드된 책: A_Farewell_to_Arms_full_episode, A_Farewell_to_Arms_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] A Farewell to Arms Book Review | [영어] 무기여 잘 있거라 책 리뷰
  - URL: https://www.youtube.com/watch?v=6p6DNfwTKkA
- [2] [한국어] 무기여 잘 있거라 책 리뷰 | [Korean] A Farewell to Arms Book Review
  - URL: https://www.youtube.com/watch?v=whTVsq-_8vg

## 2026-01-07

### YouTube 업로드 완료
- 업로드된 책: Lord_of_the_Flies_full_episode, Lord_of_the_Flies_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] Lord of the Flies Book Review | [영어] 파리대왕 책 리뷰
  - URL: https://www.youtube.com/watch?v=CYrK6XJ3pHM
- [2] [한국어] 파리대왕 책 리뷰 | [Korean] Lord of the Flies Book Review
  - URL: https://www.youtube.com/watch?v=kChZGbcIcZ8

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: Wealth_of_Nations
- 업로드된 영상 수: 2개
- [1] [Summary] Wealth of Nations Book Review Adam Smith | [핵심 요약] 국부론 핵심 정리
  - URL: https://www.youtube.com/watch?v=_R9hVoxOLGs
- [2] [핵심 요약] 국부론 핵심 정리 애덤 스미스 | [Summary] Wealth of Nations Book Review
  - URL: https://www.youtube.com/watch?v=1zACX8Hsd6g

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: The_Square_full_episode_ko, The_Square_full_episode
- 업로드된 영상 수: 2개
- [1] [English] The Square Book Review | [영어] 광장 책 리뷰
  - URL: https://www.youtube.com/watch?v=2GfBPumLF5Y
- [2] [한국어] 광장 책 리뷰 | [Korean] The Square Book Review
  - URL: https://www.youtube.com/watch?v=I0IQXtDebIg

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: The_Death_of_Ivan_Ilyich
- 업로드된 영상 수: 2개
- [1] [Summary] The_Death_of_Ivan_Ilyich Book Review Leo Tolstoy | [핵심 요약] 이반 일리치의 죽음 핵심 정리
  - URL: https://www.youtube.com/watch?v=BTvsCzGZfM4
- [2] [핵심 요약] 이반 일리치의 죽음 핵심 정리 레프 톨스토이 | [Summary] The_Death_of_Ivan_Ilyich Book Review
  - URL: https://www.youtube.com/watch?v=BnovpY5w5ZM

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: The_Structure_of_Scientific_Revolutions_full_episode, The_Structure_of_Scientific_Revolutions_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] The_Structure_of_Scientific_Revolutions Book Review | [영어] 과학혁명의 구조 책 리뷰
  - URL: https://www.youtube.com/watch?v=Gxl7cWAuzDg
- [2] [한국어] 과학혁명의 구조 책 리뷰 | [Korean] The_Structure_of_Scientific_Revolutions Book Review
  - URL: https://www.youtube.com/watch?v=L82iCU5KrdE

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: 일연_삼국유사_full_episode, 일연_삼국유사_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] 일연 삼국유사 Book Review | [영어] 일연 삼국유사 책 리뷰
  - URL: https://www.youtube.com/watch?v=jDM1h4QxVUI
- [2] [한국어] 일연 삼국유사 책 리뷰 | [Korean] 일연 삼국유사 Book Review
  - URL: https://www.youtube.com/watch?v=f2LRK6GARS8

## 2026-01-08

### YouTube 업로드 완료
- 업로드된 책: Norwegian_Wood_full_episode, Norwegian_Wood_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] Norwegian Wood Book Review | [영어] 상실의 시대 책 리뷰
  - URL: https://www.youtube.com/watch?v=9DV5Zl7BAZg
- [2] [한국어] 상실의 시대 책 리뷰 | [Korean] Norwegian Wood Book Review
  - URL: https://www.youtube.com/watch?v=GDnnnuT6T28

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Death_of_a_Salesman
- 업로드된 영상 수: 2개
- [1] [Summary] Death of a Salesman Book Review | [핵심 요약] 세일즈맨의 죽음 핵심 정리
  - URL: https://www.youtube.com/watch?v=8cSwlqDiVcg
- [2] [핵심 요약] 세일즈맨의 죽음 핵심 정리 | [Summary] Death of a Salesman Book Review
  - URL: https://www.youtube.com/watch?v=Mmd9TY1we84

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Four_Thousand_Weeks
- 업로드된 영상 수: 2개
- [1] [Summary] Four Thousand Weeks Book Review | [핵심 요약] 4000주 핵심 정리
  - URL: https://www.youtube.com/watch?v=ZnIvEcReSLU
- [2] [핵심 요약] 4000주 핵심 정리 | [Summary] Four Thousand Weeks Book Review
  - URL: https://www.youtube.com/watch?v=fBzBt7W39jY

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: 안데르센그림_형제페로_동화_괴롭고_힘든_어린이와_어른에게_가장_필요한_것은_full_episode_ko, 안데르센그림_형제페로_동화_괴롭고_힘든_어린이와_어른에게_가장_필요한_것은_full_episode
- 업로드된 영상 수: 2개
- [1] [1DANG100] Andersen, Grimm Brothers, Perrault Fairy Tales Book Review
  - URL: https://www.youtube.com/watch?v=AI3ike8Wuss
- [2] [일당백] 안데르센,그림 형제,페로 동화 : 괴롭고 힘든 어린이와 어른에게 가장 필요한 것은? 책 리뷰
  - URL: https://www.youtube.com/watch?v=N1JFwwSivQc

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Death_of_a_Salesman
- 업로드된 영상 수: 2개
- [1] [Summary] Death of a Salesman Book Review | [핵심 요약] 세일즈맨의 죽음 핵심 정리
  - URL: https://www.youtube.com/watch?v=YeiN06mKKug
- [2] [핵심 요약] 세일즈맨의 죽음 핵심 정리 | [Summary] Death of a Salesman Book Review
  - URL: https://www.youtube.com/watch?v=cR0QYWgWlaY

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Ikigai
- 업로드된 영상 수: 2개
- [1] [Summary] Ikigai Book Review | [핵심 요약] 이키가이 핵심 정리
  - URL: https://www.youtube.com/watch?v=mSkAQrep1yE
- [2] [핵심 요약] 이키가이 핵심 정리 | [Summary] Ikigai Book Review
  - URL: https://www.youtube.com/watch?v=Hj1ySsg3tn0

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: The_Book_of_Disquiet
- 업로드된 영상 수: 2개
- [1] [Summary] The Book of Disquiet Book Review | [핵심 요약] 불안의 서 핵심 정리
  - URL: https://www.youtube.com/watch?v=XuYZc6J44mM
- [2] [핵심 요약] 불안의 서 핵심 정리 | [Summary] The Book of Disquiet Book Review
  - URL: https://www.youtube.com/watch?v=4-EOxscKOrU

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Hamlet_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Hamlet Book Review | [영어] 햄릿 책 리뷰
  - URL: https://www.youtube.com/watch?v=A3UWIsFrmQU
- [2] [한국어] 햄릿 책 리뷰 | [Korean] Hamlet Book Review
  - URL: https://www.youtube.com/watch?v=ZkINbHIM3lM

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Tristes_Tropiques_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Tristes Tropiques Book Review | [영어] 슬픈 열대 책 리뷰
  - URL: https://www.youtube.com/watch?v=eV3hj5E_8d8
- [2] [한국어] 슬픈 열대 책 리뷰 | [Korean] Tristes Tropiques Book Review
  - URL: https://www.youtube.com/watch?v=50k9QSc2-vE

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: The_Book_of_Disquiet
- 업로드된 영상 수: 2개
- [1] [Summary] The Book of Disquiet Book Review | [핵심 요약] 불안의 서 핵심 정리
  - URL: https://www.youtube.com/watch?v=9I8qFu3gcIQ
- [2] [핵심 요약] 불안의 서 핵심 정리 | [Summary] The Book of Disquiet Book Review
  - URL: https://www.youtube.com/watch?v=mj7NRfJLtAw

## 2026-01-09

### YouTube 업로드 완료
- 업로드된 책: Romeo_and_Juliet_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Romeo and Juliet Book Review | [영어] 로미오와 줄리엣 책 리뷰
  - URL: https://www.youtube.com/watch?v=tOTLB-dxmls
- [2] [한국어] 로미오와 줄리엣 책 리뷰 | [Korean] Romeo and Juliet Book Review
  - URL: https://www.youtube.com/watch?v=ppsrfEzbOYo

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: Future_Self
- 업로드된 영상 수: 2개
- [1] [Summary] Future Self Book Review | [핵심 요약] 퓨처 셀프 핵심 정리
  - URL: https://www.youtube.com/watch?v=pZMtRafQ9ws
- [2] [핵심 요약] 퓨처 셀프 핵심 정리 | [Summary] Future Self Book Review
  - URL: https://www.youtube.com/watch?v=0CR4HuZaG3Q

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: The_Neurotics_Guide_to_Avoiding_Enlightenment
- 업로드된 영상 수: 2개
- [1] [Summary] The Neurotic's Guide to Avoiding Enlightenment Book Review | [핵심 요약] 뇌는 어떻게 나를 조종하는가 핵심 정리
  - URL: https://www.youtube.com/watch?v=5XVUQuyW22c
- [2] [핵심 요약] 뇌는 어떻게 나를 조종하는가 핵심 정리 | [Summary] The Neurotic's Guide to Avoiding Enlightenment Book Review
  - URL: https://www.youtube.com/watch?v=_gLIBAzEEDY

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: The_Odyssey_full_episode
- 업로드된 영상 수: 1개
- [1] [English] The Odyssey Book Review | [영어] 오다세이아 책 리뷰
  - URL: https://www.youtube.com/watch?v=AQZPGgiF53A

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: The_Odyssey_full_episode
- 업로드된 영상 수: 1개
- [1] [한국어] 오다세이아 책 리뷰 | [Korean] The Odyssey Book Review
  - URL: https://www.youtube.com/watch?v=J-PxEE9MV84

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: Winterreise
- 업로드된 영상 수: 2개
- [1] [Summary] Winterreise Book Review | [핵심 요약] 슈베르트의 겨울 나그네 핵심 정리
  - URL: https://www.youtube.com/watch?v=b-acHG0eGvY
- [2] [핵심 요약] 슈베르트의 겨울 나그네 핵심 정리 | [Summary] Winterreise Book Review
  - URL: https://www.youtube.com/watch?v=PvIbaQrsqqU

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: Tristes_Tropiques_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Tristes Tropiques Book Review | [영어] 슬픈 열대 책 리뷰
  - URL: https://www.youtube.com/watch?v=ruhMqnEL0Wo
- [2] [한국어] 슬픈 열대 책 리뷰 | [Korean] Tristes Tropiques Book Review
  - URL: https://www.youtube.com/watch?v=nYHyS1q5sTY

## 2026-01-11

### YouTube 업로드 완료
- 업로드된 책: The_Protestant_Ethic_and_the_Spirit_of_Capitalism_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Protestant Ethic & Capitalism Book Review | [영어] 프로테스탄티즘의 윤리와 자본주의 정신
  - URL: https://www.youtube.com/watch?v=eL05LOss05k
- [2] [한국어] 프로테스탄티즘의 윤리와 자본주의 정신 | [Korean] Protestant Ethic & Capitalism Book Review
  - URL: https://www.youtube.com/watch?v=Y05T3AebwVQ

## 2026-01-12

### YouTube 업로드 완료
- 업로드된 책: The_Old_Man_and_the_Sea
- 업로드된 영상 수: 2개
- [1] [Summary] The Old Man and the Sea Book Review | [핵심 요약] 노인과 바다 핵심 정리
  - URL: https://www.youtube.com/watch?v=6b50coYFtk8
- [2] [핵심 요약] 노인과 바다 핵심 정리 | [Summary] The Old Man and the Sea Book Review
  - URL: https://www.youtube.com/watch?v=K8MIWCe30D8

## 2026-01-12

### YouTube 업로드 완료
- 업로드된 책: The_Stranger
- 업로드된 영상 수: 2개
- [1] [Summary] The Stranger Book Review | [핵심 요약] 이방인 핵심 정리
  - URL: https://www.youtube.com/watch?v=UpP-uhEbR1k
- [2] [핵심 요약] 이방인 핵심 정리 | [Summary] The Stranger Book Review
  - URL: https://www.youtube.com/watch?v=zj_xq4ROPqQ

## 2026-01-12

### YouTube 업로드 완료
- 업로드된 책: Brave_New_World
- 업로드된 영상 수: 2개
- [1] [Summary] Brave New World Book Review | [핵심 요약] 멋진 신세계 핵심 정리
  - URL: https://www.youtube.com/watch?v=jUBZBe7dxIM
- [2] [핵심 요약] 멋진 신세계 핵심 정리 | [Summary] Brave New World Book Review
  - URL: https://www.youtube.com/watch?v=iZ9rOZbLxxM

## 2026-01-13

### YouTube 업로드 완료
- 업로드된 책: Grit
- 업로드된 영상 수: 2개
- [1] [Summary] Grit Book Review | [핵심 요약] 그릿 핵심 정리
  - URL: https://www.youtube.com/watch?v=PWjeUx3Rv40
- [2] [핵심 요약] 그릿 핵심 정리 | [Summary] Grit Book Review
  - URL: https://www.youtube.com/watch?v=NpvOHPpFnb0

## 2026-01-14

### 유발 하라리 - 넥서스(Nexus) summary+video 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 유발 하라리 "넥서스 (Nexus)" 한글/영문 summary+video 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - 번역 매핑 추가 (넥서스 ↔ Nexus)
  - 이미지 다운로드 (100개, 저자/주제 관련)
  - Summary + NotebookLM Video 형태로 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 추가**: `src/utils/translations.py`에 "넥서스" ↔ "Nexus" 매핑 추가
- **생성된 영상**:
  - 한글: `output/Nexus_kr.mp4` (200.49 MB)
  - 영문: `output/Nexus_en.mp4` (234.26 MB)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=PBGWP4S90D4
  - 영문: https://www.youtube.com/watch?v=Gr0kyF2wBBQ
- **수정된 파일**:
  - `src/utils/translations.py`: 넥서스 번역 매핑 추가
  - `data/ildangbaek_books.csv`: 넥서스 업로드 정보 업데이트

## 2026-01-15

### YouTube 업로드 완료
- 업로드된 책: The_48_Laws_of_Power
- 업로드된 영상 수: 2개
- [1] [Summary] The 48 Laws of Power Book Review | [핵심 요약] 권력의 법칙 핵심 정리
  - URL: https://www.youtube.com/watch?v=bMA9YaGKTzY
- [2] [핵심 요약] 권력의 법칙 핵심 정리 | [Summary] The 48 Laws of Power Book Review
  - URL: https://www.youtube.com/watch?v=_bSRdMpKW5U

## 2026-01-15

### YouTube 업로드 완료
- 업로드된 책: The_48_Laws_of_Power
- 업로드된 영상 수: 2개
- [1] [Summary] The 48 Laws of Power Book Review | [핵심 요약] 권력의 법칙 핵심 정리
  - URL: https://www.youtube.com/watch?v=J1dnrH8ZMR0
- [2] [핵심 요약] 권력의 법칙 핵심 정리 | [Summary] The 48 Laws of Power Book Review
  - URL: https://www.youtube.com/watch?v=HlTaXreLw7c

## 2026-01-15

### YouTube 업로드 완료
- 업로드된 책: Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration_full_episode_ko, Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration Book Review | [영어] Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration 책 리뷰
  - URL: https://www.youtube.com/watch?v=NqnA36-IH04
- [2] [한국어] Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration 책 리뷰 | [Korean] Edgar_Allan_Poe_Horror_Stories_and_Poe_Songryeong_Collaboration Book Review
  - URL: https://www.youtube.com/watch?v=1dKsiVS6gP0

## 2026-01-15

### YouTube 업로드 완료
- 업로드된 책: The_Stranger_full_episode_ko, The_Stranger_full_episode
- 업로드된 영상 수: 2개
- [1] [English] The_Stranger Book Review | [영어] The_Stranger 책 리뷰
  - URL: https://www.youtube.com/watch?v=fWtO5G1Pswg
- [2] [한국어] The_Stranger 책 리뷰 | [Korean] The_Stranger Book Review
  - URL: https://www.youtube.com/watch?v=vBO4lEBmaao

## 2026-01-15

### YouTube 업로드 완료
- 업로드된 책: Gullivers_Travels_full_episode_ko, Gullivers_Travels_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Gullivers_Travels Book Review | [영어] Gullivers_Travels 책 리뷰
  - URL: https://www.youtube.com/watch?v=clUULPkveh0
- [2] [한국어] Gullivers_Travels 책 리뷰 | [Korean] Gullivers_Travels Book Review
  - URL: https://www.youtube.com/watch?v=42zz0RtDDyw

## 2026-01-16

### YouTube 업로드 완료
- 업로드된 책: Dopamine_Nation
- 업로드된 영상 수: 2개
- [1] [Summary] Dopamine Nation Book Review | [핵심 요약] 도파민네이션 핵심 정리
  - URL: https://www.youtube.com/watch?v=qKDEdGSxfbk
- [2] [핵심 요약] 도파민네이션 핵심 정리 | [Summary] Dopamine Nation Book Review
  - URL: https://www.youtube.com/watch?v=JWZR1VjdJCs

## 2026-01-16

### YouTube 업로드 완료
- 업로드된 책: The_Singularity_Is_Near
- 업로드된 영상 수: 2개
- [1] [Summary] The Singularity Is Near Book Review | [핵심 요약] 특이점이 온다 핵심 정리
  - URL: https://www.youtube.com/watch?v=zphxWm6olYc
- [2] [핵심 요약] 특이점이 온다 핵심 정리 | [Summary] The Singularity Is Near Book Review
  - URL: https://www.youtube.com/watch?v=1r_oGXMMbKY

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: Why_Fish_Dont_Exist
- 업로드된 영상 수: 2개
- [1] [Summary] Why Fish Don't Exist Book Review | [핵심 요약] 물고기는 존재하지 않는다 핵심 정리
  - URL: https://www.youtube.com/watch?v=yzDjClWRXDc
- [2] [핵심 요약] 물고기는 존재하지 않는다 핵심 정리 | [Summary] Why Fish Don't Exist Book Review
  - URL: https://www.youtube.com/watch?v=4vkM7QlstiQ

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: No_Longer_Human
- 업로드된 영상 수: 2개
- [1] [Summary] No Longer Human Book Review | [핵심 요약] 인간 실격 핵심 정리
  - URL: https://www.youtube.com/watch?v=uzpOrWu99Us
- [2] [핵심 요약] 인간 실격 핵심 정리 | [Summary] No Longer Human Book Review
  - URL: https://www.youtube.com/watch?v=9zTZrbFIKOA

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: Stolen_Focus
- 업로드된 영상 수: 2개
- [1] [Summary] Stolen Focus Book Review | [핵심 요약] 도둑맞은 집중력 핵심 정리
  - URL: https://www.youtube.com/watch?v=4_oriZUu3WQ
- [2] [핵심 요약] 도둑맞은 집중력 핵심 정리 | [Summary] Stolen Focus Book Review
  - URL: https://www.youtube.com/watch?v=PLuorfku5QQ

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: No_Longer_Human
- 업로드된 영상 수: 2개
- [1] [Summary] No Longer Human Book Review | [핵심 요약] 인간 실격 핵심 정리
  - URL: https://www.youtube.com/watch?v=omLyLMeBJcc
- [2] [핵심 요약] 인간 실격 핵심 정리 | [Summary] No Longer Human Book Review
  - URL: https://www.youtube.com/watch?v=L8FLJWGj7GE

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: Yolha_Ilgi_full_episode_ko, Yolha_Ilgi_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Yolha Ilgi Book Review | [영어] 열하일기 책 리뷰
  - URL: https://www.youtube.com/watch?v=oiqPw8kwQSw
- [2] [한국어] 열하일기 책 리뷰 | [Korean] Yolha Ilgi Book Review
  - URL: https://www.youtube.com/watch?v=vEY4hjPV5CA

## 2026-01-18

### YouTube 업로드 완료
- 업로드된 책: Eichmann_in_Jerusalem_full_episode_ko, Eichmann_in_Jerusalem_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Eichmann in Jerusalem Book Review | [영어] 예루살렘의 아이히만 책 리뷰
  - URL: https://www.youtube.com/watch?v=ImOURyEbzPw
- [2] [한국어] 예루살렘의 아이히만 책 리뷰 | [Korean] Eichmann in Jerusalem Book Review
  - URL: https://www.youtube.com/watch?v=ZMzTUeOh4pY

## 2026-01-18

### 헤르만 헤세 - 데미안 (Demian) 일당백 스타일 영상 제작 및 YouTube 업로드
- **작업 내용**:
  - 헤르만 헤세 "데미안 (Demian)" 한글/영문 일당백 스타일 영상 제작
  - input 폴더에서 파일 준비 및 표준 네이밍으로 이동
  - Part 1, Part 2 비디오와 인포그래픽을 연결하여 전체 에피소드 영상 생성
  - YouTube 업로드 완료 (한글/영문)
- **주요 수정사항**:
  - **번역 매핑 확인**: `src/utils/translations.py`에 이미 "데미안" ↔ "Demian", "헤르만 헤세" ↔ "Hermann Hesse" 매핑이 존재함
- **생성된 영상**:
  - 한글: `output/Demian_full_episode_ko.mp4` (557.92 MB, 16분 16초)
  - 영문: `output/Demian_full_episode_en.mp4` (566.49 MB, 15분 26초)
- **YouTube 업로드**:
  - 한글: https://www.youtube.com/watch?v=C1VeauTb6gs
  - 영문: https://www.youtube.com/watch?v=f8ff5TNd47U
- **수정된 파일**:
  - `data/ildangbaek_books.csv`: 데미안 업로드 정보 업데이트

## 2026-01-19

### YouTube 업로드 완료
- 업로드된 책: Same_as_Ever
- 업로드된 영상 수: 2개
- [1] [Summary] Same as Ever Book Review Morgan Housel | [핵심 요약] 불변의 법칙 핵심 정리
  - URL: https://www.youtube.com/watch?v=zw-vURBx-b4
- [2] [핵심 요약] 불변의 법칙 핵심 정리 모건 하우절 | [Summary] Same as Ever Book Review
  - URL: https://www.youtube.com/watch?v=ElvVq7ugy0I

## 2026-01-19

### YouTube 업로드 완료
- 업로드된 책: Cosmos_full_episode_ko, Cosmos_full_episode
- 업로드된 영상 수: 2개
- [1] [English] Cosmos Book Review | [영어] 코스모스 책 리뷰
  - URL: https://www.youtube.com/watch?v=L1WYsstVHN8
- [2] [한국어] 코스모스 책 리뷰 | [Korean] Cosmos Book Review
  - URL: https://www.youtube.com/watch?v=YzI7EZmaOc8

## 2026-01-19

### YouTube 업로드 완료
- 업로드된 책: I_Am_a_Cat_full_episode, I_Am_a_Cat_full_episode_ko
- 업로드된 영상 수: 2개
- [1] [English] I_Am_a_Cat Book Review | [영어] 나는 고양이로소이다 책 리뷰
  - URL: https://www.youtube.com/watch?v=xQHl6POMKWE
- [2] [한국어] 나는 고양이로소이다 책 리뷰 | [Korean] I_Am_a_Cat Book Review
  - URL: https://www.youtube.com/watch?v=YgmGQUZTO7M
