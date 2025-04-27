## key claude
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
## to do
Use the kaggle dataset and also implement the following:

Replace the simulated Claude responses with kaggle dataset
Implement real OSINT data collection
Create actual visualizations instead of placeholders
Add more sophisticated analysis algorithms

# AI-Powered Red Team Simulator

A sophisticated LLM-based autonomous adversarial agent that realistically simulates cyber and physical threats against national infrastructure to test and enhance resilience, providing explainable analysis and actionable insights to defenders.

## Overview

This project creates an AI-powered Red Team that can:
- Generate realistic attack scenarios based on target information
- Simulate multi-stage attacks against infrastructure
- Analyze vulnerabilities and provide detailed explanations
- Generate actionable recommendations for defenders
- Visualize attack patterns and success rates

## Features

- **Autonomous Attack Simulation**: Simulates sophisticated attacks without human guidance
- **OSINT Integration**: Leverages open-source intelligence for target information
- **Explainable Results**: Provides clear reports on vulnerabilities and attack paths
- **Actionable Insights**: Generates specific defensive measures
- **Interactive Visualizations**: Displays attack graphs and vulnerability metrics

## Sponsor Resources Used

- **Anthropic's Claude**: Powers the core simulation engine, generates realistic attack scenarios, and provides natural language explanations
- **Azure**: Used for computation and potential cloud deployment
- **Windsurf AI IDE**: Used for development

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables:
   - `ANTHROPIC_API_KEY`: Your Anthropic API key

## Usage

### Running the Demo

```bash
python main.py
