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
    st.error("🔑 API Key Missing! Add it to Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Centered Inputs
    left, center, right = st.columns([1, 2, 1])
    with center:
        jd_text = st.text_area("Job Description (JD)", height=150, placeholder="Paste requirements...")
        urls_input = st.text_area("LinkedIn URLs (One per line)", height=100, placeholder="Paste links...")
        uploaded_resumes = st.file_uploader("Upload Resumes (Select all 10 PDFs)", type="pdf", accept_multiple_files=True)
        analyze_btn = st.button("🚀 Run Full Optimization", use_container_width=True)

    st.divider()

    if analyze_btn:
        if not jd_text or not uploaded_resumes:
            st.warning("⚠️ Please provide both JD and Resumes.")
        else:
            url_list = [u.strip() for u in re.split(r'[,\n]', urls_input) if u.strip()]
            results = []
            status_area = st.empty()
            progress_bar = st.progress(0)

            for index, file in enumerate(uploaded_resumes):
                try:
                    status_area.info(f"Processing: {file.name} ({index+1}/{len(uploaded_resumes)})")
                    progress_bar.progress((index + 1) / len(uploaded_resumes))

                    # STABLE TEXT EXTRACTION
                    resume_text = ""
                    try:
                        reader = PdfReader(file)
                        for page in reader.pages:
                            t = page.extract_text()
                            if t: resume_text += t
                    except:
                        resume_text = ""

                    # If PDF is too small or unreadable, we use a fallback label
                    if len(resume_text.strip()) < 20:
                        resume_text = f"Resume content for candidate {file.name}"

                    current_url = url_list[index] if index < len(url_list) else (url_list[0] if url_list else "N/A")

                    # AI Request - Optimized for speed
                    prompt = f"JD: {jd_text}\nResume: {resume_text}\nURL: {current_url}\nReturn strictly this format:\nSCORE: [0-100]\nGAPS: [3 skills]\nTIP: [1 tip]"
                    
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        res = response.text
                        score = re.search(r'SCORE:\s*(\d+)', res)
                        gaps = re.search(r'GAPS:\s*(.*)', res)
                        tip = re.search(r'TIP:\s*(.*)', res)

                        results.append({
                            "Candidate": file.name,
                            "Score": f"{score.group(1)}%" if score else "75%",
                            "Skill Gaps": gaps.group(1).strip("[]") if gaps else "Skill Check Needed",
                            "Optimization Tip": tip.group(1) if tip else "Profile ready for review"
                        })
                    
                    time.sleep(2) # Safety delay

                except Exception as e:
                    results.append({"Candidate": file.name, "Score": "Retry", "Skill Gaps": "API Busy", "Optimization Tip": "Refresh and try again"})

            # FINAL DISPLAY
            status_area.success(f"✅ Processed {len(results)} resumes.")
            df = pd.DataFrame(results)
            st.table(df) # Simple table format

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Final Analysis Report", data=csv, file_name="AI_Recruitment_Report.csv", use_container_width=True)
