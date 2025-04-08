import streamlit as st
from utils2 import extract_vocabulary, extract_grammar, extract_text_from_pdf
import pandas as pd
from typing import Optional

def download_results(df: pd.DataFrame, output_language: str) -> tuple[str, str, bytes]:
    """
    Prepare results for download with proper encoding based on language
    
    Args22
        df: DataFrame containing the analysis results
        output_language: Selected output language
    
    Returns:
        tuple: (button_label, filename, csv_data)
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
    # Initialize dark mode state if not already set
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False

    st.set_page_config(
        page_title="Korean Text Analyzer",
        page_icon="🇰🇷",
        layout="wide"
    )

    # Toggle for dark mode in sidebar
    with st.sidebar:
        st.header("Theme Settings 🎨")
        st.session_state.dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)

    # Custom CSS with dynamic theming
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
    st.write("Analyze Korean text to extract vocabulary and grammar insights.")

    # Settings sidebar
    with st.sidebar:
        st.header("Analysis Settings ⚙️")
        st.info("Select the type of analysis you want to perform. You can choose from Vocabulary, Grammar, or Both.")
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

    # Main content
    input_type = st.radio("Input Type:", ["Paste Text", "Upload File PDF"])
    
    user_input: Optional[str] = None
    pdf_file = None
    
    if input_type == "Paste Text":
        user_input = st.text_area("Enter your Korean text here:", height=200)
    elif input_type == "Upload File PDF":
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        if uploaded_file:
            pdf_file = uploaded_file

    if st.button("Analyze Text", key="analyze"):
        if user_input or pdf_file:
            with st.spinner('Analyzing text... Please wait.'):  
                try:
                     # Initialize variables to store all results
                    all_vocab_results = []
                    all_grammar_results = []
                    
                    if pdf_file:
                        page_texts = extract_text_from_pdf(pdf_file)
                        for page_data in page_texts:
                            page_num = page_data["page"]
                            text = page_data["text"]
                             
                            st.subheader(f"Page {page_num}")
                            
                            # Perform analysis
                            vocab_result = None
                            grammar_result = None

                            if "Vocabulary" in analysis_type or "Both" in analysis_type:
                                vocab_result = extract_vocabulary(text, output_language)
                                if not vocab_result.empty:  # Check if there are results
                                    all_vocab_results.append(vocab_result.assign(page=page_num))
                            
                            if "Grammar" in analysis_type or "Both" in analysis_type:
                                grammar_result = extract_grammar(text, output_language)
                                if not grammar_result.empty:
                                    all_grammar_results.append(grammar_result.assign(page=page_num))
                            
                            # Display results for each page
                            if vocab_result is not None and not vocab_result.empty:
                                st.subheader(f"Vocabulary Analysis - Page {page_num}")
                                st.dataframe(vocab_result, use_container_width=True, hide_index=True)
                            
                            if grammar_result is not None and not grammar_result.empty:
                                st.subheader(f"Grammar Analysis - Page {page_num}")
                                st.dataframe(grammar_result, use_container_width=True, hide_index=True)

                    elif user_input:
                        # Call analysis functions here
                        vocab_result = None
                        grammar_result = None

                        if "Vocabulary" in analysis_type or "Both" in analysis_type:
                            vocab_result = extract_vocabulary(user_input, output_language)
                            if not vocab_result.empty:
                                all_vocab_results.append(vocab_result)
                        
                        if "Grammar" in analysis_type or "Both" in analysis_type:
                            grammar_result = extract_grammar(user_input, output_language)
                            if not grammar_result.empty:
                                all_grammar_results.append(grammar_result)

                        # Display results
                        if vocab_result is not None and not vocab_result.empty:
                            st.subheader("Vocabulary Analysis")
                            st.dataframe(
                                vocab_result,
                                use_container_width=True,
                                hide_index=True
                            )

                        if grammar_result is not None and not grammar_result.empty:
                            st.subheader("Grammar Analysis")
                            st.dataframe(
                                grammar_result,
                                use_container_width=True,
                                hide_index=True
                            )
                    
                     # Export results
                    results_to_export = []
                    if all_vocab_results:
                        combined_vocab_results = pd.concat(all_vocab_results, ignore_index=True)
                        combined_vocab_results['type'] = 'vocabulary'
                        results_to_export.append(combined_vocab_results)
                    if all_grammar_results:
                        combined_grammar_results = pd.concat(all_grammar_results, ignore_index=True)
                        combined_grammar_results['type'] = 'grammar'
                        results_to_export.append(combined_grammar_results)

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
                        
                        # Preview result before download
                        st.write("미리보기:")
                        st.dataframe(combined_results)
                
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                else:
                    st.success("Analysis completed successfully! 분석이 완료되었습니다!")
        else:
            st.warning("Please provide some text or a PDF file to analyze!")

if __name__ == "__main__":
    main()