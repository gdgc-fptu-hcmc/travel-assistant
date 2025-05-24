from .base_agent import BaseAgent
import os
import google.generativeai as genai
import time
import re
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoodAgent(BaseAgent):
    def __init__(self):
        """Initialize the Food Agent."""
        super().__init__()
        self.system_prompt = """You are a food and cuisine expert. Provide information about:
1. Local specialties and must-try dishes
2. Restaurant recommendations
3. Food safety tips
4. Dietary restrictions and alternatives
5. Food culture and traditions
Use emojis to make responses more engaging and appetizing.
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

    def process(self, input_data, conversation_history=None):
        """
        Process food-related queries and provide restaurant recommendations
        """
        try:
            logger.info(f"FoodAgent processing input: {input_data}")
            
            # Extract location and cuisine type from input
            location = self._extract_location(input_data)
            cuisine = self._extract_cuisine(input_data)
            
            # Generate response
            response = self._generate_response(location, cuisine)
            
            return {
                "agent": self.name,
                "status": "success",
                "content": response
            }
            
        except Exception as e:
            logger.error(f"Error in FoodAgent: {str(e)}")
            return {
                "agent": self.name,
                "status": "error",
                "message": f"Error processing food request: {str(e)}"
            }
    
    def _extract_location(self, text):
        """Extract location from input text"""
        # TODO: Implement location extraction logic
        return "Đà Nẵng"  # Default for now
    
    def _extract_cuisine(self, text):
        """Extract cuisine type from input text"""
        # TODO: Implement cuisine extraction logic
        return "local"  # Default for now
    
    def _generate_response(self, location, cuisine):
        """Generate restaurant recommendations"""
        # TODO: Implement restaurant recommendation logic
        return f"""Chào bạn! Dưới đây là một số nhà hàng ngon ở {location} mà bạn có thể tham khảo:

1. Nhà hàng Hải Sản:
   - Địa chỉ: 123 Đường Biển
   - Đặc sản: Hải sản tươi sống
   - Giá: Trung bình 500k-1tr/người

2. Nhà hàng Đặc Sản:
   - Địa chỉ: 456 Đường Trung Tâm
   - Đặc sản: Món ăn địa phương
   - Giá: Trung bình 300k-500k/người

3. Nhà hàng Quốc Tế:
   - Địa chỉ: 789 Đường Phố Tây
   - Đặc sản: Món Âu, Á
   - Giá: Trung bình 800k-1.5tr/người

Lưu ý: Giá cả có thể thay đổi tùy theo mùa và thời điểm. Bạn nên đặt bàn trước để đảm bảo có chỗ. 😊"""

    def process_with_context(self, input_data: dict) -> dict:
        """
        Process food-related queries with context.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response with food information
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