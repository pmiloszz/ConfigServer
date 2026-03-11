# ConfigServer
It allows applications to retrieve flags and rules at runtime (e.g., ), supports user targeting, percentage rollouts, and instant changes via push (SSE/WebSocket) or pull from a cache. Commercial (LaunchDarkly) and open-source (ConfigCat, Unleash) solutions demonstrate typical requirements and patterns.

# In order to run the app in current state
'''bash
uv run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
'''

# Using CRUD options
### Get
'''bash
#list
curl -sS "http://127.0.0.1:8000/flags?app_name=demo&env=dev"
#by flag
curl -sS "http://127.0.0.1:8000/flags/1"
'''

### Post
'''bash
curl -sS -X POST http://127.0.0.1:8000/flags \
  -H "Content-Type: application/json" \
  -d '{"app":"demo","env":"dev","key":"feature_z","value":true,"description":"test"}'"
'''
### Put
'''bash
curl -sS -X PUT http://127.0.0.1:8000/flags/1 \
  -H "Content-Type: application/json" \
  -d '{"value":false,"description":"turned off","version":2}'
'''
### Delete
'''bash
curl -sS -X DELETE http://127.0.0.1:8000/flags/3 -i
'''

# Requirements
- uv package manager [link](https://docs.astral.sh/uv/getting-started/installation/#scoop)