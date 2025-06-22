import logging
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import re

logging.basicConfig(level=logging.INFO, format='(%(levelname)s) %(message)s')

def split_course_code(course_code):
    return re.split(r'\xa0', course_code)

def join_course_code(subj, code, short=False):
    if short:
        return f'{subj[0]}{code}'
    else:
        return f'{subj} {code}'

def extract_courses_and_prereqs(url, short=False):
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
        course = join_course_code(subj, code, short=short)
        course_list.append(course)
        prereq_dict[course] = []

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
                prereqs = []
                contents = list(attrblock.children)
                
                for i, element in enumerate(contents):
                    if isinstance(element, Tag) and element.name == 'a':
                        text = element.get_text(strip=True)
                        psubj, pcode = split_course_code(text)
                        logging.debug(f'{psubj} - {pcode}')
                        prereq_code = join_course_code(psubj, pcode, short=short)
                        
                        is_coreq = False
                        if i + 1 < len(contents):
                            next_item = contents[i + 1]
                            if isinstance(next_item, NavigableString) and "*" in next_item:
                                is_coreq = True
                        prereqs.append((prereq_code, "coreq" if is_coreq else "prereq"))
                
                prereq_dict[course] = prereqs

    return course_list, prereq_dict