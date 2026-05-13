import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all, FAMILY_LABELS, INCOME_LABELS

st.set_page_config(page_title="資料探索", layout="wide")
apply_styles()
st.title("資料探索（EDA）")
st.info("""
**本頁分析重點**
在建立預測模型前，先了解資料的基本特性。本頁展示：
- 各變數的**分佈形狀**（是否偏態、異常值？）
- 使用 vs 未使用長照的**群組差異**（箱型圖）
- 各變數與「是否使用長照服務」的**相關係數**（熱圖最右欄）

相關係數的方向與後續邏輯斯迴歸的勝算比（OR > 1 或 < 1）方向一致，可作為交叉驗證。
""")

@st.cache_data
def get_data():
    df = load_all()
    df['家庭型態名'] = df['家庭型態'].map(FAMILY_LABELS)
    df['收入類別名'] = df['低收入身分類別'].map(INCOME_LABELS)
    return df

data = get_data()

# ── 概覽 ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("總樣本數",    f"{len(data):,}")
c2.metric("使用長照人數", f"{data['是否使用長照服務'].sum():,}")
c3.metric("整體使用率",  f"{data['是否使用長照服務'].mean()*100:.1f}%")
miss = data[['距離公車站距離','距離零售商距離','距離醫院距離']].isna().mean().mean()
c4.metric("距離變數缺失率", f"{miss*100:.1f}%")

st.markdown("---")

# ── 三個分析 Tab ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["連續變數分佈", "類別變數分佈", "與長照使用的關係"])

with tab1:
    col_l, col_r = st.columns(2)
    COLOR_MAP = {0: '#90CAF9', 1: '#EF9A9A'}

    with col_l:
        fig = px.histogram(
            data, x='年齡', nbins=30, color='是否使用長照服務',
            barmode='overlay', opacity=0.75,
            color_discrete_map=COLOR_MAP,
            labels={'是否使用長照服務': '使用長照'},
            title="年齡分佈（按長照使用）",
        )
        fig.update_layout(height=320, plot_bgcolor='white', paper_bgcolor='white',
                          legend=dict(title='使用長照', orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        fig = px.histogram(
            data, x='嚴重度', nbins=7, color='是否使用長照服務',
            barmode='overlay', opacity=0.75,
            color_discrete_map=COLOR_MAP,
            labels={'是否使用長照服務': '使用長照'},
            title="身心障礙嚴重度分佈（1=輕微，7=最嚴重）",
        )
        fig.update_layout(height=320, plot_bgcolor='white', paper_bgcolor='white',
                          legend=dict(title='使用長照', orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        fig = px.box(
            data, x='是否使用長照服務', y='年齡',
            color='是否使用長照服務', color_discrete_map=COLOR_MAP,
            labels={'是否使用長照服務': '使用長照', '年齡': '年齡'},
            title="年齡箱型圖（使用 vs 未使用長照）",
        )
        fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white',
                          showlegend=False)
        fig.update_xaxes(ticktext=['未使用','使用'], tickvals=[0, 1])
        st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        fig = px.box(
            data, x='是否使用長照服務', y='嚴重度',
            color='是否使用長照服務', color_discrete_map=COLOR_MAP,
            labels={'是否使用長照服務': '使用長照', '嚴重度': '嚴重度'},
            title="嚴重度箱型圖（使用 vs 未使用長照）",
        )
        fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white',
                          showlegend=False)
        fig.update_xaxes(ticktext=['未使用','使用'], tickvals=[0, 1])
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_l, col_r = st.columns(2)

    with col_l:
        cnt = data['家庭型態名'].value_counts().reset_index()
        cnt.columns = ['家庭型態', '人數']
        fig = px.bar(cnt, x='家庭型態', y='人數', title="家庭型態分佈",
                     color='家庭型態', color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white',
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        cnt2 = data['收入類別名'].value_counts().reset_index()
        cnt2.columns = ['類別', '人數']
        fig = px.bar(cnt2, x='類別', y='人數', title="低收入身分類別分佈",
                     color='類別', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white',
                          showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        cnt3 = data['子女數'].value_counts().sort_index().reset_index()
        cnt3.columns = ['子女數', '人數']
        fig = px.bar(cnt3, x='子女數', y='人數', title="子女數分佈",
                     color_discrete_sequence=['#42A5F5'])
        fig.update_layout(height=300, plot_bgcolor='white', paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with col_r2:
        elev = data['是否為無電梯公寓'].value_counts().reset_index()
        elev.columns = ['類型', '人數']
        elev['類型'] = elev['類型'].map({0: '有電梯', 1: '無電梯'})
        fig = px.pie(elev, names='類型', values='人數', title="住宅電梯比例",
                     color_discrete_sequence=['#66BB6A', '#EF5350'])
        fig.update_layout(height=300, paper_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    col_l, col_r = st.columns(2)

    with col_l:
        sev_rate = (data.groupby('嚴重度')['是否使用長照服務']
                    .mean().reset_index())
        sev_rate['使用率'] = sev_rate['是否使用長照服務'] * 100
        fig = px.bar(sev_rate, x='嚴重度', y='使用率',
                     title="各嚴重度長照使用率 (%)",
                     color='使用率', color_continuous_scale='Oranges',
                     text=sev_rate['使用率'].map('{:.1f}%'.format))
        fig.update_traces(textposition='outside')
        fig.update_layout(height=320, plot_bgcolor='white', paper_bgcolor='white',
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        age_bins = [65, 70, 75, 80, 85, 90, 100]
        age_labels = ['65-69', '70-74', '75-79', '80-84', '85-89', '90+']
        tmp = data.copy()
        tmp['年齡層'] = pd.cut(tmp['年齡'], bins=age_bins, labels=age_labels, right=False)
        age_rate = (tmp.groupby('年齡層', observed=True)['是否使用長照服務']
                    .mean().reset_index())
        age_rate['使用率'] = age_rate['是否使用長照服務'] * 100
        fig = px.bar(age_rate, x='年齡層', y='使用率',
                     title="各年齡層長照使用率 (%)",
                     color='使用率', color_continuous_scale='Blues',
                     text=age_rate['使用率'].map('{:.1f}%'.format))
        fig.update_traces(textposition='outside')
        fig.update_layout(height=320, plot_bgcolor='white', paper_bgcolor='white',
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    # Correlation heatmap
    st.subheader("變數相關性矩陣（皮爾森）")
    corr_cols = ['年齡', '嚴重度', '子女數', '是否與子女同縣市', '低收入身分類別',
                 '層數', '是否為無電梯公寓', '土壤液化區', '是否使用長照服務']
    corr = data[corr_cols].corr()

    fig = px.imshow(
        corr, text_auto='.2f', aspect='auto',
        color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
        title="相關係數矩陣（最右欄 / 最下列為目標變數）",
    )
    fig.update_layout(height=460, paper_bgcolor='white')
    st.plotly_chart(fig, use_container_width=True)
    st.caption("與「是否使用長照服務」欄位的相關係數可看出各變數的預測方向（正值 = 正向影響，負值 = 負向影響）。")