import logging
from scrape import extract_courses_and_prereqs
from graph_utils import CourseGraph, visualize_prereq_graph_lex

logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

URL = "https://catalog.iit.edu/courses/math/"
# subject_list = []
# def URL(subject):
#     return f"https://catalog.iit.edu/courses/{subject}/"

courses, prereqs = extract_courses_and_prereqs(URL)

cg = CourseGraph(prereqs)

selected = ['M332', 'M374']
subgraph = cg.get_subgraph(selected, include_coreqs=True)

visualize_prereq_graph_lex(subgraph)