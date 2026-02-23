// Created: 2026-02-22
# Kerne Protocol — Email Audit Report
**Date:** 2026-02-22  
**Domain audited:** `kerne.ai`  
**Provider:** Resend (resend.com)  
**Conducted by:** Cline (automated audit)

---

## Summary

| Capability | Status | Notes |
|---|---|---|
| **Outbound Sending** (`team@kerne.ai`) | ✅ Working | Domain verified, DKIM + SPF verified |
| **DKIM Record** | ✅ Verified | `resend._domainkey.kerne.ai` present |
| **SPF Record** | ✅ Verified | `v=spf1 include:amazonses.com ~all` on `send.kerne.ai` |
| **DMARC Record** | ⚠️ Minimal | `v=DMARC1; p=none;` — no `rua` reporting address, no enforcement |
| **Inbound MX Record** | ❌ Failed | MX for `@kerne.ai` pointing to Resend inbound SMTP not present in DNS |
| **Email Receiving** | ❌ Not Working | Root cause: missing MX record — emails sent to `@kerne.ai` bounce |
| **Email Forwarding Script** | ❌ Broken | Resend `/routes` API endpoint is deprecated (405 Method Not Allowed) |

---

## Detailed Findings

### 1. Outbound Sending — ✅ WORKING

**Test performed:** Direct Resend API call sending from `team@kerne.ai`  
**Result:** `200 OK` — Email ID returned, email accepted for delivery.

The domain `kerne.ai` has been verified in Resend since `2026-02-12`. All three sending DNS records are verified:

| Record | Name | Value | Status |
|---|---|---|---|
| DKIM | `resend._domainkey.kerne.ai` | RSA public key TXT record | ✅ Verified |
| SPF (MX) | `send.kerne.ai` | `feedback-smtp.us-east-1.amazonses.com` (MX 10) | ✅ Verified |
| SPF (TXT) | `send.kerne.ai` | `v=spf1 include:amazonses.com ~all` | ✅ Verified |

**Conclusion:** You can send from any `@kerne.ai` address right now (e.g. `team@kerne.ai`, `contact@kerne.ai`).

---

### 2. Inbound Receiving — ❌ NOT WORKING

**Root cause:** The Resend API reports the receiving MX record as `status: "failed"`.

Resend requires the following MX record to be added at the **root domain** (`@`) to enable receiving:

| Record | Host | Value | Priority |
|---|---|---|---|
| MX | `@` (root) | `inbound-smtp.us-east-1.amazonaws.com` | `10` |

**Checked DNS via Google's resolver (8.8.8.8):** No MX records exist on the root domain `kerne.ai`. The nameservers are `dns1.registrar-servers.com` and `dns2.registrar-servers.com` (Namecheap).

**Impact:** Any emails sent *to* `@kerne.ai` addresses will result in a bounce with "No MX record found" or "Host unknown." This means:
- Replies to outreach emails are lost
- You cannot receive emails from investors, leads, or partners at `@kerne.ai`
- Forwarding rules cannot work at all without inbound MX working first

---

### 3. DMARC — ⚠️ WEAK POLICY

**Current record:** `v=DMARC1; p=none;`

This is the weakest possible DMARC policy. `p=none` means even if authentication fails, emails are not quarantined or rejected. This is acceptable for initial setup but should be hardened.

**Recommended upgrade:**
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@kerne.ai; ruf=mailto:dmarc@kerne.ai; fo=1;
```

---

### 4. Email Forwarding Script — ❌ BROKEN

**File:** `add_email_forward.py`  
**Error:** `405 Method Not Allowed` on `GET https://api.resend.com/routes`

Resend has **deprecated** the `/routes` endpoint. Inbound email forwarding now requires:
1. An MX record pointing to Resend's inbound SMTP (see above)
2. A **Webhook** configured in the Resend dashboard to receive parsed inbound email payloads

The original script cannot create forwarding rules anymore. A new implementation is needed.

---

## Action Plan (Priority Order)

### STEP 1 — Add MX Record in Namecheap (Critical, ~5 min)
This is the single most important fix. Without it, receiving is completely broken.

1. Log in to **Namecheap** → Domain List → `kerne.ai` → Manage DNS
2. Add a new record:
   - **Type:** MX
   - **Host:** `@`
   - **Value:** `inbound-smtp.us-east-1.amazonaws.com`
   - **Priority:** `10`
   - **TTL:** Automatic
3. Save and wait for DNS propagation (usually 5–30 minutes with Namecheap)
4. Go to **Resend Dashboard** → Domains → `kerne.ai` → Verify records to confirm the receiving record turns green

### STEP 2 — Set Up Inbound Webhook in Resend Dashboard
Once the MX record is verified, configure inbound email routing:

1. In Resend dashboard, go to **Email** → **Inbound**
2. Create a routing rule for `*@kerne.ai` (or specific addresses like `team@`, `contact@`)
3. Set the action to **Webhook** pointing to your webhook endpoint (or use Resend's built-in forwarding to a personal address)

Alternatively, Resend supports direct forwarding via the dashboard UI without needing a webhook — configure `team@kerne.ai` → your personal email directly.

### STEP 3 — Upgrade DMARC (Optional but Recommended)
Update the `_dmarc.kerne.ai` TXT record from:
```
v=DMARC1; p=none;
```
To:
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@kerne.ai; pct=100;
```
This prevents spoofing of your domain.

---

## Current Bot Code Status

| File | Status |
|---|---|
| `kerne_email.py` | ✅ Works — uses Resend HTTP API for sending |
| `bot/email_manager.py` | ✅ Works — uses SMTP to `smtp.resend.com:465` with API key, sends from `team@kerne.ai` |
| `bot/test_email_connectivity.py` | ⚠️ False negative — the test points to `kerne.systems` (different domain, not kerne.ai) and has a duplicate-contact guard that prevents it from ever re-running. Needs to be updated. |
| `add_email_forward.py` | ❌ Broken — uses deprecated `/routes` endpoint |

---

## Quick Fix Commands

Once the MX record is live and Resend inbound is configured, the `add_email_forward.py` script has been updated to use the Resend inbound webhooks API instead of the deprecated `/routes` endpoint. See the updated file.