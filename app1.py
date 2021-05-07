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
    st.title('USCIS Case Snapshot')
    rno = st.text_input('Input your reference Receipt Number', 'SRC2190061566')
    series = rno[:3]
    serial = int(rno[3:])
    ##########################################################################

    # extract USCIS status
    with st.beta_expander('Case Details', expanded=False):
        link = user_funcs.base + rno
        er = False
        _, formno, case_status, case_desc = user_funcs.get_status(link)
        if case_status == '' or case_desc == '':
            er = True
            st.write('---------------   CASE DOES NOT EXIST   -------------------')
        else:
            st.write(f'Form I-{formno}')
            st.markdown("<h2 style='text-align: center;'>CASE STATUS</h2>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center;color: #0DDBEE;'>{case_status}</h2>", unsafe_allow_html=True)
            st.write('------------------------------------')
            st.write(case_desc)
            er = False

    ############################################################################

    # range analysis
    loop = True
    td = 0
    while loop:
        try:
            _df = user_funcs.load_data(user_funcs.get_filename(series, td))
            break
        except FileNotFoundError:
            td += 1
            pass


###########################
        # st.header('Number of cases by the Form # (Application type)')
        # col1, col2 = st.beta_columns((2, 1))
        # with col1:
        #     fig, ax1 = plt.subplots()
        #     df_window_counts = df_window.FormNo.value_counts().to_frame().reset_index()
        #     df_window_counts.columns = ['FormNo', 'Count']
        #     sns.barplot(data=df_window_counts, x='FormNo', y='Count')
        #     st.pyplot(fig)
        # with col2:
        #     st.dataframe(df_window_counts, width=1024)
#############################
    with st.beta_expander('Similar Applications', expanded=False):
        if er:
            st.write('---------------   INPUT VALID RECEIPT NUMBER   ------------------- ')
            return
        st.header('Similar Application Range')
        # rnge = st.number_input('Input Number of Cases to Analyze', value=10000)

        rnge = st.slider('Pick the number of applications around your case to analyze', min_value=100, max_value=10000,
                     value=5000, step=50)
        rng_start, rng_end = serial - 3 * rnge // 4, serial + rnge // 4
        df_window = user_funcs.variable_window(_df, rng_start, rng_end).reset_index()
        df_window = df_window[['ReceiptNo', 'FormNo', 'Status', 'serial']].rename(columns={'serial': 'Serial'})

        df_window_series = df_window[df_window['FormNo'] == formno]
        series_total = df_window_series.shape[0]
        df_window_series['Status'] = df_window_series['Status'].apply(user_funcs.rename_status)
        df_window_series_group = df_window_series.groupby('Status').count()['Serial'].reset_index().rename(
            columns={'Serial': 'Count'})

        df_window_series_group['Ratio'] = df_window_series_group.Count / series_total
        df_window_series_group['Percent'] = df_window_series_group['Ratio'].apply(lambda x: "{:.0%}".format(x))
        # st.dataframe(df_window_series_group)

        st.header('Status distribution of similar applications')
        st.subheader(f'Within the selected {rnge} applications')
        # col3, col4 = st.beta_columns((1, 1))
        # with col3:
        #     fig, ax1 = plt.subplots()
        #     sns.barplot(data=df_window_series_group, x='Status', y='Ratio')
        #     ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90, horizontalalignment='right')
        #     st.pyplot(fig)
        # with col4:
        #     st.dataframe(df_window_series_group[['Status', 'Percent']], width=1024, height=2025)

        al1 = alt.Chart(df_window_series_group).mark_bar().encode(
            x='Status',
            y='Ratio',
            color='Status',
            tooltip = alt.Tooltip(['Ratio:Q'])
        ).properties(
            width=700,
            height=400).interactive()
        st.write(al1)


        approved = df_window_series_group.loc[df_window_series_group.Status == 'Approved', 'Percent']
        pending = df_window_series_group.loc[df_window_series_group.Status.str.contains('Pending|Transferred|Received'), 'Ratio']
        rejected = df_window_series_group.loc[df_window_series_group.Status == 'Rejected', 'Percent']

        st.header('Approval Ratio')
        summary1 = f"{approved.values[0]} of the similar cases are APPROVED."
        summary2 = f"{'{:.0%}'.format(pending.sum())} of cases are still PENDING."
        summary3 = f"{rejected.values[0]} of the similar cases are REJECTED."

        st.markdown(f"<h2 style='text-align: center; color: green;'>{summary1}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: orange;'>{summary2}</h2>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: red;'>{summary3}</h2>", unsafe_allow_html=True)
