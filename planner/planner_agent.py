"""
Planner Agent - Uses Google ADK to intelligently decompose goals into agent workflows
"""
import httpx
import json
import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai.types import Tool, FunctionDeclaration, GenerateContentConfig

class PlannerAgent:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Planner Agent with Google ADK"""
        # Priority 1: Environment variable (production)
        api_key = os.getenv('GOOGLE_API_KEY')
        
        # Priority 2: Provided parameter (for testing)
        if not api_key and api_key is not None:
            api_key = api_key
        
        # Priority 3: Error if no key found
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable not set. "
                "Please set it in your environment or .env file. "
                "Get your key from: https://makersuite.google.com/app/apikey"
            )
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = os.getenv('GOOGLE_MODEL', 'gemini-2.0-flash-exp')
        self.registry_url = os.getenv('REGISTRY_URL', 'http://registry:8000')  # Use Docker service name
    
    async def get_available_agents(self) -> List[Dict[str, Any]]:
        """Fetch available agents from registry"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.registry_url}/list_agents")
            response.raise_for_status()
            return response.json()
    
    def convert_agents_to_tools(self, agents: List[Dict[str, Any]]) -> List[Tool]:
        """Convert Agent Cards to Google ADK Tools"""
        tools = []
        
        for agent in agents:
            # Extract schema from Agent Card
            input_schema = agent.get('inputSchema', {})
            
            # Create function declaration for this agent
            function = FunctionDeclaration(
                name=agent['name'],
                description=agent['description'],
                parameters=input_schema  # Use MCP-compatible schema directly
            )
            
            # Create tool
            tool = Tool(function_declarations=[function])
            tools.append(tool)
        
        return tools
    
    async def generate_plan(self, goal: str) -> Dict[str, Any]:
        """
        Generate a workflow plan using Google ADK
        
        Steps:
        1. Fetch available agents from registry
        2. Convert agents to ADK tools
        3. Use Gemini with tools to generate multiple decomposition strategies
        4. Score and select best decomposition
        5. Detect gaps if coverage < 100%
        """
        
        # Step 1: Get available agents
        agents = await self.get_available_agents()
        
        if not agents:
            return {
                "status": "error",
                "message": "No agents available in registry"
            }
        
        # Step 2: Convert to tools
        tools = self.convert_agents_to_tools(agents)
        
        # Step 3: Create system instruction for planning
        system_instruction = self._create_system_instruction(agents)
        
        # Step 4: Use Gemini to generate decomposition strategies
        decompositions = await self._generate_decompositions(
            goal, 
            agents, 
            tools, 
            system_instruction
        )
        
        # Step 5: Score decompositions
        best_decomposition = self._score_and_select_best(decompositions, goal)
        
        # Step 6: Analyze for gaps
        gap_analysis = await self._analyze_gaps(best_decomposition, goal, agents)
        
        # Step 7: Format response
        coverage = best_decomposition['coverage']
        
        if coverage >= 1.0:
            return {
                "status": "complete",
                "coverage": coverage,
                "plan": best_decomposition['steps'],
                "alternative_approaches_tried": len(decompositions),
                "scoring": best_decomposition.get('score_breakdown', {})
            }
        else:
            return {
                "status": "partial",
                "coverage": coverage,
                "achievable_plan": best_decomposition['steps'],
                "gaps": gap_analysis['gaps'],
                "alternative_approaches_tried": len(decompositions),
                "recommendation": gap_analysis['recommendation']
            }
    
    def _create_system_instruction(self, agents: List[Dict[str, Any]]) -> str:
        """Create system instruction for the LLM"""
        agent_list = "\n".join([
            f"- {a['name']}: {a['description']}" 
            for a in agents
        ])
        
        return f"""You are an expert workflow architect for an agent orchestration system.

Your job is to decompose user goals into executable workflows using available agents.

AVAILABLE AGENTS:
{agent_list}

RULES:
1. Break down the user's goal into logical, sequential steps
2. Each step should use ONE agent from the available list
3. Steps should flow logically (output of step N feeds into step N+1)
4. Be creative in combining agents to achieve the goal
5. If you cannot complete the entire goal with available agents, do as much as possible
6. Output ONLY valid JSON in this exact format:

{{
  "reasoning": "Brief explanation of your approach",
  "steps": [
    {{
      "step": 1,
      "agent_name": "exact_agent_name_from_list",
      "task": "Specific task description for this agent",
      "confidence": "high|medium|low"
    }}
  ],
  "estimated_coverage": 0.0 to 1.0,
  "missing_capabilities": ["list", "of", "missing", "capabilities"]
}}

Be precise. Think step-by-step. Maximize coverage while maintaining logical flow."""
    
    async def _generate_decompositions(
        self, 
        goal: str, 
        agents: List[Dict[str, Any]],
        tools: List[Tool],
        system_instruction: str
    ) -> List[Dict[str, Any]]:
        """Generate multiple decomposition strategies using Gemini"""
        
        decompositions = []
        
        # Generate 3-4 different approaches
        approaches = [
            "Create a LINEAR workflow (A → B → C → D)",
            "Create an EFFICIENT workflow (minimize steps, maximize agent reuse)",
            "Create a COMPREHENSIVE workflow (prioritize complete coverage)",
            "Create a CREATIVE workflow (think outside the box, combine agents in novel ways)"
        ]
        
        for i, approach in enumerate(approaches, 1):
            try:
                prompt = f"""Goal: {goal}

Strategy for this attempt: {approach}

Generate a workflow plan following the system instructions."""
                
                # Use Gemini with tools
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7 + (i * 0.1),  # Vary temperature for diversity
                        response_mime_type="application/json"
                    )
                )
                
                # Parse response
                if response.text:
                    try:
                        plan_json = json.loads(response.text)
                    except json.JSONDecodeError:
                        continue
                
        # Validate and score
        validated_plan = self._validate_plan(plan_json, agents)
        if validated_plan:
            decompositions.append({
                'attempt': i,
                'approach': approach,
                'steps': validated_plan.get('steps', []),
                'coverage': validated_plan.get('estimated_coverage', 0.0),
                'reasoning': validated_plan.get('reasoning', ''),
                'missing': validated_plan.get('missing_capabilities', [])
            })
                
            except Exception as e:
                print(f"Decomposition attempt {i} failed: {e}")
                continue
        
        # If no decompositions succeeded, create a fallback
        if not decompositions:
            decompositions.append(self._create_fallback_plan(goal, agents))
        
        return decompositions
    
    def _validate_plan(self, plan: Dict[str, Any], agents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate that plan uses only available agents"""
        available_agent_names = {a['name'] for a in agents}
        
        if 'steps' not in plan:
            return None
        
        valid_steps = []
        for step in plan['steps']:
            agent_name = step.get('agent_name', '')
            if agent_name in available_agent_names:
                valid_steps.append(step)
        
        if not valid_steps:
            return None
        
        # Recalculate coverage based on valid steps
        original_step_count = len(plan['steps'])
        valid_step_count = len(valid_steps)
        coverage = valid_step_count / original_step_count if original_step_count > 0 else 0.0
        
        return {
            'steps': valid_steps,
            'estimated_coverage': coverage,
            'reasoning': plan.get('reasoning', ''),
            'missing_capabilities': plan.get('missing_capabilities', [])
        }
    
    def _score_and_select_best(
        self, 
        decompositions: List[Dict[str, Any]], 
        goal: str
    ) -> Dict[str, Any]:
        """Score decompositions and select the best one"""
        
        scored = []
        for decomp in decompositions:
            # Scoring criteria
            coverage_score = decomp['coverage'] * 0.6  # 60% weight
            efficiency_score = (1.0 / max(len(decomp['steps']), 1)) * 0.3  # 30% weight
            
            # Composability: Do outputs match next step inputs?
            composability_score = 0.1  # Simplified for now
            
            total_score = coverage_score + efficiency_score + composability_score
            
            scored.append({
                **decomp,
                'total_score': total_score,
                'score_breakdown': {
                    'coverage': coverage_score,
                    'efficiency': efficiency_score,
                    'composability': composability_score
                }
            })
        
        # Return highest scoring decomposition
        best = max(scored, key=lambda x: x['total_score'])
        return best
    
    async def _analyze_gaps(
        self, 
        plan: Dict[str, Any], 
        goal: str, 
        agents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Gemini to analyze capability gaps"""
        
        if plan['coverage'] >= 1.0:
            return {'gaps': [], 'recommendation': ''}
        
        # Use Gemini to identify and specify gaps
        gap_prompt = f"""Goal: {goal}

Current Plan (achievable with available agents):
{json.dumps(plan['steps'], indent=2)}

Coverage: {plan['coverage'] * 100:.0f}%

Missing capabilities: {', '.join(plan.get('missing', []))}

Task: Identify the specific missing capability and generate an MCP-compatible Agent Card specification for it.

Output ONLY valid JSON in this format:
{{
  "at_step": <number>,
  "description": "Detailed description of what's missing and why it's needed",
  "required_capability": "Short name for the capability",
  "suggested_agent_card": {{
    "name": "snake_case_agent_name",
    "description": "Detailed description of what this agent should do",
    "inputSchema": {{
      "type": "object",
      "properties": {{}},
      "required": []
    }},
    "outputSchema": {{
      "type": "object",
      "properties": {{}}
    }},
    "implementation_hints": {{
      "suggested_libraries": ["lib1", "lib2"],
      "complexity": "low|medium|high",
      "estimated_effort": "X days"
    }}
  }}
}}"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=gap_prompt,
                config=GenerateContentConfig(
                    temperature=0.3,  # Lower temp for more deterministic specs
                    response_mime_type="application/json"
                )
            )
            
            gap_data = json.loads(response.text)
            
            recommendation = (
                f"You can complete {plan['coverage'] * 100:.0f}% of this workflow now. "
                f"Build the {gap_data['suggested_agent_card']['name']} to complete the workflow."
            )
            
            return {
                'gaps': [gap_data],
                'recommendation': recommendation
            }
            
        except Exception as e:
            print(f"Gap analysis failed: {e}")
            return {
                'gaps': [{
                    'at_step': len(plan['steps']) + 1,
                    'description': 'Unable to complete full workflow with available agents',
                    'required_capability': 'unknown'
                }],
                'recommendation': f"Complete {plan['coverage'] * 100:.0f}% of workflow with current agents"
            }
    
    def _create_fallback_plan(self, goal: str, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a simple fallback plan if Gemini fails"""
        return {
            'attempt': 0,
            'approach': 'fallback',
            'steps': [{
                'step': 1,
                'agent_name': agents[0]['name'],
                'task': f"Attempt to address: {goal}",
                'confidence': 'low'
            }],
            'coverage': 0.3,
            'reasoning': 'Fallback plan due to generation failure',
            'missing': ['Advanced planning capabilities']
        }


# Singleton instance
planner_agent = None

def get_planner_agent(api_key: str = None) -> PlannerAgent:
    """Get or create the planner agent instance"""
    global planner_agent
    if planner_agent is None:
        planner_agent = PlannerAgent(api_key=api_key)
    return planner_agent