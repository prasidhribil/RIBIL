from app.routers.location import parse_nominatim_address

# Test with the actual Nominatim response
nominatim_data = {
    "address": {
        "suburb": "Yamalur",
        "city_district": "Bengaluru East City Corporation",
        "city": "Bengaluru",
        "county": "Bangalore East",
        "state_district": "Bengaluru Urban",
        "state": "Karnataka",
        "country": "India",
        "country_code": "in"
    }
}

parsed = parse_nominatim_address(nominatim_data)
print(f"Parsed result: {parsed}")
print(f"Village: {parsed['village']}")
