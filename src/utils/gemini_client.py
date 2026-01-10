"""
Gemini LLM Client for DIVA-SQL

This module provides integration with Google's Gemini API for the DIVA-SQL framework.
"""

import google.generativeai as genai
import os
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GeminiResponse:
    """Response wrapper for Gemini API responses"""
    content: str
    finish_reason: Optional[str] = None
    usage_metadata: Optional[Dict] = None


class GeminiLLMClient:
    """
    Google Gemini API client wrapper for DIVA-SQL
    
    This class provides a consistent interface for the DIVA-SQL framework
    to interact with Google's Gemini models.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gemini-2.0-flash",
                 generation_config: Optional[Dict] = None,
                 safety_settings: Optional[Dict] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (or set GOOGLE_API_KEY env var)
            model_name: Gemini model to use
            generation_config: Generation parameters
            safety_settings: Safety filter settings
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        self.model_name = model_name
        self.generation_config = generation_config or {
            "temperature": 0.1,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        # Safety settings - allow most content for SQL generation
        self.safety_settings = safety_settings or [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        # Initialize the model
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            logger.info(f"Initialized Gemini model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def generate_text(self, 
                     prompt: str, 
                     system_instruction: Optional[str] = None,
                     max_retries: int = 3,
                     retry_delay: float = 1.0) -> GeminiResponse:
        """
        Generate text using Gemini API
        
        Args:
            prompt: The input prompt
            system_instruction: Optional system instruction
            max_retries: Number of retry attempts
            retry_delay: Delay between retries
            
        Returns:
            GeminiResponse with generated content
        """
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Generating text (attempt {attempt + 1})")
                response = self.model.generate_content(full_prompt)
                
                # Handle the response
                if response.text:
                    return GeminiResponse(
                        content=response.text.strip(),
                        finish_reason=getattr(response, 'finish_reason', None),
                        usage_metadata=getattr(response, 'usage_metadata', None)
                    )
                else:
                    logger.warning("Empty response from Gemini")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise Exception("Received empty response from Gemini")
                        
            except Exception as e:
                logger.error(f"Error generating text (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed to generate text after {max_retries} attempts: {e}")
    
    # OpenAI-compatible interface for DIVA-SQL
    class Chat:
        def __init__(self, parent_client):
            self.parent = parent_client
            self.completions = GeminiLLMClient.ChatCompletions(parent_client)
    
    class ChatCompletions:
        def __init__(self, parent_client):
            self.parent = parent_client
        
        def create(self, messages, model=None, **kwargs):
            """
            OpenAI-compatible chat completions interface
            
            Args:
                messages: List of message dictionaries
                model: Model name (optional, uses client default)
                **kwargs: Additional parameters
                
            Returns:
                Response object compatible with OpenAI format
            """
            # Convert messages to a single prompt
            prompt_parts = []
            system_instruction = None
            
            for message in messages:
                role = message.get('role', 'user')
                content = message.get('content', '')
                
                if role == 'system':
                    system_instruction = content
                elif role == 'user':
                    prompt_parts.append(f"User: {content}")
                elif role == 'assistant':
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt = "\n".join(prompt_parts)
            
            # Generate response
            response = self.parent.generate_text(
                prompt=prompt,
                system_instruction=system_instruction
            )
            
            # Return OpenAI-compatible response
            class CompatibleResponse:
                def __init__(self, content):
                    self.choices = [CompatibleChoice(content)]
            
            class CompatibleChoice:
                def __init__(self, content):
                    self.message = CompatibleMessage(content)
            
            class CompatibleMessage:
                def __init__(self, content):
                    self.content = content
            
            return CompatibleResponse(response.content)
    
    @property
    def chat(self):
        """OpenAI-compatible chat interface"""
        return self.Chat(self)


def create_gemini_client(api_key: Optional[str] = None, 
                        model_name: str = "gemini-2.0-flash") -> GeminiLLMClient:
    """
    Factory function to create a Gemini client
    
    Args:
        api_key: Google AI API key
        model_name: Gemini model to use
        
    Returns:
        Configured GeminiLLMClient instance
    """
    return GeminiLLMClient(api_key=api_key, model_name=model_name)


# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    
    # Add src to path for testing
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    
    # Test the client
    try:
        client = create_gemini_client()
        
        # Test basic generation
        response = client.generate_text(
            "Generate a simple SQL query to select all columns from a table named 'users'."
        )
        print("Basic generation test:")
        print(response.content)
        print()
        
        # Test OpenAI-compatible interface
        messages = [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": "Write a SQL query to count rows in a table called 'products'."}
        ]
        
        response = client.chat.completions.create(messages=messages)
        print("OpenAI-compatible test:")
        print(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error testing Gemini client: {e}")
        print("Make sure to set your GOOGLE_API_KEY environment variable")
