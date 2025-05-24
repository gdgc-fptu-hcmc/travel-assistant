import re
import logging
from typing import Dict, List, Any, Optional
from .travel_agent import TravelAgent
from .weather_agent import WeatherAgent
from .food_agent import FoodAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from .place_agent import PlaceAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        """Initialize the agent manager with all available agents"""
        self.agents = {
            'flight': FlightAgent(),
            'hotel': HotelAgent(),
            'place': PlaceAgent(),
            'food': FoodAgent(),
            'weather': WeatherAgent()
        }
        
        # Lưu trữ session data
        self.sessions = {}
        
        # Define keywords for each agent
        self.keywords = {
            'weather': ['weather', 'climate', 'temperature', 'rain', 'sunny', 'forecast', 
                       'mưa', 'nắng', 'nhiệt độ', 'thời tiết', 'khí hậu', 'dự báo'],
            'food': ['food', 'restaurant', 'cuisine', 'dish', 'eat', 'dinner', 'lunch', 'breakfast',
                    'ăn', 'nhà hàng', 'món', 'đồ ăn', 'ẩm thực', 'quán', 'tiệm'],
            'travel': ['travel', 'trip', 'visit', 'tour', 'destination', 'place', 'attraction',
                      'du lịch', 'thăm', 'đi', 'đến', 'địa điểm', 'thắng cảnh'],
            'flight': ['flight', 'airplane', 'airline', 'ticket', 'book', 'reserve', 'airport',
                      'máy bay', 'vé', 'đặt vé', 'chuyến bay', 'hãng hàng không', 'sân bay'],
            'hotel': ['hotel', 'accommodation', 'room', 'book', 'reserve', 'stay', 'lodge',
                     'khách sạn', 'phòng', 'đặt phòng', 'nghỉ', 'lưu trú', 'resort']
        }

    def _detect_agent(self, user_input: str, conversation_history: List[Dict] = None) -> str:
        """
        Detect which agent should handle the user input based on keywords and conversation context.
        Returns the agent name or 'travel' as default.
        """
        user_input = user_input.lower()
        
        # Count keyword matches for each agent
        scores = {}
        for agent, keywords in self.keywords.items():
            score = sum(1 for keyword in keywords if keyword in user_input)
            scores[agent] = score
        
        # Phân tích ngữ cảnh từ lịch sử hội thoại
        if conversation_history:
            # Phân tích 3 tin nhắn gần nhất để tìm context
            recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
            
            context_agents = []
            for message in recent_messages:
                if message.get('agent') and message.get('agent') != 'manager':
                    context_agents.append(message.get('agent'))
            
            # Nếu có agent xuất hiện nhiều trong lịch sử, tăng điểm cho agent đó
            for agent in context_agents:
                if agent in scores:
                    scores[agent] += 0.5  # Tăng điểm dựa trên context
        
        # Return agent with highest score, or 'travel' if no matches
        best_agent = max(scores.items(), key=lambda x: x[1])
        return best_agent[0] if best_agent[1] > 0 else 'travel'

    def process(self, input_data, conversation_history=None):
        """
        Process input data by routing it to the appropriate agent
        """
        try:
            # Determine which agent to use based on input
            agent = self._route_to_agent(input_data)
            logger.info(f"Routing message to {agent.name} agent")
            
            # Process the input with the selected agent
            response = agent.process(input_data, conversation_history)
            return response
            
        except Exception as e:
            logger.error(f"Error in AgentManager: {str(e)}")
            return {
                "agent": "unknown",
                "status": "error",
                "message": f"Error processing request: {str(e)}"
            }
    
    def _route_to_agent(self, input_data):
        """
        Route the input to the appropriate agent based on content
        """
        # Convert input to lowercase for easier matching
        text = input_data.lower()
        
        # Check for flight-related keywords
        if any(keyword in text for keyword in ['chuyến bay', 'vé máy bay', 'bay', 'sân bay']):
            return self.agents['flight']
            
        # Check for hotel-related keywords
        if any(keyword in text for keyword in ['khách sạn', 'đặt phòng', 'phòng', 'resort']):
            return self.agents['hotel']
            
        # Check for place-related keywords
        if any(keyword in text for keyword in ['địa điểm', 'du lịch', 'thăm quan', 'thắng cảnh']):
            return self.agents['place']
            
        # Check for food-related keywords
        if any(keyword in text for keyword in ['nhà hàng', 'quán ăn', 'món ăn', 'đặc sản']):
            return self.agents['food']
            
        # Check for weather-related keywords
        if any(keyword in text for keyword in ['thời tiết', 'nhiệt độ', 'mưa', 'nắng']):
            return self.agents['weather']
            
        # Default to place agent if no specific match
        return self.agents['place']
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Trích xuất các thông tin quan trọng từ câu hỏi"""
        entities = {
            'locations': [],
            'dates': [],
            'keywords': []
        }
        
        # Trích xuất địa điểm
        location_patterns = [
            r'(?:at|in|to|from) ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)',  # English
            r'(?:ở|tại|đến|từ) ([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]+)*)'    # Vietnamese
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            if matches:
                entities['locations'].extend(matches)
        
        # TODO: Bổ sung trích xuất ngày tháng và từ khóa
        
        return entities
    
    def _build_context_from_history(self, history: List) -> Dict[str, Any]:
        """Xây dựng ngữ cảnh từ lịch sử hội thoại"""
        context = {
            'locations': [],
            'dates': [],
            'preferences': []
        }
        
        if not history:
            return context
        
        # Lấy các thông tin quan trọng từ lịch sử
        for message in history:
            if 'entities' in message:
                # Thêm locations từ entities vào context
                if 'locations' in message['entities']:
                    for location in message['entities']['locations']:
                        if location not in context['locations']:
                            context['locations'].append(location)
                
                # Thêm dates từ entities vào context
                if 'dates' in message['entities']:
                    for date in message['entities']['dates']:
                        if date not in context['dates']:
                            context['dates'].append(date)
        
        return context
    
    def _check_required_info(self, agent_name: str, user_input: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Kiểm tra xem có cần thông tin từ agent khác không"""
        result = {
            'needed': False,
            'agent': None,
            'query': None
        }
        
        # Nếu là FlightAgent và không có thông tin về thời tiết
        if agent_name == 'flight' and 'Đà Nẵng' in user_input:
            result['needed'] = True
            result['agent'] = 'weather'
            result['query'] = f"Thời tiết ở Đà Nẵng trong tuần này"
            
            # Ghi log về việc cần bổ sung thông tin thời tiết
            logger.info(f"FlightAgent yêu cầu thông tin thời tiết từ WeatherAgent: {result['query']}")
        
        # Nếu là FoodAgent và không có thông tin về địa điểm
        elif agent_name == 'food' and not entities.get('locations'):
            result['needed'] = False  # Tạm thời không cần thông tin bổ sung
        
        # Kiểm tra xem agent cần hỗ trợ có hỗ trợ API bên ngoài không
        if result['needed'] and result['agent']:
            if result['agent'] in self.agents and hasattr(self.agents[result['agent']], 'uses_external_apis'):
                if self.agents[result['agent']].uses_external_apis:
                    logger.info(f"Supporting agent {result['agent']} uses external APIs")
            
        return result 