# Amazon Competitor Tracker — Project Handoff to Claude Code

This document is a complete handoff from a Cowork session to Claude Code. Read it end-to-end before doing anything. The user (Guy) is mid-project and expects you to pick up exactly where the previous session stopped.

---

## 1. Context: Who the user is and what they sell

- **Name:** Guy
- **Business:** Private-label brand owner selling on Amazon
- **Product portfolio:** 10–15 active SKUs grouped under **3 Parent ASINs**
- **Marketplaces:** Amazon US (primary), Canada, Mexico (this project: **US only**)
- **Supply chain:** Manufactures in China, stores in Amazon FBA
- **Supplier comms:** WeChat, Alibaba, and a shared Spreadsheet
- **Time on operations daily:** 1–2 hours
- **Biggest pain point:** PPC management — wants to reach #1 in category, optimize ad budget, increase profitability, save time
- **Tools already on his computer:** Keepa **Browser Extension** (free version, NOT the paid API)

---

## 2. The trigger: SOPHIE SOCIETY workshop, Day 1

Guy is in a week-long workshop with SOPHIE SOCIETY. **Day 1 has three deliverables:**

1. Create a **Skill** for himself
2. Create a **tool / artifact**
3. Create a **scheduled task**

After exploring options, Guy chose to **combine all three into one connected workflow** focused on his biggest pain point (PPC + competitor positioning).

---

## 3. The chosen project: Amazon Competitor Tracker

A live dashboard that tracks **his 3 Parent ASINs vs. 5 competitor ASINs each (18 ASINs total)** on Amazon US, capturing BSR + price daily, persisting history, and surfacing actionable alerts.

### 3.1 What it must do

- For each of the 3 Parent ASINs, show:
  - Daily BSR trend (his ASIN + 5 competitors on the same chart)
  - Daily price trend (his ASIN + 5 competitors on the same chart)
  - **Correlation view:** what was the price on the day BSR was X (this is the killer feature — most sellers never see this)
  - Stock-out (OOS) markers on competitors
  - Min/max price range across child variations (since competitors can drop price on a single variation)
- Persist history forever (so trends accumulate over weeks/months)
- Live Artifact format: opens in Cowork sidebar, refreshable

### 3.2 The 3 deliverables (each component)

| Deliverable | Description |
|---|---|
| **Skill: Amazon Competitor Tracker** | Documents the data-collection process — which ASINs to fetch, what fields to extract from each Amazon page (BSR, Buy Box price, child price min/max, review count, rating, OOS status), how to append to the JSON history file, and the alert rules |
| **Live Artifact: Competitor Dashboard** | 3 tabs (one per Parent ASIN). Charts: BSR over time, price over time, correlation chart. Today's Alerts section. "Refresh now" button. Reads from `competitor_history.json` |
| **Scheduled Task: Daily 08:00** | Runs the Skill, fetches today's data, appends to history, computes alerts, sends Guy a summary with ONLY the exceptions (not a full report) |

### 3.3 Alert rules Guy specified

- **Alert me if:** my BSR worsens by X% (Guy will set the threshold; default suggested: 25%)
- **Alert me if:** a competitor drops their price significantly (default suggested: ≥10% drop vs. 7-day average)

(Two other alert types — competitor goes OOS, competitor jumps in BSR — were offered but Guy did NOT choose them. Don't add unless he asks.)

---

## 4. Architecture decisions already made

### 4.1 Data source — the hard problem

Guy has only the **Keepa Browser Extension**, NOT the Keepa API. This means:

- We can't just hit a clean REST endpoint for historical BSR + price data.
- The previous session decided to use **Claude in Chrome (browser automation)** to navigate to each ASIN page daily, read BSR + Buy Box price + Keepa graph data directly off the rendered page, and append to history.
- **Known fragility:** Amazon may show CAPTCHAs. If this becomes frequent, the upgrade path is **Keepa API at $15–50/month**, which provides a clean JSON endpoint with years of historical data.
- **Bonus:** Because Keepa Extension already shows historical data on the page, the first scrape can backfill weeks of history, not just start from today.

If you (Claude Code) think there's a better approach (e.g., Selenium with rotating proxies, Playwright, Keepa CSV export), surface it to Guy before building.

### 4.2 Storage

- File: `competitor_history.json` (or SQLite if you prefer — Guy doesn't care about the format)
- Location: project root (Guy will keep it on his local machine, not cloud)
- Schema (proposed, refine as needed):
  ```json
  {
    "asins": {
      "B0XXXXXXX1": {
        "is_mine": true,
        "parent_group": "Parent A",
        "name": "Product name",
        "snapshots": [
          {
            "date": "2026-04-28",
            "bsr_main": 1234,
            "bsr_subcategory": 12,
            "subcategory_name": "Espresso Machines",
            "buy_box_price": 29.99,
            "child_price_min": 24.99,
            "child_price_max": 39.99,
            "rating": 4.5,
            "review_count": 1247,
            "is_oos": false
          }
        ]
      }
    }
  }
  ```

### 4.3 Variation handling

Guy asked: "what if a competitor drops the price on only one variation?"
**Answer:** Track BSR at the **Parent ASIN level** (Amazon shows one BSR per Parent — it's the rank of the best-selling child). Track price as **min/max range across all Children + the Buy Box price of the best-selling child**. This catches single-variation price drops without exploding the data volume.

### 4.4 Marketplace scope

**US only.** Guy explicitly chose this — even though he sells in CA + MX, those are too small to bother tracking competitors for.

### 4.5 Tech stack (suggested, not locked)

- **Artifact:** Single-file HTML + vanilla JS + Chart.js (loaded from CDN) — has to work as a standalone HTML file
- **Charts:** Chart.js or Recharts — Chart.js is simpler for vanilla HTML
- **Scheduled task runner:** Whatever Claude Code recommends for the user's OS (cron on macOS/Linux, Task Scheduler on Windows)
- **Browser automation:** Playwright (preferred over Selenium for stealth + speed)

---

## 5. Current status — what's done, what's open

### Done
- Business discovery (4 questions answered)
- Architecture decisions (data source, storage, variation handling, marketplace, alerts)
- Workshop ideas document delivered to Guy: `sophie_society_day1_ideas.docx`

### Not yet done — pick up here
1. **Receive 18 ASINs from Guy.** He committed to sending them in chat. Format requested:
   ```
   Parent ASIN #1 (mine): BXXXXXXXXX — product name
      Competitors:
      1. BXXXXXXXXX — name
      2. ...
      5. BXXXXXXXXX — name
   Parent ASIN #2 (mine): ...
   Parent ASIN #3 (mine): ...
   ```
2. **Build the Live Artifact** (start here once ASINs arrive — Guy wants to see the dashboard first, even with placeholder data)
3. **Build the Skill** that documents the data-collection process
4. **Build the Scheduled Task** that runs daily at 08:00 and invokes the Skill
5. **First end-to-end run** — populate `competitor_history.json` with today's snapshot for all 18 ASINs and verify the dashboard renders

### Open questions Guy hasn't answered yet
- Exact threshold for "BSR worsened" alert (suggest 25%)
- Exact threshold for "competitor dropped price" alert (suggest 10% vs 7-day average)
- Does he want push notifications, email, or just an in-Cowork summary?

---

## 6. How Guy likes to work

- **Language:** Hebrew (RTL). Mix of Hebrew + English technical terms is normal — keep technical terms in English (ASIN, BSR, Buy Box, FBA, PPC, etc.) and conversational text in Hebrew.
- **Style:** Decisive recommendations, then ask. Don't dump 10 options when 2 are right.
- **Pace:** He moves fast — finalized the project in 4 message exchanges. Don't over-explain.
- **Proof-of-life:** He likes seeing things rendered. Build the artifact early with placeholder data so he can react.

---

## 7. First action when this session starts

1. Read this file end-to-end.
2. Greet Guy in Hebrew, confirm you've absorbed the context, and ask him to paste the 18 ASINs (he was about to send them).
3. While waiting for ASINs, scaffold the Live Artifact HTML with placeholder data so he can see the layout the moment he sends them.

---

## 8. Files in this handoff

- `CLAUDE.md` (this file) — project context
- `sophie_society_day1_ideas.docx` — the ideas brainstorm from Day 1 of the workshop, written in Hebrew RTL. Guy may reference it but it's not strictly needed to continue.

---

*Handoff prepared at the end of the previous Cowork session. Guy is ready to go — don't make him repeat himself.*
