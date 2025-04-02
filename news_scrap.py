import requests
import json
import re
import os
import time
import ssl
import urllib3
import warnings
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from nltk.tokenize import sent_tokenize
import trafilatura

# 경고 메시지 무시 설정
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# 키워드 확장
expanded_keywords = [
    'OLED', 'LCD', '디스플레이', '폴더블', '애플'
]

# Core keywords: 가장 중요하고 자주 등장하는 핵심 용어들
core_keywords = {
    'OLED', 'LCD', 'AMOLED', 'MicroLED', 'QLED', 'QD-OLED',
    'LTPO', 'LTPS', 'TFT', 'MLED',
    'Mini-LED', 'Micro-LED', 'WOLED', 'POLED',
    '폴더블', '롤러블', '스트레처블', '투명디스플레이', '폴더블폰',
    '퀀텀닷', '나노셀', '유기발광', '발광다이오드', '마이크로', '유기발광다이오드',
    '잉크젯', 'IJP', '인광', '소자', 'Vision', '올레도스', '레도스', 'Micro', '게이밍',
    '비전프로', 'FMM', 'FMM-less', 'SE4', '베젤', 'Bezel', '언더 페널페이스', '트리폴드',
    '트리폴드폰',
    'TADF', 'PPI', 'QD', '비전 프로', 'VR', 'MR', 'OLED', '애플', '스마트홈', '혼합현실', '스마트 안경',
    '애플워치', '삼성디스플레이', '삼성D', '공정기술', '공정 기술', '슬림'
}

# Basic keywords: 관련성이 있지만 상대적으로 덜 중요한 용어들
basic_keywords = {
    # 기업 및 기관
    'LG전자', 'LG디스플레이', 'SK하이닉스', '삼성전자', '삼성디스플레이', '삼성 D',
    'BOE', 'AUO', 'CSOT', 'JOLED', '비전옥스', '티안마', 'JDI', 'Sharp', 'Innolux',
    '한국디스플레이산업협회', 'KDLA', '한국전자통신연구원', 'ETRI',
    # 디스플레이 기술
    'OLED', 'LCD', 'QLED', 'MicroLED', 'Mini-LED', 'AMOLED', 'POLED', 'QD-OLED', 'WOLED',
    'MLED', 'Micro',
    '유기발광다이오드', '액정표시장치', '퀀텀닷', '마이크로LED', '미니LED',
    '능동형유기발광다이오드',
    '플렉서블디스플레이', '폴더블디스플레이', '롤러블디스플레이', '스트레처블디스플레이',
    '투명디스플레이', '홀로그래픽디스플레이', '입체디스플레이', 'Bezel', '베젤',
    # 제품 및 응용 분야
    '스마트폰', '태블릿', '노트북', '모니터', '게이밍모니터', 'TV', '스마트TV', 'UHDTV',
    '웨어러블기기',
    '자동차디스플레이', '헤드업디스플레이', 'HUD', '증강현실', 'AR', '가상현실', 'VR', '혼합현실',
    'MR',
    '애플워치', '아이패드', '갤럭시', '아이폰', 'Vision Pro', 'Vision',
    # 기술 용어
    '백플레인', '구동기술', 'TFT', '박막트랜지스터', '발광효율', '색재현율', '명암비', '응답속도',
    '광효율',
    '해상도', '픽셀밀도', 'PPI', '리프레시율', '광시야각', '소비전력', '수명', '번인현상', 'RGB',
    'HDR', '번인',
    '탠덤', '편광판', '백라이트', '언더페널페이스', '트리폴드', '트리폴드폰', 'TADF', 'QD',
    # 생산 및 제조
    '대형패널', '중소형패널', '8세대', '10.5세대', '11세대', '증착', '봉지', '모듈화', '수율',
    '생산능력', '가동률', '공정', '장비', '소재', '부품', '8.5세대', '8.6세대', '6세대',
    # 시장 및 비즈니스 용어
    '시장점유율', '매출액', '영업이익', '설비투자', 'CAPEX', '연구개발', 'R&D', '특허',
    '공급과잉', '수요예측', '가격경쟁력', '원가절감', '수익성', '경쟁력', '차별화전략',
    # 산업 동향
    '산업생태계', '공급망', '밸류체인', '기술로드맵', '기술격차', '기술추격', '기술혁신',
    '산업구조조정', '산업고도화', '스마트팩토리', '산업지원정책', '규제완화',
    # 미래 기술 및 트렌드
    '차세대디스플레이', '지능형디스플레이', '인공지능', 'AI', '사물인터넷', 'loT', '5G', '6G',
    '메타버스', '디지털트윈', '친환경디스플레이', '저전력기술'
}

# Blacklist: 관련은 있지만 디스플레이 산업의 핵심 내용은 아닌 용어들
blacklist = {
    '주가', '증시', '투자자', '매수', '매도',
    '연예인', '배우', '가수', '아이돌', '드라마', '영화',
    '스포츠', '경기', '선수', '팀',
    '정치', '국회', '의원', '대통령', '장관',
    '범죄', '사건', '수사', '재판',
    '부동산', '주택', '아파트', '청약',
    '음식', '맛집', '레스토랑', '요리',
    '여행', '관광', '호텔', '항공',
    '학교', '입시', '수능', '대학',
    '취업', '이직', '연봉',
    '인공지능', '빅데이터', '클라우드',
    '반도체', 'CPU', 'GPU', '메모리',
    '배터리', '전기차', '자율주행',
    '코로나', '팬데믹', '백신',
    '환율', '금리', '인플레이션',
    '전쟁', '방송', '아이돌', '홍보', '광고', '태양', '수소', '태양전지'
}


def crawl_naver_news_api(keywords, now, client_id="", client_secret=""):
    """
    네이버 뉴스 API를 사용하여 뉴스 기사를 크롤링하고,
    주어진 시간에 따라 기사 수집 시간 범위를 설정합니다.

    Args:
        keywords (list): 검색할 키워드 목록
        now (datetime): 코드 실행 시간
        client_id (str): 네이버 API client_id
        client_secret (str): 네이버 API client_secret

    Returns:
        list: 크롤링된 뉴스 기사 목록
    """

    articles = []
    
    hour = now.hour

    if 7 <= hour < 13:  # 오전 7시 ~ 오후 1시
        end_date = now.replace(hour=7, minute=0, second=0, microsecond=0)
        start_date = (now - timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    elif 13 <= hour < 17:  # 오후 1시 ~ 오후 5시
        end_date = now.replace(hour=13, minute=0, second=0, microsecond=0)
        start_date = (now - timedelta(days=1)).replace(hour=17, minute=0, second=0, microsecond=0)
    else:  # 오후 5시 이후
        end_date = now.replace(hour=17, minute=0, second=0, microsecond=0)
        start_date = now.replace(hour=17, minute=0, second=0, microsecond=0) - timedelta(days=1)

    for keyword in keywords:
        start = 1
        while start <= 1000:  # Naver API 최대 결과 수
            url = "https://openapi.naver.com/v1/search/news.json"
            headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret,
            }
            params = {
                "query": keyword,
                "display": 100,  # 한 번에 최대 결과 수 요청
                "start": start,
                "sort": "date",
            }

            try:
                response = requests.get(url, headers=headers, params=params, verify=False)
                response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
                result = json.loads(response.text)

                if 'items' not in result or not result['items']:
                    break

                for item in result['items']:
                    pub_date = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0900')
                    if start_date <= pub_date <= end_date:
                        content = extract_full_content(item['link'])
                        articles.append({
                            'title': item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '').replace('&lt;', '<').replace('&gt;', '>'),
                            'date': pub_date.strftime('%Y-%m-%d %H:%M'),
                            'link': item['link'],
                            'content': content
                        })
                    elif pub_date < start_date:
                        break

                start += 100
                time.sleep(0.1)  # API 호출 간 딜레이
            except requests.exceptions.RequestException as e:
                print(f"Error during requests to Naver API: {e}")
                break  # 에러 발생 시 현재 키워드 크롤링 중단
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON response from Naver API: {e}")
                break  # JSON 디코드 에러 발생 시 현재 키워드 크롤링 중단

    return remove_duplicates(articles)


def extract_full_content(url):
    """
    주어진 URL에서 뉴스 기사의 본문 내용을 추출합니다.

    Args:
        url (str): 뉴스 기사 URL

    Returns:
        str: 추출된 기사 본문 내용
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
        html = response.text
        json_data = trafilatura.extract(html, output_format='json', include_comments=False,
                                       include_tables=False)

        if json_data:
            data = json.loads(json_data)
            content = data.get('text', "")
            return content
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data from {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while extracting content from {url}: {str(e)}")
        return None


def remove_duplicates(articles):
    """
    뉴스 기사 목록에서 제목과 링크가 동일한 중복 기사를 제거합니다.

    Args:
        articles (list): 뉴스 기사 목록

    Returns:
        list: 중복이 제거된 뉴스 기사 목록
    """

    seen = set()
    unique_articles = []
    for article in articles:
        key = (article['title'], article['link'])
        if key not in seen:
            seen.add(key)
            unique_articles.append(article)
    return unique_articles


def calculate_relevance_score(title, content):
    """
    기사의 제목과 본문 내용을 기반으로 관련성 점수를 계산합니다.

    Args:
        title (str): 기사 제목
        content (str): 기사 본문 내용

    Returns:
        int: 계산된 관련성 점수
    """

    # title과 content가 None이 아닌지 확인
    title = title or ""
    content = content or ""

    # 깨진 텍스트 감지를 위한 정규 표현식
    broken_text_pattern = re.compile(r'[^\x00-\x7F\uAC00-\uD7A3]')

    # 깨진 텍스트의 비율 계산
    title_broken_ratio = len(broken_text_pattern.findall(title)) / len(title) if title else 0
    content_broken_ratio = len(broken_text_pattern.findall(content)) / len(content) if content else 0

    # 깨진 텍스트 비율이 20%를 넘으면 점수 감소
    broken_text_penalty = 0
    if title_broken_ratio > 0.2 or content_broken_ratio > 0.4:
        broken_text_penalty = -50  # 점수 감소

    # 제목 점수 계산
    title_score = sum(20 for word in core_keywords if word in title)
    title_score -= sum(15 for word in blacklist if word in title)

    # 본문 점수 계산
    content_words = re.findall(r'\w+', content.lower())
    content_score = sum(3 for word in content_words if word in basic_keywords)
    content_score -= sum(5 for word in content_words if word in blacklist)

    # 문장 단위 분석
    sentences = sent_tokenize(content)
    sentence_score = sum(3 for sentence in sentences if any(word in sentence for word in core_keywords))

    # 총점 계산
    total_score = title_score + content_score + sentence_score + broken_text_penalty

    return total_score


def filter_articles(articles, threshold=25):
    """
    기사 목록을 관련성 점수를 기준으로 필터링하고,
    관련성 점수 및 날짜를 기준으로 정렬합니다.

    Args:
        articles (list): 뉴스 기사 목록
        threshold (int): 관련성 점수 기준값

    Returns:
        list: 필터링 및 정렬된 뉴스 기사 목록
    """

    filtered_articles = []
    for article in articles:
        title = article.get('title', "")
        content = article.get('content', "")
        score = calculate_relevance_score(title, content)

        if score >= threshold:
            article['relevance_score'] = score
            filtered_articles.append(article)

    # 관련성 점수 순으로 정렬 (내림차순)
    filtered_articles.sort(key=lambda x: x['relevance_score'], reverse=True)

    # 날짜를 기준으로 내림차순 정렬 (최신 기사가 먼저 오도록)
    filtered_articles.sort(key=lambda x: x.get('date', ""), reverse=True)

    return filtered_articles


def save_articles_to_json(articles, filename='articles.json'):
    """
    뉴스 기사 목록을 JSON 파일로 저장합니다.

    Args:
        articles (list): 뉴스 기사 목록
        filename (str): 저장할 JSON 파일 이름
    """

    def datetime_to_string(obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        return obj

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4, default=datetime_to_string)
    print(f"{filename}에 저장되었습니다.")



# 메인 실행 블록
if __name__ == "__main__":
    load_dotenv()
    client_id = os.getenv("CLIENT_ID") or os.getenv("client_id")
    client_secret = os.getenv("CLIENT_SECRET") or os.getenv("client_secret")

    if not client_id or not client_secret:
        print("Error: client_id or client_secret is not set in .env file or environment variables.")
    else:
        now = datetime.now()
        articles = crawl_naver_news_api(expanded_keywords, now, client_id=client_id,
                                           client_secret=client_secret)
        print(f"총 {len(articles)}개의 기사를 수집했습니다. (실행 시간: {now.strftime('%H:%M')})")

        filtered_articles = filter_articles(articles, threshold=25)
        save_articles_to_json(filtered_articles, filename=f'articles_filtered_{now.strftime("%H%M")}.json')

        print(f"총 {len(articles)}개의 기사 중 {len(filtered_articles)}개가 선별되었습니다.")

        # 상위 5개 기사 출력 예시
        for article in filtered_articles[:5]:
            print(f"제목: {article['title']}")
            print(f"관련성 점수: {article['relevance_score']}")
            print(" ")
