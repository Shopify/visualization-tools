## Introduction
`plotify` is a package that allows simple, fast, and accurate production of common types of data visualizations.
By installing and importing `plotify` you can call the `create_plotly_fig()` method. 
When you ask plotify to plot something using a dataframe, it takes care of aggregating the data at the correct grain
and outputs a nice grid of plots showing you all the results.
The main benefit is to increase speed and convenience for basic data visualization.

## How to Install
in the shell type: `pip install git+git://github.com/Shopify/visualization-tools.git`
in a Jupyter notebook type: `!pip2 install git+git://github.com/Shopify/visualization-tools.git`

## Example Command
Assuming you have a dataframe named `df` already available in your notebook:
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
![alt text](https://github.com/Shopify/visualization-tools/blob/master/plots_example.png "examples plots")

See more examples [in this notebook](https://github.com/Shopify/visualization-tools/blob/master/plotify/example/plotify_example.ipynb)
