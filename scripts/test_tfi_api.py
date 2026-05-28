import os
import requests
from dotenv import load_dotenv
from google.transit import gtfs_realtime_pb2


load_dotenv()


def fetch_gtfs_realtime(url, api_key):
    headers = {
        "x-api-key": api_key
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)

    return feed


def main():
    api_key = os.getenv("TFI_API_KEY")
    vehicle_positions_url = os.getenv("TFI_VEHICLE_POSITIONS_URL")

    if not api_key or api_key == "your_tfi_api_key_here":
        raise ValueError("TFI_API_KEY is missing. Add your real API key to the .env file.")

    if not vehicle_positions_url or vehicle_positions_url == "your_tfi_vehicle_positions_url_here":
        raise ValueError("TFI_VEHICLE_POSITIONS_URL is missing. Add your real vehicle positions URL to the .env file.")

    print("Fetching TFI vehicle positions")

    feed = fetch_gtfs_realtime(vehicle_positions_url, api_key)

    print(f"Feed timestamp: {feed.header.timestamp}")
    print(f"Entities returned: {len(feed.entity)}")

    for entity in feed.entity[:5]:
        print("=" * 60)
        print(f"Entity ID: {entity.id}")

        if entity.HasField("vehicle"):
            vehicle = entity.vehicle
            print(f"Trip ID: {vehicle.trip.trip_id}")
            print(f"Route ID: {vehicle.trip.route_id}")
            print(f"Vehicle ID: {vehicle.vehicle.id}")
            print(f"Latitude: {vehicle.position.latitude}")
            print(f"Longitude: {vehicle.position.longitude}")
            print(f"Timestamp: {vehicle.timestamp}")


if __name__ == "__main__":
    main()