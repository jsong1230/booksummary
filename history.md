# BookReview-AutoMaker 프로젝트 히스토리

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
