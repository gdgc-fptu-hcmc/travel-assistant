# Smart Travel Assistant System

A multi-agent travel planning system built with Vertex AI Agent Builder that helps users plan their trips efficiently.

## Features

- Trip planning by date/city
- Hotel search (name, price, location)
- Tourist attraction reviews
- Flight ticket search
- Public transportation information
- Total trip cost calculation
- Currency conversion
- Cost summary display

## System Architecture

The system consists of multiple specialized agents:

- FlightAgent: Handles flight searches and bookings
- HotelAgent: Manages hotel searches and bookings
- ReviewAgent: Provides tourist attraction reviews
- CurrencyAgent: Handles currency conversions
- PublicTransportAgent: Manages public transportation information
- CostAgent: Calculates total trip costs
- SummaryAgent: Generates trip summaries

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

3. Run the application:
```bash
python app.py
```

## API Documentation

The system provides RESTful APIs for each agent's functionality. Detailed API documentation can be found in the `/docs` directory.

## Deployment

The system is designed to be deployed on Google Cloud Platform (GCP) using Gemini AI and App Engine.

## Free APIs Used

- OpenTripMap API for tourist attractions
- OpenWeatherMap API for weather information
- ExchangeRate-API for currency conversion
- Public Transport APIs (varies by city) 
