import os
from datetime import datetime
from agents.flight_agent import FlightAgent
from agents.hotel_agent import HotelAgent
from agents.place_agent import PlaceAgent
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

def print_json(data):
    """Print JSON data in a formatted way"""
    print(json.dumps(data, indent=2))

def test_flight_search():
    """Test flight search functionality."""
    print("\n=== Testing Flight Search ===")
    
    # Initialize FlightAgent
    flight_agent = FlightAgent()
    
    # Test data
    test_input = {
        'type': 'search_flights',
        'from_city': 'SGN',
        'to_city': 'HAN',
        'date': '2025-05-31'
    }
    
    # Process request
    response = flight_agent.process(test_input)
    
    # Print results
    if response['status'] == 'success':
        print("\nFlight Search Results:")
        print(f"From: {response['data']['from_city']}")
        print(f"To: {response['data']['to_city']}")
        print(f"Date: {response['data']['date']}")
        print("\nAvailable Flights:")
        for flight in response['data']['flights']:
            print(f"\nAirline: {flight['airline']}")
            print(f"Flight Number: {flight['flight_number']}")
            print(f"Departure: {flight['departure_time']}")
            print(f"Arrival: {flight['arrival_time']}")
            print(f"Price: {flight['price']}")
    else:
        print(f"\nError: {response['message']}")

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

async def async_main():
    """Async main function."""
    print("Starting Travel Assistant Demo...")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}\n")
    
    try:
        # Test flight search
        test_flight_search()
        
        # Test individual agents
        await test_hotel_search()
        await test_place_search()
        
        # Test agent collaboration
        await test_agent_collaboration()
        
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        print("Please check your API keys and internet connection.")

def main():
    """Main entry point."""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()