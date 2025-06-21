import logging
from scrape import extract_courses_and_prereqs
from graph_utils import CourseGraph, list_of_lists, visualize_lol
import streamlit as st

logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

# URL = "https://catalog.iit.edu/courses/math/"

def URL(subject):
    return f"https://catalog.iit.edu/courses/{subject}/"

subjects = st.text_input("Enter subject (e.g., math, cs):", "math")

if subjects:
    all_courses = []
    all_prereqs = {}
    for subject in subjects.split(','):
        subject = subject.strip()
        courses, prereqs = extract_courses_and_prereqs(URL(subject.lower()))
        all_courses.extend(courses)
        all_prereqs.update(prereqs)
    cg = CourseGraph(all_prereqs)

    st.title("IIT Course Prerequisite Planner")

    selected = st.multiselect("Select target courses:", sorted(all_courses))
    include_coreqs = st.checkbox("Include corequisites", value=True)

    if selected:
        subgraph = cg.get_subgraph(selected, include_coreqs=include_coreqs, as_dict=True)
        layers = list_of_lists(subgraph, include_coreqs=include_coreqs)
        visualize_lol(layers, subgraph, include_coreqs=include_coreqs)

# FIXME: Show full course
# FIXME: Only one subject graph shown at a time
# FIXME: Some courses throw errors: D151