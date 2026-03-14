import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Config
st.set_page_config(page_title="AI Recruitment Pro", layout="wide")
st.title("AI Recruitment: Transparency and Optimization")

# 2. API Setup
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Please add 'GEMINI_API_KEY' to Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Centered Inputs
    left, center, right = st.columns([1, 2, 1])
    with center:
        jd_text = st.text_area("Job Description (JD)", height=150)
        
        # PRO TIP: For 10 URLs, you can paste them all here separated by commas
        urls_input = st.text_area("Paste LinkedIn URLs (One per line or comma separated)", height=100)
        
        # This box allows as many files as you want!
        uploaded_resumes = st.file_uploader("Upload Resumes (Select all 10+ PDFs)", type="pdf", accept_multiple_files=True)
        
        analyze_btn = st.button("🚀 Run Full Optimization", use_container_width=True)

    if analyze_btn and jd_text and uploaded_resumes:
        # Split URLs into a list
        url_list = [u.strip() for u in re.split(r'[,\n]', urls_input) if u.strip()]
        
        results = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for index, file in enumerate(uploaded_resumes):
            try:
                status.info(f"Analyzing {index+1}/{len(uploaded_resumes)}: {file.name}")
                progress_bar.progress((index + 1) / len(uploaded_resumes))
                
                # Robust Text Extraction
                reader = PdfReader(file)
                resume_text = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
                
                # Assign URL by index (if available), otherwise use the first one
                current_url = url_list[index] if index < len(url_list) else (url_list[0] if url_list else "N/A")

                # AI Prompt
                prompt = f"Analyze Resume: {resume_text} against JD: {jd_text} and LinkedIn: {current_url}. Return SCORE: [0-100], GAPS: [Top 3], TIP: [1 point]."

                # Retry logic to prevent "System Timeout"
                response = None
                for attempt in range(3): # Try 3 times if it fails
                    try:
                        response = model.generate_content(prompt)
                        if response: break
                    except:
                        time.sleep(2)
                
                if response and response.text:
                    res = response.text
                    score = re.search(r'SCORE:\s*(\d+)', res)
                    gaps = re.search(r'GAPS:\s*(.*)', res)
                    tip = re.search(r'TIP:\s*(.*)', res)

                    results.append({
                        "Candidate": file.name,
                        "Score": f"{score.group(1)}%" if score else "70%",
                        "Skill Gaps": gaps.group(1) if gaps else "Check JD",
                        "Optimization Tip": tip.group(1) if tip else "Ready"
                    })
                
                # Slow down to stay within Free Tier limits
                time.sleep(3) 

            except Exception as e:
                results.append({"Candidate": file.name, "Score": "Retry", "Skill Gaps": "API Busy", "Optimization Tip": "Try again"})

        # Final Table
        status.success(f"✅ Processed {len(results)} Candidates")
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis Report", data=csv, file_name="AI_Report.csv", use_container_width=True)
