#!/bin/bash
cd /workspaces/Elson/Elson/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload