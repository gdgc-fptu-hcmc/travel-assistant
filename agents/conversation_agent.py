from typing import Dict, Any
from .base_agent import BaseAgent
import json
import os
from dotenv import load_dotenv

load_dotenv()

class ConversationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Conversation Agent",
            description="A travel assistant that helps users plan their trips through natural conversation"
        )
        self.conversation_history = []
        self.fun_facts = [
            "Did you know? The world's shortest commercial flight is just 2 minutes long, between two Scottish islands!",
            "Travel tip: Rolling your clothes instead of folding them saves space in your suitcase!",
            "Fun fact: France is the most visited country in the world.",
            "Did you know? Japan has more than 5 million vending machines!",
            "Travel tip: Always keep a digital copy of your important documents when traveling.",
            "Fun fact: The longest place name in the world is in New Zealand: Taumatawhakatangihangakoauauotamateaturipukakapikimaungahoronukupokaiwhenuakitanatahu!",
            "Did you know? The Great Wall of China is more than 21,000 km long!",
            "Travel tip: Learning a few basic phrases in the local language can make your trip much smoother.",
            "Fun fact: Venice has over 400 bridges!",
            "Did you know? The currency with the highest value is the Kuwaiti Dinar."
        ]
        
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

    async def process(self, input_data):
        try:
            user_input = input_data.get("user_input", "").strip().lower()
            print(f"Processing input: {user_input}")
            
            # Handle greetings and small talk
            if self._is_greeting(user_input):
                return {
                    "status": "success",
                    "message": self._get_greeting_response(),
                    "analysis": {
                        "intent": "greeting",
                        "parameters": {}
                    }
                }
                
            # Handle thank you messages
            if self._is_thank_you(user_input):
                return {
                    "status": "success",
                    "message": "You're welcome! If you need more travel tips, just ask!",
                    "analysis": {
                        "intent": "thank_you",
                        "parameters": {}
                    }
                }
            
            # Store conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Generate response using Gemini
            prompt = self._create_analysis_prompt(user_input)
            try:
                response = await self._generate_response(prompt)
                if response:
                    try:
                        # Try to parse as JSON first
                        print(f"Parsing JSON response: {response[:100]}...")
                        analysis = json.loads(response)
                        self.conversation_history.append({"role": "assistant", "content": response})
                        
                        # If it's a trip planning intent with locations
                        if analysis.get("intent") == "trip_planning" and analysis.get("parameters", {}).get("locations"):
                            locations = analysis["parameters"]["locations"]
                            location_str = ", ".join(locations)
                            return {
                                "status": "success",
                                "message": f"Great choice! I'll help you plan your trip to {location_str}. Would you like to:\n1. Search for flights\n2. Find hotels\n3. Explore places to visit\n4. Get a complete trip plan",
                                "analysis": analysis
                            }
                        elif analysis.get("intent") == "general_conversation":
                            return {
                                "status": "success",
                                "message": "I'd be happy to help you plan your trip! Please tell me which city or country you'd like to visit. For example:\n- Hanoi, Vietnam\n- Paris, France\n- Tokyo, Japan\n- New York, USA",
                                "analysis": analysis
                            }
                        
                        return {
                            "status": "success",
                            "analysis": analysis
                        }
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON response: {str(e)}")
                        print(f"Raw response: {response}")
                        # If not JSON, treat as general conversation
                        return {
                            "status": "success",
                            "message": "I'd be happy to help you plan your trip! Please tell me which city or country you'd like to visit. For example:\n- Hanoi, Vietnam\n- Paris, France\n- Tokyo, Japan\n- New York, USA",
                            "analysis": {
                                "intent": "general_conversation",
                                "parameters": {}
                            }
                        }
                else:
                    # If Gemini response is empty
                    return {
                        "status": "success",
                        "message": "I'd be happy to help you plan your trip! Please tell me which city or country you'd like to visit. For example:\n- Hanoi, Vietnam\n- Paris, France\n- Tokyo, Japan\n- New York, USA",
                        "analysis": {
                            "intent": "general_conversation",
                            "parameters": {}
                        }
                    }
            except Exception as e:
                print(f"Error generating Gemini response: {str(e)}")
                # Fallback to basic response if Gemini fails
                return {
                    "status": "success",
                    "message": "I'd be happy to help you plan your trip! Please tell me which city or country you'd like to visit. For example:\n- Hanoi, Vietnam\n- Paris, France\n- Tokyo, Japan\n- New York, USA",
                    "analysis": {
                        "intent": "general_conversation",
                        "parameters": {}
                    }
                }
                
        except Exception as e:
            print(f"Error in conversation processing: {str(e)}")
            return {
                "status": "error",
                "message": "I'm having trouble understanding. Could you please rephrase that?"
            }
    
    def _is_greeting(self, text):
        greetings = [
            "hi", "hello", "hey", "greetings", "good morning", "good afternoon", 
            "good evening", "howdy", "hi there", "hello there", "hey there",
            "chào", "xin chào", "chào bạn", "chào anh", "chào chị"
        ]
        return any(greeting in text for greeting in greetings)
    
    def _is_thank_you(self, text):
        thank_you_phrases = [
            "thank you", "thanks", "thank you very much", "thanks a lot",
            "cảm ơn", "cảm ơn bạn", "cảm ơn anh", "cảm ơn chị"
        ]
        return any(phrase in text for phrase in thank_you_phrases)
    
    def _get_greeting_response(self):
        import random
        responses = [
            "Hi there! Ready for your next adventure? Ask me anything about travel!",
            "Hello! 🌍 Where would you like to go today? (Tip: {} )".format(random.choice(self.fun_facts)),
            "Hey! I'm here to make your trip awesome. Need a flight, hotel, or a cool place to visit?",
            "Greetings! Did you know? {}".format(random.choice(self.fun_facts)),
            "Hi! Let's plan something amazing together."
        ]
        return random.choice(responses)
    
    def _get_funny_short_response(self):
        import random
        responses = [
            "I'm always here if you want to chat about travel! {}".format(random.choice(self.fun_facts)),
            "Let me know if you need a travel tip or want to discover a new place!",
            "Travel makes you richer in memories! Where to next?",
            "Ask me about flights, hotels, or fun facts!",
            "Did you know? {}".format(random.choice(self.fun_facts))
        ]
        return random.choice(responses)
    
    def _create_analysis_prompt(self, user_input):
        return f"""You are a travel assistant that analyzes user input to identify travel-related information.
        Your task is to ALWAYS return a JSON object in the following format:
        {{
            "intent": "trip_planning" | "general_conversation",
            "parameters": {{
                "locations": ["location1", "location2"],
                "dates": [],
                "preferences": []
            }}
        }}

        Rules:
        1. If the input contains ANY location name, ALWAYS set intent to "trip_planning" and include the location in the locations array
        2. If no location is found, set intent to "general_conversation"
        3. ALWAYS return valid JSON, no other text or explanation
        4. For locations, use the standard city name (e.g., "Hanoi" not "Ha Noi", "Paris" not "Pari")

        Examples of inputs and their expected JSON responses:

        Input: "Hanoi"
        Response: {{"intent": "trip_planning", "parameters": {{"locations": ["Hanoi"], "dates": [], "preferences": []}}}}

        Input: "Paris"
        Response: {{"intent": "trip_planning", "parameters": {{"locations": ["Paris"], "dates": [], "preferences": []}}}}

        Input: "I want to go to Tokyo"
        Response: {{"intent": "trip_planning", "parameters": {{"locations": ["Tokyo"], "dates": [], "preferences": []}}}}

        Input: "Tôi muốn đi Singapore"
        Response: {{"intent": "trip_planning", "parameters": {{"locations": ["Singapore"], "dates": [], "preferences": []}}}}

        Input: "Hi"
        Response: {{"intent": "general_conversation", "parameters": {{"locations": [], "dates": [], "preferences": []}}}}

        Input: "Hello"
        Response: {{"intent": "general_conversation", "parameters": {{"locations": [], "dates": [], "preferences": []}}}}

        Now analyze this input and return ONLY the JSON response:
        {user_input}
        """
    
    async def get_follow_up_questions(self, analysis):
        try:
            intent = analysis["analysis"]["intent"]
            parameters = analysis["analysis"]["parameters"]
            
            if intent == "flight_search":
                missing = []
                if not parameters.get("locations"):
                    missing.append("Where would you like to fly from and to?")
                if not parameters.get("dates"):
                    missing.append("When would you like to travel?")
                return {
                    "status": "success",
                    "content": "To help you find the best flights, I need a few more details:\n" + "\n".join(missing)
                }
                
            elif intent == "hotel_search":
                missing = []
                if not parameters.get("locations"):
                    missing.append("Which city would you like to stay in?")
                if not parameters.get("dates"):
                    missing.append("When would you like to check in and check out?")
                return {
                    "status": "success",
                    "content": "To help you find the perfect hotel, I need some more information:\n" + "\n".join(missing)
                }
                
            elif intent == "place_search":
                if not parameters.get("locations"):
                    return {
                        "status": "success",
                        "content": "Which city or area would you like to explore?"
                    }
                    
            elif intent == "trip_planning":
                return {
                    "status": "success",
                    "content": """I'll help you plan your trip! Please tell me:\n1. Where would you like to go?\n2. When would you like to travel?\n3. How long will you stay?\n4. What are your interests (e.g., culture, food, nature)?\n5. What's your budget range?"""
                }
                
            return {
                "status": "success",
                "content": "Could you please provide more details about what you're looking for?"
            }
            
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            return {
                "status": "error",
                "content": "I'm having trouble understanding. Could you please rephrase your request?"
            }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        return 'user_input' in input_data and isinstance(input_data['user_input'], str)
    
    async def summarize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize the extracted requirements in a user-friendly format."""
        prompt = f"""
        Summarize the following travel requirements in a clear, user-friendly format:
        
        Requirements: {requirements}
        
        Please provide:
        1. A brief summary of the main request
        2. Key details and preferences
        3. Any missing information that needs to be clarified
        """
        
        return self._generate_response(prompt) 