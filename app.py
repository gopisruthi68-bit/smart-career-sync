import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Config
st.set_page_config(page_title="AI Recruitment Pro", layout="wide")
st.title("AI Recruitment: Transparency and Optimization")
st.markdown("### Strategic Bulk Alignment Dashboard")

# 2. API Setup
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Please add 'GEMINI_API_KEY' to Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash for speed and reliability
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Centered Inputs
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        jd_text = st.text_area("Job Description (JD)", height=150, placeholder="Paste job requirements here...")
        
        single_linkedin = st.text_input("Single LinkedIn URL (Used if no CSV is uploaded)")
        
        st.info("📂 Optional: For 10 different URLs, upload a CSV with 'Filename' and 'LinkedIn' columns.")
        url_file = st.file_uploader("Upload URL Mapping (CSV)", type="csv")
        
        uploaded_resumes = st.file_uploader("Upload Resumes (PDF Batch)", type="pdf", accept_multiple_files=True)
        analyze_btn = st.button("🚀 Run AI Bulk Optimization", use_container_width=True)

    st.divider()

    if analyze_btn and jd_text and uploaded_resumes:
        url_map = {}
        if url_file:
            try:
                url_df = pd.read_csv(url_file)
                url_map = dict(zip(url_df.Filename, url_df.LinkedIn))
            except Exception as e:
                st.warning("CSV Format error. Falling back to single URL.")

        results = []
        progress_bar = st.progress(0)
        status_message = st.empty()
        
        for index, file in enumerate(uploaded_resumes):
            try:
                status_message.info(f"Analyzing {index+1}/{len(uploaded_resumes)}: {file.name}")
                progress_bar.progress((index + 1) / len(uploaded_resumes))
                
                # 1. Extract Text
                reader = PdfReader(file)
                resume_text = ""
                for page in reader.pages:
                    content = page.extract_text()
                    if content:
                        resume_text += content
                
                # 2. Check if PDF is actually readable
                if len(resume_text.strip()) < 10:
                    results.append({"Candidate": file.name, "Score": "0%", "Skill Gaps": "Unreadable PDF (Image/Blank)", "Tip": "Use a text-based PDF"})
                    continue

                # 3. Determine which URL to use
                current_url = url_map.get(file.name, single_linkedin if single_linkedin else "Not Provided")

                # 4. AI Call
                prompt = f"""
                You are a recruitment optimizer. Analyze the Resume and LinkedIn against the JD.
                JD: {jd_text}
                RESUME: {resume_text}
                LINKEDIN: {current_url}

                Strictly return this format:
                SCORE: [0-100]
                GAPS: [Top 3 skills only]
                TIP: [One optimization key point]
                """

                response = model.generate_content(prompt)
                
                # Safety check for empty response
                if not response.text:
                    raise ValueError("Empty AI Response")
                
                res_text = response.text
                
                # 5. Parsing
                score = re.search(r'SCORE:\s*(\d+)', res_text)
                gaps = re.search(r'GAPS:\s*(.*)', res_text)
                tip = re.search(r'TIP:\s*(.*)', res_text)

                results.append({
                    "Candidate": file.name,
                    "Score": f"{score.group(1)}%" if score else "50%",
                    "Critical Skill Gaps": gaps.group(1) if gaps else "Check Requirements",
                    "Optimization Key Point": tip.group(1) if tip else "Ready for review"
                })

                # CRITICAL: Wait to prevent "Error Processing"
                time.sleep(2) 

            except Exception as e:
                results.append({"Candidate": file.name, "Score": "Error", "Skill Gaps": "System Timeout", "Tip": "Try individual upload"})
                time.sleep(2)

        # 6. Final Table
        if results:
            status_message.success("✅ Bulk Analysis Complete!")
            df = pd.DataFrame(results)
            st.subheader("📊 Candidate Optimization Rankings")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # 7. Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full Report (CSV)", data=csv, file_name="AI_Recruitment_Report.csv", use_container_width=True)
