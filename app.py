import logging
from scrape import extract_courses_and_prereqs
from graph_utils import CourseGraph, visualize_prereq_graph, visualize_prereq_graph_lex
import streamlit as st

logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

# URL = "https://catalog.iit.edu/courses/math/"

def URL(subject):
    return f"https://catalog.iit.edu/courses/{subject}/"

subject = st.text_input("Enter subject (e.g., math, cs):", "math")
if subject:
    courses, prereqs = extract_courses_and_prereqs(URL(subject.lower()))
    cg = CourseGraph(prereqs)

    st.title("IIT Course Prerequisite Planner")

    selected = st.multiselect("Select target courses:", sorted(courses))
    include_coreqs = st.checkbox("Include corequisites", value=True)

    if selected:
        subgraph = cg.get_subgraph(selected, include_coreqs=include_coreqs, as_dict=True)
        visualize_prereq_graph(subgraph)