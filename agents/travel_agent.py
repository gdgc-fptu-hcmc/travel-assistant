from .base_agent import BaseAgent
import logging
import os
import google.generativeai as genai
import time
import re
import requests
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

        # Initialize Google Maps API
        self.google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.google_maps_api_key:
            logging.warning("GOOGLE_MAPS_API_KEY not found in environment variables")
        
        # Initialize Google Cloud credentials
        try:
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not credentials_path:
                raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")
            
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Initialize Travel Partner API client
            self.travel_service = build('travelpartner', 'v1', credentials=self.credentials)
            print("Successfully initialized Travel Partner API client")
            
        except Exception as e:
            logging.error(f"Error initializing Google Cloud credentials: {str(e)}")
            self.credentials = None
            self.travel_service = None
        
        # API endpoints
        self.places_api_url = "https://maps.googleapis.com/maps/api/place"
        self.geocoding_api_url = "https://maps.googleapis.com/maps/api/geocode/json"

        # City name mappings
        self.city_mappings = {
            # Vietnam cities
            'hcm': 'Ho Chi Minh City',
            'hanoi': 'Hanoi',
            'danang': 'Da Nang',
            'nhatrang': 'Nha Trang',
            'phuquoc': 'Phu Quoc',
            'dalat': 'Da Lat',
            'haiphong': 'Hai Phong',
            'cantho': 'Can Tho',
            'hue': 'Hue',
            'quynhon': 'Quy Nhon',
            
            # International cities
            'bangkok': 'Bangkok',
            'singapore': 'Singapore',
            'tokyo': 'Tokyo',
            'seoul': 'Seoul',
            'taipei': 'Taipei',
            'hongkong': 'Hong Kong',
            'kualalumpur': 'Kuala Lumpur',
            'jakarta': 'Jakarta',
            'manila': 'Manila',
            'sydney': 'Sydney'
        }

    def get_hotel_booking_info(self, location: str, check_in: str = None, check_out: str = None) -> Dict[str, Any]:
        """Get hotel information using Google Places API."""
        if not self.google_maps_api_key:
            return {"status": "error", "message": "Google Maps API key not configured"}

        try:
            # Set default dates if not provided
            if not check_in:
                check_in = datetime.now().strftime("%Y-%m-%d")
            if not check_out:
                check_out = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            # Map Vietnamese city names to English for better geocoding
            vietnam_cities = {
                "Hồ Chí Minh": "Ho Chi Minh City, Vietnam",
                "Hà Nội": "Hanoi, Vietnam",
                "Đà Nẵng": "Da Nang, Vietnam",
                "Hải Phòng": "Hai Phong, Vietnam",
                "Cần Thơ": "Can Tho, Vietnam",
                "Nha Trang": "Nha Trang, Vietnam",
                "Đà Lạt": "Da Lat, Vietnam",
                "Phú Quốc": "Phu Quoc, Vietnam",
                "Huế": "Hue, Vietnam"
            }

            # Map international cities
            international_cities = {
                "Tokyo": "Tokyo, Japan",
                "Seoul": "Seoul, South Korea",
                "Bangkok": "Bangkok, Thailand",
                "Singapore": "Singapore",
                "Kuala Lumpur": "Kuala Lumpur, Malaysia",
                "Hong Kong": "Hong Kong",
                "Taipei": "Taipei, Taiwan",
                "Manila": "Manila, Philippines",
                "Jakarta": "Jakarta, Indonesia",
                "Sydney": "Sydney, Australia",
                "Melbourne": "Melbourne, Australia",
                "London": "London, UK",
                "Paris": "Paris, France",
                "New York": "New York, USA",
                "Los Angeles": "Los Angeles, USA",
                "San Francisco": "San Francisco, USA",
                "Las Vegas": "Las Vegas, USA",
                "Chicago": "Chicago, USA",
                "Miami": "Miami, USA",
                "Dubai": "Dubai, UAE",
                "Rome": "Rome, Italy",
                "Barcelona": "Barcelona, Spain",
                "Amsterdam": "Amsterdam, Netherlands",
                "Berlin": "Berlin, Germany",
                "Vienna": "Vienna, Austria",
                "Prague": "Prague, Czech Republic",
                "Budapest": "Budapest, Hungary",
                "Istanbul": "Istanbul, Turkey",
                "Cairo": "Cairo, Egypt",
                "Cape Town": "Cape Town, South Africa",
                "Mumbai": "Mumbai, India",
                "Delhi": "Delhi, India",
                "Shanghai": "Shanghai, China",
                "Beijing": "Beijing, China",
                "Seoul": "Seoul, South Korea",
                "Osaka": "Osaka, Japan",
                "Fukuoka": "Fukuoka, Japan",
                "Busan": "Busan, South Korea",
                "Phuket": "Phuket, Thailand",
                "Bali": "Bali, Indonesia",
                "Penang": "Penang, Malaysia",
                "Macau": "Macau",
                "Manila": "Manila, Philippines",
                "Hanoi": "Hanoi, Vietnam",
                "Ho Chi Minh City": "Ho Chi Minh City, Vietnam",
                "Da Nang": "Da Nang, Vietnam"
            }

            # Combine all mappings
            city_mapping = {**vietnam_cities, **international_cities}

            # Use mapped name if available, otherwise use original location
            search_location = city_mapping.get(location, location)

            # Get location coordinates first
            geocode_params = {
                "address": search_location,
                "key": self.google_maps_api_key
            }
            geocode_response = requests.get(self.geocoding_api_url, params=geocode_params)
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()

            if not geocode_data.get("results"):
                return {"status": "error", "message": f"Location {location} not found"}

            # Get nearby hotels using Places API
            location = geocode_data["results"][0]["geometry"]["location"]
            nearby_params = {
                "location": f"{location['lat']},{location['lng']}",
                "radius": 5000,  # 5km radius
                "type": "lodging",  # Search for hotels
                "key": self.google_maps_api_key
            }
            nearby_response = requests.get(f"{self.places_api_url}/nearbysearch/json", params=nearby_params)
            nearby_response.raise_for_status()
            hotels_data = nearby_response.json()

            # Get detailed information for each hotel
            hotels_info = []
            for hotel in hotels_data.get("results", [])[:5]:  # Limit to 5 hotels
                place_id = hotel["place_id"]
                details_params = {
                    "place_id": place_id,
                    "fields": "name,formatted_address,rating,user_ratings_total,price_level,formatted_phone_number,website,opening_hours,reviews",
                    "key": self.google_maps_api_key
                }
                details_response = requests.get(f"{self.places_api_url}/details/json", params=details_params)
                details_response.raise_for_status()
                hotel_details = details_response.json().get("result", {})
                
                # Convert price level to actual price range
                price_level = hotel_details.get("price_level", 0)
                price_range = {
                    0: "Chưa có thông tin",
                    1: "Giá rẻ",
                    2: "Giá trung bình",
                    3: "Giá cao",
                    4: "Giá rất cao"
                }.get(price_level, "Chưa có thông tin")
                
                hotels_info.append({
                    "name": hotel_details.get("name"),
                    "address": hotel_details.get("formatted_address"),
                    "rating": hotel_details.get("rating"),
                    "total_ratings": hotel_details.get("user_ratings_total"),
                    "price_range": price_range,
                    "phone": hotel_details.get("formatted_phone_number"),
                    "website": hotel_details.get("website"),
                    "opening_hours": hotel_details.get("opening_hours", {}).get("weekday_text", []),
                    "reviews": hotel_details.get("reviews", [])[:3]  # Get top 3 reviews
                })

            return {
                "status": "success",
                "booking_info": {
                    "check_in": check_in,
                    "check_out": check_out,
                    "hotels": hotels_info
                }
            }
        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling Google Places API: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_place_info(self, location: str) -> Dict[str, Any]:
        """Get place information using Google Maps API."""
        if not self.google_maps_api_key:
            return {"status": "error", "message": "Google Maps API key not configured"}

        try:
            # First, get coordinates for the location
            geocode_params = {
                "address": location,
                "key": self.google_maps_api_key
            }
            geocode_response = requests.get(self.geocoding_api_url, params=geocode_params)
            geocode_response.raise_for_status()
            geocode_data = geocode_response.json()

            if not geocode_data.get("results"):
                return {"status": "error", "message": f"Location {location} not found"}

            # Get place details
            place_id = geocode_data["results"][0]["place_id"]
            place_params = {
                "place_id": place_id,
                "fields": "name,formatted_address,rating,user_ratings_total,types,photos,reviews,opening_hours,price_level,website,formatted_phone_number",
                "key": self.google_maps_api_key
            }
            place_response = requests.get(f"{self.places_api_url}/details/json", params=place_params)
            place_response.raise_for_status()
            place_data = place_response.json()

            # Get nearby places
            location = geocode_data["results"][0]["geometry"]["location"]
            nearby_params = {
                "location": f"{location['lat']},{location['lng']}",
                "radius": 5000,  # 5km radius
                "type": "tourist_attraction",
                "key": self.google_maps_api_key
            }
            nearby_response = requests.get(f"{self.places_api_url}/nearbysearch/json", params=nearby_params)
            nearby_response.raise_for_status()
            nearby_data = nearby_response.json()

            # Get hotel booking information
            booking_info = self.get_hotel_booking_info(location)

            return {
                "status": "success",
                "place": place_data.get("result", {}),
                "nearby_places": nearby_data.get("results", []),
                "booking_info": booking_info.get("booking_info", {})
            }
        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling Google Maps API: {str(e)}")
            return {"status": "error", "message": str(e)}

    def process(self, user_input: str) -> dict:
        """Process user input and generate travel recommendations."""
        try:
            if not user_input:
                return {
                    'status': 'error',
                    'message': 'No input provided'
                }

            # Extract location from input
            location = self._extract_location(user_input)
            if not location:
                return {
                    'status': 'error',
                    'message': 'Could not identify location from input'
                }

            # Get place information
            place_info = self.get_place_info(location)
            
            # Get hotel information
            hotel_info = self.get_hotel_booking_info(location)

            # Build prompt for Gemini
            prompt = f"""Based on the following information about {location}, provide travel recommendations:
            Place Information: {place_info}
            Hotel Information: {hotel_info}
            
            Please provide a comprehensive travel guide in Vietnamese including:
            1. Popular attractions
            2. Best time to visit
            3. Local transportation
            4. Food recommendations
            5. Cultural tips
            
            Use emojis to make the response more engaging.
            """

            # Generate response
            response = self.model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text'):
                return {
                    'status': 'error',
                    'message': 'Failed to generate response'
                }

            return {
                'status': 'success',
                'data': {
                    'location': location,
                    'place_info': place_info,
                    'hotel_info': hotel_info,
                    'recommendations': response.text
                }
            }

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def process_with_context(self, input_data: dict) -> dict:
        """Process user input with context."""
        try:
            # Extract query from input data
            if isinstance(input_data, dict):
                query = input_data.get('query', '')
                if not query:
                    return {
                        'status': 'error',
                        'message': 'No query provided in input data'
                    }
            else:
                return {
                    'status': 'error',
                    'message': 'Input data must be a dictionary'
                }

            # Process the query
            response = self.process(query)
            
            # Add context information if available
            if isinstance(input_data, dict):
                context = input_data.get('context', {})
                if context:
                    response['context'] = context
                    
            return response
            
        except Exception as e:
            logger.error(f"Error in process_with_context: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location name from text."""
        try:
            # Check if text is a known city code
            text_lower = text.lower().strip()
            if text_lower in self.city_mappings:
                return self.city_mappings[text_lower]
            
            # Use Gemini to extract location
            prompt = f"Extract the main location or city name from this text: {text}"
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                location = response.text.strip()
                # Check if extracted location is in our mappings
                location_lower = location.lower()
                if location_lower in self.city_mappings:
                    return self.city_mappings[location_lower]
                return location
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting location: {str(e)}")
            return None 