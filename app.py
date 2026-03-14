import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Setup Page
st.set_page_config(page_title="Bulk AI Resume Ranker", layout="wide")
st.title("📂 Bulk AI Resume & LinkedIn Aligner")
st.subheader("Analyze multiple candidates against one Job Description")

# 2. Get API Key from Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("API Key not found! Please add GEMINI_API_KEY to Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 3. Sidebar Inputs
    st.sidebar.header("Upload Data")
    jd_text = st.sidebar.text_area("Paste Job Description (JD) here:", height=200)
    
    # ALLOW MULTIPLE FILES
    uploaded_files = st.sidebar.file_uploader("Upload Resumes (PDF)", type="pdf", accept_multiple_files=True)

    if st.sidebar.button("Run Bulk Analysis") and jd_text and uploaded_files:
        results = []
        progress_bar = st.progress(0)
        
        st.write(f"🔍 Analyzing {len(uploaded_files)} resumes...")

        for index, file in enumerate(uploaded_files):
            try:
                # Update Progress
                progress = (index + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                # Step A: Extract Text
                reader = PdfReader(file)
                resume_text = "".join([page.extract_text() for page in reader.pages])

                # Step B: AI Prompt
                prompt = f"""
                Analyze the following Resume against the Job Description (JD).
                JD: {jd_text}
                Resume: {resume_text}

                Return ONLY this format:
                MATCH_SCORE: [0-100]
                MISSING_SKILLS: [skill1, skill2, skill3, skill4, skill5]
                """

                # Step C: Get AI Response
                response = model.generate_content(prompt).text
                
                # Step D: Filter/Parse the results
                score_match = re.search(r'MATCH_SCORE:\s*(\d+)', response)
                skills_match = re.search(r'MISSING_SKILLS:\s*\[(.*?)\]', response)
                
                score = int(score_match.group(1)) if score_match else 0
                skills = skills_match.group(1) if skills_match else "N/A"

                # Save to list
                results.append({
                    "Candidate Name": file.name,
                    "Match Score (%)": score,
                    "Top Missing Skills": skills
                })

                # Small delay to prevent API rate limiting
                time.sleep(2)

            except Exception as e:
                st.warning(f"Could not process {file.name}: {e}")

        # 4. Display Results in a Table
        df = pd.DataFrame(results)
        
        # Sort by best match
        df = df.sort_values(by="Match Score (%)", ascending=False)
        
        st.success("✅ Analysis Complete!")
        st.balloons()
        
        # Show Table
        st.dataframe(df, use_container_width=True)

        # Download Report
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Analysis Report (CSV)", data=csv, file_name="bulk_report.csv", mime="text/csv")

    elif not jd_text or not uploaded_files:
        st.info("Please paste a JD and upload at least one resume to start.")
