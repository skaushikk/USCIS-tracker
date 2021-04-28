import streamlit as st
import matplotlib.pyplot as plt
import boto3
import s3fs
import pandas as pd
import seaborn as sns
from tabulate import tabulate
import altair as alt
import altair_viewer
from collections import namedtuple
import requests
from bs4 import BeautifulSoup
import re

base = 'https://egov.uscis.gov/casestatus/mycasestatus.do?appReceiptNum='

alt.renderers.enable('altair_viewer')
sns.set(style="whitegrid", color_codes=True)

Case = namedtuple('case', ['series', 'start', 'end', 'length'])
src = Case('SRC', 2190010000, 2190110000, 100000)
msc = Case('MSC', 2190000001, 2190100001, 100000)


def catplotter(df, top_statuses=4):
    df5 = df.groupby(['cuts', 'Status']).count()['serial'].groupby('cuts', group_keys=False).nlargest(
        top_statuses).reset_index()
    palette = sns.color_palette("tab10")
    ax = sns.catplot(data=df5, kind='bar', x='cuts', y='serial', hue='Status', height=8, aspect=2, palette=palette)
    ax.set_xticklabels(rotation=40, ha="right")
    plt.show()


def altplotter(df, top_statuses=4):
    df5 = df.groupby(['cuts', 'Status']).count()['serial'].groupby('cuts', group_keys=False).nlargest(
        top_statuses).reset_index().reset_index()

    alt_chart = alt.Chart(df5).mark_bar().encode(
        x=alt.X('Status:O', axis=None),
        y='serial:Q',
        color='Status:N',
        column='cuts:N'
    ).properties(width=40).interactive()
    return alt_chart
    # altair_viewer.display(alt_chart)


def main(df, formno, bin_size):
    freq = bin_size  # input('Enter the bin size:')
    interval_range = pd.interval_range(start=df.serial[0], freq=int(freq), end=df.serial.iloc[-1])
    df['cuts'] = pd.cut(df['serial'], bins=interval_range, labels=range(1, len(interval_range)))

    df_f = df.loc[df['FormNo'] == formno]

    catplotter(df_f, 4)


def window(df, rno, formno, rnge, bin_size):
    rno_serial = int(rno[3:])
    df_window = df[abs(df.serial - rno_serial) <= rnge]
    return df_window


def bin_plotter(df, bin_size, formno):
    interval_range = pd.interval_range(start=df.iloc[0]['serial'], freq=int(bin_size),
                                       end=df.serial.iloc[-1])
    df['cuts'] = pd.cut(df['serial'], bins=interval_range, labels=range(1, len(interval_range)))
    df_f = df.loc[df['FormNo'] == formno]
    # catplotter(df_f, 3)
    altplotter(df_f, 3)


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
        return
    soup = BeautifulSoup(page.text, 'lxml')
    source = soup.find('div', {'class': 'rows text-center'})
    rno = link[-13:]
    try:
        fno = re.search(r' I-(\w+)', source.p.text)
    except:
        print(rno)
        fno = None
    fno_ = None if fno is None else fno.group(1)

    return rno, fno_, source.h1.text, source.p.text


approved_list = ['Card Was Delivered To Me By The Post Office',
                 'Document Was Mailed To Me',
                 'Card Is Being Returned to USCIS by Post Office',
                 'Card Was Returned To USCIS',
                 'Case Was Approved',
                 'Card Was Mailed To Me',
                 'Card Was Picked Up By The United States Postal Service',
                 'New Card Is Being Produced'
                 ]

if __name__ == '__main__':
    # filename = "s3://uscis-receipt-status/DATA/SRC/2021-04-26.csv"

    filename = 'DATA/SRC/2021-04-26.csv'
    _df = pd.read_csv(filename)
    _df['serial'] = _df.apply(lambda row: int(row.ReceiptNo[3:]), axis=1)
    # main(_df, '765', 5000)
    window(_df, 'SRC2190050100', '765', 1000, 200)
    # (summary(_df, '765'))
