import streamlit as st
import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from typing import List, Dict

from src.llms.openai_llm import OpenAILLM
from src.agents.meta_query_agent import MetaQueryAgent

# Page configuration
st.set_page_config(
    page_title="Meta Query Agent Chat",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages: List[Dict[str, str]] = []

if "meta_query_agent" not in st.session_state:
    st.session_state.meta_query_agent = None

if "initialized" not in st.session_state:
    st.session_state.initialized = False


def initialize_agents():
    """Initialize the OpenAI LLM, Meta Query Agent"""
    try:
        # Initialize OpenAI LLM
        openai_llm = OpenAILLM()
        model = openai_llm.get_llm_model()
        
        # Initialize Meta Query Agent with the model
        meta_query_agent = MetaQueryAgent(model=model)
        
        st.session_state.meta_query_agent = meta_query_agent
        st.session_state.initialized = True
        return True
    except Exception as e:
        st.error(f"Failed to initialize agents: {str(e)}")
        return False


def main():
    st.title("🤖 Meta Query Agent Chat Interface")
    st.markdown("Chat with the Meta Query Agent to manage your Meta campaign workflows.")
    
    # Initialize agents if not already done
    if not st.session_state.initialized:
        with st.spinner("Initializing Agents..."):
            if not initialize_agents():
                st.stop()
    
    # Display chat messages
    for message in st.session_state.messages:
        role = message.get("role", "assistant")
        agent_name = message.get("agent_name", "")

        if role == "tool":
            # Display tool messages as assistant bubbles (or create your own style)
            with st.chat_message("assistant"):
                tool_name = message.get("name", "tool")
                status = message.get("status", "success")
                agent_label = f" [{agent_name}]" if agent_name else ""
                st.caption(f"🔧 Tool: `{tool_name}`{agent_label} • status: **{status}**")
                # st.markdown(message.get("content", ""))
        else:
            with st.chat_message(role):
                agent_label = f" [{agent_name}]" if agent_name else ""
                if agent_label:
                    st.caption(agent_label)
                st.markdown(message.get("content", ""))
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "agent_name": "",
            "formatted_output": ""
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Build LangChain messages including TOOL messages
        langchain_messages = []
        for msg in st.session_state.messages:
            role = msg.get("role")

            if role == "user":
                langchain_messages.append(HumanMessage(content=msg["content"]))

            elif role == "assistant":
                # Pass the formatted output JSON string if available, else fallback to visible content
                assistant_payload = msg.get("formatted_output") or msg.get("formated_output") or msg.get("content", "")
                langchain_messages.append(AIMessage(content=assistant_payload))

            elif role == "tool":
                # ToolMessage requires tool_call_id for best compatibility
                langchain_messages.append(
                    ToolMessage(
                        content=msg.get("content", ""),
                        tool_call_id=msg.get("tool_call_id", "unknown_tool_call_id"),
                        name=msg.get("name"),
                    )
                )

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Invoke based on selected mode
                    result = st.session_state.meta_query_agent.invoke(langchain_messages)

                    # Expecting: { structured_response, tool_calls, ... }
                    structured = {}
                    tool_calls = []

                    if isinstance(result, dict) and "structured_response" in result:
                        structured = result.get("structured_response") or {}
                        tool_calls = result.get("tool_calls") or []
                    else:
                        # fallback if your invoke returns only structured_response
                        structured = result if isinstance(result, dict) else {"response": str(result), "context": {}}
                        tool_calls = []

                    response_text = structured.get("response", str(structured))

                    # Show assistant response
                    st.markdown(response_text)

                    # Store assistant message (include full structured JSON as string so it can be replayed)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "agent_name": "META_QUERY_AGENT",
                        "formatted_output": json.dumps(structured, ensure_ascii=False),
                    })

                    # Store tool calls as separate messages + display them
                    if tool_calls:
                        with st.expander("🔧 Tool calls"):
                            st.json(tool_calls)

                        for t in tool_calls:
                            tool_name = t.get("name", "")
                            # Determine agent_name based on tool name
                            if tool_name == "launching_agent_tool":
                                agent_name = "LAUNCHING_AGENT"
                            elif tool_name == "reporting_agent_tool":
                                agent_name = "REPORTING_AGENT"
                            else:
                                agent_name = "META_QUERY_AGENT"  # Default fallback
                            
                            st.session_state.messages.append({
                                "role": "tool",
                                "name": tool_name,
                                "content": t.get("content", ""),
                                "agent_name": agent_name,
                                "tool_call_id": t.get("tool_call_id") or t.get("id") or "unknown_tool_call_id",
                                "status": t.get("status", "success"),
                                "formatted_output": ""
                            })

                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message,
                        "agent_name": "META_QUERY_AGENT",
                        "formatted_output": ""
                    })

    # Sidebar with controls
    with st.sidebar:
        st.header("Agent Flow Selection")
        
        # Update mode if changed
        st.markdown("---")
        st.header("Controls")
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
        
        st.markdown("---")
        st.subheader("Chat Info")
        st.write(f"Total messages: {len(st.session_state.messages)}")
        
        if st.session_state.initialized:
            st.success("✅ Agents initialized")
        else:
            st.error("❌ Agents not initialized")


if __name__ == "__main__":
    main()
