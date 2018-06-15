from plotify import _get_column_type, _get_column_cardinality, _format_data, SUBPLOT_COLUMN_NAME,\
    COLOR_BY_COLUMN_NAME
import pandas as pd
import numpy as np
from string import ascii_lowercase, ascii_uppercase

def gen_df():

    df = pd.DataFrame({'dim_1': list(ascii_uppercase[0:10]),
                       'dim_2': list(ascii_lowercase[0:10]),
                       'dim_3': range(0,10),
                       'dim_4': [1,1,1,1, 2,2,2,2, 3,3],
                       'dim_5': ['A', 'A', 'A', 'A', 'B','B','B','B', 'C','C'],
                       'metric_1': range(0,10),
                       'metric_2': np.random.normal(0,2,10),
                       'metric_3': range(0,10)})

    return df

def test_get_column_type():
    df = gen_df()
    cols_to_test = ['dim_1', 'dim_3', 'metric_2']
    expected = ['object', 'int64', 'float64']
    actual = []
    for col in cols_to_test:
        actual.append(_get_column_type(df, col))

    assert expected == actual

def test_get_column_cardinality():
    df = gen_df()
    cols_to_test = ['dim_1', 'dim_3', 'dim_4', 'dim_5']
    expected = [10, 10, 3, 3]
    actual = []
    for col in cols_to_test:
        actual.append(_get_column_cardinality(df, col))

    assert expected == actual

def test_no_plotby_no_colorby():
    df = gen_df()
    actual = _format_data(df, 'metric_1', 'dim_5')
    expected = pd.DataFrame({SUBPLOT_COLUMN_NAME: '',
                           COLOR_BY_COLUMN_NAME: '',
                           'dim_5': ['A','B','C'],
                           'metric_1': [6, 22, 17]})
    assert actual.to_dict() == expected.to_dict()

def test_plotby_no_colorby():
    df = gen_df()
    actual = _format_data(df, 'metric_1', 'dim_1', ['dim_5'])
    expected = pd.DataFrame({SUBPLOT_COLUMN_NAME: df.dim_5,
                           COLOR_BY_COLUMN_NAME: 10*[''],
                           'dim_1': df.dim_1,
                           'metric_1': df.metric_1})

    assert actual.to_dict() == expected.to_dict()

def test_no_plotby_colorby():
    df = gen_df()
    actual = _format_data(df, 'metric_1', 'dim_1', color_by=['dim_5'])
    expected = pd.DataFrame({SUBPLOT_COLUMN_NAME: '',
                             COLOR_BY_COLUMN_NAME: df.dim_5,
                             'dim_1': df.dim_1,
                             'metric_1': df.metric_1})

    assert actual.to_dict() == expected.to_dict()

def test_plotby_colorby():
    df = gen_df()
    actual = _format_data(df, 'metric_1', 'dim_1', ['dim_5'], ['dim_4'])
    expected = pd.DataFrame({SUBPLOT_COLUMN_NAME:df.dim_5,
                             COLOR_BY_COLUMN_NAME: df.dim_4.astype(str),
                             'dim_1': df.dim_1,
                             'metric_1': df.metric_1}).\
        groupby([SUBPLOT_COLUMN_NAME, COLOR_BY_COLUMN_NAME, 'dim_1'])['metric_1'].sum().reset_index()

    assert actual.to_dict() == expected.to_dict()