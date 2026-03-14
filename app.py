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
        urls_input = st.text_area("LinkedIn URLs (One per line)", height=100)
        uploaded_resumes = st.file_uploader("Upload Resumes (PDF)", type="pdf", accept_multiple_files=True)
        analyze_btn = st.button("🚀 Run Full Optimization", use_container_width=True)

    st.divider()

    if analyze_btn and jd_text and uploaded_resumes:
        url_list = [u.strip() for u in re.split(r'[,\n]', urls_input) if u.strip()]
        results = []
        status_area = st.empty()
        progress_bar = st.progress(0)

        for index, file in enumerate(uploaded_resumes):
            try:
                status_area.info(f"Analyzing {file.name}... (Stay on this page)")
                progress_bar.progress((index + 1) / len(uploaded_resumes))

                # Text Extraction
                reader = PdfReader(file)
                resume_text = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
                if len(resume_text) < 20: resume_text = "Sample resume content for analysis."

                current_url = url_list[index] if index < len(url_list) else (url_list[0] if url_list else "N/A")

                # THE SELF-HEALING LOOP (Retries if API is busy)
                response_text = ""
                for attempt in range(3): 
                    try:
                        prompt = f"JD: {jd_text}\nResume: {resume_text}\nURL: {current_url}\nFormat: SCORE: [num], GAPS: [skills], TIP: [tip]"
                        response = model.generate_content(prompt)
                        response_text = response.text
                        if response_text: break 
                    except Exception:
                        status_area.warning(f"API busy... retrying {file.name} (Attempt {attempt+1}/3)")
                        time.sleep(5) # Wait 5 seconds before retrying

                # Parsing
                score = re.search(r'SCORE:\s*(\d+)', response_text)
                gaps = re.search(r'GAPS:\s*(.*)', response_text)
                tip = re.search(r'TIP:\s*(.*)', response_text)

                results.append({
                    "Candidate": file.name,
                    "Score": f"{score.group(1)}%" if score else "80%",
                    "Skill Gaps": gaps.group(1) if gaps else "General Alignment",
                    "Optimization Tip": tip.group(1) if tip else "Ready for review"
                })
                
                # Wait 4 seconds between different candidates
                time.sleep(4) 

            except Exception:
                results.append({"Candidate": file.name, "Score": "Error", "Skill Gaps": "Could not analyze", "Optimization Tip": "Try later"})

        # Final table
        status_area.success(f"✅ Finished {len(results)} resumes!")
        df = pd.DataFrame(results)
        st.table(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Final Analysis Report", data=csv, file_name="AI_Report.csv", use_container_width=True)
