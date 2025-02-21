import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
import requests



def data_collection():
    odata_urls = [
        'https://survey.kuklpid.gov.np/v1/projects/20/forms/kukl_customer_survey_phase1.svc'
    ]
    submission_entity_set = 'Submissions'
    username = 'anupthatal2@gmail.com'
    password = 'Super@8848'
    session = requests.Session()
    session.auth = (username, password)
    
    all_dfs = []  # List to store DataFrames from each URL
    
    for odata_url in odata_urls:
        submission_url = f"{odata_url}/{submission_entity_set}"
        response = session.get(submission_url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['value'])
            pd.set_option('display.max_columns', None)
            print(df)
            df['lat'] = df['b02'].apply(lambda x: x['coordinates'][1] if isinstance(x, dict) and 'coordinates' in x else None)
            df['lon'] = df['b02'].apply(lambda x: x['coordinates'][0] if isinstance(x, dict) and 'coordinates' in x else None)
            customer = []
            connection = []
            submittername = []
            reviewState = []
            for i in df['gb12_skip']:
                customer.append(i['gc01_skp1']['gc20']['c20'])
                connection.append(i['gc01_skp1']['gc20']['c22'])
            for i in df['__system']:
                submittername.append(i['submitterName'])
                reviewState.append(i['reviewState'])
            # for i in df['gb10-b10_package']:
            #     packages.append(i['b10_dni']['b10_dmi'])
            #     print(packages)
            df['ReviewState'] = reviewState
            df['SubmitterName'] = submittername
            df['gb12_skip-gc01_skp1-gc20-c20'] = customer
            df['gb12_skip-gc01_skp1-gc20-c22'] = connection
            df['SubmitterName'] = df['SubmitterName'].str.upper()
            df = df[['b10_dmi','ward_number','unique_form_id','lat','lon','gb12_skip-gc01_skp1-gc20-c20', 'gb12_skip-gc01_skp1-gc20-c22','SubmitterName', 'ReviewState', 'unit_owners']]
            all_dfs.append(df)  # Append the processed DataFrame
    final_df = pd.concat(all_dfs, ignore_index=True)
    return final_df

df = data_collection()


# Sidebar
with st.sidebar:
    
    location=df['ward_number'].unique().tolist()
    # location_area=st.selectbox('Select location',location)
    areas_list = df['b10_dmi'].dropna().unique().tolist()
    selected_area = st.selectbox('Select Area', areas_list)
    if selected_area:
        filtered_df = df[df['b10_dmi'] == selected_area]
        # filtered_df=df1[df1['Areas']==location_area]
        # P=filtered_df['Packages']
        SDMA=filtered_df['b10_dmi'].unique().tolist()[0]
        ward=filtered_df['ward_number'].unique().tolist()[0]
    
        # person=filtered_df['Person']
        # phone=filtered_df['Phone']
        sub_dmi_counts = filtered_df['b10_dmi'].value_counts()
        st.write(f"ward of that areas :blue[{ward}]")
        # st.write(f'Packages of :blue[{packages}]')
        st.write(f"ward of :blue[{SDMA}]")
        # st.write(f'Person responsible :blue[{person}]')
        # st.write(f'Phone number of that person :blue[{phone}]')
        st.write(sub_dmi_counts)

# Main content
col1, = st.columns(1)  # Note the use of comma to unpack the list

with col1:
    if selected_area:
        # Filter DataFrame for selected area
        selected_df = df[df['b10_dmi'] == selected_area]

        # Drop rows with NaN values in location coordinates
        selected_df = selected_df.dropna(subset=['lat', 'lon'])

        # Extract latitude and longitude lists
        lat = selected_df['lat'].astype(float).tolist()
        lon = selected_df['lon'].astype(float).tolist()

        # Calculate the center of the map
        center_lat = sum(lat) / len(lat) if len(lat) > 0 else 0
        center_lon = sum(lon) / len(lon) if len(lon) > 0 else 0

        # Create a Folium map centered at the mean of coordinates
        folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=16)

        # Add markers for each location with smaller icon
        for i in range(len(lat)):
            folium.Marker([lat[i], lon[i]], icon=folium.Icon(icon="circle", prefix='fa', icon_color='blue', icon_size=(2,2))).add_to(folium_map)

        # Display the Folium map using streamlit_folium
        st_folium(folium_map,width=1000, height=500)
