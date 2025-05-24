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
from dotenv import load_dotenv

class PlaceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Place Agent",
            description="A travel assistant that helps users find and explore places"
        )
        self.conversation_history = []
        
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
        
        load_dotenv()
        self.api_key = os.getenv('PLACE_API_KEY')
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return results."""
        try:
            if 'type' not in input_data:
                return {
                    "status": "error",
                    "message": "Missing 'type' in input data"
                }
            
            if input_data['type'] == 'search_places':
                return self.search_places(
                    input_data.get('city'),
                    input_data.get('query')
                )
            elif input_data['type'] == 'get_place_details':
                return self.get_place_details(input_data.get('place_id'))
            elif input_data['type'] == 'get_city_insights':
                return self.get_city_insights(input_data.get('city'))
            else:
                return {
                    "status": "error",
                    "message": f"Unknown operation type: {input_data['type']}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        if 'type' not in input_data:
            return False
        
        if input_data['type'] == 'search_places':
            required_fields = ['city', 'query']
            return all(field in input_data for field in required_fields)
        elif input_data['type'] == 'get_place_details':
            return 'place_id' in input_data
        elif input_data['type'] == 'get_city_insights':
            return 'city' in input_data
        
        return False
        
    def search_places(self, city: str, query: str) -> Dict[str, Any]:
        try:
            if not self._check_serp_api():
                return {
                    "status": "error",
                    "message": "Google Search Results is not available. Please install google-search-results package."
                }
                
            # First, use Gemini to enhance the search query
            prompt = f"""
            Given a search for {query} in {city}, provide:
            1. Popular categories of places
            2. Best times to visit
            3. Local tips and recommendations
            4. Cultural considerations
            5. Transportation options
            6. Safety information
            7. Photography spots
            8. Hidden gems
            """
            
            ai_insights = self._generate_response(prompt)
            
            # Then perform the actual search
            params = {
                "engine": "google",
                "q": f"{query} in {city}",
                "hl": "en",
                "gl": "us",
                "api_key": self.serp_api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if 'organic_results' in results:
                # Use Gemini to analyze and summarize the results
                places_text = str(results['organic_results'])
                summary = self._summarize_text(places_text)
                
                # Get additional insights
                analysis = self._analyze_with_context(
                    places_text,
                    f"Analyzing {query} in {city}"
                )
                
                return {
                    "status": "success",
                    "places": results['organic_results'],
                    "count": len(results['organic_results']),
                    "ai_insights": ai_insights["content"] if ai_insights["status"] == "success" else None,
                    "summary": summary,
                    "analysis": analysis["content"] if analysis["status"] == "success" else None
                }
            else:
                return {
                    "status": "error",
                    "message": "No places found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        try:
            if not Client:
                return {
                    "status": "error",
                    "message": "SERP API client not available. Please install serpapi package."
                }
                
            params = {
                "engine": "google",
                "q": f"place {place_id}",
                "hl": "en",
                "gl": "us",
                "api_key": self.serp_api_key
            }
            
            client = Client(params)
            results = client.search()
            
            if 'organic_results' in results:
                # Use Gemini to analyze the place details
                place_text = str(results['organic_results'][0])
                prompt = f"""
                Analyze this place information and provide:
                1. Key attractions and features
                2. Best times to visit
                3. Visitor tips and recommendations
                4. Cultural significance
                5. Photography opportunities
                6. Nearby attractions
                7. Local customs and etiquette
                8. Accessibility information
                
                Place data:
                {place_text}
                """
                
                analysis = self._generate_response(prompt)
                
                return {
                    "status": "success",
                    "place": results['organic_results'][0],
                    "ai_analysis": analysis["content"] if analysis["status"] == "success" else None
                }
            else:
                return {
                    "status": "error",
                    "message": "Place not found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
            
    def get_city_insights(self, city: str) -> Dict[str, Any]:
        """Get detailed insights about a city"""
        prompt = f"""
        Provide comprehensive insights about {city}:
        1. Best time to visit
        2. Local culture and customs
        3. Transportation system
        4. Safety and security
        5. Popular neighborhoods
        6. Local cuisine
        7. Shopping areas
        8. Nightlife and entertainment
        9. Day trips and excursions
        10. Local events and festivals
        """
        
        return self._generate_response(prompt)

    async def _generate_response(self, prompt):
        """Generate a response using Gemini."""
        if not self.model:
            print("Gemini model not initialized")
            return None
            
        try:
            print(f"Generating response for prompt: {prompt[:100]}...")
            response = self.model.generate_content(prompt)
            if response and hasattr(response, 'text'):
                print(f"Generated response: {response.text[:100]}...")
                return response.text
            else:
                print("No response text found in response object")
                return None
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None

    def process_place(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process place-related queries
        """
        query = data.get('query', '').lower()
        
        # Example response structure
        response = {
            'status': 'success',
            'message': f'Processing place query: {query}',
            'data': {
                'query': query,
                'type': 'place',
                'suggestions': []
            }
        }
        
        # Add place-specific logic here
        if 'tourist' in query or 'attraction' in query:
            response['data']['suggestions'].append('Finding popular tourist attractions...')
        elif 'restaurant' in query or 'food' in query:
            response['data']['suggestions'].append('Searching for local restaurants...')
        elif 'shopping' in query or 'mall' in query:
            response['data']['suggestions'].append('Looking for shopping destinations...')
        elif 'museum' in query or 'art' in query:
            response['data']['suggestions'].append('Finding cultural attractions...')
            
        return response 