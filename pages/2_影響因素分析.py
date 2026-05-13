import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all
from src.model import fit, odds_ratios, annual_odds_ratios

st.set_page_config(page_title="影響因素分析", layout="wide")
apply_styles()
st.title("影響因素分析（邏輯斯迴歸）")

@st.cache_data
def get_results():
    data   = load_all()
    model  = fit(data)
    or_df  = odds_ratios(model)
    ann_df = annual_odds_ratios(data)
    return data, model, or_df, ann_df

data, model, or_df, ann_df = get_results()

tab_or, tab_annual = st.tabs(["全年度勝算比分析", "年度 OR 趨勢"])

# ── Tab 1: 全年度勝算比 ────────────────────────────────────────────────────────
with tab_or:
    st.markdown("以全年度合併資料建立 Logit 模型，距離變數缺失值以中位數填補。")
    st.subheader("各變數勝算比（Odds Ratio）")
    st.caption("橘色 = 正向影響（OR > 1）；藍色 = 負向影響（OR < 1）；誤差線為 95% CI")

    colors = ['#F57C00' if v >= 1 else '#1976D2' for v in or_df['勝算比']]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=or_df['變數'], x=or_df['勝算比'], orientation='h',
        marker_color=colors,
        error_x=dict(
            type='data', symmetric=False,
            array=(or_df['CI上限'] - or_df['勝算比']).tolist(),
            arrayminus=(or_df['勝算比'] - or_df['CI下限']).tolist(),
            color='#9E9E9E', thickness=2, width=4,
        ),
        text=[f"{v:.3f}" for v in or_df['勝算比']],
        textposition='outside',
    ))
    fig.add_vline(x=1.0, line_dash='dash', line_color='#757575', line_width=1.5)
    fig.update_layout(
        xaxis_title="勝算比 (OR)",
        xaxis=dict(range=[0, max(or_df['CI上限']) * 1.15]),
        height=520,
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=160, r=80, t=20, b=60),
    )
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    st.plotly_chart(fig, use_container_width=True)

    col_l, col_r = st.columns(2)
    for col, condition, title in [
        (col_l, or_df['勝算比'] >= 1, "正向因素（OR > 1）"),
        (col_r, or_df['勝算比'] <  1, "負向因素（OR < 1）"),
    ]:
        with col:
            st.subheader(title)
            sub = or_df[condition][['變數','勝算比','CI下限','CI上限','p值','顯著']].copy()
            for c in ['勝算比','CI下限','CI上限']:
                sub[c] = sub[c].map('{:.3f}'.format)
            sub['p值']  = sub['p值'].map('{:.4f}'.format)
            sub['顯著'] = sub['顯著'].map({True: 'yes', False: ''})
            st.dataframe(sub, use_container_width=True, hide_index=True)

    with st.expander("完整模型摘要（statsmodels 輸出）"):
        st.text(model.summary().as_text())

# ── Tab 2: 年度 OR 趨勢 ───────────────────────────────────────────────────────
with tab_annual:
    st.markdown("""
每個年度分別建立邏輯斯迴歸模型，觀察各關鍵變數的勝算比如何隨時間變化。
變數包括：年齡、身心障礙嚴重度、低收入身分類別、是否與子女同縣市、距離醫院距離。
    """)

    YEARS  = sorted(ann_df['年份'].unique())
    COLORS = px.colors.qualitative.Set1

    fig = go.Figure()
    for i, var in enumerate(ann_df['變數'].unique()):
        sub = ann_df[ann_df['變數'] == var].sort_values('年份')
        fig.add_trace(go.Scatter(
            x=sub['年份'], y=sub['勝算比'],
            mode='lines+markers+text',
            name=var,
            line=dict(width=2.5, color=COLORS[i % len(COLORS)]),
            marker=dict(size=9),
            text=[f"{v:.2f}" for v in sub['勝算比']],
            textposition='top center',
            textfont=dict(size=11),
        ))

    fig.add_hline(y=1.0, line_dash='dash', line_color='#9E9E9E', line_width=1.5,
                  annotation_text="OR = 1（基準線）", annotation_position="right")
    fig.update_layout(
        xaxis_title="年份（民國）",
        yaxis_title="勝算比 (OR)",
        xaxis=dict(tickmode='array', tickvals=YEARS),
        height=430,
        hovermode='x unified',
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02),
        margin=dict(l=60, r=60, t=60, b=60),
    )
    fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    fig.update_yaxes(showgrid=True, gridcolor='#E8E8E8')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("各年度 OR 數值表")
    pivot = ann_df.pivot(index='變數', columns='年份', values='勝算比')
    pivot.columns = [f"民國 {y} 年" for y in pivot.columns]
    pivot = pivot.round(3)
    st.dataframe(pivot, use_container_width=True)
    st.caption("各欄為該年度獨立模型的勝算比；可觀察影響因素的效果是否隨時間有所消長。")