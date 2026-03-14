import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Setup (Cloud-Safe Version)
st.set_page_config(page_title="AI Recruitment Tool", layout="wide")

# Simple, error-free headings
st.title("AI Recruitment: Transparency and Optimization")
st.markdown("### Data-Driven Candidate Alignment & Skill Gap Analysis")
st.write("---")

# 2. API Setup
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Centered Input Section using Columns
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.subheader("📥 Input Panel")
        jd_text = st.text_area("Job Description (JD)", placeholder="Paste requirements...", height=150)
        linkedin_url = st.text_input("Candidate LinkedIn URL")
        uploaded_files = st.file_uploader("Upload Resumes (PDF Batch)", type="pdf", accept_multiple_files=True)
        
        analyze_btn = st.button("🚀 Analyze & Optimize", use_container_width=True)

    st.write("---")

    # 3. Logic Section
    if analyze_btn and jd_text and uploaded_files:
        results = []
        progress_bar = st.progress(0)
        
        for index, file in enumerate(uploaded_files):
            try:
                progress_bar.progress((index + 1) / len(uploaded_files))
                
                # Extract Text
                reader = PdfReader(file)
                resume_text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])

                # Professional AI Prompt
                prompt = f"""
                Analyze candidate for transparency and optimization.
                JD: {jd_text}
                Resume: {resume_text}
                LinkedIn: {linkedin_url if linkedin_url else "N/A"}

                Format:
                SCORE: [0-100]
                GAPS: [Top 3 skills only]
                KEY_POINT: [One short optimization tip]
                """

                response = model.generate_content(prompt).text
                
                # Data Extraction
                score = re.search(r'SCORE:\s*(\d+)', response)
                gaps = re.search(r'GAPS:\s*(.*)', response)
                point = re.search(r'KEY_POINT:\s*(.*)', response)

                results.append({
                    "Candidate": file.name,
                    "Optimization Score": f"{score.group(1)}%" if score else "0%",
                    "Critical Skill Gaps": gaps.group(1) if gaps else "Check JD",
                    "Optimization Key Point": point.group(1) if point else "Optimized"
                })

                time.sleep(1) # API Rate Limit protection

            except Exception as e:
                st.error(f"Error processing {file.name}")

        # 4. Results Display
        if results:
            st.balloons()
            df = pd.DataFrame(results)
            
            st.subheader("📊 Optimization Report")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Optimization Report (CSV)",
                data=csv,
                file_name="AI_Recruitment_Report.csv",
                mime="text/csv",
                use_container_width=True
            )
