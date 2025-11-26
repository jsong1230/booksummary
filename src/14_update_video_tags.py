#!/usr/bin/env python3
"""
기존 YouTube 영상의 태그 업데이트 스크립트
메타데이터 파일을 읽어서 이미 업로드된 영상의 태그를 업데이트합니다.
"""

import sys
import json
from pathlib import Path
from typing import Optional, Dict

# 상위 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 09_upload_from_metadata.py에서 import
import importlib.util
upload_spec = importlib.util.spec_from_file_location('upload_from_metadata', Path(__file__).parent / '09_upload_from_metadata.py')
upload_module = importlib.util.module_from_spec(upload_spec)
upload_spec.loader.exec_module(upload_module)

YouTubeUploader = upload_module.YouTubeUploader
load_metadata = upload_module.load_metadata
find_metadata_files = upload_module.find_metadata_files
load_uploaded_videos = upload_module.load_uploaded_videos

def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube 영상 태그 업데이트')
    parser.add_argument('--metadata-file', type=str, help='특정 메타데이터 파일 경로 (선택사항)')
    parser.add_argument('--video-id', type=str, help='특정 영상 ID (선택사항)')
    parser.add_argument('--auto', action='store_true', help='자동 업데이트 (확인 없이)')
    
    args = parser.parse_args()
    
    if not GOOGLE_API_AVAILABLE:
        print("❌ google-api-python-client가 필요합니다.")
        return
    
    print("=" * 60)
    print("🔄 YouTube 영상 태그 업데이트")
    print("=" * 60)
    print()
    
    try:
        uploader = YouTubeUploader()
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 업로드된 영상 목록 로드
    uploaded_videos = load_uploaded_videos()
    print(f"📋 업로드된 영상: {len(uploaded_videos)}개\n")
    
    # 특정 영상 ID가 지정된 경우
    if args.video_id:
        # 업로드 로그에서 video_path 찾기
        upload_log = Path("output/upload_log.json")
        video_path = None
        
        if upload_log.exists():
            try:
                with open(upload_log, 'r', encoding='utf-8') as f:
                    upload_history = json.load(f)
                    for entry in upload_history:
                        if entry.get('video_id') == args.video_id:
                            video_path = entry.get('video_path')
                            break
            except:
                pass
        
        # 메타데이터 파일 찾기
        metadata = None
        if video_path:
            # video_path에서 메타데이터 파일 경로 추정
            video_path_obj = Path(video_path)
            metadata_path = video_path_obj.parent / f"{video_path_obj.stem}.metadata.json"
            if metadata_path.exists():
                metadata = load_metadata(metadata_path)
        
        # 메타데이터 파일에서 직접 찾기
        if not metadata:
            metadata_files = find_metadata_files()
            for metadata_path in metadata_files:
                m = load_metadata(metadata_path)
                if m:
                    m_video_path = m.get('video_path', '')
                    # video_path 비교
                    if video_path and Path(m_video_path).name == Path(video_path).name:
                        metadata = m
                        break
        
        if not metadata:
            print(f"❌ 영상 ID {args.video_id}에 대한 메타데이터를 찾을 수 없습니다.")
            print(f"   업로드 로그를 확인하거나 메타데이터 파일을 직접 지정하세요.")
            return
        
        tags = metadata.get('tags', [])
        title = metadata.get('title', '')
        
        print(f"📌 제목: {title}")
        print(f"🏷️ 태그: {len(tags)}개")
        print()
        
        if not args.auto:
            confirm = input("태그를 업데이트하시겠습니까? (y/n): ").strip().lower()
            if confirm != 'y':
                print("취소되었습니다.")
                return
        
        success = uploader.update_video_metadata(
            video_id=args.video_id,
            tags=tags
        )
        
        if success:
            print("✅ 태그 업데이트 완료!")
        else:
            print("❌ 태그 업데이트 실패")
        
        return
    
    # 메타데이터 파일 찾기
    if args.metadata_file:
        metadata_files = [Path(args.metadata_file)]
    else:
        metadata_files = find_metadata_files()
    
    if not metadata_files:
        print("📭 메타데이터 파일을 찾을 수 없습니다.")
        print("   output/ 폴더에 *.metadata.json 파일이 있는지 확인하세요.")
        return
    
    print(f"📹 발견된 메타데이터: {len(metadata_files)}개\n")
    
    # 업로드 로그에서 video_id 찾기
    upload_log = Path("output/upload_log.json")
    video_id_map = {}
    
    if upload_log.exists():
        try:
            with open(upload_log, 'r', encoding='utf-8') as f:
                upload_history = json.load(f)
                for entry in upload_history:
                    video_path = entry.get('video_path', '')
                    video_id = entry.get('video_id', '')
                    if video_path and video_id:
                        video_id_map[video_path] = video_id
        except:
            pass
    
    # 영상 업데이트
    updated = []
    failed = []
    
    for i, metadata_path in enumerate(metadata_files, 1):
        print(f"[{i}/{len(metadata_files)}] {metadata_path.name}")
        
        # 메타데이터 로드
        metadata = load_metadata(metadata_path)
        if not metadata:
            print("   ⚠️ 메타데이터 로드 실패")
            failed.append(metadata_path.name)
            continue
        
        video_path = metadata.get('video_path', '')
        tags = metadata.get('tags', [])
        title = metadata.get('title', '')
        
        # video_id 찾기
        video_id = None
        if video_path in video_id_map:
            video_id = video_id_map[video_path]
        else:
            # 메타데이터에 video_id가 있는지 확인
            video_id = metadata.get('video_id')
        
        if not video_id:
            print(f"   ⚠️ 영상 ID를 찾을 수 없습니다. 업로드 로그를 확인하세요.")
            failed.append(metadata_path.name)
            continue
        
        print(f"   📌 제목: {title[:50]}...")
        print(f"   🏷️ 태그: {len(tags)}개")
        print(f"   🆔 영상 ID: {video_id}")
        print()
        
        if not args.auto:
            try:
                user_input = input(f"태그를 업데이트하시겠습니까? (y/n): ").strip().lower()
                if user_input != 'y':
                    print("   건너뜀")
                    continue
            except (EOFError, KeyboardInterrupt):
                print("   건너뜀")
                continue
        
        success = uploader.update_video_metadata(
            video_id=video_id,
            tags=tags
        )
        
        if success:
            updated.append({
                'video_id': video_id,
                'title': title,
                'metadata_file': metadata_path.name
            })
        else:
            failed.append(metadata_path.name)
        
        print()
    
    # 결과 요약
    print("=" * 60)
    print("📊 업데이트 결과")
    print("=" * 60)
    print(f"✅ 성공: {len(updated)}개")
    if updated:
        for item in updated:
            print(f"   - {item['title'][:50]}...")
    
    if failed:
        print(f"\n❌ 실패: {len(failed)}개")
        for item in failed:
            print(f"   - {item}")


if __name__ == "__main__":
    # GOOGLE_API_AVAILABLE import
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from googleapiclient.errors import HttpError
        GOOGLE_API_AVAILABLE = True
    except ImportError:
        GOOGLE_API_AVAILABLE = False
    
    exit(main())
