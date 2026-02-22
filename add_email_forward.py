# Created: 2026-02-16
# Updated: 2026-02-22 — Resend /routes API was deprecated (405). Replaced with
# Resend Inbound Webhooks API. See docs/email_audit_report_2026-02-22.md for full details.
"""
Manage Resend inbound email configuration for @kerne.ai.

Resend deprecated the /routes endpoint. Inbound email handling now requires:
  1. An MX record on the root domain pointing to inbound-smtp.us-east-1.amazonaws.com
  2. Inbound routing configured via the Resend Dashboard (Email → Inbound)

This script:
  - Checks the status of all kerne.ai DNS records via the Resend API
  - Lists existing API keys (to confirm the account is accessible)
  - Provides a clear status report of what is and isn't working
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables from bot/.env
load_dotenv(dotenv_path="bot/.env")

DOMAIN_ID = "3caa1309-64f1-459e-beb5-57648dce1485"


def get_api_key():
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        print("[!] Error: RESEND_API_KEY not found in bot/.env")
        return None
    return api_key


def check_domain_status():
    """
    Check the full DNS record status for kerne.ai via Resend API.
    Returns parsed record statuses.
    """
    api_key = get_api_key()
    if not api_key:
        return None

    url = f"https://api.resend.com/domains/{DOMAIN_ID}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        print(f"\n[*] Domain: {data['name']}")
        print(f"[*] Overall Status: {data['status'].upper()}")
        print(f"[*] Sending: {data['capabilities']['sending']}")
        print(f"[*] Receiving: {data['capabilities']['receiving']}")
        print("\n[*] DNS Record Status:")

        all_verified = True
        for record in data.get("records", []):
            status_icon = "✅" if record["status"] == "verified" else "❌"
            print(f"  {status_icon} [{record['record']}] {record['type']} {record['name'] or '@'}.kerne.ai")
            print(f"       Value: {record['value']}")
            print(f"       Status: {record['status'].upper()}")
            if record["status"] != "verified":
                all_verified = False

        if not all_verified:
            print("\n[!] ACTION REQUIRED:")
            print("    Add the following MX record to kerne.ai in Namecheap:")
            print("      Type:     MX")
            print("      Host:     @")
            print("      Value:    inbound-smtp.us-east-1.amazonaws.com")
            print("      Priority: 10")
            print("      TTL:      Automatic")
            print("\n    After adding the MX record:")
            print("    1. Wait 5-30 minutes for DNS propagation")
            print("    2. Run this script again to verify — status should turn VERIFIED")
            print("    3. Configure inbound routing at: https://resend.com/inbound")
        else:
            print("\n[+] All DNS records verified. Sending and receiving are fully operational.")

        return data
    except Exception as e:
        print(f"[!] Failed to fetch domain status: {e}")
        return None


def list_api_keys():
    """List Resend API keys to confirm account access."""
    api_key = get_api_key()
    if not api_key:
        return

    url = "https://api.resend.com/api-keys"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        keys = data.get("data", [])
        print(f"\n[*] Active API Keys ({len(keys)}):")
        for key in keys:
            print(f"  - {key.get('name', 'unnamed')} (ID: {key.get('id', 'unknown')})")
    except Exception as e:
        print(f"[!] Failed to list API keys: {e}")


def test_send(to_email: str):
    """
    Send a test email to verify outbound sending is working.
    """
    api_key = get_api_key()
    if not api_key:
        return False

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "Kerne Protocol <team@kerne.ai>",
        "to": [to_email],
        "subject": "Kerne Protocol — Email Test",
        "html": "<h2>Email Test</h2><p>This is a test from the Kerne Protocol email system. If you received this, outbound sending from <b>@kerne.ai</b> is working correctly.</p>"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        print(f"\n[+] Test email sent successfully!")
        print(f"    To: {to_email}")
        print(f"    Email ID: {result.get('id')}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"[!] Failed to send test email: {e}")
        if e.response is not None:
            print(f"    Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"[!] Error: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Kerne Protocol Email Management — Resend API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python add_email_forward.py --status          Check DNS record & domain health
  python add_email_forward.py --test you@gmail.com   Send a test email to verify sending
  python add_email_forward.py --keys            List active Resend API keys

NOTE: Resend deprecated /routes in early 2026. To configure email forwarding/inbound:
  1. Add MX record: @ -> inbound-smtp.us-east-1.amazonaws.com (Priority 10)
  2. Configure inbound routing at: https://resend.com/inbound
  See: docs/email_audit_report_2026-02-22.md for full details.
        """
    )
    parser.add_argument("--status", action="store_true", help="Check domain DNS record status")
    parser.add_argument("--test", metavar="EMAIL", help="Send a test email to verify outbound sending")
    parser.add_argument("--keys", action="store_true", help="List active Resend API keys")

    args = parser.parse_args()

    if args.status:
        check_domain_status()
    elif args.test:
        test_send(args.test)
    elif args.keys:
        list_api_keys()
    else:
        # Default: run full status check
        print("[*] Running full Kerne email system status check...")
        check_domain_status()
        list_api_keys()