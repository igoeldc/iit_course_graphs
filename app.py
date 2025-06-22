import logging
from scrape import extract_courses_and_prereqs
from graph_utils import CourseGraph, list_of_lists, visualize_lol
import streamlit as st # type: ignore


logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')


def URL(subject):
    return f"https://catalog.iit.edu/courses/{subject}/"

st.title("IIT Course Prerequisite Graph")


subjects = st.text_input("Enter subject (e.g., math, cs):", "math")
if subjects:
    courses_with_prereqs = []
    all_prereqs = {}
    for subject in subjects.split(','):
        subject = subject.strip()
        courses, prereqs = extract_courses_and_prereqs(URL(subject.lower()), short=False)
        courses_with_prereqs.extend(course for course in courses if prereqs.get(course))
        all_prereqs.update(prereqs)
    cg = CourseGraph(all_prereqs)

    selected = st.multiselect("Select target courses (with prerequisites):", sorted(courses_with_prereqs))
    include_coreqs = st.checkbox("Include corequisites", value=True)

    if selected:
        subgraph = cg.get_subgraph(selected, include_coreqs=include_coreqs, as_dict=True)
        layers = list_of_lists(subgraph, include_coreqs=include_coreqs)
        visualize_lol(layers, subgraph, include_coreqs=include_coreqs)
