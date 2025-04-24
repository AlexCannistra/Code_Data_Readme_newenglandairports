"""
Project on New England Airports Program

Creator: Alex Cannistra
Data: New England_Airports

Description:
The purpose of this program, the New England Airports Data Explorer,
is supposed to be an interactive web application that enables users
to explore, analyze, and visualize any airport-related data across
the various New England states. With Streamlit integration, this
python program allows users to filter airports by different attributes
such as elevation, runway length, type, and location through  sidebar
controls. This program has several dynamic visualizations, including
bar charts, pie charts, and an interactive heatmap with hoverable
"tooltips" to look into the data in a specific area. Also, it provides
tools for data analysis like pivot tables and top-ranked lists,
giving the user ability to uncover trends, distributions, and regional
patterns in airport info. This application can be used by anyone but is
especially ideal for aviation enthusiasts, researchers, or policymakers
looking to gain insights into airport characteristics and their spatial
distribution across Massachusetts, Connecticut, Rhode Island, New Hampshire,
Vermont, and Maine.
"""

#imports for graphical Analysis Streamlit Access, etc
import pandas as pd
import streamlit as st
import pydeck as pdk
import matplotlib.pyplot as plt


#Loading / Cleaning our Data [DA7]
def load_and_prepare_data(file_path):
    #Read the CSV new_england_airports file
    df = pd.read_csv(file_path)

    #Filter for our New England states
    new_england_states = ['US-MA', 'US-CT', 'US-RI', 'US-NH', 'US-VT', 'US-ME']
    df = df[df['iso_region'].isin(new_england_states)]

    #Drop Columns
    columns_to_drop = ['continent', 'iata_code', 'home_link', 'keywords', 'gps_code']
    df = df.drop(columns=columns_to_drop, axis=1)

    df['elevation_ft'] = df['elevation_ft'].fillna(df['elevation_ft'].median())
    df = df.dropna(subset=['municipality'])

    df['elevation_category'] = df['elevation_ft'].apply(
        lambda x: 'Low' if x < 200 else 'Medium' if x < 1000 else 'High') #[DA1]
    return df

file_path = "new_england_airports(in).csv"
data = load_and_prepare_data(file_path)

#Data Analysis Function [PY2] [DA9]
def analyze_airport_data(df):
    try: #[PY3]
        total_airports = len(df)
        avg_elevation = df['elevation_ft'].mean()
        airport_counts = df['type'].value_counts().to_dict() #[PY5]
        return total_airports, avg_elevation, airport_counts
    except Exception as e:
        st.error(f"Error during analysis: {e}")
        return None, None, {}


#Running Streamlit
def run_airport_explorer(df):
    st.title("New England Airports Data Explorer")

    #Sidebar Filter (remove and add, select back) [ST1]
    st.sidebar.title("Filters")
    selected_state = st.sidebar.multiselect("Select State(s)", options=df['iso_region'].unique(),
                                            default=df['iso_region'].unique())
    selected_type = st.sidebar.multiselect("Select Airport Type(s)", options=df['type'].unique(),
                                           default=df['type'].unique())
    selected_elevation = st.sidebar.multiselect("Select Elevation Category", options=df['elevation_category'].unique(),
                                                default=df['elevation_category'].unique())

    #Numeric Filters [ST2]
    st.sidebar.title("Numeric Filters")
    min_elevation = int(df['elevation_ft'].min())
    max_elevation = int(df['elevation_ft'].max())
    elevation_range = st.sidebar.slider(
        "Elevation Range (ft)",
        min_value=min_elevation,
        max_value=max_elevation,
        value=(min_elevation, max_elevation)
    )

    if 'runway_length_ft' in df.columns:
        min_runway = int(df['runway_length_ft'].min())
        max_runway = int(df['runway_length_ft'].max())
        runway_range = st.sidebar.slider(
            "Runway Length Range (ft)",
            min_value=min_runway,
            max_value=max_runway,
            value=(min_runway, max_runway)
        )
    else:
        runway_range = None

    #Filtering Data on sidebar condition
    filtered_data = df[
        (df['iso_region'].isin(selected_state)) & #[DA5]
        (df['type'].isin(selected_type)) &
        (df['elevation_category'].isin(selected_elevation)) &
        (df['elevation_ft'].between(*elevation_range)) #[DA4]
        ]

    if runway_range is not None:
        filtered_data = filtered_data[filtered_data['runway_length_ft'].between(*runway_range)]

    #Data Explo.
    st.subheader("Filtered Airport Data")
    st.dataframe(filtered_data)

    #Visualizations Section (subheader)
    st.subheader("Visualizations")

    #Bar Chart (Visualization) [VIZ1]
    st.markdown("### Airport Type Distribution")
    st.bar_chart(filtered_data['type'].value_counts())

    #Elevation Categories, Pie chart [PY4] [ST3] [VIZ2]
    st.sidebar.title("Pie Chart Categories")
    selected_categories = [
        category for category in filtered_data['elevation_category'].unique()
        if st.sidebar.checkbox(f"Show {category} Elevation", value=True)
    ]

    #Pie Chart (Visualization)
    if selected_categories:
        st.markdown("### Elevation Category Proportion")
        filtered_for_pie = filtered_data[filtered_data['elevation_category'].isin(selected_categories)]
        if not filtered_for_pie.empty:
            fig, ax = plt.subplots()
            filtered_for_pie['elevation_category'].value_counts().plot.pie(
                autopct='%1.1f%%', startangle=140, ax=ax
            )
            ax.set_ylabel('')
            st.pyplot(fig)
        else:
            st.warning("No data available for the selected elevation categories.")
    else:
        st.warning("Please select at least one elevation category to display the pie chart.")

    #Map (Visualization) [MAP]
    st.subheader("Airport Locations Map")

    #Valid Cords. check
    if not filtered_data.empty and 'latitude_deg' in filtered_data.columns and 'longitude_deg' in filtered_data.columns:
        filtered_data = filtered_data.dropna(subset=['latitude_deg', 'longitude_deg'])

        #Error Checking, w/ no Valid Locations
        if filtered_data.empty:
            st.warning("No valid location data available to plot.")
        else: #Hover Icon for Map, additional cool feature for heatmap [ST4]
            tooltip = {
                "html": "<b>Name:</b> {name} <br/>"
                        "<b>Type:</b> {type} <br/>"
                        "<b>Elevation (ft):</b> {elevation_ft}",
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white"
                }
            }

            scatter_layer = pdk.Layer(
                "ScatterplotLayer",
                data=filtered_data,
                get_position="[longitude_deg, latitude_deg]",
                get_radius=5000,
                get_fill_color="[200, 30, 0, 160]",
                pickable=True,
            )

            heatmap_layer = pdk.Layer(
                "HeatmapLayer",
                data=filtered_data,
                get_position="[longitude_deg, latitude_deg]",
                aggregation="sum",
                threshold=1,
                intensity=1
            )

            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=filtered_data['latitude_deg'].mean(),
                    longitude=filtered_data['longitude_deg'].mean(),
                    zoom=7,
                    pitch=50,
                ),
                layers=[scatter_layer, heatmap_layer],
                tooltip=tooltip
            ))
    else:
        st.warning("No location data to display on the map.")

    #Numeric Charts Section Subheader
    st.subheader("Numeric Filtering Visualizations")

    #Elevation Histogram
    st.markdown("### Elevation Distribution")
    fig, ax = plt.subplots()
    filtered_data['elevation_ft'].hist(bins=20, ax=ax)
    ax.set_title("Histogram of Elevation")
    ax.set_xlabel("Elevation (ft)")
    ax.set_ylabel("Count")
    st.pyplot(fig)

    #Summary Stats.
    st.subheader("Summary Statistics")
    total_airports, avg_elevation, airport_counts = analyze_airport_data(filtered_data)
    st.write(f"Total Airports: {total_airports}")
    st.write(f"Average Elevation: {avg_elevation:.2f} ft")
    st.write("Airport Counts by Type:")
    st.json(airport_counts)

    #Pivot Table [DA6]
    st.subheader("Pivot Table: Airports by Type and State")
    pivot_table = filtered_data.pivot_table(index='iso_region', columns='type', values='id', aggfunc='count',
                                            fill_value=0)
    st.dataframe(pivot_table)

#misc.
file_path = 'new_england_airports(in).csv'
data = load_and_prepare_data(file_path)
run_airport_explorer(data)

#end of file
