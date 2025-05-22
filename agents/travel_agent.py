from .base_agent import BaseAgent
import logging
import os
import google.generativeai as genai
import time
import re

class TravelAgent(BaseAgent):
    def __init__(self):
        """Initialize the Travel Agent."""
        super().__init__()
        
        # System prompt for the model
        self.system_prompt = """You are a travel expert. Please provide concise, engaging, and visually appealing summaries in Vietnamese about:
1. Popular destinations and attractions
2. Best times to visit
3. Transportation options
4. Accommodation recommendations
5. Local customs and etiquette

Guidelines:
- Always respond in Vietnamese
- Use emojis to make responses more engaging
- Keep responses short, sweet, and easy to read
- If the user asks about a specific city or destination, provide detailed information about that place
- If the user's question is unclear, ask for clarification

Example response format:
🗺️ [Destination Name]
📍 Địa điểm nổi tiếng: [list with emojis]
⏰ Thời điểm tốt nhất: [time with emoji]
🚗 Di chuyển: [transportation with emoji]
🏨 Nơi ở: [accommodation with emoji]
💡 Mẹo nhỏ: [tips with emoji]
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
        """Process travel-related queries."""
        max_retries = 3
        base_delay = 2  # Start with 2 seconds delay
        
        for attempt in range(max_retries):
            try:
                logging.info(f"TravelAgent processing input: {user_input} (attempt {attempt + 1}/{max_retries})")
                # Generate response using Gemini
                response = self.model.generate_content(
                    f"{self.system_prompt}\n\nUser: {user_input}"
                )
                logging.info(f"TravelAgent response: {response.text}")
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
                    
                    logging.warning(f"Quota exceeded, retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                    
                logging.error(f"TravelAgent error: {str(e)}")
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
        Process travel-related queries with context.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response with travel information
        """
        try:
            user_input = input_data.get('user_input', '')
            context = input_data.get('context', {})
            entities = input_data.get('entities', {})
            history = input_data.get('history', [])
            
            logging.info(f"TravelAgent processing input with context: {user_input}")
            
            # Build enhanced prompt with context
            enhanced_prompt = f"{self.system_prompt}\n\n"
            
            # Add context information if available
            if context:
                if context.get('locations'):
                    locations = ", ".join(context['locations'])
                    enhanced_prompt += f"Địa điểm đã đề cập: {locations}\n"
                    
                if context.get('dates'):
                    dates = ", ".join(context['dates'])
                    enhanced_prompt += f"Thời gian đã đề cập: {dates}\n"
                    
                # Add supporting info from other agents if available
                if context.get('supporting_info'):
                    supporting_info = context['supporting_info']
                    if isinstance(supporting_info, dict) and supporting_info.get('content'):
                        enhanced_prompt += f"Thông tin bổ sung: {supporting_info['content']}\n"
            
            # Add conversation history for context
            if history and len(history) > 0:
                enhanced_prompt += "\nLịch sử trò chuyện gần đây:\n"
                # Get last 3 exchanges
                recent_history = history[-6:] if len(history) >= 6 else history
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
                    logging.info(f"TravelAgent generating response with context (attempt {attempt + 1}/{max_retries})")
                    response = self.model.generate_content(enhanced_prompt)
                    
                    if not response or not hasattr(response, 'text'):
                        raise ValueError("Empty or invalid response from model")
                    
                    logging.info(f"TravelAgent response with context: {response.text[:100]}...")
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
                        
                        logging.warning(f"Quota exceeded, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    
                    logging.error(f"Error generating response with context: {str(e)}")
                    if attempt == max_retries - 1:
                        return {
                            "status": "error",
                            "message": f"Failed to generate response after {max_retries} attempts: {str(e)}"
                        }
            
            return {
                "status": "error",
                "message": "Failed to generate response after all retries"
            }
            
        except Exception as e:
            logging.error(f"Error in process_with_context: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            } 