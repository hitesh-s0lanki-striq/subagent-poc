from dotenv import load_dotenv
import logging
import json

from typing import List, Dict, Union, Any
from langchain.agents import create_agent
from langchain.agents.structured_output import ProviderStrategy
from langchain_core.messages import BaseMessage, ToolMessage, AIMessage

from src.states.meta_query_agent_state import MetaQueryAgentOutput
from src.system_prompts.meta_query_agent_system_prompt import get_meta_query_agent_system_prompt

from src.tools.launching_agent_tool import launching_agent_tool
from src.tools.reporting_agent_tool import reporting_agent_tool

load_dotenv()
logger = logging.getLogger(__name__)

class MetaQueryAgent:
    def __init__(self, model: str):
        self.name = "Meta Query Agent"
        self.instructions = get_meta_query_agent_system_prompt()
        self.model = model
        self.tools = [launching_agent_tool, reporting_agent_tool]

        # Create the agent executable upon initialization
        self.agent = create_agent(
            model=self.model,
            system_prompt=self.instructions,
            tools=self.tools,
            response_format=ProviderStrategy(MetaQueryAgentOutput)
        )
        
    def _serialize_message(self, msg) -> dict:
        if hasattr(msg, "model_dump"):
            return msg.model_dump()

        if hasattr(msg, "dict"):
            try:
                return msg.dict()
            except Exception:
                pass

        d = {
            "type": getattr(msg, "type", type(msg).__name__),
            "content": getattr(msg, "content", str(msg)),
        }

        for k in ["name", "id", "tool_call_id", "artifact", "status", "additional_kwargs", "response_metadata"]:
            if hasattr(msg, k):
                d[k] = getattr(msg, k)

        return d

    def _clean_messages(self, messages: List[BaseMessage]) -> List[BaseMessage]:
        """
        Clean messages to ensure valid structure for OpenAI API.
        Tool messages must be preceded by an AIMessage with tool_calls.
        Removes orphaned tool messages that don't have a valid preceding AIMessage.
        """
        cleaned = []
        i = 0
        
        while i < len(messages):
            msg = messages[i]
            
            # If it's a tool message, check if the previous message is an AIMessage with tool_calls
            if isinstance(msg, ToolMessage):
                # Look back to find the most recent AIMessage
                prev_ai_idx = None
                for j in range(i - 1, -1, -1):
                    if isinstance(messages[j], AIMessage):
                        prev_ai_idx = j
                        break
                
                # Only include tool message if there's a preceding AIMessage with tool_calls
                if prev_ai_idx is not None:
                    prev_ai = messages[prev_ai_idx]
                    # Check if the AIMessage has tool_calls
                    tool_calls = getattr(prev_ai, 'tool_calls', None) or []
                    if tool_calls:
                        # Check if this tool message's tool_call_id matches one of the tool_calls
                        tool_call_id = getattr(msg, 'tool_call_id', None) or getattr(msg, 'id', None)
                        if tool_call_id:
                            # Verify the tool_call_id exists in the previous AIMessage's tool_calls
                            matching_tool_call = False
                            for tc in tool_calls:
                                # Handle both dict and object formats
                                tc_id = None
                                if isinstance(tc, dict):
                                    tc_id = tc.get('id')
                                elif hasattr(tc, 'id'):
                                    tc_id = tc.id
                                
                                if tc_id == tool_call_id:
                                    matching_tool_call = True
                                    break
                            
                            if matching_tool_call:
                                cleaned.append(msg)
                            # If no match, skip this tool message (it's orphaned)
                        else:
                            # No tool_call_id, skip it (invalid tool message)
                            pass
                    else:
                        # Previous AIMessage has no tool_calls, skip this tool message
                        pass
                else:
                    # No preceding AIMessage, skip this tool message (orphaned)
                    pass
            else:
                # Not a tool message, include it
                cleaned.append(msg)
            
            i += 1
        
        return cleaned

    def invoke(self, messages: Union[List[Dict[str, str]], List[BaseMessage]]) -> Dict[str, Any]:
        """
        Returns:
        {
          "structured_response": <MasterAgentOutput as dict>,
          "tool_calls": [<tool message dicts>...],
          "messages": [<all message dicts>...]   # optional but useful
        }
        """
        try:
            # Convert dict messages to BaseMessage if needed
            if messages and isinstance(messages[0], dict):
                from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
                base_messages = []
                for msg in messages:
                    role = msg.get("role", "user")
                    if role == "user":
                        base_messages.append(HumanMessage(content=msg.get("content", "")))
                    elif role == "assistant":
                        base_messages.append(AIMessage(content=msg.get("content", "")))
                    elif role == "tool":
                        base_messages.append(ToolMessage(
                            content=msg.get("content", ""),
                            tool_call_id=msg.get("tool_call_id", "unknown"),
                            name=msg.get("name")
                        ))
                messages = base_messages
            
            # Clean messages to ensure valid structure
            # Remove orphaned tool messages that don't have a valid preceding AIMessage with tool_calls
            cleaned_messages = self._clean_messages(messages)
            
            # Additional safety: if we still have issues, filter out all tool messages
            # (The agent will make its own tool calls, so previous tool messages aren't strictly necessary)
            if not cleaned_messages:
                # If cleaning removed everything, fall back to just human/assistant messages
                cleaned_messages = [msg for msg in messages if not isinstance(msg, ToolMessage)]
            
            # Try to invoke with cleaned messages, with fallback to removing all tool messages
            try:
                response = self.agent.invoke({"messages": cleaned_messages})
            except Exception as invoke_error:
                # If there's still an error about tool messages, remove all tool messages and retry
                if "tool" in str(invoke_error).lower() and "tool_calls" in str(invoke_error).lower():
                    logger.warning(f"Tool message error detected, retrying without tool messages: {invoke_error}")
                    # Remove all tool messages as a last resort
                    cleaned_messages = [msg for msg in cleaned_messages if not isinstance(msg, ToolMessage)]
                    response = self.agent.invoke({"messages": cleaned_messages})
                else:
                    # Re-raise if it's a different error
                    raise

            # Serialize ALL returned messages
            raw_msgs = response.get("messages", []) or []
            serializable_messages = [self._serialize_message(m) for m in raw_msgs]

            # Extract tool call messages (can be multiple)
            tool_calls = []
            for m in serializable_messages:
                # LangChain tool messages typically have type == "tool"
                if (m.get("type") == "tool") or (m.get("name") in {
                    "weather_agent_tool",
                    "meta_campaign_agent_tool",
                    "brand_profile_context_tool",
                }):
                    tool_calls.append(m)

            # Handle structured_response
            structured_response = response.get("structured_response")

            if hasattr(structured_response, "model_dump"):
                structured_response = structured_response.model_dump()
            elif isinstance(structured_response, str):
                import json
                try:
                    structured_response = json.loads(structured_response)
                except Exception:
                    structured_response = {"raw_response": structured_response}
            elif structured_response is None:
                structured_response = {"response": "", "context": {}}
            elif not isinstance(structured_response, dict):
                structured_response = dict(structured_response) if hasattr(structured_response, "__dict__") else {"raw_response": str(structured_response)}

            # (Optional) log messages to file
            import os, json
            os.makedirs("logs", exist_ok=True)
            with open("logs/messages.json", "w") as f:
                json.dump(serializable_messages, f, indent=2)

            return {
                "structured_response": structured_response,
                "tool_calls": tool_calls,
                "messages": serializable_messages,  # keep for debugging; remove if you want
            }

        except Exception as e:
            logger.error(f"Error in MasterAgent.invoke: {e}", exc_info=True)
            return {
                "structured_response": {
                    "context": {"stage": "error"},
                    "response": f"Error during master agent: {str(e)}"
                },
                "tool_calls": [],
                "messages": [],
                "error": True,
                "error_message": str(e),
            }


