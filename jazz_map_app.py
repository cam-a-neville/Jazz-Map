import streamlit as st
import pandas as pd
import pydeck as pdk
import re 
from streamlit_folium import st_folium
import folium
import plotly.express as px
from folium.plugins import MousePosition

# Set up Streamlit page
st.set_page_config(page_title="Jazz Map", layout="wide")
st.title("Jazz Legends and Jazz Venues, Mapped")

# Description of my project
st.text("The history of jazz in the U.S. is a rich one, spanning time and place. With modern-day tools, we can visualize both.")
st.text("This application allows the user to view a complete history of 20th century jazz venues, clubs, and halls in the cities of Los Angeles, New York, and Chicago, along with the careers of six jazz legends.")
st.text("The core of the map of venues is the time slider, which allows the user to change what window of years the map will display. In conjunction with the counter displaying the amount of active venues, and the markers on the map for each venue, the user can use this tool to view how jazz shrunk and grew in different cities and neighborhoods throughout the 20th century.")
st.text("For the map of artists, it can be used to track the addresses of individuals throughout their life, or to get a more general overview of where jazz artists tended to move for their careers. When each point is clicked on a short description and some basic data about the artist is shared.")

# Create the point the venue map will center on
CENTER_LAT = 40.7161
CENTER_LON = -89.2978
# slightly different point for the artist map
CENTER_LAT_TWO = 32.9897
CENTER_LON_TWO = -112.6655


# Load the different tabs of my google sheet
@st.cache_data
def load_data():
    return pd.read_csv("https://docs.google.com/spreadsheets/d/1gohOWra462LpOoNbmK9yos1epTlem2f9KnxwVHGSYcU/export?format=csv&gid=714094255")
df = load_data()

@st.cache_data
def load_data():
    return pd.read_csv("https://docs.google.com/spreadsheets/d/1gohOWra462LpOoNbmK9yos1epTlem2f9KnxwVHGSYcU/export?format=csv&gid=0")
df_artists = load_data()



# I'm starting by creating the time span selection system on the sidebar
st.sidebar.header("Select Time Span")

span_test = st.sidebar.slider("Please select a rating range", min_value=1900, max_value=2000, value=(2000, 1900))

range_start = span_test[0]
range_end = span_test[1]
# make it so that if a venue has any overlap with the window selected it will show
filtered_df = df[(df["start year"]>=range_start) & (df["start year"]<=range_end) | (df["end year"]>=range_start) & (df["end year"]<=range_end) | (df["start year"]<=range_start) & (df["end year"]>=range_end)]


# now make the sidebar option to select cities
st.sidebar.header("Filter Venues by City")

# Get unique values for filtering
unique_cities = df["city"].unique()

# Multiselect widgets for filtering
selected_cities = st.sidebar.multiselect(
    "Select City/Cities",
    options=unique_cities,
    default=unique_cities,  # Show all by default
    key="city_filter"
)

# Apply filters
filtered_df = filtered_df[
    (filtered_df["city"].isin(selected_cities))
]



# Clean coordinate data for filtered results
filtered_map_data = filtered_df[['city', 'venue', 'latitude', 'longitude', 'start year', 'end year']].dropna()
filtered_map_data['latitude'] = pd.to_numeric(filtered_map_data['latitude'], errors='coerce')
filtered_map_data['longitude'] = pd.to_numeric(filtered_map_data['longitude'], errors='coerce')
filtered_map_data = filtered_map_data.dropna()



# Main content section for the venue map
col1, col2 = st.columns([3, 1])


# I originally had a completely different kind of map, but changed to this for the hover data

with col1:


	# Create title of map that changes depending on time window
	if isinstance(range_start, int):
		st.subheader(f"{range_start}-{range_end} Map of Venues:")
	elif isinstance(range_start, str):
		st.subheader("1900-2000 Venue Map:")

	# and a subtitle that changes depending on filtered cities
	if len(selected_cities) >= 1:
		are_there_cities = st.text(f"Showing Venues in {(', '.join(map(str, selected_cities)))}")
	else:
		are_there_cities = st.text("No Selected Cities")


	# Creating the actual map here

	venue_m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=3.7)

	# Putting the markers from my data onto the map
	for index, row in filtered_map_data.iterrows():
		popup_html = "<br>".join([f"<b>{k}:</b> {str(v)}" for k, v in row.to_dict().items()])
		
		folium.CircleMarker(
			location=[row['latitude'], row['longitude']],
			radius=6,
			color="purple",
			fill=True,
			fill_opacity=0.7,
			tooltip=row.get("location"),
			popup=folium.Popup(folium.Html(popup_html, script=True), max_width=250),
			interactive=False   
		).add_to(venue_m)

	# This is so it can respond when I click on markers
	folium.LatLngPopup().add_to(venue_m)

	# Getting the map to load
	st_data = st_folium(venue_m, width = 1000, key = "venue_map")

	# Setting up last object clicked so I can reference what I click
	last = st_data.get("last_object_clicked")
	if last is not None:
		st.session_state["last_object_clicked"] = last




# Creating a counter next to the map, which displays how many venues are in each city at any given time

with col2:

	# filter with the count of each city
	venue_count_df = filtered_map_data['city'].value_counts().reset_index()

	# turn df to 2 lists
	city_list = venue_count_df['city'].tolist()
	count_list = venue_count_df['count'].tolist()

	# use a loop to print result
	st.subheader("Active Venues")
	for i in range(len(selected_cities)):
		st.text(f"{city_list[i]}: {count_list[i]}")



# Now time to create the second map, for artists

# Sidebar filters
st.sidebar.header("Filter Artists")

# Get unique values for filtering
unique_artists = df_artists["name"].unique()

# Multiselect widgets for filtering
selected_artists = st.sidebar.multiselect(
    "Select Artist/Artists",
    options=unique_artists,
    default=unique_artists,  # Show all by default
    key="artist_filter"
)

# Apply filters to the artist location df
df_artists = df_artists[
    (df_artists["name"].isin(selected_artists))
]

# Clean coordinate data for filtered results
filtered_artist_map_data = df_artists[['name', 'location number', 'latitude', 'longitude', 'city', 'birthday', 'instrument', 'overview', 'article link']].dropna()
filtered_artist_map_data['latitude'] = pd.to_numeric(filtered_artist_map_data['latitude'], errors='coerce')
filtered_artist_map_data['longitude'] = pd.to_numeric(filtered_artist_map_data['longitude'], errors='coerce')
filtered_artist_map_data = filtered_artist_map_data.dropna()

st.text("") # for format purposes

# title of map
st.subheader("Map of Artist Careers:")

# subtitle that changes to relfect visible artists
if len(selected_artists) >= 1:
    are_there_artists = st.text(f"Showing Career(s) of {(', '.join(map(str, selected_artists)))}")
else:
	are_there_artists = st.text("No Selected Artists")



# Creating the base map 
artist_m = folium.Map(location=[CENTER_LAT_TWO, CENTER_LON_TWO], zoom_start=3.4)

# This is so it can respond when I click on markers
folium.LatLngPopup().add_to(artist_m)


# Now time to add markers and lines:

# use a dict to split my df into individual dfs for each artist
dict_of_artist_dfs = {value: group for value, group in filtered_artist_map_data.groupby('name')}

# run a for loop that is the length of however many artists are selected
for i in range(len(selected_artists)):
	# here is where I enact the dict
	current_artist_df = dict_of_artist_dfs[selected_artists[i]]

	# create this list for later, to tell artists apart by color
	color_list = ("red", "orange", "yellow", "green", "blue", "purple")

	# and make a list that only has the name of whatever my current selected artist is
	select_artist_name_list = current_artist_df['name'].to_list()


	# here I set up counter for the amount of locations my selected artist lived in
	locations_count = len(current_artist_df['location number'])

	# and create tuples for the current artists cords
	lat_tuple = tuple(current_artist_df['latitude'].tolist())
	lon_tuple = tuple(current_artist_df['longitude'].tolist())

	# run a loop that creates a line between these tuples
	# this loop will run for the total amount of locations that artist has lived in their life
	for x in range(locations_count-1):
		first_pair = [lat_tuple[x], lon_tuple[x]]
		second_pair = [lat_tuple[x+1], lon_tuple[x+1]]

		folium.PolyLine(
			locations=[first_pair, second_pair],
			color=color_list[i], # the color changes each time through the for loop
			weight=3,
			tooltip=select_artist_name_list[0], # hover data of the artist name
		).add_to(artist_m)

	
	# Putting the markers from my data onto the map with another for loop
	for index, row in current_artist_df.iterrows():
		popup_html = "<br>".join([f"<b>{k}:</b> {str(v)}" for k, v in row.to_dict().items()])

		folium.CircleMarker(
			location=[row['latitude'], row['longitude']],
			radius=6,
			color=color_list[i], # same color system
			fill=True,
			fill_opacity=0.7,
			tooltip=select_artist_name_list[0], # and hover data of name
			# had a ton of issues with the popup below
			# I initiall was trying to make it read out information about the artist and a way that was just not working
			# I eventually added all the info I wanted into the google sheet itself, and it now functions as imagined
			popup=folium.Popup(folium.Html(popup_html, script=True), max_width=500),
			interactive=False   
		).add_to(artist_m)


# Getting the map to load
st_data = st_folium(artist_m, width = 1000, key = "artist_map")

# Setting up last object clicked so I can reference what I click
last = st_data.get("last_object_clicked")
if last is not None:
	st.session_state["last_object_clicked"] = last