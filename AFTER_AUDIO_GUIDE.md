# 오디오 생성 완료 후 가이드

NotebookLM에서 AI 오디오 오버뷰 생성이 완료되면 다음 단계를 진행하세요.

## 1단계: 오디오 다운로드 및 저장

### NotebookLM에서 다운로드
1. NotebookLM에서 생성된 오디오 확인
2. **다운로드** 버튼 클릭
3. 파일 형식: `.wav` 또는 `.mp3` (둘 다 가능)

### 프로젝트에 저장
```bash
# 오디오 파일을 assets/audio/ 폴더에 저장
# 파일명 형식: {책제목}_review.wav 또는 {책제목}_review.mp3
# 예시: 노르웨이의_숲_review.wav
```

**권장 파일명:**
- `노르웨이의_숲_review.wav` (또는 .mp3)
- 또는 `노르웨이의_숲_notebooklm.wav`

## 2단계: 오디오 정보 확인

오디오 파일의 길이와 품질을 확인하세요:
- **길이**: 영상 제작 시 이미지 배치 계획에 필요
- **품질**: 필요시 노이즈 제거나 볼륨 조정

## 3단계: 이미지 자산 확인

이미지가 준비되어 있는지 확인:
```bash
# 이미지 확인
ls -la assets/images/노르웨이의_숲/
```

필요한 이미지:
- ✅ `cover.jpg` - 책 표지
- ✅ `mood_*.jpg` - 무드 이미지들 (5~10장)

이미지가 없으면:
```bash
./run_images.sh
# 책 제목: 노르웨이의 숲
# 저자: 무라카미 하루키
# 키워드: 문학, 일본, 청춘, 상실 등
```

## 4단계: 영상 제작 (Phase 4)

오디오와 이미지가 준비되면 영상 제작을 시작할 수 있습니다.

### 준비 사항 체크리스트
- [ ] 오디오 파일: `assets/audio/노르웨이의_숲_review.wav`
- [ ] 책 표지: `assets/images/노르웨이의_숲/cover.jpg`
- [ ] 무드 이미지: `assets/images/노르웨이의_숲/mood_*.jpg` (5~10장)
- [ ] 폰트 (선택사항): `assets/fonts/` 폴더에 자막용 폰트

### 영상 제작 실행
```bash
# 영상 제작 스크립트 실행 (Phase 4에서 구현 예정)
./run_make_video.sh
```

또는:
```bash
source venv/bin/activate
python src/03_make_video.py
```

## 5단계: 영상 제작 옵션

영상 제작 시 설정할 수 있는 옵션:

### 기본 설정
- **해상도**: 1080p (1920x1080)
- **프레임레이트**: 30fps
- **형식**: MP4

### 효과 옵션
- **Ken Burns 효과**: 이미지 줌인/패닝 (기본 활성화)
- **전환 효과**: 이미지 간 페이드 (기본 활성화)
- **자막**: OpenAI Whisper로 자동 생성 (선택사항)

### 출력
- **저장 위치**: `output/노르웨이의_숲_review.mp4`

## 6단계: YouTube 업로드 (선택사항)

영상이 완성되면 YouTube에 자동 업로드할 수 있습니다:
```bash
./run_upload.sh
```

## 현재 상태 확인

```bash
# 오디오 파일 확인
ls -la assets/audio/

# 이미지 확인
ls -la assets/images/노르웨이의_숲/

# 준비 완료 여부 확인
echo "✅ 오디오: $(ls assets/audio/*.wav assets/audio/*.mp3 2>/dev/null | wc -l | xargs)개"
echo "✅ 이미지: $(ls assets/images/노르웨이의_숲/*.jpg 2>/dev/null | wc -l | xargs)개"
```

## 다음 작업

Phase 4 영상 합성 스크립트가 준비되면 바로 사용할 수 있습니다!

