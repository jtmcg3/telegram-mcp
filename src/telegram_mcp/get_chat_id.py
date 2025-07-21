#!/usr/bin/env python3
"""
Utility script to get your Telegram chat ID
Run this after creating your bot and sending it a message
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_chat_id():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment")
        print("Make sure you have a .env file with your bot token")
        return
    
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    print("Getting updates from Telegram...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if data['result']:
            for update in data['result']:
                chat = update['message']['chat']
                print(f"Chat ID: {chat['id']}")
                print(f"Chat Type: {chat['type']}")
                if 'username' in chat:
                    print(f"Username: @{chat['username']}")
                if 'first_name' in chat:
                    print(f"Name: {chat['first_name']}")
                print("-" * 30)
        else:
            print("No messages found. Send a message to your bot first!")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    get_chat_id()