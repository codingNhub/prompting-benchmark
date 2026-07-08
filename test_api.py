# Quick test to verify API connection works end to end.
# Run with: python test_api.py
# Delete this file before paper submission.

from src.config_manager import load_config
from src.model_wrapper import call_model

# Load config
config = load_config()

# Send one test prompt
prompt = "Classify the sentiment of this sentence. Choose one label: Positive, Negative, or Neutral.\n\nSentence: I absolutely love this project.\nSentiment:"

print("Sending test prompt to Llama 3...")
result = call_model(prompt, config)

print(f"Response: {result['raw_text']}")
print(f"Input tokens: {result['input_tokens']}")
print(f"Output tokens: {result['output_tokens']}")
print("API connection successful.")