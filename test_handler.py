# test_handler.py
import json
import api_main

# Simulate a job input
job = {"input": {"videos": ["1_2024-10-30_145008.mp4"]}}
result = api_main.handler(job)
print(json.dumps(result, indent=2))