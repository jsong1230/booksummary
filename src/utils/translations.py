"""
번역 관련 유틸리티 함수
"""


def translate_book_title(book_title: str) -> str:
    """책 제목을 영어로 변환"""
    # 알려진 책 제목 매핑
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
    }
    
    # 공백을 언더스코어로 변환한 버전도 확인
    book_title_underscore = book_title.replace(' ', '_')
    if book_title_underscore in title_map:
        return title_map[book_title_underscore]
    
    return title_map.get(book_title, book_title)


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
    }
    
    if author in author_map:
        return author_map[author]
    
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

