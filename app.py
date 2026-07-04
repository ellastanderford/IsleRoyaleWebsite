import os
import heapq
from flask import Flask, render_template, request
import folium

app = Flask(__name__)

# ==========================================
# 1. campground database & map coordinates
# ==========================================
ALL_CAMPGROUNDS = {
    "Beaver Island": [47.904424, -89.174108],
    "Belle Isle": [48.157932, -88.586855],
    "Birch Island": [48.119809, -88.689763],
    "Caribou Island": [48.100179, -88.569310],
    "Chickenbone East": [48.084501, -88.698689],
    "Chickenbone West": [48.072115, -88.725469],
    "Chippewa Harbor": [48.030052, -88.650519],
    "Daisy Farm": [48.096984, -88.598019],
    "Duncan Bay": [48.155665, -88.521566],
    "Duncan Narrows": [48.170007, -88.478093],
    "Feldtmann Lake": [47.849616, -89.182606],
    "Grace Island": [47.891715, -89.217567],
    "Hatchet Lake": [48.021358, -88.847011],
    "Hay Bay": [47.933970, -88.939891],
    "Huginnin Cove": [47.943947, -89.179326],
    "Island Mine": [47.940957, -89.039102],
    "Lake Desor North": [47.981375, -88.993671],
    "Lake Desor South": [47.970990, -88.971582],
    "Lake Richie": [48.051557, -88.687496],
    "Lake Richie Canoe": [48.044038, -88.701623],
    "Lane Cove": [48.149882, -88.558474],
    "Little Todd Harbor": [48.029438, -88.925529],
    "Malone Bay": [47.985260, -88.805700],
    "McCargoe Cove": [48.103000, -88.707000],
    "Merritt Lane": [48.186166, -88.429442],
    "Moskey Basin": [48.064000, -88.643000],
    "Pickerel Cove": [48.127334, -88.653045],
    "Rock Harbor": [48.150626, -88.474865],
    "Siskiwit Bay": [47.899488, -89.000762],
    "Three Mile": [48.129549, -88.529806],
    "Todd Harbor": [48.052702, -88.822095],
    "Tookers Island": [48.134819, -88.492374],
    "Washington Creek (Windigo)": [47.924625, -89.151849],
    "Wood Lake": [48.018419, -88.733648],

    # --- Structural Trail Intersections ---
    "Jct_Mt_Franklin": [48.1328, -88.5492],
    "Jct_Mt_Ojibway": [48.1141, -88.6045],
    "Jct_Lake_Richie_Malone": [48.0435, -88.6790],
    "Jct_Hatchet_Ridge": [48.0381, -88.8312],
    "Jct_Minong_Todd": [48.0610, -88.8105]
}

OFFICIAL_TRAIL_NETWORK = [
    # East Side / Rock Harbor System
    ("Rock Harbor", "Three Mile", 2.7),
    ("Three Mile", "Daisy Farm", 4.4),
    
    # Mount Franklin & Lane Cove Snaps
    ("Three Mile", "Jct_Mt_Franklin", 3.1),
    ("Jct_Mt_Franklin", "Lane Cove", 1.5),
    ("Jct_Mt_Franklin", "Jct_Mt_Ojibway", 2.5),
    
    # Daisy Farm Ridges
    ("Daisy Farm", "Moskey Basin", 3.9),
    ("Daisy Farm", "Jct_Mt_Ojibway", 1.7),
    
    # Central Greenstone Spine
    ("Jct_Mt_Ojibway", "Chickenbone East", 5.9),
    ("Chickenbone East", "Chickenbone West", 1.8),
    ("Chickenbone East", "McCargoe Cove", 1.2),
    ("Chickenbone West", "McCargoe Cove", 3.2),
    
    # Indian Portage Trail
    ("Chickenbone West", "Lake Richie", 3.4),
    ("Chickenbone East", "Lake Richie", 4.3),
    
    # Lake Richie / Moskey Systems
    ("Moskey Basin", "Lake Richie", 2.0),
    ("Lake Richie", "Jct_Lake_Richie_Malone", 0.5),
    ("Jct_Lake_Richie_Malone", "Chippewa Harbor", 3.8),
    ("Jct_Lake_Richie_Malone", "Malone Bay", 5.8),
    ("Wood Lake", "Lake Richie", 2.1),
    ("Lake Richie Canoe", "Lake Richie", 0.8),

    # Todd Harbor / Northern Trails
    ("Chickenbone West", "Jct_Hatchet_Ridge", 5.4),
    ("Jct_Hatchet_Ridge", "Hatchet Lake", 0.8),
    ("Hatchet Lake", "Jct_Minong_Todd", 3.3),
    ("Jct_Minong_Todd", "Todd Harbor", 0.8),
    ("Jct_Minong_Todd", "Little Todd Harbor", 6.8),
    ("Belle Isle", "McCargoe Cove", 5.2),
    ("Birch Island", "McCargoe Cove", 1.0),

    # West End Base Chains
    ("Jct_Hatchet_Ridge", "Lake Desor South", 8.1),
    ("Lake Desor South", "Washington Creek (Windigo)", 11.3),
    ("Lake Desor North", "Lake Desor South", 3.0),
    ("Washington Creek (Windigo)", "Feldtmann Lake", 8.8),
    ("Feldtmann Lake", "Siskiwit Bay", 10.3),
    ("Siskiwit Bay", "Island Mine", 4.4),
    ("Island Mine", "Washington Creek (Windigo)", 6.6),
    ("Washington Creek (Windigo)", "Huginnin Cove", 4.0),
    
    # Connectors
    ("Beaver Island", "Washington Creek (Windigo)", 1.5),
    ("Grace Island", "Washington Creek (Windigo)", 2.5),
    ("Caribou Island", "Three Mile", 2.0),
    ("Duncan Narrows", "Duncan Bay", 1.5),
    ("Duncan Bay", "Jct_Mt_Franklin", 2.0),
    ("Pickerel Cove", "Three Mile", 3.2),
    ("Tookers Island", "Rock Harbor", 1.8),
    ("Merritt Lane", "Rock Harbor", 4.2),
    ("Hay Bay", "Siskiwit Bay", 4.5)
]

saved_route_plan = [
    {"day": "Day 1", "campground": "Rock Harbor"}
]
trip_meals = []
gear_list = []

def find_shortest_path_trail(start, target):
    if start == target:
        return 0.0, [start]

    graph = {camp: [] for camp in ALL_CAMPGROUNDS.keys()}
    for u, v, w in OFFICIAL_TRAIL_NETWORK:
        if u in graph and v in graph:
            graph[u].append((v, w))
            graph[v].append((u, w))

    pq = [(0.0, start)]
    distances = {node: float('inf') for node in graph}
    previous_nodes = {node: None for node in graph}
    distances[start] = 0.0

    while pq:
        current_distance, current_node = heapq.heappop(pq)
        if current_distance > distances[current_node]:
            continue
        if current_node == target:
            break

        for neighbor, weight in graph[current_node]:
            alt_path = current_distance + weight
            if alt_path < distances[neighbor]:
                distances[neighbor] = alt_path
                previous_nodes[neighbor] = current_node
                heapq.heappush(pq, (alt_path, neighbor))

    if distances[target] == float('inf'):
        return float('inf'), []

    path = []
    curr = target
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
    return distances[target], path

def parse_full_itinerary_map_data(route_plan):
    if len(route_plan) < 2:
        return "0.0", []

    total_miles = 0.0
    complete_trail_gps_points = []

    for i in range(len(route_plan) - 1):
        start = route_plan[i]['campground']
        end = route_plan[i+1]['campground']
        
        miles, node_path = find_shortest_path_trail(start, end)
        if miles == float('inf'):
            return "disconnected trail system paths selected", []
            
        total_miles += miles
        for node in node_path:
            coords = ALL_CAMPGROUNDS[node]
            if not complete_trail_gps_points or complete_trail_gps_points[-1] != coords:
                complete_trail_gps_points.append(coords)

    return f"{round(total_miles, 1)}", complete_trail_gps_points

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/itinerary', methods=['GET', 'POST'])
def itinerary():
    global saved_route_plan

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_stop':
            new_day = len(saved_route_plan) + 1
            last_campground = saved_route_plan[-1]['campground'] if saved_route_plan else "Rock Harbor"
            saved_route_plan.append({"day": f"Day {new_day}", "campground": last_campground})
            
        elif action == 'remove_stop':
            if len(saved_route_plan) > 0:
                saved_route_plan.pop()
                
        elif action == 'save_route':
            for index in range(len(saved_route_plan)):
                selected_camp = request.form.get(f'camp_{index}')
                if selected_camp in ALL_CAMPGROUNDS:
                    saved_route_plan[index]['campground'] = selected_camp

    total_miles, _ = parse_full_itinerary_map_data(saved_route_plan)
    clean_dropdown_campgrounds = sorted([c for c in ALL_CAMPGROUNDS.keys() if not c.startswith("Jct_")])

    return render_template('itinerary.html', 
                           route=saved_route_plan, 
                           campgrounds=clean_dropdown_campgrounds, 
                           total_miles=total_miles)

# This route now dynamically generates the map object directly in memory on request
@app.route('/map_embed')
def map_embed():
    global saved_route_plan
    
    ir_map = folium.Map(location=[48.05, -88.80], zoom_start=10, control_scale=True)

    # Base markers
    for name, coords in ALL_CAMPGROUNDS.items():
        if not name.startswith("Jct_"):
            folium.CircleMarker(
                location=coords, radius=5, popup=name,
                color='dimgray', fill=True, fill_color='lightgray', fill_opacity=0.7
            ).add_to(ir_map)

    # Route math and lines
    _, snapped_trail_coordinates = parse_full_itinerary_map_data(saved_route_plan)

    # Route pins
    for index, stop in enumerate(saved_route_plan):
        camp_name = stop['campground']
        if camp_name in ALL_CAMPGROUNDS:
            folium.Marker(
                location=ALL_CAMPGROUNDS[camp_name],
                popup=f"{stop['day']}: {camp_name}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(ir_map)

    if len(snapped_trail_coordinates) > 1:
        folium.PolyLine(
            locations=snapped_trail_coordinates,
            color='blue', weight=4, opacity=0.85, dash_array='5, 10'
        ).add_to(ir_map)

    return ir_map._repr_html_()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)