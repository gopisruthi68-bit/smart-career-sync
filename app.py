import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import time
from PyPDF2 import PdfReader

# 1. Page Config
st.set_page_config(page_title="AI Recruitment Tool", layout="wide")

# Custom CSS for Centering and Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 38px !important;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-top: -30px;
    }
    .sub-header {
        font-size: 18px !important;
        color: #6B7280;
        text-align: center;
        margin-bottom: 40px;
    }
    /* Style the table for transparency */
    .stDataFrame {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_input=True)

# Headings
st.markdown('<div class="main-header">AI Recruitment: Transparency and Optimization</div>', unsafe_allow_input=True)
st.markdown('<div class="sub-header">Data-Driven Candidate Alignment & Skill Gap Analysis</div>', unsafe_allow_input=True)

# 2. API Setup
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 API Key Missing! Please add 'GEMINI_API_KEY' to your Streamlit Secrets.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # --- CENTERED INPUT SECTION ---
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.write("### 📥 Input Panel")
        jd_text = st.text_area("Job Description (JD)", placeholder="Paste the job requirements here...", height=150)
        linkedin_url = st.text_input("Candidate LinkedIn URL (Optional)", placeholder="https://linkedin.com/in/username")
        uploaded_files = st.file_uploader("Upload Resumes (Select multiple PDFs)", type="pdf", accept_multiple_files=True)
        
        analyze_btn = st.button("🚀 Analyze & Optimize", use_container_width=True)

    st.divider()

    # 3. Processing Logic
    if analyze_btn and jd_text and uploaded_files:
        results = []
        progress_bar = st.progress(0)
        
        for index, file in enumerate(uploaded_files):
            try:
                # Update UI Progress
                progress = (index + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                # PDF Text Extraction
                reader = PdfReader(file)
                resume_text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])

                # Targeted AI Prompt for Key Points and Skill Gaps
                prompt = f"""
                Analyze this candidate for transparency and optimization.
                JD: {jd_text}
                Resume: {resume_text}
                LinkedIn: {linkedin_url if linkedin_url else "Not provided"}

                Provide the evaluation in this EXACT format:
                SCORE: [0-100]
                SKILL_GAPS: [List only the 3 most critical missing skills]
                KEY_POINTS: [One short bullet point on resume optimization]
                """

                response = model.generate_content(prompt).text
                
                # Parsing results
                score_match = re.search(r'SCORE:\s*(\d+)', response)
                skills_match = re.search(r'SKILL_GAPS:\s*\[(.*?)\]', response)
                points_match = re.search(r'KEY_POINTS:\s*\[(.*?)\]', response)

                results.append({
                    "Candidate": file.name,
                    "Optimization Score": f"{score_match.group(1)}%" if score_match else "0%",
                    "Critical Skill Gaps": skills_match.group(1) if skills_match else "None",
                    "Optimization Key Point": points_match.group(1) if points_match else "Profile looks optimal"
                })

                time.sleep(2) # Protect against API rate limits

            except Exception as e:
                st.error(f"Error processing {file.name}")

        # 4. Results & Download Option
        if results:
            st.balloons()
            df = pd.DataFrame(results)
            
            st.subheader("📊 Candidate Optimization Table")
            # Displaying the table centered and full width
            st.dataframe(df, use_container_width=True, hide_index=True)

            # THE DOWNLOAD OPTION
            st.write("---")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Optimization Report (CSV)",
                data=csv,
                file_name="AI_Recruitment_Report.csv",
                mime="text/csv",
                use_container_width=True
            )

    elif analyze_btn:
        st.warning("⚠️ Please provide both a Job Description and Resumes.")
