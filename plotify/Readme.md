## Introduction
`plotify` is a package that allows simple, fast, and accurate production of common types of data visualizations.
By installing and importing `plotify` you can call the `create_plotly_fig()` method. 
When you ask plotify to plot something using a dataframe, it takes care of aggregateing the data at the correct grain
and outputs a nice grid of plots showing you all the results.
The main benefit is to increase speed and convenience for basic data visualization.

## Example command
Assuming you have a dataframe called df already available:
```python
from plotify import create_plotly_fig
fromt plotly import plot
figure = create_plotly_fig(df, 
                           x='x_axis_column_name', 
                           value='y_axis_column_name', 
                           plot_by='dim_1',
                           color_by=['dim_2', 'dim_3'], 
                           number_of_columns=2)
plot(figure)
```

The output will look something like this:
![alt text](https://github.com/Shopify/visualization-tools/blob/master/example_plots.png "examples plots")
