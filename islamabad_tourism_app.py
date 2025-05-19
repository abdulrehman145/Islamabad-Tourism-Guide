import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import pandas as pd
import requests
from datetime import datetime
import logging
from collections import deque
import math

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page configuration
st.set_page_config(
    page_title="Islamabad Tourism Assistant",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize geocoder
geolocator = Nominatim(user_agent="islamabad_tourism_assistant")

# Cache the road network graph
@st.cache_resource
def load_graph():
    """Load and cache the drivable road network for Islamabad."""
    try:
        graph = ox.graph_from_place("Islamabad, Pakistan", network_type="drive")
        return graph
    except Exception as e:
        st.error(f"Failed to load road network: {str(e)}")
        logger.error(f"Graph loading error: {str(e)}")
        return None

# Attractions dictionary
attractions_data = {
    "Faisal Mosque": {
        "location": [33.7295, 73.0372],
        "category": "Religious",
        "address": "Shah Faisal Ave, Islamabad",
        "description": "One of the largest mosques in the world, designed by Vedat Dalokay.",
        "tags": ["history", "architecture", "religious"]
    },
    "Pakistan Monument": {
        "location": [33.6926, 73.0685],
        "category": "Cultural",
        "address": "Shakarparian, Islamabad",
        "description": "A national monument shaped like a blooming flower.",
        "tags": ["history", "cultural", "museum"]
    },
    "Daman-e-Koh": {
        "location": [33.7463, 73.0581],
        "category": "Nature",
        "address": "Margalla Hills, Islamabad",
        "description": "A hilltop garden offering panoramic views of Islamabad.",
        "tags": ["nature", "scenic", "hiking"]
    },
    "Lok Virsa Museum": {
        "location": [33.6895, 73.0770],
        "category": "Cultural",
        "address": "Garden Ave, Islamabad",
        "description": "Showcases Pakistan's folk heritage with artifacts and crafts.",
        "tags": ["cultural", "museum", "history"]
    },
    "Rawal Lake": {
        "location": [33.6969, 73.1292],
        "category": "Nature",
        "address": "Rawal Lake, Islamabad",
        "description": "An artificial reservoir with boating and picnic spots.",
        "tags": ["nature", "recreation", "water"]
    }
}
attractions_df = pd.DataFrame.from_dict(attractions_data, orient='index')
attractions_df['name'] = attractions_df.index

# Custom A* heuristic
def a_star_heuristic(u, v, graph):
    """Custom heuristic for A* based on scaled Euclidean distance."""
    u_coords = (graph.nodes[u]["y"], graph.nodes[u]["x"])
    v_coords = (graph.nodes[v]["y"], graph.nodes[v]["x"])
    return geodesic(u_coords, v_coords).meters * 1.5  # Scale heuristic for exploration

# Custom BFS implementation
def bfs_path(graph, source, target):
    """Find shortest path using BFS (unweighted)."""
    queue = deque([(source, [source])])
    visited = {source}
    
    while queue:
        node, path = queue.popleft()
        if node == target:
            return path
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    
    raise ValueError("No path found with BFS")

# Custom DFS implementation
def dfs_path(graph, source, target):
    """Find a path using DFS (may not be shortest)."""
    stack = [(source, [source])]
    visited = {source}
    
    while stack:
        node, path = stack.pop()
        if node == target:
            return path
        
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    
    raise ValueError("No path found with DFS")

# Pathfinding algorithms
def find_path(graph, source, target, algorithm="A*"):
    """Find the path between source and target nodes using the selected algorithm."""
    try:
        if graph is None:
            raise ValueError("Road network not loaded.")
        
        # Find nearest nodes
        source_node = ox.distance.nearest_nodes(graph, source[1], source[0])
        target_node = ox.distance.nearest_nodes(graph, target[1], target[0])
        logger.info(f"Source node: {source_node}, Target node: {target_node}")
        
        # Select algorithm
        if algorithm == "A*":
            path = nx.astar_path(graph, source_node, target_node, heuristic=lambda u, v: a_star_heuristic(u, v, graph), weight="length")
        elif algorithm == "Dijkstra":
            path = nx.dijkstra_path(graph, source_node, target_node, weight="length")
        elif algorithm == "BFS":
            path = bfs_path(graph, source_node, target_node)
        elif algorithm == "DFS":
            path = dfs_path(graph, source_node, target_node)
        
        # Extract route coordinates
        route_coords = [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in path]
        # Calculate distance (km)
        length = nx.path_weight(graph, path, weight="length") / 1000
        # Estimate travel time (minutes, 40 km/h)
        travel_time = length / 40 * 60
        logger.info(f"Path found with {algorithm}: Length={length:.2f} km, Time={travel_time:.2f} min")
        return route_coords, length, travel_time
    except ImportError as e:
        if "scikit-learn" in str(e):
            st.error("Missing dependency: Please install scikit-learn (`pip install scikit-learn`).")
            logger.error("scikit-learn not installed.")
        raise
    except Exception as e:
        logger.error(f"Pathfinding error with {algorithm}: {str(e)}")
        raise ValueError(f"Pathfinding failed: {str(e)}")

# Create Folium map
def create_map(start_coords, end_coords, route_coords=None, nearby_attractions=None):
    """Generate an interactive Folium map with route and attraction markers."""
    m = folium.Map(location=[33.7294, 73.0931], zoom_start=12, tiles="OpenStreetMap")
    
    # Start marker
    folium.Marker(
        start_coords,
        tooltip="Start",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)
    
    # Destination marker
    folium.Marker(
        end_coords,
        tooltip="Destination",
        icon=folium.Icon(color="red", icon="stop", prefix="fa")
    ).add_to(m)
    
    # Route polyline
    if route_coords:
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)
    
    # Nearby attractions
    if nearby_attractions is not None:
        for name, info in nearby_attractions.iterrows():
            popup_html = f"""
            <div style='width: 200px; text-align: center;'>
                <h4>{name}</h4>
                <p><b>Category:</b> {info['category']}</p>
                <p><b>Address:</b> {info['address']}</p>
            </div>
            """
            folium.Marker(
                location=info['location'],
                tooltip=name,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="purple", icon="info-sign", prefix="fa")
            ).add_to(m)
    
    return m

# Find nearby attractions
def get_nearby_attractions(dest_coords, radius_km=5, preferences=None):
    """Return attractions within radius_km, filtered by preferences."""
    nearby = attractions_df.copy()
    nearby['distance'] = nearby['location'].apply(lambda x: geodesic(dest_coords, x).km)
    nearby = nearby[nearby['distance'] <= radius_km]
    
    if preferences:
        nearby = nearby[nearby['tags'].apply(lambda x: any(p in x for p in preferences))]
    
    return nearby.sort_values('distance')

# Fetch weather data
def get_weather(coords):
    """Fetch current weather using OpenWeatherMap API."""
    try:
        api_key = "YOUR_API_KEY"  # Replace with your OpenWeatherMap API key
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units=metric"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                "temp": data["main"]["temp"],
                "description": data["weather"][0]["description"].capitalize(),
                "humidity": data["main"]["humidity"]
            }
        return None
    except:
        logger.warning("Failed to fetch weather data.")
        return None

# Custom CSS
def load_css():
    """Apply custom CSS for UI styling."""
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #26A69A;
            margin-top: 1rem;
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
        }
        .category-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            color: white;
            margin-right: 0.5rem;
        }
        .category-Religious { background-color: #673AB7; }
        .category-Cultural { background-color: #FF9800; }
        .category-Nature { background-color: #4CAF50; }
        .info-box {
            background-color: #E3F2FD;
            border-left: 5px solid #1E88E5;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# Main application
def main():
    """Main function to run the Streamlit app."""
    load_css()
    
    # Header
    st.markdown("<h1 class='main-header'>🏙️ Islamabad Tourism Assistant</h1>", unsafe_allow_html=True)
    st.markdown("Plan your trip, find the best routes, and explore Islamabad's attractions!")
    
    # Sidebar
    st.sidebar.markdown("## 🗺️ Route Planner")
    start_location = st.sidebar.text_input("Starting Point", placeholder="e.g., Air University Islamabad")
    destination = st.sidebar.text_input("Destination", placeholder="e.g., Faisal Mosque, Islamabad")
    algorithm = st.sidebar.selectbox("Pathfinding Algorithm", ["A*", "Dijkstra", "BFS", "DFS"], index=0)
    show_attractions = st.sidebar.checkbox("Show Nearby Attractions", value=True)
    
    # Preferences
    st.sidebar.markdown("## 🎯 Preferences")
    preferences = st.sidebar.multiselect(
        "Your Interests",
        ["history", "cultural", "nature", "recreation", "architecture"],
        default=["history", "nature"]
    )
    
    # Review submission
    st.sidebar.markdown("## ⭐ Submit a Review")
    selected_attraction = st.sidebar.selectbox("Select Attraction", attractions_df['name'].tolist())
    rating = st.sidebar.slider("Rating (1-5)", 1, 5, 3)
    review_text = st.sidebar.text_area("Your Review", placeholder="Share your experience...")
    if st.sidebar.button("Submit Review"):
        if review_text:
            if 'reviews' not in st.session_state:
                st.session_state.reviews = {}
            if selected_attraction not in st.session_state.reviews:
                st.session_state.reviews[selected_attraction] = []
            st.session_state.reviews[selected_attraction].append({
                "rating": rating,
                "text": review_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            st.sidebar.success("Review submitted!")
        else:
            st.sidebar.warning("Please enter a review.")
    
    # Geocode locations
    default_start = [33.7139, 73.0339]  # Air University Islamabad
    start_coords = default_start
    start_name = "Air University Islamabad"
    dest_coords = None
    dest_name = ""
    
    if start_location:
        try:
            start_loc = geolocator.geocode(start_location + ", Islamabad")
            if start_loc:
                start_coords = [start_loc.latitude, start_loc.longitude]
                start_name = start_location
            else:
                st.warning("Starting point not found. Using default: Air University Islamabad")
        except Exception as e:
            st.warning(f"Error geocoding starting point: {str(e)}. Using default.")
            logger.warning(f"Geocoding error (start): {str(e)}")
    
    if destination:
        try:
            dest_loc = geolocator.geocode(destination + ", Islamabad")
            if dest_loc:
                dest_coords = [dest_loc.latitude, dest_loc.longitude]
                dest_name = destination
            else:
                st.error("Destination not found. Try 'Faisal Mosque, Islamabad'.")
        except Exception as e:
            st.error(f"Error geocoding destination: {str(e)}.")
            logger.warning(f"Geocoding error (dest): {str(e)}")
    
    # Weather
    weather_info = None
    if dest_coords:
        weather_info = get_weather(dest_coords)
        if weather_info:
            st.sidebar.markdown("## ☀️ Weather")
            st.sidebar.info(
                f"**Current:** {weather_info['temp']}°C, {weather_info['description']}\n\n"
                f"**Humidity:** {weather_info['humidity']}%"
            )
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🗺️ Route Map", "🏞️ Attractions", "⭐ Reviews"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Your Route</h2>", unsafe_allow_html=True)
        if dest_coords:
            graph = load_graph()
            if graph:
                try:
                    route_coords, distance, travel_time = find_path(graph, start_coords, dest_coords, algorithm)
                    nearby_attractions = get_nearby_attractions(dest_coords, preferences=preferences) if show_attractions else None
                    m = create_map(start_coords, dest_coords, route_coords, nearby_attractions)
                    folium_static(m, width=800, height=500)
                    st.markdown(f"<div class='info-box'>", unsafe_allow_html=True)
                    st.write(f"**From:** {start_name}")
                    st.write(f"**To:** {dest_name}")
                    st.write(f"**Distance:** {distance:.2f} km")
                    st.write(f"**Estimated Travel Time:** {travel_time:.2f} minutes")
                    st.write(f"**Algorithm:** {algorithm}")
                    st.markdown("</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not find route: {str(e)}")
            else:
                st.error("Road network not available. Please try again later.")
        else:
            m = create_map(start_coords, start_coords)
            folium_static(m, width=800, height=500)
            st.info("Enter a destination to see the route.")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>Nearby Attractions</h2>", unsafe_allow_html=True)
        if dest_coords and show_attractions:
            nearby = get_nearby_attractions(dest_coords, preferences=preferences)
            if not nearby.empty:
                for name, info in nearby.iterrows():
                    st.markdown(f"<div class='attraction-card'>", unsafe_allow_html=True)
                    st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<span class='category-pill category-{info['category']}'>{info['category']}</span>", unsafe_allow_html=True)
                    st.write(f"**Address:** {info['address']}")
                    st.write(f"**Distance:** {info['distance']:.2f} km")
                    st.write(f"**Description:** {info['description']}")
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No attractions found within 5 km matching your preferences.")
        else:
            st.info("Enter a destination and enable 'Show Nearby Attractions' to see suggestions.")
    
    with tab3:
        st.markdown("<h2 class='sub-header'>User Reviews</h2>", unsafe_allow_html=True)
        if 'reviews' in st.session_state and st.session_state.reviews:
            for attraction, reviews in st.session_state.reviews.items():
                with st.expander(attraction, expanded=True):
                    avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
                    st.markdown(f"**Average Rating:** {avg_rating:.1f} ⭐")
                    for review in reviews:
                        st.markdown(f"**{review['rating']} ⭐**: {review['text']} - *{review['timestamp']}*")
        else:
            st.info("No reviews submitted yet. Share your experience using the sidebar!")

if __name__ == "__main__":
    main()
