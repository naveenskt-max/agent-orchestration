
class Decomposition:
    def get_decompositions(self, goal: str, agents: list):
        # Mock implementation returning a hardcoded decomposition
        # In a real implementation, this would use an LLM to generate multiple decompositions
        
        achievable_plan = [
            {
                "step": 1,
                "agent_name": "sales_data_agent",
                "task": "Fetch sales records for the last 7 days",
                "confidence": "high"
            },
            {
                "step": 2,
                "agent_name": "news_search_agent",
                "task": "Find top 10 competitor news articles",
                "confidence": "high"
            },
            {
                "step": 3,
                "agent_name": "text_analysis_agent",
                "task": "Extract themes from news articles",
                "confidence": "high"
            },
            {
                "step": 4,
                "agent_name": "data_visualization_agent",
                "task": "Create sales trend chart",
                "confidence": "medium"
            }
        ]
        
        return [achievable_plan]

decomposition = Decomposition()
