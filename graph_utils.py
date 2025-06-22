import logging
import networkx as nx
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import streamlit as st # type: ignore


logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')


class CourseGraph:
    def __init__(self, prereq_dict):
        self.full_graph = self._build_graph(prereq_dict)

    def _build_graph(self, prereq_dict):
        G = nx.DiGraph()
        for course, prereqs in prereq_dict.items():
            for prereq_code, rel_type in prereqs:
                G.add_edge(prereq_code, course, type=rel_type)
        return G

    def get_subgraph(self, target_courses, include_coreqs=True, as_dict=False):
        sub_nodes = set()

        def dfs(course):
            if course in sub_nodes:
                return
            sub_nodes.add(course)
            for prereq in self.full_graph.predecessors(course):
                edge_type = self.full_graph[prereq][course].get('type', 'prereq')
                if include_coreqs or edge_type == 'prereq':
                    dfs(prereq)

        for course in target_courses:
            if course not in self.full_graph:
                self.full_graph.add_node(course)
            dfs(course)
        
        subgraph = self.full_graph.subgraph(sub_nodes).copy()
        
        if as_dict:
            prereq_dict = {}
            for u, v in subgraph.edges():
                rel_type = subgraph[u][v].get('type', 'prereq')
                prereq_dict.setdefault(v, []).append((u, rel_type))
            return prereq_dict
        else:
            return subgraph


def list_of_lists(prereq_dict, include_coreqs=True):
    G = nx.DiGraph()
    for course, prereqs in prereq_dict.items():
        for prereq_code, rel_type in prereqs:
            if not include_coreqs and rel_type == "coreq":
                continue
            G.add_edge(prereq_code, course)

    depth = {}
    for node in nx.topological_sort(G):
        preds = list(G.predecessors(node))
        if not preds:
            depth[node] = 0
        else:
            depth[node] = 1 + max(depth[p] for p in preds)

    layers = {}
    for node, d in depth.items():
        layers.setdefault(d, []).append(node)

    if not layers:
        return [[node] for node in prereq_dict if prereq_dict[node] == []]
    
    return [sorted(layers[i]) for i in range(max(layers.keys()) + 1)]


def visualize_lol(layered_nodes, prereq_dict, include_coreqs=True):
    G = nx.DiGraph()
    edge_colors = []
    color_map = {
        "prereq": "green",
        "coreq": "blue"
    }
    legend_elements = [
        Line2D([0], [0], color='green', lw=2, label='Prerequisite'),
        Line2D([0], [0], color='blue', lw=2, label='Corequisite')
    ]
    
    for course, prereqs in prereq_dict.items():
        for prereq_code, rel_type in prereqs:
            if not include_coreqs and rel_type == "coreq":
                continue
            G.add_edge(prereq_code, course)
            edge_colors.append(color_map[rel_type])

    pos = {}
    for depth, nodes in enumerate(layered_nodes):
        row_len = len(nodes)
        for i, node in enumerate(nodes):
            # Center the row horizontally
            x = i - (row_len - 1) / 2
            pos[node] = (x, -depth)

    plt.figure(figsize=(16, 10))
    ax = plt.gca()
    for node, (x, y) in pos.items():
        ax.text(
            x, y, node,
            fontsize=15,
            ha='center', va='center',
            color='black',
            bbox=dict(boxstyle="round,pad=0.1", facecolor="white", edgecolor="none", alpha=0.8)
        )
    nx.draw_networkx_nodes(G, pos, alpha=0)
    nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrows=True, arrowsize=15, connectionstyle="arc3,rad=0.2")
    plt.legend(handles=legend_elements, loc='lower right')
    st.pyplot(plt.gcf())
    plt.clf()
