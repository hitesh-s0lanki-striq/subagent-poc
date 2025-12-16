from dotenv import load_dotenv
import logging
import json

from typing import List, Dict, Union, Any
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain_core.messages import BaseMessage

from src.states.launching_agent_state import LaunchingAgentOutput
from src.system_prompts.launching_agent_system_prompt import get_launching_agent_system_prompt

from src.tools.image_generation_tool import image_generation_tool
from src.tools.launch_campaign_tool import launch_campaign_tool

load_dotenv()
logger = logging.getLogger(__name__)

class LaunchingAgent:
    def __init__(self, model: str):
        self.name = "Launching Agent"
        self.instructions = get_launching_agent_system_prompt()
        self.model = model
        self.tools = [image_generation_tool, launch_campaign_tool]

        # Create the agent executable upon initialization
        self.agent = create_agent(
            model=self.model,
            system_prompt=self.instructions,
            tools=self.tools,
            response_format=ProviderStrategy(LaunchingAgentOutput)
        )

    def invoke(self, messages: Union[List[Dict[str, str]], List[BaseMessage]]) -> Dict[str, Any]:
        """
        Invoke the agent and return properly formatted response.
        Handles errors and ensures proper JSON serialization.
        """
        try:
            response = self.agent.invoke({"messages": messages})
            
            # Handle the structured_response - convert Pydantic model to dict if needed
            if "structured_response" in response:
                structured_response = response["structured_response"]
                
                # If it's a Pydantic model, convert to dict
                if hasattr(structured_response, 'model_dump'):
                    response["structured_response"] = structured_response.model_dump()
                elif isinstance(structured_response, str):
                    # If it's a string, try to parse as JSON
                    try:
                        response["structured_response"] = json.loads(structured_response)
                    except json.JSONDecodeError:
                        # If not valid JSON, wrap it in a dict
                        response["structured_response"] = {"raw_response": structured_response}
                elif not isinstance(structured_response, dict):
                    # If it's some other type, convert to dict
                    response["structured_response"] = dict(structured_response) if hasattr(structured_response, '__dict__') else {"raw_response": str(structured_response)}
            
            return response["structured_response"]
            
        except Exception as e:
            logger.error(f"Error in LaunchingAgent.invoke: {e}", exc_info=True)
            # Return error response in expected format
            return {
                "error": True,
                "error_message": str(e),
                "structured_response": {
                    "error": True,
                    "error_message": str(e),
                    "brief_summary": f"Error during launching campaign: {str(e)}"
                }
            }

