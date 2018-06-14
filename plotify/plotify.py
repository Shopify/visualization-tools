import warnings

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


def _format_data(df, value, x, plot_by=None, color_by=None):
    # TODO test for no plot_by or color_by
    # TODO use aggregate
    # TODO use index if x is None
    """
    :param df: instance of pandas.DataFrame
    :param x: str column name of x axis values. Default is index
    :param plot_by: list of column names (str). Default is empty list
    :param line_by: list of column names (str) Default is empty list
    :param value: str column name of y axis values
    :return: instance of pandas.DataFrame
    """

    df = df.copy()

    for name in plot_by:
        if _get_column_type(df, name) != 'object':
            warnings.warn("The type of column "+name+"in plot_by will be changed to string")
    for name in color_by:
        if _get_column_type(df, name) != 'object':
            raise Exception("The type of column "+name+"in color_by will be changed to string")
    if plot_by:
        df[plot_by] = df[plot_by].apply(lambda x: x.map(str), axis=1)
        df[SUBPLOT_COLUMN_NAME] = df[plot_by].apply('-'.join, axis=1)
    else:
        df[SUBPLOT_COLUMN_NAME] = ''
            
    if color_by:
        df[color_by] = df[color_by].apply(lambda x: x.map(str), axis=1)
        df[COLOR_BY_COLUMN_NAME] = df[color_by].apply('-'.join, axis=1)
    else:
        df[COLOR_BY_COLUMN_NAME] = ''
 
    if _get_column_cardinality(df_new, SUBPLOT_COLUMN_NAME) > MAX_SUBPLOTS:
        raise Exception('Number of subplots exceeds maximum, MAX_SUBPLOTS = ' + str(MAX_SUBPLOTS))

    if _get_column_cardinality(df_new, COLOR_BY_COLUMN_NAME) > MAX_COLORS:
        raise Exception(
            'Number of colors per plot exceeds maximum, MAX_COLORS = ' + str(MAX_COLORS))

    df_new = df.groupby(['subplot_name', 'color_name', x])[value].sum().reset_index()

    if df_new.size() != df.size():
        warnings.warn(
            "The original table was aggregated to fit the specification and the grain changed.")

    return df_new