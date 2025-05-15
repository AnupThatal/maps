import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from ipyleaflet import Map, Marker, Polyline, Polygon, LayersControl, basemaps, basemap_to_tiles
from ipywidgets import HTML
from branca.colormap import linear


# 1. Data Collection Function (Same as yours)

def data_collection():
    odata_urls = [
        'https://survey.kuklpid.gov.np/v1/projects/20/forms/kukl_customer_survey_phase1.svc',
        'https://survey.kuklpid.gov.np/v1/projects/20/forms/kukl_customer_survey_phase2.svc'
    ]
    params = {
        '$select': 'unique_form_id,b10_dmi,gb12_skip/gc01_skp1/gc20/c20,gb12_skip/gc01_skp1/gc20/c22,__system/submitterName,__system/reviewState,b02,unit_owners,gb12_skip/gc01_skp2/d08,__system/attachmentsPresent,__system/attachmentsExpected,meta/instanceName'
    }
    session = requests.Session()
    session.auth = ('anupthatal2@gmail.com', 'Super@8848')
    all_dfs = []

    for odata_url in odata_urls:
        submission_url = f"{odata_url}/Submissions"
        response = session.get(submission_url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'value' in data:
                df = pd.DataFrame(data['value'])
                df['url'] = odata_url
                all_dfs.append(df)

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df['gb12_skip-gc01_skp1-gc20-c20'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c20'))
    final_df['gb12_skip-gc01_skp1-gc20-c22'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp1', {}).get('gc20', {}).get('c22'))
    final_df['SubmitterName'] = final_df['__system'].apply(lambda x: x['submitterName'] if 'submitterName' in x else None).str.upper()
    final_df['ReviewState'] = final_df['__system'].apply(lambda x: x['reviewState'] if 'reviewState' in x else None)
    final_df['b02-Longitude'] = final_df['b02'].apply(lambda x: x['coordinates'][0] if (x and 'coordinates' in x) else None)
    final_df['b02-Latitude'] = final_df['b02'].apply(lambda x: x['coordinates'][1] if (x and 'coordinates' in x) else None)
    final_df['gb12_skip-gc01_skp2-d08'] = final_df['gb12_skip'].apply(lambda x: x.get('gc01_skp2', {}).get('d08'))
    final_df['AttachmentsPresent'] = final_df['__system'].apply(lambda x: x['attachmentsPresent'] if 'attachmentsPresent' in x else None)
    final_df['AttachmentsExpected'] = final_df['__system'].apply(lambda x: x['attachmentsExpected'] if 'attachmentsExpected' in x else None)
    final_df['InstanceName'] = final_df['meta'].apply(lambda x: x['instanceName'] if 'instanceName' in x else None)

    return final_df

# 2. Load Data
df = data_collection()

selected_area = st.sidebar.selectbox('Select DMA', df['b10_dmi'].dropna().unique().tolist())
filtered_df = df[df['b10_dmi'] == selected_area]
filtered_df = filtered_df.dropna(subset=['b02-Latitude', 'b02-Longitude'])
print(filtered_df)
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            min-width: 200px;
            max-width: 200px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# 5. Generate Map using ipyleaflet
def display_ipyleaflet_map(data):
    basemap_options = {
    "Open Street Map": "open-street-map",
    "Carto Positron (Light)": "carto-positron",
    "Carto Darkmatter (Dark)": "carto-darkmatter",
    "Stamen Terrain": "stamen-terrain",
    "White Background": "white-bg"
}

    selected_basemap = st.sidebar.selectbox("Select Basemap Style", list(basemap_options.keys()))
    selected_style = basemap_options[selected_basemap]

    center_lat = data['b02-Latitude'].mean()
    center_lon = data['b02-Longitude'].mean()
    fig=px.scatter_mapbox(data,lat='b02-Latitude',size_max=20,lon='b02-Longitude',color='SubmitterName',zoom=11,height=500,hover_name='gb12_skip-gc01_skp1-gc20-c22',width=800)

    

    fig.update_layout(mapbox_style=selected_style,mapbox_center={"lat": center_lat, "lon": center_lon},dragmode='pan',margin={"r":0,"t":0,"l":0,"b":0},  legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5,
        font=dict(size=10)
    ))


    return fig,center_lat, center_lon

st.markdown("### Map View")
px_map, center_lat, center_lon = display_ipyleaflet_map(data=filtered_df)
st.plotly_chart(px_map,use_container_width=True)
st.markdown(f"**Map Center Coordinates:** Latitude: `{center_lat:.5f}`, Longitude: `{center_lon:.5f}`")
