## Introduction
`plotify` is a package that allows simple, fast, and accurate production of common types of data visualizations.
By installing and importing `plotify` you can call the `create_plotly_fig()` method. 
When you ask plotify to plot something using a dataframe, it takes care of aggregating the data at the correct grain
and outputs a nice grid of plots showing you all the results.
The main benefit is to increase speed and convenience for basic data visualization.

## Example command
Assuming you have a dataframe called df already available in your notebook:
```python
from plotify.plotify import *
from plotly.offline import init_notebook_mode, iplot
init_notebook_mode()

figure = create_plotly_fig(df=df, 
                           x='date', 
                           value='order', 
                           plot_by='country',
                           color_by='plan', 
                           number_of_column=2)
iplot(figure)
```

The output will look something like this:
![alt text](https://github.com/Shopify/visualization-tools/blob/master/example_plots.png "examples plots")
