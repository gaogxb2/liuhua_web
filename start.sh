#!/bin/bash
cd "$(dirname "$0")"
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8001
