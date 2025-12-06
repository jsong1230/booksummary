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
        "작별인사": "Farewell",
        "Farewell": "Farewell",  # 영어 제목은 그대로 반환
        "호밀밭의 파수꾼": "The Catcher in the Rye",
        "The Catcher in the Rye": "The Catcher in the Rye",
        "벅아이": "Buckeye",
        "동물농장": "Animal Farm",
        "햄릿": "Hamlet",
        "선라이즈 온 더 리핑": "Sunrise on the Reaping",
        "헝거 게임: 선라이즈 온 더 리핑": "Sunrise on the Reaping",
        "불안 세대": "The Anxious Generation",
        "불안_세대": "The Anxious Generation",
        "소니아와 써니의 고독": "The Loneliness of Sonia and Sunny",
        "The Loneliness of Sonia and Sunny": "The Loneliness of Sonia and Sunny",
        "The Loneliness of Sonia and Sunny (소니아와 써니의 고독)": "The Loneliness of Sonia and Sunny",
        "연금술사": "The Alchemist",
        "The Alchemist": "The Alchemist",
        "죽음의 수용소에서": "Man's Search for Meaning",
        "죽음의_수용소에서": "Man's Search for Meaning",
        "Man's Search for Meaning": "Man's Search for Meaning",
        "듀얼 브레인": "Co-Intelligence",
        "듀얼_브레인": "Co-Intelligence",
        "Co-Intelligence": "Co-Intelligence",
        "아토믹 해빗": "Atomic Habits",
        "아토믹_해빗": "Atomic Habits",
        "Atomic Habits": "Atomic Habits",
        "스티브 잡스": "Steve Jobs",
        "스티브_잡스": "Steve Jobs",
        "Steve Jobs": "Steve Jobs",
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
        "The Boy is Coming": "소년이 온다",
        "Farewell": "작별인사",
        "The Catcher in the Rye": "호밀밭의 파수꾼",
        "Buckeye": "벅아이",
        "Animal Farm": "동물농장",
        "Hamlet": "햄릿",
        "Sunrise on the Reaping": "선라이즈 온 더 리핑",
        "The Anxious Generation": "불안 세대",
        "The Loneliness of Sonia and Sunny": "소니아와 써니의 고독",
        "Sátántangó": "사탄탱고",
        "Sátántangó (사탄탱고)": "사탄탱고",
        "The Alchemist": "연금술사",
        "Co-Intelligence": "듀얼 브레인",
        "Man's Search for Meaning": "죽음의 수용소에서",
        "Atomic Habits": "아토믹 해빗",
        "Steve Jobs": "스티브 잡스",
    }
    
    # 공백을 언더스코어로 변환한 버전도 확인
    book_title_underscore = book_title.replace(' ', '_')
    if book_title_underscore in reverse_title_map:
        return reverse_title_map[book_title_underscore]
    
    # 매핑이 없으면 원본 반환 (이미 한글일 수도 있음)
    result = reverse_title_map.get(book_title, book_title)
    
    # 결과가 여전히 영어인 경우 (한글이 없음), 한글 발음으로 변환 시도
    if is_english_title(result):
        # 간단한 발음 변환 (추후 개선 가능)
        # 예: "Buckeye" -> "벅아이" 같은 매핑이 없으면 원본 반환
        # 여기서는 매핑에 없으면 원본을 반환하되, generate_title에서 처리
        pass
    
    return result


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
        "파울로 코엘료": "Paulo Coelho",
        "Paulo Coelho": "Paulo Coelho",
        "김영하": "Youngha Kim",
        "Youngha Kim": "Youngha Kim",  # 영어 이름은 그대로 반환
        "J.D. Salinger": "J.D. Salinger",
        "제롬 데이비드 샐린저": "J.D. Salinger",
        "샐린저": "J.D. Salinger",
        "빅터 프랭클": "Viktor Frankl",
        "Viktor Frankl": "Viktor Frankl",
        "빅터 E. 프랭클": "Viktor E. Frankl",
        "Viktor E. Frankl": "Viktor E. Frankl",
        "이선 몰릭": "Ethan Mollick",
        "Ethan Mollick": "Ethan Mollick",
        "제임스 클리어": "James Clear",
        "James Clear": "James Clear",
        "월터 아이작슨": "Walter Isaacson",
        "Walter Isaacson": "Walter Isaacson",
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
        "Ethan Mollick": "이선 몰릭",
        "Viktor Frankl": "빅터 프랭클",
        "James Clear": "제임스 클리어",
        "Walter Isaacson": "월터 아이작슨",
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

