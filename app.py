import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Configuration
st.set_page_config(page_title="AI Profile Aligner Pro", layout="wide", page_icon="🎯")

def extract_pdf_text(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        return "".join([page.extract_text() for page in reader.pages])
    except:
        return ""

# 2. Secure API Key Logic
api_key = st.secrets.get("GEMINI_API_KEY") or st.sidebar.text_input("Enter API Key (Local Test)", type="password")

# 3. UI Layout
st.title("🎯 AI Smart Profile Aligner")
st.write("Professional Resume & LinkedIn Audit")

col1, col2, col3 = st.columns(3)
with col1:
    jd = st.text_area("Job Description", placeholder="Paste JD here...", height=250)
with col2:
    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    resume_text = extract_pdf_text(uploaded_resume) if uploaded_resume else ""
with col3:
    li_url = st.text_input("LinkedIn URL")
    li_context = st.text_area("LinkedIn About/Experience", height=150, placeholder="Paste your LinkedIn 'About' text here for better results...")

st.markdown("---")
analyze_button = st.button("🚀 RUN ANALYSIS", use_container_width=True)

if analyze_button:
    if not api_key or not uploaded_resume or not jd:
        st.warning("⚠️ Missing Information: Please provide API Key, Resume, and JD.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            with st.spinner("Analyzing..."):
                # STRICT PROMPT: No compliments, simple words, max 5 skills
                prompt = f"""
                Analyze this Job Description against the Resume and LinkedIn text provided.
                
                JD: {jd}
                RESUME: {resume_text}
                LINKEDIN: {li_context}

                Return ONLY the following structure. Do not include introductory text or compliments.
                SCORE1: [A single number 0-100 representing Resume Match]
                SCORE2: [A single number 0-100 representing LinkedIn Brand Strength]
                MISSING_SKILLS: [Exactly 5 simple keywords missing from the profile, separated by commas]
                KEYPOINTS: [3 short, simple bullet points on how to improve. Max 10 words per bullet]
                """
                
                response = model.generate_content(prompt).text
                
                # --- DATA EXTRACTION ---
                s1 = re.search(r'SCORE1:\s*(\d+)', response)
                score_res = int(s1.group(1)) if s1 else 0
                
                s2 = re.search(r'SCORE2:\s*(\d+)', response)
                score_li = int(s2.group(1)) if s2 else 0

                # --- RESULTS DISPLAY ---
                st.markdown("### 📊 Analysis Results")
                
                # Show Balloons only if score is high
                if score_res >= 70:
                    st.balloons()
                    st.success(f"Match Score: {score_res}%")
                else:
                    st.error(f"Match Score: {score_res}%")

                res_col, skill_col = st.columns([1, 1])
                
                with res_col:
                    st.subheader("Key Improvement Points")
                    points_match = re.search(r'KEYPOINTS:(.*)', response, re.DOTALL)
                    if points_match:
                        st.write(points_match.group(1).strip())

                with skill_col:
                    st.subheader("Top 5 Missing Skills")
                    skills_match = re.search(r'MISSING_SKILLS:(.*?)KEYPOINTS', response, re.DOTALL)
                    if skills_match:
                        skills_list = [s.strip() for s in skills_match.group(1).split(',')]
                        # Ensure only 5 items
                        df_skills = pd.DataFrame(skills_list[:5], columns=["Skill Name"])
                        st.table(df_skills)

                # --- DOWNLOAD OPTION ---
                st.markdown("---")
                report_text = f"AI PROFILE AUDIT REPORT\n\nResume Match: {score_res}%\nLinkedIn Score: {score_li}%\n\nMissing Skills:\n{skills_match.group(1) if skills_match else ''}\n\nImprovement Plan:\n{points_match.group(1) if points_match else ''}"
                
                st.download_button(
                    label="📥 Download Audit Report",
                    data=report_text,
                    file_name="AI_Profile_Audit.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        except Exception as e:
            if "429" in str(e):
                st.error("🚦 Limit Reached. Retrying in 20 seconds...")
                time.sleep(20)
                st.rerun()
            else:
                st.error(f"Error: {e}")

st.markdown("<center><small>Built with Gemini 2.5 Flash | v1.1</small></center>", unsafe_allow_html=True)
