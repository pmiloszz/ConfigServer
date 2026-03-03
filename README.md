# ConfigServer
It allows applications to retrieve flags and rules at runtime (e.g., ), supports user targeting, percentage rollouts, and instant changes via push (SSE/WebSocket) or pull from a cache. Commercial (LaunchDarkly) and open-source (ConfigCat, Unleash) solutions demonstrate typical requirements and patterns.

# In order to run the app in current state
source .venv/Scripts/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Requirements
- uv package manager [link](https://docs.astral.sh/uv/getting-started/installation/#scoop)