#!/usr/bin/env python3
"""
일당백 에피소드 제작 워크플로우 안내 CLI 프로그램

사용자가 일당백 에피소드를 쉽게 만들 수 있도록 단계별로 안내합니다.
"""

import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Tuple, List

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.file_utils import get_standard_safe_title
from src.utils.logger import setup_logger

# 로거 설정
logger = setup_logger(__name__)


def ask_yes_no(question: str, default: str = "n") -> bool:
    """
    사용자에게 yes/no 질문을 하고 답변을 받습니다.
    
    Args:
        question: 질문 내용
        default: 기본값 ('y' 또는 'n')
        
    Returns:
        True (yes) 또는 False (no)
    """
    default_prompt = "Y/n" if default.lower() == "y" else "y/N"
    while True:
        try:
            answer = input(f"{question} ({default_prompt}): ").strip().lower()
            if not answer:
                answer = default.lower()
            
            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            else:
                print("⚠️ 'y' 또는 'n'을 입력해주세요.")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            sys.exit(1)


def wait_for_enter(message: str):
    """
    사용자에게 Enter 키 입력을 대기합니다.
    
    Args:
        message: 표시할 메시지
    """
    try:
        input(f"\n{message}\n계속하려면 Enter를 누르세요...")
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 취소되었습니다.")
        sys.exit(1)


def run_subprocess(command: list, description: str) -> bool:
    """
    서브프로세스를 실행합니다.
    
    Args:
        command: 실행할 명령어 리스트
        description: 작업 설명
        
    Returns:
        성공 여부 (True/False)
    """
    logger.info(f"🔄 {description} 실행 중...")
    logger.info(f"   명령어: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=False,  # 실시간 출력을 위해 False
            text=True
        )
        logger.info(f"✅ {description} 완료")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {description} 실패: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"❌ 명령어를 찾을 수 없습니다: {command[0]}")
        return False


def step1_extract_subtitles():
    """Step 1: 자막 추출"""
    print("=" * 60)
    print("📝 Step 1: 자막 추출")
    print("=" * 60)
    print()
    
    need_extraction = ask_yes_no("새로운 자막 추출이 필요한가요?", default="n")
    
    if not need_extraction:
        print("✅ 자막 추출을 건너뜁니다.")
        return None
    
    # 책 제목 입력
    print()
    try:
        book_title = input("📖 책 제목을 입력하세요: ").strip()
        if not book_title:
            print("❌ 책 제목이 필요합니다.")
            return None
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 취소되었습니다.")
        sys.exit(1)
    
    # URL1 입력
    print()
    try:
        url1 = input("🔗 Part 1 유튜브 URL을 입력하세요: ").strip()
        if not url1:
            print("❌ Part 1 URL이 필요합니다.")
            return None
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 취소되었습니다.")
        sys.exit(1)
    
    # URL2 입력
    print()
    try:
        url2 = input("🔗 Part 2 유튜브 URL을 입력하세요: ").strip()
        if not url2:
            print("❌ Part 2 URL이 필요합니다.")
            return None
    except (EOFError, KeyboardInterrupt):
        print("\n❌ 취소되었습니다.")
        sys.exit(1)
    
    # 자막 추출 스크립트 실행
    print()
    script_path = project_root / "scripts" / "fetch_separate_scripts.py"
    command = [
        sys.executable,
        str(script_path),
        "--url1", url1,
        "--url2", url2,
        "--title", book_title
    ]
    
    success = run_subprocess(command, "자막 추출")
    
    if success:
        print()
        print("✅ 자막 추출이 완료되었습니다.")
        return book_title
    else:
        print()
        print("❌ 자막 추출에 실패했습니다.")
        return None


def find_and_normalize_files(input_dir: Path, language: str = "ko") -> Optional[dict]:
    """
    input 폴더에서 언어별 파일을 찾아서 정규화된 이름으로 매핑
    
    Args:
        input_dir: input 폴더 경로
        language: 언어 ('ko' 또는 'en')
        
    Returns:
        정규화된 파일 매핑 딕셔너리 또는 None
        {
            'part1_video': Path,
            'part1_info': Path,
            'part2_video': Path,
            'part2_info': Path
        }
    """
    if not input_dir.exists():
        return None
    
    # 언어 접미사 매핑
    lang_suffixes = {
        'ko': ['_ko', '_kr', '_korean', '_한글'],
        'en': ['_en', '_english', '_영어', '_영문']
    }
    
    suffixes = lang_suffixes.get(language, ['_ko'])
    
    # 언어별 mp4 파일 찾기
    mp4_files = []
    for suffix in suffixes:
        mp4_files.extend(list(input_dir.glob(f"*part*{suffix}*.mp4")))
        mp4_files.extend(list(input_dir.glob(f"*{suffix}*part*.mp4")))
    
    # 언어별 png 파일 찾기
    png_files = []
    for suffix in suffixes:
        png_files.extend(list(input_dir.glob(f"*part*{suffix}*.png")))
        png_files.extend(list(input_dir.glob(f"*{suffix}*part*.png")))
        png_files.extend(list(input_dir.glob(f"*info*{suffix}*.png")))
        png_files.extend(list(input_dir.glob(f"*{suffix}*info*.png")))
    
    # 중복 제거
    mp4_files = list(set(mp4_files))
    png_files = list(set(png_files))
    
    if len(mp4_files) < 2 or len(png_files) < 2:
        return None
    
    # Part 1/2 구분 (파일명에 '1', '2' 포함 여부로 판단)
    part1_video = None
    part2_video = None
    part1_info = None
    part2_info = None
    
    # 비디오 파일 분류 (우선순위: part1/part2 > 숫자 1/2 포함)
    for file in mp4_files:
        filename_lower = file.name.lower()
        # part1, part2가 명시적으로 있는 경우 우선
        if 'part1' in filename_lower or 'part_1' in filename_lower:
            if part1_video is None:
                part1_video = file
        elif 'part2' in filename_lower or 'part_2' in filename_lower:
            if part2_video is None:
                part2_video = file
        # 숫자로 구분 (단, 10, 11, 12 등은 제외)
        elif ('1' in filename_lower and '11' not in filename_lower and '12' not in filename_lower and 
              '10' not in filename_lower and '21' not in filename_lower):
            # '1'이 포함되어 있고 다른 숫자 조합이 아닌 경우
            if part1_video is None:
                part1_video = file
        elif '2' in filename_lower and '12' not in filename_lower and '22' not in filename_lower:
            if part2_video is None:
                part2_video = file
    
    # 명확하게 구분되지 않으면 첫 번째/두 번째로 할당
    if part1_video is None and len(mp4_files) >= 1:
        part1_video = mp4_files[0]
    if part2_video is None and len(mp4_files) >= 2:
        # part1_video가 아닌 다른 파일 찾기
        for file in mp4_files:
            if file != part1_video:
                part2_video = file
                break
    
    # 이미지 파일 분류 (우선순위: part1/part2 > info 포함 > 숫자 1/2)
    for file in png_files:
        filename_lower = file.name.lower()
        # part1, part2가 명시적으로 있는 경우 우선
        if 'part1' in filename_lower or 'part_1' in filename_lower:
            if part1_info is None:
                part1_info = file
        elif 'part2' in filename_lower or 'part_2' in filename_lower:
            if part2_info is None:
                part2_info = file
        # info와 숫자 조합
        elif 'info' in filename_lower:
            if ('1' in filename_lower and '11' not in filename_lower and '12' not in filename_lower and 
                '10' not in filename_lower):
                if part1_info is None:
                    part1_info = file
            elif ('2' in filename_lower and '12' not in filename_lower and '22' not in filename_lower):
                if part2_info is None:
                    part2_info = file
        # 숫자만으로 구분
        elif ('1' in filename_lower and '11' not in filename_lower and '12' not in filename_lower and 
              '10' not in filename_lower and '21' not in filename_lower):
            if part1_info is None:
                part1_info = file
        elif '2' in filename_lower and '12' not in filename_lower and '22' not in filename_lower:
            if part2_info is None:
                part2_info = file
    
    # 명확하게 구분되지 않으면 첫 번째/두 번째로 할당
    if part1_info is None and len(png_files) >= 1:
        part1_info = png_files[0]
    if part2_info is None and len(png_files) >= 2:
        # part1_info가 아닌 다른 파일 찾기
        for file in png_files:
            if file != part1_info:
                part2_info = file
                break
    
    # 모든 파일이 있는지 확인
    if part1_video and part1_info and part2_video and part2_info:
        return {
            'part1_video': part1_video,
            'part1_info': part1_info,
            'part2_video': part2_video,
            'part2_info': part2_info
        }
    
    return None


def auto_import_files(book_title: str, language: str = "ko") -> Tuple[bool, str]:
    """
    input 폴더에서 언어별 파일을 찾아서 assets/notebooklm/{책제목}/로 이동
    
    Args:
        book_title: 책 제목
        language: 언어 ('ko' 또는 'en')
        
    Returns:
        (성공 여부, 메시지)
    """
    safe_title = get_standard_safe_title(book_title)
    input_dir = Path("input")
    target_dir = Path("assets/notebooklm") / safe_title / language
    
    print()
    print("=" * 60)
    print(f"📁 Step 0: 파일 자동 정리 및 이동 ({language.upper()})")
    print("=" * 60)
    print()
    print(f"🔍 input 폴더 확인 중 ({language.upper()} 파일)...")
    
    # input 폴더에서 언어별 파일 찾기
    found_files = find_and_normalize_files(input_dir, language)
    
    if found_files:
        print()
        print("✅ input 폴더에서 4개 파일 발견:")
        for key, file_path in found_files.items():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   - {key}: {file_path.name} ({file_size:.2f}MB)")
        
        # 타겟 디렉토리 생성
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print()
        print(f"📦 파일 이동 중: input → {target_dir}")
        print()
        
        # 파일 이동 및 이름 정규화
        moved_files = {}
        for key, src_file in found_files.items():
            # 정규화된 파일명 생성 (언어 접미사 포함)
            lang_suffix = "_ko" if language == "ko" else "_en"
            if key == 'part1_video':
                dst_name = f"part1_video{lang_suffix}.mp4"
            elif key == 'part1_info':
                dst_name = f"part1_info{lang_suffix}.png"
            elif key == 'part2_video':
                dst_name = f"part2_video{lang_suffix}.mp4"
            elif key == 'part2_info':
                dst_name = f"part2_info{lang_suffix}.png"
            else:
                continue
            
            dst_file = target_dir / dst_name
            
            # 기존 파일이 있으면 백업
            if dst_file.exists():
                backup_name = dst_name + ".backup"
                backup_file = target_dir / backup_name
                shutil.copy2(dst_file, backup_file)
                logger.info(f"   📦 기존 파일 백업: {backup_name}")
            
            # 파일 이동
            try:
                shutil.move(str(src_file), str(dst_file))
                moved_files[key] = dst_file
                print(f"   ✅ {src_file.name} → {dst_name}")
            except Exception as e:
                logger.error(f"   ❌ 파일 이동 실패 ({src_file.name}): {e}")
                return False, f"파일 이동 실패: {e}"
        
        print()
        print(f"✅ 파일 이동 완료: input → assets/notebooklm/{safe_title}/{language}/")
        return True, "파일 이동 완료"
    
    # input 폴더에 파일이 없으면 기존 경로 확인
    print()
    print(f"⚠️ input 폴더에 {language.upper()} 파일이 없습니다.")
    print(f"🔍 기존 경로 확인 중: {target_dir}")
    
    lang_suffix = "_ko" if language == "ko" else "_en"
    required_files = {
        'part1_video': target_dir / f"part1_video{lang_suffix}.mp4",
        'part1_info': target_dir / f"part1_info{lang_suffix}.png",
        'part2_video': target_dir / f"part2_video{lang_suffix}.mp4",
        'part2_info': target_dir / f"part2_info{lang_suffix}.png"
    }
    
    existing_files = []
    missing_files = []
    
    for key, file_path in required_files.items():
        if file_path.exists():
            existing_files.append(key)
        else:
            missing_files.append(key)
    
    if not missing_files:
        print()
        print("✅ 기존 파일을 사용하여 작업을 진행합니다.")
        return True, "기존 파일 사용"
    else:
        print()
        print("❌ 필수 파일이 없습니다:")
        for key in missing_files:
            print(f"   - {required_files[key].name}")
        print()
        print(f"📁 다음 중 하나를 수행해주세요:")
        print(f"   1. input 폴더에 4개 파일을 넣고 다시 실행")
        print(f"   2. {target_dir} 폴더에 직접 파일을 준비")
        return False, "필수 파일 없음"


def step2_verify_files(book_title: str, language: str = "ko") -> bool:
    """Step 2: 파일 준비 확인"""
    safe_title = get_standard_safe_title(book_title)
    target_dir = Path("assets/notebooklm") / safe_title / language
    
    lang_suffix = "_ko" if language == "ko" else "_en"
    # 필수 파일 확인
    required_files = {
        "Part 1 인포그래픽": target_dir / f"part1_info{lang_suffix}.png",
        "Part 1 영상": target_dir / f"part1_video{lang_suffix}.mp4",
        "Part 2 인포그래픽": target_dir / f"part2_info{lang_suffix}.png",
        "Part 2 영상": target_dir / f"part2_video{lang_suffix}.mp4"
    }
    
    print()
    print("🔍 최종 파일 확인 중...")
    print()
    
    missing_files = []
    existing_files = []
    
    for name, file_path in required_files.items():
        if file_path.exists():
            file_size = file_path.stat().st_size / (1024 * 1024)  # MB
            print(f"   ✅ {name}: {file_path.name} ({file_size:.2f}MB)")
            existing_files.append((name, file_path))
        else:
            print(f"   ❌ {name}: {file_path.name} (없음)")
            missing_files.append((name, file_path))
    
    print()
    
    if missing_files:
        print("❌ 필수 파일이 없습니다:")
        for name, file_path in missing_files:
            print(f"   - {name}: {file_path}")
        print()
        return False
    
    print("✅ 모든 필수 파일이 준비되었습니다!")
    print()
    return True


def step3_create_episode(book_title: str, language: str = "ko", auto_mode: bool = False, infographic_duration: float = 30.0) -> bool:
    """Step 3: 영상 합성"""
    print()
    print("=" * 60)
    print("🎬 Step 3: 영상 합성")
    print("=" * 60)
    print()
    
    # 인포그래픽 표시 시간 설정
    if not auto_mode:
        print("⏱️ 인포그래픽 표시 시간 설정")
        try:
            duration_input = input("   인포그래픽 표시 시간(초, 기본값: 30): ").strip()
            if duration_input:
                infographic_duration = float(duration_input)
            else:
                infographic_duration = 30.0
        except ValueError:
            print("   ⚠️ 잘못된 입력, 기본값 30초 사용")
            infographic_duration = 30.0
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            sys.exit(1)
        print()
    else:
        print(f"⏱️ 인포그래픽 표시 시간: {infographic_duration}초 (자동 모드)")
        print()
    
    # 배경음악 설정
    print("🎵 배경음악 설정 (선택사항)")
    
    bgm_path = None
    bgm_volume = 0.3
    
    if auto_mode:
        # 자동 모드: 먼저 자동 다운로드 시도
        print()
        print("   🔍 배경음악 자동 다운로드 시도 중...")
        script_path = project_root / "src" / "21_download_background_music.py"
        command = [
            sys.executable,
            str(script_path),
            "--title", book_title
        ]
        
        success = run_subprocess(command, "배경음악 다운로드")
        
        if success:
            # 다운로드된 파일 찾기
            safe_title = get_standard_safe_title(book_title)
            music_dir = Path("assets/music")
            downloaded_music = music_dir / f"{safe_title}_background.mp3"
            
            if downloaded_music.exists():
                bgm_path = str(downloaded_music)
                print(f"   ✅ 자동 다운로드 완료: {downloaded_music.name}")
            else:
                print("   ⚠️ 자동 다운로드 실패, 기존 파일 검색 중...")
        else:
            print("   ⚠️ 자동 다운로드 실패, 기존 파일 검색 중...")
        
        # 자동 다운로드 실패하거나 파일이 없으면 기존 파일 검색
        if not bgm_path:
            input_dir = Path("input")
            bgm_files = []
            if input_dir.exists():
                bgm_patterns = [
                    "background*.mp3", "background*.wav", "background*.m4a",
                    "bgm*.mp3", "bgm*.wav", "bgm*.m4a",
                    "music*.mp3", "music*.wav", "music*.m4a"
                ]
                for pattern in bgm_patterns:
                    bgm_files.extend(list(input_dir.glob(pattern)))
                bgm_files = list(set(bgm_files))
            
            music_dir = Path("assets/music")
            if music_dir.exists():
                bgm_files.extend(list(music_dir.glob("*.mp3")))
                bgm_files.extend(list(music_dir.glob("*.wav")))
                bgm_files.extend(list(music_dir.glob("*.m4a")))
            
            bgm_files = list(set(bgm_files))
            
            if bgm_files:
                if len(bgm_files) == 1:
                    bgm_path = str(bgm_files[0])
                    print(f"   ✅ 배경음악 자동 선택: {bgm_files[0].name}")
                else:
                    # 첫 번째 파일 자동 선택
                    bgm_path = str(bgm_files[0])
                    print(f"   ✅ 배경음악 자동 선택: {bgm_files[0].name} (첫 번째 파일)")
            else:
                print("   ℹ️ 배경음악 파일이 없습니다. (건너뜀)")
    else:
        # 대화형 모드
        # 자동 다운로드 시도
        auto_download = ask_yes_no("   책 분위기에 맞는 배경음악을 자동으로 다운로드하시겠습니까?", default="n")
        
        if auto_download:
            print()
            print("   🔍 배경음악 자동 다운로드 중...")
            script_path = project_root / "src" / "21_download_background_music.py"
            command = [
                sys.executable,
                str(script_path),
                "--title", book_title
            ]
            
            success = run_subprocess(command, "배경음악 다운로드")
            
            if success:
                # 다운로드된 파일 찾기
                safe_title = get_standard_safe_title(book_title)
                music_dir = Path("assets/music")
                downloaded_music = music_dir / f"{safe_title}_background.mp3"
                
                if downloaded_music.exists():
                    bgm_path = str(downloaded_music)
                    print(f"   ✅ 자동 다운로드 완료: {downloaded_music.name}")
                else:
                    print("   ⚠️ 자동 다운로드 실패, 수동으로 선택하세요.")
            else:
                print("   ⚠️ 자동 다운로드 실패, 수동으로 선택하세요.")
            print()
        
        # 자동 다운로드 실패하거나 건너뛴 경우
        if not bgm_path:
            # input 폴더에서 배경음악 파일 자동 찾기
            input_dir = Path("input")
            bgm_files = []
            if input_dir.exists():
                # 일반적인 배경음악 파일명 패턴
                bgm_patterns = [
                    "background*.mp3", "background*.wav", "background*.m4a",
                    "bgm*.mp3", "bgm*.wav", "bgm*.m4a",
                    "music*.mp3", "music*.wav", "music*.m4a"
                ]
                for pattern in bgm_patterns:
                    bgm_files.extend(list(input_dir.glob(pattern)))
                bgm_files = list(set(bgm_files))
            
            # assets/music 폴더도 확인
            music_dir = Path("assets/music")
            if music_dir.exists():
                bgm_files.extend(list(music_dir.glob("*.mp3")))
                bgm_files.extend(list(music_dir.glob("*.wav")))
                bgm_files.extend(list(music_dir.glob("*.m4a")))
            
            bgm_files = list(set(bgm_files))
            
            if bgm_files:
                print(f"   ✅ 배경음악 파일 발견: {len(bgm_files)}개")
                for i, bgm_file in enumerate(bgm_files, 1):
                    file_size = bgm_file.stat().st_size / (1024 * 1024)  # MB
                    print(f"      [{i}] {bgm_file.name} ({file_size:.2f}MB)")
                
                if len(bgm_files) == 1:
                    # 파일이 하나면 자동 선택
                    bgm_path = str(bgm_files[0])
                    print(f"   ✅ 자동 선택: {bgm_files[0].name}")
                else:
                    # 여러 개면 선택
                    try:
                        choice = input(f"   사용할 배경음악 번호 선택 (1-{len(bgm_files)}, Enter로 건너뛰기): ").strip()
                        if choice:
                            idx = int(choice) - 1
                            if 0 <= idx < len(bgm_files):
                                bgm_path = str(bgm_files[idx])
                                print(f"   ✅ 선택됨: {bgm_files[idx].name}")
                    except (ValueError, IndexError):
                        print("   ⚠️ 잘못된 선택, 배경음악 건너뜀")
                    except (EOFError, KeyboardInterrupt):
                        print("\n❌ 취소되었습니다.")
                        sys.exit(1)
            else:
                # 파일이 없으면 수동 입력
                try:
                    bgm_input = input("   배경음악 파일 경로 (Enter로 건너뛰기): ").strip()
                    if bgm_input:
                        bgm_path = bgm_input
                except (EOFError, KeyboardInterrupt):
                    print("\n❌ 취소되었습니다.")
                    sys.exit(1)
    
    # 음량 설정 (배경음악이 선택된 경우만)
    if bgm_path and not auto_mode:
        try:
            volume_input = input("   배경음악 음량 (0.0 ~ 1.0, 기본값: 0.3): ").strip()
            if volume_input:
                bgm_volume = float(volume_input)
                bgm_volume = max(0.0, min(1.0, bgm_volume))  # 0.0 ~ 1.0 범위로 제한
            else:
                bgm_volume = 0.3
        except ValueError:
            print("   ⚠️ 잘못된 입력, 기본값 0.3 사용")
            bgm_volume = 0.3
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            sys.exit(1)
    elif bgm_path and auto_mode:
        print(f"   🔊 배경음악 음량: {bgm_volume} (자동 모드)")
    
    print()
    
    script_path = project_root / "src" / "create_full_episode.py"
    command = [
        sys.executable,
        str(script_path),
        "--title", book_title,
        "--language", language,
        "--infographic-duration", str(infographic_duration)
    ]
    
    if bgm_path:
        command.extend(["--background-music", bgm_path])
        command.extend(["--bgm-volume", str(bgm_volume)])
    
    success = run_subprocess(command, "영상 합성")
    
    if success:
        print()
        print("✅ 영상 합성이 완료되었습니다!")
        return True
    else:
        print()
        print("❌ 영상 합성에 실패했습니다.")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='일당백 에피소드 제작 워크플로우',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='책 제목 (인자로 제공하지 않으면 대화형으로 입력받음)'
    )
    
    parser.add_argument(
        '--language',
        type=str,
        default='ko',
        choices=['ko', 'en'],
        help='언어 (기본값: ko)'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='자동 모드 (모든 질문에 기본값 사용)'
    )
    
    parser.add_argument(
        '--infographic-duration',
        type=float,
        default=30.0,
        help='인포그래픽 표시 시간 (초, 기본값: 30.0)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 일당백 에피소드 제작 워크플로우")
    print("=" * 60)
    print()
    
    # 책 제목 입력 (인자 또는 대화형)
    if args.title:
        book_title = args.title.strip()
        print(f"📖 책 제목: {book_title}")
    else:
        try:
            book_title = input("📖 작업할 책 제목(영문)을 입력하세요: ").strip()
            if not book_title:
                print("❌ 책 제목이 필요합니다.")
                sys.exit(1)
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            sys.exit(1)
    
    print()
    
    # 언어 선택
    if args.auto:
        selected_language = args.language
        print(f"🌐 언어: {selected_language.upper()} (자동 모드)")
    else:
        print()
        print("🌐 언어 선택")
        try:
            lang_input = input("   한글(ko) 또는 영문(en)을 선택하세요 (기본값: ko): ").strip().lower()
            if lang_input in ['ko', 'en']:
                selected_language = lang_input
            else:
                selected_language = args.language
            print(f"   ✅ 선택된 언어: {selected_language.upper()}")
        except (EOFError, KeyboardInterrupt):
            print("\n❌ 취소되었습니다.")
            sys.exit(1)
    
    print()
    
    # Step 0: 파일 자동 정리 및 이동
    success, message = auto_import_files(book_title, selected_language)
    if not success:
        print()
        print(f"❌ {message}")
        sys.exit(1)
    
    # 썸네일 처리 (선택사항)
    print()
    print("🖼️ 썸네일 처리 (선택사항)")
    input_dir = Path("input")
    safe_title = get_standard_safe_title(book_title)
    output_dir = Path("output")
    
    # 썸네일 파일 찾기
    thumbnail_files = []
    lang_suffixes = {
        'ko': ['_ko', '_kr', '_korean', '_한글'],
        'en': ['_en', '_english', '_영어', '_영문']
    }
    suffixes = lang_suffixes.get(selected_language, ['_ko'])
    
    for suffix in suffixes:
        thumbnail_files.extend(list(input_dir.glob(f"*thumbnail*{suffix}*.png")))
        thumbnail_files.extend(list(input_dir.glob(f"*{suffix}*thumbnail*.png")))
        thumbnail_files.extend(list(input_dir.glob(f"thumbnail{suffix}.png")))
    
    thumbnail_files = list(set(thumbnail_files))
    
    if thumbnail_files:
        print(f"   ✅ 썸네일 파일 발견: {len(thumbnail_files)}개")
        for thumb_file in thumbnail_files:
            lang_suffix = "_ko" if selected_language == "ko" else "_en"
            output_thumb = output_dir / f"{safe_title}_thumbnail{lang_suffix}.jpg"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                from PIL import Image
                # PNG를 JPG로 변환
                img = Image.open(thumb_file)
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(output_thumb, 'JPEG', quality=95, optimize=True)
                print(f"   ✅ 썸네일 변환 완료: {output_thumb.name}")
            except Exception as e:
                logger.warning(f"   ⚠️ 썸네일 변환 실패: {e}")
    else:
        print("   ℹ️ 썸네일 파일이 없습니다. (건너뜀)")
    
    # Step 1: 자막 추출 (선택사항)
    if not args.auto:
        need_subtitles = ask_yes_no("\n새로운 자막 추출이 필요한가요?", default="n")
        if need_subtitles:
            step1_extract_subtitles()
    else:
        print("\n📝 자막 추출: 건너뜀 (자동 모드)")
    
    # Step 2: 파일 준비 확인
    if not step2_verify_files(book_title, selected_language):
        print()
        print("❌ 파일 준비가 완료되지 않았습니다.")
        print("필요한 파일을 준비한 후 다시 실행해주세요.")
        sys.exit(1)
    
    # Step 3: 영상 합성
    if not step3_create_episode(book_title, selected_language, args.auto, args.infographic_duration):
        print()
        print("❌ 영상 합성에 실패했습니다.")
        sys.exit(1)
    
    # Step 4: 메타데이터 생성
    print()
    print("=" * 60)
    print("📋 Step 4: 메타데이터 생성")
    print("=" * 60)
    print()
    
    if args.auto:
        create_metadata = True
        print("📋 메타데이터 생성: 자동 생성 (자동 모드)")
    else:
        create_metadata = ask_yes_no("메타데이터를 생성하시겠습니까?", default="y")
    
    if create_metadata:
        script_path = project_root / "src" / "20_create_episode_metadata.py"
        command = [
            sys.executable,
            str(script_path),
            "--title", book_title,
            "--language", selected_language
        ]
        
        success = run_subprocess(command, "메타데이터 생성")
        
        if success:
            print()
            print("✅ 메타데이터 생성이 완료되었습니다!")
        else:
            print()
            print("❌ 메타데이터 생성에 실패했습니다.")
    
    # 다른 언어도 생성할지 확인
    if not args.auto:
        other_language = 'en' if selected_language == 'ko' else 'ko'
        create_other = ask_yes_no(f"\n{other_language.upper()} 버전도 생성하시겠습니까?", default="n")
        
        if create_other:
            print()
            print(f"🌐 {other_language.upper()} 버전 생성 시작")
            print()
            
            # 다른 언어 파일 정리 및 이동
            success, message = auto_import_files(book_title, other_language)
            if success:
                # 파일 준비 확인
                if step2_verify_files(book_title, other_language):
                    # 영상 합성
                    step3_create_episode(book_title, other_language, args.auto, args.infographic_duration)
    
    # 완료
    print()
    print("=" * 60)
    print("🎉 전체 워크플로우 완료!")
    print("=" * 60)
    print()
    
    safe_title = get_standard_safe_title(book_title)
    lang_suffix = "_ko" if selected_language == "ko" else "_en"
    output_path = Path("output") / f"{safe_title}_full_episode{lang_suffix}.mp4"
    
    if output_path.exists():
        file_size = output_path.stat().st_size / (1024 * 1024)  # MB
        print(f"📁 생성된 영상: {output_path}")
        print(f"📊 파일 크기: {file_size:.2f}MB")
    else:
        print(f"⚠️ 출력 파일을 찾을 수 없습니다: {output_path}")
    
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 취소되었습니다.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

