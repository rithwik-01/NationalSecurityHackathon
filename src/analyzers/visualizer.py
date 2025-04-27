import os
import json
from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
import folium
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

class Visualizer:
    def __init__(self, output_dir: str = None):
        """Initialize the visualizer with output directory"""
        if output_dir is None:
            # Default to data/visualizations in project root
            project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_dir = os.path.join(project_root, 'data', 'visualizations')
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir
        
        # Set style
        sns.set_style("darkgrid")
        plt.style.use('dark_background')
        
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
                'success': '#2ecc71',
                'fail': '#e74c3c'
            }
        }
    
    def _set_plot_style(self, fig):
        """Set consistent style for all plots"""
        fig.update_layout(
            template='plotly_white',
            font=dict(family='Arial, sans-serif'),
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            )
        )
        return fig

    def plot_success_rates(self, analysis_results: Dict[str, Any]) -> str:
        """Plot attack success rates"""
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = success_rate * 100,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 33], 'color': "lightgray"},
                    {'range': [33, 66], 'color': "gray"},
                    {'range': [66, 100], 'color': "darkgray"}
                ]
            },
            title = {'text': "Overall Attack Success Rate (%)"}
        ))
        
        self._set_plot_style(fig)
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'success_rates.html')
        fig.write_html(output_path)
        return output_path

    def plot_attack_vectors(self, analysis_results: Dict[str, Any]) -> str:
        """Plot attack vector distribution"""
        metrics = analysis_results.get("metrics", {})
        attack_vectors = metrics.get("attack_vectors", {})
        
        # Create sunburst chart
        fig = go.Figure(go.Sunburst(
            labels = [k for k,v in attack_vectors.items()],
            parents = ["" for _ in attack_vectors],
            values = [v for k,v in attack_vectors.items()],
        ))
        
        fig.update_layout(title_text="Attack Vector Distribution")
        self._set_plot_style(fig)
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'attack_vectors_sunburst.html')
        fig.write_html(output_path)
        return output_path

    def plot_vulnerability_severity(self, analysis_results: Dict[str, Any]) -> str:
        """Plot vulnerability severity distribution"""
        metrics = analysis_results.get("metrics", {})
        severity_distribution = metrics.get("severity_distribution", {})
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=list(severity_distribution.keys()),
            values=list(severity_distribution.values())
        )])
        
        fig.update_layout(title_text="Vulnerability Severity Distribution")
        self._set_plot_style(fig)
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'vulnerability_severity.html')
        fig.write_html(output_path)
        return output_path

    def plot_attack_graph(self, graph: nx.DiGraph) -> str:
        """Plot attack graph visualization"""
        
        # Create positions
        pos = nx.spring_layout(graph)
        
        # Create plotly figure
        edge_trace = go.Scatter(
            x=[], y=[], line=dict(width=0.5, color='#888'), 
            hoverinfo='none', mode='lines')
        
        for edge in graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += tuple([x0, x1, None])
            edge_trace['y'] += tuple([y0, y1, None])
            
        node_trace = go.Scatter(
            x=[], y=[], text=[], mode='markers+text',
            hoverinfo='text', textposition="top center",
            marker=dict(size=10, color='lightblue'))
            
        for node in graph.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])
            node_trace['text'] += tuple([node])
            
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=0,l=0,r=0,t=0)))
                           
        self._set_plot_style(fig)
        
        # Save plot
        output_path = os.path.join(self.output_dir, 'attack_graph.html')
        fig.write_html(output_path)
        return output_path

    def create_interactive_dashboard(self, analysis_results: Dict[str, Any], simulation_results: List[Dict[str, Any]]) -> str:
        """Create an interactive dashboard with all visualizations"""
        # Create subplots with correct specifications
        fig = make_subplots(
            rows=2, cols=2,
            specs=[
                [{"type": "indicator"}, {"type": "domain"}],
                [{"type": "domain"}, {"type": "xy"}]
            ],
            subplot_titles=(
                "Success Rate", 
                "Attack Vectors",
                "Vulnerability Severity",
                "Attack Timeline"
            )
        )
        
        # Add success rate gauge
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=success_rate * 100,
                title={'text': "Success Rate (%)"},
                gauge={'axis': {'range': [0, 100]}}
            ),
            row=1, col=1
        )
        
        # Add attack vector sunburst
        attack_vectors = metrics.get("attack_vectors", {})
        if attack_vectors:
            fig.add_trace(
                go.Sunburst(
                    labels=[k for k,v in attack_vectors.items()],
                    parents=["" for _ in attack_vectors],
                    values=[v for k,v in attack_vectors.items()]
                ),
                row=1, col=2
            )
        
        # Add severity pie chart
        severity_distribution = metrics.get("severity_distribution", {})
        if any(severity_distribution.values()):
            fig.add_trace(
                go.Pie(
                    labels=list(severity_distribution.keys()),
                    values=list(severity_distribution.values())
                ),
                row=2, col=1
            )
        
        # Add timeline
        timestamps = [r.get('timestamp', '') for r in simulation_results]
        success_values = [1 if r.get('overall_success') else 0 for r in simulation_results]
        
        if timestamps and success_values:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=success_values,
                    mode='lines+markers',
                    name='Attack Success'
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="Red Team Simulation Dashboard",
            showlegend=True
        )
        self._set_plot_style(fig)
        
        # Save dashboard
        output_path = os.path.join(self.output_dir, 'dashboard.html')
        fig.write_html(output_path)
        return output_path

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
        marker_cluster = folium.plugins.MarkerCluster().add_to(m)
        
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
        folium.plugins.HeatMap(heat_data).add_to(m)
        
        if save:
            filepath = os.path.join(self.output_dir, "maritime_targets_map.html")
            m.save(filepath)
            return filepath
        
        return None
