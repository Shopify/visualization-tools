from __future__ import division

import warnings
import pandas as pd
from pandas.api.types import is_numeric_dtype, is_string_dtype
import numpy as np
import plotly.graph_objs as go
from plotly import tools
from plotly.offline import plot


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
COLOR_COLUMN = '__color__'

try:
    basestring
except NameError:
    basestring = str

def _get_column_type(df, column_name):
    """
    Method that returns the numpy type of a column
    
    :param df: pandas.DataFrame instance
    :param column_name: str column name
    :return: str dtype.name (e.g., 'object', 'int64', 'float64')
    """
    d = df.dtypes
    return d[d.index == column_name].values[0].name


def _get_column_cardinality(df, column_name):
    """
    Method that returns the number of unique elements in a column
    
    :param df: pandas.DataFrame instance
    :param column_name: str column name
    :return: int column cardinality
    """

    return df[column_name].nunique()

def _check_valid_calculation(some_dict):
    try:
        a = isinstance(some_dict['name'], basestring)
    except KeyError:
        raise Exception('the calculation dict is missing a name key-value pair')
    try:
        b = isinstance(some_dict['numerator'], basestring)
    except KeyError:
        raise Exception('the calculation dict is missing a numerator key-value pair')
    try:
        c = isinstance(some_dict['denominator'], basestring)
    except KeyError:
        raise Exception('the calculation dict is missing a denominator key-value pair')

    if not (a and b and c):
        raise Exception('All column name references in the calculation must be strings')

    return True



def _format_data(df, value, x, plot_by=None, color_by=None, aggregate=True):
    # TODO use index if x is None
    """
    Method that takes the original dataframe given by the user and returns
    a formated dataframe that can be manipulated by the _plotify method
    
    :param df: instance of pandas.DataFrame
    :param value: str column name of y axis values or dict with calculation information
    :param x: str column name of x axis values
    :param plot_by: str or list of column names
    :param line_by: str or list of column names
    :return: instance of pandas.DataFrame
    """

    df = df.copy()

    if isinstance(value, dict):
        _check_valid_calculation(value)
    else:
        if not is_numeric_dtype(df[value]):
            message = "The value column " + value + " is not numeric"
            raise Exception(message)

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
        if isinstance(color_by, basestring):
            color_by = [color_by]
        for name in color_by:
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

    if isinstance(value, dict):
        df_new = df.groupby([SUBPLOT_COLUMN_NAME, COLOR_BY_COLUMN_NAME, x])[[value['numerator'], value['denominator']]].sum().reset_index()
        df_new[value['name']] = df_new[value['numerator']]/df_new[value['denominator']]
    else:
        df_new = df.groupby([SUBPLOT_COLUMN_NAME, COLOR_BY_COLUMN_NAME, x])[value].sum().reset_index()

    if df_new.index.size != df.index.size and not aggregate:
        warnings.warn(
            "The original table was aggregated to fit the specification and the grain changed as a result.")

    return df_new


def _assign_color(df, color_by_column_name):
    """
    Method that add a << COLOR_COLUMN >> to df representing the color of the trace.

    :param df: pandas.DataFrame instance
    :param color_by_column_name: str name of the column for the color.
    :return: initial df with an extra column called << COLOR_COLUMN >> reprenting the color
    """

    df = df.copy()
    COLOR_IND_TMP = '__color_indicator__'
    df_color_ind = pd.DataFrame(df[color_by_column_name].unique()).reset_index()
    df_color_ind = df_color_ind.rename(columns={'index': COLOR_IND_TMP, 0:COLOR_BY_COLUMN_NAME})
    df_color_ind[COLOR_COLUMN] = df_color_ind.apply(lambda rec: COLOR_MASTER_LIST[rec[COLOR_IND_TMP]], axis=1)

    df = df.merge(df_color_ind, on=color_by_column_name)
    df = df.drop(columns=COLOR_IND_TMP)

    return df


def _get_show_legend_df(df, plot_by, color_by):
    """
    Method that gets all combinations of plot_by and color_by values in the dataset
    
    :param df: pandas.DataFrame instance
    :param plot_by: str plot_by column name
    :param color_by: str color_by column name
    :return: pandas.DataFrame instance
    """
    
    df = df.copy()
    return df \
        .groupby(color_by, as_index=False) \
        .first()[[plot_by, color_by]]


def _show_legend(df_show_legend, plot_by, color_by, plot_by_name , color_by_name):
    """
    Method that determines if the combination plot_by_name and color_by_name is present in the dataset
    
    :param df_show_legend: pandas.DataFrame instance containing a line per combination
    :param plot_by: str plot_by column name
    :param color_by: str color_by column name
    :param plot_by_name: str plot_by value to test
    :param color_by_name: str color_by value to test
    :return: bool True if combination is present in dataset
    """
    return df_show_legend[(df_show_legend[plot_by] == plot_by_name) & (df_show_legend[color_by] == color_by_name)].shape[0] != 0


def merge_trace_and_get_figure(traces, number_of_column):
    """
    Method that returns plotly figure object based on traces and subplot grid layout
    
    :param traces: dict of dicts is a plotly trace objects (one per series to display)
    :param number_of_column: int user input for number of column in subplot grid
    :return: dict plotly figure object
    """
    
    number_of_plot = len(traces)

    if number_of_plot == 1:
        number_of_column = 1
        number_of_row = 1
    else:
        number_of_row = int(np.ceil(number_of_plot / number_of_column))

    # We are creating temporary subplot title because that also create very other useful element in
    # the layout dict under the 'annotations' key
    fig = tools.make_subplots(rows=number_of_row, cols=number_of_column, subplot_titles=['Plot{}'.format(i) for i,j in enumerate(traces)])

    plot_ind = 0
    for row in range(number_of_row):
        for col in range(number_of_column):
            for trace in traces[plot_ind]:
                fig.append_trace(trace, row + 1, col + 1)
            plot_ind = plot_ind + 1
            if plot_ind == number_of_plot:
                break
    return fig


def _get_plot_by_order(df, plot_by):
    """
    Method that returns list of subplots from plot_by column
    
    :param df: pandas.DataFrame instance
    :param plot_by: name of plot_by column 
    :return: list containing subplot names
    """
        
    return df[plot_by].unique().tolist()


def _build_trace(df, x, y, name, showlegend, color):
    """
    Method that builds that plot data for a single trace
    
    :param df: pandas.DataFrame instance 
    :param x: str x-axis column name
    :param y: str y-axis column name
    :param name: str trace name
    :param showlegend: bool if True show trace name in legend
    :param color: str the color code for this trace
    :return: plotly go object
    """
        
    df = df.copy()
    return go.Scatter(x=df[x],
                      y=df[y],
                      name=name,
                      legendgroup=name,
                      showlegend=showlegend,
                      marker={'color': color},
                      )


def build_traces(df, x, y, plot_by, color_by):
    """
    Method that build a nested list of all traces to plot
    
    :param df: pandas.DataFrame instance
    :param x: str x-axis column name
    :param y: str y-axis column name
    :param plot_by: plot_by column name
    :param color_by: color_by column name
    :return: list of lists for traces with the required data for display (one sublist per subplot)
    """

    df = df.copy()
    df = _assign_color(df=df, color_by_column_name=color_by)
    df_show_legend = _get_show_legend_df(df=df, plot_by=plot_by, color_by=color_by)

    plot_by_names = _get_plot_by_order(df=df, plot_by=plot_by)
    traces_allsubplot = []
    for plot_by_name in plot_by_names:
        df_specific_subplot = df[df[plot_by] == plot_by_name]

        traces_per_subplot = []
        for specific_subplot_color_by_name, df_specific_subplot_color_by in df_specific_subplot.groupby(color_by):
            traces_per_subplot.append(_build_trace(df=df_specific_subplot_color_by,
                                                   x=x,
                                                   y=y,
                                                   name=specific_subplot_color_by_name,
                                                   showlegend=_show_legend(df_show_legend=df_show_legend, plot_by=plot_by, color_by=color_by, plot_by_name=plot_by_name, color_by_name=specific_subplot_color_by_name),
                                                   color=df_specific_subplot_color_by[COLOR_COLUMN].tolist()[0]))
        traces_allsubplot.append(traces_per_subplot)

    return traces_allsubplot


def set_x_y_axis_title(fig, x_name, y_name, n_plot):
    """
    Method that sets axis titles
    
    :param fig: dict plotly figure object
    :param x_name: str x_title 
    :param y_name: str y_title
    :param n_plot: int number of subplots
    :return: dict plotly figure object
    """
        
    for i in range(0, n_plot):
        fig['layout']['xaxis{}'.format(i + 1)].update(title=x_name)
        fig['layout']['yaxis{}'.format(i + 1)].update(title=y_name)


def set_subplot_title(fig, x, y, plot_by_all_name, color_by):
    """
    Method that sets subplot titles
    
    :param fig: dict plotly figure object
    :param x: str x-axis column name
    :param y: str y-axis column name
    :param plot_by_all_name: str plot_by column name
    :param color_by: str color_by column name
    :return: dict plotly figure object
    """
    
    for ind, plot_by_specific in enumerate(plot_by_all_name):
        fig['layout']['annotations'][ind].update(
            {'text': '{y} per {x} per {color_by} for {plot_by_specific}'.format(x=x,y=y,color_by=color_by, plot_by_specific=plot_by_specific)}
        )


def create_plotly_fig(df, x, value, plot_by=None, color_by=None, number_of_column=None):
    """
    Method that builds the plotly figure object to be displayed
    
    :param df: pandas.DataFrame instance
    :param x: str x-axis column name
    :param value: str y-axis column name
    :param plot_by: str or list column names to segment subplots
    :param color_by: str or list column names to segment colors per subplot
    :param number_of_column: int number of columns in subplot grid
    :return: 
    """
    
    df = df.copy()
    df = _format_data(df=df,
                      value=value,
                      x=x,
                      plot_by=plot_by,
                      color_by=color_by)
    if isinstance(value, dict):
        value = value['name']

    traces = build_traces(df=df,
                          x=x,
                          y=value,
                          plot_by=SUBPLOT_COLUMN_NAME,
                          color_by=COLOR_BY_COLUMN_NAME)
    fig = merge_trace_and_get_figure(traces, number_of_column=number_of_column)
    set_x_y_axis_title(fig,
                       x_name=x,
                       y_name=value,
                       n_plot=len(traces))

    set_subplot_title(fig=fig,
                      x=x,
                      y=value,
                      plot_by_all_name=_get_plot_by_order(df=df, plot_by=SUBPLOT_COLUMN_NAME),
                      color_by=color_by)
    return fig

