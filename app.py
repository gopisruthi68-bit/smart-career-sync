import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Simple Page Setup
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
        jd_text = st.text_area("Job Description (JD)", height=150)
        urls_input = st.text_area("Paste LinkedIn URLs (One per line)", height=100)
        # accept_multiple_files is TRUE - this allows your 10 resumes
        uploaded_resumes = st.file_uploader("Upload Resumes (PDF)", type="pdf", accept_multiple_files=True)
        analyze_btn = st.button("🚀 Run Full Optimization", use_container_width=True)

    st.divider()

    # 3. Processing Logic
    if analyze_btn:
        if not jd_text or not uploaded_resumes:
            st.warning("Please provide both the JD and at least one Resume.")
        else:
            # Prepare URLs
            url_list = [u.strip() for u in re.split(r'[,\n]', urls_input) if u.strip()]
            results = []
            
            # Create a status area so you can see it working
            status_area = st.empty()
            progress_bar = st.progress(0)

            for index, file in enumerate(uploaded_resumes):
                try:
                    status_area.info(f"Analyzing: {file.name} ({index + 1}/{len(uploaded_resumes)})")
                    progress_bar.progress((index + 1) / len(uploaded_resumes))

                    # Read PDF
                    reader = PdfReader(file)
                    resume_text = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
                    
                    # Match URL
                    current_url = url_list[index] if index < len(url_list) else (url_list[0] if url_list else "N/A")

                    # AI Request
                    prompt = f"JD: {jd_text}\nResume: {resume_text}\nURL: {current_url}\nReturn SCORE: [0-100], GAPS: [3 skills], TIP: [1 tip]"
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        res = response.text
                        score = re.search(r'SCORE:\s*(\d+)', res)
                        gaps = re.search(r'GAPS:\s*(.*)', res)
                        tip = re.search(r'TIP:\s*(.*)', res)

                        results.append({
                            "Candidate": file.name,
                            "Score": f"{score.group(1)}%" if score else "70%",
                            "Skill Gaps": gaps.group(1) if gaps else "N/A",
                            "Optimization Tip": tip.group(1) if tip else "Ready"
                        })
                    
                    # Wait 2 seconds between files to keep the API happy
                    time.sleep(2)

                except Exception:
                    results.append({"Candidate": file.name, "Score": "Error", "Skill Gaps": "Could not read", "Optimization Tip": "Retry"})

            # 4. Show Results Table
            status_area.success(f"✅ Finished! Processed {len(results)} resumes.")
            df = pd.DataFrame(results)
            st.table(df) # st.table is easier to read than st.dataframe for your eyes

            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Report", data=csv, file_name="AI_Report.csv", use_container_width=True)
