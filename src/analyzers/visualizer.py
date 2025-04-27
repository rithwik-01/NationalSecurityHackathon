# src/analyzers/visualizer.py
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import os

class Visualizer:
    def __init__(self, output_dir: str = "data/visualizations"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams["figure.figsize"] = (12, 8)
    
    def plot_success_rates(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot success rates of attack simulations"""
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        
        fig, ax = plt.subplots()
        ax.bar(["Success Rate"], [success_rate], color="crimson")
        ax.bar(["Defense Rate"], [1 - success_rate], color="forestgreen")
        
        ax.set_ylim(0, 1)
        ax.set_ylabel("Rate")
        ax.set_title("Attack Success vs. Defense Success Rate")
        
        for i, v in enumerate([success_rate, 1 - success_rate]):
            ax.text(i, v/2, f"{v:.1%}", ha="center", color="white", fontweight="bold")
        
        if save:
            filepath = os.path.join(self.output_dir, "success_rates.png")
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()
            return filepath
        
        return None
    
    def plot_attack_vectors(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot distribution of attack vectors"""
        metrics = analysis_results.get("metrics", {})
        attack_vectors = metrics.get("attack_vectors", {})
        
        if not attack_vectors:
            return None
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame({"Attack Vector": list(attack_vectors.keys()), 
                          "Count": list(attack_vectors.values())})
        df = df.sort_values("Count", ascending=False)
        
        fig, ax = plt.subplots()
        sns.barplot(x="Count", y="Attack Vector", data=df, palette="viridis", ax=ax)
        
        ax.set_title("Distribution of Attack Vectors")
        ax.set_xlabel("Number of Simulations")
        
        if save:
            filepath = os.path.join(self.output_dir, "attack_vectors.png")
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()
            return filepath
        
        return None
    
    def plot_vulnerability_severity(self, analysis_results: Dict[str, Any], save: bool = True) -> str:
        """Plot distribution of vulnerability severity"""
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
        
        # Create color map
        colors = {"Low": "green", "Medium": "gold", "High": "orange", "Critical": "red"}
        df["Color"] = df["Severity"].map(colors)
        
        fig, ax = plt.subplots()
        bars = ax.bar(df["Severity"], df["Count"], color=df["Color"])
        
        ax.set_title("Distribution of Vulnerability Severity")
        ax.set_xlabel("Severity Level")
        ax.set_ylabel("Number of Vulnerabilities")
        
        # Add count labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f"{height:.0f}", ha="center", va="bottom")
        
        if save:
            filepath = os.path.join(self.output_dir, "vulnerability_severity.png")
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()
            return filepath
        
        return None
    
    def plot_attack_graph(self, graph: nx.DiGraph, save: bool = True) -> str:
        """Plot attack graph visualization"""
        plt.figure(figsize=(15, 10))
        
        # Define node colors based on type and success
        node_colors = []
        for node in graph.nodes():
            node_type = graph.nodes[node].get("type", "")
            success = graph.nodes[node].get("success", None)
            
            if node_type == "target":
                node_colors.append("lightblue")
            elif node_type == "step":
                node_colors.append("green" if success else "red")
            elif node_type == "outcome":
                node_colors.append("darkred" if success else "darkgreen")
            else:
                node_colors.append("gray")
        
        # Create layout
        pos = nx.spring_layout(graph, seed=42)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=700, alpha=0.8)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, width=1.0, alpha=0.5, edge_color="gray", 
                              arrowsize=20, connectionstyle="arc3,rad=0.1")
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=8, font_family="sans-serif")
        
        plt.title("Attack Graph Visualization")
        plt.axis("off")
        
        if save:
            filepath = os.path.join(self.output_dir, "attack_graph.png")
            plt.savefig(filepath, dpi=300, bbox_inches="tight")
            plt.close()
            return filepath
        
        return None
    
    def create_interactive_dashboard(self, analysis_results: Dict[str, Any], simulation_results: List[Dict[str, Any]]) -> None:
        """Create an interactive Plotly dashboard for the results"""
        # This would create a Dash application in a real implementation
        # For the hackathon, we'll just create some Plotly figures
        
        # Success rate gauge
        metrics = analysis_results.get("metrics", {})
        success_rate = metrics.get("success_rate", 0)
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = success_rate * 100,
            title = {'text': "Attack Success Rate"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "crimson"},
                'steps': [
                    {'range': [0, 33], 'color': "lightgreen"},
                    {'range': [33, 66], 'color': "gold"},
                    {'range': [66, 100], 'color': "salmon"}
                ]
            }
        ))
        
        filepath = os.path.join(self.output_dir, "success_gauge.html")
        fig.write_html(filepath)
        
        # Create other interactive visualizations as needed
