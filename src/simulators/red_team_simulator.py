# src/simulators/red_team_simulator.py
from typing import Dict, List, Any
import random
import json
import os
from datetime import datetime
import sys
sys.path.append('../')
from src.models.claude_agent import ClaudeAgent
from src.analyzers.osint_collector import OSINTCollector

class RedTeamSimulator:
    def __init__(self, claude_agent: ClaudeAgent = None, project_dir: str = None):
        self.project_dir = project_dir or os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        self.claude_agent = claude_agent or ClaudeAgent()
        self.osint_collector = OSINTCollector(project_dir=self.project_dir)
        self.current_scenario = None
        self.simulation_history = []
        
    def load_target_from_osint(self, target_type: str, target_id: str = None) -> Dict[str, Any]:
        """Load target information from OSINT sources"""
        if target_type == "maritime":
            # Get real maritime data from Kaggle dataset
            vessels = self.osint_collector.collect_ais_data(limit=20)
            
            if target_id:
                # Find the specific vessel by ID
                for vessel in vessels:
                    if vessel.get("mmsi") == target_id or vessel.get("imo") == target_id:
                        return {
                            "type": "maritime",
                            **vessel
                        }
                
                # If not found, return a random vessel
                print(f"Vessel with ID {target_id} not found, using a random vessel")
                return {
                    "type": "maritime",
                    **random.choice(vessels)
                }
            else:
                # Return a random vessel
                return {
                    "type": "maritime",
                    **random.choice(vessels)
                }
        else:
            # Get infrastructure data
            facilities = self.osint_collector.collect_infrastructure_data(limit=20)
            
            if target_id:
                # Find the specific facility by ID
                for facility in facilities:
                    if facility.get("id") == target_id:
                        return {
                            "type": "infrastructure",
                            **facility
                        }
                
                # If not found, return a random facility
                print(f"Facility with ID {target_id} not found, using a random facility")
                return {
                    "type": "infrastructure",
                    **random.choice(facilities)
                }
            else:
                # Return a random facility
                return {
                    "type": "infrastructure",
                    **random.choice(facilities)
                }
    
    def _load_maritime_target(self, vessel_id: str = None) -> Dict[str, Any]:
        """Load maritime target information from AIS data"""
        # In a real implementation, this would query the AIS APIs
        # For the hackathon, we'll use simulated data
        return {
            "type": "maritime",
            "vessel_id": vessel_id or f"IMO{random.randint(1000000, 9999999)}",
            "vessel_type": random.choice(["cargo", "tanker", "passenger", "military"]),
            "systems": ["navigation", "communication", "cargo_management", "crew_systems"],
            "security_level": random.choice(["low", "medium", "high"]),
            "position": {"lat": random.uniform(-90, 90), "lon": random.uniform(-180, 180)},
            "data_source": "AIS simulation"
        }
    
    def _load_infrastructure_target(self, facility_id: str = None) -> Dict[str, Any]:
        """Load infrastructure target information"""
        # In a real implementation, this would use OSINT data
        # For the hackathon, we'll use simulated data
        return {
            "type": "infrastructure",
            "facility_id": facility_id or f"FAC{random.randint(10000, 99999)}",
            "facility_type": random.choice(["power_plant", "water_treatment", "transportation_hub", "data_center"]),
            "systems": ["scada", "physical_security", "it_network", "employee_access"],
            "security_level": random.choice(["low", "medium", "high"]),
            "location": {"city": "Example City", "country": "Example Country"},
            "data_source": "OSINT simulation"
        }
    
    def generate_attack_scenario(self, target_info: Dict[str, Any], complexity: str = "medium") -> Dict[str, Any]:
        """Generate an attack scenario for the given target"""
        scenario = self.claude_agent.generate_attack_scenario(target_info, complexity)
        self.current_scenario = {
            "target": target_info,
            "scenario": scenario,
            "timestamp": datetime.now().isoformat(),
            "status": "generated"
        }
        return self.current_scenario
    
    def simulate_attack(self, scenario: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate the execution of an attack scenario"""
        scenario = scenario or self.current_scenario
        if not scenario:
            raise ValueError("No scenario available for simulation")
        
        # Simulate attack progression
        steps = scenario["scenario"]["steps"]
        results = []
        
        for i, step in enumerate(steps):
            # Simulate success/failure of each step
            success = random.random() > 0.3  # 70% success rate
            
            result = {
                "step": i + 1,
                "description": step,
                "success": success,
                "details": f"{'Successful' if success else 'Failed'} execution of step {i+1}"
            }
            
            results.append(result)
            
            # If a critical step fails, the attack stops
            if not success and random.random() > 0.5:
                break
        
        # Update scenario with results
        scenario["simulation_results"] = results
        scenario["status"] = "simulated"
        scenario["overall_success"] = any([r["success"] for r in results])
        
        # Add to history
        self.simulation_history.append(scenario)
        
        return scenario
    
    def analyze_vulnerability(self, scenario: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze vulnerabilities exposed in the scenario"""
        scenario = scenario or self.current_scenario
        if not scenario:
            raise ValueError("No scenario available for analysis")
        
        # Get detailed system information
        system_details = self._get_detailed_system_info(scenario["target"])
        
        # Use Claude to analyze the vulnerability
        analysis = self.claude_agent.analyze_vulnerability(scenario["scenario"], system_details)
        
        # Update scenario with analysis
        scenario["vulnerability_analysis"] = analysis
        scenario["status"] = "analyzed"
        
        return scenario
    
    def _get_detailed_system_info(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed system information for vulnerability analysis"""
        # In a real implementation, this would gather more detailed information
        # For the hackathon, we'll use simulated data
        systems = {}
        
        for system in target_info.get("systems", []):
            systems[system] = {
                "version": f"{random.randint(1, 10)}.{random.randint(0, 9)}",
                "patch_level": f"P{random.randint(1, 20)}",
                "configuration": random.choice(["default", "custom", "hardened"]),
                "known_vulnerabilities": random.randint(0, 5)
            }
        
        return {
            "detailed_systems": systems,
            "security_controls": {
                "firewall": random.choice([True, False]),
                "ids": random.choice([True, False]),
                "encryption": random.choice(["none", "partial", "full"]),
                "authentication": random.choice(["basic", "2fa", "mfa"])
            }
        }
    
    def save_results(self, filename: str = None) -> str:
        """Save simulation results to a file"""
        if not self.simulation_history:
            raise ValueError("No simulation results to save")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.json"
        
        filepath = os.path.join("data", "scenarios", filename)
        
        with open(filepath, "w") as f:
            json.dump(self.simulation_history, f, indent=2)
        
        return filepath
