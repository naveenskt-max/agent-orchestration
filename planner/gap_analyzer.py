
class GapAnalyzer:
    def analyze_gaps(self, plan: list, agents: list):
        # Mock implementation that hardcodes the gap for the executive_report_agent
        
        agent_names = [agent['name'] for agent in agents]
        
        if "executive_report_agent" not in agent_names:
            return {
                "at_step": 5,
                "description": "Cannot generate final executive report document...",
                "suggested_agent_card": {
                    "name": "executive_report_agent",
                    "description": "Generates professional executive reports...",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "sales_data": {"type": "object"},
                            "news_analysis": {"type": "object"},
                            "visualizations": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["sales_data", "news_analysis", "visualizations"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "report_url": {"type": "string"},
                            "format": {"type": "string"}
                        }
                    },
                    "implementation_hints": {
                        "suggested_libraries": ["reportlab", "python-docx"],
                        "complexity": "medium",
                        "estimated_effort": "3-5 days"
                    }
                }
            }
        return None

gap_analyzer = GapAnalyzer()
