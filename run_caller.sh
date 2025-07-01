#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to handle cleanup on exit
cleanup() {
  echo -e "\n${YELLOW}Shutting down processes...${NC}"
  # Kill all background processes in the current process group
  kill $(jobs -p) 2>/dev/null
  # Remove the PID file
  rm -f .agent.pid
  exit 0
}

# Trap to catch SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
  echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
  python3 -m venv venv
  source venv/bin/activate
  echo -e "${GREEN}Installing dependencies...${NC}"
  pip install -r requirements.txt
  python agent.py download-files
else
  source venv/bin/activate
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
  echo -e "${RED}Error: .env.local file not found!${NC}"
  echo -e "${YELLOW}Please create a .env.local file based on .env.example${NC}"
  exit 1
fi

# Check if streamlit_app.py exists
if [ ! -f "streamlit_app.py" ]; then
  echo -e "${RED}Error: streamlit_app.py not found!${NC}"
  exit 1
fi

# Check if streamlit is installed
if ! pip show streamlit > /dev/null 2>&1; then
  echo -e "${YELLOW}Streamlit not found. Installing...${NC}"
  pip install streamlit
fi

# Print header
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}     LiveKit Outbound Caller        ${NC}"
echo -e "${GREEN}====================================${NC}"

# Start the agent in background
echo -e "${BLUE}Starting LiveKit Agent...${NC}"
# Ensure any previous PID file is removed
rm -f .agent.pid
# Start agent with full environment variables passed through
python agent.py dev > agent.log 2>&1 &
AGENT_PID=$!

# Save the PID to a file that Streamlit can read
echo $AGENT_PID > .agent.pid
chmod 644 .agent.pid

# Wait for agent to start
echo -e "${YELLOW}Waiting for agent to start...${NC}"
sleep 5  # Give it more time to start up

# Check if agent started successfully
if ! ps -p $AGENT_PID > /dev/null; then
  echo -e "${RED}Error: Failed to start agent. Check agent.log for details.${NC}"
  cat agent.log
  rm .agent.pid 2>/dev/null
  exit 1
fi

# Start Streamlit in background
echo -e "${BLUE}Starting Streamlit UI...${NC}"
streamlit run streamlit_app.py > streamlit.log 2>&1 &
STREAMLIT_PID=$!

# Wait for Streamlit to start
echo -e "${YELLOW}Waiting for Streamlit UI to start...${NC}"
sleep 3

# Check if Streamlit started successfully
if ! ps -p $STREAMLIT_PID > /dev/null; then
  echo -e "${RED}Error: Failed to start Streamlit. Check streamlit.log for details.${NC}"
  cat streamlit.log
  kill $AGENT_PID
  exit 1
fi

# Get the Streamlit URL
STREAMLIT_URL=$(grep -o "http://[^ ]*" streamlit.log | head -n 1)

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Both services started successfully!${NC}"
echo -e "${GREEN}====================================${NC}"
echo -e "${BLUE}Streamlit UI:${NC} ${STREAMLIT_URL}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep script running until Ctrl+C
wait