from serpapi.google_search import GoogleSearch
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_flight_search():
    try:
        # Test flight search
        params = {
            "engine": "google_flights",
            "q": "flights from Ho Chi Minh City to Hanoi",
            "hl": "en",
            "gl": "us",
            "api_key": os.getenv('SERP_API_KEY')
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print("Flight Search Test Successful!")
        if 'flights_results' in results:
            print(f"Found {len(results['flights_results'])} flights")
            # Print first flight details
            if results['flights_results']:
                first_flight = results['flights_results'][0]
                print("\nSample Flight Details:")
                print(json.dumps(first_flight, indent=2))
        return True
    except Exception as error:
        print("Error:", error)
        return False

def test_hotel_search():
    try:
        # Test hotel search
        params = {
            "engine": "google_hotels",
            "q": "hotels in Hanoi",
            "hl": "en",
            "gl": "us",
            "api_key": os.getenv('SERP_API_KEY')
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print("Hotel Search Test Successful!")
        if 'hotels_results' in results:
            print(f"Found {len(results['hotels_results'])} hotels")
            # Print first hotel details
            if results['hotels_results']:
                first_hotel = results['hotels_results'][0]
                print("\nSample Hotel Details:")
                print(json.dumps(first_hotel, indent=2))
        return True
    except Exception as error:
        print("Error:", error)
        return False

def test_place_search():
    try:
        # Test place search
        params = {
            "engine": "google",
            "q": "tourist attractions in Hanoi",
            "hl": "en",
            "gl": "us",
            "api_key": os.getenv('SERP_API_KEY')
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print("Place Search Test Successful!")
        if 'local_results' in results:
            print(f"Found {len(results['local_results'])} places")
            # Print first place details
            if results['local_results']:
                first_place = results['local_results'][0]
                print("\nSample Place Details:")
                print(json.dumps(first_place, indent=2))
        return True
    except Exception as error:
        print("Error:", error)
        return False

if __name__ == "__main__":
    print("Testing SERP API Connection...")
    
    print("\nTesting Flight Search:")
    flight_test = test_flight_search()
    
    print("\nTesting Hotel Search:")
    hotel_test = test_hotel_search()
    
    print("\nTesting Place Search:")
    place_test = test_place_search()
    
    if flight_test and hotel_test and place_test:
        print("\nAll tests passed! Your SERP API is working correctly.")
    else:
        print("\nSome tests failed. Please check your API credentials and try again.") 