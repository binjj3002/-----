import streamlit as st
from utils import extract_vocabulary, extract_grammar, fetch_url_content
import pandas as pd
from typing import Optional

def download_results(df: pd.DataFrame, output_language: str) -> tuple[str, str, bytes]:
    """
    결과를 언어별로 다운로드할 수 있도록 준비하는 함수
    
    Args:
        df: 분석 결과를 담고 있는 DataFrame
        output_language: 출력 언어
    
    Returns:
        tuple: (버튼 레이블, 파일명, CSV 데이터)
    """
    # 언어별 다운로드 버튼 레이블
    button_labels = {
        "한국어": "분석 결과 다운로드 (CSV)",
        "English": "Download Analysis Results (CSV)",
        "Tiếng Việt": "Tải kết quả phân tích (CSV)"
    }
    
    # 언어별 파일명
    file_names = {
        "한국어": "한국어_분석_결과.csv",
        "English": "korean_analysis_results.csv",
        "Tiếng Việt": "ket_qua_phan_tich.csv"
    }
    
    # CSV 데이터 생성 (UTF-8 with BOM)
    csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    
    return (
        button_labels.get(output_language, button_labels["Tiếng Việt"]),
        file_names.get(output_language, file_names["Tiếng Việt"]),
        csv_data
    )

def main():
    # 다크 모드 상태 초기화 (이미 설정되지 않았다면)
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    st.set_page_config(
        page_title="Korean Text Analyzer",
        page_icon="🇰🇷",
        layout="wide"
    )

    # 사이드바에서 다크 모드 토글
    with st.sidebar:
        st.header("Theme Settings 🎨")
        st.session_state.dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)

    # 다크 모드에 맞춘 커스텀 CSS
    background_color = '#1e1e1e' if st.session_state.dark_mode else '#f0f0f5'
    text_color = '#ffffff' if st.session_state.dark_mode else '#333'
    
    st.markdown(f"""
        <style>
        body {{
            font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
            background-color: {background_color};
            color: {text_color};
            margin: 0;
            padding: 0;
        }}
        .header {{
            background-color: #c0392b;
            padding: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }}
        .stDataFrame {{
            background-color: {background_color};
            color: {text_color};
        }}
        .snowflake {{
            position: absolute;
            color: white;
            font-size: 24px;
            animation: fall 5s linear infinite;
        }}
        @keyframes fall {{
            0% {{ transform: translateY(0); }}
            100% {{ transform: translateY(100vh); }}
        }}
        .button {{
            background-color: #27ae60;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            color: white;
            cursor: pointer;
            transition: background-color 0.3s, transform 0.3s;
            font-size: 16px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }}
        .button:hover {{
            background-color: #2ecc71;
            transform: scale(1.05);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background-color: #333;
            color: white;
            border-radius: 10px;
        }}
        .santa {{
            position: absolute;
            width: 100px;
            animation: spin 5s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title("Korean Text Analyzer 한국어 분석기")
    st.write("한국어 텍스트를 분석하여 어휘 및 문법 분석 정보를 추출합니다.")

    # 설정 사이드바
    with st.sidebar:
        st.header("Analysis Settings ⚙️")
        st.info("분석하고 싶은 항목을 선택하세요. 어휘, 문법, 또는 둘 다 선택할 수 있습니다.")
        analysis_type = st.multiselect(
            "Select Analysis Types",
            ["Vocabulary", "Grammar", "Both"],
            default=["Both"]
        )
        
        output_language = st.selectbox(
            "Output Language",
            ["한국어", "English", "Tiếng Việt"],
            index=0
        )
        
        show_romanization = st.checkbox("Show Romanization", value=True)
        show_examples = st.checkbox("Show Example Sentences", value=True)

    # 메인 콘텐츠
    input_type = st.radio("Input Type:", ["Paste Text", "Upload File", "URL"])
    
    user_input: Optional[str] = None
    
    if input_type == "Paste Text":
        user_input = st.text_area("Enter your Korean text here:", height=200)
    elif input_type == "Upload File":
        uploaded_file = st.file_uploader("Choose a text file", type=['txt'])
        if uploaded_file:
            user_input = uploaded_file.getvalue().decode("utf-8")
    else:
        url_input = st.text_input("Enter URL:")
        if url_input:
            try:
                user_input = fetch_url_content(url_input)
            except Exception as e:
                st.error(f"Error fetching URL content: {str(e)}")

    if st.button("Analyze Text", key="analyze"):
        if user_input:
            with st.spinner('분석 중... 잠시만 기다려 주세요.'):  
                try:
                    # 분석 함수 호출
                    vocab_result = None
                    grammar_result = None

                    if "Vocabulary" in analysis_type or "Both" in analysis_type:
                        vocab_result = extract_vocabulary(user_input, output_language)
                    
                    if "Grammar" in analysis_type or "Both" in analysis_type:
                        grammar_result = extract_grammar(user_input, output_language)

                    # 분석 결과 표시
                    if vocab_result is not None:
                        st.subheader("Vocabulary Analysis")
                        st.dataframe(
                            vocab_result,
                            use_container_width=True,
                            hide_index=True
                        )

                    if grammar_result is not None:
                        st.subheader("Grammar Analysis")
                        st.dataframe(
                            grammar_result,
                            use_container_width=True,
                            hide_index=True
                        )

                    # 결과 다운로드 준비
                    results_to_export = []
                    if vocab_result is not None:
                        vocab_result['type'] = 'vocabulary'
                        results_to_export.append(vocab_result)
                    if grammar_result is not None:
                        grammar_result['type'] = 'grammar'
                        results_to_export.append(grammar_result)

                    if results_to_export:
                        combined_results = pd.concat(results_to_export, ignore_index=True)
                        
                        # 다운로드 버튼 준비
                        button_label, file_name, csv_data = download_results(
                            combined_results, 
                            output_language
                        )
                        
                        # 다운로드 버튼 표시
                        st.download_button(
                            label=button_label,
                            data=csv_data,
                            file_name=file_name,
                            mime="text/csv",
                            help="CSV 형식으로 분석 결과를 다운로드합니다."
                        )
                        
                        # 미리보기 표시
                        st.write("미리보기:") 
                        st.dataframe(combined_results)
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                else:
                    st.success("Analysis completed successfully! 분석이 완료되었습니다!")
        else:
            st.warning("Please provide some text to analyze!")

if __name__ == "__main__":
    main()
