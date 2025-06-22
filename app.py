import logging
from scrape import extract_courses_and_prereqs
from graph_utils import CourseGraph, list_of_lists, visualize_lol
import streamlit as st # type: ignore


logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

def URL(subject):
    return f"https://catalog.iit.edu/courses/{subject}/"


st.set_page_config(layout="wide")

st.title("IIT Course Prerequisite Graph")

subjects = st.text_input("Enter subject (e.g., math, cs):", "math, cs")
if subjects:
    all_courses = []
    courses_with_prereqs = []
    all_prereqs = {}
    
    for subject in subjects.split(','):
        subject = subject.strip()
        courses, prereqs = extract_courses_and_prereqs(URL(subject.lower()), short=False)
        courses_with_prereqs.extend(course for course in courses if prereqs.get(course))
        all_courses.extend(courses)
        all_prereqs.update(prereqs)
    
    cg = CourseGraph(all_prereqs)

    selected = st.multiselect("Select target courses (with prerequisites):", sorted(courses_with_prereqs))
    exclude = st.multiselect("Exclude courses:", sorted(all_courses))
    include_coreqs = st.checkbox("Include corequisites", value=True)

    if selected:
        subgraph = cg.get_subgraph(selected, include_coreqs=include_coreqs, as_dict=True)
        
        if exclude:
            subgraph = {course: prereqs for course, prereqs in subgraph.items() if course not in exclude}
            for course in subgraph:
                subgraph[course] = [pr for pr in subgraph[course] if pr[0] not in exclude]
        
        layers = list_of_lists(subgraph, include_coreqs=include_coreqs)
        visualize_lol(layers, subgraph, include_coreqs=include_coreqs)
