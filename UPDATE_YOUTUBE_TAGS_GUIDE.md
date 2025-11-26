# YouTube 영상 태그 업데이트 가이드

## 문제
기존 YouTube 영상의 태그를 업데이트하려면 추가 API 권한이 필요합니다.

## 해결 방법

### 방법 1: YouTube Studio에서 수동 업데이트 (가장 간단)
1. YouTube Studio (https://studio.youtube.com) 접속
2. 콘텐츠 메뉴에서 영상 선택
3. 세부정보 탭에서 태그 수정
4. 저장

### 방법 2: API를 통한 자동 업데이트 (새로운 refresh token 필요)

#### 1. OAuth2 스코프 추가
기존 refresh token에 `youtube.force-ssl` 스코프를 추가해야 합니다.

#### 2. 새로운 refresh token 발급
```python
# 새로운 스코프로 인증
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'  # 추가 필요
]
```

#### 3. 스크립트 사용
```bash
# 특정 영상 ID로 태그 업데이트
python3 src/14_update_video_tags.py --video-id VIDEO_ID --auto

# 모든 메타데이터 파일의 태그 업데이트
python3 src/14_update_video_tags.py --auto
```

## 현재 상태
- 메타데이터 파일의 태그는 이미 업데이트됨 ✅
- YouTube API 업데이트는 추가 권한 필요 ⚠️

## 추천
**방법 1 (수동 업데이트)**을 권장합니다. 
- 가장 간단하고 안전함
- 추가 설정 불필요
- YouTube Studio에서 직접 확인 가능
