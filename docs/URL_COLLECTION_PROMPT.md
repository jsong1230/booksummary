# NotebookLM용 URL 수집 프롬프트

유튜브 롱폼 북튜브를 위한 자료를 수집하는 역할입니다.

## 기본 정보

{작가}의 『{책제목}』에 대해 30~60분짜리 해설/분석 유튜브 영상을 만들 예정입니다.

NotebookLM에 넣을 자료로 쓸 수 있도록, 이 책을 깊이 있게 다루는 URL을 수집해주세요.

## 요구사항

### 수집 목표
- **한국어 자료 15개 내외, 영어 자료 15개 내외 (총 30개 이상)**
- 가능한 한 많이 수집 (30개로 제한하지 말 것)
- **YouTube 영상은 전체의 약 50% 목표** (30분 이상 영상만)

### 자료 유형

#### 선호하는 자료
- **유튜브**: 긴 리뷰(30분 이상), 해설, 강의, 저자 강연, 북토크 등
- **PDF**: 논문, 에세이, 강의자료
- **블로그/칼럼**: 심층 분석, 비평, 독후감, 줄거리+해설
- **학술 사이트**: 논문, 연구 자료

#### 제외할 자료
- 도서 구매 페이지, 쇼핑몰, 가격비교 사이트
- 출판사 홍보용 페이지, ISBN/기본 정보만 있는 페이지
- 위키백과, 나무위키, 위키피디아
- 2~3줄짜리 짧은 후기/리뷰만 있는 페이지
- 이 책이 아닌 작가 전체를 포괄적으로만 소개하는 페이지
- Shorts 비디오 (#Shorts 포함)

## YouTube 채널 우선순위

### 최우선 채널
1. **@1DANG100 (일당백)** - 최우선으로 반드시 포함

### 한글 우선순위 채널
1. **@thewinterbookstore (겨울서점)** - 책의 메시지를 짚어서 요약하는 스타일
2. **@chaegiljji (책읽찌라)** - 책의 메시지를 짚어서 요약하는 스타일
3. **@humanitylearning (인문학TV 휴식같은 지식)** - 책의 메시지를 짚어서 요약하는 스타일
4. **@mkkimtv (김미경TV)** - 에세이/자기계발류 감성형 컨텐츠 참고

### 한글 추가 채널
- @Gwana (과나)
- @jachung (라이프해커 자청)
- @channelyes24 (채널예스)

### 영어 우선순위 채널
1. **@BTFC (Better Than Food)** - 깊은 분석
2. **@ClimbtheStacks (Climb The Stacks)** - 깊은 분석
3. **@JackEdwards** - 감성적, 현대 독자 관점
4. **@arielbissett** - 출판·저자 맥락까지 참고 가능

### 영어 추가 채널
- @withcindy (Read with Cindy)
- @thebookleo (The Book Leo)
- @InsightJunkie

## 검색 쿼리 예시

### 한글 검색 쿼리
```
"{책제목}" {작가} 해설
"{책제목}" {작가} 분석
"{책제목}" {작가} 비평
"{책제목}" {작가} 논문
"{책제목}" {작가} 에세이
"{책제목}" {작가} 강의자료
"{책제목}" {작가} 독후감
"{책제목}" {작가} 서평
"{책제목}" {작가} 리뷰
"{책제목}" {작가} filetype:pdf
"{책제목}" {작가} 논문 pdf
"{책제목}" {작가} 강의자료 pdf
```

### 영어 검색 쿼리
```
"{책제목}" {작가} analysis
"{책제목}" {작가} review
"{책제목}" {작가} essay
"{책제목}" {작가} critique
"{책제목}" {작가} lecture
"{책제목}" {작가} discussion
"{책제목}" {작가} filetype:pdf
"{책제목}" {작가} paper pdf
"{책제목}" {작가} essay pdf
```

### 학술 사이트 검색 (한글)
```
"{책제목}" {작가} site:academia.edu
"{책제목}" {작가} site:researchgate.net
"{책제목}" {작가} site:jstor.org
"{책제목}" {작가} site:scholar.google.com
"{책제목}" {작가} site:dbpia.co.kr
"{책제목}" {작가} site:kci.go.kr
"{책제목}" {작가} site:riss.kr
"{책제목}" {작가} site:brunch.co.kr
"{책제목}" {작가} site:medium.com
"{책제목}" {작가} site:blog.naver.com
"{책제목}" {작가} site:blog.daum.net
"{책제목}" {작가} site:post.naver.com
```

### 학술 사이트 검색 (영어)
```
"{책제목}" {작가} site:academia.edu
"{책제목}" {작가} site:researchgate.net
"{책제목}" {작가} site:jstor.org
"{책제목}" {작가} site:scholar.google.com
"{책제목}" {작가} site:medium.com
"{책제목}" {작가} site:theguardian.com
"{책제목}" {작가} site:nytimes.com
"{책제목}" {작가} site:newyorker.com
"{책제목}" {작가} site:lrb.co.uk
"{책제목}" {작가} site:nybooks.com
```

## 검증 규칙

### URL 검증
- 페이지 제목과 간단한 설명/스니펫을 반드시 확인
- **책 제목({책제목}) 혹은 명백하게 이 책을 지칭하는 표현이 없는 경우는 제외**
- 너무 짧은 콘텐츠(한 단락짜리 포스트 등)는 제외
- 책 제목의 주요 키워드가 포함되어 있으면 통과 (예: "21세기를 위한 21가지 제언" -> "21세기", "21가지", "제언")
- 저자 이름이 포함되어 있으면 더 관대하게 검증

### YouTube 영상 검증
- **30분 이상 영상만 수집** (롱폼 콘텐츠)
- 제목에 책 제목이 포함되어 있어야 함
- Shorts 비디오는 제외 (#Shorts 포함)

### PDF 파일 검증
- PDF 파일은 제목과 설명만 확인 (본문 검증 생략)
- 책 제목 또는 저자 이름이 포함되어 있으면 통과

### 학술 사이트 검증
- 학술 사이트(dbpia.co.kr, kci.go.kr, riss.kr, academia.edu, researchgate.net, jstor.org 등)는 더 관대하게 검증
- 블로그/미디엄(blog.naver.com, medium.com, brunch.co.kr 등)도 더 관대하게 검증

## 제외할 도메인

다음 도메인은 제외:
- kyobobook.co.kr, yes24.com, aladin.co.kr, interpark.com (온라인 서점)
- amazon.com, amazon.co.kr, amazon.co.uk (아마존)
- naver.com/shopping, coupang.com, 11st.co.kr, gmarket.co.kr, auction.co.kr (쇼핑몰)
- ko.wikipedia.org, namu.wiki, en.wikipedia.org, wikidata.org (위키)
- /product/, /goods/, /item/, /shop/, /isbn/, /book/, /detail/ (쇼핑/상품 페이지)

## 출력 형식

- 설명 없이 URL만 출력
- 각 줄에는 오직 한 개의 URL만 있어야 함
- 한글 자료와 영어 자료를 구분하지 않고 모두 나열

## 예시 프롬프트

```
너는 유튜브 롱폼 북튜브를 위한 자료를 수집하는 역할이다.

유발 하라리의 『21세기를 위한 21가지 제언』에 대해 30~60분짜리 해설/분석 유튜브 영상을 만들 예정이다.

NotebookLM에 넣을 자료로 쓸 수 있도록, 이 책을 깊이 있게 다루는 URL 30개 이상을 수집하라.

요구사항:
- 한국어 자료 15개 내외, 영어 자료 15개 내외 (총 30개 이상)
- YouTube 영상은 전체의 약 50% 목표 (30분 이상 영상만)
- @1DANG100 채널의 영상이 있으면 최우선으로 포함
- 우선순위 채널: @thewinterbookstore, @chaegiljji, @humanitylearning, @mkkimtv (한글)
- 우선순위 채널: @BTFC, @ClimbtheStacks, @JackEdwards, @arielbissett (영어)
- PDF 파일, 논문, 학술 사이트도 포함
- 위의 검색 쿼리와 검증 규칙을 따를 것

출력 형식: 설명 없이 URL만 출력 (각 줄에 한 개의 URL)
```

