# src/api/app.py
from flask import Flask, request, jsonify, send_from_directory
import os
import json
import sys
sys.path.append('../../')
from src.simulators.red_team_simulator import RedTeamSimulator
from src.models.claude_agent import ClaudeAgent
from src.analyzers.osint_collector import OSINTCollector

# Get project directory
project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

app = Flask(__name__, static_folder=os.path.join(project_dir, 'static'))

# Initialize components
claude_agent = ClaudeAgent()
simulator = RedTeamSimulator(claude_agent, project_dir=project_dir)
osint_collector = OSINTCollector(project_dir=project_dir)

# Store simulation results
simulation_results = []

@app.route('/api/targets', methods=['GET'])
def get_targets():
    """Get available targets from OSINT data"""
    target_type = request.args.get('type', 'all')
    
    if target_type == 'maritime':
        targets = osint_collector.collect_ais_data()
    elif target_type == 'infrastructure':
        targets = osint_collector.collect_infrastructure_data()
    else:
        maritime = osint_collector.collect_ais_data()
        infrastructure = osint_collector.collect_infrastructure_data()
        targets = {
            'maritime': maritime,
            'infrastructure': infrastructure
        }
    
    return jsonify(targets)

@app.route('/api/search', methods=['GET'])
def search_targets():
    """Search for targets in OSINT data"""
    query = request.args.get('query', '')
    target_type = request.args.get('type', 'all')
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    results = osint_collector.search_osint_data(query, target_type)
    return jsonify(results)

@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """Run a red team simulation"""
    data = request.json
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    complexity = data.get('complexity', 'medium')
    
    # Load target from OSINT
    target_info = simulator.load_target_from_osint(target_type, target_id)
    
    # Generate attack scenario
    scenario = simulator.generate_attack_scenario(target_info, complexity)
    
    # Simulate attack
    result = simulator.simulate_attack(scenario)
    
    # Analyze vulnerability
    analysis = simulator.analyze_vulnerability(result)
    
    # Store result
    simulation_results.append(analysis)
    
    return jsonify(analysis)

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Get analysis of simulation results"""
    if not simulation_results:
        return jsonify({'error': 'No simulation results available'}), 404
    
    analysis = analyzer.analyze_simulation_results(simulation_results)
    return jsonify(analysis)

@app.route('/api/visualizations', methods=['GET'])
def generate_visualizations():
    """Generate visualizations of simulation results"""
    if not simulation_results:
        return jsonify({'error': 'No simulation results available'}), 404
    
    analysis = analyzer.analyze_simulation_results(simulation_results)
    
    # Generate visualizations
    success_rates_path = visualizer.plot_success_rates(analysis)
    attack_vectors_path = visualizer.plot_attack_vectors(analysis)
    severity_path = visualizer.plot_vulnerability_severity(analysis)
    
    # Generate attack graph
    graph = analyzer.generate_attack_graph(simulation_results)
    graph_path = visualizer.plot_attack_graph(graph)
    
    # Create interactive dashboard
    visualizer.create_interactive_dashboard(analysis, simulation_results)
    
    return jsonify({
        'success_rates': success_rates_path,
        'attack_vectors': attack_vectors_path,
        'severity': severity_path,
        'attack_graph': graph_path,
        'dashboard': os.path.join(visualizer.output_dir, 'success_gauge.html')
    })

@app.route('/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve visualization files"""
    return send_from_directory(visualizer.output_dir, filename)

@app.route('/')
def index():
    """Serve the main application page"""
    # Use absolute path to the static directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    static_dir = os.path.join(project_root, 'static')
    return send_from_directory(static_dir, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
