import streamlit as st
import sqlite3
import pandas as pd
from pypdf import PdfReader
import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('job_tracker.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_role TEXT,
            domain TEXT,
            kra TEXT,
            app_date TEXT,
            recruiter_name TEXT,
            recruiter_linkedin TEXT,
            exp_required INTEGER,
            exp_range TEXT,
            auto_fit_score REAL,
            manual_fit_score REAL,
            matched_keywords TEXT,
            missing_keywords TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(data):
    conn = sqlite3.connect('job_tracker.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO applications (
            job_role, domain, kra, app_date, recruiter_name, 
            recruiter_linkedin, exp_required, exp_range, 
            auto_fit_score, manual_fit_score, matched_keywords, missing_keywords
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('job_tracker.db')
    df = pd.read_sql_query("SELECT * FROM applications ORDER BY id DESC", conn)
    conn.close()
    return df

# --- NLP & TEXT ANALYSIS ENGINE ---
def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.lower()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def analyze_resume_vs_jd(cv_text, jd_text):
    if not cv_text or not jd_text:
        return 0.0, [], []
    
    # 1. Calculate automated fit score using Cosine Similarity (TF-IDF)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([jd_text, cv_text])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    auto_score = round(similarity * 10, 1) # Map to a 0-10 scale
    
    # 2. Extract Top Keywords from JD using TF-IDF ranking
    jd_vectorizer = TfidfVectorizer(stop_words='english')
    jd_matrix = jd_vectorizer.fit_transform([jd_text])
    feature_names = jd_vectorizer.get_feature_names_out()
    scores = jd_matrix.toarray()[0]
    
    # Get top 15 highest scoring meaningful words from the JD
    top_jd_words = [feature_names[i] for i in scores.argsort()[::-1][:15] if len(feature_names[i]) > 2]
    
    # 3. Match keywords against CV text
    matched = []
    missing = []
    for word in top_jd_words:
        # Check for whole word match to avoid substring false positives
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, cv_text):
            matched.append(word)
        else:
            missing.append(word)
            
    return auto_score, matched, missing

# --- APPLICATION INITIALIZATION ---
st.set_page_config(page_title="Job Track Pro", page_icon="💼", layout="wide")
init_db()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 Job Track Pro")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Dashboard & Metrics", "Track New Application"])

# --- PAGE 1: DASHBOARD & METRICS ---
if page == "Dashboard & Metrics":
    st.title("📊 Application Performance Dashboard")
    df = load_data()
    
    if df.empty:
        st.info("No applications tracked yet. Head over to 'Track New Application' to add your first job!")
    else:
        # Key Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Applications", len(df))
        col2.metric("Avg Automated Fit", f"{df['auto_fit_score'].mean():.1f}/10")
        col3.metric("Avg Manual Fit Rating", f"{df['manual_fit_score'].mean():.1f}/10")
        col4.metric("Top Targeting Domain", df['domain'].value_counts().index[0])
        
        st.markdown("---")
        st.subheader("📁 Saved Applications Archive")
        
        # Clean data representation for user readability
        display_df = df.copy()
        display_df = display_df.drop(columns=['kra']) # Drop heavy text column for tabular look
        st.dataframe(display_df, use_container_width=True)

# --- PAGE 2: TRACK NEW APPLICATION FORM ---
elif page == "Track New Application":
    st.title("➕ Track a New Job Application")
    st.markdown("Fill out the structural parameters and upload the target job's KRA to check compatibility instantly.")
    
    # Using form containers for clear structural layouts
    with st.form("application_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_role = st.text_input("Job Role Name*", placeholder="e.g., Product Manager, Market Analyst")
            domain = st.text_input("Domain / Industry*", placeholder="e.g., Real Estate, Fintech, SaaS")
            app_date = st.date_input("Application Date", datetime.date.today())
            
        with col2:
            recruiter_name = st.text_input("Recruiter Name", placeholder="John Doe")
            recruiter_linkedin = st.text_input("Recruiter LinkedIn URL", placeholder="https://linkedin.com/in/...")
            
            # Auto range feature logic
            exp_required = st.number_input("Years of Experience Required*", min_value=0, max_value=30, value=2)
            min_range = max(0, exp_required - 3)
            max_range = exp_required + 3
            exp_range_str = f"{min_range} - {max_range} Years"
            st.caption(f"💡 **Target Applicant Experience Range Based on Inputs:** {exp_range_str}")

        st.markdown("---")
        st.subheader("📝 Job Description & Fit Check Analysis")
        kra = st.text_area("Key Responsibility Areas (KRA) / Job Description*", height=150, placeholder="Paste the text requirements here...")
        
        uploaded_cv = st.file_uploader("Upload your CV (PDF format only) to evaluate compatibility", type=["pdf"])
        
        # Hidden states for parsing calculations inside the form submission loop
        submit_btn = st.form_submit_with_利益 = st.form_submit_button("Run Analysis & Save Application")
        
        if submit_btn:
            if not job_role or not domain or not kra:
                st.error("Please fill in all mandatory fields marked with an asterisk (*).")
            else:
                auto_score = 0.0
                matched_str = "N/A"
                missing_str = "N/A"
                
                # Check for uploaded file compatibility
                if uploaded_cv is not None:
                    with st.spinner("Analyzing match metrics..."):
                        cv_text = extract_text_from_pdf(uploaded_cv)
                        auto_score, matched_words, missing_words = analyze_resume_vs_jd(cv_text, kra.lower())
                        
                        matched_str = ", ".join(matched_words)
                        missing_str = ", ".join(missing_words)
                        
                        # Real-time visual metrics display inside form validation context
                        st.success("Analysis Completed Successfully!")
                        
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("Automated AI Fit Score", f"{auto_score} / 10")
                        
                        with col_m2:
                            st.write("**Top Matching Keywords Found:**")
                            st.info(matched_str if matched_str else "None")
                            st.write("**Crucial Keywords Missing from CV:**")
                            st.warning(missing_str if missing_str else "None")
                else:
                    st.warning("No CV uploaded. Savings metric defaults will apply without match indexing.")

                # Manual override fallback mechanism configuration
                # Streamlit forms process all input values simultaneously on click events
                manual_fit = auto_score 
                
                # Bundle data packet for SQLite persistence layer
                db_payload = (
                    job_role, domain, kra, str(app_date), recruiter_name,
                    recruiter_linkedin, exp_required, exp_range_str,
                    auto_score, manual_fit, matched_str, missing_str
                )
                
                save_to_db(db_payload)
                st.balloons()
                st.success(f"Successfully logged application entry for '{job_role}' inside database archives!")