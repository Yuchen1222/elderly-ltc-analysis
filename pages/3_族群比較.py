import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all, FAMILY_LABELS, INCOME_LABELS

st.set_page_config(page_title="族群比較", layout="wide")
apply_styles()
st.title("族群比較：各群體長照使用趨勢")
st.info("""
**本頁分析重點**
本頁回答研究問題三：**不同族群的長照使用差異為何？**
結果顯示，重度障礙者與 85 歲以上族群的使用率顯著高於其他群體，
且所有主要族群均在民國 110 年出現使用高峰，與整體趨勢一致，
顯示使用率的波動是**制度性因素**而非特定族群的個別現象。
""")

@st.cache_data
def get_data():
    df = load_all()
    df['年齡層']    = pd.cut(df['年齡'], bins=[65,75,85,100], labels=['65-74歲','75-84歲','85歲以上'], right=False)
    df['嚴重度分群'] = pd.cut(df['嚴重度'], bins=[0,2,4,7], labels=['輕度(1-2)','中度(3-4)','重度(5-7)'])
    df['子女同縣市'] = df['是否與子女同縣市'].map({1:'同縣市', 0:'不同縣市'})
    df['子女數分群'] = df['子女數'].apply(lambda x: '無子女' if x==0 else ('1人' if x==1 else ('2人' if x==2 else '3人以上')))
    df['家庭型態名'] = df['家庭型態'].map(FAMILY_LABELS)
    return df

data = get_data()
YEARS = sorted(data['年份'].unique())
COLORS = px.colors.qualitative.Set2


def group_trend_fig(df, group_col, title, y_max=None):
    groups = df.groupby(['年份', group_col])['是否使用長照服務'].mean().reset_index()
    groups['使用率'] = groups['是否使用長照服務'] * 100
    cats = [c for c in df[group_col].cat.categories if not pd.isna(c)] if hasattr(df[group_col], 'cat') else sorted(df[group_col].dropna().unique())

    fig = go.Figure()
    for i, cat in enumerate(cats):
        sub = groups[groups[group_col] == cat]
        fig.add_trace(go.Scatter(
            x=sub['年份'], y=sub['使用率'],
            mode='lines+markers',
            name=str(cat),
            line=dict(width=2.5, color=COLORS[i % len(COLORS)]),
            marker=dict(size=8),
        ))

    fig.update_layout(
        title=title,
        xaxis_title="年份（民國）",
        yaxis_title="使用率 (%)",
        xaxis=dict(tickmode='array', tickvals=YEARS),
        yaxis=dict(range=[0, (y_max or 35)]),
        height=320,
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=50, r=20, t=60, b=50),
    )
    fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridcolor='#E8E8E8')
    return fig


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["身心障礙嚴重度", "年齡層", "是否與子女同縣市", "子女數", "家庭型態"]
)

with tab1:
    st.plotly_chart(group_trend_fig(data, '嚴重度分群', "各身心障礙嚴重度之長照使用率"), use_container_width=True)
    st.markdown("""
**解讀：** 重度障礙者（嚴重度 5-7）長照使用率顯著高於其他族群，
且各群體均於民國 110 年出現使用高峰，與整體趨勢一致。
    """)

with tab2:
    st.plotly_chart(group_trend_fig(data, '年齡層', "各年齡層之長照使用率"), use_container_width=True)
    st.markdown("""
**解讀：** 85 歲以上高齡者使用率最高，65-74 歲族群最低，
顯示年齡對長照需求有顯著正向影響（勝算比 ≈ 1.07）。
    """)

with tab3:
    st.plotly_chart(group_trend_fig(data, '子女同縣市', "子女是否同縣市之長照使用率"), use_container_width=True)
    st.markdown("""
**解讀：** 子女住在同縣市的長者，長照使用率略高，
顯示子女的鄰近性有助於協助申請或使用服務。
    """)

with tab4:
    st.plotly_chart(group_trend_fig(data, '子女數分群', "各子女數群體之長照使用率"), use_container_width=True)
    st.markdown("""
**解讀：** 子女數較多時，家庭非正式照護可能替代部分長照服務，
但整體趨勢差異相對不顯著。
    """)

with tab5:
    st.plotly_chart(group_trend_fig(data, '家庭型態名', "各家庭型態之長照使用率"), use_container_width=True)
    st.markdown("""
**解讀：** 獨居長者使用率通常較高，因缺乏家庭非正式照護支持，
需透過正式長照服務補足。
    """)