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
    "Wood Lake": [48.018419, -88.733648]
}

OFFICIAL_TRAIL_NETWORK = [
    ("Rock Harbor", "Three Mile", 2.7),
    ("Three Mile", "Daisy Farm", 4.4),
    ("Daisy Farm", "Moskey Basin", 3.9),
    ("Three Mile", "Lane Cove", 4.6),
    ("Daisy Farm", "Chickenbone West", 7.9),
    ("Moskey Basin", "Lake Richie", 2.0),
    ("Chickenbone East", "Chickenbone West", 1.8),
    ("Chickenbone East", "McCargoe Cove", 1.2),
    ("Chickenbone West", "McCargoe Cove", 3.2),
    ("Lake Richie", "Chippewa Harbor", 4.3),
    ("Lake Richie", "Malone Bay", 6.3),
    ("Chickenbone West", "Hatchet Lake", 7.9),
    ("Hatchet Lake", "Todd Harbor", 4.1),
    ("Hatchet Lake", "Lake Desor South", 8.1),
    ("Lake Desor South", "Washington Creek (Windigo)", 11.3),
    ("Washington Creek (Windigo)", "Feldtmann Lake", 8.8),
    ("Feldtmann Lake", "Siskiwit Bay", 10.3),
    ("Siskiwit Bay", "Island Mine", 4.4),
    ("Island Mine", "Washington Creek (Windigo)", 6.6),
    ("Washington Creek (Windigo)", "Huginnin Cove", 4.0),
    ("Beaver Island", "Washington Creek (Windigo)", 1.5),
    ("Belle Isle", "McCargoe Cove", 5.2),
    ("Birch Island", "McCargoe Cove", 1.0),
    ("Caribou Island", "Three Mile", 2.0),
    ("Duncan Bay", "Lane Cove", 3.1),
    ("Duncan Narrows", "Duncan Bay", 1.5),
    ("Grace Island", "Washington Creek (Windigo)", 2.5),
    ("Lake Desor North", "Lake Desor South", 3.0),
    ("Lake Richie Canoe", "Lake Richie", 0.8),
    ("Little Todd Harbor", "Todd Harbor", 6.8),
    ("Pickerel Cove", "Three Mile", 3.2),
    ("Tookers Island", "Rock Harbor", 1.8),
    ("Wood Lake", "Lake Richie", 2.1),
    ("Merritt Lane", "Rock Harbor", 4.2),
    ("Hay Bay", "Siskiwit Bay", 4.5)
]

# ==========================================
# 2. state management storage
# ==========================================
saved_route_plan = [
    {"day": "Day 1", "campground": "Rock Harbor"},
    {"day": "Day 2", "campground": "Three Mile"},
    {"day": "Day 3", "campground": "Daisy Farm"}
]

trip_meals = [
    {"day": "Day 1", "breakfast": "Oatmeal", "lunch": "Tuna & Tortillas", "dinner": "Dehydrated Chili", "snack": "Trail Mix", "weight": 14.5}
]

gear_list = ["Tent", "Sleeping Bag", "Water Filter"]

# ====================================================
# 3. professional trail tracking core (dijkstra code)
# ====================================================
def find_shortest_path_trail(start, target):
    """
    advanced dijkstra implementation using a priority queue.
    returns a tuple of (total_distance, list_of_campground_nodes_visited)
    this ensures map paths snap along true trails instead of drawing across open water
    """
    if start == target:
        return 0.0, [start]

    graph = {camp: [] for camp in ALL_CAMPGROUNDS.keys()}
    for u, v, w in OFFICIAL_TRAIL_NETWORK:
        if u in graph and v in graph:
            graph[u].append((v, w))
            graph[v].append((u, w))

    # Priority queue storing (distance, current_node)
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

    # Stitch back path nodes sequentially
    path = []
    curr = target
    while curr is not None:
        path.insert(0, curr)
        curr = previous_nodes[curr]
        
    return distances[target], path


def parse_full_itinerary_map_data(route_plan):
    """
    scans your multi-day stops and chains together the exact trail snaps
    returns: (mileage_string, listing_of_all_lat_lng_trail_points)
    """
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
        
        # append coordinate sequences safely without duplication overlaps
        for node in node_path:
            coords = ALL_CAMPGROUNDS[node]
            if not complete_trail_gps_points or complete_trail_gps_points[-1] != coords:
                complete_trail_gps_points.append(coords)

    return f"{round(total_miles, 1)}", complete_trail_gps_points

# ==========================================
# 4. layout views controllers
# ==========================================
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
            saved_route_plan.append({"day": f"Day {new_day}", "campground": "Rock Harbor"})
            
        elif action == 'remove_stop':
            if len(saved_route_plan) > 0:
                saved_route_plan.pop()
                
        elif action == 'save_route':
            for index in range(len(saved_route_plan)):
                selected_camp = request.form.get(f'camp_{index}')
                if selected_camp in ALL_CAMPGROUNDS:
                    saved_route_plan[index]['campground'] = selected_camp

    # setup underlying base canvas map
    ir_map = folium.Map(location=[48.05, -88.80], zoom_start=10, control_scale=True)

    # plot base anchor nodes for the 34 campgrounds
    for name, coords in ALL_CAMPGROUNDS.items():
        folium.CircleMarker(
            location=coords, radius=5, popup=name,
            color='dimgray', fill=True, fill_color='lightgray', fill_opacity=0.7
        ).add_to(ir_map)

    # query trailing traces and cumulative path distance totals
    total_miles, snapped_trail_coordinates = parse_full_itinerary_map_data(saved_route_plan)

    # drop custom clear pin markers for designated itinerary travel hubs
    for index, stop in enumerate(saved_route_plan):
        camp_name = stop['campground']
        if camp_name in ALL_CAMPGROUNDS:
            folium.Marker(
                location=ALL_CAMPGROUNDS[camp_name],
                popup=f"{stop['day']}: {camp_name}",
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(ir_map)

    # draw line layers dynamically snapped on calculated coordinates
    if len(snapped_trail_coordinates) > 1:
        folium.PolyLine(
            locations=snapped_trail_coordinates,
            color='blue', weight=4, opacity=0.85, dash_array='5, 10'
        ).add_to(ir_map)

    # Make sure the templates directory exists
    os.makedirs('templates', exist_ok=True)
    ir_map.save('templates/map_embed.html')

    return render_template('itinerary.html', 
                           route=saved_route_plan, 
                           campgrounds=sorted(ALL_CAMPGROUNDS.keys()), 
                           total_miles=total_miles)

@app.route('/map_embed')
def map_embed():
    return render_template('map_embed.html')

@app.route('/meals', methods=['GET', 'POST'])
def meals():
    global trip_meals
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            new_day_num = len(trip_meals) + 1
            trip_meals.append({
                "day": f"Day {new_day_num}", 
                "breakfast": "", "lunch": "", "dinner": "", "snack": "", "weight": 0.0
            })
        elif action == 'remove':
            if len(trip_meals) > 0:
                trip_meals.pop()
        else:
            for index in range(len(trip_meals)):
                trip_meals[index]['breakfast'] = request.form.get(f'breakfast_{index}', '')
                trip_meals[index]['lunch'] = request.form.get(f'lunch_{index}', '')
                trip_meals[index]['dinner'] = request.form.get(f'dinner_{index}', '')
                trip_meals[index]['snack'] = request.form.get(f'snack_{index}', '')
                
                try:
                    weight_val = request.form.get(f'weight_{index}', '0')
                    trip_meals[index]['weight'] = float(weight_val) if weight_val.strip() else 0.0
                except ValueError:
                    trip_meals[index]['weight'] = 0.0

    total_weight = sum(meal.get('weight', 0.0) for meal in trip_meals)
    return render_template('meals.html', meals=trip_meals, total_weight=round(total_weight, 2))

@app.route('/packing', methods=['GET', 'POST'])
def packing():
    global gear_list
    if request.method == 'POST':
        item_to_add = request.form.get('new_item')
        if item_to_add:
            gear_list.append(item_to_add)
    return render_template('packing.html', gear=gear_list)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)