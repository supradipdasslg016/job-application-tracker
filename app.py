import streamlit as st
import sqlite3
import pandas as pd
from pypdf import PdfReader
import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- DATABASE SETUP ---
def init_admin_db():
    conn = sqlite3.connect('admin_metrics.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            name TEXT,
            age INTEGER,
            hometown TEXT,
            college TEXT,
            degree TEXT,
            grad_year TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_profile_to_admin_db(profile):
    conn = sqlite3.connect('admin_metrics.db')
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO visitor_profiles (timestamp, name, age, hometown, college, degree, grad_year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, profile['name'], profile['age'], profile['hometown'], profile['college'], profile['degree'], profile['grad_year']))
    conn.commit()
    conn.close()

# --- NLP ENGINE ---
def analyze_resume_vs_jd(cv_text, jd_text):
    if not cv_text or not jd_text:
        return 0.0, [], []
    
    corporate_fluff = {
        'experience', 'years', 'role', 'team', 'work', 'working', 'ability', 'skills', 'required',
        'requirements', 'responsibilities', 'successful', 'candidate', 'job', 'description', 'join',
        'environment', 'management', 'managing', 'support', 'business', 'strong', 'excellent',
        'communication', 'track', 'record', 'reporting', 'tasks', 'knowledge', 'understanding'
    }
    
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([jd_text, cv_text])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    auto_score = round(similarity * 10, 1)
    
    jd_vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    jd_matrix = jd_vectorizer.fit_transform([jd_text])
    feature_names = jd_vectorizer.get_feature_names_out()
    scores = jd_matrix.toarray()[0]
    
    top_jd_words = []
    for idx in scores.argsort()[::-1]:
        word = feature_names[idx]
        if len(word) < 3 or word.isdigit() or any(fluff in word.split() for fluff in corporate_fluff):
            continue
        top_jd_words.append(word)
        if len(top_jd_words) >= 10:
            break
            
    matched, missing = [], []
    for word in top_jd_words:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, cv_text):
            matched.append(word.title())
        else:
            missing.append(word.title())
            
    return auto_score, matched, missing

def extract_text_from_pdf(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = "".join([page.extract_text() or "" for page in reader.pages])
        return text.lower()
    except:
        return ""

# --- APPLICATION INIT ---
st.set_page_config(page_title="Job Track SaaS", page_icon="🎯", layout="wide")
init_admin_db()

if 'view_state' not in st.session_state:
    st.session_state.view_state = 'landing'
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'private_apps' not in st.session_state:
    st.session_state.private_apps = []

# --- ROUTING SYSTEM ---

# VIEW 1: LANDING PAGE
if st.session_state.view_state == 'landing':
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem;'>Data Drives the Insights.<br>Insights Build the Product.</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.2rem;'>Stop guessing your application market fit. Run deep NLP parameter matching and instantly upgrade your native LaTeX resume formatting.</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Launch Interactive Tracker Workstation", use_container_width=True, type="primary"):
            st.session_state.view_state = 'onboarding'
            st.rerun()

# VIEW 2: ONBOARDING POPUP DIALOG
elif st.session_state.view_state == 'onboarding':
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.subheader("📋 Complete Your Profile Sandbox Configuration")
        st.write("Please fill in your coordinates to calibrate the dynamic parameters of your customized LaTeX engine.")
        
        with st.form("onboarding_form"):
            name = st.text_input("Full Name*", placeholder="John Doe")
            col_row1, col_row2 = st.columns(2)
            age = col_row1.number_input("Age*", min_value=15, max_value=100, value=24)
            hometown = col_row2.text_input("Hometown / Current City*", placeholder="e.g., Pune, Maharashtra")
            
            college = st.text_input("Current/Last College Name*", placeholder="e.g., Pune Institute of Business Management")
            degree = st.text_input("Pursuing / Completed Degree*", placeholder="e.g., PGDM (Marketing Operations)")
            grad_year = st.text_input("Graduation Timeline Frame*", placeholder="e.g., May 2023 – June 2025")
            
            if st.form_submit_button("Initialize Main Dashboard", type="primary"):
                if not name or not hometown or not college or not degree or not grad_year:
                    st.error("All parameters are strictly mandatory to compile backend structures.")
                else:
                    profile_packet = {
                        'name': name, 'age': int(age), 'hometown': hometown,
                        'college': college, 'degree': degree, 'grad_year': grad_year
                    }
                    st.session_state.user_profile = profile_packet
                    save_profile_to_admin_db(profile_packet)
                    st.session_state.view_state = 'main_app'
                    st.rerun()

# VIEW 3: MAIN APP (PRIVATE WORKSPACE)
elif st.session_state.view_state == 'main_app':
    st.markdown(f"### 👋 Welcome back, {st.session_state.user_profile['name']} | LaTeX Engine Online")
    
    # Hidden Administrator Terminal Doorway in Sidebar
    st.sidebar.title("Configuration Node")
    with st.sidebar.expander("🔑 Secure Admin Gateway"):
        admin_pass = st.text_input("Enter Key", type="password")
        if admin_pass == "admin2026":
            st.success("Access Authorized")
            admin_conn = sqlite3.connect('admin_metrics.db')
            admin_df = pd.read_sql_query("SELECT * FROM visitor_profiles", admin_conn)
            admin_conn.close()
            st.write("**Global Profile Log Database:**")
            st.dataframe(admin_df)
        elif admin_pass:
            st.error("Invalid Administrative Credentials")
            
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["Dashboard & Entries", "Track Application Engine"])
    
    if page == "Dashboard & Entries":
        st.title("📊 Your Private Tracking Environment")
        st.caption("Data here is isolated safely to your local current browser instance tab context.")
        
        if not st.session_state.private_apps:
            st.info("Your application index is empty. Navigate to the tracking engine tab to parse requirements.")
        else:
            df = pd.DataFrame(st.session_state.private_apps)
            col1, col2, col3 = st.columns(3)
            col1.metric("Applications Target Count", len(df))
            col2.metric("Mean Compatibility Match", f"{df['auto_score'].mean():.1f} / 10")
            col3.metric("Primary Segment", df['Domain'].value_counts().index[0])
            
            st.markdown("---")
            st.dataframe(df.drop(columns=['raw_jd', 'latex_source']), use_container_width=True)
            
    elif page == "Track Application Engine":
        st.title("🎯 Structural Parsing Configuration Matrix")
        
        with st.form("application_pipeline_form"):
            col_a, col_b = st.columns(2)
            role = col_a.text_input("Job Role Target Name*", placeholder="e.g., Strategic Product Analyst")
            domain = col_a.text_input("Industry Vertical*", placeholder="e.g., Real Estate, EdTech")
            recruiter = col_b.text_input("Recruiter Point-of-Contact Name")
            linkedin = col_b.text_input("Recruiter Profile URL")
            
            exp_req = st.number_input("Target Experience Metrics", min_value=0, max_value=20, value=2)
            exp_range_calculated = f"{max(0, exp_req - 3)} - {exp_req + 3} Years Limit Profile"
            
            st.markdown("---")
            jd_text_block = st.text_area("Key Responsibility Areas (KRA) Source String*", height=150)
            uploaded_file = st.file_uploader("Upload Core Tracking CV (PDF Format Only)*", type=["pdf"])
            
            if st.form_submit_button("Run Strategic Structural Analysis"):
                if not role or not domain or not jd_text_block or not uploaded_file:
                    st.error("Critical parsing nodes are missing relevant field input validations.")
                else:
                    cv_extracted_text = extract_text_from_pdf(uploaded_file)
                    score, matches, missing = analyze_resume_vs_jd(cv_extracted_text, jd_text_block.lower())
                    
                    matched_string = ", ".join(matches) if matches else "None"
                    missing_string = ", ".join(missing) if missing else "None"
                    
                    # --- NATIVE LATEX SEAMLESS TEMPLATE MATCHING ENGINE ---
                    user = st.session_state.user_profile
                    
                    # Core LaTeX template structural blocks with safe string substitutions
                    latex_template = r"""\documentclass[10pt, letterpaper]{article}

% Packages:
\usepackage[
    ignoreheadfoot, 
    top=2 cm, 
    bottom=2 cm, 
    left=2 cm, 
    right=2 cm, 
    footskip=1.0 cm
]{geometry} 
\usepackage{titlesec} 
\usepackage{tabularx} 
\usepackage{array} 
\usepackage[dvipsnames]{xcolor} 
\definecolor{primaryColor}{RGB}{0, 0, 0} 
\usepackage{enumitem} 
\usepackage{fontawesome5} 
\usepackage{amsmath} 
\usepackage[
    pdftitle={CV},
    pdfauthor={Applicant},
    pdfcreator={LaTeX with RenderCV},
    colorlinks=true,
    urlcolor=primaryColor
]{hyperref} 
\usepackage[pscoord]{eso-pic} 
\usepackage{calc} 
\usepackage{bookmark} 
\usepackage{lastpage} 
\usepackage{changepage} 
\usepackage{paracol} 
\usepackage{ifthen} 
\usepackage{needspace} 
\usepackage{iftex} 

\ifPDFTeX
    \input{glyphtounicode}
    \pdfgentounicode=1
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}
\fi

\usepackage{charter}

\raggedright
\AtBeginEnvironment{adjustwidth}{\partopsep0pt} 
\pagestyle{empty} 
\setcounter{secnumdepth}{0} 
\setlength{\parindent}{0pt} 
\setlength{\topskip}{0pt} 
\setlength{\columnsep}{0.15cm} 
\pagenumbering{gobble} 

\titleformat{\section}{\needspace{4\baselineskip}\bfseries\large}{}{0pt}{}[\vspace{1pt}\titrule]
\titlespacing{\section}{-1pt}{0.4 cm}{0.4 cm}

\renewcommand\labelitemi{$\vcenter{\hbox{\small$\bullet$}}$} 
\newenvironment{highlights}{
    \begin{itemize}[topsep=0.10 cm, parsep=0.10 cm, partopsep=0pt, itemsep=1pt, leftmargin=0 cm + 10pt]
}{
    \end{itemize}
} 

\newenvironment{highlightsforbulletentries}{
    \begin{itemize}[topsep=0.10 cm, parsep=0.10 cm, partopsep=0pt, itemsep=0pt, leftmargin=10pt]
}{
    \end{itemize}
} 

\newenvironment{onecolentry}{
    \begin{adjustwidth}{0 cm + 0.00001 cm}{0 cm + 0.00001 cm}
}{
    \end{adjustwidth}
} 

\newenvironment{twocolentry}[2][]{
    \onecolentry
    \def\secondColumn{#2}
    \setcolumnwidth{\fill, 4.5 cm}
    \begin{paracol}{2}
}{
    \switchcolumn \raggedleft \secondColumn
    \end{paracol}
    \endonecolentry
} 

\begin{document}

    \begin{header}
        \fontsize{40 pt}{40 pt}\selectfont __NAME__

        \vspace{5 pt}

        \normalsize
        \mbox{__HOMETOWN__}%
        \kern 5.0 pt$\vert$\kern 5.0 pt%
        \mbox{\href{mailto:Supradipdasslg016@gmail.com}{Supradipdasslg016@gmail.com}}%
        \kern 5.0 pt$\vert$\kern 5.0 pt%
        \mbox{\href{tel:+91 6289517253}{Phone:+91 6289517253}}%
        \kern 5.0 pt$\vert$\kern 5.0 pt%
        \mbox{\href{https://www.linkedin.com/in/supradip-das016/}{linkedin.com/in/Supradip Das}}%
    \end{header}

    \vspace{5 pt - 0.3 cm}

    \section{Personal Summary}
    \begin{onecolentry}
    Professional Analytics and Strategy Specialist with a proven tracking profile inside the \textbf{__DOMAIN__} sector, specialized in navigating the requirements for high-velocity \textbf{__ROLE__} roles. Highly skilled in translating complex structural datasets into actionable insights, driving target objectives, and optimizing performance matrices across key priority business networks.
    \end{onecolentry}

    \section{Education}
    \begin{twocolentry}{__GRAD_YEAR__}
        \fontsize{11 pt}{11 pt}\textbf{__COLLEGE__}, __DEGREE__
    \end{twocolentry}
    \vspace{0.10 cm}
    \begin{onecolentry}
        \begin{highlights}
            \item \textbf{Metrics:} CGPA: 7.9 / 10.0 Evaluation Framework
            \item \textbf{Coursework:} Marketing Management, Branding, Digital Infrastructure Analytics, Statistical Optimization.
        \end{highlights}
    \end{onecolentry}

    \section{Experience}
    \begin{twocolentry}{Sept 2025 - May 2026}
        \fontsize{11 pt}{11 pt}\textbf{Marketing Manager}, PROPACITY PROPTECH PVT. LTD.
    \end{twocolentry}
    \vspace{0.10 cm}
    \begin{onecolentry}
        \begin{highlights}
            \item Drove over \textbf{200 walk-ins} for both residential and commercial projects by analyzing market trends and consumer behavior, resulting in a total revenue optimization of \textbf{21 crores}.
            \item Cultivated and managed strategic relationships with over \textbf{200 channel partners} across key regional micro-markets to expand sales network parameters.
            __DYNAMIC_EXPERIENCE_BULLET__
        \end{highlights}
    \end{onecolentry}

    \section{Skills Matrix (ATS Parameter Injected)}
    \begin{onecolentry}
        \begin{highlights}
            \item \textbf{Verified Match Skills:} __MATCHED_SKILLS__
            \item \textbf{Target Optimized Competencies:} __MISSING_SKILLS__
            \item \textbf{Core Frameworks:} SQL, Python, Excel, Power BI, Strategic Frameworks, Data Visualization, IBM SPSS, Customer Segmentation.
        \end{highlights}
    \end{onecolentry}

\end{document}"""

                    # Regex token optimization replacement strategy
                    updated_latex = latex_template.replace("__NAME__", user['name'])
                    updated_latex = updated_latex.replace("__HOMETOWN__", user['hometown'])
                    updated_latex = updated_latex.replace("__COLLEGE__", user['college'])
                    updated_latex = updated_latex.replace("__DEGREE__", user['degree'])
                    updated_latex = updated_latex.replace("__GRAD_YEAR__", user['grad_year'])
                    updated_latex = updated_latex.replace("__ROLE__", role)
                    updated_latex = updated_latex.replace("__DOMAIN__", domain)
                    updated_latex = updated_latex.replace("__MATCHED_SKILLS__", matched_string)
                    updated_latex = updated_latex.replace("__MISSING_SKILLS__", missing_string)
                    
                    # Dynamically generate tailored LaTeX bullet points using missing tokens
                    if missing:
                        bullet_txt = f"\\item Spearheaded custom pipeline evaluations using targeted \\textbf{{{missing[0]}}} and \\textbf{{{missing[1] if len(missing)>1 else missing[0]}}} architectures to eliminate process gaps."
                    else:
                        bullet_txt = "\\item Optimized multi-channel operational workflows to maintain robust lead pipeline acquisition standards."
                    updated_latex = updated_latex.replace("__DYNAMIC_EXPERIENCE_BULLET__", bullet_txt)

                    # Save state record
                    app_record = {
                        "Role": role, "Domain": domain, "Recruiter": recruiter, "LinkedIn": linkedin,
                        "Exp Limits": exp_range_calculated, "auto_score": score,
                        "Matched Tokens": matched_string, "Missing Tokens": missing_string, 
                        "raw_jd": jd_text_block, "latex_source": updated_latex
                    }
                    st.session_state.private_apps.append(app_record)
                    
                    st.success("Target Pipeline Executed Successfully!")
                    
                    st.markdown("---")
                    st.subheader("💡 Strategic Action Recommendations & LaTeX Dashboard")
                    
                    col_rec1, col_rec2 = st.columns(2)
                    with col_rec1:
                        st.metric("Algorithmic Match Score", f"{score} / 10")
                        st.info(f"**Identified Target Alignments:**\n{matched_string}")
                        st.warning(f"**Critical Targeting Gaps Discovered:**\n{missing_string}")
                        
                    with col_rec2:
                        st.markdown("### **Next Steps & Upgraded LaTeX Output**")
                        st.markdown("🔥 **SaaS Feature Unlocked:** We have dynamically updated your exact custom LaTeX layout format! The missing target keywords and tailored bullet entries have been structurally injected into the source code matrix.")
                        
                        # Trigger Download Action
                        st.download_button(
                            label="📥 Download Tailored LaTeX Code (.tex File)",
                            data=updated_latex,
                            file_name=f"{user['name'].lower().replace(' ', '_')}_optimized.tex",
                            mime="text/x-tex",
                            use_container_width=True
                        )
                        st.caption("💡 **Execution Guide:** Click download, open the `.tex` file, copy everything, paste it into your workspace on **Overleaf**, and click Recompile for a flawless PDF result.")
                    
                    # Code display preview box
                    st.markdown("### **Source Preview Matrix**")
                    st.code(updated_latex, language="latex")
                    st.balloons()
