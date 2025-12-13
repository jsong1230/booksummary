#!/usr/bin/env python3
"""
YouTube OAuth2 인증을 통해 refresh token을 받는 스크립트
book summary 채널에 대한 refresh token을 생성합니다.
"""

import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# YouTube API 스코프
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_refresh_token():
    """OAuth2 인증을 통해 refresh token 받기"""
    # client_secret.json 파일 경로
    client_secret_path = Path("client_secret.json")
    
    if not client_secret_path.exists():
        print("❌ client_secret.json 파일을 찾을 수 없습니다.")
        print("   프로젝트 루트에 client_secret.json 파일을 배치하세요.")
        return None
    
    print("=" * 60)
    print("🔐 YouTube OAuth2 인증")
    print("=" * 60)
    print()
    print("⚠️ 중요: OAuth 인증 화면에서 'book summary' 채널을 선택하세요!")
    print()
    
    try:
        # OAuth 플로우 시작
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret_path),
            SCOPES
        )
        
        # 로컬 서버에서 인증 (포트 8080 사용)
        credentials = flow.run_local_server(
            port=8080,
            prompt='consent',
            open_browser=True
        )
        
        # Refresh token 확인
        if credentials.refresh_token:
            print()
            print("=" * 60)
            print("✅ 인증 성공!")
            print("=" * 60)
            print()
            print("📋 다음 정보를 .env 파일에 추가하세요:")
            print()
            print(f"YOUTUBE_CLIENT_ID={credentials.client_id}")
            print(f"YOUTUBE_CLIENT_SECRET={credentials.client_secret}")
            print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
            print()
            print("=" * 60)
            print()
            
            # credentials.json으로도 저장 (선택사항)
            save_credentials = input("credentials.json 파일로도 저장하시겠습니까? (y/n): ").strip().lower()
            if save_credentials == 'y':
                creds_dict = {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                }
                with open('credentials.json', 'w') as f:
                    json.dump(creds_dict, f, indent=2)
                print("✅ credentials.json 저장 완료")
            
            return credentials.refresh_token
        else:
            print("❌ Refresh token을 받지 못했습니다.")
            print("   OAuth 인증 시 'consent' 화면에서 모든 권한을 승인했는지 확인하세요.")
            return None
            
    except Exception as e:
        print(f"❌ 인증 실패: {e}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # 필요한 패키지 확인
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("❌ google-auth-oauthlib 패키지가 필요합니다.")
        print("   설치: pip install google-auth-oauthlib")
        exit(1)
    
    get_refresh_token()


