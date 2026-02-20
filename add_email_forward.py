# Created: 2026-02-16
"""
Add email forwarding rule via Resend API.
Creates an alias that forwards incoming emails to a destination address.
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables from bot/.env
load_dotenv(dotenv_path="bot/.env")

def add_email_forward(alias: str, destination: str):
    """
    Add an email forwarding rule via Resend API.
    
    Args:
        alias: The email alias (e.g., 'romanday@kerne.ai')
        destination: The forwarding destination (e.g., 'romanday12@gmail.com')
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[!] Error: RESEND_API_KEY not found in bot/.env")
        return False

    url = "https://api.resend.com/routes"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "name": f"Forward {alias}",
        "match": f"to({alias})",
        "actions": [
            {
                "type": "forward",
                "value": destination
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"[+] Successfully created forwarding rule!")
        print(f"    Alias: {alias}")
        print(f"    Forwards to: {destination}")
        print(f"    Route ID: {result.get('id')}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            print(f"[!] Route may already exist or domain not verified: {e.response.text}")
        else:
            print(f"[!] HTTP Error: {e}")
            print(f"    Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"[!] Failed to create forwarding rule: {e}")
        return False


def list_routes():
    """List all existing email routes."""
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[!] Error: RESEND_API_KEY not found in bot/.env")
        return None

    url = "https://api.resend.com/routes"
    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[!] Failed to list routes: {e}")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage email forwarding via Resend API")
    parser.add_argument("--add", nargs=2, metavar=("ALIAS", "DESTINATION"), 
                        help="Add a new forwarding rule")
    parser.add_argument("--list", action="store_true", help="List all existing routes")
    
    args = parser.parse_args()
    
    if args.add:
        alias, destination = args.add
        # Ensure alias has @kerne.ai if not specified
        if "@" not in alias:
            alias = f"{alias}@kerne.ai"
        add_email_forward(alias, destination)
    elif args.list:
        routes = list_routes()
        if routes:
            print("\n[*] Existing email routes:")
            for route in routes.get("data", []):
                print(f"    - {route.get('match', 'unknown')} → {route.get('actions', [{}])[0].get('value', 'unknown')}")
    else:
        # Default: add romanday@kerne.ai -> romanday12@gmail.com
        print("[*] Adding default forwarding rule: romanday@kerne.ai -> romanday12@gmail.com")
        add_email_forward("romanday@kerne.ai", "romanday12@gmail.com")