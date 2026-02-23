// Created: 2026-02-22
# Kerne Protocol: Discord Support Structure
### Operational Guide for Retail Launch

This document defines the channel structure, roles, and escalation procedures for the Kerne Community Discord to ensure institutional-grade support for retail users.

---

## 1. Channel Architecture

### 📢 INFORMATION (Read-Only)
- `#welcome`: Rules, verification, and "Start Here" guide.
- `#announcements`: Official protocol updates and major milestones.
- `#links`: Official website, documentation, and social media links.
- `#security-alerts`: Critical security updates and oracle status.

### 💬 COMMUNITY
- `#general`: Main discussion for Kerne users.
- `#yield-strategies`: Discussion on kUSD loops and delta-neutral strategies.
- `#governance`: Discussion on protocol parameters and future proposals.
- `#developers`: Technical discussion for SDK and API integrations.

### 🛠️ SUPPORT (Ticketing System)
- `#open-a-ticket`: Primary entry point for user issues.
- `#faq`: Searchable database of common questions.
- `#bug-reports`: Reporting technical issues (incentivized).

---

## 2. Roles & Permissions

| Role | Responsibility | Permissions |
|------|----------------|-------------|
| **Founders** | Strategic leadership | Full Admin |
| **Core Team** | Protocol operations | Manage Channels, Kick/Ban |
| **Moderators** | Community management | Timeout, Delete Messages |
| **Sentinels** | Technical support / Power users | View Private Support Channels |
| **Verified** | General community | Send Messages |
| **Unverified** | New joins | Read Only (Welcome) |

---

## 3. Support SLA & Escalation

### Response Time Targets
- **Critical (Security/Solvency):** < 15 minutes (24/7)
- **High (Transaction Failure):** < 2 hours
- **Medium (General Inquiry):** < 12 hours

### Escalation Path
1. **User** opens ticket in `#open-a-ticket`.
2. **Moderator** triages the issue.
3. If technical/financial, escalate to **Sentinels**.
4. If protocol-level or unresolved, escalate to **Core Team**.
5. **Founders** notified only for Critical/Systemic issues.

---

## 4. Security Protocols
- **No DMs:** Staff will NEVER DM users first.
- **Official Links Only:** Use a bot to auto-delete any non-whitelisted links.
- **Verification:** Mandatory CAPTCHA/Wallet verification to prevent bot raids.

---

## 5. Launch Checklist
- [ ] Configure Discord server with above channels.
- [ ] Set up Ticket Tool or similar bot for support.
- [ ] Draft `#welcome` and `#faq` content.
- [ ] Recruit/Assign initial Moderator team.
- [ ] Integrate security bot for link filtering.