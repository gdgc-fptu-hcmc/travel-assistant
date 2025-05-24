import os
from dotenv import load_dotenv
from agents.agent_manager import AgentManager

def test_multi_agent():
    # Load environment variables
    load_dotenv()
    
    # Initialize AgentManager
    manager = AgentManager()
    
    # Test cases for different agents
    test_queries = [
        # Flight queries
        "Tìm chuyến bay từ Hà Nội đến Đà Nẵng ngày mai",
        "Giá vé máy bay từ Sài Gòn đến Hà Nội tháng 7",
        
        # Hotel queries
        "Khách sạn 5 sao ở Đà Nẵng gần biển",
        "Đặt phòng khách sạn ở Hồ Chí Minh giá rẻ",
        
        # Place queries
        "Địa điểm du lịch nổi tiếng ở Hà Nội",
        "Nhà hàng ngon ở Đà Nẵng",
        
        # Weather queries
        "Thời tiết ở Hồ Chí Minh tuần này",
        "Dự báo thời tiết Đà Nẵng tháng 7",
        
        # Food queries
        "Món ăn đặc sản ở Hà Nội",
        "Quán ăn ngon ở Sài Gòn"
    ]
    
    print("=== Testing Multi-Agent System ===\n")
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        print("-" * 50)
        
        # Test basic processing
        response = manager.process(query)
        print("\nResponse:")
        print(f"Agent: {response.get('agent', 'unknown')}")
        print(f"Status: {response.get('status', 'unknown')}")
        print(f"Content: {response.get('content', response.get('message', 'No content'))}")
        
        # Test with context
        context_data = {
            "user_input": query,
            "context": {
                "locations": ["Hà Nội", "Đà Nẵng", "Hồ Chí Minh"],
                "dates": ["2024-07-01", "2024-07-07"]
            },
            "entities": {},
            "history": []
        }
        
        context_response = manager.process(query, conversation_history=[context_data])
        print("\nContext Response:")
        print(f"Agent: {context_response.get('agent', 'unknown')}")
        print(f"Status: {context_response.get('status', 'unknown')}")
        print(f"Content: {context_response.get('content', context_response.get('message', 'No content'))}")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    test_multi_agent() 