import google.generativeai as genai
from typing import Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import time
import backoff

load_dotenv()

# Gemini Pro API 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# API 호출 제한을 위한 설정
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def create_structured_prompt(text: str, output_language: str, task_type: str) -> str:
    """구조화된 프롬프트 생성"""
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
    else:  # grammar
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
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        if not response.text:
            raise Exception("빈 응답 받음")
        return response.text
    except Exception as e:
        print(f"API 호출 오류: {str(e)}")
        raise

def parse_table_response(response_text: str, expected_columns: int) -> list:
    """API 응답을 테이블 형식으로 파싱"""
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    data = []
    
    for line in lines:
        if '|' in line and not line.startswith('|-'):
            items = [item.strip() for item in line.split('|')]
            items = [item for item in items if item]  # 빈 항목 제거
            if len(items) == expected_columns:
                data.append(items)
    
    return data[1:] if len(data) > 1 else []  # 헤더 제외

def extract_vocabulary(text: str, output_language: str = "Tiếng Việt") -> pd.DataFrame:
    """텍스트에서 어휘 분석"""
    prompt = create_structured_prompt(text, output_language, "vocabulary")
    response_text = call_gemini_api(prompt)
    
    data = parse_table_response(response_text, 5)
    
    column_names = {
        "한국어": ["카테고리", "단어", "품사", "의미", "예문"],
        "English": ["Category", "Word", "Part of Speech", "Meaning", "Example"],
        "Tiếng Việt": ["Danh mục", "Từ vựng", "Từ loại", "Ý nghĩa", "Ví dụ"]
    }
    
    df = pd.DataFrame(data, columns=column_names[output_language])
    return df

def extract_grammar(text: str, output_language: str = "Tiếng Việt") -> pd.DataFrame:
    """텍스트에서 문법 패턴 분석"""
    prompt = create_structured_prompt(text, output_language, "grammar")
    response_text = call_gemini_api(prompt)
    
    data = parse_table_response(response_text, 3)
    
    column_names = {
        "한국어": ["문법", "용법", "예문"],
        "English": ["Pattern", "Usage", "Example"],
        "Tiếng Việt": ["Mẫu câu", "Cách dùng", "Ví dụ"]
    }
    
    df = pd.DataFrame(data, columns=column_names[output_language])
    return df

def fetch_url_content(url: str) -> Optional[str]:
    """URL에서 텍스트 콘텐츠 가져오기"""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses
        return response.text
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch URL content: {str(e)}")