# src/api/app.py
from flask import Flask, request, jsonify, send_from_directory
import os
import json
import sys
import time
sys.path.append('../../')
from src.simulators.red_team_simulator import RedTeamSimulator
from src.models.claude_agent import ClaudeAgent
from src.analyzers.osint_collector import OSINTCollector
from src.analyzers.vulnerability_analyzer import VulnerabilityAnalyzer
from src.analyzers.visualizer import Visualizer

# Get project directory
project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

app = Flask(__name__, static_folder=os.path.join(project_dir, 'static'))

# Initialize components
claude_agent = ClaudeAgent()
simulator = RedTeamSimulator(claude_agent, project_dir=project_dir)
osint_collector = OSINTCollector(project_dir=project_dir)
analyzer = VulnerabilityAnalyzer(claude_agent)
visualizer = Visualizer()

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
    
    target = data.get('target')
    complexity = data.get('complexity', 'medium')
    
    if not target:
        return jsonify({'error': 'Target information is required'}), 400
    
    try:
        # Target info is already provided by frontend
        target_info = target
        
        # Generate attack scenario
        scenario = simulator.generate_attack_scenario(target_info, complexity)
        
        # Simulate attack
        result = simulator.simulate_attack(scenario)
        
        # Analyze vulnerability
        analysis = simulator.analyze_vulnerability(result)
        
        # Store result
        simulation_results.append(analysis)
        
        # Add timestamp and target info to response
        analysis['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S.%f')
        analysis['target'] = target_info
        
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        return jsonify({
            'error': 'Error running simulation',
            'details': str(e)
        }), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Get analysis of simulation results"""
    if not simulation_results:
        return jsonify({'error': 'No simulation results available'}), 404
    
    analysis = analyzer.analyze_simulation_results(simulation_results)
    return jsonify(analysis)

@app.route('/api/analyze', methods=['GET'])
def analyze_results():
    """Analyze simulation results using Claude"""
    if not simulation_results:
        return jsonify({'error': 'No simulation results available'}), 404
        
    try:
        # Get analysis from Claude
        analysis = claude_agent.analyze_simulation_results(simulation_results)
        
        if "error" in analysis:
            return jsonify(analysis), 500
            
        return jsonify(analysis)
        
    except Exception as e:
        print(f"Error analyzing results: {str(e)}")
        return jsonify({
            'error': 'Error analyzing results',
            'details': str(e)
        }), 500

@app.route('/api/visualizations')
def generate_visualizations():
    """Generate visualizations of simulation results"""
    if not simulation_results:
        return jsonify({'error': 'No simulation results available'}), 404
    
    try:
        # Analyze simulation results
        analysis = analyzer.analyze_simulation_results(simulation_results)
        
        # Generate attack graph
        graph = analyzer.generate_attack_graph(simulation_results)
        
        # Generate visualizations
        success_rates_path = visualizer.plot_success_rates(analysis)
        attack_vectors_path = visualizer.plot_attack_vectors(analysis)
        severity_path = visualizer.plot_vulnerability_severity(analysis)
        graph_path = visualizer.plot_attack_graph(graph)
        dashboard_path = visualizer.create_interactive_dashboard(analysis, simulation_results)
        
        # Convert paths to URLs
        base_url = '/visualizations/'
        return jsonify({
            'success_rates': base_url + os.path.basename(success_rates_path) if success_rates_path else None,
            'attack_vectors': base_url + os.path.basename(attack_vectors_path) if attack_vectors_path else None,
            'severity': base_url + os.path.basename(severity_path) if severity_path else None,
            'attack_graph': base_url + os.path.basename(graph_path) if graph_path else None,
            'dashboard': base_url + os.path.basename(dashboard_path) if dashboard_path else None
        })
    except Exception as e:
        print(f"Error generating visualizations: {str(e)}")
        return jsonify({
            'error': 'Error generating visualizations',
            'details': str(e)
        }), 500

@app.route('/visualizations/<path:filename>')
def serve_visualization(filename):
    """Serve visualization files"""
    visualization_dir = os.path.join(project_dir, 'data', 'visualizations')
    if not os.path.exists(os.path.join(visualization_dir, filename)):
        return jsonify({'error': f'Visualization {filename} not found'}), 404
    return send_from_directory(visualization_dir, filename)

@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
