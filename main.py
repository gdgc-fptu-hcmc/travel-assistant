from flask import Flask, request, jsonify
from agents.travel_agent import TravelAgent
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
travel_agent = TravelAgent()

@app.route('/api/plan-trip', methods=['POST'])
def plan_trip():
    try:
        data = request.get_json()
        user_input = data.get('query', '')
        
        if not user_input:
            return jsonify({
                'status': 'error',
                'message': 'No query provided'
            }), 400

        # Process the query
        response = travel_agent.process(user_input)
        return jsonify(response)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/hotels', methods=['GET'])
def get_hotels():
    try:
        location = request.args.get('location')
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')

        if not location:
            return jsonify({
                'status': 'error',
                'message': 'Location is required'
            }), 400

        # Get hotel information
        response = travel_agent.get_hotel_booking_info(location, check_in, check_out)
        return jsonify(response)

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 