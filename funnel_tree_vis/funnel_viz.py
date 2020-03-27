from __future__ import division

import os
import pandas as pd
import numpy as np
from PIL import Image
from anytree import Node as BaseNode, PreOrderIter
from anytree.dotexport import RenderTreeGraph


class Node(BaseNode):
    """
    Class to extend the BaseNode object coming from anytree.
    """
    def __init__(self, name, metrics, parent=None):
        """
        :param name: string representing the name of the node
        :param metrics: List of string representing all the metrics to be aggregated on each node
        :param parent: Node() object representing the parent (there is a parent)
        """
        super(Node, self).__init__(name, parent)
        self.metrics = metrics
        self.node_name_print = self.name.split('->')[-1] if name != 'root' else 'Total'
        self.calculation = {}

    def __getattr__(self, name):
        """
        :param name: the name of the value we are trying to access on the node
        :return: Return the value associated with the metric_name or the regular value if the attribute is not a metric name
        """

        # We need to add this condition because __getattr__ is getting call before
        # metrics is instantiated
        if self.__dict__.get('metrics'):
            if name in self.__dict__['metrics']:
                return self.__getattribute__(name)

            elif name in self.__dict__['calculation'].keys():
                return self.calculation[name](self)
            else:
                # Default behaviour
                raise AttributeError
        else:
            raise AttributeError

    def _add_calculation(self, calculation_dict):
        """
        Helper function to add/update a calculation in the dict
        :param calculation_dict: A dict with key='calculation name'
            and value = Function to be applied on each node.
        """
        self.calculation.update(calculation_dict)


class TreeViz(object):
    """
    Class to create the tree for visualization
    """
    SEP = '->'
    root_name = 'root'

    def __init__(self, df, node_level_list=None, metrics=None):
        """
        :param df: Pandas DataFrame with some key and metric column
        :param node_level_list: Column of the DataFrame on which we will create the tree structure
        :param metrics: Column of the Dataframe on which we will aggregate the value on a node
            level.
        """
        self.df = df.copy()

        # If node_level_list is None, every column that are not considered as a number are taken
        self.node_level_list = node_level_list or \
                                list(df.select_dtypes(exclude=[np.number]).columns.values)

        # If metrics is None, every column that are considered as a number are taken
        self.metrics = metrics or list(df.select_dtypes(include=[np.number]).columns.values)

        # Calculation to be added to the node
        self.calculation = {}

        # This this represent the metric or calculation to be shown and with which format
        #  to be printed : {'metric_name': {'type': type, 'digits': digits}}
        self._node_metric_col_print_dict = {}

    @property
    def tree(self):
        """
        Create the tree, set the node value and add calculation
        """
        # Making sure the aggregation is the right one
        df = self.df[self.node_level_list + self.metrics]\
            .groupby(self.node_level_list, as_index=False).sum()

        SEP = self.SEP
        df['pathString'] = df[self.node_level_list].apply(lambda row: SEP.join(row.values), axis=1)
        df['pathString'] = df['pathString'].map(lambda value: SEP.join([self.root_name, value]))

        tree = self._create_tree_structure(df, self.metrics)
        df_all_node = self._get_all_node_df(df)

        tree = self._set_node_metric(df_all_node, tree)
        self._add_calculation_to_node(tree, self.calculation)
        return tree

    @property
    def node_metric_col_print_dict(self):
        """
        Return the user input OR the default version of the dict.
        Dict of what we want to print in the node and in which format.
            The structure of the Dict is: {'metric_name': {'type': type, 'digits': digits}}
            type must be in ['float', 'percent', 'int']
        """
        return self._node_metric_col_print_dict or \
                self._get_default_node_metric_col_print_dict()

    def _create_tree_structure(self, df, metrics):
        """
        Function that create the whole tree structure

        :param df: Pandas DataFrame with some key and metric column
        :param metrics: Column of the Dataframe on which we will aggregate the value
            on a node level.
        :return: Return an empty tree (only the tructure)
        """
        all_node_name = self._get_node_list_from_pathstring(df['pathString'].values)

        # root is hardcoded because only node with no parent
        # so it wouldn't work in for loop
        tree = Node(self.root_name, metrics)
        for node_name in all_node_name[1:]:
            # 'root->added->3rd party domain'.rsplit(SEP, 1) splits
            # 'root->added->3rd party domain' in ['root->added', '3rd party domain']
            parent_name = node_name.rsplit(self.SEP, 1)[0]
            parent_node = self._get_node(tree, parent_name)
            Node(node_name, metrics, parent_node)
        return tree

    def _get_node_list_from_pathstring(self, path_strings):
        """
        Function that output the name of all the node based on a path_string.
        For example : path_strings = 'A->B->C'
        will return ['A', 'A->B', 'A->B->C'] which are all the node.

        :param path_strings: A string representing the path of the node: See example above
        :return: List of string representing node name
        """
        SEP = self.SEP
        node_names = []
        for path_string in path_strings:
            node_names.extend(self.cumulative_names_from_right(path_string))

        node_names = np.unique(node_names)

        # The order is important so we can create the parent first and the child after
        node_names = sorted(node_names, key=lambda path_string: path_string.count(SEP))

        return node_names

    def cumulative_names_from_right(self, path_string):
        """
        Helper function for _get_node_list_from_pathstring

        :param path_string:
        :return:
        """
        n = len(path_string.split(self.SEP))
        return [path_string.rsplit(self.SEP, i)[0] for i in range(0, n)]

    @staticmethod
    def _get_node(tree, name):
        """
        Function that return the node in the tree based on the name.

        :param tree: tree is an instance of Node()
        :param name: name of the node
        :return: Node() in the tree
        """
        node_list = [node for node in PreOrderIter(tree) if node.name == name]
        assert len(node_list) == 1, "The name of the node is not unique or does not exist"
        return node_list[0]

    def _get_all_node_df(self, df):
        df = df.copy()
        node_names = self._get_node_list_from_pathstring(df['pathString'].values)

        # Performing a Cross Join
        df['cross_join_id'] = 1
        df_node_name = pd.DataFrame({'node_name': node_names, 'cross_join_id': 1})
        df_node_name = pd.merge(df, df_node_name, on='cross_join_id')
        df_node_name['ind'] = df_node_name.apply(lambda x: x.node_name in x.pathString, axis=1)
        df_node_name = df_node_name[df_node_name['ind']] \
            .groupby('node_name', as_index=False) \
            .sum() \
            .drop(columns=['ind', 'cross_join_id'])
        return df_node_name

    def _set_node_metric(self, df, tree):
        """
        Each row of the df should be representing the leaf.
        We are using each row to set the leaf.

        :param df: Pandas DataFrame with some key, metric column and a node_name column
        :param tree: tree is an instance of Node()
        :return: Nothing
        """
        for path_string in df['node_name'].values:
            node = self._get_node(tree, path_string)
            for metric in self.metrics:
                try:
                    value = df[df.node_name == path_string][metric].values[0]
                    node.__setattr__(metric, value)
                except KeyError:
                    raise KeyError(
                        "Metric '{}' not in DataFrame columns".format(metric)
                    )
        return tree

    def plot_tree(self, filepath,
                  edge_prop_metric=None, node_label_func=None, node_shape_func=None):
        """
        Function that is returning the dotprogram and saving the png in filepath.

        :param filepath: Path of the file
        :param node_metric_col_print_dict: Dict of what we want to print in the node
            and in which format.
            The structure of the Dict is: {'metric_name': {'type': type, 'digits': digits}}
            type must be in ['float', 'percent', 'int']
        :param edge_prop_metric: Metric to compute the proportion on each edge
        :param node_label_func: Function to be apply to each node to get the label
        :param node_shape_func: Function to be apply to each node to get the shape
        :return: dotprogram in a string format
        """

        render_tree = \
            RenderTreeGraph(node=self.tree,
                            nodeattrfunc=lambda node:
                            self._get_node_attr(node,
                                                node_label_func,
                                                node_shape_func),
                            edgeattrfunc=lambda node, child:
                            self._get_edge_attr(node, child, edge_prop_metric))

        render_tree.to_picture(filepath)
        return self._to_dot(render_tree)

    def _get_node_attr(self, node, node_label_func=None, node_shape_func=None):
        """
        Function that output the right function to use for the nodeattrfunc parameter
            of the  RenderTreeGraph().

        :param node: The Node() object
        :param node_shape_func: Function to be apply to each node to get the shape
        :param node_label_func: Function to be apply to each node to get the label
        :return: A function to put in the nodeattrfunc parameter
        """

        if node_shape_func is None:
            def node_shape_func(node):
                return ""

        node_label_func = node_label_func or self._default_node_label_func

        return " ".join([node_shape_func(node), node_label_func(node)])

    def _get_edge_attr(self, node, child,  edge_prop_metric=None, edge_label_func=None):
        """
        Function that output the right function to use for the edgeattrfunc parameter
            of the  RenderTreeGraph().

        :param node: The Node() object
        :param child: Child of the Node object (Also a Node())
        :param edge_prop_metric: Metric to compute the proportion on each edge
        :param edge_label_func: Function to be apply to each edge to get the label
        :return: A function to put in the edgeattrfunc parameter
        """
        if edge_label_func is None:
            def edge_label_func(node, child, edge_prop_metric):
                if edge_prop_metric is not None:
                    ratio = child.__getattr__(edge_prop_metric)/node.__getattr__(edge_prop_metric)
                    return 'label="{prop}"'.format(prop=self._format_string(ratio, 'percent', 2))
                else:
                    return ""
        return edge_label_func(node, child, edge_prop_metric)

    @staticmethod
    def _format_string(number, type='int', digits=2):
        """
        Function that format the output to print thing nicely.

        :param number: Number to format
        :param type: one of ['int', 'float', 'percent']
        :param digits: Number of digits for type float or percent
        :return: Return the well formated number
        """

        if type == 'float':
            return "{:,.{precision}f}".format(number, precision=digits)
        elif type == 'percent':
            return "{:,.{precision}%}".format(number, precision=digits)
        elif type == 'int':
            return "{:0,}".format(number)
        else:
            raise ValueError("type argument should be 'int', 'float' or 'percent',"
                             " got {type} instead".format(type=type))

    def add_calculation(self, calculation_dict):
        """
        Helper function to add/update a calculation in the dict
        :param calculation_dict: A dict with key='calculation name' and value = Function to be
            applied on each node.
        """
        self.calculation.update(calculation_dict)

    @staticmethod
    def _add_calculation_to_node(tree, calculation_dict):
        """
        Function that add calculation to each node in tree

        :param tree: Node() Object
        :param calculation_dict: A dict with key='calculation name' and value = Function to
            be applied on each node.
        :return: Nothing
        """
        if len(calculation_dict) > 0:
            for node in PreOrderIter(tree):
                node._add_calculation(calculation_dict)

    def _get_default_node_metric_col_print_dict(self):
        """
        Function that return the default node_metric_col_print_dict by doing
            some inference on the root node (tree)

        :return: dict
        """
        int_metrics = [metric for metric in self.metrics if
                       float(self.tree.__getattr__(metric)).is_integer()]
        float_metrics = [metric for metric in self.metrics if
                         not float(self.tree.__getattr__(metric)).is_integer()]

        int_calculations = [calculation for calculation in self.tree.calculation.keys() if
                            float(self.tree.__getattr__(calculation)).is_integer()]
        float_calculations = [calculation for calculation in self.tree.calculation.keys() if
                              not float(self.tree.__getattr__(calculation)).is_integer()]

        int_format_dict = {column:{'type': 'int', 'digits':0} for column in
                           (int_metrics + int_calculations)}
        float_format_dict = {column: {'type': 'float', 'digits': 2} for column in
                             (float_calculations+float_metrics)}

        int_format_dict.update(float_format_dict)

        return int_format_dict

    def _default_node_label_func(self, node):
        """
        Function that return the default label string.

        :param node: A Node() object
        :return: Label string
        """
        all_metric_list = list(node.calculation.keys())
        all_metric_list.extend(node.metrics)

        metric_string_list = []
        for metric_name, layout_dict in self.node_metric_col_print_dict.items():
            if metric_name in all_metric_list:
                metric_formated = self._format_string(node.__getattr__(metric_name),
                                                      layout_dict['type'],
                                                      layout_dict['digits'])

                metric_tmp = "{0}: {1}".format(metric_name.replace('_', ' '),
                                               metric_formated)
                metric_string_list.append(metric_tmp)

        metric_string = "\n".join(metric_string_list)
        return 'label="{node_name}\n{separator}\n{metric_string}"'.\
            format(node_name=node.node_name_print,
                   separator="-----------",
                   metric_string=metric_string)

    @staticmethod
    def _to_dot(render_tree):
        """
        :param render_tree: Object coming from RenderTreeGraph(Node)
        :return: String of the dot program
        """
        lines = [line for line in render_tree]
        return "\n".join(lines)

    @staticmethod
    def _plot_dot(render_tree):
        render_tree.to_picture("tbd.png")
        Image.open("tbd.png").show()
        os.system("rm tbd.png")

    def update_node_metric_col_print_dict(self, node_metric_col_print_dict):
        """
        Function that update _node_metric_col_print_dict field
        :param node_metric_col_print_dict: Dict of what we want to print in the node and in which
            format. The structure of the Dict is: {'metric_name': {'type': type, 'digits': digits}}
            type must be in ['float', 'percent', 'int']
        :return:
        """
        self._node_metric_col_print_dict.update(node_metric_col_print_dict)
