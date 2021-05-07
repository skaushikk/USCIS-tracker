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

    st.title('USCIS Case Analyzer')
    st.header('Input Data')
    st_series = st.selectbox('Select the Receipt # Series:', ('SRC', 'MSC', 'LIN'))

    # st_rno = st.text_input('Input your reference Receipt Number', 'SRC2190050100')

    st_start_rnge = 5000
    st_end_rnge = 5000

    loop = True
    td = 0
    while loop:
        try:
            _df = user_funcs.load_data(user_funcs.get_filename(st_series, td))
            break
        except FileNotFoundError:
            td += 1
            pass

    rno_start = int(_df.iloc[0]['ReceiptNo'][3:])
    rno_end = int(_df.iloc[-1]['ReceiptNo'][3:])

    st_no = rno_start + (rno_end - rno_start) // 2
    # st.write(rno_start, rno_end)

    a, b = st.slider('Select the Receipt Number Range', min_value=rno_start, max_value=rno_end,
                     value=(st_no - st_start_rnge, st_no + st_end_rnge), step=1)

    st.write('Range:', b - a)
    st.write(f'Analyzing Cases Between:')
    st.markdown(f"<h4 style='text-align: center;'> {st_series}-{a}&nbsp;&nbsp&nbsp;&nbsp&nbsp;&nbsp;{st_series}-{b}</h2>", unsafe_allow_html=True)
    # filename = f's3://uscis-receipt-status/DATA/{st_series}/{st_date}.csv'

    ##########################################################################
    # ------------------ Windowed Data ------------------------------------------#
    ##########################################################################
    df_window = user_funcs.variable_window(_df, a, b).reset_index()
    df_window = df_window[['ReceiptNo', 'FormNo', 'Status', 'serial']]

    st.header('Analysis')
    st.write('Number of Data Points:', len(df_window))

    with st.beta_expander('Case Distribution', expanded=False):
        # st.dataframe(df_window, width=1024)

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
        st.markdown(
            f"<h3 style='text-align: center; color: green;'>Form I-{df_window_counts.iloc[0][0]} applications have the highest count of {df_window_counts.iloc[0][1]}</h2>",
            unsafe_allow_html=True)
    ####
    # with st.beta_expander('Breakdown by the Case Type and Status', expanded=False):
        df_window_top = df_window.groupby(['FormNo', 'Status']).count()['ReceiptNo'].groupby('FormNo',
                                                                                             group_keys=False).nlargest(
            4).reset_index()
        df_window_top = df_window_top[df_window_top.FormNo.isin(['765', '131', '485', '140'])]
        df_window_top.columns = ['FormNo', 'Status', 'Count']

        st.dataframe(df_window_top)

        ####### SUMMARY PLOT #################

        st.subheader('Applications Distribution by Case # and Status')
        alt_chart1 = alt.Chart(df_window_top).mark_bar(opacity=0.7).encode(
            x=alt.X("Status:O", axis=None, title=None),
            y=alt.Y('Count:Q', stack=None),
            color=alt.Color("Status", title=None),
            column=alt.Column('FormNo', title=None)
        ).properties(
            width=75,
            height=250).interactive()
        st.write(alt_chart1)

    ##########################################################################
    # ------------------ Windowed Application Analysis----------------------------#
    ##########################################################################
    with st.beta_expander('Analysis for an Application Type'):
        st_formno = st.selectbox('Select the Form Number:', df_window.FormNo.value_counts().index.to_list())

        st.write(f'Summarized data for forms i-{st_formno} in the selected window')
        _df_window = df_window.loc[df_window.FormNo.isin([st_formno]), :]
        df_window_summary = _df_window.groupby(['FormNo', 'Status']).count().reset_index()[
            ['FormNo', 'Status', 'ReceiptNo']].rename(columns={'ReceiptNo': 'Number of Cases'})
        # st.dataframe(df_window_summary, width=50000)

        ##########################################################################
        # ------------------ Windowed Application Bucket Analysis----------------------------#
        ##########################################################################
        refine = st.select_slider('Select the refinement', ['Fine', 'Medium', 'Course'], value='Medium', key='Medium')
        if refine == 'Fine':
            alpha = 20
        elif refine == 'Medium':
            alpha = 10
        else:
            alpha = 5

        st_binsize = (b - a) // alpha

        # st_binsize = st.number_input('Enter the bucket size', value=2000, step=25, min_value=5)
        st_bin_no = alpha

        cuts = pd.cut(df_window['serial'], bins=st_bin_no).to_list()
        df_window['cuts'] = cuts
        df_f = df_window.loc[df_window['FormNo'] == st_formno].reset_index(drop=True)

        df_f = df_f.astype({'cuts': 'str'})
        df_f['cuts'] = df_f.apply(
            lambda row: f"({str(row.cuts.split(',')[0][1:11])} - {str(row.cuts.split(',')[1][:11])})",
            axis=1)

        df_f['cstatus'] = df_f['Status'].apply(user_funcs.rename_status)

        df4 = df_f.groupby('cuts').count()['ReceiptNo'].reset_index()
        df4.columns = ['cuts', 'TotalCount']

        df5 = df_f.groupby(['cuts', 'cstatus']).count()['serial'].groupby('cuts', group_keys=False).nlargest(
            4).reset_index()
        df5.columns = ['cuts', 'status', 'count']

        df5 = pd.merge(df5, df4, on='cuts')
        df5['ratio'] = df5['count'] / df5['TotalCount']
        df6 = df5.reset_index().sort_values(['status', 'index'])
        df6['caseno'] = df6['cuts'].apply(lambda x: int(x[1:12]))

        ##########################################################################
        # ------------------ Windowed Bucket Analysis Plots----------------------------#
        ##########################################################################
        status_list = ['Approved', 'Rejected', 'RFE', 'Received', 'FingerPrints Completed', 'Transferred']
        color_list = ['green', 'red', 'yellow', 'blue', 'orange', 'aqua']

        st.header(f'I-{st_formno} Status by the buckets')
        st.subheader(f'I-{st_formno} Status Ratios')
        alt_chart2 = alt.Chart(df6).mark_area(opacity=0.6).encode(
            x=alt.X("caseno:O", title='Case Numbers'),
            y=alt.Y("ratio:Q", stack='normalize'),
            color=alt.Color("status:N", scale=alt.Scale(domain=status_list, range=color_list)),
            tooltip=[alt.Tooltip('ratio:N'), alt.Tooltip('status:N')]
        ).properties(
            width=900,
            height=400).properties(title=f'{st_series} Series, I-{st_formno} Status Distribution - Ratio').interactive()
        st.write(alt_chart2)

        st.subheader(f'I-{st_formno} Status Counts')
        al2 = alt.Chart(df5).mark_bar(opacity=0.6).encode(
            x=alt.X("cuts:O", title='Case Number Buckets'),
            y=alt.Y('count:Q', stack='zero'),
            color=alt.Color("status", scale=alt.Scale(domain=status_list, range=color_list)),
            tooltip=[alt.Tooltip('count:N'), alt.Tooltip('status:N')]
        ).properties(
            width=900,
            height=400).interactive()
        st.write(al2)
#################################################
