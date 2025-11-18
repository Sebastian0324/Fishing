import requests
import json
import dotenv
import os
import time
import threading

dotenv.load_dotenv()

# Concurrency limiter: max 2 simultaneous LLM requests
_llm_semaphore = threading.Semaphore(2)

def query_llm(message):
    """
    Query the LLM API with a message and return the response.
    Includes automatic retry logic for 429 responses and concurrency limiting.

    Args:
        message (str): The message to send to the LLM
    
    Returns:
        dict: A dictionary with 'success' and either 'response' or 'error'
    """
    # Acquire semaphore to limit concurrent requests to 2
    with _llm_semaphore:
        try:
            api_key = os.getenv('API_KEY')
        
            if not api_key:
                return {
                    "success": False,
                    "error": "API_KEY not found in environment variables"
                }
        
            # Retry logic with exponential backoff for 429 responses
            max_retries = 5
            base_delay = 1.0  # Start with ~1 second
        
            for attempt in range(max_retries):
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:5000",  # Site URL for rankings on openrouter.ai
                        "X-Title": "Fish - Email Phishing Detector",  # Site title for rankings on openrouter.ai
                    },
                    data=json.dumps({
                        "model": "deepseek/deepseek-r1:free",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a phishing email detection assistant. The user will provide the body of a potential phishing email that needs analysis. Analyze the email content and identify phishing indicators."
                            },
                            {
                                "role": "user",
                                "content": message
                            }
                        ],
                    }),
                    timeout=30
                )
            
                # Return immediately on success
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "response": result['choices'][0]['message']['content']
                    }
            
                # Return immediately on non-429 errors (don't retry)
                if response.status_code != 429:
                    return {
                        "success": False,
                        "error": f"API returned status code {response.status_code}: {response.text}"
                    }
            
                # Handle 429 - retry with exponential backoff
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        
            # All retries exhausted
            return {
                "success": False,
                "error": f"API returned status code 429 after {max_retries} retries"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"LLM API error: {str(e)}"
            }
