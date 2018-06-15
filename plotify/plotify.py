import warnings
from pandas.api.types import is_numeric_dtype, is_string_dtype

MAX_SUBPLOTS = 20
COLOR_MASTER_LIST = [
    '#3366CC',
    '#DC3912',
    '#FF9900',
    '#109618',
    '#990099',
    '#3B3EAC',
    '#0099C6',
    '#DD4477',
    '#66AA00',
    '#B82E2E',
    '#316395',
    '#994499',
    '#22AA99',
    '#AAAA11',
    '#6633CC',
    '#E67300',
    '#8B0707',
    '#329262',
    '#5574A6',
    '#3B3EAC'
]
MAX_COLORS = len(COLOR_MASTER_LIST)
SUBPLOT_COLUMN_NAME = '__subplot_column_name__'
COLOR_BY_COLUMN_NAME = '__color_by_column_name__'

def _get_column_type(df, column_name):
    """
    :param df: pandas.DataFrame instance
    :param column_name: str column name
    :return: str dtype.name (e.g., 'object', 'int64', 'float64')
    """
    d = df.dtypes
    return d[d.index == column_name].values[0].name


def _get_column_cardinality(df, column_name):
    """

    :param df: pandas.DataFrame instance
    :param column_name: str column name
    :return: int column cardinality
    """

    return df[column_name].nunique()


def _format_data(df, value, x, plot_by=None, color_by=None, aggregate=True):
    # TODO use index if x is None
    """
    :param df: instance of pandas.DataFrame
    :param x: str column name of x axis values. Default is index
    :param plot_by: list of column names (str). Default is empty list
    :param line_by: list of column names (str) Default is empty list
    :param value: str column name of y axis values
    :return: instance of pandas.DataFrame
    """
    
    if not is_numeric_dtype(df[value]):
        message = "The value column " + value + " is not numeric"
        raise Exception(message)

    df = df.copy()
    
    try:
        basestring
    except NameError:
        basestring = str

    if plot_by:
        if isinstance(plot_by, basestring):
            plot_by = [plot_by]
        for name in plot_by:
            if not is_string_dtype(df[name]):
                df[name] = df[name].astype(str)
                message = "The type of column "+name+" in plot_by has been changed to string"
                warnings.warn(message)
        df[SUBPLOT_COLUMN_NAME] = df[plot_by].apply('-'.join, axis=1)
    else:
        df[SUBPLOT_COLUMN_NAME] = ''

    if color_by:
        for name in color_by:
            if isinstance(color_by, basestring):
                color_by = [color_by]
            if not is_string_dtype(df[name]):
                df[name] = df[name].astype(str)
                message = "The type of column "+name+" in color_by has been changed to string"
                warnings.warn(message)
        df[COLOR_BY_COLUMN_NAME] = df[color_by].apply('-'.join, axis=1)
    else:
        df[COLOR_BY_COLUMN_NAME] = ''
 
    if _get_column_cardinality(df, SUBPLOT_COLUMN_NAME) > MAX_SUBPLOTS:
        message = 'Number of subplots exceeds maximum, MAX_SUBPLOTS = ' + str(MAX_SUBPLOTS)
        raise Exception(message)

    if _get_column_cardinality(df, COLOR_BY_COLUMN_NAME) > MAX_COLORS:
        message = 'Number of colors per plot exceeds maximum, MAX_COLORS = ' + str(MAX_COLORS)
        raise Exception(message)

    df_new = df.groupby([SUBPLOT_COLUMN_NAME, COLOR_BY_COLUMN_NAME, x])[value].sum().reset_index()

    if df_new.index.size != df.index.size and not aggregate:
        warnings.warn(
            "The original table was aggregated to fit the specification and the grain changed as a result.")

    return df_new
