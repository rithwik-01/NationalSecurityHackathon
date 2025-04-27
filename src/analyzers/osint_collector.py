# src/analyzers/osint_collector.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
import random
from typing import Dict, List, Any
import kagglehub
import glob

class OSINTCollector:
    def __init__(self, cache_dir: str = "data/osint", project_dir: str = None):
        self.cache_dir = cache_dir
        self.project_dir = project_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        self.dataset_dir = os.path.join(self.project_dir, cache_dir)
        os.makedirs(self.dataset_dir, exist_ok=True)
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
    
    def _get_random_user_agent(self):
        """Get a random user agent to avoid detection"""
        return random.choice(self.user_agents)
    
    def collect_ais_data(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Collect AIS shipping data from Kaggle dataset"""
        cache_file = os.path.join(self.dataset_dir, "processed_kaggle_ais.json")
        
        # Check if we have already processed data
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                all_vessels = json.load(f)
                # Return requested number of vessels
                return all_vessels[:limit]
        
        # Download the dataset if we don't have it
        dataset_files = self._download_kaggle_ais_dataset()
        if not dataset_files:
            print("Failed to download Kaggle AIS dataset")
            return self._generate_simulated_vessels(limit)
        
        try:
            # Find the CSV file in the dataset
            csv_files = [f for f in dataset_files if f.endswith('.csv')]
            if not csv_files:
                print("No CSV files found in the dataset")
                return self._generate_simulated_vessels(limit)
            
            # Use the first CSV file
            dataset_path = csv_files[0]
            print(f"Using AIS dataset file: {dataset_path}")
            
            # Load and process the dataset
            df = pd.read_csv(dataset_path)
            
            # Process the data into our format
            vessels = []
            # Group by MMSI to get unique vessels
            for mmsi, group in df.groupby('MMSI'):
                # Use the most recent data for each vessel
                if 'BaseDateTime' in group.columns:
                    latest = group.sort_values('BaseDateTime', ascending=False).iloc[0]
                else:
                    latest = group.iloc[0]  # If no datetime column, just use the first row
                
                # Extract vessel information
                vessel_name = latest.get('VesselName', f"VESSEL_{mmsi}") if 'VesselName' in latest else f"VESSEL_{mmsi}"
                vessel_type = latest.get('VesselType', 'Unknown') if 'VesselType' in latest else 'Unknown'
                
                # Get position data
                lat = latest.get('LAT', 0) if 'LAT' in latest else latest.get('Latitude', 0)
                lon = latest.get('LON', 0) if 'LON' in latest else latest.get('Longitude', 0)
                
                vessel = {
                    "mmsi": str(mmsi),
                    "imo": f"IMO{random.randint(1000000, 9999999)}",  # IMO might not be in dataset
                    "vessel_name": vessel_name,
                    "vessel_type": vessel_type,
                    "length": latest.get('Length', random.randint(50, 300)) if 'Length' in latest else random.randint(50, 300),
                    "width": latest.get('Width', random.randint(10, 50)) if 'Width' in latest else random.randint(10, 50),
                    "position": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "course": latest.get('Course', 0) if 'Course' in latest else 0,
                    "speed": latest.get('Speed', 0) if 'Speed' in latest else 0,
                    "destination": latest.get('Destination', 'Unknown') if 'Destination' in latest else 'Unknown',
                    "systems": self._determine_vessel_systems(vessel_type),
                    "security_level": self._determine_security_level_from_type(vessel_type)
                }
                vessels.append(vessel)
                
                # Limit the number of vessels to process if dataset is very large
                if len(vessels) >= limit * 10:  # Process 10x the limit to have a good selection
                    break
            
            # If we couldn't extract any vessels, fall back to simulated data
            if not vessels:
                print("No vessels could be extracted from the dataset")
                return self._generate_simulated_vessels(limit)
            
            # Cache the processed data
            with open(cache_file, "w") as f:
                json.dump(vessels, f, indent=2)
            
            # Return requested number of vessels
            return vessels[:limit]
            
        except Exception as e:
            print(f"Error processing Kaggle AIS dataset: {e}")
            # Fall back to simulated data
            return self._generate_simulated_vessels(limit)
    
    def _download_kaggle_ais_dataset(self) -> List[str]:
        """Download the AIS dataset from Kaggle using kagglehub"""
        try:
            print("Downloading AIS dataset from Kaggle...")
            # Download the dataset to our project directory
            path = kagglehub.dataset_download(
                "eminserkanerdonmez/ais-dataset",
                cache_dir=self.dataset_dir
            )
            print(f"Dataset downloaded to: {path}")
            
            # Check if it's a directory or a file
            if os.path.isdir(path):
                # Get all files in the directory
                files = glob.glob(os.path.join(path, "*"))
            else:
                # It's a single file
                files = [path]
            
            print(f"Found {len(files)} files in the dataset")
            return files
            
        except Exception as e:
            print(f"Error downloading Kaggle dataset: {e}")
            return []
    
    def _determine_vessel_systems(self, vessel_type: str) -> List[str]:
        """Determine likely systems based on vessel type"""
        base_systems = ["navigation", "communication", "engine_control"]
        
        vessel_type_lower = str(vessel_type).lower()
        
        if "cargo" in vessel_type_lower or "tanker" in vessel_type_lower:
            return base_systems + ["cargo_management", "ballast_management"]
        elif "passenger" in vessel_type_lower or "cruise" in vessel_type_lower:
            return base_systems + ["passenger_management", "entertainment_systems"]
        elif "military" in vessel_type_lower or "law enforcement" in vessel_type_lower:
            return base_systems + ["weapons_systems", "surveillance_systems"]
        elif "fishing" in vessel_type_lower:
            return base_systems + ["fishing_equipment", "refrigeration_systems"]
        else:
            return base_systems + ["crew_systems"]
    
    def _determine_security_level_from_type(self, vessel_type: str) -> str:
        """Determine likely security level based on vessel type"""
        vessel_type_lower = str(vessel_type).lower()
        
        if "military" in vessel_type_lower or "law enforcement" in vessel_type_lower:
            return "high"
        elif "passenger" in vessel_type_lower or "cruise" in vessel_type_lower or "tanker" in vessel_type_lower:
            return "medium"
        else:
            return "low"
    
    def _generate_simulated_vessels(self, limit: int) -> List[Dict[str, Any]]:
        """Generate simulated vessel data as fallback"""
        print(f"Generating {limit} simulated vessels as fallback")
        vessels = []
        for i in range(limit):
            vessel = {
                "mmsi": f"{random.randint(100000000, 999999999)}",
                "imo": f"IMO{random.randint(1000000, 9999999)}",
                "vessel_name": f"VESSEL{random.randint(1000, 9999)}",
                "vessel_type": random.choice(["Cargo", "Tanker", "Passenger", "Military", "Fishing"]),
                "length": random.randint(50, 300),
                "width": random.randint(10, 50),
                "position": {
                    "latitude": random.uniform(-90, 90),
                    "longitude": random.uniform(-180, 180)
                },
                "course": random.uniform(0, 359),
                "speed": random.uniform(0, 20),
                "destination": random.choice(["NEW YORK", "ROTTERDAM", "SINGAPORE", "SHANGHAI", "DUBAI"]),
                "systems": random.sample([
                    "navigation", 
                    "communication", 
                    "cargo_management", 
                    "crew_systems",
                    "engine_control",
                    "ballast_management",
                    "security_systems"
                ], k=random.randint(3, 5)),
                "security_level": random.choice(["low", "medium", "high"])
            }
            vessels.append(vessel)
        
        return vessels
    
    def collect_infrastructure_data(self, country: str = "US", limit: int = 10) -> List[Dict[str, Any]]:
        """Collect critical infrastructure data from real sources"""
        # This method remains the same as before
        cache_file = os.path.join(self.dataset_dir, f"infrastructure_{country}.json")
        
        # Check if we have cached data less than 24 hours old
        if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < 86400:
            with open(cache_file, "r") as f:
                return json.load(f)
        
        try:
            # Try to fetch real infrastructure data
            # Note: In a real implementation, you would use public data sources or APIs
            # This is a simplified example using a combination of real and simulated data
            facilities = []
            
            # Add some real facility data (from public sources)
            real_facilities = [
                {"id": "FAC10001", "name": "Hoover Dam", "type": "Power Plant", "location": {"city": "Boulder City", "state": "Nevada", "country": "US"}},
                {"id": "FAC10002", "name": "Three Mile Island", "type": "Power Plant", "location": {"city": "Londonderry Township", "state": "Pennsylvania", "country": "US"}},
                {"id": "FAC10003", "name": "O'Hare International Airport", "type": "Transportation Hub", "location": {"city": "Chicago", "state": "Illinois", "country": "US"}},
                {"id": "FAC10004", "name": "Raven Rock Mountain Complex", "type": "Government Facility", "location": {"city": "Liberty Township", "state": "Pennsylvania", "country": "US"}},
                {"id": "FAC10005", "name": "Ashburn Data Center Alley", "type": "Data Center", "location": {"city": "Ashburn", "state": "Virginia", "country": "US"}}
            ]
            
            for facility in real_facilities:
                # Enrich with additional data
                facility_type = facility["type"]
                
                if facility_type == "Power Plant":
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access", "Power Distribution"]
                elif facility_type == "Transportation Hub":
                    systems = ["Air Traffic Control", "Physical Security", "IT Network", "Employee Access", "Passenger Management"]
                elif facility_type == "Data Center":
                    systems = ["Cooling Systems", "Physical Security", "IT Network", "Employee Access", "Power Management"]
                elif facility_type == "Government Facility":
                    systems = ["Access Control", "Physical Security", "IT Network", "Employee Access", "Communications"]
                else:
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access"]
                
                enriched_facility = {
                    **facility,
                    "size": random.choice(["Small", "Medium", "Large"]),
                    "security_level": random.choice(["low", "medium", "high"]),
                    "systems": systems,
                    "location": {
                        **facility["location"],
                        "coordinates": {
                            "latitude": random.uniform(25, 49),  # US latitude range
                            "longitude": random.uniform(-125, -66)  # US longitude range
                        }
                    }
                }
                facilities.append(enriched_facility)
            
            # Add simulated facilities to reach the limit
            facility_types = ["Power Plant", "Water Treatment", "Transportation Hub", "Data Center", "Government Facility"]
            
            while len(facilities) < limit:
                facility_type = random.choice(facility_types)
                
                if facility_type == "Power Plant":
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access", "Power Distribution"]
                    name = f"{random.choice(['Grand', 'Central', 'Northern', 'Western', 'Eastern'])} {random.choice(['Power', 'Energy', 'Electric'])} {random.choice(['Plant', 'Station', 'Facility'])}"
                elif facility_type == "Water Treatment":
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access", "Chemical Management"]
                    name = f"{random.choice(['City', 'Regional', 'Municipal', 'County'])} {random.choice(['Water', 'Wastewater'])} {random.choice(['Plant', 'Facility', 'Treatment Center'])}"
                elif facility_type == "Transportation Hub":
                    systems = ["Traffic Management", "Physical Security", "IT Network", "Employee Access", "Passenger Management"]
                    name = f"{random.choice(['International', 'Regional', 'Municipal', 'Central'])} {random.choice(['Airport', 'Train Station', 'Bus Terminal', 'Port'])}"
                elif facility_type == "Data Center":
                    systems = ["Cooling Systems", "Physical Security", "IT Network", "Employee Access", "Power Management"]
                    name = f"{random.choice(['Secure', 'Cloud', 'Enterprise', 'Global'])} {random.choice(['Data', 'Computing', 'Server'])} {random.choice(['Center', 'Facility', 'Hub'])}"
                else:  # Government Facility
                    systems = ["Access Control", "Physical Security", "IT Network", "Employee Access", "Communications"]
                    name = f"{random.choice(['Federal', 'State', 'Regional', 'National'])} {random.choice(['Operations', 'Command', 'Administrative', 'Security'])} {random.choice(['Center', 'Facility', 'Building'])}"
                
                facility = {
                    "id": f"FAC{random.randint(10000, 99999)}",
                    "name": name,
                    "type": facility_type,
                    "size": random.choice(["Small", "Medium", "Large"]),
                    "security_level": random.choice(["low", "medium", "high"]),
                    "systems": systems,
                    "location": {
                        "city": f"City{random.randint(1, 50)}",
                        "state": f"State{random.randint(1, 20)}",
                        "country": country,
                        "coordinates": {
                            "latitude": random.uniform(25, 49),  # US latitude range
                            "longitude": random.uniform(-125, -66)  # US longitude range
                        }
                    }
                }
                facilities.append(facility)
            
            # Cache the data
            with open(cache_file, "w") as f:
                json.dump(facilities, f, indent=2)
            
            return facilities
            
        except Exception as e:
            print(f"Error fetching infrastructure data: {e}")
            # Fallback to simulated data if real data collection fails
            facilities = []
            facility_types = ["Power Plant", "Water Treatment", "Transportation Hub", "Data Center", "Government Facility"]
            
            for i in range(limit):
                facility_type = random.choice(facility_types)
                
                if facility_type == "Power Plant":
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access", "Power Distribution"]
                    name = f"{random.choice(['Grand', 'Central', 'Northern', 'Western', 'Eastern'])} {random.choice(['Power', 'Energy', 'Electric'])} {random.choice(['Plant', 'Station', 'Facility'])}"
                elif facility_type == "Water Treatment":
                    systems = ["SCADA", "Physical Security", "IT Network", "Employee Access", "Chemical Management"]
                    name = f"{random.choice(['City', 'Regional', 'Municipal', 'County'])} {random.choice(['Water', 'Wastewater'])} {random.choice(['Plant', 'Facility', 'Treatment Center'])}"
                elif facility_type == "Transportation Hub":
                    systems = ["Traffic Management", "Physical Security", "IT Network", "Employee Access", "Passenger Management"]
                    name = f"{random.choice(['International', 'Regional', 'Municipal', 'Central'])} {random.choice(['Airport', 'Train Station', 'Bus Terminal', 'Port'])}"
                elif facility_type == "Data Center":
                    systems = ["Cooling Systems", "Physical Security", "IT Network", "Employee Access", "Power Management"]
                    name = f"{random.choice(['Secure', 'Cloud', 'Enterprise', 'Global'])} {random.choice(['Data', 'Computing', 'Server'])} {random.choice(['Center', 'Facility', 'Hub'])}"
                else:  # Government Facility
                    systems = ["Access Control", "Physical Security", "IT Network", "Employee Access", "Communications"]
                    name = f"{random.choice(['Federal', 'State', 'Regional', 'National'])} {random.choice(['Operations', 'Command', 'Administrative', 'Security'])} {random.choice(['Center', 'Facility', 'Building'])}"
                
                facility = {
                    "id": f"FAC{random.randint(10000, 99999)}",
                    "name": name,
                    "type": facility_type,
                    "size": random.choice(["Small", "Medium", "Large"]),
                    "security_level": random.choice(["low", "medium", "high"]),
                    "systems": systems,
                    "location": {
                        "city": f"City{random.randint(1, 50)}",
                        "state": f"State{random.randint(1, 20)}",
                        "country": country,
                        "coordinates": {
                            "latitude": random.uniform(25, 49),  # US latitude range
                            "longitude": random.uniform(-125, -66)  # US longitude range
                        }
                    }
                }
                facilities.append(facility)
            
            # Cache the fallback data
            with open(cache_file, "w") as f:
                json.dump(facilities, f, indent=2)
            
            return facilities
    
    def search_osint_data(self, query: str, data_type: str = "all") -> List[Dict[str, Any]]:
        """Search through collected OSINT data"""
        results = []
        
        if data_type in ["all", "maritime"]:
            maritime_data = self.collect_ais_data()
            for vessel in maritime_data:
                # Simple search implementation - check if query is in any string value
                vessel_str = json.dumps(vessel).lower()
                if query.lower() in vessel_str:
                    results.append({
                        "type": "maritime",
                        "data": vessel
                    })
        
        if data_type in ["all", "infrastructure"]:
            infrastructure_data = self.collect_infrastructure_data()
            for facility in infrastructure_data:
                # Simple search implementation - check if query is in any string value
                facility_str = json.dumps(facility).lower()
                if query.lower() in facility_str:
                    results.append({
                        "type": "infrastructure",
                        "data": facility
                    })
        
        return results
