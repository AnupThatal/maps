import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import configparser
import os

git_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.git')
config_file_path = os.path.join(git_dir, 'config.ini')

print(f"git_dir: {git_dir}")
print(f"config_file_path: {config_file_path}")


config = configparser.ConfigParser()
config.read(config_file_path)

start = time.time()

@st.cache_data
def fetch_and_process_data(sdma):
    odata_urls = [
        'https://survey.kuklpid.gov.np/v1/projects/7/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/7/forms/kukl_customer_survey.svc',
        'https://survey.kuklpid.gov.np/v1/projects/15/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/9/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/6/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/2/forms/kukl_customer_survey_01.svc',
        'https://survey.kuklpid.gov.np/v1/projects/2/forms/kukl_customer_survey.svc',
        'https://survey.kuklpid.gov.np/v1/projects/16/forms/kukl_customer_survey_01.svc'
    ]

    headers = {'Accept': 'application/json'}  
    
    params = {
        '$select': 'unique_form_id,b10_sub_dmi,gb12_skip/gc01_skp1/gc20/c20,gb12_skip/gc01_skp1/gc20/c22,__system/submitterName,__system/reviewState,b02,unit_owners,gb12_skip/gc01_skp2/d08',
    }
    
    submission_entity_set = 'Submissions'
    username = config['Credentials']['username']
    password = config['Credentials']['password']
    session = requests.Session()
    session.auth = (username, password)

    all_dfs = []
    for odata_url in odata_urls:
        submission_url = f"{odata_url}/{submission_entity_set}"
        try:
            response = session.get(submission_url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()

            if 'value' in data:
                df = pd.DataFrame(data['value'])

                if 'b10_sub_dmi' in df.columns:
                    if not df.empty:
                        all_dfs.append(df)

        except requests.exceptions.RequestException as e:
            continue 

    if not all_dfs:
        st.warning("No data retrieved for the specified location.")
        return pd.DataFrame()

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df['gb12_skip-gc01_skp1-gc20-c20'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c20'))
    final_df['gb12_skip-gc01_skp1-gc20-c22'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c22'))
    final_df['SubmitterName'] = final_df['__system'].apply(lambda x: x['submitterName'] if 'submitterName' in x else None).str.upper()
    final_df['ReviewState'] = final_df['__system'].apply(lambda x: x['reviewState'] if 'reviewState' in x else None)
    final_df['b02-Longitude'] = final_df['b02'].apply(lambda x: x['coordinates'][0] if (x and 'coordinates' in x) else None)
    final_df['b02-Latitude'] = final_df['b02'].apply(lambda x: x['coordinates'][1] if (x and 'coordinates' in x) else None)
    final_df['gb12_skip-gc01_skp2-d08'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp2', {}).get('d08'))

    return final_df

st.set_page_config(page_title="Map Display App", page_icon=":earth_americas:")
st.title("Data Fetch and Map Display App")
location_area = st.text_input('Select location')
total_df=pd.read_csv('HHC_Data.csv')
total_df['sDMA'] = total_df['sDMA'].str.replace('.','')
total_df['SDMA wise HHC'] = total_df['SDMA wise HHC'].str.replace(',', '')
total_df['SDMA wise HHC'] = total_df['SDMA wise HHC'].str.replace(' ','')
total = total_df[total_df['sDMA'] == location_area]
if location_area:
    try:
        result_df = fetch_and_process_data(sdma=location_area)
        
    except Exception as e:
        st.warning("An error occurred while fetching data. Please try again later.")
else:
    result_df = pd.DataFrame()

# Display map or warning
if not result_df.empty:
        st.success(f"Data successfully retrieved and processed of sub_dma: {location_area}")
        selected_df = result_df[result_df['b10_sub_dmi'] == location_area].dropna(subset=['b02-Latitude', 'b02-Longitude'])
        num=selected_df['unique_form_id'].nunique()
        st.caption(f"Data of collection of that areas: {num}")
        tc=total['SDMA wise HHC'].values[0]
        st.caption(f"Total data of that areas: {tc}")
        if not selected_df.empty:
            fig = px.scatter_mapbox(selected_df, 
                                    lat='b02-Latitude', 
                                    lon='b02-Longitude', 
                                    hover_name='SubmitterName', 
                                    zoom=15,
                                    height=800)

            fig.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig)
            end=time.time()
            diff=start-end
            st.write(f'details of time taken {diff}')
