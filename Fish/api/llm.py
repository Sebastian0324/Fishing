import requests
import json
import dotenv
import os
import time
import threading
import re

dotenv.load_dotenv()

# Concurrency limiter: max 2 simultaneous LLM requests
_llm_semaphore = threading.Semaphore(2)

def anonymize_email_content(content):
    """
    Anonymize personal information in email content for GDPR compliance.
    Replaces emails, phone numbers, and IP addresses with generic placeholders.
    
    Args:
        content (str): The original email content
    
    Returns:
        str: Anonymized email content
    """
    if not content:
        return content
    
    anonymized = content
    
    # Anonymize email addresses
    anonymized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL_REDACTED]',
        anonymized
    )
    
    # Anonymize phone numbers (various formats)
    # International format: +1-234-567-8900, +1 (234) 567-8900
    anonymized = re.sub(
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        '[PHONE_REDACTED]',
        anonymized
    )
    
    # US/Common format: (123) 456-7890, 123-456-7890, 123.456.7890
    anonymized = re.sub(
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        '[PHONE_REDACTED]',
        anonymized
    )
    
    # Anonymize IP addresses (IPv4)
    anonymized = re.sub(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        '[IP_REDACTED]',
        anonymized
    )
    
    # Anonymize IPv6 addresses
    anonymized = re.sub(
        r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
        '[IP_REDACTED]',
        anonymized
    )
    
    return anonymized

def query_llm(message):
    """
    Query the LLM API with a message and return the response.
    Includes automatic retry logic for 429 responses and concurrency limiting.
    Automatically anonymizes personal information before sending to the API.

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
            
            # Anonymize the message content for GDPR compliance
            anonymized_message = anonymize_email_content(message)
        
            # Retry logic with exponential backoff for 429 responses
            max_retries = 5
            base_delay = 1.0  # Start with ~1 second
        
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json",
                            "HTTP-Referer": "http://localhost:5000",  # Site URL for rankings on openrouter.ai
                            "X-Title": "Fish - Email Phishing Detector",  # Site title for rankings on openrouter.ai
                        },
                        data=json.dumps({
                            "model": "google/gemini-3-pro-preview",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "You are a phishing email detection assistant. The user will provide the body of a potential phishing email that needs analysis. Analyze the email content and identify phishing indicators.\n\nRespond with a concise summary of the phishing indicators found in the email. If no phishing indicators are found, respond with 'No phishing indicators detected.'\n\nNote: Personal information (emails, phone numbers, IP addresses) have been redacted for privacy."
                                },
                                {
                                    "role": "user",
                                    "content": anonymized_message
                                }
                            ]
                        }),
                        timeout=30  # 30 second timeout to prevent hanging
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
                            "error": f"API returned status code {response.status_code}: {response.reason}"
                        }
                
                    # Handle 429 - retry with exponential backoff
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    return {
                        "success": False,
                        "error": "Request timeout - LLM API did not respond within 30 seconds"
                    }
                    
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    return {
                        "success": False,
                        "error": "Connection error - Unable to reach LLM API"
                    }
                    
                except requests.exceptions.RequestException as e:
                    return {
                        "success": False,
                        "error": f"Request error: {str(e)}"
                    }
        
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
