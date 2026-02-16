# Custom Email Setup Guide for kerne.ai

**Created: 2026-02-12**

## Current Status
- Domain `kerne.ai` is registered and resolving to IP `216.198.79.1`
- Need to confirm domain ownership before proceeding

---

## Best FREE Options for Custom Domain Email

### Option 1: Zoho Mail (RECOMMENDED - Best Free Option)

**Free Tier:**
- Up to 5 email users FREE forever
- 5GB storage per user
- Custom domain support
- Webmail interface + IMAP/POP/SMTP access
- Mobile apps available

**Setup Steps:**
1. Go to https://www.zoho.com/mail/
2. Sign up for "Forever Free Plan"
3. Verify domain ownership (add TXT record to DNS)
4. Create email accounts (e.g., `scofield@kerne.ai`, `mahone@kerne.ai`)
5. Configure MX records:
   ```
   MX 10 mx.zoho.com
   MX 20 mx2.zoho.com
   ```

**Pros:**
- Truly free, no credit card required
- Professional email hosting
- Full IMAP/SMTP access (works with Outlook, Gmail app, etc.)
- 5GB per user is generous

**Cons:**
- 5 user limit on free tier
- No POP access on free tier (IMAP only)

---

### Option 2: Cloudflare Email Routing + Gmail (Free Forwarding)

**Best for:** Receiving emails only, then responding via Gmail

**Setup Steps:**
1. Move domain DNS to Cloudflare (free)
2. Enable Email Routing in Cloudflare dashboard
3. Add custom addresses (e.g., `team@kerne.ai` → your Gmail)
4. In Gmail, enable "Send mail as" feature:
   - Settings → Accounts → "Add another email address"
   - Use Cloudflare's SMTP or Gmail's SMTP

**Pros:**
- Completely free
- Unlimited email addresses (forwarding only)
- Works with existing Gmail

**Cons:**
- Not a true inbox (forwarding only)
- Sending requires SMTP setup or Gmail "send as" workaround

---

### Option 3: ImprovMX (Free Forwarding Alternative)

**Free Tier:**
- Unlimited email forwards
- 10 domains free

**Setup Steps:**
1. Go to https://improvmx.com/
2. Add your domain
3. Configure MX records:
   ```
   MX 10 mx1.improvmx.com
   MX 20 mx2.improvmx.com
   ```
4. Create forwards (e.g., `scofield@kerne.ai` → your Gmail)

**Pros:**
- Very simple setup
- Unlimited forwards

**Cons:**
- Forwarding only, no true inbox
- Outbound mail requires SMTP relay (paid add-on)

---

### Option 4: Migadu (Pay-Per-Use, Very Cheap)

**Pricing:** ~$20/year for basic plan
- Unlimited mailboxes
- Flexible pricing

**Setup:** Similar to others, add MX records to DNS

---

## Comparison Matrix

| Feature | Zoho Mail (Free) | Cloudflare Routing | ImprovMX | Migadu |
|---------|------------------|-------------------|----------|--------|
| **Cost** | FREE | FREE | FREE | ~$20/yr |
| **True Inbox** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Storage** | 5GB/user | N/A | N/A | Flexible |
| **Users** | 5 max | Unlimited forwards | Unlimited forwards | Unlimited |
| **Send Emails** | ✅ Yes | ⚠️ Via Gmail | ⚠️ Paid add-on | ✅ Yes |
| **Mobile App** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Professional** | ✅ Yes | ⚠️ Hacky | ⚠️ Hacky | ✅ Yes |

---

## Recommendation

**Use Resend API (Free Tier)** - Best for code-based autonomous outreach and high deliverability.
- 3,000 emails/month FREE
- High IP reputation (emails land in inbox)
- Simple API integration for autonomous bots
- Custom domain support (`@kerne.ai`)

---

## Action Items

1. [x] Confirm domain ownership - `kerne.ai` is registered at Namecheap
2. [x] Access domain registrar DNS settings
3. [x] Sign up for Resend.com
4. [x] Verify domain and configure DNS records (DKIM, SPF, MX, DMARC)
5. [x] Generate API Key and add to `bot/.env` as `RESEND_API_KEY`
6. [x] Use `kerne_email.py` for dispatching emails
7. [ ] Move Nameservers to Cloudflare for Email Routing
8. [ ] Configure Cloudflare Email Routing with forwarding rules:
   - `liamlakevold@kerne.ai` → `liamlakevold@gmail.com`
   - `devonhewitt@kerne.ai` → `devhew@icloud.com`
   - `matthewlakevold@kerne.ai` → `matthewlkv@gmail.com`
   - `team@kerne.ai` → `liamlakevold@gmail.com` (catch-all)

---

## Domain Registrar Check

To find where kerne.ai is registered, run:
```bash
whois kerne.ai
```

Or check: https://lookup.icann.org/

Common registrars:
- Namecheap
- GoDaddy
- Google Domains
- Cloudflare
- Porkbun

---

## Notes

- The IP `216.198.79.1` suggests the domain may be parked or using a basic hosting setup
- If you don't own kerne.ai, you'll need to:
  1. Contact the owner to purchase
  2. Or choose a different domain (kerne.finance, kerne-protocol.com, etc.)