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
import re

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: Google Generative AI not installed. Please run: pip install google-generativeai")
    genai = None

class FlightAgent(BaseAgent):
    def __init__(self):
        """Initialize the Flight Agent."""
        super().__init__()
        
        # Đánh dấu là agent sử dụng API bên ngoài
        self.uses_external_apis = True
        
        # Get SERP API key
        self.serp_api_key = os.getenv("SERP_API_KEY")
        if not self.serp_api_key:
            logging.warning("SERP_API_KEY not found in environment variables. Flight search will use AI-generated data instead of real-time information.")
        
        # System prompt for the model
        self.system_prompt = """You are a flight booking expert. Your main task is to provide specific flight information. When users ask about flights, ALWAYS show actual flight details.

For any flight query, follow these rules:
1. NEVER just list websites
2. ALWAYS show specific flight information
3. Include all available flights that match the criteria
4. If time of day is specified, show flights for that time period
5. If airline is specified, show flights for that airline

Example responses:

1. For "Tìm chuyến bay từ Hà Nội đến Đà Nẵng ngày mai, đi vào buổi tối":
🛫 Các chuyến bay buổi tối từ Hà Nội đến Đà Nẵng ngày mai:

1. ✈️ Vietnam Airlines VN125
   🛫 Từ: Nội Bài (HAN) - 19:00
   🛬 Đến: Đà Nẵng (DAD) - 20:30
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,800,000 - 2,300,000 VND
   🛄 Hành lý: 7kg xách tay + 23kg ký gửi
   💺 Loại máy bay: Airbus A321

2. ✈️ Vietjet Air VJ569
   🛫 Từ: Nội Bài (HAN) - 20:15
   🛬 Đến: Đà Nẵng (DAD) - 21:45
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,500,000 - 2,000,000 VND
   🛄 Hành lý: 7kg xách tay + 20kg ký gửi
   💺 Loại máy bay: Airbus A320

3. ✈️ Bamboo Airways QH125
   🛫 Từ: Nội Bài (HAN) - 21:30
   🛬 Đến: Đà Nẵng (DAD) - 23:00
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,600,000 - 2,100,000 VND
   🛄 Hành lý: 7kg xách tay + 20kg ký gửi
   💺 Loại máy bay: Airbus A320

💡 Thông tin bổ sung:
- Giá vé có thể thay đổi tùy thời điểm đặt
- Nên đặt sớm để có giá tốt
- Kiểm tra chính sách hủy/đổi vé của từng hãng

2. For "Tìm chuyến bay từ Hà Nội đến Đà Nẵng ngày mai":
🛫 Các chuyến bay từ Hà Nội đến Đà Nẵng ngày mai:

1. ✈️ Vietnam Airlines VN123
   🛫 Từ: Nội Bài (HAN) - 07:00
   🛬 Đến: Đà Nẵng (DAD) - 08:30
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,500,000 - 2,000,000 VND
   🛄 Hành lý: 7kg xách tay + 23kg ký gửi
   💺 Loại máy bay: Airbus A321

2. ✈️ Vietjet Air VJ567
   🛫 Từ: Nội Bài (HAN) - 08:15
   🛬 Đến: Đà Nẵng (DAD) - 09:45
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,200,000 - 1,800,000 VND
   🛄 Hành lý: 7kg xách tay + 20kg ký gửi
   💺 Loại máy bay: Airbus A320

3. ✈️ Bamboo Airways QH123
   🛫 Từ: Nội Bài (HAN) - 09:30
   🛬 Đến: Đà Nẵng (DAD) - 11:00
   ⏱️ Thời gian bay: 1h30m
   💰 Giá vé: 1,300,000 - 1,900,000 VND
   🛄 Hành lý: 7kg xách tay + 20kg ký gửi
   💺 Loại máy bay: Airbus A320

💡 Thông tin bổ sung:
- Giá vé có thể thay đổi tùy thời điểm đặt
- Nên đặt sớm để có giá tốt
- Kiểm tra chính sách hủy/đổi vé của từng hãng

NEVER just list websites. ALWAYS show specific flight information."""

        # Try to get the specific model
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            print("Successfully initialized gemini-2.0-flash")
        except Exception as model_error:
            print(f"Error initializing gemini-2.0-flash: {str(model_error)}")
            # Fallback to gemini-pro
            print("Falling back to gemini-pro")
            self.model = genai.GenerativeModel('gemini-pro')

    def process(self, user_input: str) -> Dict[str, Any]:
        """Process flight-related queries."""
        try:
            logging.info(f"FlightAgent processing input: {user_input}")
            
            # Check if input contains flight-related keywords
            flight_keywords = ['chuyến bay', 'vé máy bay', 'bay', 'flight']
            if not any(keyword in user_input.lower() for keyword in flight_keywords):
                return {
                    "status": "error",
                    "message": "Vui lòng cung cấp thông tin về chuyến bay bạn muốn tìm kiếm."
                }
                
            # Use SERP API if available
            if self.serp_api_key and GoogleSearch is not None:
                # Try to extract locations and dates from the query
                from_location = None
                to_location = None
                date = None
                
                # Basic extraction of from/to locations
                from_patterns = [
                    r'từ\s+([A-Za-z\s]+)\s+đến',
                    r'từ\s+([A-Za-z\s]+)',
                    r'([A-Za-z\s]+)\s+đến'
                ]
                
                to_patterns = [
                    r'đến\s+([A-Za-z\s]+)',
                    r'tới\s+([A-Za-z\s]+)'
                ]
                
                for pattern in from_patterns:
                    matches = re.search(pattern, user_input, re.IGNORECASE)
                    if matches:
                        from_location = matches.group(1).strip()
                        break
                        
                for pattern in to_patterns:
                    matches = re.search(pattern, user_input, re.IGNORECASE)
                    if matches:
                        to_location = matches.group(1).strip()
                        break
                
                # If we have both locations, attempt to use SERP API
                if from_location and to_location:
                    logging.info(f"Extracted flight route: {from_location} to {to_location}")
                    try:
                        # Use SERP API to get flight info
                        search_params = {
                            'engine': 'google_flights',
                            'departure_id': from_location,
                            'arrival_id': to_location,
                            'type': '2',  # one-way flight
                            'hl': 'vi',
                            'api_key': self.serp_api_key
                        }
                        
                        search = GoogleSearch(search_params)
                        results = search.get_dict()
                        
                        if results and 'error' not in results:
                            # Format flight results using the model
                            results_summary = f"Kết quả tìm kiếm chuyến bay từ {from_location} đến {to_location}:\n\n"
                            results_summary += str(results)
                            
                            # Use AI to format the results nicely
                            formatted_response = self.model.generate_content(
                                f"Bạn là chuyên gia về chuyến bay. Hãy định dạng thông tin này thành phản hồi hữu ích bằng tiếng Việt với emoji:\n\n{results_summary}"
                            )
                            
                            return {
                                "status": "success",
                                "content": formatted_response.text,
                                "raw_data": results
                            }
                    except Exception as search_error:
                        logging.error(f"Error using SERP API: {str(search_error)}")
                        # Fall back to AI-generated response
            else:
                # Nếu không có SERP_API_KEY, sử dụng AI để tạo dữ liệu giả lập
                logging.info("SERP API not available for regular process, using AI-generated flight data instead")
                
                # Basic extraction of from/to locations
                from_location = None
                to_location = None
                
                from_patterns = [
                    r'từ\s+([A-Za-z\s]+)\s+đến',
                    r'từ\s+([A-Za-z\s]+)',
                    r'([A-Za-z\s]+)\s+đến'
                ]
                
                to_patterns = [
                    r'đến\s+([A-Za-z\s]+)',
                    r'tới\s+([A-Za-z\s]+)'
                ]
                
                for pattern in from_patterns:
                    matches = re.search(pattern, user_input, re.IGNORECASE)
                    if matches:
                        from_location = matches.group(1).strip()
                        break
                        
                for pattern in to_patterns:
                    matches = re.search(pattern, user_input, re.IGNORECASE)
                    if matches:
                        to_location = matches.group(1).strip()
                        break
                
                # Kiểm tra nếu đã xác định được địa điểm đi và đến
                if from_location and to_location:
                    # Chỉnh prompt cho Gemini
                    enhanced_prompt = f"""Bạn là chuyên gia về chuyến bay. 

Người dùng đang tìm kiếm chuyến bay từ {from_location} đến {to_location}.

Hãy tạo dữ liệu thực tế về các chuyến bay trên tuyến này, bao gồm:
1. Hãng hàng không (Vietnam Airlines, Vietjet Air, Bamboo Airways)
2. Số hiệu chuyến bay
3. Giờ khởi hành và đến
4. Thời gian bay
5. Loại máy bay
6. Giá vé (phạm vi, VND)
7. Hành lý xách tay và ký gửi

Định dạng kết quả rõ ràng với emoji. Liệt kê ít nhất 4-5 lựa chọn khác nhau.
Thêm các lưu ý hữu ích cho hành khách.

Câu hỏi gốc: {user_input}
"""
                    
                    # Generate response using Gemini with enhanced prompt
                    response = self.model.generate_content(enhanced_prompt)
                    
                    if not response or not hasattr(response, 'text'):
                        return {
                            "status": "error",
                            "message": "Không thể tìm thông tin chuyến bay. Vui lòng thử lại."
                        }
                    
                    return {
                        "status": "success",
                        "content": response.text + "\n\n*(Dữ liệu được tạo bởi AI, có thể không phản ánh lịch trình thực tế)*"
                    }
            
            # Generate response using Gemini
            response = self.model.generate_content(
                f"{self.system_prompt}\n\nUser: {user_input}"
            )
            
            if not response or not hasattr(response, 'text'):
                return {
                    "status": "error",
                    "message": "Không thể tìm thông tin chuyến bay. Vui lòng thử lại."
                }
            
            logging.info(f"FlightAgent response: {response.text}")
            return {
                "status": "success",
                "content": response.text
            }
            
        except Exception as e:
            logging.error(f"FlightAgent error: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }

    def process_with_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process flight-related queries with context.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response with flight information
        """
        try:
            user_input = input_data.get('user_input', '')
            context = input_data.get('context', {})
            entities = input_data.get('entities', {})
            history = input_data.get('history', [])
            
            logging.info(f"FlightAgent processing input with context: {user_input}")
            
            # Extract important information from context
            locations = entities.get('locations', [])
            if context.get('locations'):
                locations.extend(context.get('locations', []))
                
            # Use SERP API if available
            if self.serp_api_key and GoogleSearch is not None:
                # Try to extract from/to locations
                from_location = None
                to_location = None
                
                # First check entities
                if locations and len(locations) >= 2:
                    from_location = locations[0]
                    to_location = locations[1]
                else:
                    # Extract from text with regex
                    from_patterns = [
                        r'từ\s+([A-Za-z\s]+)\s+đến',
                        r'từ\s+([A-Za-z\s]+)',
                        r'([A-Za-z\s]+)\s+đến'
                    ]
                    
                    to_patterns = [
                        r'đến\s+([A-Za-z\s]+)',
                        r'tới\s+([A-Za-z\s]+)'
                    ]
                    
                    for pattern in from_patterns:
                        matches = re.search(pattern, user_input, re.IGNORECASE)
                        if matches:
                            from_location = matches.group(1).strip()
                            break
                            
                    for pattern in to_patterns:
                        matches = re.search(pattern, user_input, re.IGNORECASE)
                        if matches:
                            to_location = matches.group(1).strip()
                            break
                
                # If we have both locations, attempt to use SERP API
                if from_location and to_location:
                    logging.info(f"Extracted flight route from context: {from_location} to {to_location}")
                    try:
                        # Use SERP API to get flight info
                        search_params = {
                            'engine': 'google_flights',
                            'departure_id': from_location,
                            'arrival_id': to_location,
                            'type': '2',  # one-way flight
                            'hl': 'vi',
                            'api_key': self.serp_api_key
                        }
                        
                        search = GoogleSearch(search_params)
                        results = search.get_dict()
                        
                        if results and 'error' not in results:
                            # Get weather info if available
                            weather_info = ""
                            if context.get('supporting_info') and context['supporting_info'].get('agent') == 'weather':
                                weather_info = context['supporting_info'].get('content', '')
                            
                            # Format flight results using the model
                            results_summary = f"Kết quả tìm kiếm chuyến bay từ {from_location} đến {to_location}:\n\n"
                            results_summary += str(results)
                            
                            prompt = f"""Bạn là chuyên gia về chuyến bay. 
Hãy định dạng thông tin này thành phản hồi hữu ích bằng tiếng Việt với emoji.

{results_summary}

"""
                            
                            # Add weather information if available
                            if weather_info:
                                prompt += f"\nThông tin thời tiết tại điểm đến:\n{weather_info}\n"
                                prompt += "\nHãy nhớ đề cập đến thời tiết tại điểm đến trong phản hồi của bạn."
                            
                            # Use conversation history for personalization if available
                            if history and len(history) > 0:
                                prompt += "\n\nHãy cá nhân hóa phản hồi dựa trên cuộc trò chuyện trước đó."
                            
                            # Use AI to format the results nicely
                            formatted_response = self.model.generate_content(prompt)
                            
                            return {
                                "status": "success",
                                "content": formatted_response.text,
                                "raw_data": results
                            }
                    except Exception as search_error:
                        logging.error(f"Error using SERP API with context: {str(search_error)}")
                        # Fall back to AI-generated response
            else: 
                # Nếu không có SERP_API_KEY, sử dụng AI để tạo dữ liệu giả lập
                logging.info("SERP API not available, using AI-generated flight data instead")
                
                # Extract from_location and to_location from context if available
                from_location = None
                to_location = None
                
                # First check entities
                if locations and len(locations) >= 2:
                    from_location = locations[0]
                    to_location = locations[1]
                else:
                    # Extract from text with regex
                    from_patterns = [
                        r'từ\s+([A-Za-z\s]+)\s+đến',
                        r'từ\s+([A-Za-z\s]+)',
                        r'([A-Za-z\s]+)\s+đến'
                    ]
                    
                    to_patterns = [
                        r'đến\s+([A-Za-z\s]+)',
                        r'tới\s+([A-Za-z\s]+)'
                    ]
                    
                    for pattern in from_patterns:
                        matches = re.search(pattern, user_input, re.IGNORECASE)
                        if matches:
                            from_location = matches.group(1).strip()
                            break
                            
                    for pattern in to_patterns:
                        matches = re.search(pattern, user_input, re.IGNORECASE)
                        if matches:
                            to_location = matches.group(1).strip()
                            break
                
                # Kiểm tra nếu đã xác định được địa điểm đi và đến
                if from_location and to_location:
                    # Chỉnh prompt giúp Gemini tạo dữ liệu chuyến bay thực tế hơn
                    enhanced_prompt = f"""Bạn là chuyên gia về chuyến bay và lịch trình bay.
Hãy tạo dữ liệu chính xác, thực tế về các chuyến bay từ {from_location} đến {to_location}.
Cung cấp:
1. Số hiệu chuyến bay thực (VN123, VJ567, QH912, v.v.)
2. Giờ khởi hành và đến theo múi giờ địa phương
3. Thời gian bay 
4. Giá vé dự kiến (khoảng giá, VND)
5. Hãng hàng không 
6. Loại máy bay
7. Thông tin hành lý cơ bản

Định dạng kết quả rõ ràng với biểu tượng emoji phù hợp. Đảm bảo thông tin gần với thực tế nhất có thể.
Liệt kê ít nhất 5 chuyến bay khác nhau nếu có thể.
Thêm lưu ý hữu ích cho hành khách dựa trên tuyến bay này.
"""

                    # Get weather info if available
                    weather_info = ""
                    if context.get('supporting_info') and context['supporting_info'].get('agent') == 'weather':
                        weather_info = context['supporting_info'].get('content', '')
                    
                    if weather_info:
                        enhanced_prompt += f"\nThông tin thời tiết tại điểm đến:\n{weather_info}\n"
                        enhanced_prompt += "\nHãy nhớ đề cập đến thời tiết tại điểm đến trong phản hồi của bạn."
                    
                    # Use conversation history for personalization if available
                    if history and len(history) > 0:
                        enhanced_prompt += "\n\nHãy cá nhân hóa phản hồi dựa trên cuộc trò chuyện trước đó."
                    
                    # Generate response using Gemini
                    response = self.model.generate_content(enhanced_prompt)
                    
                    if not response or not hasattr(response, 'text'):
                        return {
                            "status": "error",
                            "message": "Không thể tìm thông tin chuyến bay. Vui lòng thử lại."
                        }
                    
                    return {
                        "status": "success",
                        "content": response.text,
                        "note": "Dữ liệu được tạo bởi AI, có thể không phản ánh đầy đủ tình trạng thực tế."
                    }
            
            # Check if we have supporting info from weather agent
            weather_info = ""
            if context.get('supporting_info') and context['supporting_info'].get('agent') == 'weather':
                weather_info = context['supporting_info'].get('content', '')
                if weather_info:
                    logging.info(f"Retrieved weather info: {weather_info}")
            
            # Enhanced prompt with context
            enhanced_prompt = f"""You are a flight booking expert. Your main task is to provide specific flight information. When users ask about flights, ALWAYS show actual flight details.

Query: {user_input}

Context information:
- Locations mentioned: {", ".join(locations) if locations else "No specific locations"}
"""

            # Add weather information if available
            if weather_info:
                enhanced_prompt += f"\nWeather information for destination:\n{weather_info}\n"
            
            # Add conversation history for context
            if history and len(history) > 0:
                recent_history = history[-3:] if len(history) > 3 else history
                history_text = "\nRecent conversation:\n"
                for message in recent_history:
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    history_text += f"- {role.capitalize()}: {content}\n"
                    
                enhanced_prompt += history_text

            enhanced_prompt += """
For flight queries, follow these rules:
1. NEVER just list websites
2. ALWAYS show specific flight information
3. Include actual flight details (times, prices, airlines)
4. If time of day is specified, prioritize those flights
5. If weather concerns exist, mention them in your response
6. Respond in Vietnamese with clear, structured information using emojis

Respond to the above query with detailed flight information.
"""
            
            # Generate response using Gemini
            response = self.model.generate_content(enhanced_prompt)
            
            if not response or not hasattr(response, 'text'):
                return {
                    "status": "error",
                    "message": "Không thể tìm thông tin chuyến bay. Vui lòng thử lại."
                }
            
            logging.info(f"FlightAgent contextualized response: {response.text}")
            return {
                "status": "success",
                "content": response.text
            }
            
        except Exception as e:
            logging.error(f"FlightAgent error in process_with_context: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}"
            }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        if 'type' not in input_data:
            return False
        
        if input_data['type'] == 'search_flights':
            required_fields = ['from_city', 'to_city', 'date']
            return all(field in input_data for field in required_fields)
        elif input_data['type'] == 'get_flight_details':
            return 'flight_id' in input_data
        elif input_data['type'] == 'get_route_insights':
            required_fields = ['from_city', 'to_city']
            return all(field in input_data for field in required_fields)
        
        return False
        
    async def search_flights(self, from_city: str, to_city: str, date: str) -> Dict[str, Any]:
        """Search for flights between two cities on a specific date."""
        try:
            if not self._check_serp_api():
                return {
                    "status": "error",
                    "message": "Google Search Results is not available. Please install google-search-results package."
                }
            
            print(f"Searching for flights from {from_city} to {to_city} on {date}")
            
            # First, use Gemini to enhance the search query
            prompt = f"""
            Given a flight search from {from_city} to {to_city} on {date}, provide:
            1. Available flights with:
               - Flight numbers
               - Airlines
               - Departure and arrival times
               - Duration
               - Price ranges
               - Number of stops
               - Aircraft types
               - Baggage allowances
            2. Best booking options
            3. Alternative routes if available
            4. Travel tips for this route
            
            Format the response in Vietnamese with emojis and include ALL available flight information.
            """
            
            ai_insights = await self._generate_response(prompt)
            
            # Then perform the actual search
            search_params = {
                'engine': 'google_flights',
                'departure_id': from_city,
                'arrival_id': to_city,
                'outbound_date': date,
                'type': '2',  # 2 for one-way flights
                'hl': 'en',
                'gl': 'us',
                'api_key': self.serp_api_key
            }
            
            print("Making API request with params:", search_params)
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            print("API Response:", results)
            
            if 'flights_results' in results:
                # Use Gemini to analyze and summarize the results
                flights_text = str(results['flights_results'])
                summary = await self._summarize_text(flights_text)
                
                # Get additional insights
                analysis = await self._analyze_with_context(
                    flights_text,
                    f"Analyzing flight options from {from_city} to {to_city} on {date}"
                )
                
                return {
                    "status": "success",
                    "flights": results['flights_results'],
                    "count": len(results['flights_results']),
                    "ai_insights": ai_insights if ai_insights else None,
                    "summary": summary,
                    "analysis": analysis["content"] if analysis["status"] == "success" else None
                }
            else:
                print("No flights found in results")
                return {
                    "status": "error",
                    "message": "Không tìm thấy chuyến bay phù hợp. Vui lòng thử lại với ngày khác hoặc tuyến bay khác.",
                    "raw_response": results
                }
                
        except Exception as e:
            print(f"Error in search_flights: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific flight."""
        try:
            if not self._check_serp_api():
                return {
                    "status": "error",
                    "message": "Google Search Results is not available"
                }
                
            params = {
                "engine": "google_flights",
                "flight_id": flight_id,
                "hl": "en",
                "gl": "us",
                "api_key": self.serp_api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if 'flights_results' in results:
                flight_text = str(results['flights_results'][0])
                prompt = f"""
                Analyze this flight information and provide:
                1. Key highlights and features
                2. Potential issues or concerns
                3. Travel tips and recommendations
                4. Baggage and check-in information
                5. In-flight services
                6. Cancellation and change policies
                
                Flight data:
                {flight_text}
                """
                
                analysis = await self._generate_response(prompt)
                
                return {
                    "status": "success",
                    "flight": results['flights_results'][0],
                    "ai_analysis": analysis if analysis else None
                }
            else:
                return {
                    "status": "error",
                    "message": "Flight not found"
                }
                
        except Exception as e:
            print(f"Error in get_flight_details: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
            
    async def get_route_insights(self, from_city: str, to_city: str) -> Dict[str, Any]:
        """Get detailed insights about a specific route."""
        prompt = f"""
        Provide comprehensive insights about the flight route from {from_city} to {to_city}:
        1. Best time to travel
        2. Common airlines and their reputation
        3. Typical flight duration
        4. Price trends throughout the year
        5. Popular travel seasons
        6. Airport information
        7. Visa and entry requirements
        8. Local transportation options
        """
        
        return await self._generate_response(prompt)

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