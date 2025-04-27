# main.py
import os
from src.api.app import app
from src.simulators.red_team_simulator import RedTeamSimulator
from src.analyzers.osint_collector import OSINTCollector
from src.analyzers.vulnerability_analyzer import VulnerabilityAnalyzer
from src.analyzers.visualizer import Visualizer
from src.models.claude_agent import ClaudeAgent

def setup_environment():
    """Set up the environment for the application"""
    # Create necessary directories
    os.makedirs("data/osint", exist_ok=True)
    os.makedirs("data/scenarios", exist_ok=True)
    os.makedirs("data/visualizations", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # Copy static files if they don't exist
    if not os.path.exists("static/index.html"):
        with open("static/index.html", "w") as f:
            # Copy the HTML content here
            pass

def run_demo():
    """Run a demonstration of the simulator"""
    print("Running Red Team Simulator Demo...")
    
    # Initialize components
    claude_agent = ClaudeAgent()
    simulator = RedTeamSimulator(claude_agent)
    osint_collector = OSINTCollector()
    analyzer = VulnerabilityAnalyzer(claude_agent)
    visualizer = Visualizer()
    
    # Collect some OSINT data
    print("Collecting OSINT data...")
    maritime_targets = osint_collector.collect_ais_data(limit=5)
    infrastructure_targets = osint_collector.collect_infrastructure_data(limit=5)
    
    # Run simulations
    print("Running simulations...")
    simulation_results = []
    
    # Maritime target simulation
    maritime_target = maritime_targets[0]
    print(f"Simulating attack on maritime target: {maritime_target.get('vessel_name', 'Unknown')}")
    scenario = simulator.generate_attack_scenario(maritime_target, "medium")
    result = simulator.simulate_attack(scenario)
    analysis = simulator.analyze_vulnerability(result)
    simulation_results.append(analysis)
    
    # Infrastructure target simulation
    infrastructure_target = infrastructure_targets[0]
    print(f"Simulating attack on infrastructure target: {infrastructure_target.get('name', 'Unknown')}")
    scenario = simulator.generate_attack_scenario(infrastructure_target, "high")
    result = simulator.simulate_attack(scenario)
    analysis = simulator.analyze_vulnerability(result)
    simulation_results.append(analysis)
    
    # Analyze results
    print("Analyzing simulation results...")
    analysis_results = analyzer.analyze_simulation_results(simulation_results)
    
    # Generate visualizations
    print("Generating visualizations...")
    visualizer.plot_success_rates(analysis_results)
    visualizer.plot_attack_vectors(analysis_results)
    visualizer.plot_vulnerability_severity(analysis_results)
    
    # Generate attack graph
    graph = analyzer.generate_attack_graph(simulation_results)
    visualizer.plot_attack_graph(graph)
    
    # Create interactive dashboard
    visualizer.create_interactive_dashboard(analysis_results, simulation_results)
    
    print("Demo complete! Visualizations saved to data/visualizations/")
    print("Start the web application with 'python main.py server' to view the full interface")

def run_server():
    """Run the web application server"""
    print("Starting Red Team Simulator web application...")
    app.run(debug=True, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    import sys
    
    setup_environment()
    
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server()
    else:
        run_demo()
