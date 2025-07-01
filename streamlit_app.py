import streamlit as st
import subprocess
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

st.set_page_config(
    page_title="Outbound Caller",
    page_icon="📞",
    layout="centered",
)

st.title("📞 Outbound Caller")
st.subheader("Make outbound calls using LiveKit Agent")

# Input fields
phone_number = st.text_input("Phone Number", placeholder="+1234567890")
# transfer_to = st.text_input("Transfer To (optional)", placeholder="+1234567890")
transfer_to = ""
# Add some explanation
st.markdown("""
### How it works
1. Enter the phone number to call in international format (e.g., +1234567890)
2. Click "Place Call" to initiate the outbound call
3. The agent will handle the conversation according to the script in `agent.py`
""")

# Check if agent is running
agent_running = False
try:
    # More robust check for agent process
    if os.name == 'nt':  # Windows
        result = subprocess.run(
            ["tasklist"], 
            capture_output=True, 
            text=True
        )
        if "agent.py" in result.stdout:
            agent_running = True
    else:  # Unix/Linux/MacOS
        # Try multiple methods to detect the agent
        # Method 1: ps aux
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        if "python agent.py dev" in result.stdout or "python3 agent.py dev" in result.stdout:
            agent_running = True
        
        # Method 2: Check for process listening on LiveKit websocket port
        if not agent_running:
            try:
                livekit_url = os.getenv("LIVEKIT_URL", "")
                if livekit_url and ":" in livekit_url:
                    # Try to parse the port from the URL
                    port = livekit_url.split(":")[-1].split("/")[0]
                    if port.isdigit():
                        netstat_result = subprocess.run(
                            ["netstat", "-tuln"], 
                            capture_output=True, 
                            text=True
                        )
                        if f":{port}" in netstat_result.stdout:
                            agent_running = True
            except Exception:
                pass
                
        # Method 3: Check for agent PID file if it exists
        if not agent_running and os.path.exists(".agent.pid"):
            try:
                with open(".agent.pid", "r") as f:
                    pid = f.read().strip()
                    if pid.isdigit():
                        # Check if process with this PID exists
                        os.kill(int(pid), 0)  # This will raise an exception if process doesn't exist
                        agent_running = True
            except Exception:
                pass
except Exception as e:
    st.error(f"Error checking agent status: {str(e)}")
    agent_running = False

if not agent_running:
    st.warning("⚠️ Agent doesn't appear to be running. Make sure to start it with `python agent.py dev` before placing calls.")

# Place call button
if st.button("Place Call", disabled=not phone_number):
    if not agent_running:
        st.error("⚠️ Agent is not running! Start it with `python agent.py dev` before placing calls.")
    else:
        try:
            # Prepare metadata for the call
            metadata = {
                "phone_number": phone_number,
                "transfer_to": transfer_to if transfer_to else phone_number
            }
            
            # Create the LiveKit dispatch command
            command = [
                "lk", "dispatch", "create",
                "--new-room",
                "--agent-name", "outbound-caller",
                "--metadata", json.dumps(metadata)
            ]
            
            # Execute the command
            with st.spinner("Placing call..."):
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                )
                
            if "Dispatch created" in result.stdout:
                st.success(f"✅ Call placed successfully to {phone_number}")
                st.code(result.stdout)
            else:
                st.error("❌ Failed to place call")
                st.code(result.stderr)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display agent status and how to start it
st.sidebar.title("Agent Status")
if agent_running:
    st.sidebar.success("✅ Agent is running")
else:
    st.sidebar.error("❌ Agent is not running")
    st.sidebar.markdown("""
    ### Start the agent
    ```
    python agent.py dev
    ```
    """)

# Display configuration info
st.sidebar.title("Configuration")
livekit_url = os.getenv("LIVEKIT_URL", "Not configured")
sip_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID", "Not configured")

st.sidebar.markdown(f"""
### LiveKit Configuration
- **LiveKit URL**: `{livekit_url}`
- **SIP Trunk ID**: `{sip_trunk_id}`

Make sure all required environment variables are set in your `.env.local` file.
""")

# Add call history (this would be a placeholder - in a real app you'd store and retrieve history)
st.sidebar.title("Recent Calls")
st.sidebar.info("Call history would be displayed here in a full implementation")