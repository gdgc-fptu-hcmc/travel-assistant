import os
from dotenv import load_dotenv
from agents.travel_agent import TravelAgent

def test_travel_agent():
    # Load environment variables
    load_dotenv()
    
    # Initialize TravelAgent
    agent = TravelAgent()
    
    # Test cases
    test_queries = [
        "Tôi muốn đi du lịch Đà Nẵng vào tháng 7",
        "Khách sạn ở Hồ Chí Minh giá rẻ",
        "Điểm đến phổ biến ở Hà Nội"
    ]
    
    print("=== Testing TravelAgent with Hotel Booking Integration ===\n")
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        print("-" * 50)
        
        # Test basic processing
        response = agent.process(query)
        print("\nBasic Response:")
        print(response.get("message", "No message in response"))
        
        # Test context processing
        context_data = {
            "user_input": query,
            "context": {
                "locations": ["Đà Nẵng", "Hồ Chí Minh", "Hà Nội"],
                "dates": ["2024-07-01", "2024-07-07"]
            },
            "entities": {},
            "history": []
        }
        
        context_response = agent.process_with_context(context_data)
        print("\nContext Response:")
        print(context_response.get("content", "No content in response"))
        
        # Test hotel booking info
        if "location" in response.get("raw_data", {}):
            location = response["raw_data"]["location"]
            print(f"\nTesting hotel booking for: {location}")
            booking_info = agent.get_hotel_booking_info(location)
            print("\nBooking Info:")
            print(booking_info)
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    test_travel_agent() 