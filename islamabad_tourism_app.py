# tourism_assistant.py
import streamlit as st
import osmnx as ox
import networkx as nx
import folium
import pandas as pd
import math
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from queue import PriorityQueue, Queue, LifoQueue
from typing import Dict, List, Tuple

# Configure OSMnx settings
ox.settings.log_console = False
ox.settings.use_cache = True
ox.settings.timeout = 300

# Initialize geocoder
@st.cache_resource
def get_geolocator():
    return Nominatim(user_agent="islamabad_tourism_v2")

# Constants
ISLAMABAD_CENTER = (33.6844, 73.0479)
TRANSPORT_MODES = ['drive', 'walk', 'bike']
ALGORITHMS = ['A*', 'Dijkstra', 'BFS', 'DFS']

# Session state initialization
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'graph' not in st.session_state:
    st.session_state.graph = None

def get_coordinates(address: str) -> Tuple[float, float]:
    """Get coordinates with enhanced error handling and caching"""
    try:
        location = get_geolocator().geocode(f"{address}, Islamabad")
        if location:
            return (location.latitude, location.longitude)
    except (GeocoderTimedOut, GeocoderUnavailable):
        st.error("Geocoding service unavailable. Using default location.")
    return ISLAMABAD_CENTER

def haversine(node1: Tuple[float, float], node2: Tuple[float, float]) -> float:
    """Calculate great-circle distance between two points"""
    lat1, lon1 = node1
    lat2, lon2 = node2
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2) * math.sin(dlat/2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) * math.sin(dlon/2))
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

class PathFinder:
    """Pathfinding algorithms implementation"""
    
    def __init__(self, G: nx.MultiDiGraph):
        self.G = G
        self.nodes = list(G.nodes)
        self.edges = list(G.edges)
        
    def get_neighbors(self, node: int) -> List[int]:
        return list(self.G.neighbors(node))
    
    def get_node_location(self, node: int) -> Tuple[float, float]:
        return (self.G.nodes[node]['y'], self.G.nodes[node]['x'])
    
    def find_path(self, start: int, end: int, algorithm: str) -> List[int]:
        if algorithm == 'A*':
            return self.a_star(start, end)
        elif algorithm == 'Dijkstra':
            return self.dijkstra(start, end)
        elif algorithm == 'BFS':
            return self.bfs(start, end)
        elif algorithm == 'DFS':
            return self.dfs(start, end)
        return []
    
    def a_star(self, start: int, end: int) -> List[int]:
        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {}
        g_score = {node: float('inf') for node in self.nodes}
        g_score[start] = 0
        
        while not open_set.empty():
            current = open_set.get()[1]
            
            if current == end:
                return self.reconstruct_path(came_from, current)
                
            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + self.G[current][neighbor][0]['length']
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + haversine(
                        self.get_node_location(neighbor),
                        self.get_node_location(end)
                    )
                    open_set.put((f_score, neighbor))
        return []
    
    def dijkstra(self, start: int, end: int) -> List[int]:
        distances = {node: float('inf') for node in self.nodes}
        distances[start] = 0
        prev_nodes = {}
        pq = PriorityQueue()
        pq.put((0, start))
        
        while not pq.empty():
            dist, current = pq.get()
            if current == end:
                break
            for neighbor in self.get_neighbors(current):
                new_dist = dist + self.G[current][neighbor][0]['length']
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    prev_nodes[neighbor] = current
                    pq.put((new_dist, neighbor))
        return self.reconstruct_path(prev_nodes, end)
    
    def bfs(self, start: int, end: int) -> List[int]:
        queue = Queue()
        queue.put(start)
        visited = {start: None}
        
        while not queue.empty():
            current = queue.get()
            if current == end:
                break
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.put(neighbor)
        return self.reconstruct_path(visited, end)
    
    def dfs(self, start: int, end: int) -> List[int]:
        stack = LifoQueue()
        stack.put(start)
        visited = {start: None}
        
        while not stack.empty():
            current = stack.get()
            if current == end:
                break
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited[neighbor] = current
                    stack.put(neighbor)
        return self.reconstruct_path(visited, end)
    
    def reconstruct_path(self, came_from: Dict[int, int], current: int) -> List[int]:
        path = []
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        return path[::-1]

def get_route_map(G: nx.MultiDiGraph, route: List[int], algorithm: str) -> folium.Map:
    """Generate optimized route map with algorithm-specific styling"""
    route_colors = {
        'A*': '#FF0000',
        'Dijkstra': '#00FF00',
        'BFS': '#0000FF',
        'DFS': '#FF00FF'
    }
    route_map = ox.plot_route_folium(G, route, 
                                   color=route_colors.get(algorithm, '#FF0000'),
                                   opacity=0.7,
                                   tiles='CartoDB positron')
    return route_map

def main():
    """Main application function"""
    st.set_page_config(
        page_title
