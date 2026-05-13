import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Metric 卡片 ───────────────────────────────────── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1px solid #DBEAFE;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 10px rgba(21,101,192,0.07);
    transition: box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 4px 16px rgba(21,101,192,0.13);
}
[data-testid="stMetricLabel"] {
    font-weight: 600 !important;
    color: #64748B !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricValue"] {
    color: #1565C0 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* ── 側邊欄 ────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #EFF6FF 0%, #F0F4F8 100%) !important;
    border-right: 1px solid #DBEAFE;
}
[data-testid="stSidebarNav"] {
    padding-top: 0.5rem;
}
[data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 2px 6px;
    font-weight: 500;
    transition: background 0.15s;
}
[data-testid="stSidebarNav"] a:hover {
    background: #DBEAFE !important;
}
[data-testid="stSidebarNav"] a[aria-selected="true"] {
    background: #1565C0 !important;
    color: white !important;
}

/* ── Tabs ──────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 2px solid #E0E7EF;
    padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 22px;
    font-weight: 500;
    color: #64748B;
    border: 1px solid transparent;
    border-bottom: none;
}
.stTabs [aria-selected="true"] {
    background: #EFF6FF !important;
    color: #1565C0 !important;
    border-color: #DBEAFE !important;
    border-bottom-color: #EFF6FF !important;
}

/* ── Alert / Info 框 ──────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-width: 1px !important;
}

/* ── Expander ─────────────────────────────────────── */
details summary {
    border-radius: 8px;
    font-weight: 500;
    padding: 0.6rem 1rem;
}
details[open] summary {
    border-radius: 8px 8px 0 0;
    background: #EFF6FF;
    color: #1565C0;
}

/* ── Buttons ──────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(21,101,192,0.22) !important;
}

/* ── Dataframe ────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #E0E7EF !important;
}

/* ── 標題顏色 ──────────────────────────────────────── */
h1 { color: #1A1A2E; font-weight: 700 !important; }
h2 { color: #1565C0 !important; font-weight: 600 !important; }
h3 { color: #1E3A5F !important; font-weight: 600 !important; }

/* ── 主要內容區塊 ──────────────────────────────────── */
.main .block-container {
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* ── 隱藏 Streamlit 預設底部 ───────────────────────── */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>
"""

_SIDEBAR_HEADER = """
<div style="
    background:linear-gradient(135deg,#1565C0,#1976D2);
    border-radius:10px;
    padding:0.9rem 1rem;
    margin-bottom:1rem;
    color:white;
    text-align:center
">
  <div style="font-weight:700;font-size:0.95rem;line-height:1.4">
    高齡族群長照分析
  </div>
  <div style="font-size:0.75rem;opacity:0.85;margin-top:0.2rem">
    108–112 年 ｜ 研究展示系統
  </div>
</div>
"""


def apply_styles():
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(_SIDEBAR_HEADER, unsafe_allow_html=True)