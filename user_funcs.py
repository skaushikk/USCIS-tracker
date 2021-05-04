import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from tabulate import tabulate
import altair as alt
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import pytz

base = 'https://egov.uscis.gov/casestatus/mycasestatus.do?appReceiptNum='


@st.cache
def load_data(file):
    df = pd.read_csv(file)
    df = df[~df.ReceiptNo.isnull()]
    df['serial'] = df.ReceiptNo.str.slice(3, 13).astype(np.int64)
    return df


def get_filename(series, delta):
    tz = pytz.timezone('America/Chicago')
    yesterday = datetime.now(tz) - timedelta(days=delta)
    name = datetime.strftime(yesterday, '%Y-%m-%d')
    return f's3://uscis-receipt-status/DATA/{series}/{name}.csv'


def variable_window(df, rno_start, rno_end):
    df_window = df.loc[((df.serial >= rno_start) & (df.serial <= rno_end))]
    return df_window


def summary(df):
    df_summary = df.loc[df.FormNo.isin(['765', '131', '485', '140']), :]
    df_summary = df_summary.groupby(['FormNo', 'Status']).count()[['serial']]
    df_summary.columns = ['Count']
    print(df_summary)
    df_summary.reset_index(inplace=True)
    print(tabulate(df_summary, headers='keys', tablefmt='psql'))


def get_status(link):
    try:
        page = requests.get(link)
    except requests.exceptions.ConnectionError:
        return None
    soup = BeautifulSoup(page.text)
    source = soup.find('div', {'class': 'rows text-center'})
    rno = link[-13:]
    try:
        header = source.h1.text
        text = source.p.text
    except:
        print(rno)
        return None
    try:
        fno = re.search(r' I-(\w+)', source.p.text).group(1)
    except:
        fno = '765'
    return rno, fno, header, text


approved_list = ['Card Was Delivered To Me By The Post Office',
                 'Document Was Mailed To Me',
                 'Card Is Being Returned to USCIS by Post Office',
                 'Card Was Returned To USCIS',
                 'Case Was Approved',
                 'Card Was Mailed To Me',
                 'Card Was Picked Up By The United States Postal Service',
                 'New Card Is Being Produced',
                 'Card Was '
                 ]


# rename statuses to approved, rejected, pending

def rename_status(status):
    status = str(status)
    if status in approved_list:
        return 'Approved'
    elif re.search(re.compile(r'Rejected|Denied'), status):
        return 'Rejected'
    elif re.search(r'Evidence', status):
        return 'RFE'
    elif status == 'Case Was Received':
        return 'Received'
    elif status == 'Case Was Updated To Show Fingerprints Were Taken':
        return 'FingerPrints Completed'
    elif re.search(r'Transfer', status):
        return 'Transferred'
    else:
        return 'Pending'
