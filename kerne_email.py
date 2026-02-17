# Created: 2026-02-12
"""
Kerne Protocol Email Dispatcher
Uses Resend API for high-deliverability custom domain emails (@kerne.ai).
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv
from loguru import logger

# Load environment variables from bot/.env
load_dotenv(dotenv_path="bot/.env")

def send_kerne_email(to, subject, body_html, from_email="team@kerne.ai"):
    """
    Sends an email using the Resend API.
    """
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY not found in bot/.env")
        print("\n[!] Error: RESEND_API_KEY missing.")
        print("Please add 'RESEND_API_KEY=re_your_key' to bot/.env")
        return False

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": f"Kerne Protocol <{from_email}>",
        "to": [to],
        "subject": subject,
        "html": body_html
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.success(f"Email sent successfully! ID: {result.get('id')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kerne Protocol Email Dispatcher")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--subject", required=True, help="Email subject")
    parser.add_argument("--body", required=True, help="Email body (HTML supported)")
    parser.add_argument("--from", dest="from_addr", default="team@kerne.ai", help="Sender email (default: team@kerne.ai)")

    args = parser.parse_args()

    print(f"[*] Sending email to {args.to}...")
    success = send_kerne_email(
        to=args.to,
        subject=args.subject,
        body_html=args.body,
        from_email=args.from_addr
    )
    
    if success:
        print("[+] Done.")
    else:
        print("[-] Failed.")