import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import hashlib
import json
from functools import lru_cache
import requests

try:
    from python_dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed. Please run: pip install python-dotenv")
    load_dotenv = lambda: None

# Load environment variables
load_dotenv()

# Try to import required packages
try:
    import google.generativeai as genai
except ImportError:
    print("Warning: Google Generative AI not installed. Please run: pip install google-generativeai")
    genai = None

try:
    from serpapi.google_search import GoogleSearch
except ImportError:
    print("Warning: Google Search Results not installed. Please run: pip install google-search-results")
    GoogleSearch = None

class BaseAgent:
    SUPPORTED_MODELS = {
        'gemini': {
            'name': 'gemini-pro',
            'provider': 'google',
            'max_tokens': 1024,
            'temperature': 0.7
        },
        'claude': {
            'name': 'claude-3-opus-20240229',
            'provider': 'anthropic',
            'max_tokens': 4096,
            'temperature': 0.7
        },
        'gpt4': {
            'name': 'gpt-4-turbo-preview',
            'provider': 'openai',
            'max_tokens': 4096,
            'temperature': 0.7
        }
    }

    def __init__(self, model_type: str = 'gemini'):
        """Initialize base agent with AI model configuration."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize model
        self.model_type = model_type
        self.model = self._initialize_model(model_type)
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize cache
        self._cache = {}
        self._cache_ttl = 3600  # Cache TTL in seconds

        # External APIs flag - specific agents will override if needed
        self.uses_external_apis = False
        
    def _initialize_model(self, model_type: str):
        """Initialize the selected AI model."""
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model type: {model_type}")
            
        model_config = self.SUPPORTED_MODELS[model_type]
        self.logger.info(f"Initializing {model_type} model: {model_config['name']}")
        
        if model_type == 'gemini':
            return self._initialize_gemini(model_config)
        elif model_type == 'claude':
            return self._initialize_claude(model_config)
        elif model_type == 'gpt4':
            return self._initialize_gpt4(model_config)
            
    def _initialize_gemini(self, config: Dict[str, Any]):
        """Initialize Google Gemini model."""
        if not genai:
            raise ImportError("Google Generative AI package not installed")
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
            
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(
            config['name'],
            generation_config={
                "temperature": config['temperature'],
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": config['max_tokens'],
            }
        )
        
    def _initialize_claude(self, config: Dict[str, Any]):
        """Initialize Anthropic Claude model."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        return {
            'api_key': api_key,
            'config': config
        }
        
    def _initialize_gpt4(self, config: Dict[str, Any]):
        """Initialize OpenAI GPT-4 model."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        return {
            'api_key': api_key,
            'config': config
        }

    def _get_cache_key(self, prompt: str) -> str:
        """Generate a cache key for the prompt."""
        return hashlib.md5(prompt.encode()).hexdigest()
        
    def _get_from_cache(self, prompt: str) -> Dict[str, Any]:
        """Get response from cache if available and not expired."""
        cache_key = self._get_cache_key(prompt)
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if time.time() - cache_entry['timestamp'] < self._cache_ttl:
                self.logger.info("Cache hit for prompt")
                return cache_entry['response']
        return None
        
    def _save_to_cache(self, prompt: str, response: Dict[str, Any]):
        """Save response to cache."""
        cache_key = self._get_cache_key(prompt)
        self._cache[cache_key] = {
            'response': response,
            'timestamp': time.time()
        }
        
    def process(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and generate a response.
        To be implemented by child classes.
        """
        raise NotImplementedError("Child classes must implement process method")
    
    def process_with_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user input with additional context and history.
        
        Args:
            input_data (Dict): Dictionary containing user_input, context, entities, history
            
        Returns:
            Dict: Response from the agent
        """
        user_input = input_data.get('user_input', '')
        context = input_data.get('context', {})
        entities = input_data.get('entities', {})
        history = input_data.get('history', [])
        
        # Tạo prompt với context
        prompt = self._create_context_prompt(user_input, context, entities, history)
        
        # Generate response
        response = self._generate_response(prompt)
        
        # Format response
        result = {
            "status": response.get("status", "error"),
            "content": response.get("content", ""),
            "timestamp": response.get("timestamp", datetime.now().isoformat())
        }
        
        return result
        
    def _create_context_prompt(self, user_input: str, context: Dict[str, Any], 
                              entities: Dict[str, Any], history: List) -> str:
        """
        Create a prompt with context for the model.
        
        Args:
            user_input (str): User's question
            context (Dict): Context information
            entities (Dict): Extracted entities
            history (List): Conversation history
            
        Returns:
            str: Formatted prompt with context
        """
        prompt_parts = []
        
        # Add role definition
        prompt_parts.append(f"Bạn là {self.__class__.__name__}, một trợ lý thông minh về du lịch.")
        prompt_parts.append("Nhiệm vụ của bạn là cung cấp thông tin chính xác và hữu ích về các chủ đề du lịch.")
        prompt_parts.append("Hãy trả lời ngắn gọn, súc tích, đầy đủ thông tin và đúng trọng tâm.")
        
        # Add context
        if context:
            prompt_parts.append("\nThông tin ngữ cảnh:")
            
            # Add locations
            if context.get('locations'):
                locations = ", ".join(context['locations'])
                prompt_parts.append(f"- Địa điểm đã đề cập: {locations}")
                
            # Add dates
            if context.get('dates'):
                dates = ", ".join(context['dates'])
                prompt_parts.append(f"- Thời gian đã đề cập: {dates}")
                
            # Add supporting info from other agents
            if context.get('supporting_info'):
                supporting_info = context['supporting_info']
                if isinstance(supporting_info, dict) and supporting_info.get('content'):
                    prompt_parts.append(f"- Thông tin bổ sung: {supporting_info['content']}")
        
        # Add conversation history (last 3 messages)
        if history and len(history) > 0:
            prompt_parts.append("\nLịch sử hội thoại gần đây:")
            recent_history = history[-3:] if len(history) > 3 else history
            for message in recent_history:
                role = message.get('role', 'unknown')
                content = message.get('content', '')
                prompt_parts.append(f"- {role.capitalize()}: {content}")
        
        # Add current question
        prompt_parts.append(f"\nCâu hỏi của người dùng: {user_input}")
        
        # Add instruction for response
        prompt_parts.append("\nHãy cung cấp thông tin chính xác, đầy đủ và đúng trọng tâm. Trả lời bằng tiếng Việt.")
        
        return "\n".join(prompt_parts)
    
    def _check_serp_api(self) -> bool:
        """Check if SERP API is available."""
        if GoogleSearch is None:
            print("Error: Google Search Results is not installed. Please run: pip install google-search-results")
            return False
        return True
    
    def _check_gemini(self) -> bool:
        """Check if Gemini is available."""
        if genai is None:
            print("Error: Google Generative AI is not installed. Please run: pip install google-generativeai")
            return False
        return True
    
    async def call_other_agent(self, agent_name: str, query: str) -> Dict[str, Any]:
        """
        Call another agent and get its response.
        
        Args:
            agent_name (str): Name of the agent to call
            query (str): Query to send to the agent
            
        Returns:
            Dict: Response from the other agent
        """
        # To be implemented when integration with AgentManager is established
        # This is just a placeholder for the method signature
        return {
            "status": "error",
            "message": "Method not implemented yet",
            "agent": self.__class__.__name__
        }
    
    def format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format the response in a standard way."""
        return {
            "status": "success",
            "data": data,
            "agent": self.__class__.__name__
        }

    def _generate_response(self, prompt: str) -> Dict[str, Any]:
        """Generate a response using the selected AI model."""
        # Check cache first
        cached_response = self._get_from_cache(prompt)
        if cached_response:
            return cached_response
            
        max_retries = 3
        base_delay = 42
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Generating response for prompt (attempt {attempt + 1}/{max_retries})")
                
                if self.model_type == 'gemini':
                    response = self._generate_gemini_response(prompt)
                elif self.model_type == 'claude':
                    response = self._generate_claude_response(prompt)
                elif self.model_type == 'gpt4':
                    response = self._generate_gpt4_response(prompt)
                    
                if response and 'content' in response:
                    # Save to cache
                    self._save_to_cache(prompt, response)
                    
                    # Add to conversation history
                    self._add_to_history(prompt, response['content'])
                    
                    return response
                else:
                    raise ValueError(f"Invalid response from {self.model_type} API")
                    
            except Exception as e:
                error_str = str(e)
                self.logger.error(f"Error generating response (attempt {attempt + 1}/{max_retries}): {error_str}")
                
                # Check if it's a rate limit error
                if "429" in error_str and ("quota" in error_str.lower() or "rate" in error_str.lower()):
                    if attempt < max_retries - 1:
                        delay = base_delay * (attempt + 1)  # Exponential backoff
                        self.logger.warning(f"Rate limit hit. Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                        continue
                
                return {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
    def _generate_gemini_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using Gemini."""
        response = self.model.generate_content(prompt)
        return {
            "status": "success",
            "content": response.text,
            "timestamp": datetime.now().isoformat()
        }
        
    def _generate_claude_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using Claude."""
        headers = {
            "x-api-key": self.model['api_key'],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model['config']['name'],
            "prompt": prompt,
            "max_tokens_to_sample": self.model['config']['max_tokens'],
            "temperature": self.model['config']['temperature']
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/complete",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "content": response.json()['completion'],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(f"Claude API error: {response.text}")
            
    def _generate_gpt4_response(self, prompt: str) -> Dict[str, Any]:
        """Generate response using GPT-4."""
        headers = {
            "Authorization": f"Bearer {self.model['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model['config']['name'],
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.model['config']['max_tokens'],
            "temperature": self.model['config']['temperature']
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "content": response.json()['choices'][0]['message']['content'],
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception(f"GPT-4 API error: {response.text}")
    
    def _format_conversation_history(self) -> str:
        if not self.conversation_history:
            return "No previous conversation."
        
        formatted = []
        for entry in self.conversation_history[-5:]:  # Keep last 5 exchanges
            formatted.append(f"User: {entry['prompt']}")
            formatted.append(f"Assistant: {entry['response']}")
        return "\n".join(formatted)
    
    def _add_to_history(self, prompt: str, response: str):
        """Add a conversation exchange to history."""
        self.conversation_history.append({
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    
    def _extract_entities(self, text: str, entity_type: str) -> List[str]:
        if not self._check_gemini():
            return []
            
        prompt = f"""
        As {self.name}, {self.description}
        Extract all {entity_type} from the following text. Return only the list of {entity_type}, one per line:
        
        {text}
        """
        
        response = self._generate_response(prompt)
        if response["status"] == "success":
            return [line.strip() for line in response["content"].split("\n") if line.strip()]
        return []
    
    def _summarize_text(self, text: str) -> str:
        """Summarize text using Gemini."""
        if not self._check_gemini():
            return "Error: Google Generative AI is not available"
            
        prompt = f"Summarize the following text concisely:\n\n{text}"
        response = self._generate_response(prompt)
        return response["content"] if response["status"] == "success" else "Error generating summary"
    
    def _analyze_with_context(self, text: str, context: str) -> Dict[str, Any]:
        """Analyze text with context using Gemini."""
        if not self._check_gemini():
            return {
                "status": "error",
                "message": "Google Generative AI is not available"
            }
            
        prompt = f"""
        Context: {context}
        
        Analyze the following text and provide insights:
        {text}
        """
        return self._generate_response(prompt)
    
    def collaborate(self, other_agent: 'BaseAgent', query: str) -> Dict[str, Any]:
        """Enable agent collaboration through MCP"""
        if not self._check_gemini():
            return {
                "status": "error",
                "message": "Google Generative AI is not available"
            }
            
        prompt = f"""
        As {self.name}, {self.description}
        Collaborate with {other_agent.name} ({other_agent.description}) to address:
        
        {query}
        
        Please provide a coordinated response that combines both agents' expertise.
        """
        
        return self._generate_response(prompt)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Return agent's capabilities and description"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": [
                "Natural language understanding",
                "Context-aware responses",
                "Entity extraction",
                "Text summarization",
                "Collaborative problem solving"
            ],
            "model": self.model.name if hasattr(self, 'model') else None
        } 