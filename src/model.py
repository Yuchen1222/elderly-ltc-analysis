import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression as SklearnLR
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, roc_curve
import xgboost as xgb

FEATURES = [
    '年齡', '嚴重度', '家庭型態', '子女數', '是否與子女同縣市',
    '低收入身分類別', '有無殘疾', '層數', '是否為無電梯公寓',
    '距離公車站距離', '距離零售商距離', '距離醫院距離', '土壤液化區',
]

FEATURE_ZH = {
    '年齡':           '年齡',
    '嚴重度':         '身心障礙嚴重度',
    '家庭型態':       '家庭型態',
    '子女數':         '子女數',
    '是否與子女同縣市': '是否與子女同縣市',
    '低收入身分類別':  '低收入身分類別',
    '有無殘疾':       '有無殘疾',
    '層數':           '層數',
    '是否為無電梯公寓': '是否為無電梯公寓',
    '距離公車站距離':  '距離公車站',
    '距離零售商距離':  '距離零售商',
    '距離醫院距離':   '距離醫院',
    '土壤液化區':     '土壤液化區',
}

KEY_VARS_ANNUAL = ['年齡', '嚴重度', '低收入身分類別', '是否與子女同縣市', '距離醫院距離']

FEATURE_LABELS = [FEATURE_ZH.get(f, f) for f in FEATURES]


def _impute(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ['距離公車站距離', '距離零售商距離', '距離醫院距離']:
        df[col] = df[col].fillna(df[col].median())
    return df


# ── statsmodels logit (odds ratio analysis) ──────────────────────────────────

def fit(data: pd.DataFrame):
    df = _impute(data[FEATURES + ['是否使用長照服務']])
    X = sm.add_constant(df[FEATURES])
    return sm.Logit(df['是否使用長照服務'], X).fit(disp=False)


def odds_ratios(model) -> pd.DataFrame:
    coef = model.params[1:]
    ci   = model.conf_int().iloc[1:]
    pval = model.pvalues[1:]
    return pd.DataFrame({
        '變數':    [FEATURE_ZH.get(c, c) for c in coef.index],
        '原始欄位': coef.index.tolist(),
        '勝算比':  np.exp(coef.values),
        'CI下限':  np.exp(ci.iloc[:, 0].values),
        'CI上限':  np.exp(ci.iloc[:, 1].values),
        'p值':    pval.values,
        '顯著':   pval.values < 0.05,
    }).sort_values('勝算比', ascending=False).reset_index(drop=True)


def feature_medians(data: pd.DataFrame) -> dict:
    return _impute(data[FEATURES]).median().to_dict()


def predict_prob(model, user_input: dict) -> float:
    row = pd.DataFrame([user_input], columns=FEATURES)
    row = sm.add_constant(row, has_constant='add')
    return float(model.predict(row[model.model.exog_names])[0])


def log_odds_contributions(model, user_input: dict, means: dict) -> pd.DataFrame:
    coef = model.params
    rows = [
        {'變數': FEATURE_ZH.get(f, f),
         '貢獻值': coef[f] * (user_input[f] - means[f])}
        for f in FEATURES
    ]
    return pd.DataFrame(rows).sort_values('貢獻值')


# ── annual OR trends ──────────────────────────────────────────────────────────

def annual_odds_ratios(data: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in sorted(data['年份'].unique()):
        sub   = data[data['年份'] == year]
        or_df = odds_ratios(fit(sub))
        for _, row in or_df[or_df['原始欄位'].isin(KEY_VARS_ANNUAL)].iterrows():
            rows.append({'年份': year, '變數': row['變數'], '勝算比': row['勝算比']})
    return pd.DataFrame(rows)


# ── sklearn model comparison ──────────────────────────────────────────────────

def _prepare_arrays(data: pd.DataFrame):
    df = _impute(data[FEATURES + ['是否使用長照服務']])
    return df[FEATURES].values, df['是否使用長照服務'].values


def fit_comparison_models(data: pd.DataFrame) -> tuple:
    X, y = _prepare_arrays(data)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler   = StandardScaler()
    X_tr_sc  = scaler.fit_transform(X_tr)
    X_te_sc  = scaler.transform(X_te)

    configs = {
        '邏輯斯迴歸': (SklearnLR(max_iter=1000, random_state=42),               X_tr_sc, X_te_sc),
        '隨機森林':   (RandomForestClassifier(200, random_state=42, n_jobs=-1), X_tr,    X_te),
        'XGBoost':   (xgb.XGBClassifier(n_estimators=200, random_state=42,
                                         eval_metric='logloss', verbosity=0),   X_tr,    X_te),
    }

    results = {}
    for name, (model, Xtr, Xte) in configs.items():
        model.fit(Xtr, y_tr)
        y_prob       = model.predict_proba(Xte)[:, 1]
        auc          = roc_auc_score(y_te, y_prob)
        fpr, tpr, _  = roc_curve(y_te, y_prob)
        results[name] = {
            'model':   model,
            'auc':     auc,
            'fpr':     fpr.tolist(),
            'tpr':     tpr.tolist(),
            'X_train': Xtr,
        }

    return results, X, y, scaler