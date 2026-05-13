import streamlit as st
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.styles import apply_styles

from src.data_processing import load_all
from src.model import fit, predict_prob, log_odds_contributions, feature_medians

st.set_page_config(page_title="長照需求評估", layout="wide")
apply_styles()
st.title("長照需求評估系統")

@st.cache_data
def get_model():
    data    = load_all()
    model   = fit(data)
    medians = feature_medians(data)
    return model, medians

model, medians = get_model()

# ── 兩種模式 ──────────────────────────────────────────────────────────────────
mode_tab, research_tab, compare_tab = st.tabs(["長照需求評估（一般民眾）", "研究分析模式（進階）", "雙人情境比較"])


# ════════════════════════════════════════════════════════════════════════════
# 一般民眾模式
# ════════════════════════════════════════════════════════════════════════════
with mode_tab:
    st.markdown("""
此工具協助您初步評估家中長者可能需要長期照顧服務的程度。
**回答以下 5 個問題，約需 1 分鐘。**

> ⚠️ 本工具僅供初步參考，正式申請請撥打 **1966 長照服務專線**由專業人員進行評估。
    """)

    st.markdown("---")

    # ── 問卷 ──────────────────────────────────────────────────────────────
    st.subheader("基本資料")
    col_a, col_b = st.columns(2)
    with col_a:
        age = st.number_input("長者年齡（歲）", min_value=65, max_value=100, value=75, step=1)
    with col_b:
        low_income_raw = st.selectbox(
            "家庭經濟狀況",
            options=[0, 1, 2, 3],
            format_func=lambda x: {0:"一般戶", 1:"中低收入戶", 2:"低收入戶", 3:"極低收入戶"}[x],
            help="低收入戶可獲得更高比例的長照補助"
        )

    st.subheader("身體功能狀況")
    DISABILITY_OPTIONS = {
        "輕度　—　日常生活大致自理，偶爾需要協助（如洗澡、外出）": 2,
        "中度　—　部分日常活動需要他人協助（如穿衣、如廁）": 4,
        "重度　—　多數日常活動需要協助，行動明顯不便": 6,
        "極重度　—　幾乎完全依賴他人照顧，無法自主行動": 7,
    }
    disability_sel = st.radio("請選擇最符合長者現況的描述", list(DISABILITY_OPTIONS.keys()))
    severity = DISABILITY_OPTIONS[disability_sel]
    has_dis  = 1 if severity >= 4 else 0

    st.subheader("居住與家庭狀況")
    LIVING_OPTIONS = {
        "獨居（一個人住，無家人同住）": {
            "家庭型態": 1, "子女數": 0, "是否與子女同縣市": 0},
        "與配偶同住（無子女同住）": {
            "家庭型態": 2, "子女數": 2, "是否與子女同縣市": 0},
        "與子女或其他家人同住": {
            "家庭型態": 3, "子女數": 2, "是否與子女同縣市": 1},
        "子女住附近（同縣市，但不同住）": {
            "家庭型態": 1, "子女數": 2, "是否與子女同縣市": 1},
    }
    living_sel   = st.radio("長者目前的居住情況", list(LIVING_OPTIONS.keys()))
    living_vals  = LIVING_OPTIONS[living_sel]

    col_c, col_d = st.columns(2)
    with col_c:
        elevator_raw = st.radio("住宅是否有電梯", ["有電梯", "無電梯（需爬樓梯）"])
        no_elevator  = 0 if elevator_raw == "有電梯" else 1
    with col_d:
        floor_level  = st.slider("居住樓層", 1, 15, 3)

    # ── 計算預測值 ────────────────────────────────────────────────────────
    user_input = {
        "年齡":           age,
        "嚴重度":         severity,
        "家庭型態":       living_vals["家庭型態"],
        "子女數":         living_vals["子女數"],
        "是否與子女同縣市": living_vals["是否與子女同縣市"],
        "低收入身分類別":  low_income_raw,
        "有無殘疾":       has_dis,
        "層數":           floor_level,
        "是否為無電梯公寓": no_elevator,
        "距離公車站距離":  int(medians["距離公車站距離"]),
        "距離零售商距離":  int(medians["距離零售商距離"]),
        "距離醫院距離":   int(medians["距離醫院距離"]),
        "土壤液化區":     0,
    }
    prob = predict_prob(model, user_input)

    # ── 評估結果 ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("評估結果")

    RISK = (
        ("低度需求",   "#E8F5E9", "#2E7D32", "目前長照需求程度較低",
         ["每 6 個月重新評估一次，隨時注意健康變化",
          "預先了解長照申請流程（撥打 1966 可免費諮詢）",
          "鼓勵長者參與社區活動，維持身心健康",
          "評估住宅安全（防滑、扶手等），預防跌倒"])
        if prob < 0.30 else
        ("中度需求",   "#FFF8E1", "#E65100", "建議盡快進行正式評估",
         ["撥打 1966 預約長照需求評估員上門評估（免費）",
          "了解可申請的居家服務：居家照護、日間照顧中心",
          "若家中有主要照顧者，可申請「喘息服務」",
          "評估住宅無障礙改善需求（補助扶手、防滑設施）"])
        if prob < 0.60 else
        ("高度需求",   "#FFEBEE", "#B71C1C", "建議立即申請長照服務",
         ["**立即撥打 1966**，申請長照需求評估",
          "準備文件：身分證、健保卡、身障手冊（如有）、近期診斷書",
          "可申請服務：居家照護、日照中心、交通接送、輔具租借",
          "低收入戶可獲 90% 補助，一般戶補助 70%，務必告知承辦人員"])
    )

    label, bg, fg, summary, actions = RISK

    pct = int(prob * 100)
    st.markdown(f"""
<div style="background:{bg};border:2px solid {fg};border-radius:12px;padding:1.5rem;margin-bottom:1rem">
  <div style="display:flex;align-items:center;gap:1.5rem">
    <div style="font-size:3.5rem;font-weight:bold;color:{fg};line-height:1">{pct}%</div>
    <div>
      <div style="font-size:1.4rem;font-weight:bold;color:{fg}">{label}</div>
      <div style="font-size:1rem;color:#444;margin-top:0.2rem">{summary}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    col_res, col_act = st.columns([1, 1])

    with col_res:
        st.markdown("**影響此評估結果的主要因素：**")
        contrib_df = log_odds_contributions(model, user_input, medians)
        top_pos = contrib_df[contrib_df["貢獻值"] > 0.05].sort_values("貢獻值", ascending=False).head(3)
        top_neg = contrib_df[contrib_df["貢獻值"] < -0.05].sort_values("貢獻值").head(3)

        if not top_pos.empty:
            st.markdown("**提高需求的因素：**")
            for _, r in top_pos.iterrows():
                st.markdown(f"- {r['變數']}")
        if not top_neg.empty:
            st.markdown("**降低需求的因素：**")
            for _, r in top_neg.iterrows():
                st.markdown(f"- {r['變數']}")

    with col_act:
        st.markdown("**建議採取的行動：**")
        for action in actions:
            st.markdown(f"✅ {action}")

    # ── 服務資源 ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("長照服務資源")
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown("""
**立即諮詢**

📞 **1966 長照服務專線**
- 免費電話，24小時服務
- 可預約評估員上門
- 提供服務說明與申請協助
        """)
    with r2:
        st.markdown("""
**可申請的服務類型**

- 居家照護（護理、復健）
- 日間照顧中心
- 交通接送服務
- 輔具購買/租借補助
- 居家喘息服務
        """)
    with r3:
        st.markdown("""
**補助比例參考**

| 身分 | 自付比例 |
|------|---------|
| 極低收入戶 | 免費 |
| 低收入戶 | 5% |
| 中低收入戶 | 10% |
| 一般戶 | 30% |
        """)


# ════════════════════════════════════════════════════════════════════════════
# 研究分析模式
# ════════════════════════════════════════════════════════════════════════════
with research_tab:
    st.markdown("此模式提供完整的 13 個預測變數輸入，並顯示各因素對預測結果的詳細貢獻分析。")

    PRESETS = {
        "情境 A：獨居重度障礙長者": {
            "年齡": 82, "嚴重度": 6, "家庭型態": 1, "子女數": 0,
            "是否與子女同縣市": 0, "低收入身分類別": 0, "有無殘疾": 1,
            "層數": 5, "是否為無電梯公寓": 1,
            "距離公車站距離": 800, "距離零售商距離": 1200,
            "距離醫院距離": 5000, "土壤液化區": 0,
        },
        "情境 B：有家庭支持的健康高齡者": {
            "年齡": 70, "嚴重度": 2, "家庭型態": 3, "子女數": 2,
            "是否與子女同縣市": 1, "低收入身分類別": 0, "有無殘疾": 0,
            "層數": 2, "是否為無電梯公寓": 0,
            "距離公車站距離": 300, "距離零售商距離": 400,
            "距離醫院距離": 1500, "土壤液化區": 0,
        },
        "情境 C：中度障礙低收入偏遠長者": {
            "年齡": 76, "嚴重度": 4, "家庭型態": 2, "子女數": 1,
            "是否與子女同縣市": 0, "低收入身分類別": 2, "有無殘疾": 1,
            "層數": 3, "是否為無電梯公寓": 0,
            "距離公車站距離": 1500, "距離零售商距離": 2500,
            "距離醫院距離": 12000, "土壤液化區": 0,
        },
        "自訂": None,
    }

    preset_sel = st.selectbox("套用預設情境", list(PRESETS.keys()))
    p = PRESETS[preset_sel] or {k: int(medians.get(k, 0)) for k in PRESETS["情境 A：獨居重度障礙長者"]}

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**基本資料**")
        r_age = st.slider("年齡", 65, 99, p["年齡"], key="r_age")
        r_sev = st.slider("身心障礙嚴重度（1–7）", 1, 7, p["嚴重度"], key="r_sev")
        r_dis = st.selectbox("有無殘疾證明", [0,1], index=p["有無殘疾"],
                             format_func=lambda x: '無' if x==0 else '有', key="r_dis")
    with c2:
        st.markdown("**家庭狀況**")
        r_fam = st.selectbox("家庭型態", [1,2,3,4], index=p["家庭型態"]-1,
            format_func=lambda x: {1:'獨居',2:'僅夫妻',3:'與子女同住',4:'其他'}[x], key="r_fam")
        r_chi = st.slider("子女數", 0, 5, p["子女數"], key="r_chi")
        r_sc  = st.selectbox("子女是否同縣市", [0,1], index=p["是否與子女同縣市"],
            format_func=lambda x: '否' if x==0 else '是', key="r_sc")
        r_inc = st.selectbox("低收入身分類別", [0,1,2,3], index=p["低收入身分類別"],
            format_func=lambda x: {0:'一般戶',1:'中低收入',2:'低收入',3:'極低收入'}[x], key="r_inc")
    with c3:
        st.markdown("**居住環境**")
        r_fl  = st.slider("居住樓層", 1, 15, p["層數"], key="r_fl")
        r_el  = st.selectbox("電梯", [0,1], index=p["是否為無電梯公寓"],
            format_func=lambda x: '有電梯' if x==0 else '無電梯', key="r_el")
        r_liq = st.selectbox("土壤液化區", [0,1], index=p["土壤液化區"],
            format_func=lambda x: '否' if x==0 else '是', key="r_liq")
        r_bus = st.number_input("距公車站(m)", 50, 3000, p["距離公車站距離"], step=50, key="r_bus")
        r_ret = st.number_input("距零售商(m)", 50, 5000, p["距離零售商距離"], step=50, key="r_ret")
        r_hos = st.number_input("距醫院(m)", 200, 20000, p["距離醫院距離"], step=200, key="r_hos")

    r_input = {
        "年齡": r_age, "嚴重度": r_sev, "家庭型態": r_fam, "子女數": r_chi,
        "是否與子女同縣市": r_sc, "低收入身分類別": r_inc, "有無殘疾": r_dis,
        "層數": r_fl, "是否為無電梯公寓": r_el,
        "距離公車站距離": r_bus, "距離零售商距離": r_ret,
        "距離醫院距離": r_hos, "土壤液化區": r_liq,
    }
    r_prob = predict_prob(model, r_input)

    rc1, rc2 = st.columns([1, 2])
    with rc1:
        r_color = '#4CAF50' if r_prob < 0.30 else ('#FF9800' if r_prob < 0.60 else '#F44336')
        gauge = go.Figure(go.Indicator(
            mode='gauge+number',
            value=r_prob * 100,
            number=dict(suffix='%', font=dict(size=40)),
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=r_color, thickness=0.3),
                steps=[
                    dict(range=[0,  30], color='#E8F5E9'),
                    dict(range=[30, 60], color='#FFF8E1'),
                    dict(range=[60,100], color='#FFEBEE'),
                ],
            ),
        ))
        gauge.update_layout(height=240, margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(gauge, use_container_width=True)
        avg = predict_prob(model, medians)
        st.metric("與全體平均差距", f"{(r_prob-avg)*100:+.1f}%", f"全體平均 {avg*100:.1f}%")

    with rc2:
        st.markdown("**各因素貢獻（log-odds，相對於全體平均）**")
        cdf = log_odds_contributions(model, r_input, medians)
        cdf = cdf[cdf["貢獻值"].abs() > 0.001]
        fig = go.Figure(go.Bar(
            y=cdf["變數"], x=cdf["貢獻值"], orientation='h',
            marker_color=['#F57C00' if v > 0 else '#1976D2' for v in cdf["貢獻值"]],
            text=[f"{v:+.3f}" for v in cdf["貢獻值"]], textposition='outside',
        ))
        fig.add_vline(x=0, line_color='#9E9E9E', line_width=1)
        fig.update_layout(height=360, plot_bgcolor='white', paper_bgcolor='white',
                          margin=dict(l=150, r=80, t=10, b=40))
        fig.update_yaxes(showgrid=False)
        fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8')
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# 雙人情境比較
# ════════════════════════════════════════════════════════════════════════════
with compare_tab:
    st.markdown("""
同時輸入兩位長者的特徵，比較長照使用機率與各因素貢獻的差異。
適合用來展示：**政策介入效果**、**不同居住情境的差距**、**家庭支持的影響幅度**。
    """)

    DISABILITY_MAP = {
        "輕度（偶爾需協助）": 2,
        "中度（部分需協助）": 4,
        "重度（多數需協助）": 6,
        "極重度（完全依賴）": 7,
    }
    LIVING_MAP = {
        "獨居":         {"家庭型態": 1, "子女數": 0, "是否與子女同縣市": 0},
        "與配偶同住":   {"家庭型態": 2, "子女數": 2, "是否與子女同縣市": 0},
        "與子女同住":   {"家庭型態": 3, "子女數": 2, "是否與子女同縣市": 1},
        "子女在同縣市": {"家庭型態": 1, "子女數": 2, "是否與子女同縣市": 1},
    }
    INCOME_MAP = {"一般戶": 0, "中低收入戶": 1, "低收入戶": 2, "極低收入戶": 3}

    def person_inputs(suffix, default_age, default_dis, default_liv, default_inc, default_elev):
        age  = st.number_input("年齡", 65, 100, default_age, key=f"cp_age_{suffix}")
        dis  = st.selectbox("身體功能", list(DISABILITY_MAP), index=default_dis, key=f"cp_dis_{suffix}")
        liv  = st.selectbox("居住情況", list(LIVING_MAP), index=default_liv, key=f"cp_liv_{suffix}")
        inc  = st.selectbox("經濟狀況", list(INCOME_MAP), index=default_inc, key=f"cp_inc_{suffix}")
        elev = st.radio("電梯", ["有電梯", "無電梯"], index=default_elev, key=f"cp_elev_{suffix}", horizontal=True)
        lv   = LIVING_MAP[liv]
        return {
            "年齡": age, "嚴重度": DISABILITY_MAP[dis],
            "家庭型態": lv["家庭型態"], "子女數": lv["子女數"],
            "是否與子女同縣市": lv["是否與子女同縣市"],
            "低收入身分類別": INCOME_MAP[inc],
            "有無殘疾": 1 if DISABILITY_MAP[dis] >= 4 else 0,
            "層數": int(medians["層數"]),
            "是否為無電梯公寓": 0 if elev == "有電梯" else 1,
            "距離公車站距離":  int(medians["距離公車站距離"]),
            "距離零售商距離":  int(medians["距離零售商距離"]),
            "距離醫院距離":   int(medians["距離醫院距離"]),
            "土壤液化區": 0,
        }

    col_a, col_sep, col_b = st.columns([5, 1, 5])

    with col_a:
        st.markdown("""
<div style="background:#EFF6FF;border:2px solid #1565C0;border-radius:10px;padding:0.8rem 1rem;margin-bottom:1rem">
<b style="color:#1565C0">情境甲</b>
</div>""", unsafe_allow_html=True)
        inp_a = person_inputs("a", 82, 2, 0, 0, 1)   # 82歲、重度、獨居、一般戶、無電梯

    with col_sep:
        st.markdown("<div style='text-align:center;padding-top:8rem;font-size:2rem;color:#9E9E9E'>vs</div>",
                    unsafe_allow_html=True)

    with col_b:
        st.markdown("""
<div style="background:#F0FDF4;border:2px solid #2E7D32;border-radius:10px;padding:0.8rem 1rem;margin-bottom:1rem">
<b style="color:#2E7D32">情境乙</b>
</div>""", unsafe_allow_html=True)
        inp_b = person_inputs("b", 70, 0, 2, 0, 0)   # 70歲、輕度、與子女同住、一般戶、有電梯

    prob_a = predict_prob(model, inp_a)
    prob_b = predict_prob(model, inp_b)
    diff   = (prob_a - prob_b) * 100

    st.markdown("---")

    # ── 機率比較 ──────────────────────────────────────────────────────────
    st.subheader("預測機率比較")
    m1, m2, m3 = st.columns(3)
    m1.metric("情境甲使用機率", f"{prob_a*100:.1f}%",
              help="依情境甲輸入的特徵預測")
    m2.metric("情境乙使用機率", f"{prob_b*100:.1f}%",
              help="依情境乙輸入的特徵預測")
    delta_label = "甲高於乙" if diff > 0 else "乙高於甲"
    m3.metric("機率差距", f"{abs(diff):.1f}%", f"情境{'甲' if diff > 0 else '乙'}風險較高")

    # ── 機率視覺化 ─────────────────────────────────────────────────────────
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=["情境甲", "情境乙"],
        y=[prob_a * 100, prob_b * 100],
        marker_color=["#1565C0", "#2E7D32"],
        text=[f"{prob_a*100:.1f}%", f"{prob_b*100:.1f}%"],
        textposition="outside",
        textfont=dict(size=16, color=["#1565C0", "#2E7D32"]),
        width=0.4,
    ))
    fig_bar.update_layout(
        yaxis=dict(range=[0, max(prob_a, prob_b) * 130], title="長照使用機率 (%)"),
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=60, r=60, t=20, b=40),
        showlegend=False,
    )
    fig_bar.update_xaxes(showgrid=False)
    fig_bar.update_yaxes(showgrid=True, gridcolor="#E8E8E8")
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── 因素貢獻並排比較 ───────────────────────────────────────────────────
    st.subheader("各因素貢獻比較")
    st.caption("橫軸為 log-odds 貢獻值；兩條並排長條顯示同一因素對兩個情境的影響差異")

    cdf_a = log_odds_contributions(model, inp_a, medians).set_index("變數")["貢獻值"]
    cdf_b = log_odds_contributions(model, inp_b, medians).set_index("變數")["貢獻值"]

    import pandas as pd
    combined = pd.DataFrame({"情境甲": cdf_a, "情境乙": cdf_b})
    combined["差距絕對值"] = (combined["情境甲"] - combined["情境乙"]).abs()
    combined = combined.sort_values("差距絕對值", ascending=True)

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        y=combined.index, x=combined["情境甲"], orientation="h",
        name="情境甲", marker_color="#1565C0", opacity=0.85,
    ))
    fig_cmp.add_trace(go.Bar(
        y=combined.index, x=combined["情境乙"], orientation="h",
        name="情境乙", marker_color="#2E7D32", opacity=0.85,
    ))
    fig_cmp.add_vline(x=0, line_color="#9E9E9E", line_width=1)
    fig_cmp.update_layout(
        barmode="group",
        xaxis_title="log-odds 貢獻值（相對於全體平均）",
        height=480, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=160, r=60, t=20, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig_cmp.update_yaxes(showgrid=False)
    fig_cmp.update_xaxes(showgrid=True, gridcolor="#E8E8E8")
    st.plotly_chart(fig_cmp, use_container_width=True)

    # ── 關鍵差異摘要 ──────────────────────────────────────────────────────
    st.subheader("關鍵差異摘要")
    top_diff = combined.nlargest(3, "差距絕對值")
    for feat in top_diff.index:
        va, vb = combined.loc[feat, "情境甲"], combined.loc[feat, "情境乙"]
        direction = "情境甲明顯較高" if va > vb else "情境乙明顯較高"
        st.markdown(f"- **{feat}**：{direction}（差距 {abs(va-vb):.3f}）")