"""
Local LLM client for LM Studio integration.
"""
import requests
from typing import Optional, Dict, Any, List


class LocalLLMClient:
    """Client for interacting with local LLM via OpenAI-compatible API."""
    
    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        """
        Initialize local LLM client.
        
        Args:
            base_url: Base URL for the local LLM API
        """
        self.base_url = base_url.rstrip('/')
        self.chat_endpoint = f"{self.base_url}/chat/completions"
        self.completions_endpoint = f"{self.base_url}/completions"
    
    def send_message(self, prompt: str,
                    system_prompt: Optional[str] = None,
                    model: str = "local-model",
                    max_tokens: int = 2048,
                    temperature: float = 0.7,
                    history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a message to the local LLM.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            model: Model name (for LM Studio, usually doesn't matter)
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            history: Optional conversation history
            
        Returns:
            Dict with 'response', 'usage', and 'metadata' keys
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            if history:
                messages.extend(history)
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code != 200:
                return {
                    'response': None,
                    'error': f"API error: {response.status_code} - {response.text}",
                    'metadata': {'success': False}
                }
            
            data = response.json()
            
            return {
                'response': data['choices'][0]['message']['content'],
                'usage': data.get('usage', {}),
                'metadata': {
                    'success': True,
                    'model': data.get('model', model),
                    'finish_reason': data['choices'][0].get('finish_reason')
                }
            }
            
        except requests.exceptions.Timeout:
            return {
                'response': None,
                'error': 'Request timed out',
                'metadata': {'success': False}
            }
        except requests.exceptions.ConnectionError:
            return {
                'response': None,
                'error': 'Could not connect to local LLM. Is LM Studio running?',
                'metadata': {'success': False}
            }
        except Exception as e:
            return {
                'response': None,
                'error': str(e),
                'metadata': {'success': False}
            }
    
    def simple_prompt(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Send a simple prompt and return just the response text.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional arguments to pass to send_message
            
        Returns:
            Response text or None if error
        """
        result = self.send_message(prompt, **kwargs)
        return result.get('response')
    
    def code_generation(self, specification: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate code using the local LLM.
        
        Args:
            specification: Code specification
            language: Programming language
            
        Returns:
            Dict with response and metadata
        """
        system_prompt = f"You are an expert {language} programmer. Generate clean, efficient, and well-documented code."
        prompt = f"Generate {language} code for:\n\n{specification}\n\nProvide only the code with comments."
        
        return self.send_message(
            prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=4096
        )
    
    def code_review(self, code: str, context: str = "") -> Dict[str, Any]:
        """
        Review code using the local LLM.
        
        Args:
            code: Code to review
            context: Additional context
            
        Returns:
            Dict with response and metadata
        """
        system_prompt = "You are a code review expert. Provide constructive, specific feedback."
        prompt = f"""Review this code:

Context: {context}

Code:
```
{code}
```

Provide feedback on:
- Code quality
- Potential issues
- Improvements
- Best practices"""

        return self.send_message(
            prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=2048
        )
    
    def check_availability(self) -> bool:
        """
        Check if the local LLM is available.
        
        Returns:
            True if available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


