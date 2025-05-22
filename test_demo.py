import asyncio
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.place_agent import PlaceAgent
import json
from datetime import datetime, timedelta

def print_json(data):
    """Print JSON data in a formatted way"""
    print(json.dumps(data, indent=2))

async def test_flight_search():
    """Test flight search functionality"""
    print("\n=== Testing Flight Search ===")
    agent = FlightAgent()
    
    # Test flight search with realistic data
    result = await agent.process({
        "type": "search_flights",
        "from_city": "SGN",  # Ho Chi Minh City
        "to_city": "HAN",    # Hanoi
        "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # Next week
    })
    
    print("\nFlight Search Results:")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Found {result.get('count', 0)} flights")
        if result.get('flights'):
            print("\nSample Flight Details:")
            sample_flight = result['flights'][0]
            print(f"Airline: {sample_flight.get('airline', 'N/A')}")
            print(f"Departure: {sample_flight.get('departure_time', 'N/A')}")
            print(f"Arrival: {sample_flight.get('arrival_time', 'N/A')}")
            print(f"Price: {sample_flight.get('price', 'N/A')}")
        print("\nAI Insights:")
        print(result.get('ai_insights'))
        print("\nSummary:")
        print(result.get('summary'))
    else:
        print(f"Error: {result.get('message')}")

async def test_hotel_search():
    """Test hotel search functionality"""
    print("\n=== Testing Hotel Search ===")
    agent = HotelAgent()
    
    # Test hotel search with realistic data
    check_in = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    result = await agent.process({
        "type": "search_hotels",
        "city": "Ho Chi Minh City",
        "check_in": check_in,
        "check_out": check_out,
        "guests": 2,
        "room_type": "double"
    })
    
    print("\nHotel Search Results:")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Found {result.get('count', 0)} hotels")
        if result.get('hotels'):
            print("\nSample Hotel Details:")
            sample_hotel = result['hotels'][0]
            print(f"Name: {sample_hotel.get('name', 'N/A')}")
            print(f"Location: {sample_hotel.get('location', 'N/A')}")
            print(f"Price per night: {sample_hotel.get('price', 'N/A')}")
            print(f"Rating: {sample_hotel.get('rating', 'N/A')}")
        print("\nAI Insights:")
        print(result.get('ai_insights'))
        print("\nSummary:")
        print(result.get('summary'))
    else:
        print(f"Error: {result.get('message')}")

async def test_place_search():
    """Test place search functionality"""
    print("\n=== Testing Place Search ===")
    agent = PlaceAgent()
    
    # Test place search with realistic data
    result = await agent.process({
        "type": "search_places",
        "city": "Ho Chi Minh City",
        "query": "historical landmarks",
        "category": "attractions",
        "max_results": 5
    })
    
    print("\nPlace Search Results:")
    print(f"Status: {result.get('status')}")
    if result.get('status') == 'success':
        print(f"Found {result.get('count', 0)} places")
        if result.get('places'):
            print("\nSample Places:")
            for place in result['places'][:3]:  # Show first 3 places
                print(f"\nName: {place.get('title', 'N/A')}")
                print(f"Description: {place.get('snippet', 'N/A')}")
                print(f"Rating: {place.get('rating', 'N/A')}")
        print("\nAI Insights:")
        print(result.get('ai_insights'))
        print("\nSummary:")
        print(result.get('summary'))
    else:
        print(f"Error: {result.get('message')}")

async def test_agent_collaboration():
    """Test collaboration between agents"""
    print("\n=== Testing Agent Collaboration ===")
    flight_agent = FlightAgent()
    hotel_agent = HotelAgent()
    place_agent = PlaceAgent()
    
    # Test collaboration with realistic trip planning
    check_in = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    check_out = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    
    print("\nPlanning a 3-day trip to Ho Chi Minh City from Hanoi...")
    
    print("\n1. Flight Options:")
    flight_result = await flight_agent.process({
        "type": "search_flights",
        "from_city": "HAN",
        "to_city": "SGN",
        "date": check_in
    })
    if flight_result.get('status') == 'success':
        print("Available flights found!")
        print(flight_result.get('ai_insights'))
    else:
        print(f"Flight search error: {flight_result.get('message')}")
    
    print("\n2. Hotel Options:")
    hotel_result = await hotel_agent.process({
        "type": "search_hotels",
        "city": "Ho Chi Minh City",
        "check_in": check_in,
        "check_out": check_out,
        "guests": 2,
        "room_type": "double"
    })
    if hotel_result.get('status') == 'success':
        print("Available hotels found!")
        print(hotel_result.get('ai_insights'))
    else:
        print(f"Hotel search error: {hotel_result.get('message')}")
    
    print("\n3. Places to Visit:")
    place_result = await place_agent.process({
        "type": "search_places",
        "city": "Ho Chi Minh City",
        "query": "top attractions",
        "category": "attractions",
        "max_results": 5
    })
    if place_result.get('status') == 'success':
        print("Recommended places found!")
        print(place_result.get('ai_insights'))
    else:
        print(f"Place search error: {place_result.get('message')}")

async def main():
    """Main test function"""
    print("Starting Travel Assistant Demo...")
    print("Current date:", datetime.now().strftime("%Y-%m-%d"))
    
    try:
        # Test individual agents
        await test_flight_search()
        await test_hotel_search()
        await test_place_search()
        
        # Test agent collaboration
        await test_agent_collaboration()
        
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        print("Please check your API keys and internet connection.")

if __name__ == "__main__":
    asyncio.run(main())