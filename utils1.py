import google.generativeai as genai  # Google Generative AI 라이브러리 임포트
from typing import Optional  # Optional 타입을 위한 임포트
import pandas as pd  # 데이터 프레임 작업을 위한 pandas 라이브러리 임포트
import requests  # HTTP 요청을 위한 requests 라이브러리 임포트
from bs4 import BeautifulSoup  # HTML 파싱을 위한 BeautifulSoup 임포트
import os  # 운영 체제 관련 작업을 위한 os 라이브러리 임포트
from dotenv import load_dotenv  # .env 파일에서 환경 변수 로드를 위한 dotenv 임포트
import time  # 시간 관련 함수 사용을 위한 time 라이브러리 임포트
import backoff  # 백오프 전략을 위한 backoff 라이브러리 임포트

load_dotenv()  # .env 파일에서 환경 변수 로드

# Gemini Pro API 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # 환경 변수에서 API 키 로드
genai.configure(api_key=GOOGLE_API_KEY)  # Google Generative AI 설정

# API 호출 제한을 위한 설정
MAX_RETRIES = 3  # 최대 재시도 횟수
RETRY_DELAY = 1  # 재시도 간 딜레이 시간 (초 단위)

def create_structured_prompt(text: str, output_language: str, task_type: str) -> str:
    """구조화된 프롬프트 생성"""
    # 어휘 분석 작업인 경우
    if task_type == "vocabulary":
        return f"""You are Claude, a highly capable AI assistant with expertise in Korean language analysis. Your task is to analyze Korean text and provide comprehensive vocabulary explanations.
        
        Input Text: {text}
        
        Task: Analyze this text and extract vocabulary in multiple categories, following these specific guidelines:
        
        1. Selection Categories and Quantities:
        A. Essential Core Vocabulary (10 words):
           * Most crucial words for understanding the main message
           * High-frequency words in the text
           * Words essential for topic comprehension

        B. Topic-Specific Vocabulary (10 words):
           * Field-specific terminology
           * Subject-matter vocabulary
           * Technical or specialized terms

        C. Useful Expressions (10 phrases):
           * Idiomatic expressions
           * Common phrases
           * Colloquial expressions

        D. Advanced Vocabulary (10 words):
           * Academic or formal words
           * Literary expressions
           * Sophisticated vocabulary

        2. For Each Word/Expression, Provide:
        - Korean word/phrase in Hangul
        - Part of speech (명사, 동사, 형용사, etc.)
        - Precise definition in {output_language}
        - Etymology if relevant (especially for Sino-Korean words)
        - Register (formal/informal/written/spoken)
        - Common collocations
        - One natural example sentence showing typical usage

        3. Format Requirements:
        Output your analysis in clean table format with these exact columns, organized by categories:
        | Category | Korean Word | Part of Speech | {output_language} Meaning | Natural Example Sentence |

        4. Quality Standards:
        - Definitions must be precise and context-appropriate
        - Example sentences must be natural and contemporary
        - Explanations should be clear and concise
        - Maintain consistent formatting throughout
        - Include difficulty level (beginner/intermediate/advanced)

        5. Additional Context:
        - Provide common synonyms where applicable
        - Note any regional variations
        - Include level-appropriate alternatives
        - Highlight any potential confusion points
        
        Remember:
        - Organize words clearly by category
        - Ensure comprehensive coverage of the text
        - Focus on practical usage while including advanced vocabulary
        - Provide clear learning progression from basic to advanced terms
        """
    else:  # 문법 분석 작업인 경우
        return f"""You are Claude, a highly capable AI assistant specializing in Korean grammar analysis. Your task is to analyze Korean text and explain its grammatical patterns.
        
        Input Text: {text}
        
        Task: Analyze this text and extract key grammatical patterns, following these specific guidelines:
        
        1. Pattern Selection:
        - Identify exactly 5 most significant grammatical patterns
        - Prioritize based on:
          * Importance to the text's meaning
          * Frequency in modern Korean
          * Complexity level
          * Practical applicability

        2. For Each Pattern, Provide:
        - Complete grammatical structure
        - Clear explanation in {output_language}
        - Formation rules with any irregular changes
        - Usage context (formal/informal, written/spoken)
        - Common mistakes to avoid
        - Two contrasting example sentences

        3. Format Requirements:
        Output your analysis in a clean table format with these exact columns:
        | Grammar Pattern | Usage in {output_language} | Natural Example Sentence |

        4. Quality Standards:
        - Explanations must be systematic and clear
        - Examples should demonstrate correct usage
        - Include relevant conjugation rules
        - Highlight any exceptions or special cases
        
        Remember: Focus on practical application and clear explanation of usage rules. Prioritize patterns that are most relevant for learners at an intermediate level.
        """

@backoff.on_exception(backoff.expo, Exception, max_tries=MAX_RETRIES)
def call_gemini_api(prompt: str) -> str:
    """Gemini API 호출 with 재시도 로직"""
    try:
        model = genai.GenerativeModel('gemini-pro')  # Gemini 모델 설정
        response = model.generate_content(prompt)  # 모델을 사용하여 프롬프트에 대한 응답 생성
        if not response.text:  # 응답 텍스트가 비어 있으면 예외 발생
            raise Exception("빈 응답 받음")
        return response.text  # 응답 텍스트 반환
    except Exception as e:
        print(f"API 호출 오류: {str(e)}")  # 오류 메시지 출력
        raise

def parse_table_response(response_text: str, expected_columns: int) -> list:
    """API 응답을 테이블 형식으로 파싱"""
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]  # 응답 텍스트를 라인별로 분리하고 공백 제거
    data = []
    
    for line in lines:  # 각 라인에 대해 처리
        if '|' in line and not line.startswith('|-'):  # 테이블 형식인지 확인
            items = [item.strip() for item in line.split('|')]  # '|' 구분자로 항목 분리
            items = [item for item in items if item]  # 빈 항목 제거
            if len(items) == expected_columns:  # 예상되는 열 수와 일치하면 데이터에 추가
                data.append(items)
    
    return data[1:] if len(data) > 1 else []  # 헤더 제외하고 데이터 반환

def extract_vocabulary(text: str, output_language: str = "Tiếng Việt") -> pd.DataFrame:
    """텍스트에서 어휘 분석"""
    prompt = create_structured_prompt(text, output_language, "vocabulary")  # 어휘 분석을 위한 프롬프트 생성
    response_text = call_gemini_api(prompt)  # API 호출
    
    data = parse_table_response(response_text, 5)  # 응답에서 데이터 파싱
    
    column_names = {
        "한국어": ["카테고리", "단어", "품사", "의미", "예문"],
        "English": ["Category", "Word", "Part of Speech", "Meaning", "Example"],
        "Tiếng Việt": ["Danh mục", "Từ vựng", "Từ loại", "Ý nghĩa", "Ví dụ"]
    }
    
    df = pd.DataFrame(data, columns=column_names[output_language])  # pandas DataFrame으로 변환
    return df

def extract_grammar(text: str, output_language: str = "Tiếng Việt") -> pd.DataFrame:
    """텍스트에서 문법 패턴 분석"""
    prompt = create_structured_prompt(text, output_language, "grammar")  # 문법 분석을 위한 프롬프트 생성
    response_text = call_gemini_api(prompt)  # API 호출
    
    data = parse_table_response(response_text, 3)  # 응답에서 데이터 파싱
    
    column_names = {
        "한국어": ["문법", "용법", "예문"],
        "English": ["Pattern", "Usage", "Example"],
        "Tiếng Việt": ["Mẫu câu", "Cách dùng", "Ví dụ"]
    }
    
    df = pd.DataFrame(data, columns=column_names[output_language])  # pandas DataFrame으로 변환
    return df

def fetch_url_content(url: str) -> Optional[str]:
    """URL에서 텍스트 콘텐츠 가져오기"""
    try:
        response = requests.get(url)  # URL로 GET 요청
        response.raise_for_status()  # 오류가 있을 경우 예외 발생
        return response.text  # 텍스트 콘텐츠 반환
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch URL content: {str(e)}")  # 오류 메시지 출력
