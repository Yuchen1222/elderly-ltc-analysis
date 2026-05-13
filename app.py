import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from src.styles import apply_styles

from src.data_processing import data_exists, load_all, year_stats

st.set_page_config(
    page_title="高齡族群長照分析",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_styles()

if not data_exists():
    st.error("尚未產生資料，請先執行：`python data/generate_data.py`")
    st.stop()

@st.cache_data
def get_summary():
    data  = load_all()
    stats = year_stats(data)
    peak  = stats.loc[stats['使用率'].idxmax()]
    latest = stats[stats['年份'] == 112].iloc[0]
    earliest = stats[stats['年份'] == 108].iloc[0]
    return {
        'n':          len(data),
        'peak_year':  int(peak['年份']),
        'peak_rate':  peak['使用率'],
        'end_rate':   latest['使用率'],
        'start_rate': earliest['使用率'],
    }

s = get_summary()

# ── 標題區 ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1565C0,#1976D2);padding:2rem 2.5rem;border-radius:12px;color:white;margin-bottom:1.5rem">
<div style="font-size:1.8rem;font-weight:700;color:white;line-height:1.3">高齡族群長照使用之時間變化與影響因素分析</div>
<div style="margin:0.5rem 0 0;opacity:0.9;font-size:1rem;color:white">
民國 108–112 年｜銀髮安居模擬資料｜陳祥瑋・陳紀宇・鄭博仁・詹鶴章・黃宇晨
</div>
</div>
""", unsafe_allow_html=True)

# ── 關鍵數字 ──────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("分析樣本數",   f"{s['n']:,} 筆",    "108–112 年四個年度")
c2.metric("使用率高峰",   f"{s['peak_rate']:.1f}%", f"民國 {s['peak_year']} 年")
c3.metric("112 年使用率", f"{s['end_rate']:.1f}%",
          f"{s['end_rate']-s['peak_rate']:+.1f}% 較高峰")
c4.metric("最強影響因子", "身障嚴重度",         "Odds Ratio ≈ 1.61")

st.markdown("---")

# ── 研究背景與故事線 ──────────────────────────────────────────────────────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.subheader("研究背景")
    st.markdown(f"""
台灣已正式邁入**超高齡社會**，65 歲以上人口比例持續上升。
政府自 2017 年起推行「**長照 2.0**」政策，期望透過制度化服務協助失能長者維持生活品質。
然而，長照服務的實際使用率並未隨高齡化單向上升。

本研究發現，使用率於**民國 {s['peak_year']} 年達到 {s['peak_rate']:.1f}% 的高峰**後逐年下降至 {s['end_rate']:.1f}%，
揭示長照「**需求與使用之間的落差**」——即使需求存在，服務未必被使用。

> 影響這個落差的，不只是健康狀況，還有**家庭結構、居住環境、經濟條件**，
> 以及長者是否能順利取得服務資訊。
    """)

    st.info("""
**核心研究問題**
1. 長照使用率如何隨時間變化？是否持續上升？
2. 哪些因素顯著影響高齡者使用長照服務的機率？
3. 不同族群（障礙程度、年齡、家庭型態）的使用差異為何？
    """)

with col_r:
    st.subheader("研究流程")
    st.markdown("""
```
1  資料來源
   銀髮安居模擬資料（108/110/111/112 年）
   共 6,000 筆，13 個預測變數

2  資料處理
   欄位標準化、缺失值處理
   身心障礙程度反轉為「嚴重度」指標

3  統計建模
   邏輯斯迴歸（Logit）
   以「是否使用長照服務」為因變數

4  模型比較
   加入隨機森林、XGBoost
   ROC / AUC 評估 + SHAP 解釋

5  結果視覺化
   年度趨勢、族群比較、個人預測
```
    """)

st.markdown("---")

# ── 四大核心發現 ──────────────────────────────────────────────────────────────
st.subheader("四大核心發現")
f1, f2, f3, f4 = st.columns(4)

with f1:
    st.markdown("""
**使用率呈階段性變化**

長照使用率並非隨高齡化持續上升。
{peak_year} 年達高峰後逐年下降，
顯示制度設計與服務輸送存在瓶頸。
    """.format(peak_year=s['peak_year']))

with f2:
    st.markdown("""
**健康狀況主導需求**

身心障礙嚴重度（OR≈1.61）與年齡（OR≈1.07）
是影響長照使用最顯著的正向因子。
身體功能退化直接驅動正式照護需求。
    """)

with f3:
    st.markdown("""
**家庭支持替代正式照護**

與子女同住或子女在同縣市者，
正式長照使用率相對較低，
顯示非正式照護具有替代效果。
    """)

with f4:
    st.markdown("""
**弱勢族群存在使用落差**

低收入族群即使有補助政策，
長照使用率仍偏低（OR < 1），
反映資訊取得與申請流程的障礙。
    """)

st.markdown("---")

# ── 導覽說明 ──────────────────────────────────────────────────────────────────
st.subheader("分析頁面導覽")
st.markdown("""
| 頁面 | 內容 | 對應研究目的 |
|------|------|-------------|
| 資料探索 | 變數分佈、箱型圖、相關性矩陣 | 了解資料特性與雙變量關係 |
| 趨勢總覽 | 108–112 年使用率折線圖、年齡層分析 | 研究問題 1：時間趨勢 |
| 影響因素分析 | 勝算比圖、年度 OR 趨勢 | 研究問題 2：影響因素 |
| 族群比較 | 五大族群互動趨勢圖 | 研究問題 3：族群差異 |
| 個人預測工具 | 互動預測 + 因素貢獻拆解 | 模型應用展示 |
| 模型比較 | ROC、SHAP 可解釋性分析 | 方法論嚴謹性驗證 |
| 研究結論 | 核心發現、政策建議、參考文獻 | 研究總結 |
""")

st.caption("本研究使用銀髮安居模擬資料，不含個人識別資訊。分析方法與框架可延伸至真實行政資料（如長照資訊系統、健保資料庫）。")