# tourism_assistant.py
import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from streamlit_folium import folium_static
from shapely.geometry import Point
import pandas as pd

# Configure OSMnx settings
ox.settings.log_console = False
ox.settings.use_cache = True
ox.settings.timeout = 300

# Initialize geocoder
@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="islamabad_tourism_v1")

# Predefined popular spots with enhanced data
PREDEFINED_SPOTS = {
    "Faisal Mosque": {
        "category": "Religious",
        "address": "Shah Faisal Ave, Islamabad",
        "coordinates": (33.7294, 73.0361)
    },
    "Daman-e-Koh": {
        "category": "Viewpoint",
        "address": "Margalla Hills, Islamabad",
        "coordinates": (33.7428, 73.0558)
    },
    "Pakistan Monument": {
        "category": "Historical",
        "address": "Shakarparian, Islamabad",
        "coordinates": (33.6934, 73.0656)
    }
}

# Session state for reviews
if 'reviews' not in st.session_state:
    st.session_state.reviews = {}

def get_coordinates(address):
    """Get coordinates with enhanced error handling and caching"""
    try:
        location = get_geolocator().geocode(f"{address}, Islamabad")
        if location:
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderUnavailable) as e:
        st.error("Geocoding service unavailable. Using default location.")
    return (33.6844, 73.0479)  # Centroid of Islamabad

@st.cache_data(ttl=3600)  # Cache routes for 1 hour
def get_route_map(origin_coords, dest_coords, transport_mode='drive'):
    """Generate optimized route map with error handling"""
    try:
        G = ox.graph_from_point(origin_coords, dist=5000, network_type=transport_mode)
        
        origin_node = ox.distance.nearest_nodes(G, origin_coords[1], origin_coords[0])
        dest_node = ox.distance.nearest_nodes(G, dest_coords[1], dest_coords[0])
        
        route = nx.shortest_path(G, origin_node, dest_node, weight='length')
        route_map = ox.plot_route_folium(G, route, zoom=13, 
                                       route_color='#4285F4', 
                                       opacity=0.7,
                                       tiles='CartoDB positron')
        
        # Custom markers
        folium.Marker(origin_coords, 
                    icon=folium.Icon(color='green', icon='map-pin', prefix='fa')).add_to(route_map)
        folium.Marker(dest_coords, 
                    icon=folium.Icon(color='red', icon='flag-checkered', prefix='fa')).add_to(route_map)
        
        return route_map, ox.stats.route_stats(G, route)
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return None, None

def get_nearby_pois(location_coords):
    """Get nearby Points of Interest with fallback to predefined"""
    try:
        tags = {'tourism': True, 'historic': True, 'leisure': True}
        gdf = ox.features.features_from_point(location_coords, tags, dist=2000)
        gdf = gdf[['name', 'tourism', 'addr:street', 'geometry']].dropna()
        gdf['coordinates'] = gdf['geometry'].apply(lambda x: (x.centroid.y, x.centroid.x))
        return gdf.head(5)
    except Exception:
        return pd.DataFrame.from_dict(PREDEFINED_SPOTS, orient='index')

def review_section(place_name):
    """Interactive review section with state management"""
    with st.expander(f"✍️ Reviews for {place_name}", expanded=False):
        with st.form(key=f'review_form_{place_name}'):
            cols = st.columns([2, 1])
            with cols[0]:
                review_text = st.text_area("Share your experience", key=f'text_{place_name}')
            with cols[1]:
                rating = st.slider("Rating", 1, 5, 5, key=f'rating_{place_name}')
                
            if st.form_submit_button("Post Review"):
                if place_name not in st.session_state.reviews:
                    st.session_state.reviews[place_name] = []
                st.session_state.reviews[place_name].append({
                    'rating': rating,
                    'text': review_text
                })
        
        if place_name in st.session_state.reviews:
            for idx, review in enumerate(st.session_state.reviews[place_name]):
                st.markdown(f"""
                <div style="padding: 10px; background: #f8f9fa; border-radius: 5px; margin: 5px 0;">
                    <div style="color: #f39c12; font-size: 1.2em;">{"★" * review['rating']}</div>
                    <div>{review['text']}</div>
                </div>
                """, unsafe_allow_html=True)

def main():
    """Main application function"""
    st.set_page_config(
        page_title="Islamabad Tourism Assistant",
        page_icon="🏙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-title {color: #1a73e8; text-align: center; padding: 1rem;}
    .sidebar .sidebar-content {background-color: #f8f9fa;}
    .st-emotion-cache-1y4p8pa {padding: 2rem 1rem;}
    [data-testid="stExpander"] {background: white; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-title">🏙️ Islamabad Tourism Assistant</h1>', unsafe_allow_html=True)
    
    # Sidebar Controls
    with st.sidebar:
        st.header("🗺️ Navigation Controls")
        destination = st.text_input("📍 Enter Destination", "Pakistan Monument")
        transport_mode = st.selectbox("🚗 Transportation Mode", ["drive", "walk", "bike"], index=0)
        show_route = st.toggle("🗺️ Show Route Map", True)
        show_pois = st.toggle("🏞️ Show Nearby Attractions", True)
    
    # Get coordinates
    dest_coords = get_coordinates(destination)
    
    # Main content columns
    map_col, poi_col = st.columns([2, 1], gap="large")
    
    with map_col:
        if show_route:
            route_map, route_stats = get_route_map((33.6844, 73.0479), dest_coords, transport_mode)
            if route_map:
                folium_static(route_map, width=700, height=500)
                if route_stats:
                    st.caption(f"Route Distance: {route_stats['length']/1000:.1f} km | "
                             f"Estimated Time: {route_stats['travel_time']/60:.0f} mins")
    
    with poi_col:
        if show_pois:
            st.subheader("🏞️ Nearby Attractions")
            pois = get_nearby_pois(dest_coords)
            
            if not pois.empty:
                for _, row in pois.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 1rem; margin: 0.5rem 0; 
                                    background: white; border-radius: 10px;
                                    box-shadow: 0 2px 8px rgba(0,0,0,0.1)">
                            <h4>{row['name']}</h4>
                            <div style="color: #666; font-size: 0.9em;">
                                <div>📍 {row.get('addr:street', 'Address not available')}</div>
                                <div>🏷️ {row['tourism'].title()}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        review_section(row['name'])
            else:
                st.info("No nearby attractions found. Showing popular spots:")
                for name, info in PREDEFINED_SPOTS.items():
                    with st.expander(name):
                        st.write(f"📍 {info['address']}")
                        st.write(f"🏷️ {info['category']}")
                        review_section(name)

if __name__ == "__main__":
    main()
