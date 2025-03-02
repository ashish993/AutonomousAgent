import streamlit as st
import os
from dotenv import load_dotenv
from pocketgroq import GroqProvider
from pocketgroq.autonomous_agent import AutonomousAgent

# Load environment variables
load_dotenv()

def get_groq_api_key():
    # Set the default API key
    default_api_key = "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"
    
    # Check if the API key is already in the session state
    if 'groq_api_key' not in st.session_state:
        st.session_state['groq_api_key'] = default_api_key
    
    return st.session_state.get('groq_api_key')

@st.cache_data
def get_available_models(api_key):
    groq_provider = GroqProvider(api_key=api_key)
    return [model['id'] for model in groq_provider.get_available_models()]

@st.cache_resource
def get_groq_provider(api_key):
    return GroqProvider(api_key=api_key)

@st.cache_resource
def initialize_agent(api_key, model, temperature):
    groq_provider = get_groq_provider(api_key)
    return AutonomousAgent(groq_provider, model=model, temperature=temperature)

def main():
    st.title("Research Agent Chat")

    

    api_key = get_groq_api_key()

    # Get available models using the cached function
    available_models = get_available_models(api_key)

    # Model selection dropdown
    default_model = "llama3-8b-8192"
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = default_model

    # Use key parameter to let Streamlit manage session state
    selected_model = st.selectbox(
        "Select Model:",
        available_models,
        index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
        key='selected_model'
    )

    # Temperature slider
    temperature = st.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.0, step=0.1, key='temperature')

    # Add Verify checkbox
    verify = st.checkbox("Double-Check (Find two distinct sources that agree)", key='verify')

    # Initialize the agent using the cached function
    agent = initialize_agent(api_key, st.session_state.selected_model, st.session_state.temperature)

    if not agent:
        st.warning("Failed to initialize the agent. Please check your API key.")
        return

    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is your question?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            research_steps = []
            
            for step in agent.process_request(prompt, verify=verify):
                if isinstance(step, dict) and 'type' in step:
                    if step['type'] == 'research':
                        research_steps.append(step['content'])
                    elif step['type'] == 'response':
                        full_response += step['content']
                        message_placeholder.markdown(full_response)
                else:
                    full_response += step
                    message_placeholder.markdown(full_response)
            
            if research_steps:
                with st.expander("View research process"):
                    for i, step in enumerate(research_steps, 1):
                        st.markdown(f"**Step {i}:** {step}")

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    main()
