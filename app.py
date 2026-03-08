import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
from PyPDF2 import PdfReader

# 1. Page Configuration
st.set_page_config(page_title="AI Profile Aligner Pro", layout="wide", page_icon="🎯")

# Helper: Extract Text from PDF
def extract_pdf_text(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        return "".join([page.extract_text() for page in reader.pages])
    except:
        return ""

# 2. 🛡️ SECURE API LOGIC (Fixes the SecretNotFoundError)
api_key = None

# Check for Streamlit Cloud Secrets first
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except:
    # If not on Cloud, show sidebar input for local testing
    with st.sidebar:
        st.title("🛡️ Admin Access")
        api_key = st.text_input("Enter Gemini API Key (Local Testing)", type="password")
        st.info("On the web, this is handled by Cloud Secrets.")

# 3. Main UI Layout
st.title("🎯 AI Smart Profile Aligner")
st.write("Analyze your Resume and LinkedIn against any Job Description.")

col1, col2, col3 = st.columns(3)
with col1:
    jd = st.text_area("Job Description", placeholder="Paste JD here...", height=250)
with col2:
    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    resume_text = extract_pdf_text(uploaded_resume) if uploaded_resume else ""
with col3:
    li_url = st.text_input("LinkedIn URL")
    li_context = st.text_area("About Section (Optional)", height=125)

st.markdown("---")
analyze_button = st.button("🚀 RUN DEEP ANALYSIS", use_container_width=True)

# 4. Analysis Logic
if analyze_button:
    if not api_key:
        st.error("Missing API Key! Please provide one in the sidebar or Cloud Secrets.")
    elif not uploaded_resume or not jd:
        st.warning("Please upload a Resume and paste a Job Description.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            with st.spinner("AI is auditing your career profile..."):
                prompt = f"Analyze: JD: {jd}\nRESUME: {resume_text}\nLINKEDIN: {li_url} {li_context}\nReturn SCORE1: [0-100], SCORE2: [0-100], MISSING_SKILLS: [list], INSIGHTS: [3 points]"
                response = model.generate_content(prompt).text
                
                # Extraction
                s1 = re.search(r'SCORE1:\s*(\d+)', response)
                val1 = int(s1.group(1)) if s1 else 0
                s2 = re.search(r'SCORE2:\s*(\d+)', response)
                val2 = int(s2.group(1)) if s2 else 0

                # Results Display
                st.markdown("---")
                if val1 >= 90:
                    st.success(f"🏆 Perfect Match! Score: {val1}%")
                    st.balloons()
                else:
                    st.error(f"❌ Alignment: {val1}%")

                # 5. Visualizations & Conditional Table
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("📊 Alignment Scores")
                    st.bar_chart(pd.DataFrame({"Metric": ["Match", "Brand"], "Score": [val1, val2]}), x="Metric", y="Score", color="#00A0DC")
                
                if val1 < 90:
                    with c2:
                        st.subheader("⚠️ Skills Gap Table")
                        skills_match = re.search(r'MISSING_SKILLS:(.*?)INSIGHTS', response, re.DOTALL)
                        if skills_match:
                            skills = [s.strip('- ').strip() for s in skills_match.group(1).split('\n') if s.strip()]
                            st.table(pd.DataFrame(skills, columns=["Missing Keywords"]))

                st.subheader("💡 Expert Insights")
                insights_match = re.search(r'INSIGHTS:(.*)', response, re.DOTALL)
                st.write(insights_match.group(1) if insights_match else "Analysis complete.")

        except Exception as e:
            if "429" in str(e):
                st.error("⏳ Rate limit reached! Please wait 20 seconds and try again.")
            else:
                st.error(f"Error: {e}")

st.markdown("<center><small>Built with Gemini 2.5 Flash | v1.0</small></center>", unsafe_allow_html=True)