#!/usr/bin/env python3
"""
YouTube OAuth 재인증 스크립트 (Playwright 자동화)

브라우저 자동화를 통해 OAuth 인증 과정을 자동화합니다.
"""
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

# 재인증에 사용할 전체 스코프 목록
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.force-ssl',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
]

def get_oauth_url():
    """OAuth 인증 URL 생성"""
    return (
        "https://accounts.google.com/o/oauth2/auth?response_type=code"
        "&client_id=200915652800-28bfif4421eslt3cb1ke2causahbl58c.apps.googleusercontent.com"
        "&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F"
        "&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.upload+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyoutube.force-ssl+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fyt-analytics.readonly"
        "&state=LBHXsTkWP9bdo5EL60eVN7CXrPdpmb"
        "&access_type=offline"
    )

def extract_access_token_from_page(page):
    """페이지에서 액세스 토큰 추출"""
    try:
        # 페이지 로드 대기
        time.sleep(2)

        # 콘솤창에 표시되는 액세스 토큰 찾기
        # URL 쿼리 파라미터에서 추출하는 것이 더 간단
        for frame in page.frames:
            try:
                # URL에서 토큰 추출 (redirect 후 URL에서)
                url = page.url
                if "access_token=" in url:
                    # URL에서 토큰 추출
                    token_start = url.index("access_token=") + len("access_token=")
                    token_end = url.find("&", token_start)
                    if token_end == -1:
                        token_end = len(url)
                    access_token = url[token_start:token_end]
                    return access_token
            except:
                continue

        # body 텍스트에서도 시도
        body_text = page.body()
        if "access_token=" in body_text:
            for line in body_text.split('\n'):
                if "access_token=" in line:
                    token = line.split("access_token=")[1].split("&")[0].strip('"')
                    return token

        return None


def save_credentials(access_token, refresh_token=None):
    """credentials.json 파일 저장"""
    # 기존 client_secret.json 로드
    client_secret_path = project_root / 'secrets' / 'client_secret.json'
    with open(client_secret_path, 'r', encoding='utf-8') as f:
        client_data = json.load(f)

    # credentials 데이터 생성
    creds_data = {
        'token': access_token,
        'refresh_token': refresh_token or "",
        'token_uri': "https://oauth2.googleapis.com/token",
        'client_id': client_data.get('installed', {}).get('client_id', ""),
        'client_secret': client_data.get('installed', {}).get('client_secret', ""),
        'scopes': SCOPES,
    }

    # credentials.json 저장
    credentials_path = project_root / 'secrets' / 'credentials.json'
    with open(credentials_path, 'w', encoding='utf-8') as f:
        json.dump(creds_data, f, ensure_ascii=False, indent=2)

    print(f"✅ secrets/credentials.json 저장 완료")

    # .env 파일도 업데이트 (YOUTUBE_REFRESH_TOKEN은 빈 문자열로 둠)
    env_path = project_root / '.env'
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # YOUTUBE_REFRESH_TOKEN 라인 찾아 빈 문자열로 변경
    updated_lines = []
    for line in lines:
        if line.startswith('YOUTUBE_REFRESH_TOKEN='):
            updated_lines.append('YOUTUBE_REFRESH_TOKEN=\n')
        else:
            updated_lines.append(line)

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    print(f"✅ .env 파일 업데이트 완료 (YOUTUBE_REFRESH_TOKEN 초기화)")


def main():
    """메인 함수"""
    print("=" * 60)
    print("YouTube OAuth 재인증 (Playwright 자동화)")
    print("=" * 60)

    oauth_url = get_oauth_url()

    print("")
    print(f"OAuth 인증 URL을 브라우저에서 열어주세요:")
    print(f"{oauth_url}")
    print("")
    print("인증이 완료되면 자동으로 토큰을 추출합니다...")
    print("")

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(oauth_url, wait_until="networkidle")

            print("페이지 로드 완료. 콘솤창이 뜨면 Enter를 눌르세요...")
            print("")

            # 사용자가 로그인하고 권한 승인할 때까지 대기
            print("로그인 후 5초 대기 중... (취소하려면 Ctrl+C)")

            time.sleep(5)

            # 액세스 토큰 추출 시도
            access_token = extract_access_token_from_page(page)

            if access_token:
                save_credentials(access_token)
                print("")
                print("=" * 60)
                print("✅ OAuth 인증 완료!")
                print("=" * 60)
                print("")
                print("액세스 토큰이 추출되었습니다:")
                print(f"   {access_token[:50]}...")
                print("")
                print("이제 댓글 추가 스크립트를 실행하세요:")
                print("   python src/25_batch_add_pinned_comments.py --apply --resume --limit 50")
                return
            else:
                print("⚠️ 액세스 토큰을 추출하지 못했습니다.")
                print("URL에서 직접 확인해주세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    finally:
        if browser:
            browser.close()


if __name__ == "__main__":
    main()
