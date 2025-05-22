from .base_agent import BaseAgent
import os
import google.generativeai as genai
import time
import re

class WeatherAgent(BaseAgent):
    def __init__(self):
        """Initialize the Weather Agent."""
        super().__init__()
        self.system_prompt = """You are a weather expert. Provide information about:
1. Current weather conditions
2. Temperature ranges
3. Precipitation chances
4. Weather forecasts
5. Travel recommendations based on weather
Use emojis to make responses more engaging and informative.
"""

        # Initialize Gemini
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
                
            genai.configure(api_key=api_key)
            
            # List available models
            models = genai.list_models()
            print("Available models:", [model.name for model in models])
            
            # Try to get the specific model
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("Successfully initialized gemini-2.0-flash")
            except Exception as model_error:
                print(f"Error initializing gemini-2.0-flash: {str(model_error)}")
                # Fallback to gemini-pro
                print("Falling back to gemini-pro")
                self.model = genai.GenerativeModel('gemini-pro')
                
        except Exception as e:
            print(f"Error initializing Gemini: {str(e)}")
            self.model = None

    def process(self, user_input: str) -> dict:
        """Process weather-related queries."""
        max_retries = 3
        base_delay = 2  # Start with 2 seconds delay
        
        for attempt in range(max_retries):
            try:
                # Generate response using Gemini
                response = self.model.generate_content(
                    f"{self.system_prompt}\n\nUser: {user_input}"
                )
                
                return {
                    "status": "success",
                    "message": response.text
                }
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str and "quota" in error_str.lower():
                    # Extract retry delay from error message if available
                    retry_match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)', error_str)
                    if retry_match:
                        delay = int(retry_match.group(1))
                    else:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                    
                    print(f"Quota exceeded, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                    
                print(f"Error: {str(e)}")
                if attempt == max_retries - 1:
                    return {
                        "status": "error",
                        "message": f"An error occurred after {max_retries} attempts: {str(e)}"
                    }
                    
        return {
            "status": "error",
            "message": "Failed to generate response after all retries"
        }

    def process_with_context(self, input_data: dict) -> dict:
        """
        Process weather-related queries with context.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response with weather information
        """
        try:
            user_input = input_data.get('user_input', '')
            context = input_data.get('context', {})
            entities = input_data.get('entities', {})
            history = input_data.get('history', [])
            
            # Build enhanced prompt with context
            enhanced_prompt = f"{self.system_prompt}\n\n"
            
            # Add context information if available
            if context:
                if context.get('locations'):
                    locations = ", ".join(context['locations'])
                    enhanced_prompt += f"Locations mentioned: {locations}\n"
                    
                if context.get('dates'):
                    dates = ", ".join(context['dates'])
                    enhanced_prompt += f"Dates mentioned: {dates}\n"
            
            # Add conversation history for context
            if history and len(history) > 0:
                enhanced_prompt += "\nRecent conversation:\n"
                recent_history = history[-5:] if len(history) >= 5 else history
                for message in recent_history:
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    enhanced_prompt += f"{role.capitalize()}: {content}\n"
            
            # Add user query
            enhanced_prompt += f"\nUser: {user_input}"
            
            # Generate response with retry logic
            max_retries = 3
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(enhanced_prompt)
                    
                    if not response or not hasattr(response, 'text'):
                        raise ValueError("Empty or invalid response from model")
                    
                    return {
                        "status": "success",
                        "content": response.text
                    }
                    
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str and "quota" in error_str.lower():
                        retry_match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)', error_str)
                        if retry_match:
                            delay = int(retry_match.group(1))
                        else:
                            delay = base_delay * (2 ** attempt)
                        
                        print(f"Quota exceeded, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    
                    print(f"Error: {str(e)}")
                    if attempt == max_retries - 1:
                        return {
                            "status": "error",
                            "message": f"An error occurred after {max_retries} attempts: {str(e)}"
                        }
            
            return {
                "status": "error",
                "message": "Failed to generate response after all retries"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }