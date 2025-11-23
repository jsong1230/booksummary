# NotebookLM 사용 가이드

## 📚 선택된 책: 노르웨이의 숲 (무라카미 하루키)

이 책에 대한 URL을 수집하여 NotebookLM에 소스로 추가하는 방법을 안내합니다.

## 1단계: URL 수집

### 자동 수집 (권장)
```bash
# 가상환경 활성화
source venv/bin/activate

# URL 수집 실행
python scripts/collect_urls_for_notebooklm.py --title "노르웨이의 숲" --author "무라카미 하루키" --num 25
```

### 수동 실행
```bash
./run_collect_books.sh
# 또는
python scripts/collect_urls_for_notebooklm.py
# 인터랙티브 모드로 책 제목 입력
```

## 2단계: 수집된 URL 확인

수집이 완료되면 다음 파일이 생성됩니다:
- `assets/urls/노르웨이의_숲_notebooklm.txt` - NotebookLM에 복사할 URL 리스트
- `assets/urls/노르웨이의_숲_notebooklm.json` - 상세 정보 (JSON)

### 파일 내용 확인
```bash
cat assets/urls/노르웨이의_숲_notebooklm.txt
```

## 3단계: NotebookLM에 소스 추가

### 방법 1: URL 직접 추가 (개별)
1. [NotebookLM](https://notebooklm.google.com)에 접속
2. 새 노트북 생성 또는 기존 노트북 열기
3. 왼쪽 사이드바에서 **"소스 추가"** 클릭
4. **"URL"** 선택
5. 수집된 URL을 하나씩 붙여넣기
6. **"추가"** 클릭

### 방법 2: 일괄 추가 (권장)
1. `assets/urls/노르웨이의_숲_notebooklm.txt` 파일 열기
2. 모든 URL 선택 (Cmd+A / Ctrl+A)
3. 복사 (Cmd+C / Ctrl+C)
4. NotebookLM에서 **"소스 추가" > "URL"** 선택
5. URL을 한 줄에 하나씩 붙여넣기
   - 각 URL을 엔터로 구분하여 붙여넣기
   - 또는 여러 개의 URL을 한 번에 붙여넣기 (NotebookLM이 자동으로 인식)

### 방법 3: 드래그 앤 드롭
1. `assets/urls/노르웨이의_숲_notebooklm.txt` 파일을 열어둡니다
2. NotebookLM에서 **"소스 추가"** 클릭
3. URL을 드래그하여 NotebookLM에 드롭

## 4단계: Audio Overview 생성

모든 소스가 추가되면:
1. NotebookLM 상단의 **"Audio Overview 생성"** 버튼 클릭
2. 생성 완료까지 대기 (보통 몇 분 소요)
3. 생성된 오디오를 다운로드
4. `assets/audio/` 폴더에 저장

## 수집되는 URL 유형

다음과 같은 URL들이 수집됩니다:

### 📺 YouTube 영상
- 책 리뷰 영상
- 작가 인터뷰
- 강의/강연 영상
- 팟캐스트 영상

### 📖 온라인 서점
- 교보문고 상세 페이지
- 예스24 상세 페이지
- 알라딘 상세 페이지

### 📰 뉴스/리뷰
- 한겨레 서평
- 경향신문 리뷰
- 중앙일보 서평
- 기타 서평 사이트

### 📚 참고 자료
- 위키백과
- 책 소개 페이지
- 작가 인터뷰 기사

## 팁

1. **URL 개수**: 최소 20개 이상의 URL을 수집하는 것을 권장합니다.
2. **YouTube 영상**: YouTube 영상은 NotebookLM에서 오디오를 추출하여 활용할 수 있습니다.
3. **다양한 소스**: 다양한 출처의 URL을 포함하면 더 풍부한 콘텐츠를 생성할 수 있습니다.
4. **URL 유효성**: 수집 후 일부 URL이 작동하지 않을 수 있습니다. 이는 정상입니다.

## 문제 해결

### URL이 너무 적게 수집되는 경우
```bash
# URL 개수 증가
python scripts/collect_urls_for_notebooklm.py --title "책제목" --num 30
```

### 특정 책으로 다시 수집
```bash
python scripts/collect_urls_for_notebooklm.py --title "책제목" --author "저자명" --num 25
```

### URL 유효성 검증
```bash
python scripts/collect_urls_for_notebooklm.py --title "책제목" --validate
```

## 다음 단계

URL 수집이 완료되면:
1. ✅ NotebookLM에 소스 추가
2. ✅ Audio Overview 생성
3. ✅ 오디오 다운로드 (`assets/audio/`)
4. ✅ 영상 제작 (Phase 4)

