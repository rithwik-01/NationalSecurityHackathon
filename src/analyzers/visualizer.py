import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import os
import folium
from folium.plugins import MarkerCluster, HeatMap, TimestampedGeoJson
import json
import datetime

class Visualizer:
    def __init__(self, output_dir: str = "data/visualizations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set_style("darkgrid")
        plt.rcParams["figure.figsize"] = (14, 8)
        
        # Enhanced color schemes
        self.color_schemes = {
            'attack_vectors': px.colors.qualitative.Bold,
            'severity': {
                "Low": "#66c2a5",
                "Medium": "#fc8d62", 
                "High": "#e78ac3", 
                "Critical": "#e31a1c"
            },
            'success_fail': {
                'success': '#ff4d4d',  # Red for attacks (indicating danger)
                'fail': '#4dff4d'      # Green for successful defense
            }
        }
    
    def plot_success_rates(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot success rates of attack simulations with enhanced visualization"""
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        
        # Create figure with Plotly for better interactivity
        fig = go.Figure()
        
        # Add attack success rate
        fig.add_trace(go.Bar(
            x=["Attack Success Rate"],
            y=[success_rate * 100],
            marker_color=self.color_schemes['success_fail']['success'],
            text=[f"{success_rate:.1%}"],
            textposition="inside",
            name="Attack Success"
        ))
        
        # Add defense success rate
        fig.add_trace(go.Bar(
            x=["Defense Success Rate"],
            y=[(1 - success_rate) * 100],
            marker_color=self.color_schemes['success_fail']['fail'],
            text=[f"{1-success_rate:.1%}"],
            textposition="inside",
            name="Defense Success"
        ))
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Attack vs Defense Success Rate',
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            xaxis_title="",
            yaxis_title="Percentage (%)",
            yaxis_range=[0, 100],
            template="plotly_dark",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        if save:
            # Save as HTML for interactivity
            html_filepath = os.path.join(self.output_dir, "success_rates.html")
            fig.write_html(html_filepath)
            
            # Also save as image for embedding
            img_filepath = os.path.join(self.output_dir, "success_rates.png")
            fig.write_image(img_filepath)
            return html_filepath
        
        return None
    
    def plot_attack_vectors(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot distribution of attack vectors with enhanced visualization"""
        metrics = analysis_results.get("metrics", {})
        attack_vectors = metrics.get("attack_vectors", {})
        
        if not attack_vectors:
            return None
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame({"Attack Vector": list(attack_vectors.keys()), 
                          "Count": list(attack_vectors.values())})
        df = df.sort_values("Count", ascending=False)
        
        # Create sunburst chart for hierarchical attack vectors
        # First, add a category column
        categories = []
        subcategories = []
        
        for vector in df["Attack Vector"]:
            if ":" in vector:
                cat, subcat = vector.split(":", 1)
                categories.append(cat.strip())
                subcategories.append(subcat.strip())
            else:
                categories.append("Other")
                subcategories.append(vector)
        
        df["Category"] = categories
        df["Subcategory"] = subcategories
        
        # Create sunburst plot
        fig1 = px.sunburst(
            df, 
            path=['Category', 'Subcategory'], 
            values='Count',
            color_discrete_sequence=self.color_schemes['attack_vectors'],
            title="Attack Vectors Distribution (Hierarchical)"
        )
        
        # Also create a horizontal bar chart for quick reference
        fig2 = px.bar(
            df, 
            y="Attack Vector", 
            x="Count", 
            color="Category",
            title="Top Attack Vectors",
            orientation='h',
            color_discrete_sequence=self.color_schemes['attack_vectors']
        )
        
        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
        
        if save:
            # Save both visualizations
            sunburst_filepath = os.path.join(self.output_dir, "attack_vectors_sunburst.html")
            bar_filepath = os.path.join(self.output_dir, "attack_vectors_bar.html")
            
            fig1.write_html(sunburst_filepath)
            fig2.write_html(bar_filepath)
            
            # Save images for embedding
            fig1.write_image(os.path.join(self.output_dir, "attack_vectors_sunburst.png"))
            fig2.write_image(os.path.join(self.output_dir, "attack_vectors_bar.png"))
            
            return sunburst_filepath
        
        return None
    
    def plot_vulnerability_severity(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot distribution of vulnerability severity with enhanced visualization"""
        metrics = analysis_results.get("metrics", {})
        severity_distribution = metrics.get("severity_distribution", {})
        
        if not severity_distribution:
            return None
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame({"Severity": list(severity_distribution.keys()), 
                          "Count": list(severity_distribution.values())})
        
        # Order severity levels
        severity_order = ["Low", "Medium", "High", "Critical"]
        df["Severity"] = pd.Categorical(df["Severity"], categories=severity_order, ordered=True)
        df = df.sort_values("Severity")
        
        # Create a more informative visualization
        # Bullet chart/gauge chart to show severity
        fig1 = go.Figure()
        
        colors = [self.color_schemes['severity'][s] for s in df['Severity']]
        
        # Create a donut chart
        fig1.add_trace(go.Pie(
            labels=df['Severity'],
            values=df['Count'],
            hole=.4,
            marker_colors=colors,
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        
        fig1.update_layout(
            title_text='Vulnerability Severity Distribution',
            annotations=[dict(text='Severity<br>Levels', x=0.5, y=0.5, font_size=15, showarrow=False)]
        )
        
        # Create radar chart to show vulnerability categories
        # If we have category data in the metrics
        vulnerability_categories = metrics.get("vulnerability_categories", {})
        
        if vulnerability_categories:
            df2 = pd.DataFrame(vulnerability_categories)
            
            fig2 = px.line_polar(
                df2, 
                r='score', 
                theta='category', 
                line_close=True,
                title="Vulnerability Score by Category",
                color_discrete_sequence=['#ff5050']
            )
            
            fig2.update_traces(fill='toself')
            
            if save:
                radar_filepath = os.path.join(self.output_dir, "vulnerability_categories.html")
                fig2.write_html(radar_filepath)
                fig2.write_image(os.path.join(self.output_dir, "vulnerability_categories.png"))
        
        if save:
            filepath = os.path.join(self.output_dir, "vulnerability_severity.html")
            fig1.write_html(filepath)
            fig1.write_image(os.path.join(self.output_dir, "vulnerability_severity.png"))
            return filepath
        
        return None
    
    def plot_map_of_targets(self, targets: List[Dict[str, Any]], save: bool = True) -> str:
        """Create an interactive map with all maritime targets"""
        # Check if we have targets with coordinates
        valid_targets = [t for t in targets if "position" in t and 
                         "latitude" in t["position"] and 
                         "longitude" in t["position"]]
        
        if not valid_targets:
            return None
        
        # Create base map centered at the average position
        lats = [t["position"]["latitude"] for t in valid_targets]
        lons = [t["position"]["longitude"] for t in valid_targets]
        center_lat = sum(lats) / len(lats)
        center_lon = sum(lons) / len(lons)
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=5)
        
        # Create cluster for vessels
        marker_cluster = MarkerCluster().add_to(m)
        
        # Add markers for each target
        for target in valid_targets:
            pos = target["position"]
            name = target.get("vessel_name", "Unknown Vessel")
            vessel_type = target.get("vessel_type", "Unknown")
            mmsi = target.get("mmsi", "Unknown")
            security = target.get("security_level", "Unknown")
            
            # Determine icon and color based on vessel type and security level
            icon_map = {
                "Tanker": "ship", "Cargo": "ship", "Container Ship": "ship",
                "Passenger": "ship", "Fishing": "ship", "Tug": "ship",
                "Military": "flag", "Law Enforcement": "flag",
                "Unknown": "question-sign"
            }
            
            color_map = {
                "high": "red", "medium": "orange", "low": "green", "Unknown": "blue"
            }
            
            # Default icon if type not in map
            icon = icon_map.get(vessel_type, "ship")
            color = color_map.get(security, "blue")
            
            # Create popup with vessel information
            popup_html = f"""
            <h4>{name}</h4>
            <b>MMSI:</b> {mmsi}<br>
            <b>Type:</b> {vessel_type}<br>
            <b>Security Level:</b> {security}<br>
            <b>Position:</b> {pos['latitude']:.4f}, {pos['longitude']:.4f}<br>
            """
            
            if "course" in target:
                popup_html += f"<b>Course:</b> {target['course']}°<br>"
            if "speed" in target:
                popup_html += f"<b>Speed:</b> {target['speed']} knots<br>"
            if "destination" in target:
                popup_html += f"<b>Destination:</b> {target['destination']}<br>"
            
            popup = folium.Popup(popup_html, max_width=300)
            
            # Add marker
            folium.Marker(
                location=[pos["latitude"], pos["longitude"]],
                popup=popup,
                tooltip=name,
                icon=folium.Icon(color=color, icon=icon, prefix='glyphicon')
            ).add_to(marker_cluster)
            
        # Add heatmap layer
        heat_data = [[t["position"]["latitude"], t["position"]["longitude"]] for t in valid_targets]
        HeatMap(heat_data).add_to(m)
        
        if save:
            filepath = os.path.join(self.output_dir, "maritime_targets_map.html")
            m.save(filepath)
            return filepath
        
        return None
    
    def plot_attack_graph(self, graph: nx.DiGraph, save: bool = True) -> str:
        """Plot attack graph visualization with enhanced styling"""
        # Create attack path visualization using Plotly for interactivity
        pos = nx.spring_layout(graph, seed=42)
        
        # Extract node positions
        node_x = []
        node_y = []
        for node in graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
        # Create node trace
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                reversescale=True,
                color=[],
                size=20,
                colorbar=dict(
                    thickness=15,
                    title='Node Risk Score',
                    xanchor='left',
                    title_side='right'  # Changed from titleside to title_side
                ),
                line_width=2
            )
        )
        
        # Assign node colors and create hover text
        node_text = []
        node_colors = []
        
        for node in graph.nodes():
            node_type = graph.nodes[node].get("type", "unknown")
            node_success = graph.nodes[node].get("success", False)
            node_risk = graph.nodes[node].get("risk_score", 0.5)
            
            # Create descriptive hover text
            hover_text = f"Node: {node}<br>"
            hover_text += f"Type: {node_type}<br>"
            
            if node_type == "step":
                status = "Successful" if node_success else "Failed"
                hover_text += f"Status: {status}<br>"
                hover_text += f"Risk Score: {node_risk:.2f}"
            
            node_text.append(hover_text)
            node_colors.append(node_risk)
            
        node_trace.marker.color = node_colors
        node_trace.text = node_text
        
        # Create edge traces with arrows
        edge_traces = []
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            # Calculate the points for the arrow
            arrow_length = 0.03
            dx = x1 - x0
            dy = y1 - y0
            length = (dx**2 + dy**2)**0.5
            dx = dx / length
            dy = dy / length
            
            # End the line slightly before the target node
            x_end = x1 - dx * arrow_length * 2
            y_end = y1 - dy * arrow_length * 2
            
            # Main edge line
            edge_trace = go.Scatter(
                x=[x0, x_end],
                y=[y0, y_end],
                line=dict(width=1, color='#888'),
                hoverinfo='none',
                mode='lines'
            )
            
            # Arrow head
            arrow_x = x_end
            arrow_y = y_end
            
            # Get edge metadata
            edge_data = graph.get_edge_data(edge[0], edge[1])
            technique = edge_data.get("technique", "")
            probability = edge_data.get("probability", 0)
            
            # Create hover text for edge
            hover_text = f"From: {edge[0]}<br>To: {edge[1]}"
            if technique:
                hover_text += f"<br>Technique: {technique}"
            if probability:
                hover_text += f"<br>Probability: {probability:.2f}"
            
            # Add arrow annotation
            arrow_trace = go.Scatter(
                x=[arrow_x, x1],
                y=[arrow_y, y1],
                line=dict(width=2, color='#888'),
                hoverinfo='text',
                text=hover_text,
                mode='lines+markers',
                marker=dict(
                    symbol='triangle-right',
                    size=8,
                    color='#888',
                    angle=np.arctan2(dy, dx) * 180 / np.pi
                )
            )
            
            edge_traces.append(edge_trace)
            edge_traces.append(arrow_trace)
            
        # Create the figure
        fig = go.Figure(data=edge_traces + [node_trace],
                     layout=go.Layout(
                        title='Interactive Attack Graph Visualization',
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        template='plotly_dark'
                    )
                )
        
        # Add node labels as annotations
        for node, (x, y) in pos.items():
            node_type = graph.nodes[node].get("type", "")
            node_color = "white"
            
            # Adjust label color based on node type
            if node_type == "target":
                node_color = "lightblue"
            elif node_type == "outcome":
                node_color = "salmon"
                
            fig.add_annotation(
                x=x,
                y=y,
                text=str(node),
                showarrow=False,
                font=dict(color=node_color, size=10),
                xanchor="center",
                yanchor="bottom",
                yshift=15
            )
        
        if save:
            filepath = os.path.join(self.output_dir, "attack_graph.html")
            fig.write_html(filepath)
            
            # Also save a static image
            img_filepath = os.path.join(self.output_dir, "attack_graph.png")
            fig.write_image(img_filepath)
            
            return filepath
        
        return None
    
    def create_interactive_dashboard(self, analysis_results: Dict[str, Any], simulation_results: List[Dict[str, Any]]) -> None:
        """Create an interactive Plotly dashboard integrating all visualizations"""
        # Create a comprehensive HTML dashboard that combines all visualizations
        dashboard_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Red Team Simulator Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #1e1e1e; color: #f0f0f0; }
                .container { width: 95%; margin: 0 auto; padding: 20px; }
                .header { background-color: #990000; color: white; padding: 20px; text-align: center; margin-bottom: 20px; }
                .dashboard-row { display: flex; flex-wrap: wrap; margin: -10px; }
                .dashboard-card { flex: 1; min-width: 300px; margin: 10px; background-color: #2d2d2d; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.3); overflow: hidden; }
                .card-header { background-color: #404040; padding: 15px; font-weight: bold; }
                .card-body { padding: 15px; }
                .iframe-container { position: relative; overflow: hidden; padding-top: 56.25%; }
                .iframe-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
                .metric-box { text-align: center; padding: 20px; }
                .metric-value { font-size: 24px; font-weight: bold; margin: 10px 0; }
                .metric-label { font-size: 14px; color: #aaa; }
                .status-high { color: #ff4d4d; }
                .status-medium { color: #ffcc00; }
                .status-low { color: #33cc33; }
                .summary-section { margin-bottom: 20px; }
                h2, h3 { color: #ddd; }
                ul { padding-left: 20px; }
                li { margin-bottom: 5px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #444; }
                th { background-color: #333; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Red Team Simulator - Attack Analysis Dashboard</h1>
                <p>Comprehensive visualization of simulation results and vulnerability analysis</p>
            </div>
            <div class="container">
                <div class="dashboard-row">
                    <!-- Key Metrics Section -->
                    <div class="dashboard-card">
                        <div class="card-header">Key Attack Metrics</div>
                        <div class="card-body">
                            <div class="metric-box">
                                <div class="metric-label">Overall Attack Success Rate</div>
                                <div class="metric-value status-high">{success_rate:.1%}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Critical Vulnerabilities</div>
                                <div class="metric-value status-high">{critical_vulns}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Average Time to Breach</div>
                                <div class="metric-value">{avg_time_to_breach}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Overall Security Posture</div>
                                <div class="metric-value status-{security_posture_class}">{security_posture}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Success Rate Visualization -->
                    <div class="dashboard-card">
                        <div class="card-header">Attack Success vs Defense Rate</div>
                        <div class="card-body">
                            <div class="iframe-container">
                                <iframe src="success_rates.html"></iframe>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-row">
                    <!-- Attack Vectors Visualization -->
                    <div class="dashboard-card">
                        <div class="card-header">Attack Vectors Distribution</div>
                        <div class="card-body">
                            <div class="iframe-container">
                                <iframe src="attack_vectors_sunburst.html"></iframe>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Vulnerability Severity -->
                    <div class="dashboard-card">
                        <div class="card-header">Vulnerability Severity</div>
                        <div class="card-body">
                            <div class="iframe-container">
                                <iframe src="vulnerability_severity.html"></iframe>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-row">
                    <!-- Map View -->
                    <div class="dashboard-card">
                        <div class="card-header">Target Map</div>
                        <div class="card-body">
                            <div class="iframe-container">
                                <iframe src="maritime_targets_map.html"></iframe>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Attack Graph -->
                    <div class="dashboard-card">
                        <div class="card-header">Attack Graph Analysis</div>
                        <div class="card-body">
                            <div class="iframe-container">
                                <iframe src="attack_graph.html"></iframe>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-row">
                    <!-- Summary and Recommendations -->
                    <div class="dashboard-card">
                        <div class="card-header">Attack Summary & Recommendations</div>
                        <div class="card-body">
                            <div class="summary-section">
                                <h3>Attack Summary</h3>
                                <p>{attack_summary}</p>
                            </div>
                            <div class="summary-section">
                                <h3>Top Vulnerabilities</h3>
                                <ul>
                                    {vulnerability_list}
                                </ul>
                            </div>
                            <div class="summary-section">
                                <h3>Recommended Mitigations</h3>
                                <ul>
                                    {mitigation_list}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <script>
                // You could add JavaScript for dashboard interactivity here
            </script>
        </body>
        </html>
        """
        
        # Extract metrics needed for the dashboard
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        
        # Extract severity counts
        severity = metrics.get("severity_distribution", {})
        critical_vulns = severity.get("Critical", 0)
        
        # Determine security posture class
        if success_rate > 0.7:
            security_posture = "Poor"
            security_posture_class = "high"
        elif success_rate > 0.3:
            security_posture = "Moderate"
            security_posture_class = "medium"
        else:
            security_posture = "Good"
            security_posture_class = "low"
        
        # Average time to breach (this would come from actual simulation data)
        avg_time_to_breach = metrics.get("average_time_to_breach", "4h 23m")
        
        # Build vulnerability and mitigation lists
        vulnerabilities = analysis_results.get("vulnerabilities", [])
        vulnerability_list = ""
        for vuln in vulnerabilities[:5]:  # Top 5 vulnerabilities
            severity_class = "high" if vuln.get("severity") == "Critical" else "medium"
            vulnerability_list += f'<li><span class="status-{severity_class}">[{vuln.get("severity", "Unknown")}]</span> {vuln.get("description", "Unknown vulnerability")}</li>'
        
        mitigations = analysis_results.get("mitigations", [])
        mitigation_list = ""
        for mitigation in mitigations[:5]:  # Top 5 mitigations
            mitigation_list += f'<li>{mitigation.get("description", "Unknown mitigation")}</li>'
        
        # Attack summary
        attack_summary = analysis_results.get("summary", "No attack summary available.")
        
        # Format the HTML with actual data
        dashboard_html = dashboard_html.format(
            success_rate=success_rate,
            critical_vulns=critical_vulns,
            avg_time_to_breach=avg_time_to_breach,
            security_posture=security_posture,
            security_posture_class=security_posture_class,
            vulnerability_list=vulnerability_list,
            mitigation_list=mitigation_list,
            attack_summary=attack_summary
        )
        
        # Save the dashboard
        filepath = os.path.join(self.output_dir, "dashboard.html")
        with open(filepath, 'w') as f:
            f.write(dashboard_html)
        
        print(f"Interactive dashboard created at {filepath}")
