import asyncio
import websockets
import requests
from bs4 import BeautifulSoup
import json
import re

# Configuration
WEBSOCKET_URI = "ws://127.0.0.1:8765"
SCRAPE_URL = "https://www.tradingview.com/symbols/SOLUSDT/technicals/"
UPDATE_INTERVAL = 30  # seconds

async def get_solana_sentiment():
    try:
        response = requests.get(SCRAPE_URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        script_tag = soup.find("script", string=lambda text: "technicalAnalysis" in text if text else False)

        if script_tag:
            script_content = script_tag.string
            match = re.search(r"window\.tv_widget = new TradingView\.widget\((.*?)\);", script_content, re.DOTALL)
            if match:
                try:
                    json_data_str = match.group(1)
                    json_data = json.loads(json_data_str)

                    recommendation = json_data.get("technicalAnalysis", {}).get("recomm", None)
                    if recommendation:
                        if recommendation == "BUY":
                            sentiment_score = 1.66
                        elif recommendation == "STRONG_BUY":
                            sentiment_score = 2.0
                        elif recommendation == "SELL":
                            sentiment_score = 0.33
                        elif recommendation == "STRONG_SELL":
                            sentiment_score = 0.0
                        elif recommendation == "NEUTRAL":
                            sentiment_score = 1.0
                        else:
                            sentiment_score = 1.0  # Default to neutral if unknown
                        print(f"Sentiment from TradingView: {recommendation} (Score: {sentiment_score})") # Print sentiment
                        return sentiment_score
                    else:
                        print("Could not find 'recomm' data in JSON.")
                        return None

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    return None
            else:
                print("Could not find JSON data in script tag.")
                return None
        else:
            print("Could not find script tag with technical analysis data.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

async def send_data_to_websocket(websocket):
    while True:
        sentiment = await get_solana_sentiment()

        if sentiment is not None:
            try:
                await websocket.send(json.dumps({"sentiment": sentiment}))
                print(f"Sent sentiment to WebSocket: {sentiment}") # Print sent sentiment
            except websockets.exceptions.ConnectionClosedError:
                print("WebSocket connection closed. Reconnecting...")
                break
            except Exception as e:
                print(f"Error sending data: {e}")

        await asyncio.sleep(UPDATE_INTERVAL)

async def main():
    while True:
        try:
            async with websockets.connect(WEBSOCKET_URI) as websocket:
                print("Connected to WebSocket")
                await send_data_to_websocket(websocket)
        except ConnectionRefusedError:
            print(f"Connection refused to {WEBSOCKET_URI}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"WebSocket connection error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())