"""
根據研究報告描述的變數分佈與目標使用率，產生銀髮安居模擬資料。
執行方式：python data/generate_data.py
"""
import numpy as np
import pandas as pd
from scipy.special import expit
from scipy.optimize import brentq
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

YEAR_CONFIGS = [
    (108, 1500, 0.059, 108),
    (110, 1500, 0.180, 110),
    (111, 1500, 0.154, 111),
    (112, 1500, 0.129, 112),
]

TRUE_COEF = {
    'severity':          0.45,
    'age':               0.07,
    'num_children':     -0.03,
    'same_county':       0.07,
    'low_income_cat':   -0.18,
    'has_disability':    0.12,
    'floor_level':       0.02,
    'no_elevator':      -0.08,
    'bus_distance':      0.0001,
    'retailer_distance': 0.00008,
    'hospital_distance':-0.00006,
    'liquefaction_zone':-0.06,
    'family_type':      -0.06,
}


def generate_year_data(year, n_samples, target_rate, seed):
    rng = np.random.RandomState(seed)

    age = np.clip(rng.normal(75, 8, n_samples), 65, 99).astype(int)

    # 身心障礙程度：原始 1=最嚴重，7=最輕微（與報告一致）
    disability_level = rng.choice(
        [1, 2, 3, 4, 5, 6, 7], n_samples,
        p=[0.05, 0.08, 0.12, 0.20, 0.25, 0.20, 0.10]
    )
    severity = 8 - disability_level  # 反轉為嚴重度（7=最嚴重）

    family_type = rng.choice([1, 2, 3, 4], n_samples, p=[0.25, 0.30, 0.30, 0.15])
    num_children = rng.choice([0, 1, 2, 3, 4, 5], n_samples, p=[0.08, 0.15, 0.32, 0.28, 0.12, 0.05])
    same_county = rng.binomial(1, 0.60, n_samples)
    low_income_cat = rng.choice([0, 1, 2, 3], n_samples, p=[0.68, 0.15, 0.10, 0.07])
    has_disability = rng.binomial(1, 0.25, n_samples)
    floor_level = rng.choice(range(1, 16), n_samples)
    base_elevator_prob = np.where(floor_level >= 4, 0.55, 0.15)
    no_elevator = rng.binomial(1, base_elevator_prob).astype(int)

    def sample_distance(pct_missing, scale, low, high):
        vals = rng.exponential(scale, n_samples).clip(low, high).astype(int)
        missing_mask = rng.random(n_samples) < pct_missing
        return np.where(missing_mask, -1, vals)

    bus_dist      = sample_distance(0.05, 400,   50,  3000)
    retailer_dist = sample_distance(0.05, 600,   50,  5000)
    hospital_dist = sample_distance(0.05, 3000, 200, 20000)
    liquefaction  = rng.binomial(1, 0.18, n_samples)

    logit = (
        (age - 75)                                     * TRUE_COEF['age']
        + severity                                     * TRUE_COEF['severity']
        + num_children                                 * TRUE_COEF['num_children']
        + same_county                                  * TRUE_COEF['same_county']
        + low_income_cat                               * TRUE_COEF['low_income_cat']
        + has_disability                               * TRUE_COEF['has_disability']
        + floor_level                                  * TRUE_COEF['floor_level']
        + no_elevator                                  * TRUE_COEF['no_elevator']
        + np.where(bus_dist > 0,      bus_dist,      0) * TRUE_COEF['bus_distance']
        + np.where(retailer_dist > 0, retailer_dist, 0) * TRUE_COEF['retailer_distance']
        + np.where(hospital_dist > 0, hospital_dist, 0) * TRUE_COEF['hospital_distance']
        + liquefaction                                 * TRUE_COEF['liquefaction_zone']
        + family_type                                  * TRUE_COEF['family_type']
    )

    intercept = brentq(lambda c: expit(logit + c).mean() - target_rate, -10, 10)
    use_ltc = rng.binomial(1, expit(logit + intercept))

    return pd.DataFrame({
        'age':                   age,
        'disability_level':      disability_level,
        'family_type':           family_type,
        'num_children':          num_children,
        'same_county':           same_county,
        'low_income_category':   low_income_cat,
        'has_disability_cert':   has_disability,
        'floor_level':           floor_level,
        'no_elevator':           no_elevator,
        'bus_stop_distance':     bus_dist,
        'retailer_distance':     retailer_dist,
        'hospital_distance':     hospital_dist,
        'liquefaction_zone':     liquefaction,
        'use_ltc':               use_ltc,
    })


if __name__ == '__main__':
    for year, n, rate, seed in YEAR_CONFIGS:
        df = generate_year_data(year, n, rate, seed)
        path = os.path.join(OUTPUT_DIR, f'angels_simulation_{year}.csv')
        df.to_csv(path, index=False)
        actual = df['use_ltc'].mean()
        print(f"Year {year}: {len(df):,} rows | usage rate {actual:.3f} (target {rate:.3f})")
    print("Done.")
