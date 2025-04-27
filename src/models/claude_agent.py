# src/models/claude_agent.py
import anthropic
import os
import json
from typing import Dict, List, Any

class ClaudeAgent:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def generate_attack_scenario(self, target_info: Dict[str, Any], complexity: str = "medium") -> Dict[str, Any]:
        """Generate a realistic attack scenario based on target information"""
        prompt = self._create_attack_scenario_prompt(target_info, complexity)
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
            system="You are an expert red team security analyst tasked with identifying realistic vulnerabilities in systems.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response into a structured scenario
        return self._parse_attack_scenario(response.content[0].text)
        
    def analyze_vulnerability(self, scenario: Dict[str, Any], system_details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a vulnerability and provide detailed explanation and recommendations"""
        prompt = self._create_vulnerability_analysis_prompt(scenario, system_details)
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.2,
            system="You are a cybersecurity expert analyzing vulnerabilities and providing actionable recommendations.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response into structured analysis
        return self._parse_vulnerability_analysis(response.content[0].text)
    
    def analyze_simulation_results(self, simulation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze simulation results using Claude to generate insights and recommendations"""
        if not simulation_results:
            return {"error": "No simulation results to analyze"}
            
        # Create a detailed prompt for analysis
        prompt = f"""You are a cybersecurity expert analyzing red team simulation results. Please provide a detailed analysis of the following simulation results, including:

1. Key Findings
2. Attack Pattern Analysis
3. Critical Vulnerabilities
4. Defense Recommendations
5. Risk Assessment

Here are the simulation results:
{json.dumps(simulation_results, indent=2)}

Please provide your analysis in a structured format."""

        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.7,
                system="You are an expert cybersecurity analyst specializing in red team assessments and vulnerability analysis.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = response.content[0].text
            
            # Parse the analysis into sections
            sections = {
                "key_findings": [],
                "attack_patterns": [],
                "critical_vulnerabilities": [],
                "recommendations": [],
                "risk_assessment": ""
            }
            
            # Simple parsing of the response into sections
            current_section = None
            for line in analysis.split('\n'):
                if "Key Findings" in line:
                    current_section = "key_findings"
                elif "Attack Pattern" in line:
                    current_section = "attack_patterns"
                elif "Critical Vulnerabilities" in line:
                    current_section = "critical_vulnerabilities"
                elif "Defense Recommendations" in line:
                    current_section = "recommendations"
                elif "Risk Assessment" in line:
                    current_section = "risk_assessment"
                elif current_section and line.strip():
                    if current_section == "risk_assessment":
                        sections[current_section] += line + "\n"
                    elif line.startswith("- "):
                        sections[current_section].append(line[2:])
                        
            return {
                "analysis": sections,
                "raw_analysis": analysis
            }
            
        except Exception as e:
            return {
                "error": f"Error analyzing results: {str(e)}"
            }
    
    def _create_attack_scenario_prompt(self, target_info: Dict[str, Any], complexity: str) -> str:
        # Detailed prompt engineering for realistic attack scenarios
        return f"""
        As a red team security expert, create a realistic attack scenario targeting the following system:
        
        Target Information:
        {self._format_dict(target_info)}
        
        Complexity level: {complexity}
        
        Your response should include:
        1. Attack vector and initial access method
        2. Step-by-step attack progression
        3. Potential impact if successful
        4. Indicators of compromise
        5. Required attacker resources and skills
        
        Format your response as a structured JSON object with these fields.
        """
    
    def _create_vulnerability_analysis_prompt(self, scenario: Dict[str, Any], system_details: Dict[str, Any]) -> str:
        # Prompt for detailed vulnerability analysis
        return f"""
        Analyze the following attack scenario against the specified system:
        
        Attack Scenario:
        {self._format_dict(scenario)}
        
        System Details:
        {self._format_dict(system_details)}
        
        Provide a detailed analysis including:
        1. Vulnerability assessment (severity, exploitability, impact)
        2. Technical explanation of how the vulnerability works
        3. Specific defensive measures to mitigate this vulnerability
        4. Long-term security improvements to prevent similar attacks
        5. Detection methods to identify this attack in progress
        
        Format your response as a structured JSON object with these fields.
        """
    
    def _format_dict(self, d: Dict[str, Any]) -> str:
        return "\n".join([f"- {k}: {v}" for k, v in d.items()])
    
    def _parse_attack_scenario(self, text: str) -> Dict[str, Any]:
        # Parse the Claude response into a structured scenario
        # In a real implementation, use regex or JSON parsing
        # This is a simplified placeholder
        return {
            "attack_vector": "Example attack vector",
            "steps": ["Step 1", "Step 2", "Step 3"],
            "impact": "Critical",
            "indicators": ["IOC 1", "IOC 2"],
            "attacker_profile": {"resources": "Medium", "skills": "Advanced"}
        }
    
    def _parse_vulnerability_analysis(self, text: str) -> Dict[str, Any]:
        # Parse the Claude response into structured analysis
        # In a real implementation, use regex or JSON parsing
        # This is a simplified placeholder
        return {
            "severity": "High",
            "explanation": "Technical explanation of vulnerability",
            "mitigations": ["Mitigation 1", "Mitigation 2"],
            "long_term_fixes": ["Fix 1", "Fix 2"],
            "detection_methods": ["Detection 1", "Detection 2"]
        }
