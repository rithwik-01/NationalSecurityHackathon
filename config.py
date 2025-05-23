# config.py
import os

# API Keys (to be set as environment variables)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "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")

# OSINT Resources
OSINT_RESOURCES = {
    "ais_shipping": "https://www.aishub.net",
    "historical_ais": "https://developer.barentswatch.no/docs/AIS/historic-ais-api/",
    "vessel_traffic": "https://hub.marinecadastre.gov/pages/vesseltraffic",
    "flight_tracking": "https://www.flightradar24.com"
}

# Simulation parameters
SIMULATION_PARAMS = {
    "max_steps": 10,
    "threat_levels": ["low", "medium", "high", "critical"],
    "target_systems": ["network", "physical", "personnel", "supply_chain"]
}
