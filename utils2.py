import google.generativeai as genai
from typing import Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import time
import backoff
import pdfplumber

load_dotenv()

# Gemini Pro API 설정
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# API 호출 제한을 위한 설정
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
def create_structured_prompt(text: str, output_language: str, task_type: str) -> str:
    """구조화된 프롬프트 생성 (HTML 형식, 상세 지침, 단계별 사고 포함)"""
    if task_type == "vocabulary":
        return f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #0056b3;">Korean Vocabulary Analysis Task</h2>
            <p><strong>You are Claude, a highly capable AI assistant with expertise in Korean language analysis.</strong> Your task is to analyze the provided Korean text and provide comprehensive vocabulary explanations.</p>
            
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p><strong>Input Text:</strong></p>
                <pre style="white-space: pre-wrap; font-family: monospace; padding: 10px; background-color: #e0e0e0; border-radius: 3px;">{text}</pre>
            </div>
            
            <p><strong>Task:</strong> Analyze the text and extract vocabulary in multiple categories, following these specific guidelines:</p>
            
            <ol>
                <li>
                    <p><strong>Selection Categories and Quantities:</strong></p>
                    <ul>
                        <li><strong>A. Essential Core Vocabulary (10 words):</strong>
                            <ul>
                                <li>Most crucial words for understanding the main message</li>
                                <li>High-frequency words in the text</li>
                                <li>Words essential for topic comprehension</li>
                            </ul>
                        </li>
                        <li><strong>B. Topic-Specific Vocabulary (10 words):</strong>
                            <ul>
                                <li>Field-specific terminology</li>
                                <li>Subject-matter vocabulary</li>
                                <li>Technical or specialized terms</li>
                            </ul>
                        </li>
                        <li><strong>C. Useful Expressions (10 phrases):</strong>
                            <ul>
                                <li>Idiomatic expressions</li>
                                <li>Common phrases</li>
                                <li>Colloquial expressions</li>
                            </ul>
                        </li>
                        <li><strong>D. Advanced Vocabulary (10 words):</strong>
                            <ul>
                                <li>Academic or formal words</li>
                                <li>Literary expressions</li>
                                <li>Sophisticated vocabulary</li>
                            </ul>
                        </li>
                    </ul>
                </li>
                <li>
                    <p><strong>For Each Word/Expression, Provide:</strong></p>
                    <ul>
                        <li>Korean word/phrase in Hangul</li>
                        <li>Part of speech (명사, 동사, 형용사, etc.)</li>
                        <li>Precise definition in {output_language}</li>
                        <li>Etymology if relevant (especially for Sino-Korean words)</li>
                        <li>Register (formal/informal/written/spoken)</li>
                        <li>Common collocations</li>
                        <li>One natural example sentence showing typical usage</li>
                    </ul>
                </li>
                <li>
                    <p><strong>Format Requirements:</strong></p>
                    <p>Output your analysis in clean table format with these exact columns, organized by categories:</p>
                    <pre style="font-family: monospace; padding: 10px; background-color: #e0e0e0; border-radius: 3px;">| Category | Korean Word | Part of Speech | {output_language} Meaning | Natural Example Sentence |</pre>
                </li>
                <li>
                    <p><strong>Quality Standards:</strong></p>
                    <ul>
                        <li>Definitions must be precise and context-appropriate</li>
                        <li>Example sentences must be natural and contemporary</li>
                        <li>Explanations should be clear and concise</li>
                        <li>Maintain consistent formatting throughout</li>
                        <li>Include difficulty level (beginner/intermediate/advanced)</li>
                    </ul>
                </li>
                <li>
                    <p><strong>Additional Context:</strong></p>
                    <ul>
                        <li>Provide common synonyms where applicable</li>
                        <li>Note any regional variations</li>
                        <li>Include level-appropriate alternatives</li>
                        <li>Highlight any potential confusion points</li>
                    </ul>
                </li>
            </ol>
            
            <p><strong>Think Step-by-Step:</strong></p>
            <p>Before providing the final output, please think step-by-step about the following:</p>
            <ul>
                <li>First, identify the main topic of the text.</li>
                <li>Second, identify the most important words related to the topic.</li>
                <li>Third, categorize the words based on the given categories.</li>
                <li>Fourth, provide the required information for each word/expression.</li>
                <li>Finally, format the output in the specified table format.</li>
            </ul>
            
            <p><strong>Remember:</strong></p>
            <ul>
                <li>Organize words clearly by category.</li>
                <li>Ensure comprehensive coverage of the text.</li>
                <li>Focus on practical usage while including advanced vocabulary.</li>
                <li>Provide clear learning progression from basic to advanced terms.</li>
            </ul>
        </div>
        """
    else:  # grammar
        return f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #0056b3;">Korean Grammar Analysis Task</h2>
            <p><strong>You are Claude, a highly capable AI assistant specializing in Korean grammar analysis.</strong> Your task is to analyze the provided Korean text and explain its grammatical patterns.</p>
            
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <p><strong>Input Text:</strong></p>
                <pre style="white-space: pre-wrap; font-family: monospace; padding: 10px; background-color: #e0e0e0; border-radius: 3px;">{text}</pre>
            </div>
            
            <p><strong>Task:</strong> Analyze the text and extract key grammatical patterns, following these specific guidelines:</p>
            
            <ol>
                <li>
                    <p><strong>Pattern Selection:</strong></p>
                    <ul>
                        <li>Identify exactly 5 most significant grammatical patterns</li>
                        <li>Prioritize based on:
                            <ul>
                                <li>Importance to the text's meaning</li>
                                <li>Frequency in modern Korean</li>
                                <li>Complexity level</li>
                                <li>Practical applicability</li>
                            </ul>
                        </li>
                    </ul>
                </li>
                <li>
                    <p><strong>For Each Pattern, Provide:</strong></p>
                    <ul>
                        <li>Complete grammatical structure</li>
                        <li>Clear explanation in {output_language}</li>
                        <li>Formation rules with any irregular changes</li>
                        <li>Usage context (formal/informal, written/spoken)</li>
                        <li>Common mistakes to avoid</li>
                        <li>Two contrasting example sentences</li>
                    </ul>
                </li>
                <li>
                    <p><strong>Format Requirements:</strong></p>
                    <p>Output your analysis in a clean table format with these exact columns:</p>
                    <pre style="font-family: monospace; padding: 10px; background-color: #e0e0e0; border-radius: 3px;">| Grammar Pattern | Usage in {output_language} | Natural Example Sentence |</pre>
                </li>
                <li>
                    <p><strong>Quality Standards:</strong></p>
                    <ul>
                        <li>Explanations must be systematic and clear</li>
                        <li>Examples should demonstrate correct usage</li>
                        <li>Include relevant conjugation rules</li>
                        <li>Highlight any exceptions or special cases</li>
                    </ul>
                </li>
            </ol>
            
            <p><strong>Think Step-by-Step:</strong></p>
            <p>Before providing the final output, please think step-by-step about the following:</p>
            <ul>
                <li>First, identify the main grammatical structures used in the text.</li>
                <li>Second, select the 5 most significant patterns based on the given criteria.</li>
                <li>Third, provide the required information for each pattern.</li>
                <li>Finally, format the output in the specified table format.</li>
            </ul>
            
            <p><strong>Remember:</strong> Focus on practical application and clear explanation of usage rules. Prioritize patterns that are most relevant for learners at an intermediate level.</p>
        </div>
        """
#def create_structured_prompt(text: str, output_language: str, task_type: str) -> str:
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

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file, page by page."""
    page_texts = []
    with pdfplumber.open(pdf_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
               page_texts.append({"page": page_num, "text": text})
    return page_texts