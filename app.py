import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Config
st.set_page_config(page_title="AI Recruitment Tool", layout="wide")

# Fixed CSS styling
st.markdown("""
    <style>
    .main-header {
        font-size: 38px !important;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
    }
    .sub-header {
        font-size: 18px !important;
        color: #6B7280;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_input=True)

st.markdown('<div class="main-header">AI Recruitment: Transparency and Optimization</div>', unsafe_allow_input=True)
st.markdown('<div class="sub-header">Data-Driven Candidate Alignment & Skill Gap Analysis</div>', unsafe_allow_input=True)

# 2. API Setup
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Add 'GEMINI_API_KEY' to Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Centered Input Panel
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        jd_text = st.text_area("Job Description (JD)", placeholder="Paste requirements...", height=150)
        linkedin_url = st.text_input("LinkedIn URL (Optional)")
        uploaded_files = st.file_uploader("Upload Resumes (PDFs)", type="pdf", accept_multiple_files=True)
        analyze_btn = st.button("🚀 Analyze & Optimize", use_container_width=True)

    st.divider()

    if analyze_btn and jd_text and uploaded_files:
        results = []
        progress_bar = st.progress(0)
        
        for index, file in enumerate(uploaded_files):
            try:
                progress_bar.progress((index + 1) / len(uploaded_files))
                
                reader = PdfReader(file)
                resume_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])

                prompt = f"""
                Analyze for transparency/optimization. JD: {jd_text}. Resume: {resume_text}. 
                LinkedIn: {linkedin_url if linkedin_url else 'N/A'}.
                Format:
                SCORE: [0-100]
                GAPS: [Top 3 skills only]
                KEY_POINT: [One optimization tip]
                """

                response = model.generate_content(prompt).text
                
                # Extracting values
                score = re.search(r'SCORE:\s*(\d+)', response)
                gaps = re.search(r'GAPS:\s*\[?(.*?)\]?$', response, re.MULTILINE)
                point = re.search(r'KEY_POINT:\s*(.*)', response)

                results.append({
                    "Candidate": file.name,
                    "Optimization Score": f"{score.group(1)}%" if score else "0%",
                    "Critical Skill Gaps": gaps.group(1) if gaps else "None",
                    "Key Optimization Point": point.group(1) if point else "Optimized"
                })
                time.sleep(1) 

            except Exception:
                st.error(f"Error processing {file.name}")

        if results:
            df = pd.DataFrame(results)
            st.subheader("📊 Optimization Report")
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Optimization Report (CSV)", data=csv, file_name="AI_Recruitment_Report.csv", mime="text/csv", use_container_width=True)
