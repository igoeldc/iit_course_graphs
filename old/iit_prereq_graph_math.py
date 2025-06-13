import logging
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import re
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

URL = "https://catalog.iit.edu/courses/math/"

# subject_list = []
# def URL(subject):
#     return f"https://catalog.iit.edu/courses/{subject}/"

def split_course_code(course_code):
    return re.split(r'\xa0', course_code)

def join_course_code(subj, code, short=False):
    if short:
        return f'{subj[0]}{code}'
    else:
        return f'{subj} {code}'

def extract_courses_and_prereqs(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    course_list = []
    prereq_dict = {}

    for courseblock in soup.select(".courseblock"):
        # Extract course code and title
        blocktitle = courseblock.select_one(".courseblocktitle")
        course_code = blocktitle.select_one(".coursecode").get_text(strip=True)
        subj, code = split_course_code(course_code)
        
        logging.debug(f'{subj} - {code}')
        course = join_course_code(subj, code, short=True)
        course_list.append(course)

        # # Extract course description
        # desc_tag = courseblock.select_one(".courseblockdesc")
        # if desc_tag:
        #     desc_text = desc_tag.get_text()
        #     # Look for any MATH xxx course codes in the description
        #     prereqs = re.findall(r"MATH\s\d+", desc_text)
        #     prereq_dict[course_code] = list(set(prereqs)) if prereqs else []
        
        # Extract prerequisites
        for attrblock in courseblock.select(".courseblockattr"):
            if 'Prerequisite' in attrblock.get_text():
                logging.debug(attrblock.get_text())
                # prereq_links = attrblock.select("a")
                prereqs = []
                contents = list(attrblock.children)
                # for prereq in prereq_links:
                #     psubj, pcode = split_course_code(prereq.get_text())
                #     logging.debug(f'{psubj} - {pcode}')
                #     prereq_code = join_course_code(psubj, pcode, short=True)
                #     prereqs.append(prereq_code)
                
                for i, element in enumerate(contents):
                    if isinstance(element, Tag) and element.name == 'a':
                        text = element.get_text(strip=True)
                        psubj, pcode = split_course_code(text)
                        logging.debug(f'{psubj} - {pcode}')
                        prereq_code = join_course_code(psubj, pcode, short=True)
                        
                        is_coreq = False
                        if i + 1 < len(contents):
                            next_item = contents[i + 1]
                            if isinstance(next_item, NavigableString) and "*" in next_item:
                                is_coreq = True
                        prereqs.append((prereq_code, "coreq" if is_coreq else "prereq"))

                    #     psubj, pcode = split_course_code(element.get_text(strip=True))
                    #     logging.debug(f'{psubj} - {pcode}')
                    #     prereq_code = join_course_code(psubj, pcode, short=True)
                    #     prereqs.append(prereq_code)
                    # elif isinstance(element, NavigableString) and element.strip():
                    #     # Handle cases where prerequisites are listed as text
                    #     prereq_text = element.strip()
                    #     if prereq_text:
                    #         # Match MATH xxx format
                    #         match = re.match(r'MATH\s*(\d+)', prereq_text)
                    #         if match:
                    #             prereq_code = join_course_code('MATH', match.group(1), short=True)
                    #             prereqs.append(prereq_code)
                
                prereq_dict[course] = prereqs

    return course_list, prereq_dict

def visualize_prereq_graph(prereq_dict):
    G = nx.DiGraph()
    
    edge_colors = []
    color_map = {
        "prereq": "green",
        "coreq": "blue"
    }

    for course, prereqs in prereq_dict.items():
        for prereq_code, rel_type in prereqs:
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
    plt.show()

def visualize_prereq_graph_lex(prereq_dict, layout_prog='dot',
                               rankdir='TB', node_size=200, font_size=5):
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
    plt.show()

# Run it
if __name__ == "__main__":
    courses, prereqs = extract_courses_and_prereqs(URL)
    logging.debug("Courses:")
    logging.debug(courses)
    logging.debug("Prerequisites:")
    for course, reqs in prereqs.items():
        logging.debug(f"{course}: {reqs}")
    visualize_prereq_graph(prereqs)
    # visualize_prereq_graph_lex(prereqs)