import os
import logging
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from dotenv import load_dotenv
from agents.agent_manager import AgentManager
from werkzeug.serving import WSGIRequestHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize agent manager
agent_manager = AgentManager()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())

# Configure WSGI server
WSGIRequestHandler.protocol_version = "HTTP/1.1"

# Store unlocked IPs in a set
unlocked_ips = set()

@app.route("/", methods=["GET"])
def home():
    """Render the home page."""
    return render_template("home.html")

@app.route("/author", methods=["GET"])
def author():
    """Render the author page."""
    return render_template("author.html")

@app.route("/project-docs", methods=["GET"])
def project_docs():
    """Render the project documentation page."""
    return render_template("project_docs.html")

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    user_ip = request.remote_addr
    if user_ip in unlocked_ips:
        # Already unlocked for this IP
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session['conversation_history'] = []
        return render_template("chat.html", contact_email='gdsc.fpt.hcm23@gmail.com')
    if request.method == "POST":
        answer = request.form.get('answer', '').strip().lower()
        if answer == 'gdsc.fpt.hcm23@gmail.com':
            unlocked_ips.add(user_ip)
            flash('Access granted! You can now use the Chat Assistant.', 'success')
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())
                session['conversation_history'] = []
            return render_template("chat.html", contact_email='gdsc.fpt.hcm23@gmail.com')
        else:
            flash('Incorrect answer. Please try again.', 'danger')
    return render_template("chatbot_lock.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat requests."""
    try:
        # Get message from request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_input = data.get("message", "").strip()
        
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Create session_id if not exists
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            session['conversation_history'] = []
        
        session_id = session.get('session_id')
        conversation_history = session.get('conversation_history', [])
        
        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Process user input with agent manager
        try:
            # Pass both session_id and conversation history to agent manager
            response = agent_manager.process(user_input, session_id, conversation_history)
            
            # Add response to history
            conversation_history.append({"role": "assistant", "content": response.get("content", response.get("message", ""))})
            session['conversation_history'] = conversation_history
            
            if response["status"] == "success":
                return jsonify({
                    "response": response.get("content", response.get("message", "")),
                    "agent": response.get("agent", "unknown"),
                    "status": "success"
                })
            else:
                return jsonify({
                    "error": response.get("message", "Unknown error"),
                    "agent": response.get("agent", "unknown"),
                    "status": "error"
                }), 500
                
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            return jsonify({
                "error": "An error occurred while processing your message",
                "details": str(e),
                "agent": "system"
            }), 500

    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "error": "An error occurred while processing your request",
            "details": str(e),
            "agent": "system"
        }), 500

@app.route('/project-idea')
def project_idea():
    return render_template("project_idea.html")

@app.route('/reference-docs')
def reference_docs():
    return render_template("reference_docs.html")

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("405.html"), 405

if __name__ == "__main__":
    # Verify required environment variables
    required_vars = ["GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Check if any agents use external APIs
    uses_external_apis = any(agent.uses_external_apis for agent in agent_manager.agents.values())
    
    # Only warn if there are agents using external APIs
    if uses_external_apis:
        optional_vars = ["SERP_API_KEY"]
        missing_optional = [var for var in optional_vars if not os.getenv(var)]
        if missing_optional:
            logging.warning(f"Missing optional environment variables: {', '.join(missing_optional)}")
            logging.warning("Some advanced features will be limited (real-time flight search)")

    # Run the Flask app with proper socket handling
    app.run(
        debug=True,
        port=5001,
        host='0.0.0.0',
        threaded=True,
        use_reloader=True
    ) 