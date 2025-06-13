import logging
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt
import streamlit as st

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

def visualize_prereq_graph(prereq_dict, include_coreqs=True):
    G = nx.DiGraph()
    
    edge_colors = []
    color_map = {
        "prereq": "green",
        "coreq": "blue"
    }

    for course, prereqs in prereq_dict.items():
        for prereq_code, rel_type in prereqs:
            if not include_coreqs and rel_type == "coreq":
                continue
            G.add_edge(prereq_code, course)
            edge_colors.append(color_map[rel_type])
    
    plt.figure(figsize=(12, 8))
    
    # pos = nx.spring_layout(G, k=2, iterations=500)
    
    # init_pos = nx.shell_layout(G)
    # pos = nx.kamada_kawai_layout(G, scale=3, pos=init_pos)
    
    pos = graphviz_layout(G, prog='dot')

    nx.draw(G, pos, with_labels=True, node_size=300, node_color='lightblue',
            font_size=5, font_color='black', arrows=True, edge_color=edge_colors)
    
    plt.title("Course Prerequisite Graph")
    st.pyplot(plt.gcf())
    plt.clf()

def visualize_prereq_graph_lex(prereq_dict, layout_prog='dot',
                               rankdir='BT', node_size=200, font_size=5):
    G = nx.DiGraph()

    # Build the graph
    for course, prereqs in prereq_dict.items():
        for prereq_code, rel_type in prereqs:
            G.add_edge(prereq_code, course, type=rel_type)

    # Compute topological levels
    in_degrees = dict(G.in_degree())
    levels = {}
    level_nodes = {}
    queue = [node for node in G.nodes() if in_degrees[node] == 0]

    for node in queue:
        levels[node] = 0
        level_nodes.setdefault(0, []).append(node)

    while queue:
        current = queue.pop(0)
        current_level = levels[current]
        for neighbor in G.successors(current):
            in_degrees[neighbor] -= 1
            if in_degrees[neighbor] == 0:
                queue.append(neighbor)
                levels[neighbor] = current_level + 1
                level_nodes.setdefault(current_level + 1, []).append(neighbor)

    # Convert to AGraph
    A = nx.nx_agraph.to_agraph(G)
    A.graph_attr['rankdir'] = rankdir  # Bottom-to-top layout
    A.graph_attr['ordering'] = 'out'

    # Enforce lexicographic order within each rank using invisible edges
    for lvl, nodes in level_nodes.items():
        sorted_nodes = sorted(nodes)
        for i in range(len(sorted_nodes) - 1):
            A.add_edge(sorted_nodes[i], sorted_nodes[i+1], style='invis')
        for node in sorted_nodes:
            A.get_node(node).attr['rank'] = 'same'

    # Set edge colors
    for edge in A.edges():
        u, v = edge[0], edge[1]
        if G.has_edge(u, v):  # only color real edges
            rel_type = G[u][v].get('type', 'prereq')
            edge.attr['color'] = 'blue' if rel_type == 'coreq' else 'green'

    # Layout and draw
    A.layout(prog=layout_prog)
    pos = {}
    for node in G.nodes():
        n = A.get_node(node)
        x, y = map(float, n.attr['pos'].split(','))
        pos[node] = (x, -y)

    plt.figure(figsize=(16, 10))
    edge_colors = ['blue' if G[u][v]['type'] == 'coreq' else 'green' for u, v in G.edges()]
    nx.draw(G, pos, with_labels=True, node_size=node_size, node_color='lightblue',
            font_size=font_size, font_color='black', arrows=True, edge_color=edge_colors)
    plt.title("Course Prerequisite Graph (Lexical Order by Level)")
    st.pyplot(plt.gcf())
    plt.clf()