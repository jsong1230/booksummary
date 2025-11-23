# YouTube 영상 자동 검색 가이드

GPT/Claude API를 사용하여 YouTube 영상을 자동으로 검색하고 NotebookLM용 마크다운 파일에 추가하는 방법입니다.

## 사용 방법

### 기본 사용법

```bash
./run_youtube_search.sh --title "책제목" --author "저자명"
```

### 예시

```bash
# 노르웨이의 숲 검색
./run_youtube_search.sh --title "노르웨이의 숲" --author "무라카미 하루키"

# 저자 없이 검색
./run_youtube_search.sh --title "1984"
```

### 옵션

- `--title`: 책 제목 (필수)
- `--author`: 저자 이름 (선택사항)
- `--use-openai`: OpenAI GPT 사용 (기본값: Claude)
- `--max-results`: 쿼리당 최대 결과 수 (기본값: 3)
- `--output`: 출력 파일 경로 (기본값: 자동 생성)

### 예시 (옵션 포함)

```bash
# OpenAI GPT 사용, 쿼리당 5개 결과
./run_youtube_search.sh --title "노르웨이의 숲" --author "무라카미 하루키" --use-openai --max-results 5

# 특정 파일에 저장
./run_youtube_search.sh --title "노르웨이의 숲" --output "assets/urls/my_book.md"
```

## 작동 방식

1. **AI 검색 쿼리 생성**: Claude/GPT API를 사용하여 책에 대한 다양한 YouTube 검색 쿼리를 생성합니다.
   - 책 리뷰, 서평, 해석, 분석
   - 작가 인터뷰
   - 독서 후기, 줄거리
   - 팟캐스트, 강의 등

2. **YouTube 영상 검색**: YouTube Data API v3를 사용하여 각 쿼리로 실제 영상을 검색합니다.

3. **URL 자동 추가**: 찾은 영상 URL을 기존 마크다운 파일에 자동으로 추가합니다.

## 필요한 API 키

### .env 파일에 설정 필요:

1. **Claude API** (기본 사용)
   ```
   CLAUDE_API_KEY=your_claude_api_key
   ```

2. **OpenAI API** (선택사항)
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

3. **YouTube Data API v3** (필수)
   ```
   YOUTUBE_API_KEY=your_youtube_data_api_key
   ```
   
   > 💡 **YouTube Data API 키 발급 방법**:
   > 1. [Google Cloud Console](https://console.cloud.google.com/) 접속
   > 2. 프로젝트 선택 또는 생성
   > 3. "API 및 서비스" > "라이브러리"
   > 4. "YouTube Data API v3" 검색 후 활성화
   > 5. "API 및 서비스" > "사용자 인증 정보"
   > 6. "API 키 만들기" 클릭
   > 7. 생성된 키를 `.env` 파일의 `YOUTUBE_API_KEY`에 입력

## 출력 결과

스크립트 실행 후:
- 기존 마크다운 파일에 YouTube 영상 URL이 자동으로 추가됩니다
- 새로 찾은 영상 개수와 총 URL 개수가 표시됩니다
- 각 영상의 제목과 채널 정보가 콘솔에 출력됩니다

## 장점

✅ **자동화**: 수동으로 YouTube를 검색할 필요 없음  
✅ **다양한 쿼리**: AI가 다양한 검색 쿼리를 자동 생성  
✅ **실제 영상만**: 재생 가능한 실제 YouTube 영상 URL만 수집  
✅ **자동 통합**: 기존 마크다운 파일에 자동으로 추가

## 문제 해결

### YouTube API 키 오류
```
⚠️ YouTube API가 설정되지 않았습니다.
```
→ `.env` 파일에 `YOUTUBE_API_KEY`를 추가하세요.

### Claude/OpenAI API 오류
```
⚠️ API 호출 실패
```
→ 기본 검색 쿼리를 사용하여 계속 진행됩니다. API 키를 확인하세요.

### 영상을 찾을 수 없음
→ 검색 쿼리를 조정하거나 `--max-results` 값을 늘려보세요.

