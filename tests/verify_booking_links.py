import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.hotel_rag import HotelRAGAgent

async def verify_booking_links():
    print("🏨 Hotel Booking Links Verification")
    print("=" * 50)
    
    agent = HotelRAGAgent()
    
    # Test cases (Real hotels used in MetadataGenerator)
    test_cases = [
        ("The Shilla Seoul", "Seoul"),
        ("Ritz Paris", "Paris"),
        ("The Plaza", "New York"),
        ("Sofitel Ambassador Seoul", "Seoul") # User reported issue case
    ]
    
    for hotel_name, location in test_cases:
        print(f"\nTesting: {hotel_name} ({location})")
        links = agent._generate_booking_links(hotel_name, location)
        
        # Verify only google_hotels exists
        if len(links) != 1 or "google_hotels" not in links:
            print(f"  ❌ Error: Expected only 'google_hotels', found {list(links.keys())}")
        else:
            print(f"  ✅ Link generated: {links['google_hotels']}")
            
    print("\n" + "=" * 50)
    print("💰 Price Categorization Verification")
    print("=" * 50)
    
    price_test_cases = [
        ({"hotel_name": "The Shilla Seoul", "review_snippet": "Good stay"}, "High"), # Name based
        ({"hotel_name": "Youth Hostel", "review_snippet": "Cheap"}, "Low"), # Name based
        ({"hotel_name": "Unknown Hotel", "review_snippet": "This is a luxury hotel"}, "High"), # Review based
        ({"hotel_name": "Unknown Hotel", "review_snippet": "Cheap and affordable"}, "Low"), # Review based
        ({"hotel_name": "Unknown Hotel", "review_snippet": "Just okay"}, "Medium") # Default
    ]
    
    for input_data, expected in price_test_cases:
        estimated = agent._estimate_price_range(input_data)
        if estimated == expected:
            print(f"  ✅ Correct: {input_data['hotel_name']} / '{input_data['review_snippet']}' -> {estimated}")
        else:
            print(f"  ❌ Failed: {input_data['hotel_name']} -> Expected {expected}, Got {estimated}")

    print("\n" + "=" * 50)
    print("✅ Verification Complete")

if __name__ == "__main__":
    asyncio.run(verify_booking_links())
