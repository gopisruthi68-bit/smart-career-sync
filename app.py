import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader

# -----------------------------
# PAGE SETUP
# -----------------------------
st.set_page_config(page_title="AI Recruitment Pro", layout="wide")

st.title("AI Recruitment Optimizer")
st.markdown("### Resume vs Job Description + LinkedIn Analysis")
st.divider()

# -----------------------------
# GEMINI API SETUP
# -----------------------------
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("🔑 Add GEMINI_API_KEY in Streamlit secrets")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={"temperature":0.7}
)

# -----------------------------
# INPUT SECTION
# -----------------------------
col1, col2, col3 = st.columns([1,2,1])

with col2:

    jd_text = st.text_area(
        "📋 Job Description",
        height=150,
        placeholder="Paste job description here..."
    )

    urls_input = st.text_area(
        "🔗 LinkedIn URLs (optional, one per line)",
        height=100,
        placeholder="https://linkedin.com/in/example"
    )

    uploaded_resumes = st.file_uploader(
        "📄 Upload Resumes (PDF)",
        type="pdf",
        accept_multiple_files=True
    )

    run_btn = st.button("🚀 Run AI Recruitment Analysis", use_container_width=True)

# -----------------------------
# SKILLS DATABASE
# -----------------------------
skills_db = [
    "python","java","sql","docker","aws","spring",
    "kubernetes","machine learning","deep learning",
    "react","node","api","microservices",
    "ci/cd","testing","git","linux"
]

# -----------------------------
# ANALYSIS
# -----------------------------
if run_btn and jd_text and uploaded_resumes:

    url_list = [u.strip() for u in urls_input.split("\n") if u.strip()]

    results = []
    advice_map = {}

    progress = st.progress(0)

    for i, file in enumerate(uploaded_resumes):

        reader = PdfReader(file)

        resume_text = ""

        for page in reader.pages:
            resume_text += page.extract_text() or ""

        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()

        # -----------------------------
        # SKILL DETECTION
        # -----------------------------
        detected_skills = [
            skill for skill in skills_db
            if skill in resume_lower
        ]

        jd_skills = [
            skill for skill in skills_db
            if skill in jd_lower
        ]

        match_count = len(set(detected_skills) & set(jd_skills))
        total_needed = max(len(jd_skills),1)

        score = int((match_count / total_needed) * 100)

        missing = list(set(jd_skills) - set(detected_skills))

        linkedin_url = url_list[i] if i < len(url_list) else "Not Provided"

        # -----------------------------
        # AI ADVICE
        # -----------------------------
        prompt = f"""
You are an expert technical recruiter.

Job Description:
{jd_text[:400]}

Resume Text:
{resume_text[:800]}

Detected Skills:
{detected_skills}

Missing Skills:
{missing}

Give exactly 5 personalized suggestions to improve this candidate's resume
based on missing skills and job description.

Return only numbered points.
"""

        try:

            response = model.generate_content(prompt)
            advice = response.text

        except:

            advice = f"""
1. Add missing skills such as {', '.join(missing[:3])}
2. Improve project descriptions related to {', '.join(detected_skills[:2])}
3. Align resume keywords with the job description
4. Highlight measurable achievements
5. Improve LinkedIn profile summary
"""

        results.append({
            "Candidate": file.name,
            "LinkedIn": linkedin_url,
            "Score": score,
            "Detected Skills": ", ".join(detected_skills),
            "Missing Skills": ", ".join(missing[:5])
        })

        advice_map[file.name] = advice

        progress.progress((i+1)/len(uploaded_resumes))

    st.balloons()

# -----------------------------
# RESULTS TABLE
# -----------------------------
    df = pd.DataFrame(results)

    st.subheader("📊 Candidate Ranking Table")

    st.dataframe(df, use_container_width=True)

# -----------------------------
# SCORE CHART
# -----------------------------
    st.subheader("📈 Candidate Score Chart")

    st.bar_chart(df.set_index("Candidate")["Score"])

# -----------------------------
# RESUME SUGGESTIONS
# -----------------------------
    st.subheader("💡 Resume Optimization Suggestions")

    for name, advice in advice_map.items():

        with st.expander(f"Suggestions for {name}"):

            st.write(advice)

# -----------------------------
# DOWNLOAD REPORT
# -----------------------------
    csv = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Recruitment Report",
        csv,
        "AI_Recruitment_Report.csv",
        "text/csv",
        use_container_width=True
    )

    st.success("✅ AI Analysis Completed!")
