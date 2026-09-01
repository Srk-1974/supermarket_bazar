#!/usr/bin/env bash
# Simple helper to run the Flask app locally
python -m pip install -r requirements.txt
cp .env.example .env 2>/dev/null || true
python app.py
