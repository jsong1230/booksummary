"""
유튜브 롱폼 북튜브를 위한 깊이 있는 자료 수집 스크립트
{작가}의 『{책제목}』에 대해 30~60분짜리 해설/분석 유튜브 영상을 만들 예정.
NotebookLM에 넣을 자료로 쓸 수 있도록, 이 책을 깊이 있게 다루는 URL 30개를 수집.
"""

import os
import sys
import csv
import time
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from urllib.parse import urlparse

# src 디렉토리를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

# YouTube API import
try:
    from googleapiclient.discovery import build
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

load_dotenv()


class DeepURLCollector:
    """깊이 있는 자료 수집 클래스"""
    
    # 최우선 검색할 YouTube 채널 (모든 언어)
    TOP_PRIORITY_CHANNEL = '@1DANG100'  # 일당백 - 최우선
    
    # 우선 검색할 YouTube 채널 (한글)
    PRIORITY_KO_CHANNELS = [
        '@thewinterbookstore',  # 겨울서점
        '@chaegiljji',  # 책읽찌라
        '@humanitylearning',  # 인문학TV 휴식같은 지식
        '@mkkimtv',  # 김미경TV
    ]
    
    # 추가 검색할 YouTube 채널 (한글)
    ADDITIONAL_KO_CHANNELS = [
        '@Gwana',  # 과나
        '@jachung',  # 라이프해커 자청
        '@channelyes24',  # 채널예스
    ]
    
    # 우선 검색할 YouTube 채널 (영어)
    PRIORITY_EN_CHANNELS = [
        '@BTFC',  # Better Than Food
        '@ClimbtheStacks',  # Climb The Stacks
        '@JackEdwards',  # Jack Edwards
        '@arielbissett',  # Ariel Bissett
    ]
    
    # 추가 검색할 YouTube 채널 (영어)
    ADDITIONAL_EN_CHANNELS = [
        '@withcindy',  # Read with Cindy
        '@thebookleo',  # The Book Leo
        '@InsightJunkie',  # Insight Junkie
    ]
    
    # 제외할 도메인 패턴
    EXCLUDED_DOMAINS = [
        'kyobobook.co.kr', 'yes24.com', 'aladin.co.kr', 'interpark.com',
        'amazon.com', 'amazon.co.kr', 'amazon.co.uk',
        'naver.com/shopping', 'coupang.com', '11st.co.kr',
        'gmarket.co.kr', 'auction.co.kr',
        'ko.wikipedia.org', 'namu.wiki', 'en.wikipedia.org',
        'wikidata.org', 'wikipedia.org',
    ]
    
    # 제외할 URL 패턴
    EXCLUDED_PATTERNS = [
        r'/product/', r'/goods/', r'/item/', r'/shop/',
        r'/isbn/', r'/book/', r'/detail/',
        r'/search\?', r'/category/',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.ddgs = DDGS()
        
        # YouTube API 초기화
        self.youtube = None
        if YOUTUBE_API_AVAILABLE:
            youtube_api_key = os.getenv("YOUTUBE_API_KEY") or os.getenv("GOOGLE_BOOKS_API_KEY")
            if youtube_api_key:
                try:
                    self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
                    print("✅ YouTube API 초기화 완료")
                except Exception as e:
                    print(f"⚠️ YouTube API 초기화 실패: {e}")
    
    def is_excluded_url(self, url: str) -> bool:
        """URL이 제외 대상인지 확인"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 도메인 체크
        for excluded_domain in self.EXCLUDED_DOMAINS:
            if excluded_domain in domain:
                return True
        
        # URL 패턴 체크
        for pattern in self.EXCLUDED_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        return False
    
    def validate_url_content(self, url: str, book_title: str, author: str = None, strict: bool = True) -> Dict[str, any]:
        """URL 내용 검증 - 책 제목이 실제로 포함되어 있는지 확인
        
        Args:
            url: 검증할 URL
            book_title: 책 제목
            author: 저자 이름
            strict: 엄격한 검증 여부 (False면 더 관대하게 검증)
        """
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = None
            if soup.title:
                title = soup.title.string.strip()
            elif soup.find('meta', property='og:title'):
                title = soup.find('meta', property='og:title').get('content', '').strip()
            
            # 설명 추출
            description = None
            if soup.find('meta', property='og:description'):
                description = soup.find('meta', property='og:description').get('content', '').strip()
            elif soup.find('meta', attrs={'name': 'description'}):
                description = soup.find('meta', attrs={'name': 'description'}).get('content', '').strip()
            
            # 본문 텍스트 추출 (간단히)
            body_text = ''
            if soup.body:
                # 스크립트와 스타일 제거
                for script in soup.body(["script", "style"]):
                    script.decompose()
                body_text = soup.body.get_text(separator=' ', strip=True)[:2000]  # 처음 2000자만
            
            # 검증: 책 제목이 포함되어 있는지
            combined_text = f"{title} {description} {body_text}".lower()
            book_title_lower = book_title.lower()
            
            # 책 제목의 주요 단어 추출 (긴 제목의 경우)
            book_title_words = [w for w in book_title_lower.split() if len(w) > 2]
            # 주요 키워드 (예: "21세기를 위한 21가지 제언" -> "21세기", "21가지", "제언")
            key_words = [w for w in book_title_lower.split() if len(w) >= 3]
            
            # 책 제목이 포함되어 있지 않으면 제외
            title_found = book_title_lower in combined_text
            key_words_found = any(word in combined_text for word in key_words) if key_words else False
            
            if not title_found and not key_words_found:
                # 저자 이름도 확인
                if author:
                    author_lower = author.lower()
                    author_parts = [w for w in author_lower.split() if len(w) > 2]
                    author_found = any(part in combined_text for part in author_parts) if author_parts else False
                    if not author_found:
                        if strict:
                            return {
                                'valid': False,
                                'reason': 'book_title_not_found',
                                'title': title,
                                'description': description[:200] if description else None
                            }
                        # 엄격하지 않으면 저자 이름만 있어도 통과
                else:
                    if strict:
                        return {
                            'valid': False,
                            'reason': 'book_title_not_found',
                            'title': title,
                            'description': description[:200] if description else None
                        }
            
            # 너무 짧은 콘텐츠 체크 (엄격 모드일 때만, 본문이 100자 미만이면 제외 - 완화)
            if strict and len(body_text) < 100 and not url.startswith('https://www.youtube.com'):
                return {
                    'valid': False,
                    'reason': 'content_too_short',
                    'title': title,
                    'description': description[:200] if description else None
                }
            
            return {
                'valid': True,
                'title': title,
                'description': description[:200] if description else None,
                'status_code': response.status_code
            }
            
        except requests.exceptions.Timeout:
            # 타임아웃이어도 URL 자체는 유효할 수 있으므로, 제목만으로 판단
            return {'valid': True, 'title': None, 'description': None, 'reason': 'timeout_but_accepted'}
        except requests.exceptions.RequestException as e:
            # 403, 404 등 오류는 제외하되, 다른 오류는 일단 통과
            if '403' in str(e) or '404' in str(e) or 'Forbidden' in str(e):
                return {'valid': False, 'reason': str(e)}
            # 기타 오류는 일단 통과 (검증 완화)
            return {'valid': True, 'title': None, 'description': None, 'reason': 'request_error_but_accepted'}
        except Exception as e:
            # 기타 예외는 일단 통과 (검증 완화)
            return {'valid': True, 'title': None, 'description': None, 'reason': 'exception_but_accepted'}
    
    def search_channel_videos(self, channel_handle: str, book_title: str, author: str = None) -> List[Dict]:
        """특정 YouTube 채널에서 책 관련 영상 검색"""
        if not self.youtube:
            return []
        
        videos = []
        
        try:
            # 채널 핸들로 채널 ID 찾기
            channel_response = self.youtube.search().list(
                q=channel_handle,
                part='id,snippet',
                type='channel',
                maxResults=1
            ).execute()
            
            if not channel_response.get('items'):
                return []
            
            channel_id = channel_response['items'][0]['id']['channelId']
            
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_details = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not channel_details.get('items'):
                return []
            
            upload_playlist_id = channel_details['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # 플레이리스트에서 영상 검색
            search_query = book_title
            if author:
                search_query = f"{book_title} {author}"
            
            # 채널의 모든 영상에서 검색
            playlist_items = []
            next_page_token = None
            
            while len(playlist_items) < 50:  # 최대 50개 영상 확인
                try:
                    request_params = {
                        'part': 'snippet,contentDetails',
                        'playlistId': upload_playlist_id,
                        'maxResults': 50
                    }
                    if next_page_token:
                        request_params['pageToken'] = next_page_token
                    
                    response = self.youtube.playlistItems().list(**request_params).execute()
                    playlist_items.extend(response.get('items', []))
                    
                    next_page_token = response.get('nextPageToken')
                    if not next_page_token:
                        break
                except:
                    break
            
            # 책 제목과 관련된 영상 필터링
            for item in playlist_items:
                video_title = item['snippet']['title']
                video_description = item['snippet'].get('description', '')
                combined = f"{video_title} {video_description}".lower()
                
                # 책 제목이 포함되어 있는지 확인
                if book_title.lower() not in combined:
                    if author:
                        author_lower = author.lower()
                        if not any(part in combined for part in author_lower.split() if len(part) > 2):
                            continue
                    else:
                        continue
                
                video_id = item['contentDetails']['videoId']
                
                # 영상 길이 확인 (30분 이상)
                try:
                    video_response = self.youtube.videos().list(
                        part='contentDetails',
                        id=video_id
                    ).execute()
                    
                    duration_str = video_response['items'][0]['contentDetails']['duration']
                    duration_seconds = self._parse_duration(duration_str)
                    
                    if duration_seconds < 1800:  # 30분 미만이면 제외
                        continue
                except:
                    pass  # 길이 정보를 못 가져와도 계속 진행
                
                videos.append({
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'title': video_title,
                    'description': video_description[:200],
                    'type': 'youtube',
                    'channel': '@1DANG100'
                })
            
        except Exception as e:
            print(f"  ⚠️ 채널 검색 오류: {e}")
        
        return videos
    
    def search_youtube_videos(self, book_title: str, author: str = None, max_results: int = 10, lang: str = 'ko') -> List[Dict]:
        """YouTube에서 긴 리뷰/해설/강의 영상 검색"""
        if not self.youtube:
            return []
        
        videos = []
        seen_video_ids = set()
        
        # 1. 일당백(@1DANG100) 채널 최우선 검색
        print(f"  📺 [{self.TOP_PRIORITY_CHANNEL}] 일당백 채널 최우선 검색 중...")
        channel_videos = self.search_channel_videos(self.TOP_PRIORITY_CHANNEL, book_title, author)
        for video in channel_videos:
            video_id = video['url'].split('v=')[-1].split('&')[0]
            if video_id not in seen_video_ids:
                seen_video_ids.add(video_id)
                videos.append(video)
                print(f"    ✓ [일당백 최우선] {video['title'][:60]}...")
        
        # 2. 우선순위 채널 검색
        priority_channels = self.PRIORITY_KO_CHANNELS if lang == 'ko' else self.PRIORITY_EN_CHANNELS
        print(f"  📺 우선순위 채널에서 검색 중 ({len(priority_channels)}개 채널)...")
        for channel_handle in priority_channels:
            if len(videos) >= max_results:
                break
            channel_videos = self.search_channel_videos(channel_handle, book_title, author)
            for video in channel_videos:
                video_id = video['url'].split('v=')[-1].split('&')[0]
                if video_id not in seen_video_ids:
                    seen_video_ids.add(video_id)
                    videos.append(video)
                    channel_name = channel_handle.replace('@', '')
                    print(f"    ✓ [{channel_name}] {video['title'][:60]}...")
                    if len(videos) >= max_results:
                        break
        
        # 3. 추가 채널 검색 (여유가 있을 때)
        if len(videos) < max_results:
            additional_channels = self.ADDITIONAL_KO_CHANNELS if lang == 'ko' else self.ADDITIONAL_EN_CHANNELS
            print(f"  📺 추가 채널에서 검색 중 ({len(additional_channels)}개 채널)...")
            for channel_handle in additional_channels:
                if len(videos) >= max_results:
                    break
                channel_videos = self.search_channel_videos(channel_handle, book_title, author)
                for video in channel_videos:
                    video_id = video['url'].split('v=')[-1].split('&')[0]
                    if video_id not in seen_video_ids:
                        seen_video_ids.add(video_id)
                        videos.append(video)
                        channel_name = channel_handle.replace('@', '')
                        print(f"    ✓ [{channel_name}] {video['title'][:60]}...")
                        if len(videos) >= max_results:
                            break
        
        # 4. 일반 검색 (채널 검색으로 부족할 때)
        if len(videos) < max_results:
            print("  📺 일반 YouTube 검색 중...")
            # 검색 쿼리 생성
            if lang == 'ko':
                queries = [
                    f"{book_title} {author} 해설" if author else f"{book_title} 해설",
                    f"{book_title} {author} 분석" if author else f"{book_title} 분석",
                    f"{book_title} {author} 강의" if author else f"{book_title} 강의",
                    f"{book_title} {author} 강연" if author else f"{book_title} 강연",
                    f"{book_title} {author} 북토크" if author else f"{book_title} 북토크",
                    f"{book_title} {author} 리뷰" if author else f"{book_title} 리뷰",
                ]
            else:
                queries = [
                    f"{book_title} {author} analysis" if author else f"{book_title} analysis",
                    f"{book_title} {author} lecture" if author else f"{book_title} lecture",
                    f"{book_title} {author} review" if author else f"{book_title} review",
                    f"{book_title} {author} discussion" if author else f"{book_title} discussion",
                    f"{book_title} {author} book talk" if author else f"{book_title} book talk",
                ]
            
            region = 'KR' if lang == 'ko' else 'US'
        
        for query in queries:
            if len(videos) >= max_results:
                break
            
            try:
                search_response = self.youtube.search().list(
                    q=query,
                    part='id,snippet',
                    type='video',
                    maxResults=5,
                    order='relevance',
                    regionCode=region,
                    videoDuration='long'  # 긴 영상만 (20분 이상, 실제로는 30분 이상 필터링)
                ).execute()
                
                for item in search_response.get('items', []):
                    if len(videos) >= max_results:
                        break
                    
                    video_id = item['id']['videoId']
                    if video_id in seen_video_ids:
                        continue
                    
                    video_title = item['snippet']['title']
                    video_description = item['snippet'].get('description', '')
                    
                    # 책 제목이 포함되어 있는지 확인
                    combined = f"{video_title} {video_description}".lower()
                    if book_title.lower() not in combined:
                        if author:
                            author_lower = author.lower()
                            if not any(part in combined for part in author_lower.split() if len(part) > 2):
                                continue
                        else:
                            continue
                    
                    # 영상 길이 정보 가져오기 (선택적)
                    try:
                        video_response = self.youtube.videos().list(
                            part='contentDetails',
                            id=video_id
                        ).execute()
                        
                        duration_str = video_response['items'][0]['contentDetails']['duration']
                        # PT15M30S 형식을 파싱
                        duration_seconds = self._parse_duration(duration_str)
                        
                        # 30분(1800초) 미만이면 제외 (롱폼 콘텐츠만)
                        if duration_seconds < 1800:
                            continue
                    except:
                        pass  # 길이 정보를 못 가져와도 계속 진행
                    
                    seen_video_ids.add(video_id)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    videos.append({
                        'url': video_url,
                        'title': video_title,
                        'description': video_description[:200],
                        'type': 'youtube'
                    })
                    print(f"    ✓ YouTube: {video_title[:60]}...")
                
                time.sleep(0.5)  # API 제한 방지
                
            except Exception as e:
                print(f"  ⚠️ YouTube 검색 오류: {e}")
                continue
        
        return videos
    
    def _parse_duration(self, duration_str: str) -> int:
        """ISO 8601 duration 형식 파싱 (PT15M30S -> 초)"""
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    
    def search_web_urls(self, book_title: str, author: str = None, max_results: int = 50, lang: str = 'ko') -> List[Dict]:
        """웹에서 깊이 있는 자료 검색 (PDF, 논문, 학술 사이트 포함)"""
        urls = []
        seen_urls = set()
        
        # 학술 사이트 및 특정 사이트 목록
        academic_sites_ko = [
            'site:academia.edu',
            'site:researchgate.net',
            'site:jstor.org',
            'site:scholar.google.com',
            'site:dbpia.co.kr',
            'site:kci.go.kr',
            'site:riss.kr',
            'site:brunch.co.kr',
            'site:medium.com',
            'site:blog.naver.com',
            'site:blog.daum.net',
            'site:post.naver.com',
        ]
        
        academic_sites_en = [
            'site:academia.edu',
            'site:researchgate.net',
            'site:jstor.org',
            'site:scholar.google.com',
            'site:medium.com',
            'site:theguardian.com',
            'site:nytimes.com',
            'site:newyorker.com',
            'site:lrb.co.uk',  # London Review of Books
            'site:nybooks.com',  # New York Review of Books
        ]
        
        if lang == 'ko':
            # 일반 검색 쿼리
            queries = [
                f'"{book_title}" {author} 해설' if author else f'"{book_title}" 해설',
                f'"{book_title}" {author} 분석' if author else f'"{book_title}" 분석',
                f'"{book_title}" {author} 비평' if author else f'"{book_title}" 비평',
                f'"{book_title}" {author} 논문' if author else f'"{book_title}" 논문',
                f'"{book_title}" {author} 에세이' if author else f'"{book_title}" 에세이',
                f'"{book_title}" {author} 강의자료' if author else f'"{book_title}" 강의자료',
                f'"{book_title}" {author} 독후감' if author else f'"{book_title}" 독후감',
                f'"{book_title}" {author} 서평' if author else f'"{book_title}" 서평',
                f'"{book_title}" {author} 리뷰' if author else f'"{book_title}" 리뷰',
            ]
            
            # PDF 파일 검색
            pdf_queries = [
                f'"{book_title}" {author} filetype:pdf' if author else f'"{book_title}" filetype:pdf',
                f'"{book_title}" {author} 논문 pdf' if author else f'"{book_title}" 논문 pdf',
                f'"{book_title}" {author} 강의자료 pdf' if author else f'"{book_title}" 강의자료 pdf',
            ]
            
            # 학술 사이트 검색
            for site in academic_sites_ko:
                queries.append(f'"{book_title}" {author} {site}' if author else f'"{book_title}" {site}')
        else:
            # 일반 검색 쿼리
            queries = [
                f'"{book_title}" {author} analysis' if author else f'"{book_title}" analysis',
                f'"{book_title}" {author} review' if author else f'"{book_title}" review',
                f'"{book_title}" {author} essay' if author else f'"{book_title}" essay',
                f'"{book_title}" {author} critique' if author else f'"{book_title}" critique',
                f'"{book_title}" {author} lecture' if author else f'"{book_title}" lecture',
                f'"{book_title}" {author} discussion' if author else f'"{book_title}" discussion',
            ]
            
            # PDF 파일 검색
            pdf_queries = [
                f'"{book_title}" {author} filetype:pdf' if author else f'"{book_title}" filetype:pdf',
                f'"{book_title}" {author} paper pdf' if author else f'"{book_title}" paper pdf',
                f'"{book_title}" {author} essay pdf' if author else f'"{book_title}" essay pdf',
            ]
            
            # 학술 사이트 검색
            for site in academic_sites_en:
                queries.append(f'"{book_title}" {author} {site}' if author else f'"{book_title}" {site}')
        
        # PDF 검색 쿼리 추가
        queries.extend(pdf_queries)
        
        for query in queries:
            if len(urls) >= max_results:
                break
            
            try:
                print(f"  검색 중: {query[:60]}...")
                # 더 많은 결과 수집 (최대 20개)
                results = list(self.ddgs.text(query, max_results=20))
                
                for result in results:
                    if len(urls) >= max_results:
                        break
                    
                    url = result.get('href', '')
                    if not url or url in seen_urls:
                        continue
                    
                    # 제외 URL 체크
                    if self.is_excluded_url(url):
                        continue
                    
                    # PDF 파일은 검증 완화 (제목만 확인)
                    is_pdf = url.lower().endswith('.pdf') or '/pdf' in url.lower() or url.lower().endswith('.pdf?')
                    if is_pdf:
                        # PDF는 제목만 간단히 확인
                        title = result.get('title', '').lower()
                        body = result.get('body', '').lower()
                        combined = f"{title} {body}".lower()
                        if book_title.lower() not in combined:
                            if author:
                                author_lower = author.lower()
                                if not any(part in combined for part in author_lower.split() if len(part) > 2):
                                    continue
                            else:
                                continue
                        seen_urls.add(url)
                        urls.append({
                            'url': url,
                            'title': result.get('title', ''),
                            'description': result.get('body', '')[:200] if result.get('body') else '',
                            'type': 'pdf'
                        })
                        print(f"    ✓ PDF: {url[:80]}...")
                        continue
                    
                    # 학술 사이트는 검증 완화
                    is_academic = any(site in url.lower() for site in [
                        'academia.edu', 'researchgate.net', 'jstor.org', 
                        'scholar.google.com', 'dbpia.co.kr', 'kci.go.kr', 'riss.kr'
                    ])
                    
                    # 블로그/미디엄 등은 검증 더 완화
                    is_blog = any(site in url.lower() for site in [
                        'blog.naver.com', 'blog.daum.net', 'post.naver.com',
                        'medium.com', 'brunch.co.kr', 'tistory.com'
                    ])
                    
                    # URL 검증 (학술 사이트와 블로그는 더 관대하게)
                    validation = self.validate_url_content(url, book_title, author, strict=not (is_academic or is_blog))
                    if not validation.get('valid'):
                        # 디버깅: 왜 제외되었는지 로그 (처음 몇 개만)
                        if len(urls) < 5:
                            reason = validation.get('reason', 'unknown')
                            print(f"    ⏭️ 제외됨 ({reason}): {url[:60]}...")
                        continue
                    
                    seen_urls.add(url)
                    urls.append({
                        'url': url,
                        'title': validation.get('title', ''),
                        'description': validation.get('description', ''),
                        'type': 'web'
                    })
                    print(f"    ✓ {url[:80]}...")
                
                time.sleep(0.5)  # 요청 간 대기 (속도 개선)
                
            except Exception as e:
                print(f"  ⚠️ 검색 오류: {e}")
                continue
        
        return urls
    
    def collect_urls(self, book_title: str, author: str = None, total_results: int = 30) -> Tuple[List[str], List[str]]:
        """한글/영어 자료 수집 (가능한 한 많이 수집, YouTube 50% 목표)"""
        # 최소 목표는 30개이지만, 더 많이 수집하도록 변경
        min_ko_count = total_results // 2
        min_en_count = total_results - min_ko_count
        
        # YouTube 목표: 전체의 50%
        youtube_target_ko = max(15, min_ko_count // 2)
        youtube_target_en = max(15, min_en_count // 2)
        
        print(f"🔍 '{book_title}' 관련 깊이 있는 자료 수집 중...")
        if author:
            print(f"   작가: {author}")
        print(f"   목표: 최소 한글 {min_ko_count}개 + 영어 {min_en_count}개 (가능한 한 많이 수집)")
        print(f"   YouTube 목표: 한글 {youtube_target_ko}개, 영어 {youtube_target_en}개 (30분 이상 영상)\n")
        
        # 한글 자료 수집
        print("=" * 60)
        print("📚 한글 자료 수집 중...")
        print("=" * 60)
        
        ko_urls = []
        seen_ko_urls = set()
        
        # YouTube 영상 (한글) - 50% 목표로 적극 수집
        print("  📺 YouTube 영상 검색 중 (30분 이상)...")
        try:
            youtube_ko = self.search_youtube_videos(book_title, author, max_results=youtube_target_ko * 2, lang='ko')
            youtube_count = 0
            for item in youtube_ko:
                if item['url'] not in seen_ko_urls:
                    seen_ko_urls.add(item['url'])
                    ko_urls.append(item['url'])
                    youtube_count += 1
                    if youtube_count >= youtube_target_ko:
                        break
            print(f"  ✅ YouTube 영상 {youtube_count}개 수집 완료")
        except Exception as e:
            print(f"  ⚠️ YouTube 검색 오류: {e}")
        
        # 웹 자료 (한글) - 나머지 50% 수집
        print("  🌐 웹 자료 검색 중...")
        web_ko = self.search_web_urls(book_title, author, max_results=50, lang='ko')
        web_count = 0
        for item in web_ko:
            if item['url'] not in seen_ko_urls:
                seen_ko_urls.add(item['url'])
                ko_urls.append(item['url'])
                web_count += 1
                # YouTube가 부족하면 웹 자료를 더 많이 수집
                if len(ko_urls) >= min_ko_count and web_count >= youtube_count:
                    break
        print(f"  ✅ 웹 자료 {web_count}개 수집 완료")
        
        # 최소 목표는 달성했는지 확인하고, 부족하면 추가 검색
        if len(ko_urls) < min_ko_count:
            print(f"  ⚠️ 한글 자료가 부족합니다 ({len(ko_urls)}/{min_ko_count}). 추가 검색 중...")
            additional_ko = self.search_web_urls(book_title, author, max_results=min_ko_count - len(ko_urls) + 10, lang='ko')
            for item in additional_ko:
                if item['url'] not in seen_ko_urls:
                    seen_ko_urls.add(item['url'])
                    ko_urls.append(item['url'])
        
        # 영어 자료 수집
        print("\n" + "=" * 60)
        print("📚 English Resources Collection...")
        print("=" * 60)
        
        en_urls = []
        seen_en_urls = set()
        
        # YouTube 영상 (영어) - 50% 목표로 적극 수집
        print("  📺 YouTube Videos Search (30+ minutes)...")
        try:
            youtube_en = self.search_youtube_videos(book_title, author, max_results=youtube_target_en * 2, lang='en')
            youtube_count = 0
            for item in youtube_en:
                if item['url'] not in seen_en_urls:
                    seen_en_urls.add(item['url'])
                    en_urls.append(item['url'])
                    youtube_count += 1
                    if youtube_count >= youtube_target_en:
                        break
            print(f"  ✅ YouTube Videos {youtube_count} collected")
        except Exception as e:
            print(f"  ⚠️ YouTube Search Error: {e}")
        
        # 웹 자료 (영어) - 나머지 50% 수집
        print("  🌐 Web Resources Search...")
        web_en = self.search_web_urls(book_title, author, max_results=50, lang='en')
        web_count = 0
        for item in web_en:
            if item['url'] not in seen_en_urls:
                seen_en_urls.add(item['url'])
                en_urls.append(item['url'])
                web_count += 1
                # YouTube가 부족하면 웹 자료를 더 많이 수집
                if len(en_urls) >= min_en_count and web_count >= youtube_count:
                    break
        print(f"  ✅ Web Resources {web_count} collected")
        
        # 최소 목표는 달성했는지 확인하고, 부족하면 추가 검색
        if len(en_urls) < min_en_count:
            print(f"  ⚠️ English resources insufficient ({len(en_urls)}/{min_en_count}). Additional search...")
            additional_en = self.search_web_urls(book_title, author, max_results=min_en_count - len(en_urls) + 10, lang='en')
            for item in additional_en:
                if item['url'] not in seen_en_urls:
                    seen_en_urls.add(item['url'])
                    en_urls.append(item['url'])
        
        print(f"\n✅ 수집 완료:")
        print(f"   한글: {len(ko_urls)}개")
        print(f"   영어: {len(en_urls)}개")
        print(f"   총계: {len(ko_urls) + len(en_urls)}개")
        if len(ko_urls) + len(en_urls) >= total_results:
            print(f"   ✅ 목표 달성! (목표: {total_results}개 이상)")
        print()
        
        return ko_urls, en_urls
    
    def save_urls(self, book_title: str, ko_urls: List[str], en_urls: List[str], author: str = None) -> str:
        """URL을 파일로 저장 (NotebookLM 형식)"""
        from utils.file_utils import safe_title
        
        safe_title_str = safe_title(book_title)
        output_dir = Path("assets/urls")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        md_path = output_dir / f"{safe_title_str}_notebooklm.md"
        
        total_urls = ko_urls + en_urls
        
        # 마크다운 파일 저장
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {book_title} - NotebookLM 소스 URL\n\n")
            if author:
                f.write(f"**작가**: {author}  \n")
            f.write(f"**총 {len(total_urls)}개의 URL (한글 {len(ko_urls)}개 + 영어 {len(en_urls)}개)**\n\n")
            
            f.write("## 📋 URL 리스트\n\n")
            f.write("아래 URL들을 복사하여 NotebookLM에 소스로 추가하세요.\n\n")
            
            # URL만 출력 (설명 없이)
            for url in total_urls:
                f.write(f"{url}\n")
        
        print(f"💾 URL 저장 완료: {md_path}")
        return str(md_path)


def load_books_from_csv(csv_path: str = "data/ildangbaek_books.csv") -> List[Tuple[str, str]]:
    """CSV에서 아직 처리하지 않은 책 목록 로드"""
    books = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('title', '').strip()
            author = row.get('author', '').strip()
            status = row.get('status', '').strip()
            
            # 아직 처리하지 않은 책만 (not_processed)
            if status == 'not_processed' and title:
                books.append((title, author))
    
    return books


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='깊이 있는 자료 URL 수집 (NotebookLM용)')
    parser.add_argument('--title', type=str, help='책 제목')
    parser.add_argument('--author', type=str, help='저자 이름')
    parser.add_argument('--csv', action='store_true', help='CSV에서 아직 처리하지 않은 책들 모두 처리')
    parser.add_argument('--num', type=int, default=30, help='총 수집할 URL 개수 (기본값: 30)')
    
    args = parser.parse_args()
    
    collector = DeepURLCollector()
    
    if args.csv:
        # CSV에서 책 목록 로드
        books = load_books_from_csv()
        
        if not books:
            print("📭 처리할 책이 없습니다.")
            return
        
        print(f"📚 총 {len(books)}개의 책을 처리합니다.\n")
        
        for i, (title, author) in enumerate(books, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(books)}] {title}" + (f" - {author}" if author else ""))
            print(f"{'='*80}\n")
            
            try:
                ko_urls, en_urls = collector.collect_urls(title, author, args.num)
                
                if ko_urls or en_urls:
                    collector.save_urls(title, ko_urls, en_urls, author)
                    print(f"✅ 완료: {title} (한글 {len(ko_urls)}개, 영어 {len(en_urls)}개)")
                else:
                    print(f"⚠️ URL 수집 실패: {title}")
                
                # 요청 간 대기
                if i < len(books):
                    print("\n⏳ 3초 대기 중...\n")
                    time.sleep(3)
                    
            except Exception as e:
                print(f"❌ 오류 발생: {title} - {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*80}")
        print("✅ 모든 책 처리 완료!")
        print(f"{'='*80}\n")
        
    elif args.title:
        # 단일 책 처리
        ko_urls, en_urls = collector.collect_urls(args.title, args.author, args.num)
        
        if ko_urls or en_urls:
            collector.save_urls(args.title, ko_urls, en_urls, args.author)
            print("\n✅ URL 수집 완료!")
        else:
            print("\n❌ 수집된 URL이 없습니다.")
    else:
        print("❌ --title 또는 --csv 옵션을 지정해주세요.")


if __name__ == "__main__":
    main()

