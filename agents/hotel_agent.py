try:
    from serpapi import Client
except ImportError:
    print("Warning: SERP API not installed. Please run: pip install serpapi")
    Client = None

try:
    from serpapi.google_search import GoogleSearch
except ImportError:
    print("Warning: Google Search Results not installed. Please run: pip install google-search-results")
    GoogleSearch = None

import os
from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent
import logging
from dotenv import load_dotenv

class HotelAgent(BaseAgent):
    def __init__(self):
        """Initialize the Hotel Agent."""
        super().__init__()
        
        load_dotenv()
        self.api_key = os.getenv('HOTEL_API_KEY')
        
        # Initialize Gemini
        try:
            import google.generativeai as genai
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
        
        # System prompt for the model
        self.system_prompt = """You are a hotel booking expert. Please provide concise, engaging, and visually appealing summaries in Vietnamese about:
1. Hotel options and prices
2. Room types and amenities
3. Location and nearby attractions
4. Booking procedures
5. Hotel services and facilities

Guidelines:
- Always respond in Vietnamese
- Use emojis to make responses more engaging
- Keep responses short, sweet, and easy to read
- If the user asks about a specific hotel, provide detailed information about that hotel
- If the user's question is unclear, ask for clarification

Example response format:
🏨 [Hotel Name]
⭐ Xếp hạng: [rating with emoji]
💰 Giá phòng: [price with emoji]
📍 Vị trí: [location with emoji]
🛏️ Loại phòng: [room type with emoji]
✨ Tiện nghi: [amenities with emoji]
"""

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process hotel-related queries
        """
        query = data.get('query', '').lower()
        
        # Example response structure
        response = {
            'status': 'success',
            'message': f'Processing hotel query: {query}',
            'data': {
                'query': query,
                'type': 'hotel',
                'suggestions': []
            }
        }
        
        # Add hotel-specific logic here
        if 'luxury' in query or '5 star' in query:
            response['data']['suggestions'].append('Searching for luxury accommodations...')
        elif 'budget' in query or 'cheap' in query:
            response['data']['suggestions'].append('Looking for budget-friendly hotels...')
        elif 'family' in query:
            response['data']['suggestions'].append('Finding family-friendly hotels...')
            
        return response
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        if 'type' not in input_data:
            return False
        
        if input_data['type'] == 'search_hotels':
            required_fields = ['city', 'check_in', 'check_out']
            return all(field in input_data for field in required_fields)
        elif input_data['type'] == 'get_hotel_details':
            return 'hotel_id' in input_data
        elif input_data['type'] == 'get_area_insights':
            required_fields = ['city', 'area']
            return all(field in input_data for field in required_fields)
        
        return False
        
    def search_hotels(self, city: str, check_in: str, check_out: str) -> Dict[str, Any]:
        try:
            if not self._check_serp_api():
                return {
                    "status": "error",
                    "message": "Google Search Results is not available. Please install google-search-results package."
                }
                
            # First, use Gemini to enhance the search query
            prompt = f"""
            Given a hotel search in {city} from {check_in} to {check_out}, provide:
            1. Best areas to stay
            2. Typical price ranges
            3. Popular hotel chains
            4. Local events during the stay
            5. Seasonal considerations
            6. Transportation options
            7. Safety recommendations
            8. Local customs and etiquette
            """
            
            ai_insights = self._generate_response(prompt)
            
            # Then perform the actual search
            params = {
                "engine": "google_hotels",
                "location": city,
                "check_in": check_in,
                "check_out": check_out,
                "hl": "en",
                "gl": "us",
                "api_key": self.serp_api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if 'hotels_results' in results:
                # Use Gemini to analyze and summarize the results
                hotels_text = str(results['hotels_results'])
                summary = self._summarize_text(hotels_text)
                
                # Get additional insights
                analysis = self._analyze_with_context(
                    hotels_text,
                    f"Analyzing hotel options in {city} from {check_in} to {check_out}"
                )
                
                return {
                    "status": "success",
                    "hotels": results['hotels_results'],
                    "count": len(results['hotels_results']),
                    "ai_insights": ai_insights["content"] if ai_insights["status"] == "success" else None,
                    "summary": summary,
                    "analysis": analysis["content"] if analysis["status"] == "success" else None
                }
            else:
                return {
                    "status": "error",
                    "message": "No hotels found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        try:
            if not Client:
                return {
                    "status": "error",
                    "message": "SERP API client not available. Please install serpapi package."
                }
                
            params = {
                "engine": "google_hotels",
                "hotel_id": hotel_id,
                "hl": "en",
                "gl": "us",
                "api_key": self.serp_api_key
            }
            
            client = Client(params)
            results = client.search()
            
            if 'hotels_results' in results:
                # Use Gemini to analyze the hotel details
                hotel_text = str(results['hotels_results'][0])
                prompt = f"""
                Analyze this hotel information and provide:
                1. Key amenities and features
                2. Location advantages/disadvantages
                3. Value for money assessment
                4. Guest experience insights
                5. Room types and recommendations
                6. Dining options
                7. Additional services
                8. Booking policies and tips
                
                Hotel data:
                {hotel_text}
                """
                
                analysis = self._generate_response(prompt)
                
                return {
                    "status": "success",
                    "hotel": results['hotels_results'][0],
                    "ai_analysis": analysis["content"] if analysis["status"] == "success" else None
                }
            else:
                return {
                    "status": "error",
                    "message": "Hotel not found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def get_area_insights(self, city: str, area: str) -> Dict[str, Any]:
        """Get detailed insights about a specific area in a city"""
        prompt = f"""
        Provide comprehensive insights about the {area} area in {city}:
        1. Safety and security
        2. Transportation options
        3. Local attractions
        4. Dining and nightlife
        5. Shopping opportunities
        6. Cultural significance
        7. Best time to visit
        8. Local tips and recommendations
        """
        
        return self._generate_response(prompt)
        
    def _generate_response(self, prompt: str) -> Dict[str, Any]:
        """Generate a response using Gemini."""
        if not self.model:
            return {
                "status": "error",
                "message": "Gemini model not initialized"
            }
            
        try:
            response = self.model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                return {
                    "status": "success",
                    "content": response.text
                }
            else:
                return {
                    "status": "error",
                    "message": "No response text found in response object"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def _summarize_text(self, text: str) -> str:
        """Summarize text using Gemini."""
        prompt = f"""
        Summarize this text in a concise and engaging way:
        {text}
        """
        
        response = self._generate_response(prompt)
        return response["content"] if response["status"] == "success" else "Summary not available"
        
    def _analyze_with_context(self, text: str, context: str) -> Dict[str, Any]:
        """Analyze text with context using Gemini."""
        prompt = f"""
        Context: {context}
        
        Analyze this text and provide insights:
        {text}
        """
        
        return self._generate_response(prompt)
        
    def _check_serp_api(self) -> bool:
        """Check if SERP API is available."""
        return GoogleSearch is not None and hasattr(self, 'serp_api_key') and self.serp_api_key

    def process_with_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process hotel-related queries with context.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response with hotel information
        """
        try:
            user_input = input_data.get('user_input', '')
            context = input_data.get('context', {})
            entities = input_data.get('entities', {})
            history = input_data.get('history', [])
            
            logging.info(f"HotelAgent processing input with context: {user_input}")
            
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
            
            # Add conversation history for context
            if history and len(history) > 0:
                enhanced_prompt += "\nLịch sử trò chuyện gần đây:\n"
                recent_history = history[-5:] if len(history) >= 5 else history
                for message in recent_history:
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    enhanced_prompt += f"{role.capitalize()}: {content}\n"
            
            # Add user query
            enhanced_prompt += f"\nUser: {user_input}"
            
            # Generate response using Gemini
            logging.info("HotelAgent generating response with context")
            response = self.model.generate_content(enhanced_prompt)
            
            if not response or not hasattr(response, 'text'):
                return {
                    "status": "error",
                    "message": "Không thể tìm thông tin khách sạn. Vui lòng thử lại."
                }
                
            logging.info(f"HotelAgent response with context: {response.text[:100]}...")
            return {
                "status": "success",
                "content": response.text
            }
                
        except Exception as e:
            logging.error(f"HotelAgent error in process_with_context: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            } 