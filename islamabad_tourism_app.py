import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import osmnx as ox
import networkx as nx
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from datetime import datetime
import math

# Set page configuration
st.set_page_config(
    page_title="Islamabad Tourism Assistant",
    page_icon="🏙️",
    layout="wide"
)

# Initialize session state
if 'reviews' not in st.session_state:
    st.session_state.reviews = {}

if 'graph' not in st.session_state:
    st.session_state.graph = None

# Define attraction data
attractions_data = {
    "Faisal Mosque": {
        "description": "One of the largest mosques in the world, designed by Turkish architect Vedat Dalokay. The mosque's architecture is inspired by a Bedouin tent and is situated at the foot of Margalla Hills.",
        "location": [33.7295, 73.0372],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Faisal_Mosque.jpg/1200px-Faisal_Mosque.jpg",
        "best_time": "Early morning or late afternoon",
        "activities": ["Prayer", "Photography", "Architecture appreciation"],
        "category": "Religious",
        "address": "Shah Faisal Ave, Islamabad"
    },
    "Pakistan Monument": {
        "description": "A national monument representing the four provinces of Pakistan. The monument is shaped like a blooming flower and provides a panoramic view of Islamabad.",
        "location": [33.6926, 73.0685],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Pakistan_Monument_at_Night.jpg/1200px-Pakistan_Monument_at_Night.jpg",
        "best_time": "Evening (sunset view)",
        "activities": ["Photography", "Museum visit", "Scenic views"],
        "category": "Cultural",
        "address": "Shakarparian, Islamabad"
    },
    "Daman-e-Koh": {
        "description": "A viewing point and hilltop garden offering spectacular views of Islamabad. Located in the Margalla Hills, it's a popular spot for locals and tourists alike.",
        "location": [33.7463, 73.0581],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Daman-e-Koh_Top_View_at_Night.jpg/1200px-Daman-e-Koh_Top_View_at_Night.jpg",
        "best_time": "Evening (sunset view)",
        "activities": ["Scenic views", "Photography", "Picnics", "Monkey watching"],
        "category": "Nature",
        "address": "Margalla Hills, Islamabad"
    },
    "Lok Virsa Museum": {
        "description": "The National Institute of Folk & Traditional Heritage, showcasing Pakistan's cultural heritage through artifacts, crafts, and music.",
        "location": [33.6895, 73.0770],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Lok_Virsa_Museum.jpg/1200px-Lok_Virsa_Museum.jpg",
        "best_time": "Weekday mornings",
        "activities": ["Cultural exhibits", "Folk music", "Craft shopping"],
        "category": "Cultural",
        "address": "Garden Avenue, Shakarparian, Islamabad"
    },
    "Margalla Hills National Park": {
        "description": "A large natural reserve with hiking trails, wildlife, and beautiful scenery. Perfect for nature lovers and adventure seekers.",
        "location": [33.7480, 73.0375],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Margalla_Hills.jpg/1200px-Margalla_Hills.jpg",
        "best_time": "Early morning or late afternoon",
        "activities": ["Hiking", "Bird watching", "Wildlife spotting", "Photography"],
        "category": "Nature",
        "address": "Margalla Hills, Islamabad"
    },
    "Rawal Lake": {
        "description": "An artificial reservoir that supplies water to Islamabad and Rawalpindi. The lake view park offers boating, fishing, and picnic spots.",
        "location": [33.6969, 73.1292],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Rawal_Lake_Islamabad.jpg/1200px-Rawal_Lake_Islamabad.jpg",
        "best_time": "Morning or evening",
        "activities": ["Boating", "Fishing", "Picnics", "Bird watching"],
        "category": "Nature",
        "address": "Murree Road, Islamabad"
    },
    "Lake View Park": {
        "description": "A family amusement park on the banks of Rawal Lake, offering recreational facilities, gardens, and a bird aviary.",
        "location": [33.7014, 73.1230],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Lake_View_Park_Islamabad.jpg/1200px-Lake_View_Park_Islamabad.jpg",
        "best_time": "Evening",
        "activities": ["Amusement rides", "Boating", "Picnics", "Bird watching"],
        "category": "Recreation",
        "address": "Murree Road, Islamabad"
    },
    "Shakarparian": {
        "description": "A hilly area with terraced gardens, a cultural complex, and the Pakistan Monument Museum.",
        "location": [33.6890, 73.0695],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Shakar_Parian_Islamabad.JPG/1200px-Shakar_Parian_Islamabad.JPG",
        "best_time": "Evening",
        "activities": ["Garden walks", "Museum visits", "Picnics", "Cultural events"],
        "category": "Nature",
        "address": "Shakarparian, Islamabad"
    },
    "Saidpur Village": {
        "description": "A centuries-old village transformed into a cultural center with restaurants, craft shops, and historic buildings.",
        "location": [33.7385, 73.0587],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Saidpur_Village.jpg/1200px-Saidpur_Village.jpg",
        "best_time": "Evening",
        "activities": ["Dining", "Shopping", "Cultural exploration", "Photography"],
        "category": "Cultural",
        "address": "Saidpur Road, Islamabad"
    },
    "Centaurus Mall": {
        "description": "A luxury shopping mall with international brands, a food court, and entertainment facilities.",
        "location": [33.7096, 73.0493],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Centaurus_Mall_Islamabad.jpg/1200px-Centaurus_Mall_Islamabad.jpg",
        "best_time": "Afternoon or evening",
        "activities": ["Shopping", "Dining", "Movies", "Entertainment"],
        "category": "Shopping",
        "address": "F-8/4, Jinnah Avenue, Blue Area, Islamabad"
    }
}

# Default location (Air University Islamabad)
DEFAULT_LOCATION = {
    "name": "Air University Islamabad",
    "coordinates": [33.7139, 73.0339],
    "address": "Service Road E, E-9/4 E-9, Islamabad"
}

# Convert attractions data to DataFrame
attractions_df = pd.DataFrame.from_dict(attractions_data, orient='index')
attractions_df['name'] = attractions_df.index

# Custom CSS
def load_css():
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
            text-shadow: 1px 1px 2px #B0BEC5;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #26A69A;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
        }
        .attraction-card {
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            padding: 1rem;
            margin: 0.5rem 0;
            background-color: #FFFFFF;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .attraction-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .info-box {
            background-color: #E3F2FD;
            border-left: 5px solid #1E88E5;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
        .warning-box {
            background-color: #FFF8E1;
            border-left: 5px solid #FFC107;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
        .category-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            color: white;
        }
        .category-Religious {
            background-color: #673AB7;
        }
        .category-Cultural {
            background-color: #FF9800;
        }
        .category-Nature {
            background-color: #4CAF50;
        }
        .category-Recreation {
            background-color: #03A9F4;
        }
        .category-Shopping {
            background-color: #F44336;
        }
        .activity-tag {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            margin-right: 0.3rem;
            margin-bottom: 0.3rem;
            background-color: #E0E0E0;
            color: #333333;
        }
        .review-card {
            border-left: 3px solid #4CAF50;
            background-color: #F1F8E9;
            padding: 0.75rem;
            margin-bottom: 0.75rem;
            border-radius: 0 5px 5px 0;
        }
        .review-time {
            font-size: 0.8rem;
            color: #757575;
            margin-top: 0.25rem;
        }
        .review-stars {
            color: #FFC107;
            margin-right: 0.5rem;
        }
        .route-info {
            background-color: #E8F5E9;
            border-left: 5px solid #4CAF50;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
        .nearby-attractions {
            background-color: #E0F7FA;
            border-left: 5px solid #00BCD4;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# Geocoding functions
@st.cache_data(ttl=86400)
def geocode_location(location_name):
    try:
        geolocator = Nominatim(user_agent="islamabad_tourism_assistant")
        location = geolocator.geocode(f"{location_name}, Islamabad, Pakistan", exactly_one=True)
        
        if location:
            return {
                "name": location_name,
                "coordinates": [location.latitude, location.longitude],
                "address": location.address
            }
        else:
            return None
    except Exception as e:
        st.error(f"Error geocoding location: {e}")
        return None

# Map and routing functions
@st.cache_data(ttl=3600)
def load_islamabad_graph():
    try:
        # Define the bounding box for Islamabad
        north, south, east, west = 33.8, 33.6, 73.2, 72.9
        
        # Download and create graph
        G = ox.graph_from_bbox(north, south, east, west, network_type='drive', simplify=True)
        
        # Project the graph to UTM
        G_proj = ox.project_graph(G)
        
        return G, G_proj
    except Exception as e:
        st.error(f"Error loading map data: {e}")
        return None, None

def get_nearest_node(G, location):
    try:
        return ox.distance.nearest_nodes(G, location[1], location[0])  # Longitude, Latitude order for osmnx
    except Exception as e:
        st.error(f"Error finding nearest node: {e}")
        return None

def calculate_route_bfs(G, start_node, end_node):
    """Calculate route using Breadth First Search"""
    try:
        # BFS algorithm
        queue = [(start_node, [start_node])]
        visited = set([start_node])
        
        while queue:
            (vertex, path) = queue.pop(0)
            for neighbor in G.neighbors(vertex):
                if neighbor == end_node:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None
    except Exception as e:
        st.error(f"Error in BFS algorithm: {e}")
        return None

def calculate_route_dfs(G, start_node, end_node):
    """Calculate route using Depth First Search"""
    try:
        # DFS algorithm
        stack = [(start_node, [start_node])]
        visited = set([start_node])
        
        while stack:
            (vertex, path) = stack.pop()
            for neighbor in G.neighbors(vertex):
                if neighbor == end_node:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, path + [neighbor]))
        return None
    except Exception as e:
        st.error(f"Error in DFS algorithm: {e}")
        return None

def calculate_route(G, G_proj, start_location, end_location, algorithm="a_star"):
    """Calculate route using the selected algorithm"""
    try:
        # Get nearest nodes
        start_node = get_nearest_node(G, start_location["coordinates"])
        end_node = get_nearest_node(G, end_location["coordinates"])
        
        if start_node is None or end_node is None:
            return None, None, None
        
        # Calculate route based on algorithm
        route = None
        if algorithm == "dijkstra":
            route = nx.shortest_path(G, start_node, end_node, weight='length')
        elif algorithm == "a_star":
            route = nx.shortest_path(G, start_node, end_node, weight='length', method='astar')
        elif algorithm == "bfs":
            route = calculate_route_bfs(G, start_node, end_node)
        elif algorithm == "dfs":
            route = calculate_route_dfs(G, start_node, end_node)
            
        if route is None:
            return None, None, None
            
        # Calculate distance and travel time
        edge_lengths = []
        for u, v in zip(route[:-1], route[1:]):
            data = min(G.get_edge_data(u, v).values(), key=lambda x: x['length'])
            edge_lengths.append(data['length'])
            
        distance_meters = sum(edge_lengths)
        distance_km = distance_meters / 1000  # Convert to kilometers
        
        # Assume average speed of 40 km/h
        avg_speed_kmh = 40
        travel_time_hours = distance_km / avg_speed_kmh
        travel_time_minutes = math.ceil(travel_time_hours * 60)  # Convert to minutes and round up
        
        return route, distance_km, travel_time_minutes
    except Exception as e:
        st.error(f"Error calculating route: {e}")
        return None, None, None

def create_route_map(G, route, start_location, end_location, nearby_attractions=None):
    """Create a folium map with the route and markers"""
    try:
        # Create a folium map centered at Islamabad
        m = folium.Map(location=[33.7294, 73.0931], zoom_start=12, tiles="OpenStreetMap")
        
        if route:
            # Get the route LineString
            route_coords = []
            for node in route:
                point = G.nodes[node]
                route_coords.append((point['y'], point['x']))  # Latitude, Longitude order for folium
                
            # Add the route to the map
            folium.PolyLine(
                route_coords,
                color='blue',
                weight=5,
                opacity=0.7,
                tooltip="Route"
            ).add_to(m)
            
            # Add markers for start and end points
            folium.Marker(
                location=start_location["coordinates"],
                popup=folium.Popup(f"<b>Start:</b> {start_location['name']}", max_width=300),
                tooltip=f"Start: {start_location['name']}",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
            
            folium.Marker(
                location=end_location["coordinates"],
                popup=folium.Popup(f"<b>Destination:</b> {end_location['name']}", max_width=300),
                tooltip=f"Destination: {end_location['name']}",
                icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')
            ).add_to(m)
            
            # Set map bounds to show the whole route
            sw = min([c[0] for c in route_coords]), min([c[1] for c in route_coords])
            ne = max([c[0] for c in route_coords]), max([c[1] for c in route_coords])
            m.fit_bounds([sw, ne])
        
        # Add nearby attractions if provided
        if nearby_attractions is not None:
            for name, info in nearby_attractions.iterrows():
                popup_html = f"""
                <div style="width: 200px; text-align: center;">
                    <h3>{name}</h3>
                    <p><b>Category:</b> {info['category']}</p>
                    <p><b>Best time:</b> {info['best_time']}</p>
                </div>
                """
                
                # Customize icon based on category
                icon_colors = {
                    "Religious": "purple",
                    "Cultural": "orange",
                    "Nature": "green",
                    "Recreation": "blue",
                    "Shopping": "red"
                }
                icon_color = icon_colors.get(info['category'], "blue")
                
                folium.Marker(
                    location=info['location'],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=name,
                    icon=folium.Icon(color=icon_color, icon="info-sign")
                ).add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Error creating map: {e}")
        return None

def find_nearby_attractions(location, radius_km=5):
    """Find attractions within a certain radius of the location"""
    try:
        nearby = []
        
        for name, info in attractions_data.items():
            # Calculate distance
            distance = geodesic(location["coordinates"], info["location"]).kilometers
            
            if distance <= radius_km:
                nearby.append({
                    "name": name,
                    "distance": distance,
                    "category": info["category"],
                    "location": info["location"],
                    "address": info["address"]
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x["distance"])
        
        return nearby
    except Exception as e:
        st.error(f"Error finding nearby attractions: {e}")
        return []

# Reviews functions
def save_review(attraction, rating, comment):
    """Save a review for an attraction"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if attraction not in st.session_state.reviews:
        st.session_state.reviews[attraction] = []
        
    st.session_state.reviews[attraction].append({
        "rating": rating,
        "comment": comment,
        "timestamp": timestamp
    })

def get_average_rating(attraction):
    """Get the average rating for an attraction"""
    if attraction not in st.session_state.reviews or len(st.session_state.reviews[attraction]) == 0:
        return 0
    
    total = sum([review["rating"] for review in st.session_state.reviews[attraction]])
    return total / len(st.session_state.reviews[attraction])

def display_reviews(attraction):
    """Display all reviews for an attraction"""
    if attraction not in st.session_state.reviews or len(st.session_state.reviews[attraction]) == 0:
        st.info(f"No reviews for {attraction} yet. Be the first to review!")
        return
    
    avg_rating = get_average_rating(attraction)
    st.write(f"**Average Rating:** {'⭐' * int(round(avg_rating))} ({avg_rating:.1f}/5 from {len(st.session_state.reviews[attraction])} reviews)")
    
    for review in st.session_state.reviews[attraction]:
        st.markdown(f"""
        <div class="review-card">
            <span class="review-stars">{'⭐' * review['rating']}</span>
            <span>{review['comment']}</span>
            <div class="review-time">{review['timestamp']}</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    load_css()
    
    # Load the Islamabad graph if not already loaded
    if st.session_state.graph is None:
        with st.spinner("Loading map data for Islamabad..."):
            G, G_proj = load_islamabad_graph()
            if G is not None and G_proj is not None:
                st.session_state.graph = (G, G_proj)
    else:
        G, G_proj = st.session_state.graph
    
    # Header
    st.markdown("<h1 class='main-header'>🏙️ Islamabad Tourism Assistant</h1>", unsafe_allow_html=True)
    
    # Sidebar for inputs and controls
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Faisal_Mosque_July_1_2005_pic32.JPG/800px-Faisal_Mosque_July_1_2005_pic32.JPG", caption="Islamabad - The Beautiful")
    
    st.sidebar.markdown("## 🗺️ Plan Your Route")
    
    # Starting location input
    start_location_input = st.sidebar.text_input("Enter Starting Location", "")
    starting_location = None
    
    if start_location_input.strip() == "":
        st.sidebar.warning("No starting location provided. Using default: Air University Islamabad")
        starting_location = DEFAULT_LOCATION
    else:
        start_location_name = f"{start_location_input}, Islamabad" if "islamabad" not in start_location_input.lower() else start_location_input
        with st.sidebar.spinner(f"Finding {start_location_name}..."):
            starting_location = geocode_location(start_location_name)
        
        if starting_location is None:
            st.sidebar.error(f"Could not find '{start_location_input}'. Using default location instead.")
            starting_location = DEFAULT_LOCATION
    
    # Destination input
    destination_input = st.sidebar.text_input("Enter Destination", "")
    destination_location = None
    
    if destination_input.strip() != "":
        dest_location_name = f"{destination_input}, Islamabad" if "islamabad" not in destination_input.lower() else destination_input
        with st.sidebar.spinner(f"Finding {dest_location_name}..."):
            destination_location = geocode_location(dest_location_name)
            
        if destination_location is None:
            st.sidebar.error(f"Could not find '{destination_input}'. Please try another destination.")
    
    # Algorithm selection
    algorithm = st.sidebar.selectbox(
        "Pathfinding Algorithm",
        ["A* (Fastest)", "Dijkstra", "BFS (Breadth-First Search)", "DFS (Depth-First Search)"],
        index=0
    )
    
    # Map algorithm names to their implementation names
    algorithm_map = {
        "A* (Fastest)": "a_star",
        "Dijkstra": "dijkstra",
        "BFS (Breadth-First Search)": "bfs",
        "DFS (Depth-First Search)": "dfs"
    }
    
    selected_algorithm = algorithm_map[algorithm]
    
    # Show nearby attractions option
    show_nearby = st.sidebar.checkbox("Show Nearby Attractions", value=True)
    
    # Category filter
    st.sidebar.markdown("## 🔍 Filter Attractions")
    categories = sorted(attractions_df['category'].unique())
    selected_categories = st.sidebar.multiselect(
        "By Category",
        categories,
        default=categories
    )
    
    # Activities filter
    all_activities = []
    for acts in attractions_df['activities']:
        all_activities.extend(acts)
    unique_activities = sorted(set(all_activities))
    
    selected_activities = st.sidebar.multiselect(
        "By Activities",
        unique_activities
    )
    
    # Filter attractions based on selections
    filtered_attractions = attractions_df.copy()
    
    if selected_categories:
        filtered_attractions = filtered_attractions[filtered_attractions['category'].isin(selected_categories)]
    
    if selected_activities:
        filtered_attractions = filtered_attractions[filtered_attractions['activities'].apply(
            lambda x: any(activity in x for activity in selected_activities)
        )]
    
    # Weather information (mock data)
    st.sidebar.markdown("## 🌤️ Current Weather")
    st.sidebar.info(
        "☀️ **Current:** 28°C, Sunny\n\n"
        "🌡️ **Today:** 25-32°C\n\n"
        "💨 **Wind:** 10 km/h\n\n"
        "💧 **Humidity:** 45%"
    )
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Routing", "🏛️ Attractions", "📝 Reviews", "ℹ️ Travel Tips"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Find Your Way in Islamabad</h2>", unsafe_allow_html=True)
        
        if G is None or G_proj is None:
            st.error("Failed to load map data. Please refresh the page and try again.")
        elif destination_location is None:
            st.info("Enter a destination in the sidebar to plan your route.")
        else:
            with st.spinner(f"Calculating route using {algorithm}..."):
                route, distance, time = calculate_route(
                    G, G_proj, 
                    starting_location, 
                    destination_location,
                    selected_algorithm
                )
            
            if route is None:
                st.error("Could not find a route. Try different locations or a different algorithm.")
            else:
                # Display route info
                st.markdown(f"""
                <div class="route-info">
                    <h3>🚗 Route Information</h3>
                    <p><b>From:</b> {starting_location['name']} ({starting_location['address']})</p>
                    <p><b>To:</b> {destination_location['name']} ({destination_location['address']})</p>
                    <p><b>Distance:</b> {distance:.2f} km</p>
                    <p><b>Estimated Travel Time:</b> {time} minutes (at avg. speed of 40 km/h)</p>
                    <p><b>Algorithm Used:</b> {algorithm}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Find nearby attractions if enabled
                nearby_attractions_df = None
                if show_nearby:
                    nearby = find_nearby_attractions(destination_location)
                    
                    if nearby:
                        st.markdown(f"""
                        <div class="nearby-attractions">
                            <h3>🌟 Nearby Attractions (within 5 km)</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Create a dataframe for nearby attractions
                        nearby_df = pd.DataFrame(nearby)
                        st.table(nearby_df[['name', 'category', 'distance']].assign(distance=lambda x: x['distance'].round(2).astype(str) + ' km'))
                        
                        # Filter the full attractions dataframe to only include nearby ones
                        nearby_names = [item["name"] for item in nearby]
                        nearby_attractions_df = attractions_df[attractions_df['name'].isin(nearby_names)]
                
                # Create and display the map
                map_container = st.container()
                with map_container:
                    m = create_route_map(G, route, starting_location, destination_location, nearby_attractions_df)
                    if m is not None:
                        folium_static(m, width=800, height=500)
    
    with tab2:
        st.markdown("<h2 class='sub-header'>Explore Top Attractions</h2>", unsafe_allow_html=True)
        
        if not filtered_attractions.empty:
            for name, info in filtered_attractions.iterrows():
                with st.container():
                    st.markdown(f"<div class='attraction-card' id='{name.lower().replace(' ', '-')}'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.image(info['image'], use_column_width=True)
                    
                    with col2:
                        st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<span class='category-pill category-{info['category']}'>{info['category']}</span>", unsafe_allow_html=True)
                        st.write(info['description'])
                        
                        st.markdown("<p><b>Best time to visit:</b> " + info['best_time'] + "</p>", unsafe_allow_html=True)
                        st.markdown("<p><b>Address:</b> " + info['address'] + "</p>", unsafe_allow_html=True)
                        
                        # Display activities
                        st.markdown("<p><b>Activities:</b></p>", unsafe_allow_html=True)
                        activities_html = " ".join([f"<span class='activity-tag'>{activity}</span>" for activity in info['activities']])
                        st.markdown(activities_html, unsafe_allow_html=True)
                        
                        # Display average rating
                        avg_rating = get_average_rating(name)
                        if avg_rating > 0:
                            st.markdown(f"<p><b>Rating:</b> {'⭐' * int(round(avg_rating))} ({avg_rating:.1f}/5)</p>", unsafe_allow_html=True)
                        else:
                            st.markdown("<p><b>Rating:</b> No ratings yet</p>", unsafe_allow_html=True)
                        
                        # Plan route button
                        if st.button(f"Plan Route to {name}", key=f"route_{name}"):
                            st.session_state.selected_destination = name
                            st.experimental_rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<hr>", unsafe_allow_html=True)
        else:
            st.warning("No attractions match your selected filters. Try changing your filter criteria.")
    
    with tab3:
        st.markdown("<h2 class='sub-header'>Reviews & Ratings</h2>", unsafe_allow_html=True)
        
        # Select attraction to review or view reviews
        attractions_list = list(attractions_data.keys())
        selected_attraction = st.selectbox("Select an attraction", attractions_list)
        
        st.markdown("<h3>Reviews</h3>", unsafe_allow_html=True)
        display_reviews(selected_attraction)
        
        st.markdown("<h3>Add Your Review</h3>", unsafe_allow_html=True)
        with st.form(key=f"review_form_{selected_attraction}"):
            rating = st.slider("Rating", 1, 5, 5)
            comment = st.text_area("Your Review", max_chars=500)
            submit_button = st.form_submit_button("Submit Review")
            
            if submit_button:
                if comment.strip():
                    save_review(selected_attraction, rating, comment)
                    st.success("Thank you for your review!")
                    st.experimental_rerun()
                else:
                    st.error("Please enter a comment for your review.")
    
    with tab4:
        st.markdown("<h2 class='sub-header'>Travel Tips for Islamabad</h2>", unsafe_allow_html=True)
        
        # General tips
        st.markdown("<h3>General Information</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>🇵🇰 <b>Language:</b> Urdu is the national language, but English is widely understood in urban areas.</p>
            <p>💲 <b>Currency:</b> Pakistani Rupee (PKR)</p>
            <p>⚡ <b>Electricity:</b> 220V, 50Hz (UK-style 3-pin plugs)</p>
            <p>☎️ <b>Country Code:</b> +92</p>
            <p>🚨 <b>Emergency:</b> Call 15 for Police, 1122 for Rescue</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Best time to visit
        st.markdown("<h3>Best Time to Visit</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>🌞 <b>Spring (March-April):</b> Pleasant temperatures, blooming gardens. Perfect for outdoor activities.</p>
            <p>🌧️ <b>Summer (May-August):</b> Hot, with monsoon rains in July-August. Indoor activities recommended during peak heat.</p>
            <p>🍂 <b>Autumn (September-November):</b> Mild weather, ideal for sightseeing and hiking in Margalla Hills.</p>
            <p>❄️ <b>Winter (December-February):</b> Cold, sometimes foggy. Snowfall in the surrounding hills makes for beautiful views.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Transportation
        st.markdown("<h3>Getting Around</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>🚕 <b>Taxis:</b> Ride-hailing apps like Careem and Uber operate in Islamabad.</p>
            <p>🚗 <b>Car Rental:</b> Available at the airport and major hotels.</p>
            <p>🚌 <b>Metro Bus:</b> Connects Islamabad with Rawalpindi.</p>
            <p>🚶‍♂️ <b>Walking:</b> Islamabad is well-planned with wide sidewalks, but distances can be long.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Safety
        st.markdown("<h3>Safety Tips</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="warning-box">
            <p>📱 Keep emergency contacts handy and stay connected.</p>
            <p>💰 Avoid displaying large amounts of cash or valuable items.</p>
            <p>🧠 Be aware of your surroundings, especially in crowded areas.</p>
            <p>🚫 Respect local customs and dress modestly, especially at religious sites.</p>
            <p>🚗 If driving, be cautious as traffic rules may not always be followed by others.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Local etiquette
        st.markdown("<h3>Local Etiquette</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>👋 Greet with "Assalam-o-Alaikum" (Peace be upon you).</p>
            <p>👚 Dress modestly, especially women. Cover shoulders and knees.</p>
            <p>📸 Ask permission before photographing people, especially women.</p>
            <p>👞 Remove shoes before entering homes or religious places.</p>
            <p>🤝 Use right hand for eating, greeting, and passing items.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Food recommendations
        st.markdown("<h3>Must-Try Food</h3>", unsafe_allow_html=True)
        
        food_col1, food_col2 = st.columns(2)
        
        with food_col1:
            st.markdown("""
            - **Biryani** - Fragrant rice dish with meat and spices
            - **Chapli Kebab** - Spicy meat patties
            - **Nihari** - Slow-cooked meat stew
            - **Haleem** - Wheat, lentils and meat porridge
            """)
            
        with food_col2:
            st.markdown("""
            - **Samosa** - Fried pastry with savory filling
            - **Jalebi** - Sweet, circular dessert
            - **Kashmiri Chai** - Pink tea with nuts
            - **Golgappay/Pani Puri** - Crispy hollow balls with flavored water
            """)

        # Popular shopping areas
        st.markdown("<h3>Shopping Spots</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>🛍️ <b>Centaurus Mall</b> - High-end international brands</p>
            <p>🛍️ <b>Jinnah Super Market</b> - Mix of boutiques and eateries</p>
            <p>🛍️ <b>Super Market</b> - Traditional crafts and souvenirs</p>
            <p>🛍️ <b>Daman-e-Koh Viewpoint</b> - Souvenir shops with local items</p>
            <p>🛍️ <b>Saidpur Village</b> - Handicrafts and traditional items</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Day trips
        st.markdown("<h3>Day Trips from Islamabad</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>🏞️ <b>Murree</b> - Hill station (1-2 hours drive)</p>
            <p>🏞️ <b>Taxila</b> - Ancient Buddhist ruins (45 minutes drive)</p>
            <p>🏞️ <b>Ayubia National Park</b> - Natural beauty, chair lifts (2 hours drive)</p>
            <p>🏞️ <b>Khanpur Dam</b> - Water activities (1 hour drive)</p>
            <p>🏞️ <b>Nathiagali</b> - Mountain resort (2-3 hours drive)</p>
        </div>
        """, unsafe_allow_html=True)

# Create a recommendation system based on user preferences
def recommend_itinerary():
    st.markdown("<h2 class='sub-header'>Custom Itinerary Recommendation</h2>", unsafe_allow_html=True)
    
    # User preferences
    days = st.slider("Number of days in Islamabad", 1, 7, 3)
    interests = st.multiselect(
        "Select your interests",
        ["Religious Sites", "Cultural Experience", "Nature & Parks", "Shopping", "Local Cuisine"]
    )
    
    with_children = st.checkbox("Traveling with children")
    budget_option = st.selectbox("Budget", ["Budget-friendly", "Moderate", "Luxury"])
    
    # Generate itinerary button
    if st.button("Generate Itinerary"):
        if not interests:
            st.warning("Please select at least one interest to generate an itinerary.")
            return
            
        st.markdown("<h3>Your Personalized Itinerary</h3>", unsafe_allow_html=True)
        
        # Convert interests to categories
        interest_to_category = {
            "Religious Sites": "Religious",
            "Cultural Experience": "Cultural",
            "Nature & Parks": "Nature",
            "Shopping": "Shopping",
            "Local Cuisine": "Recreation"
        }
        
        # Filter attractions based on interests
        selected_categories = [interest_to_category[interest] for interest in interests if interest in interest_to_category]
        filtered_attractions = attractions_df[attractions_df['category'].isin(selected_categories)]
        
        # Add family-friendly filter if traveling with children
        if with_children:
            # For this example, assume some activities are not suitable for children
            child_friendly_activities = ["Photography", "Garden walks", "Picnics", "Scenic views", "Museum visit", "Cultural exhibits"]
            filtered_attractions = filtered_attractions[filtered_attractions['activities'].apply(
                lambda x: any(activity in x for activity in child_friendly_activities)
            )]
        
        # If we have too few attractions, add some more
        if len(filtered_attractions) < days * 2:
            additional_attractions = attractions_df[~attractions_df.index.isin(filtered_attractions.index)]
            # Sort by potential interest
            additional_attractions['interest_score'] = additional_attractions['category'].apply(
                lambda x: 0.5 if x in selected_categories else 0.3
            )
            additional_attractions = additional_attractions.sort_values('interest_score', ascending=False)
            filtered_attractions = pd.concat([filtered_attractions, additional_attractions.head(days * 2 - len(filtered_attractions))])
        
        # Create daily itineraries
        for day in range(1, days+1):
            st.markdown(f"<h4>Day {day}</h4>", unsafe_allow_html=True)
            
            # Select 2-3 attractions for the day
            if len(filtered_attractions) > 0:
                day_attractions = filtered_attractions.sample(min(3, len(filtered_attractions)))
                filtered_attractions = filtered_attractions.drop(day_attractions.index)
                
                for i, (name, info) in enumerate(day_attractions.iterrows()):
                    if i == 0:
                        time = "Morning"
                    elif i == 1:
                        time = "Afternoon"
                    else:
                        time = "Evening"
                        
                    st.markdown(f"""
                    <div class="info-box">
                        <p><b>{time}:</b> Visit {name} - {info['category']}</p>
                        <p>{info['description'][:100]}...</p>
                        <p><i>Recommended activities:</i> {', '.join(info['activities'][:3])}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add meal recommendations
                meal_places = {
                    "Budget-friendly": ["Street food at G-9 Markaz", "Savour Foods", "Student Biryani"],
                    "Moderate": ["Chaaye Khana", "MONAL Downtown", "Street 1 Cafe"],
                    "Luxury": ["Monal Restaurant", "Tuscany Courtyard", "Islamabad Serena Hotel"]
                }
                
                selected_meals = meal_places[budget_option]
                
                st.markdown(f"""
                <div class="info-box">
                    <p><b>Dining recommendations:</b></p>
                    <p>🍳 <b>Breakfast:</b> {np.random.choice(selected_meals)}</p>
                    <p>🍲 <b>Lunch:</b> {np.random.choice(selected_meals)}</p>
                    <p>🍽️ <b>Dinner:</b> {np.random.choice(selected_meals)}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"Day {day}: We recommend exploring the city at your own pace or taking a day trip to nearby attractions like Murree or Taxila.")
        
        # Add transportation recommendations
        st.markdown("<h4>Transportation Recommendations</h4>", unsafe_allow_html=True)
        
        transport_options = {
            "Budget-friendly": "Use the Metro Bus system for main routes and Careem/Uber for specific locations.",
            "Moderate": "Consider hiring a Careem/Uber for the day or using ride-hailing services as needed.",
            "Luxury": "Hire a private car with driver for the duration of your stay for maximum convenience."
        }
        
        st.markdown(f"""
        <div class="info-box">
            <p>🚗 {transport_options[budget_option]}</p>
            <p>🗺️ Consider purchasing a local SIM card for navigation and easy access to ride-hailing apps.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Additional tips based on preferences
        st.markdown("<h4>Additional Tips</h4>", unsafe_allow_html=True)
        
        if "Religious Sites" in interests:
            st.markdown("""
            <div class="warning-box">
                <p>👚 When visiting religious sites, ensure you dress modestly. Women should cover their heads with a scarf.</p>
                <p>👞 Remove shoes before entering prayer areas in mosques.</p>
                <p>📸 Ask permission before taking photographs inside religious buildings.</p>
            </div>
            """, unsafe_allow_html=True)
        
        if "Nature & Parks" in interests:
            st.markdown("""
            <div class="warning-box">
                <p>🥾 For hiking in Margalla Hills, wear comfortable shoes and carry water.</p>
                <p>🐒 Be cautious around monkeys in parks - don't feed them or display food openly.</p>
                <p>🌞 Apply sunscreen and wear a hat during outdoor activities, even in cooler weather.</p>
            </div>
            """, unsafe_allow_html=True)
        
        if with_children:
            st.markdown("""
            <div class="warning-box">
                <p>🧒 Lake View Park and Pakistan Monument have open spaces for children to play.</p>
                <p>🍼 Carry snacks and water for children as options might be limited in some areas.</p>
                <p>🥤 Ensure children drink only bottled water.</p>
            </div>
            """, unsafe_allow_html=True)

# Weather forecast function (using mock data)
def weather_forecast():
    st.markdown("<h2 class='sub-header'>Weather Forecast for Islamabad</h2>", unsafe_allow_html=True)
    
    # Mock weather data
    forecast = [
        {"date": "Today", "temp_high": 32, "temp_low": 25, "condition": "Sunny", "icon": "☀️", "precipitation": "0%"},
        {"date": "Tomorrow", "temp_high": 31, "temp_low": 24, "condition": "Mostly Sunny", "icon": "🌤️", "precipitation": "10%"},
        {"date": "Day 3", "temp_high": 30, "temp_low": 24, "condition": "Partly Cloudy", "icon": "⛅", "precipitation": "20%"},
        {"date": "Day 4", "temp_high": 29, "temp_low": 23, "condition": "Scattered Showers", "icon": "🌦️", "precipitation": "40%"},
        {"date": "Day 5", "temp_high": 28, "temp_low": 22, "condition": "Rainy", "icon": "🌧️", "precipitation": "80%"}
    ]
    
    # Display the forecast
    st.markdown("<div style='display: flex; justify-content: space-between; flex-wrap: wrap;'>", unsafe_allow_html=True)
    
    for day in forecast:
        st.markdown(f"""
        <div style='width: 18%; min-width: 120px; background-color: #E3F2FD; border-radius: 10px; padding: 10px; margin: 5px; text-align: center;'>
            <h3>{day['date']}</h3>
            <div style='font-size: 2rem;'>{day['icon']}</div>
            <p>{day['condition']}</p>
            <p>{day['temp_high']}°C / {day['temp_low']}°C</p>
            <p>Precipitation: {day['precipitation']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Weather tips
    st.markdown("<h3>Weather Tips</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <p>🧴 <b>Summer:</b> Use sunscreen, wear light cotton clothes, and stay hydrated.</p>
        <p>☔ <b>Monsoon:</b> Carry an umbrella and avoid hiking during heavy rain.</p>
        <p>🧣 <b>Winter:</b> Mornings and evenings can be cold, so bring layers.</p>
        <p>🥾 <b>Spring/Autumn:</b> Perfect for outdoor activities, but weather can change suddenly in hilly areas.</p>
    </div>
    """, unsafe_allow_html=True)

# Event calendar function (mock data)
def event_calendar():
    st.markdown("<h2 class='sub-header'>Upcoming Events in Islamabad</h2>", unsafe_allow_html=True)
    
    # Mock event data
    events = [
        {
            "name": "Pakistan Day Parade",
            "date": "March 23",
            "location": "Parade Ground",
            "description": "Military parade and cultural performances celebrating Pakistan's Republic Day.",
            "category": "Cultural"
        },
        {
            "name": "Islamabad Food Festival",
            "date": "April 15-17",
            "location": "F-9 Park",
            "description": "Annual food festival featuring local and international cuisines.",
            "category": "Food"
        },
        {
            "name": "Lok Mela",
            "date": "November 7-15",
            "location": "Lok Virsa Complex",
            "description": "Folk Festival showcasing traditional arts, crafts, and music from across Pakistan.",
            "category": "Cultural"
        },
        {
            "name": "Margalla Hill Marathon",
            "date": "October 5",
            "location": "Trail 5, Margalla Hills",
            "description": "Annual marathon race through the scenic trails of Margalla Hills.",
            "category": "Sports"
        },
        {
            "name": "Spring Flower Show",
            "date": "March 20-25",
            "location": "Rose & Jasmine Garden",
            "description": "Exhibition of spring flowers with competitions and plant sales.",
            "category": "Nature"
        }
    ]
    
    # Filter options
    event_categories = sorted(set(event["category"] for event in events))
    selected_event_categories = st.multiselect(
        "Filter events by category",
        event_categories,
        default=event_categories
    )
    
    # Filter events
    filtered_events = [event for event in events if event["category"] in selected_event_categories]
    
    if not filtered_events:
        st.info("No events match your selected filters.")
    else:
        for event in filtered_events:
            category_colors = {
                "Cultural": "FF9800",
                "Food": "E91E63",
                "Sports": "4CAF50",
                "Nature": "009688"
            }
            color = category_colors.get(event["category"], "9E9E9E")
            
            st.markdown(f"""
            <div class="attraction-card">
                <h3>{event["name"]} <span style="background-color:#{color}; color:white; padding:3px 8px; border-radius:10px; font-size:0.8rem;">{event["category"]}</span></h3>
                <p><b>Date:</b> {event["date"]}</p>
                <p><b>Location:</b> {event["location"]}</p>
                <p>{event["description"]}</p>
            </div>
            """, unsafe_allow_html=True)

# Run the app with all features
if __name__ == "__main__":
    main()
    
    # Additional features in separate expanders
    with st.expander("🗓️ Event Calendar"):
        event_calendar()
        
    with st.expander("🌦️ Weather Forecast"):
        weather_forecast()
        
    with st.expander("🧭 Custom Itinerary Planner"):
        recommend_itinerary()
