import streamlit as st
import user_funcs
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
import numpy as np
import altair_viewer

sns.set()


##########################################################################
# ------------------ Total Data ------------------------------------------#
##########################################################################

def app():
    # st.set_page_config(layout="centered")
    # add_selectbox = st.sidebar.selectbox('How would you like to be contacted?', ('Email', 'Home phone', 'Mobile phone'))

    st.title('USCIS Case Status Tracker App')
    st.header('Input Data')
    st_series = st.selectbox('Select the Receipt # Series:', ('SRC', 'MSC'))
    st.write('You Selected -- ', st_series)

    # st_rno = st.text_input('Input your reference Receipt Number', 'SRC2190050100')

    st_start_rnge = 5000
    st_end_rnge = 5000

    _df = user_funcs.load_data(user_funcs.get_filename(st_series, 1))

    rno_start = int(_df.iloc[0]['ReceiptNo'][3:])
    rno_end = int(_df.iloc[-1]['ReceiptNo'][3:])

    st_no = rno_start + (rno_end - rno_start) // 2
    st.write(rno_start, rno_end)

    a, b = st.slider('Receipt # Range', min_value=rno_start, max_value=rno_end,
                     value=(st_no - st_start_rnge, st_no + st_end_rnge), step=1)

    st.write('Range:', b - a)

    # filename = f's3://uscis-receipt-status/DATA/{st_series}/{st_date}.csv'

    ##########################################################################
    # ------------------ Windowed Data ------------------------------------------#
    ##########################################################################
    df_window = user_funcs.variable_window(_df, a, b).reset_index()
    df_window = df_window[['ReceiptNo', 'FormNo', 'Status', 'serial']]

    st.header('Analysis for Selected Window')
    st.write('Number of Data Points:', len(df_window))
    st.subheader('Data for the selected window')
    st.dataframe(df_window, width=1024)

    # ax1 = sns.barplot(_df.FormNo.value_counts().index.to_list(), _df.FormNo.value_counts().to_list())
    st.subheader('Number of cases by the Form # (Application type)')
    col1, col2 = st.beta_columns((2, 1))
    with col1:
        fig, ax1 = plt.subplots()
        df_window_counts = df_window.FormNo.value_counts().to_frame().reset_index()
        df_window_counts.columns = ['FormNo', 'Count']
        sns.barplot(data=df_window_counts, x='FormNo', y='Count')
        st.pyplot(fig)
    with col2:
        st.dataframe(df_window_counts, width=1024)

    ####

    st.subheader('Breakdown by the Case type')
    df_window_top = df_window.groupby(['FormNo', 'Status']).count()['ReceiptNo'].groupby('FormNo',
                                                                                         group_keys=False).nlargest(
        4).reset_index()
    df_window_top = df_window_top[df_window_top.FormNo.isin(['765', '131', '485', '140'])]
    df_window_top.columns = ['FormNo', 'Status', 'Count']

    st.dataframe(df_window_top)

    # f2, ax3 = plt.subplots()
    ax3 = sns.catplot(data=df_window_top, kind='bar', x='FormNo', y='Count', hue='Status', height=4, aspect=2)
    ax3.set_xticklabels(rotation=90, ha="right")

    st.pyplot(ax3)

    ##########################################################################
    # ------------------ Windowed Application Analysis----------------------------#
    ##########################################################################
    with st.beta_expander('Analysis for an Application Type'):
        st_formno = st.selectbox('Select the Form Number:', df_window.FormNo.value_counts().index.to_list())

        st.write(f'Summarized data for forms i-{st_formno} in the selected window')
        _df_window = df_window.loc[df_window.FormNo.isin([st_formno]), :]
        df_window_summary = _df_window.groupby(['FormNo', 'Status']).count().reset_index()[
            ['FormNo', 'Status', 'ReceiptNo']].rename(columns={'ReceiptNo': 'Number of Cases'})
        st.dataframe(df_window_summary, width=50000)

        ##########################################################################
        # ------------------ Windowed Application Bucket Analysis----------------------------#
        ##########################################################################

        st_binsize = st.number_input('Enter the bucket size', value=2000, step=25, min_value=5)
        st_bin_no = (b - a) // st_binsize
        st.write(st_formno, a, b, st_binsize, st_bin_no)

        cuts = pd.cut(df_window['serial'], bins=st_bin_no).to_list()
        df_window['cuts'] = cuts
        df_f = df_window.loc[df_window['FormNo'] == st_formno]

        df_f = df_f.astype({'cuts': 'str'})
        df_f['cuts'] = df_f.apply(
            lambda row: f"({str(row.cuts.split(',')[0][1:11])} - {str(row.cuts.split(',')[1][:11])})",
            axis=1)
        # st.dataframe(df_f)

        df_f['cstatus'] = np.where(df_f.Status.isin(user_funcs.approved_list), 'Approved', df_f.Status)
        df_f['cstatus'] = np.where(df_f.cstatus.str.contains('Reject|Denied'), 'Rejected', df_f.cstatus)
        # st.dataframe(df_f)

        df5 = df_f.groupby(['cuts', 'cstatus']).count()['serial'].groupby('cuts', group_keys=False).nlargest(
            4).reset_index()
        df5.columns = ['cuts', 'status', 'count']

        df6 = df_f.groupby('cuts').count()['ReceiptNo'].reset_index()
        df6.columns = ['cuts', 'TotalCount']
        df5 = pd.merge(df5, df6, on='cuts')
        df5['ratio'] = df5['count'] / df5['TotalCount']

        # st.dataframe(df5)

        ##########################################################################
        # ------------------ Windowed Bucket Analysis Plots----------------------------#
        ##########################################################################

        st.subheader(f'I-{st_formno} Status by the buckets')

        palette = sns.color_palette("tab10")

        ax4 = sns.catplot(data=df5, kind='bar', x='cuts', y='ratio', hue='status', height=6, aspect=2, palette=palette)
        ax4.set_xticklabels(rotation=90, ha="right")
        ax4.fig.suptitle(f'{st_series} Series, I-{st_formno} Status Distribution - Ratio')
        st.pyplot(ax4)

        status_list = st.selectbox('Pick the status to plot', df5.status.value_counts().index.to_list())

        al2 = alt.Chart(df5).mark_bar(opacity=0.7).encode(
            x='cuts:O',
            y=alt.Y('count:Q', stack=None),
            color="status",
        ).interactive()
        st.write(al2)
