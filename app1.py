import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import user_funcs
import pandas as pd
import altair as alt
import altair_viewer


def app():
    sns.set()
    st.title('USCIS Case Status Tracker App')
    rno = st.text_input('Input your reference Receipt Number', 'SRC2190061566')
    series = rno[:3]
    serial = int(rno[3:])
    st.write(series, serial)
    ##########################################################################

    # extract USCIS status
    with st.beta_expander('Case Details', expanded=False):
        link = user_funcs.base + rno
        try:
            _, formno, case_status, case_desc = user_funcs.get_status(link)
            if _ and formno is None:
                formno = '765'
            # st.header('Case Details')

            st.write(f'Form I-{formno}')
            st.markdown("<h2 style='text-align: center; color: blue;'>CASE STATUS</h2>",  unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: black;'>{case_status}</h2>",  unsafe_allow_html=True)
            st.write('------------------------------------')
            st.write(case_desc)
            er = False
        except:
            st.write('---------------   CASE DOES NOT EXIST   -------------------')
            er = True
    ############################################################################

    # range analysis
    with st.beta_expander('Range Analysis', expanded=False):
        if er:
            st.write('---------------   INPUT VALID RECEIPT NUMBER   ------------------- ')
            return
        rnge = st.number_input('Input Number of Cases to Analyze', value=10000)
        rng_start, rng_end = serial - rnge // 2, serial + rnge // 2

        try:
            _df = user_funcs.load_data(user_funcs.get_filename(series, 0))
        except FileNotFoundError:
            _df = user_funcs.load_data(user_funcs.get_filename(series, 1))

        df_window = user_funcs.variable_window(_df, rng_start, rng_end).reset_index()
        df_window = df_window[['ReceiptNo', 'FormNo', 'Status', 'serial']].rename(columns={'serial': 'Serial'})

        st.header('Number of cases by the Form # (Application type)')
        col1, col2 = st.beta_columns((2, 1))
        with col1:
            fig, ax1 = plt.subplots()
            df_window_counts = df_window.FormNo.value_counts().to_frame().reset_index()
            df_window_counts.columns = ['FormNo', 'Count']
            sns.barplot(data=df_window_counts, x='FormNo', y='Count')
            st.pyplot(fig)
        with col2:
            st.dataframe(df_window_counts, width=1024)

        # alt_chart = alt.Chart(df_window_counts).mark_bar().encode(x='FormNo',
        #                                                           y='Count', color=alt.Color('FormNo:N')).interactive()
        # st.write(alt_chart)

        df_window_series = df_window[df_window['FormNo'] == formno]
        # st.dataframe(df_window_series)
        series_total = df_window_series.shape[0]
        df_window_series['Status'] = df_window_series['Status'].apply(user_funcs.rename_status)
        df_window_series_group = df_window_series.groupby('Status').count()['Serial'].reset_index().rename(
            columns={'Serial': 'Count'})

        df_window_series_group['Ratio'] = df_window_series_group.Count / series_total
        df_window_series_group['Percent'] = df_window_series_group['Ratio'].apply(lambda x: "{:.0%}".format(x))

        st.header('Distrubution of the cases by STATUS')
        col3, col4 = st.beta_columns((1, 1))
        with col3:
            fig, ax1 = plt.subplots()
            sns.barplot(data=df_window_series_group, x='Status', y='Ratio')
            ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90, horizontalalignment='right')
            st.pyplot(fig)
        with col4:
            st.dataframe(df_window_series_group[['Status', 'Percent']], width=1024, height=2025)

        approved = df_window_series_group.loc[df_window_series_group.Status == 'Approved', 'Percent']
        pending = df_window_series_group.loc[df_window_series_group.Status.str.contains('Pending'), 'Ratio']
        st.header('Approval Ratio')
        summary1= f"{approved.values[0]} of the similar cases are APPROVED."
        summary2 = f"{'{:.0%}'.format(pending.sum())} of cases are still PENDING."

        st.markdown(f"<h2 style='text-align: center; color: green;'>{summary1}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: orange;'>{summary2}</h2>", unsafe_allow_html=True)
