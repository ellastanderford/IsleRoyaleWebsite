# Isle Royale Backcountry Route Planner

A production-ready backcountry trip-planning web application built for backpackers exploring Isle Royale National Park. The platform allows users to build multi-day itineraries, automatically calculates true-trail cumulative mileages using an implementation of **Dijkstra's Algorithm**, builds dynamic interactive maps, tracks daily meal weight metrics, and manages an interactive gear checklist.

🚀 https://isleroyalewebsite.onrender.com/

---

## 🛠️ Tech Stack & Architecture

* **Backend Engine:** Python, Flask (Web Framework)
* **Algorithmic Graph Engine:** Custom Dijkstra's Shortest Path Algorithm
* **Geospatial Mapping Layer:** Folium (OpenStreetMap & Leaflet.js wrappers)
* **Frontend Architecture:** HTML5, CSS3, JavaScript (Vanilla UI updates)
* **Design Pattern:** Jinja2 Template Inheritance (`layout.html` template layout)

---

## 💡 Engineering Highlights

### 1. Advanced Pathfinding Engine (Dijkstra's Algorithm)
Standard portfolio map applications draw straight "as-the-crow-flies" lines between locations, which cuts straight across bays and open water on an island. 

This application models Isle Royale's official National Park Service trail network as a **weighted, undirected graph**. 
* **Nodes:** 34 official backcountry campsites.
* **Edges & Weights:** True topographic trail distances between connected junctions.

When a user selects an itinerary sequence, the backend graph engine executes Dijkstra's algorithm to calculate the absolute shortest path over the actual trail ridges, mapping intermediate points accurately and returning the exact topological cumulative distance.

### 2. Live Map Layering
Leveraging `Folium`, the app parses the list sequence returned by the algorithm, fetches spatial coordinates from an internal database mapping layout, and dynamically renders standard mapping markers and a geometric dashed trail layer on an embedded iframe canvas.

### 3. Dry & Performant Frontend Layouts
* Implements **Jinja2 Template Inheritance** via a master `layout.html` file to keep structural styling unified and prevent codebase bloat.
* Handles frontend state logic (like item cross-offs on the **Gear Checklist**) using browser-side JavaScript, eliminating unnecessary API roundtrips to the server.

---

## 📦 Features

* **Interactive Route Mapping:** Add or remove multi-day stops and watch the trail map snap along the geography of the island.
* **Visual Image Carousel:** Clean, self-contained layout showcasing public domain photography from the National Park Service gallery.
* **Dynamic Meal Metric Logs:** Track breakfast, lunch, dinner, and snack configurations while tracking total food base weight metrics.
* **Functional Checklist Engine:** Check items off interactively before checking out into the backcountry.

---

## 🚀 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
