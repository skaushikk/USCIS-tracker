import streamlit as st


def app():
    st.title('USCIS Case Status Analyzer')
    with st.beta_expander("ABOUT", expanded=True):
        # st.subheader('ABOUT')
        st.write('USCIS Case Status Tracker app is built to help, people who have a pending '
                 'application with the United States Citizenship and Immigration Services (USCIS)'
                 'by educating, tracking, predicting their case with respect to other similar '
                 'applications. Similar applications are defined as those of the same kind, from same locations'
                 'and applied during similar times')

        st.write('The current indefinite uncertain timeline due to political climate, COVID protocols, '
                 'resulted in unprecedented strain on USCIS servicing capabilities and consequently piling on '
                 'extreme stress to the applicants with lives on hold waiting for the adjudication. ')
        st.write('Furthermore, this app provides a platform for more broader, indepth analysis and prediction')

    with st.beta_expander("DISCLAIMER", expanded=False):
        st.write('The application does not store any user information at all. All the information provided is from '
                 'publicly available data.')

    with st.beta_expander("KNOWLEDGEBASE", expanded=False):
        st.write("The details on different types of forms, terminology can be found in the USCIS information pages"
                 "https://www.uscis.gov/tools/a-z-index")
        # st.selectbox()