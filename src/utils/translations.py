"""
번역 관련 유틸리티 함수
"""


def translate_book_title(book_title: str) -> str:
    """책 제목을 영어로 변환"""
    # 알려진 책 제목 매핑 (한글 -> 영어)
    title_map = {
        "노르웨이의 숲": "Norwegian Wood",
        "노르웨이의_숲": "Norwegian Wood",
        "1984": "1984",
        "사피엔스": "Sapiens",
        "21세기를 위한 21가지 제언": "21 Lessons for the 21st Century",
        "호모 데우스": "Homo Deus",
        "데미안": "Demian",
        "군주론": "The Prince",
        "그리스인 조르바": "Zorba the Greek",
        "조르바": "Zorba the Greek",
        "죄와 벌": "Crime and Punishment",
        "죄와벌": "Crime and Punishment",
        "소년이 온다": "Human Acts",
        "Human Acts": "Human Acts",  # 영어 제목은 그대로 반환
        "The Boy is Coming": "Human Acts",  # 구버전 호환성
        "삼국지": "Three Kingdoms",
        "삼국지 연의": "Romance of the Three Kingdoms",
        "삼국지연의": "Romance of the Three Kingdoms",
        "작별인사": "Farewell",
    }
    
    # 공백을 언더스코어로 변환한 버전도 확인
    book_title_underscore = book_title.replace(' ', '_')
    if book_title_underscore in title_map:
        return title_map[book_title_underscore]
    
    return title_map.get(book_title, book_title)


def translate_book_title_to_korean(book_title: str) -> str:
    """책 제목을 한글로 변환 (역방향)"""
    # 영어 -> 한글 매핑
    reverse_title_map = {
        "Norwegian Wood": "노르웨이의 숲",
        "1984": "1984",
        "Sapiens": "사피엔스",
        "21 Lessons for the 21st Century": "21세기를 위한 21가지 제언",
        "Homo Deus": "호모 데우스",
        "Demian": "데미안",
        "The Prince": "군주론",
        "Zorba the Greek": "그리스인 조르바",
        "Crime and Punishment": "죄와 벌",
        "Human Acts": "소년이 온다",
        "The Boy is Coming": "소년이 온다",  # 구버전 호환성
        "Three Kingdoms": "삼국지",
        "Romance of the Three Kingdoms": "삼국지 연의",
        "Farewell": "작별인사",
    }
    
    # 공백을 언더스코어로 변환한 버전도 확인
    book_title_underscore = book_title.replace(' ', '_')
    if book_title_underscore in reverse_title_map:
        return reverse_title_map[book_title_underscore]
    
    return reverse_title_map.get(book_title, book_title)


def is_english_title(book_title: str) -> bool:
    """제목이 영어인지 판단 (한글이 포함되어 있지 않으면 영어로 간주)"""
    # 한글이 포함되어 있으면 한글 제목
    for char in book_title:
        if '\uAC00' <= char <= '\uD7A3':  # 한글 유니코드 범위
            return False
    # 한글이 없고 알파벳/숫자/공백/특수문자만 있으면 영어로 간주
    return True


def translate_author_name(author: str) -> str:
    """작가 이름을 영어로 변환"""
    author_map = {
        "무라카미 하루키": "Murakami Haruki",
        "하루키": "Haruki",
        "유발 하라리": "Yuval Noah Harari",
        "조지 오웰": "George Orwell",
        "어니스트 헤밍웨이": "Ernest Hemingway",
        "윌리엄 셰익스피어": "William Shakespeare",
        "도스토옙스키": "Fyodor Dostoevsky",
        "헤르만 헤세": "Hermann Hesse",
        "헤세": "Hermann Hesse",
        "마키아벨리": "Niccolò Machiavelli",
        "니콜로 마키아벨리": "Niccolò Machiavelli",
        "니코스 카잔차키스": "Nikos Kazantzakis",
        "카잔차키스": "Nikos Kazantzakis",
        "도스토옙스키": "Fyodor Dostoevsky",
        "표도르 도스토옙스키": "Fyodor Dostoevsky",
        "한강": "Han Kang",
        "한강 작가": "Han Kang",
        "나관중": "Luo Guanzhong",
        "나관중 작가": "Luo Guanzhong",
        "김영하": "Kim Young-ha",
        "김영하 작가": "Kim Young-ha",
    }
    
    if author in author_map:
        return author_map[author]
    
    return author


def translate_author_name_to_korean(author: str) -> str:
    """작가 이름을 한글로 변환 (역방향)"""
    # 영어 -> 한글 매핑
    reverse_author_map = {
        "Murakami Haruki": "무라카미 하루키",
        "Haruki": "하루키",
        "Yuval Noah Harari": "유발 하라리",
        "George Orwell": "조지 오웰",
        "Ernest Hemingway": "어니스트 헤밍웨이",
        "William Shakespeare": "윌리엄 셰익스피어",
        "Fyodor Dostoevsky": "표도르 도스토옙스키",
        "Hermann Hesse": "헤르만 헤세",
        "Niccolò Machiavelli": "니콜로 마키아벨리",
        "Nikos Kazantzakis": "니코스 카잔차키스",
        "Han Kang": "한강",
        "Luo Guanzhong": "나관중",
        "Kim Young-ha": "김영하",
    }
    
    if author in reverse_author_map:
        return reverse_author_map[author]
    
    return author


def get_book_alternative_title(book_title: str) -> dict:
    """책의 대체 제목 반환 (한글/영문)"""
    # 알려진 책의 대체 제목
    alt_titles = {
        "노르웨이의 숲": {
            "ko": "상실의 시대",
            "en": "The Age of Loss"
        },
        "노르웨이의_숲": {
            "ko": "상실의 시대",
            "en": "The Age of Loss"
        }
    }
    
    return alt_titles.get(book_title, {})

