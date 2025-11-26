import asyncio
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from config/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", ".env"))
load_dotenv(env_path)

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.query_parser import QueryParserAgent
from src.agents.hotel_rag import HotelRAGAgent
from src.agents.weather_tool import WeatherToolAgent
from src.core.state import StateManager, ConversationState

async def run_custom_query():
    print("🚀 Running Custom Query Test")
    print("=" * 50)
    
    query = "서울에서 조용하고 낭만적인 호텔 추천해줘. 12월 15일부터 3일간 여행이야."
    print(f"Query: {query}")
    
    # Initialize agents
    query_parser = QueryParserAgent()
    hotel_agent = HotelRAGAgent()
    weather_agent = WeatherToolAgent()
    
    # 1. Parse Query
    print("\n1. Parsing Query...")
    state = StateManager.create_initial_state("test_session", query)
    state = await query_parser.parse(state)
    
    # 2. Search Hotels
    print("2. Searching Hotels...")
    search_params = {
        'destination': state['destination'],
        'preferences': state['preferences'],
        'budget': state['preferences'].get('budget_range') if state['preferences'] else None
    }
    hotels = await hotel_agent.search(search_params)
    
    # 3. Get Weather
    print("3. Getting Weather...")
    weather = []
    if state['destination'] and state['dates']:
        weather = await weather_agent.get_forecast(
            state['destination'], 
            state['dates']
        )
    
    # 4. Format Output
    output = {
        "query": query,
        "parsed_state": {
            "destination": state['destination'],
            "dates": state['dates'],
            "preferences": state['preferences']
        },
        "hotels": [
            {
                "name": h.name,
                "location": h.location,
                "rating": h.rating,
                "price": h.price_range,
                "highlights": h.review_highlights,
                "booking_links": h.booking_links
            } for h in hotels
        ],
        "weather": [w.model_dump() for w in weather],
        "generated_at": datetime.now().isoformat()
    }
    
    # Save to log
    log_path = "logs/test5.log"
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Results saved to {log_path}")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(run_custom_query())
