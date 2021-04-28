import streamlit as st
import altair as altair
import user_funcs
import pandas as pd
import seaborn as sns
from tabulate import tabulate
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import altair as alt
import numpy as np
import boto3
import s3fs


import app1
import app2

sns.set()

PAGES = {
    "Case Analysis": app1,
    "Range Analysis": app2
}
st.sidebar.title('Navigation')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app()