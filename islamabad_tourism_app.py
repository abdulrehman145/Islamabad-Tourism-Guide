!pip install folium streamlit streamlit-folium osmnx networkx geopy pyngrok
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import base64
from PIL import Image
import io

# Set page configuration
st.set_page_config(
    page_title="Islamabad Tourism Assistant",
    page_icon="🏙️",
    layout="wide"
)

# Define attraction data
attractions_data = {
    "Faisal Mosque": {
        "description": "One of the largest mosques in the world, designed by Turkish architect Vedat Dalokay. The mosque's architecture is inspired by a Bedouin tent and is situated at the foot of Margalla Hills.",
        "location": [33.7295, 73.0372],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/Faisal_Mosque.jpg/1200px-Faisal_Mosque.jpg",
        "best_time": "Early morning or late afternoon",
        "activities": ["Prayer", "Photography", "Architecture appreciation"],
        "category": "Religious"
    },
    "Pakistan Monument": {
        "description": "A national monument representing the four provinces of Pakistan. The monument is shaped like a blooming flower and provides a panoramic view of Islamabad.",
        "location": [33.6926, 73.0685],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Pakistan_Monument_at_Night.jpg/1200px-Pakistan_Monument_at_Night.jpg",
        "best_time": "Evening (sunset view)",
        "activities": ["Photography", "Museum visit", "Scenic views"],
        "category": "Cultural"
    },
    "Daman-e-Koh": {
        "description": "A viewing point and hilltop garden offering spectacular views of Islamabad. Located in the Margalla Hills, it's a popular spot for locals and tourists alike.",
        "location": [33.7463, 73.0581],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Daman-e-Koh_Top_View_at_Night.jpg/1200px-Daman-e-Koh_Top_View_at_Night.jpg",
        "best_time": "Evening (sunset view)",
        "activities": ["Scenic views", "Photography", "Picnics", "Monkey watching"],
        "category": "Nature"
    },
    "Lok Virsa Museum": {
        "description": "The National Institute of Folk & Traditional Heritage, showcasing Pakistan's cultural heritage through artifacts, crafts, and music.",
        "location": [33.6895, 73.0770],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Lok_Virsa_Museum.jpg/1200px-Lok_Virsa_Museum.jpg",
        "best_time": "Weekday mornings",
        "activities": ["Cultural exhibits", "Folk music", "Craft shopping"],
        "category": "Cultural"
    },
    "Margalla Hills National Park": {
        "description": "A large natural reserve with hiking trails, wildlife, and beautiful scenery. Perfect for nature lovers and adventure seekers.",
        "location": [33.7480, 73.0375],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/56/Margalla_Hills.jpg/1200px-Margalla_Hills.jpg",
        "best_time": "Early morning or late afternoon",
        "activities": ["Hiking", "Bird watching", "Wildlife spotting", "Photography"],
        "category": "Nature"
    },
    "Rawal Lake": {
        "description": "An artificial reservoir that supplies water to Islamabad and Rawalpindi. The lake view park offers boating, fishing, and picnic spots.",
        "location": [33.6969, 73.1292],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Rawal_Lake_Islamabad.jpg/1200px-Rawal_Lake_Islamabad.jpg",
        "best_time": "Morning or evening",
        "activities": ["Boating", "Fishing", "Picnics", "Bird watching"],
        "category": "Nature"
    },
    "Lake View Park": {
        "description": "A family amusement park on the banks of Rawal Lake, offering recreational facilities, gardens, and a bird aviary.",
        "location": [33.7014, 73.1230],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Lake_View_Park_Islamabad.jpg/1200px-Lake_View_Park_Islamabad.jpg",
        "best_time": "Evening",
        "activities": ["Amusement rides", "Boating", "Picnics", "Bird watching"],
        "category": "Recreation"
    },
    "Shakarparian": {
        "description": "A hilly area with terraced gardens, a cultural complex, and the Pakistan Monument Museum.",
        "location": [33.6890, 73.0695],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Shakar_Parian_Islamabad.JPG/1200px-Shakar_Parian_Islamabad.JPG",
        "best_time": "Evening",
        "activities": ["Garden walks", "Museum visits", "Picnics", "Cultural events"],
        "category": "Nature"
    },
    "Saidpur Village": {
        "description": "A centuries-old village transformed into a cultural center with restaurants, craft shops, and historic buildings.",
        "location": [33.7385, 73.0587],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ef/Saidpur_Village.jpg/1200px-Saidpur_Village.jpg",
        "best_time": "Evening",
        "activities": ["Dining", "Shopping", "Cultural exploration", "Photography"],
        "category": "Cultural"
    },
    "Centaurus Mall": {
        "description": "A luxury shopping mall with international brands, a food court, and entertainment facilities.",
        "location": [33.7096, 73.0493],
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Centaurus_Mall_Islamabad.jpg/1200px-Centaurus_Mall_Islamabad.jpg",
        "best_time": "Afternoon or evening",
        "activities": ["Shopping", "Dining", "Movies", "Entertainment"],
        "category": "Shopping"
    }
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
    </style>
    """, unsafe_allow_html=True)

# App functions
def create_map(attractions):
    m = folium.Map(location=[33.7294, 73.0931], zoom_start=12, tiles="OpenStreetMap")
    
    for name, info in attractions.iterrows():
        popup_html = f"""
        <div style="width: 200px; text-align: center;">
            <h3>{name}</h3>
            <p><b>Category:</b> {info['category']}</p>
            <p><b>Best time:</b> {info['best_time']}</p>
            <a href="#{name.replace(' ', '_')}" target="_self">More details</a>
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

def display_itinerary(selected_attractions, days):
    if not selected_attractions or days < 1:
        return
    
    attractions_per_day = max(1, len(selected_attractions) // days)
    remaining = len(selected_attractions) % days
    
    st.markdown(f"<h2 class='sub-header'>Your {days}-Day Itinerary</h2>", unsafe_allow_html=True)
    
    daily_attractions = []
    start_idx = 0
    
    for day in range(1, days + 1):
        count = attractions_per_day + (1 if day <= remaining else 0)
        end_idx = start_idx + count
        daily_attractions.append(selected_attractions[start_idx:end_idx])
        start_idx = end_idx
    
    for day in range(1, days + 1):
        with st.expander(f"Day {day}", expanded=True):
            st.write("---")
            for attraction in daily_attractions[day-1]:
                info = attractions_df.loc[attraction]
                
                # Morning/Afternoon/Evening recommendation based on best time
                time_of_day = "Morning"
                if "evening" in info['best_time'].lower():
                    time_of_day = "Evening"
                elif "afternoon" in info['best_time'].lower():
                    time_of_day = "Afternoon"
                
                st.markdown(f"<h3>{time_of_day}: {attraction}</h3>", unsafe_allow_html=True)
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(info['image'], caption=attraction, use_column_width=True)
                
                with col2:
                    st.markdown(f"<span class='category-pill category-{info['category']}'>{info['category']}</span>", unsafe_allow_html=True)
                    st.write(info['description'])
                    st.write(f"**Best time to visit:** {info['best_time']}")
                    
                    st.write("**Activities:**")
                    activities_html = ""
                    for activity in info['activities']:
                        activities_html += f"<span class='activity-tag'>{activity}</span>"
                    st.markdown(activities_html, unsafe_allow_html=True)
                
                st.write("---")

def main():
    load_css()
    
    # Header
    st.markdown("<h1 class='main-header'>🏙️ Islamabad Tourism Assistant</h1>", unsafe_allow_html=True)
    
    # Sidebar for filters and selections
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Faisal_Mosque_July_1_2005_pic32.JPG/800px-Faisal_Mosque_July_1_2005_pic32.JPG", caption="Islamabad - The Beautiful")
    
    st.sidebar.markdown("## Plan Your Visit")
    
    # Category filter
    categories = sorted(attractions_df['category'].unique())
    selected_categories = st.sidebar.multiselect(
        "Filter by Category",
        categories,
        default=categories
    )
    
    # Activities filter
    all_activities = []
    for acts in attractions_df['activities']:
        all_activities.extend(acts)
    unique_activities = sorted(set(all_activities))
    
    selected_activities = st.sidebar.multiselect(
        "Filter by Activities",
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
    
    # Itinerary planner
    st.sidebar.markdown("## Itinerary Planner")
    available_attractions = filtered_attractions['name'].tolist()
    
    selected_attractions = st.sidebar.multiselect(
        "Select Attractions for Itinerary",
        available_attractions,
        default=available_attractions[:3] if len(available_attractions) >= 3 else available_attractions
    )
    
    days = st.sidebar.slider("Number of Days", 1, 7, 2)
    
    # Weather information
    st.sidebar.markdown("## Current Weather")
    st.sidebar.info(
        "☀️ **Current:** 28°C, Sunny\n\n"
        "🌡️ **Today:** 25-32°C\n\n"
        "💨 **Wind:** 10 km/h\n\n"
        "💧 **Humidity:** 45%"
    )
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Map", "Attractions", "Itinerary", "Travel Tips"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Explore Islamabad</h2>", unsafe_allow_html=True)
        st.write("Interactive map of top attractions in Islamabad. Click on markers for details.")
        
        if not filtered_attractions.empty:
            m = create_map(filtered_attractions)
            folium_static(m, width=800, height=500)
        else:
            st.warning("No attractions match your filters. Please adjust your selections.")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>Top Attractions</h2>", unsafe_allow_html=True)
        
        if not filtered_attractions.empty:
            for name, info in filtered_attractions.iterrows():
                with st.container():
                    st.markdown(f"<div class='attraction-card' id='{name.replace(' ', '_')}'></div>", unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.image(info['image'], caption=name, use_column_width=True)
                    
                    with col2:
                        st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<span class='category-pill category-{info['category']}'>{info['category']}</span>", unsafe_allow_html=True)
                        st.write(info['description'])
                        st.write(f"**Location:** {info['location'][0]}, {info['location'][1]}")
                        st.write(f"**Best time to visit:** {info['best_time']}")
                        
                        activities_html = ""
                        for activity in info['activities']:
                            activities_html += f"<span class='activity-tag'>{activity}</span>"
                        st.markdown(f"**Activities:** {activities_html}", unsafe_allow_html=True)
        else:
            st.warning("No attractions match your filters. Please adjust your selections.")
    
    with tab3:
        if selected_attractions:
            display_itinerary(selected_attractions, days)
        else:
            st.info("Select attractions and number of days in the sidebar to generate an itinerary.")
    
    with tab4:
        st.markdown("<h2 class='sub-header'>Travel Tips for Islamabad</h2>", unsafe_allow_html=True)
        
        tips = {
            "Best Time to Visit": "October to May, when the weather is pleasant and suitable for outdoor activities.",
            "Transportation": "Uber and Careem are readily available. Local buses and taxis are options too. Renting a car is recommended for flexibility.",
            "Accommodation": "Blue Area and F-sectors have many hotels ranging from budget to luxury options.",
            "Local Cuisine": "Try local dishes like Chapli Kabab, Biryani, and traditional tea (chai) at Monal Restaurant or Des Pardes.",
            "Cultural Etiquette": "Dress modestly, especially when visiting religious sites. Remove shoes before entering mosques.",
            "Safety": "Islamabad is generally considered safe. However, always keep an eye on your belongings and follow travel advisories.",
            "Language": "Urdu is the national language, but English is widely spoken in tourist areas."
        }
        
        for title, content in tips.items():
            with st.expander(title, expanded=True):
                st.write(content)
        
        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
        st.write("**Emergency Contacts:**")
        st.write("- Police: 15")
        st.write("- Ambulance: 1122")
        st.write("- Tourist Information: +92-51-9272117")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
