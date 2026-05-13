import os
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

RENAME = {
    'age':                '年齡',
    'disability_level':   '身心障礙程度',
    'family_type':        '家庭型態',
    'num_children':       '子女數',
    'same_county':        '是否與子女同縣市',
    'low_income_category':'低收入身分類別',
    'has_disability_cert':'有無殘疾',
    'floor_level':        '層數',
    'no_elevator':        '是否為無電梯公寓',
    'bus_stop_distance':  '距離公車站距離',
    'retailer_distance':  '距離零售商距離',
    'hospital_distance':  '距離醫院距離',
    'liquefaction_zone':  '土壤液化區',
    'use_ltc':            '是否使用長照服務',
}

FAMILY_LABELS   = {1: '獨居', 2: '僅夫妻', 3: '與子女同住', 4: '其他'}
INCOME_LABELS   = {0: '一般戶', 1: '中低收入', 2: '低收入', 3: '極低收入'}
ELEVATOR_LABELS = {0: '有電梯', 1: '無電梯'}

YEARS = [108, 110, 111, 112]


def data_path(year):
    return os.path.join(DATA_DIR, f'angels_simulation_{year}.csv')


def data_exists():
    return all(os.path.exists(data_path(y)) for y in YEARS)


def load_year(year):
    df = pd.read_csv(data_path(year))
    df = df.rename(columns=RENAME)
    df['年份'] = year
    return df


def process(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['嚴重度'] = 8 - df['身心障礙程度']
    for col in ['距離公車站距離', '距離零售商距離', '距離醫院距離']:
        df[col] = df[col].replace(-1, np.nan)
    df['是否使用長照服務'] = df['是否使用長照服務'].astype(int)
    return df


def load_all() -> pd.DataFrame:
    return process(pd.concat([load_year(y) for y in YEARS], ignore_index=True))


def year_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = (
        df.groupby('年份')
        .agg(
            樣本數=('是否使用長照服務', 'count'),
            使用人數=('是否使用長照服務', 'sum'),
            使用率=('是否使用長照服務', 'mean'),
            平均年齡=('年齡', 'mean'),
            平均嚴重度=('嚴重度', 'mean'),
        )
        .reset_index()
    )
    stats['使用率'] *= 100
    return stats