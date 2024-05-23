import simpy
import random
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from geopy.distance import geodesic
import matplotlib.pyplot as plt

# Step 1: Setup Environment

# Define road network (simple example)
road_lines = [
    LineString([(37.7749, -122.4194), (37.7750, -122.4183), (37.7760, -122.4172), (37.7770, -122.4161)])
]

road_network = gpd.GeoDataFrame(geometry=road_lines)

# Define toll zones
toll_zones = [
    Polygon([(37.7749, -122.4194), (37.7750, -122.4183), (37.7745, -122.4180), (37.7749, -122.4194)]),
    Polygon([(37.7760, -122.4172), (37.7770, -122.4161), (37.7755, -122.4150), (37.7760, -122.4172)])
]

toll_zones_gdf = gpd.GeoDataFrame(geometry=toll_zones)

# Define initial vehicle positions and destinations
initial_positions = [
    (37.7749, -122.4194),
    (37.7749, -122.4194),
    (37.7749, -122.4194),
    (37.7749, -122.4194),
    (37.7749, -122.4194)
]

destinations = [
    (37.7770, -122.4161),
    (37.7770, -122.4161),
    (37.7770, -122.4161),
    (37.7770, -122.4161),
    (37.7770, -122.4161)
]

# Step 2: Simulate Vehicle Movement

def detect_toll_crossing(current_position, toll_zones_gdf):
    for toll_zone in toll_zones_gdf.geometry:
        if toll_zone.contains(current_position):
            return True
    return False

def calculate_toll_charge(distance, rate_per_km=0.05, fixed_fee=1.00):
    return max(distance * rate_per_km, fixed_fee)

user_accounts = {i: 100.0 for i in range(len(initial_positions))}

def deduct_toll_charge(vehicle_id, charge):
    if user_accounts[vehicle_id] >= charge:
        user_accounts[vehicle_id] -= charge
        return True
    else:
        return False

# Step 6: Analytics and Reporting
vehicle_movements = []
toll_collections = []

def vehicle(env, vehicle_id, start, end, road_network, toll_zones_gdf):
    current_position = Point(start)
    while current_position.distance(Point(end)) > 0.001:  # 0.001 degrees as a simple threshold
        step_lat = (end[0] - current_position.x) * 0.01
        step_lon = (end[1] - current_position.y) * 0.01
        current_position = Point(current_position.x + step_lat, current_position.y + step_lon)
        
        if detect_toll_crossing(current_position, toll_zones_gdf):
            distance_traveled = geodesic((start[0], start[1]), (current_position.x, current_position.y)).km
            toll_charge = calculate_toll_charge(distance_traveled)
            if deduct_toll_charge(vehicle_id, toll_charge):
                toll_collections.append((vehicle_id, toll_charge, env.now))
        
        vehicle_movements.append((vehicle_id, current_position.x, current_position.y, env.now))
        yield env.timeout(1)

# Initialize the Simpy environment
env = simpy.Environment()

# Start vehicle processes
for i in range(len(initial_positions)):
    env.process(vehicle(env, i, initial_positions[i], destinations[i], road_network, toll_zones_gdf))

# Run the simulation
env.run(until=100)

# Convert movements and collections to DataFrames for reporting
movements_df = pd.DataFrame(vehicle_movements, columns=['vehicle_id', 'lat', 'lon', 'time'])
toll_collections_df = pd.DataFrame(toll_collections, columns=['vehicle_id', 'charge', 'time'])

print("Vehicle Movements:")
print(movements_df.head())

print("\nToll Collections:")
print(toll_collections_df.head())

# Plot vehicle movements
for vehicle_id, group in movements_df.groupby('vehicle_id'):
    plt.plot(group['lon'], group['lat'], label=f'Vehicle {vehicle_id}')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Vehicle Movements')
plt.legend()
plt.show()

# Plot toll collections over time
toll_collections_df.groupby('time')['charge'].sum().plot(kind='bar')
plt.xlabel('Time')
plt.ylabel('Toll Collections')
plt.title('Toll Collections Over Time')
plt.show()
