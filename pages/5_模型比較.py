import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all
from src.model import fit_comparison_models, FEATURES, FEATURE_LABELS
import shap

st.set_page_config(page_title="模型比較", layout="wide")
apply_styles()
st.title("模型比較與可解釋性分析（SHAP）")
st.markdown("比較邏輯斯迴歸、隨機森林、XGBoost 三種模型在測試集（20%）上的預測效能，並以 SHAP 解析非線性模型的特徵貢獻。")

@st.cache_data
def get_comparison():
    data = load_all()
    return fit_comparison_models(data)

with st.spinner("訓練三個模型中（首次載入約需 10 秒）..."):
    results, X_all, y_all, scaler = get_comparison()

# ── AUC 指標 ──────────────────────────────────────────────────────────────────
st.subheader("測試集 AUC（Area Under ROC Curve）")
c1, c2, c3 = st.columns(3)
COLORS = {'邏輯斯迴歸': '#1976D2', '隨機森林': '#388E3C', 'XGBoost': '#F57C00'}

c1.metric("邏輯斯迴歸", f"{results['邏輯斯迴歸']['auc']:.4f}")
c2.metric("隨機森林",   f"{results['隨機森林']['auc']:.4f}",
          f"{results['隨機森林']['auc'] - results['邏輯斯迴歸']['auc']:+.4f} vs LR")
c3.metric("XGBoost",   f"{results['XGBoost']['auc']:.4f}",
          f"{results['XGBoost']['auc'] - results['邏輯斯迴歸']['auc']:+.4f} vs LR")
st.caption("AUC 越接近 1 代表模型區分能力越強；以 20% 測試集評估，避免過擬合導致的樂觀估計。")

st.markdown("---")

# ── ROC 曲線 ──────────────────────────────────────────────────────────────────
col_l, col_r = st.columns(2)

with col_l:
    st.subheader("ROC 曲線比較")
    fig_roc = go.Figure()
    for name, res in results.items():
        fig_roc.add_trace(go.Scatter(
            x=res['fpr'], y=res['tpr'], mode='lines',
            name=f"{name}（AUC={res['auc']:.3f}）",
            line=dict(width=2.5, color=COLORS[name]),
        ))
    fig_roc.add_shape(type='line', x0=0, y0=0, x1=1, y1=1,
                      line=dict(dash='dash', color='#9E9E9E', width=1))
    fig_roc.update_layout(
        xaxis_title='False Positive Rate（偽陽性率）',
        yaxis_title='True Positive Rate（真陽性率）',
        height=380, plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(x=0.35, y=0.05),
        margin=dict(l=60, r=20, t=20, b=60),
    )
    fig_roc.update_xaxes(showgrid=True, gridcolor='#E8E8E8', range=[0, 1])
    fig_roc.update_yaxes(showgrid=True, gridcolor='#E8E8E8', range=[0, 1])
    st.plotly_chart(fig_roc, use_container_width=True)

with col_r:
    st.subheader("特徵重要性比較")
    model_sel_imp = st.selectbox("選擇模型", ['隨機森林', 'XGBoost'], key='imp_sel')
    imp_vals = results[model_sel_imp]['model'].feature_importances_
    imp_df = (pd.DataFrame({'特徵': FEATURE_LABELS, '重要性': imp_vals})
              .sort_values('重要性'))

    fig_imp = go.Figure(go.Bar(
        y=imp_df['特徵'], x=imp_df['重要性'], orientation='h',
        marker_color=COLORS[model_sel_imp],
        text=[f"{v:.3f}" for v in imp_df['重要性']],
        textposition='outside',
    ))
    fig_imp.update_layout(
        xaxis_title='特徵重要性（Gini）',
        height=380, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=150, r=60, t=20, b=60),
    )
    fig_imp.update_yaxes(showgrid=False)
    fig_imp.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    st.plotly_chart(fig_imp, use_container_width=True)

st.markdown("---")

# ── SHAP 分析 ─────────────────────────────────────────────────────────────────
st.subheader("SHAP 可解釋性分析")
st.markdown("""
SHAP（SHapley Additive exPlanations）以博弈論為基礎，量化每個特徵對**每一筆預測**的貢獻。
與特徵重要性不同，SHAP 能顯示特徵值的高低如何影響預測方向。
""")

model_sel_shap = st.selectbox("選擇模型進行 SHAP 分析", ['隨機森林', 'XGBoost'], key='shap_sel')

@st.cache_data
def compute_shap(model_name, n_samples=600):
    model   = results[model_name]['model']
    X_input = results[model_name]['X_train']
    idx     = np.random.RandomState(42).choice(len(X_input), min(n_samples, len(X_input)), replace=False)
    X_sub   = X_input[idx]
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X_sub)
    # 舊版 shap 回傳 list[class0, class1]，新版回傳 3D array (samples, features, classes)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[1]
    elif shap_vals.ndim == 3:
        shap_vals = shap_vals[:, :, 1]
    return shap_vals, X_sub

with st.spinner("計算 SHAP 值..."):
    shap_vals, X_sub = compute_shap(model_sel_shap)

shap_tab1, shap_tab2 = st.tabs(["Beeswarm 圖", "SHAP 特徵重要性"])

with shap_tab1:
    st.markdown("每個點代表一筆樣本；橫軸為 SHAP 值（正 = 增加長照使用機率），顏色代表該特徵的數值高低（紅 = 高，藍 = 低）。")

    from sklearn.preprocessing import minmax_scale

    mean_abs_order = np.abs(shap_vals).mean(axis=0).argsort()
    feat_ordered   = [FEATURE_LABELS[i] for i in mean_abs_order]
    shap_ordered   = shap_vals[:, mean_abs_order]
    X_norm         = minmax_scale(X_sub[:, mean_abs_order])

    rng = np.random.RandomState(42)
    fig_bee = go.Figure()
    for i, feat in enumerate(feat_ordered):
        jitter = rng.normal(0, 0.18, len(shap_ordered))
        fig_bee.add_trace(go.Scatter(
            x=shap_ordered[:, i],
            y=np.full(len(shap_ordered), i) + jitter,
            mode='markers',
            marker=dict(
                size=4, opacity=0.55,
                color=X_norm[:, i],
                colorscale='RdBu_r', cmin=0, cmax=1,
            ),
            name=feat, showlegend=False,
            hovertemplate=f'<b>{feat}</b><br>SHAP: %{{x:.4f}}<extra></extra>',
        ))

    fig_bee.add_vline(x=0, line_color='#9E9E9E', line_width=1.2)
    fig_bee.update_layout(
        xaxis_title='SHAP 值',
        yaxis=dict(tickmode='array', tickvals=list(range(len(feat_ordered))), ticktext=feat_ordered),
        height=480, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=160, r=40, t=20, b=60),
    )
    fig_bee.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    fig_bee.update_yaxes(showgrid=False)
    st.plotly_chart(fig_bee, use_container_width=True)

with shap_tab2:
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    shap_imp = (pd.DataFrame({'特徵': FEATURE_LABELS, 'SHAP重要性': mean_abs_shap})
                .sort_values('SHAP重要性'))

    fig_shap_bar = go.Figure(go.Bar(
        y=shap_imp['特徵'], x=shap_imp['SHAP重要性'], orientation='h',
        marker_color=COLORS[model_sel_shap],
        text=[f"{v:.4f}" for v in shap_imp['SHAP重要性']],
        textposition='outside',
    ))
    fig_shap_bar.update_layout(
        xaxis_title='平均 |SHAP 值|',
        height=420, plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=150, r=80, t=20, b=60),
    )
    fig_shap_bar.update_yaxes(showgrid=False)
    fig_shap_bar.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
    st.plotly_chart(fig_shap_bar, use_container_width=True)
    st.caption("平均絕對 SHAP 值越大，代表該特徵對模型預測的整體貢獻越顯著。")