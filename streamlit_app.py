import streamlit as st
import seaborn as sns

import app1
import app2
import about_page

sns.set()

PAGES = {
    "About": about_page,
    "Case Analysis": app1,
    "Range Analysis": app2
}
st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app()
