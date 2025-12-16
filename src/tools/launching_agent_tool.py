from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
import streamlit as st
import json
from src.llms.openai_llm import OpenAILLM
from src.agents.launching_agent import LaunchingAgent
import logging

logger = logging.getLogger(__name__)

@tool("launching_agent_tool")     
def launching_agent_tool(query: str) -> str:
    """
    Meta Ads Campaign Launching agent tool. 
    - If query is not provided: returns the follow_up_question (what Master should ask user).
    - If query is provided: returns the launching information for the query.
    """
    try:
        # Initialize session state messages if not exists
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Add incoming query to session state as user message
        st.session_state.messages.append({
            "role": "user",
            "content": query,
            "agent_name": "LAUNCHING_AGENT",
            "formatted_output": ""
        })
        
        # Get all messages related to LAUNCHING_AGENT
        launching_agent_messages = []
        for msg in st.session_state.messages:
            if msg.get("agent_name") == "LAUNCHING_AGENT":
                role = msg.get("role")
                if role == "user":
                    launching_agent_messages.append(HumanMessage(content=msg.get("content", "")))
                elif role == "assistant":
                    # Use formatted_output if available, else content
                    content = msg.get("formatted_output") or msg.get("content", "")
                    launching_agent_messages.append(AIMessage(content=content))
        
        model = OpenAILLM().get_llm_model()
        launching_agent = LaunchingAgent(model=model)

        # Invoke with all related messages
        result_message = launching_agent.invoke(launching_agent_messages)

        print(f"Launching agent tool result: {result_message}")

        # Determine response text and return value
        response_text = ""
        if isinstance(result_message, dict):
            follow_up_question = result_message.get("follow_up_question", "")
            state = result_message.get("state", "")
            
            if follow_up_question:
                response_text = follow_up_question
            elif state == "completed":
                response_text = "Meta Campaign launch successfully"
            else:
                response_text = str(result_message)
        else:
            response_text = str(result_message)
        
        # Add agent response to session state
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "agent_name": "LAUNCHING_AGENT",
            "formatted_output": json.dumps(result_message, ensure_ascii=False) if isinstance(result_message, dict) else ""
        })

        # Return the response text
        return response_text
    
    except Exception as e:
        logger.error(f"Error in launching_agent_tool: {e}", exc_info=True)
        error_msg = f"Error during launching campaign: {str(e)}"
        
        # Store error in session state
        if "messages" in st.session_state:
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "agent_name": "LAUNCHING_AGENT",
                "formatted_output": ""
            })
        
        return error_msg
