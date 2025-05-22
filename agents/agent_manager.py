import re
import logging
from typing import Dict, List, Any, Optional
from .travel_agent import TravelAgent
from .weather_agent import WeatherAgent
from .food_agent import FoodAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent

class AgentManager:
    def __init__(self):
        """Initialize the Agent Manager with all available agents."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('AgentManager')
        
        self.agents = {
            'travel': TravelAgent(),
            'weather': WeatherAgent(),
            'food': FoodAgent(),
            'flight': FlightAgent(),
            'hotel': HotelAgent()
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

    def process(self, user_input: str, session_id: str = None, conversation_history: List = None) -> dict:
        """
        Process user input by routing it to the appropriate agent.
        
        Args:
            user_input (str): The user's message
            session_id (str, optional): Session identifier
            conversation_history (List, optional): Previous conversation history
            
        Returns:
            dict: Response from the selected agent
        """
        try:
            # Khởi tạo dữ liệu session nếu chưa có
            if session_id and session_id not in self.sessions:
                self.sessions[session_id] = {
                    'conversation_history': [],
                    'context': {},
                    'entities': {}
                }
            
            # Sử dụng lịch sử hội thoại từ tham số hoặc từ session
            history = conversation_history
            if not history and session_id and 'conversation_history' in self.sessions[session_id]:
                history = self.sessions[session_id]['conversation_history']
            
            # Tạo context từ lịch sử hội thoại
            context = self._build_context_from_history(history)
            
            # Detect which agent should handle this input
            agent_name = self._detect_agent(user_input, history)
            
            self.logger.info(f"Routing message to {agent_name} agent")
            
            # Trích xuất các thông tin quan trọng từ câu hỏi
            extracted_entities = self._extract_entities(user_input)
            
            # Lưu entities vào session
            if session_id:
                self.sessions[session_id]['entities'].update(extracted_entities)
            
            # Kiểm tra xem có cần thông tin từ agent khác không
            required_info = self._check_required_info(agent_name, user_input, extracted_entities)
            
            # Nếu cần thông tin từ agent khác
            if required_info and required_info['needed']:
                supporting_agent_name = required_info['agent']
                query = required_info['query']
                
                self.logger.info(f"Getting additional information from {supporting_agent_name} agent")
                
                # Gọi agent hỗ trợ để lấy thông tin
                supporting_info = self.agents[supporting_agent_name].process(query)
                
                # Thêm thông tin hỗ trợ vào context
                context['supporting_info'] = supporting_info
            
            # Chuẩn bị input cho agent chính
            agent_input = {
                'user_input': user_input,
                'context': context,
                'entities': extracted_entities,
                'history': history
            }
            
            # Get response from the selected agent with context
            response = self.agents[agent_name].process_with_context(agent_input)
            
            # Add agent info to response
            response['agent'] = agent_name
            
            # Cập nhật lịch sử hội thoại trong session
            if session_id:
                # Thêm câu hỏi và trả lời vào lịch sử
                self.sessions[session_id]['conversation_history'].append({
                    'role': 'user',
                    'content': user_input
                })
                self.sessions[session_id]['conversation_history'].append({
                    'role': 'assistant',
                    'content': response.get('content', ''),
                    'agent': agent_name
                })
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "agent": "manager"
            }
    
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
            self.logger.info(f"FlightAgent yêu cầu thông tin thời tiết từ WeatherAgent: {result['query']}")
        
        # Nếu là FoodAgent và không có thông tin về địa điểm
        elif agent_name == 'food' and not entities.get('locations'):
            result['needed'] = False  # Tạm thời không cần thông tin bổ sung
        
        # Kiểm tra xem agent cần hỗ trợ có hỗ trợ API bên ngoài không
        if result['needed'] and result['agent']:
            if result['agent'] in self.agents and hasattr(self.agents[result['agent']], 'uses_external_apis'):
                if self.agents[result['agent']].uses_external_apis:
                    self.logger.info(f"Supporting agent {result['agent']} uses external APIs")
            
        return result 