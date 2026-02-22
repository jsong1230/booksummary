"""
YouTube OAuth 재인증 스크립트

기존 refresh token이 youtube.force-ssl 스코프를 포함하지 않아
API 호출 시 권한 오류가 발생하는 경우, 이 스크립트를 실행하여
새로운 스코프를 포함한 refresh token을 재발급받습니다.

사용법:
    /Users/jsong/.pyenv/versions/3.11.10/bin/python scripts/reauth_youtube.py

완료 후:
    출력된 YOUTUBE_REFRESH_TOKEN 값을 .env 파일에 업데이트하세요.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

# 재인증에 사용할 전체 스코프 목록
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]


def main():
    """OAuth 재인증을 실행하고 새로운 refresh token을 출력합니다."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("오류: google-auth-oauthlib 패키지가 필요합니다.")
        print("설치 명령어: pip install google-auth-oauthlib")
        return

    # client_secret.json 파일 확인
    client_secret_path = project_root / 'secrets' / 'client_secret.json'
    if not client_secret_path.exists():
        print(f"오류: secrets/client_secret.json 파일을 찾을 수 없습니다.")
        print(f"확인한 경로: {client_secret_path}")
        print("")
        print("Google Cloud Console에서 OAuth 클라이언트 시크릿 파일을 다운로드하여")
        print("secrets/client_secret.json 경로에 저장하세요.")
        return

    # 기존 토큰 캐시 파일 삭제 (있는 경우)
    token_cache_path = project_root / 'secrets' / 'token_cache.json'
    if token_cache_path.exists():
        token_cache_path.unlink()
        print(f"기존 토큰 캐시 삭제: {token_cache_path.name}")

    print("=" * 60)
    print("YouTube OAuth 재인증")
    print("=" * 60)
    print("")
    print("다음 스코프로 재인증을 진행합니다:")
    for scope in SCOPES:
        print(f"  - {scope}")
    print("")
    print("브라우저가 열리면 Google 계정으로 로그인하고")
    print("YouTube 접근 권한을 허용해주세요.")
    print("")

    try:
        # OAuth 인증 플로우 실행
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path),
            SCOPES
        )
        credentials = flow.run_local_server(port=8080)

        # 결과 출력
        print("")
        print("=" * 60)
        print("새로운 OAuth 토큰 발급 완료")
        print("=" * 60)
        print("")
        print("아래 값을 .env 파일의 YOUTUBE_REFRESH_TOKEN에 업데이트하세요:")
        print("")
        print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
        print("")

        # 토큰 정보를 임시 파일로 저장 (검증용)
        temp_token_path = project_root / 'secrets' / 'new_token_temp.json'
        import json
        token_data = {
            'refresh_token': credentials.refresh_token,
            'token': credentials.token,
            'scopes': list(credentials.scopes) if credentials.scopes else SCOPES,
        }
        with open(temp_token_path, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, ensure_ascii=False, indent=2)

        print(f"토큰 정보가 임시 파일에도 저장되었습니다: {temp_token_path}")
        print("확인 후 이 임시 파일은 삭제하세요.")
        print("")
        print("다음 단계:")
        print("  1. 위의 YOUTUBE_REFRESH_TOKEN 값을 복사합니다.")
        print("  2. .env 파일을 열어 YOUTUBE_REFRESH_TOKEN 값을 교체합니다.")
        print("  3. secrets/new_token_temp.json 파일을 삭제합니다.")
        print("  4. 업로드 스크립트를 다시 실행합니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
        print("")
        print("인증에 실패했습니다. 다음을 확인하세요:")
        print("  - secrets/client_secret.json 파일이 올바른지 확인")
        print("  - 포트 8080이 사용 가능한지 확인")
        print("  - Google Cloud Console에서 OAuth 동의 화면 설정 확인")


if __name__ == '__main__':
    main()
