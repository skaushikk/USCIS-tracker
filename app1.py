import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import user_funcs



def app():
    sns.set()
    st.title('USCIS Case Status Tracker App')
    rno = st.text_input('Input your reference Receipt Number','SRC2190061566')
    series = rno[:3]
    serial = int(rno[3:])
    st.write(series, serial)
    ##########################################################################

    # extract USCIS status
    with st.beta_expander('Case Details'):
        link = user_funcs.base + rno
        _, formno, case_status, case_desc = user_funcs.get_status(link)
        if _ and formno is None:
            formno = '765'
        st.write('Application Type:', formno)
        st.write('Your Case Status:')
        st.write(case_status)
        st.write('Your Case Description:')
        st.write(case_desc)
    ############################################################################

    # range analysis
    with st.beta_expander('Range Analysis', expanded=True):
        rnge = st.number_input('Input your range', 1000)
        clicked = st.button('Click me!')
        rng_start, rng_end = serial - rnge, serial + rnge

        # filename = f's3://uscis-receipt-status/DATA/{series}/{st_date}.csv'
        try:
            _df = user_funcs.load_data(user_funcs.get_filename(series, 0))
        except FileNotFoundError:
            _df = user_funcs.load_data(user_funcs.get_filename(series, 1))

        df_window = user_funcs.variable_window(_df, rng_start, rng_end).reset_index()
        df_window = df_window[['ReceiptNo', 'FormNo', 'Status', 'serial']].rename(columns={'serial':'Serial'})

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

        df_window_series = df_window[df_window['FormNo'] == formno]
        # st.dataframe(df_window_series)
        series_total = df_window_series.shape[0]
        df_window_series.Status = np.where(df_window_series.Status.isin(user_funcs.approved_list), 'Approved',
                                           df_window_series.Status)
        df_window_series['Status'] = np.where(df_window_series.Status.str.contains('Reject|Denied'), 'Rejected',
                                              df_window_series.Status)

        df_window_series_group = df_window_series.groupby('Status').count()['Serial'].reset_index().rename(columns={'Serial':'Count'})

        df_window_series_group['Ratio'] = df_window_series_group.Count / series_total
        col3, col4 = st.beta_columns((1, 1))
        with col3:
            fig, ax1 = plt.subplots()
            sns.barplot(data=df_window_series_group, x='Status', y='Ratio')
            ax1.set_xticklabels(ax1.get_xticklabels(), rotation=90, horizontalalignment='right')
            st.pyplot(fig)
        with col4:
            st.dataframe(df_window_series_group[['Status', 'Ratio']], width=1024)
