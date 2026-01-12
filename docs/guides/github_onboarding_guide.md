# GitHub & DefiLlama Listing Guide for Kerne

To get Kerne listed on DefiLlama (and other major aggregators), you need to interact with their open-source code repositories on GitHub. This guide explains the process of "Forking" and "Pull Requests" in plain English.

---

### 0. Account Setup: Kerne Official
Before you begin, you should create a **Kerne Official GitHub account** (e.g., `github.com/kerne-protocol`). 
- **Why?** It builds institutional credibility. Whales and auditors want to see that the protocol's code is managed by an official entity, not a personal account.
- **Professionalism:** It allows you to use a professional profile picture (the Kerne logo) and link to the official `kerne.ai` website.
- **Future-Proofing:** As you grow, you can add other developers to this "Organization" without sharing your personal login details.

### 1. What is a "Fork"?
Think of a **Fork** as a "Save As" for a project. 
- DefiLlama has a master project (the "Upstream") where all their code lives.
- You cannot edit their code directly.
- Instead, you click the **"Fork"** button on their GitHub page. This creates an exact copy of their project under your own GitHub account.
- You now have your own version of DefiLlama's code that you *can* edit.

### 2. Adding the Kerne Adapter
Once you have your fork, you add the Kerne code:
1.  Navigate to the folder where adapters live (e.g., `src/adaptors/`).
2.  Create a new folder named `kerne-protocol`.
3.  Create a file named `index.js` inside that folder.
4.  Paste the code from our `bot/defillama_adapter.js` into that file.
5.  **Commit** the changes (this is like "Saving" the file in your fork).

### 3. What is a "Pull Request" (PR)?
A **Pull Request** is a formal request to DefiLlama to "pull" your changes from your fork into their official project.
- You go back to the original DefiLlama repository.
- GitHub will notice that your fork has new code and will show a button: **"Compare & pull request."**
- You click that button, write a short description (e.g., "Add Kerne Protocol Yield Adapter"), and submit it.

### 4. The Review Process
- DefiLlama's team will look at your code.
- They might ask a question or ask for a small change.
- Once they are happy, they click **"Merge."**
- **The Result:** Your code is now part of the official DefiLlama website. Kerne will appear on their charts and rankings within a few hours.

---

### Why this is the "Institutional Way"
Every major protocol (Aave, Uniswap, Lido) follows this exact process. By managing your own GitHub account and submitting these PRs, you are signaling to the market that Kerne is a professional, developer-led protocol that follows industry standards.

**Next Step:** Create a GitHub account at `github.com` and I will walk you through the specific URLs for the DefiLlama repos.
