import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all, year_stats

st.set_page_config(page_title="趨勢總覽", layout="wide")
apply_styles()
st.title("長照使用率趨勢總覽（108–112年）")
st.info("""
**本頁分析重點**
本頁回答研究問題一：**長照使用率如何隨時間變化？**
結果顯示，使用率並非隨高齡化持續上升，而在民國 110 年達高峰後逐年下降，
揭示長照「需求－使用落差」的存在，是本研究最核心的發現之一。
""")

@st.cache_data
def get_data():
    return load_all()

data  = get_data()
stats = year_stats(data)

peak = stats.loc[stats['使用率'].idxmax()]
r108 = stats[stats['年份'] == 108].iloc[0]
r112 = stats[stats['年份'] == 112].iloc[0]

# KPI row
c1, c2, c3, c4 = st.columns(4)
c1.metric("總樣本數",    f"{len(data):,}",        f"{data['年份'].nunique()} 個年度")
c2.metric("108年使用率", f"{r108['使用率']:.1f}%")
c3.metric("使用率最高點", f"{peak['使用率']:.1f}%", f"民國 {int(peak['年份'])} 年")
c4.metric("112年使用率", f"{r112['使用率']:.1f}%",
          f"{r112['使用率'] - r108['使用率']:+.1f}%")

st.markdown("---")

# Trend line chart
st.subheader("各年度長照使用率（%）")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=stats['年份'], y=stats['使用率'],
    mode='lines+markers+text',
    line=dict(color='#1976D2', width=3),
    marker=dict(size=12, color='#1976D2'),
    text=[f"{r:.1f}%" for r in stats['使用率']],
    textposition='top center',
    textfont=dict(size=14),
    name='長照使用率',
))

fig.update_layout(
    xaxis_title="年份（民國）",
    yaxis_title="使用率 (%)",
    xaxis=dict(tickmode='array', tickvals=stats['年份'].tolist(), tickfont=dict(size=13)),
    yaxis=dict(range=[0, 22]),
    height=380,
    hovermode='x unified',
    plot_bgcolor='white',
    paper_bgcolor='white',
    margin=dict(l=60, r=40, t=30, b=60),
)
fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
fig.update_yaxes(showgrid=True, gridcolor='#E8E8E8')

st.plotly_chart(fig, use_container_width=True)

# Year-by-year bar chart (sample composition)
st.subheader("各年度樣本統計")

col_l, col_r = st.columns(2)

with col_l:
    display = stats.copy()
    display['使用率'] = display['使用率'].map('{:.1f}%'.format)
    display['平均年齡'] = display['平均年齡'].map('{:.1f}'.format)
    display['平均嚴重度'] = display['平均嚴重度'].map('{:.2f}'.format)
    display.columns = ['年份', '樣本數', '使用長照人數', '使用率', '平均年齡', '平均身障嚴重度']
    st.dataframe(display, use_container_width=True, hide_index=True)

with col_r:
    # Age distribution by year
    year_sel = st.selectbox("選擇年份查看年齡分佈", stats['年份'].tolist())
    sub = data[data['年份'] == year_sel]

    age_bins = [65, 70, 75, 80, 85, 90, 100]
    age_labels = ['65-69', '70-74', '75-79', '80-84', '85-89', '90+']
    sub = sub.copy()
    sub['年齡區間'] = pd.cut(sub['年齡'], bins=age_bins, labels=age_labels, right=False)

    age_rate = (
        sub.groupby('年齡區間', observed=True)['是否使用長照服務']
        .agg(['mean', 'count'])
        .reset_index()
    )
    age_rate['mean'] *= 100

    fig2 = go.Figure(go.Bar(
        x=age_rate['年齡區間'].astype(str),
        y=age_rate['mean'],
        marker_color='#42A5F5',
        text=[f"{v:.1f}%" for v in age_rate['mean']],
        textposition='outside',
    ))
    fig2.update_layout(
        title=f"民國 {year_sel} 年各年齡層長照使用率",
        xaxis_title="年齡層", yaxis_title="使用率 (%)",
        height=300, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=50, r=20, t=40, b=50),
        yaxis=dict(range=[0, max(age_rate['mean']) * 1.25]),
    )
    fig2.update_xaxes(showgrid=False)
    fig2.update_yaxes(showgrid=True, gridcolor='#E8E8E8')
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.success("""
**研究發現：使用率高峰與下降的意義**

長照使用率在民國 110 年達到最高點後下降，這個現象**不代表長照需求減少**。
台灣 65 歲以上人口在同期持續增加，顯示需求仍在，但實際使用未能同步成長。

可能原因包括：疫情後服務輸送調整、申請流程障礙、以及服務量能的限制。
年齡層分析進一步顯示，85 歲以上長者的使用率顯著高於其他群體，
確認年齡是驅動長照需求的關鍵因素（見「影響因素分析」頁面）。
""")