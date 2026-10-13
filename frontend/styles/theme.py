import streamlit as st

def apply_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

    :root {
        --bg: #F7F8FC;
        --surface: #FFFFFF;
        --brand: #4338CA;
        --brand-strong: #312E81;
        --teal: #0F766E;
        --text: #172033;
        --muted: #475569;
        --border: #CBD5E1;
        --focus: #F59E0B;
        --danger: #B91C1C;
        --warning: #92400E;
        --success: #166534;
    }

    * { font-family: 'Inter', sans-serif; }

    /* Main background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f7f9ff 0%, #eef3ff 100%);
        color: #0f172a;
    }
    .stApp {
        background: linear-gradient(180deg, #f7f9ff 0%, #eef3ff 100%);
    }
    main .block-container {
        max-width: 1360px;
        padding-top: 0.5rem;
        padding-bottom: 1rem;
    }
    [data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #1e293b 100%);
        border-right: none;
        box-shadow: 10px 0 30px rgba(15, 23, 42, 0.18);
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 3px 0;
        display: block;
        transition: all 0.2s;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.25);
    }

    /* Hero section */
    .hero-section {
        background: linear-gradient(135deg, #1a3a8f 0%, #2563eb 50%, #3b82f6 100%);
        border-radius: 20px;
        padding: 50px 40px;
        margin-bottom: 30px;
        position: relative;
        overflow: hidden;
    }
    .hero-section::after {
        content: '';
        position: absolute;
        bottom: -30px;
        left: 0;
        right: 0;
        height: 60px;
        background: #f0f4ff;
        border-radius: 50% 50% 0 0 / 100% 100% 0 0;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 900;
        color: white;
        line-height: 1.1;
        margin: 0;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: rgba(255,255,255,0.8);
        margin: 10px 0 25px 0;
    }

    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(26,58,143,0.1);
        border-top: 4px solid #2563eb;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-4px); }
    .metric-card h2 {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1a3a8f;
        margin: 0;
    }
    .metric-card p {
        color: #64748b;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 5px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Task cards */
    .task-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        margin: 8px 0;
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        transition: all 0.2s;
    }
    .task-card:hover { transform: translateX(4px); }
    .task-card.overdue { border-left-color: #ef4444; background: #fff5f5; }
    .task-card.due-soon { border-left-color: #f59e0b; background: #fffbeb; }
    .task-card.on-track { border-left-color: #10b981; background: #f0fdf4; }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1a3a8f, #2563eb);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(37,99,235,0.4);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(37,99,235,0.5);
    }

    /* Page header */
    .page-header {
        background: linear-gradient(135deg, #1a3a8f, #2563eb);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 28px;
        box-shadow: 0 8px 30px rgba(26,58,143,0.3);
    }
    .page-header h1 {
        color: white;
        font-size: 2rem;
        font-weight: 900;
        margin: 0;
    }
    .page-header p {
        color: rgba(255,255,255,0.75);
        margin: 6px 0 0 0;
        font-size: 0.95rem;
    }

    /* Section cards */
    .section-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    .section-card h3 {
        color: #1a3a8f;
        font-weight: 800;
        margin-bottom: 16px;
        font-size: 1.2rem;
    }

    /* Notification banner */
    .notif-banner {
        background: linear-gradient(135deg, #eff6ff, #dbeafe);
        border: 2px solid #2563eb;
        border-radius: 12px;
        padding: 14px 20px;
        margin: 8px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Calendar cells */
    .cal-day-header {
        background: linear-gradient(135deg, #1a3a8f, #2563eb);
        color: white;
        padding: 10px;
        border-radius: 10px 10px 0 0;
        text-align: center;
        font-weight: 700;
    }
    .cal-day-body {
        background: white;
        border: 2px solid #e2e8f0;
        border-top: none;
        border-radius: 0 0 10px 10px;
        padding: 8px;
        min-height: 100px;
    }
    .cal-task-pill {
        background: #2563eb;
        color: white;
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 0.72rem;
        margin: 3px 0;
        font-weight: 600;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .cal-task-pill.overdue { background: #ef4444; }
    .cal-task-pill.due-soon { background: #f59e0b; }
    .cal-task-pill.on-track { background: #10b981; }

    /* Auth pages */
    .st-key-auth-shell {
        width: min(1040px, 100%);
        margin: 0 auto;
        padding: clamp(10px, 2.5vh, 24px) 0 0;
    }
    .st-key-auth-shell [data-testid="stHorizontalBlock"] {
        align-items: stretch;
        gap: 1.1rem;
    }
    .st-key-auth-brand {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 54%, #3b82f6 100%);
        border-radius: 26px;
        padding: 30px 32px;
        color: white;
        box-shadow: 0 18px 45px rgba(37,99,235,0.22);
        min-height: 410px;
        height: 100%;
    }
    .st-key-auth-brand [data-testid="stVerticalBlock"] {
        justify-content: center;
        gap: 0.45rem;
    }
    .st-key-auth-brand .brand-badge {
        width: 58px;
        height: 58px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255,255,255,0.16);
        font-size: 1.6rem;
        font-weight: 900;
        margin-bottom: 20px;
    }
    .st-key-auth-brand h1 {
        margin: 0;
        font-size: 2.3rem;
        color: white;
        font-weight: 900;
        letter-spacing: -0.04em;
    }
    .st-key-auth-brand p {
        color: rgba(255,255,255,0.86);
        font-size: 1rem;
        margin: 12px 0 16px;
        line-height: 1.6;
    }
    .st-key-auth-brand .feature-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 10px;
        font-weight: 600;
    }
    .st-key-auth-brand .feature-list li {
        background: rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 10px 12px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .st-key-auth-card {
        background: rgba(255,255,255,0.97);
        border-radius: 24px;
        padding: 26px 30px;
        box-shadow: 0 18px 40px rgba(15,23,42,0.08);
        min-height: 410px;
        height: 100%;
        border: 1px solid rgba(148, 163, 184, 0.18);
    }
    .st-key-auth-card [data-testid="stVerticalBlock"] {
        gap: 0.55rem;
    }
    .auth-heading {
        margin-bottom: 0.25rem;
    }
    .auth-heading span {
        color: #2563eb;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.14em;
    }
    .auth-heading h1 {
        color: #0f172a;
        font-size: 2rem;
        font-weight: 850;
        letter-spacing: -0.045em;
        line-height: 1.15;
        margin: 0.25rem 0 0.35rem;
    }
    .auth-heading p {
        color: #64748b;
        font-size: 0.92rem;
        margin: 0;
    }
    .st-key-auth-card [data-testid="stWidgetLabel"] p {
        color: #334155 !important;
        font-weight: 650;
    }
    .st-key-auth-card input {
        color: #0f172a !important;
        background: #f8fbff !important;
    }
    .st-key-auth-card [data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
        color: #ffffff !important;
        border: 0 !important;
        min-height: 46px;
        box-shadow: 0 8px 18px rgba(37,99,235,0.22) !important;
    }
    .auth-divider {
        height: 1px;
        background: #e8edf5;
        margin: 0.55rem 0 0.75rem;
    }
    .auth-footer-label {
        color: #64748b;
        text-align: center;
        font-size: 0.86rem;
        margin-bottom: 0.35rem;
    }
    .st-key-auth-switch button {
        background: #eff6ff !important;
        color: #1d4ed8 !important;
        border: 1px solid #dbeafe !important;
        box-shadow: none !important;
    }
    .st-key-auth-switch button:hover {
        background: #dbeafe !important;
        border-color: #bfdbfe !important;
        transform: none !important;
    }
    .login-container {
        max-width: 420px;
        margin: 0 auto;
        background: white;
        border-radius: 20px;
        padding: 40px;
        box-shadow: 0 20px 60px rgba(26,58,143,0.15);
        border-top: 6px solid #2563eb;
    }
    .login-title {
        font-size: 2rem;
        font-weight: 900;
        color: #1a3a8f;
        text-align: center;
        margin-bottom: 8px;
    }

    /* Badge */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-blue { background: #dbeafe; color: #1d4ed8; }
    .badge-green { background: #d1fae5; color: #065f46; }
    .badge-red { background: #fee2e2; color: #991b1b; }
    .badge-yellow { background: #fef3c7; color: #92400e; }

    /* Progress bar */
    .progress-container {
        background: #e2e8f0;
        border-radius: 50px;
        height: 16px;
        overflow: hidden;
        margin: 8px 0;
    }
    .progress-bar {
        height: 100%;
        border-radius: 50px;
        background: linear-gradient(90deg, #1a3a8f, #3b82f6);
        transition: width 0.5s ease;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }

    /* Alerts */
    [data-testid="stAlert"] {
        border-radius: 12px;
        border: none;
        font-weight: 600;
    }

    /* Input fields */
    [data-testid="stTextInput"] input,
    [data-testid="stSelectbox"] select,
    [data-testid="stTextarea"] textarea {
        border-radius: 12px;
        border: 1.5px solid #dfe7f5;
        padding: 10px 12px;
        font-size: 0.95rem;
        width: 100%;
        background: #f8fbff;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextarea"] textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
    }
    .stForm {
        gap: 0.7rem;
    }

    /* Sidebar app name */
    .sidebar-brand {
        text-align: center;
        padding: 25px 15px 20px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        margin-bottom: 15px;
    }
    .sidebar-brand h1 {
        font-size: 1.6rem;
        font-weight: 900;
        color: white;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .sidebar-brand p {
        color: rgba(255,255,255,0.6);
        font-size: 0.78rem;
        margin: 4px 0 0 0;
    }

    /* User card in sidebar */
    .sidebar-user {
        background: rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 12px 15px;
        margin: 10px 0 20px 0;
        text-align: center;
    }

    /* Accessible token overrides. Each foreground/background pair meets
       normal-text contrast requirements without relying on colour alone. */
    [data-testid="stAppViewContainer"], .stApp { background: var(--bg); color: var(--text); }
    [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] { color: var(--text); }
    .page-header, .hero-section { background: linear-gradient(135deg, var(--brand-strong), var(--brand)); }
    .page-header p, .hero-subtitle { color: #F8FAFC; }
    .section-card, .metric-card, .task-card, .cal-day-body { background: var(--surface); border: 1px solid var(--border); }
    .section-card h3, .metric-card h2, .login-title { color: var(--brand-strong); }
    .metric-card p, .auth-heading p, .auth-footer-label { color: var(--muted); }
    .stButton > button, .st-key-auth-card [data-testid="stFormSubmitButton"] button {
        background: var(--brand) !important; color: #FFFFFF !important; box-shadow: 0 2px 8px rgba(67,56,202,.25) !important;
    }
    .stButton > button:hover, .stButton > button:focus-visible { background: var(--brand-strong) !important; }
    .stButton > button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
        outline: 3px solid var(--focus) !important; outline-offset: 2px;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextarea"] textarea, [data-testid="stSelectbox"] select {
        color: var(--text) !important; background: #FFFFFF !important; border-color: #94A3B8 !important;
    }
    .cal-day-header, .cal-task-pill { background: var(--brand-strong); color: #FFFFFF; }
    .cal-task-pill.on-track { background: var(--success); }
    .cal-task-pill.due-soon { background: var(--warning); }
    .cal-task-pill.overdue { background: var(--danger); }
    .task-card.overdue { border-left-color: var(--danger); background: #FEF2F2; }
    .task-card.due-soon { border-left-color: var(--warning); background: #FFFBEB; }
    .task-card.on-track { border-left-color: var(--success); background: #F0FDF4; }
    .badge-blue { background: #E0E7FF; color: #312E81; }
    .badge-green { background: #DCFCE7; color: #166534; }
    .badge-red { background: #FEE2E2; color: #991B1B; }
    .badge-yellow { background: #FEF3C7; color: #78350F; }

    @media (max-width: 760px) {
        .st-key-auth-shell {
            width: 100%;
            padding: 0.25rem 0.25rem 1rem;
        }
        .st-key-auth-shell [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        .st-key-auth-brand {
            min-height: 0;
            padding: 22px 24px;
        }
        .st-key-auth-card {
            min-height: 0;
            padding: 22px 22px;
        }
        .st-key-auth-brand .feature-list {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def page_header(title, subtitle, icon):
    st.markdown(f"""
    <div class='page-header'>
        <h1>{icon} {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

