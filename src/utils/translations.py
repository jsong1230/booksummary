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
        "어린왕자": "The Little Prince",
        "어린_왕자": "The Little Prince",
        "The Little Prince": "The Little Prince",
        "내 이름은 빨강": "My Name is Red",
        "내_이름은_빨강": "My Name is Red",
        "My Name is Red": "My Name is Red",
        "돈의 심리학": "The Psychology of Money",
        "돈의_심리학": "The Psychology of Money",
        "The Psychology of Money": "The Psychology of Money",
        "작은 아씨들": "Little Women",
        "작은_아씨들": "Little Women",
        "Little Women": "Little Women",
        "인간관계론": "How to Win Friends and Influence People",
        "인간_관계론": "How to Win Friends and Influence People",
        "How to Win Friends and Influence People": "How to Win Friends and Influence People",
        "사기": "Records of the Grand Historian",
        "사기(史記)": "Records of the Grand Historian",
        "Records of the Grand Historian": "Records of the Grand Historian",
        "Shiji": "Records of the Grand Historian",
        "신경 끄기의 기술": "The Subtle Art of Not Giving a F*ck",
        "신경_끄기의_기술": "The Subtle Art of Not Giving a F*ck",
        "The Subtle Art of Not Giving a F*ck": "The Subtle Art of Not Giving a F*ck",
        "The Subtle Art of Not Giving a Fuck": "The Subtle Art of Not Giving a F*ck",
        "부에 대한 연감": "The Almanack of Naval Ravikant",
        "부에_대한_연감": "The Almanack of Naval Ravikant",
        "네이벌 라비칸트 연감": "The Almanack of Naval Ravikant",
        "네이벌_라비칸트_연감": "The Almanack of Naval Ravikant",
        "The Almanack of Naval Ravikant": "The Almanack of Naval Ravikant",
        "부의 추월차선": "The Millionaire Fastlane",
        "부의_추월차선": "The Millionaire Fastlane",
        "The Millionaire Fastlane": "The Millionaire Fastlane",
        "나는 오늘도 경제적 자유를 꿈꾼다": "I Will Teach You to Be Rich",
        "나는_오늘도_경제적_자유를_꿈꾼다": "I Will Teach You to Be Rich",
        "I Will Teach You to Be Rich": "I Will Teach You to Be Rich",
        "일론 머스크": "Elon Musk",
        "일론_머스크": "Elon Musk",
        "Elon Musk": "Elon Musk",
        "남아 있는 나날": "The Remains of the Day",
        "남아_있는_나날": "The Remains of the Day",
        "남아있는 나날": "The Remains of the Day",
        "남아있는_나날": "The Remains of the Day",
        "The Remains of the Day": "The Remains of the Day",
        "인간의 위대한 여정": "The Life Cycle Completed",
        "인간의_위대한_여정": "The Life Cycle Completed",
        "The Life Cycle Completed": "The Life Cycle Completed",
        "오베라는 남자": "A Man Called Ove",
        "오베라는_남자": "A Man Called Ove",
        "A Man Called Ove": "A Man Called Ove",
        "크리스마스 선물": "The Gift of the Magi",
        "크리스마스_선물": "The Gift of the Magi",
        "The Gift of the Magi": "The Gift of the Magi",
        "호두까기 인형": "The Nutcracker",
        "호두까기_인형": "The Nutcracker",
        "The Nutcracker": "The Nutcracker",
        "스노우맨": "The Snowman",
        "스노우_맨": "The Snowman",
        "The Snowman": "The Snowman",
        "에센셜리즘": "Essentialism",
        "에센셜_리즘": "Essentialism",
        "Essentialism": "Essentialism",
        "팩트풀니스": "Factfulness",
        "팩트_풀니스": "Factfulness",
        "Factfulness": "Factfulness",
        "21세기 자본": "Capital in the Twenty-First Century",
        "21세기_자본": "Capital in the Twenty-First Century",
        "Capital in the Twenty-First Century": "Capital in the Twenty-First Century",
        "유전자": "The Gene",
        "유전자_": "The Gene",
        "The Gene": "The Gene",
        "은하수를 여행하는 히치하이커를 위한 안내서": "Hitchhiker's Guide to the Galaxy",
        "은하수를_여행하는_히치하이커를_위한_안내서": "Hitchhiker's Guide to the Galaxy",
        "Hitchhiker's Guide to the Galaxy": "Hitchhiker's Guide to the Galaxy",
        "The Hitchhiker's Guide to the Galaxy": "Hitchhiker's Guide to the Galaxy",
        "괴델, 에셔, 바흐": "Gödel, Escher, Bach: An Eternal Golden Braid",
        "괴델_에셔_바흐": "Gödel, Escher, Bach: An Eternal Golden Braid",
        "Gödel, Escher, Bach: An Eternal Golden Braid": "Gödel, Escher, Bach: An Eternal Golden Braid",
        "Gödel Escher Bach": "Gödel, Escher, Bach: An Eternal Golden Braid",
        "여섯 번째 대멸종": "The Sixth Extinction",
        "여섯_번째_대멸종": "The Sixth Extinction",
        "6번째 대멸종": "The Sixth Extinction",
        "6번째_대멸종": "The Sixth Extinction",
        "The Sixth Extinction": "The Sixth Extinction",
        "현명한 투자자": "The Intelligent Investor",
        "현명한_투자자": "The Intelligent Investor",
        "The Intelligent Investor": "The Intelligent Investor",
        "부자 아빠 가난한 아빠": "Rich Dad Poor Dad",
        "부자_아빠_가난한_아빠": "Rich Dad Poor Dad",
        "Rich Dad Poor Dad": "Rich Dad Poor Dad",
        "딥 워크": "Deep Work",
        "딥_워크": "Deep Work",
        "Deep Work": "Deep Work",
        "생각에 관한 생각": "Thinking, Fast and Slow",
        "생각에_관한_생각": "Thinking, Fast and Slow",
        "Thinking, Fast and Slow": "Thinking, Fast and Slow",
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
        "The Little Prince": "어린왕자",
        "My Name is Red": "내 이름은 빨강",
        "The Psychology of Money": "돈의 심리학",
        "Little Women": "작은 아씨들",
        "How to Win Friends and Influence People": "인간관계론",
        "Records of the Grand Historian": "사기",
        "Shiji": "사기",
        "The Subtle Art of Not Giving a F*ck": "신경 끄기의 기술",
        "The Subtle Art of Not Giving a Fuck": "신경 끄기의 기술",
        "The Almanack of Naval Ravikant": "네이벌 라비칸트 연감",
        "The Millionaire Fastlane": "부의 추월차선",
        "I Will Teach You to Be Rich": "나는 오늘도 경제적 자유를 꿈꾼다",
        "Elon Musk": "일론 머스크",
        "The Remains of the Day": "남아 있는 나날",
        "The Life Cycle Completed": "인간의 위대한 여정",
        "A Man Called Ove": "오베라는 남자",
        "The Gift of the Magi": "크리스마스 선물",
        "The Nutcracker": "호두까기 인형",
        "The Snowman": "스노우맨",
        "Essentialism": "에센셜리즘",
        "Factfulness": "팩트풀니스",
        "Capital in the Twenty-First Century": "21세기 자본",
        "The Gene": "유전자",
        "Hitchhiker's Guide to the Galaxy": "은하수를 여행하는 히치하이커를 위한 안내서",
        "The Hitchhiker's Guide to the Galaxy": "은하수를 여행하는 히치하이커를 위한 안내서",
        "Gödel, Escher, Bach: An Eternal Golden Braid": "괴델, 에셔, 바흐",
        "Gödel Escher Bach": "괴델, 에셔, 바흐",
        "The Sixth Extinction": "여섯 번째 대멸종",
        "The Intelligent Investor": "현명한 투자자",
        "Rich Dad Poor Dad": "부자 아빠 가난한 아빠",
        "Deep Work": "딥 워크",
        "Thinking, Fast and Slow": "생각에 관한 생각",
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
        "생텍쥐페리": "Antoine de Saint-Exupéry",
        "앙투안 드 생텍쥐페리": "Antoine de Saint-Exupéry",
        "Antoine de Saint-Exupéry": "Antoine de Saint-Exupéry",
        "우르한 파묵": "Orhan Pamuk",
        "Orhan Pamuk": "Orhan Pamuk",
        "모건 하우설": "Morgan Housel",
        "Morgan Housel": "Morgan Housel",
        "루이자 메이 올콧": "Louisa May Alcott",
        "Louisa May Alcott": "Louisa May Alcott",
        "데일 카네기": "Dale Carnegie",
        "Dale Carnegie": "Dale Carnegie",
        "사마천": "Sima Qian",
        "Sima Qian": "Sima Qian",
        "마크 맨슨": "Mark Manson",
        "Mark Manson": "Mark Manson",
        "나발 라비칸트": "Naval Ravikant",
        "Naval Ravikant": "Naval Ravikant",
        "엠제이 드마코": "MJ DeMarco",
        "MJ DeMarco": "MJ DeMarco",
        "람릿 세티": "Ramit Sethi",
        "Ramit Sethi": "Ramit Sethi",
        "가즈오 이시구로": "Kazuo Ishiguro",
        "Kazuo Ishiguro": "Kazuo Ishiguro",
        "에릭 에릭슨": "Erik Erikson",
        "Erik Erikson": "Erik Erikson",
        "프레드릭 배크만": "Fredrik Backman",
        "Fredrik Backman": "Fredrik Backman",
        "오 헨리": "O. Henry",
        "O. Henry": "O. Henry",
        "E.T.A. 호프만": "E.T.A. Hoffmann",
        "호프만": "E.T.A. Hoffmann",
        "E.T.A. Hoffmann": "E.T.A. Hoffmann",
        "레이먼드 브릭스": "Raymond Briggs",
        "브릭스": "Raymond Briggs",
        "Raymond Briggs": "Raymond Briggs",
        "그렉 맥커운": "Greg McKeown",
        "그렉_맥커운": "Greg McKeown",
        "Greg McKeown": "Greg McKeown",
        "한스 로슬링": "Hans Rosling",
        "한스_로슬링": "Hans Rosling",
        "Hans Rosling": "Hans Rosling",
        "토마 피케티": "Thomas Piketty",
        "토마_피케티": "Thomas Piketty",
        "Thomas Piketty": "Thomas Piketty",
        "시다르타 무케르지": "Siddhartha Mukherjee",
        "시다르타_무케르지": "Siddhartha Mukherjee",
        "Siddhartha Mukherjee": "Siddhartha Mukherjee",
        "더글라스 애덤스": "Douglas Adams",
        "더글라스_애덤스": "Douglas Adams",
        "Douglas Adams": "Douglas Adams",
        "더글러스 호프스태터": "Douglas Hofstadter",
        "더글러스_호프스태터": "Douglas Hofstadter",
        "Douglas Hofstadter": "Douglas Hofstadter",
        "엘리자베스 콜버트": "Elizabeth Kolbert",
        "엘리자베스_콜버트": "Elizabeth Kolbert",
        "Elizabeth Kolbert": "Elizabeth Kolbert",
        "벤저민 그레이엄": "Benjamin Graham",
        "벤저민_그레이엄": "Benjamin Graham",
        "Benjamin Graham": "Benjamin Graham",
        "로버트 기요사키": "Robert Kiyosaki",
        "로버트_기요사키": "Robert Kiyosaki",
        "Robert Kiyosaki": "Robert Kiyosaki",
        "칼 뉴포트": "Cal Newport",
        "칼_뉴포트": "Cal Newport",
        "Cal Newport": "Cal Newport",
        "대니얼 카너먼": "Daniel Kahneman",
        "대니얼_카너먼": "Daniel Kahneman",
        "Daniel Kahneman": "Daniel Kahneman",
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
        "Antoine de Saint-Exupéry": "생텍쥐페리",
        "Orhan Pamuk": "우르한 파묵",
        "Morgan Housel": "모건 하우설",
        "Louisa May Alcott": "루이자 메이 올콧",
        "Dale Carnegie": "데일 카네기",
        "Sima Qian": "사마천",
        "Mark Manson": "마크 맨슨",
        "Naval Ravikant": "나발 라비칸트",
        "MJ DeMarco": "엠제이 드마코",
        "Ramit Sethi": "람릿 세티",
        "Kazuo Ishiguro": "가즈오 이시구로",
        "Erik Erikson": "에릭 에릭슨",
        "Fredrik Backman": "프레드릭 배크만",
        "O. Henry": "오 헨리",
        "E.T.A. Hoffmann": "E.T.A. 호프만",
        "Raymond Briggs": "레이먼드 브릭스",
        "Greg McKeown": "그렉 맥커운",
        "Hans Rosling": "한스 로슬링",
        "Thomas Piketty": "토마 피케티",
        "Siddhartha Mukherjee": "시다르타 무케르지",
        "Douglas Adams": "더글라스 애덤스",
        "Douglas Hofstadter": "더글러스 호프스태터",
        "Elizabeth Kolbert": "엘리자베스 콜버트",
        "Benjamin Graham": "벤저민 그레이엄",
        "Robert Kiyosaki": "로버트 기요사키",
        "Cal Newport": "칼 뉴포트",
        "Daniel Kahneman": "대니얼 카너먼",
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

