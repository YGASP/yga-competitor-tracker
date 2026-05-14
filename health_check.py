"""
YGA Competitor Tracker — Daily Health Check
Runs at 09:00. If today's data is missing, collects it and sends an email report.
If collection fails, sends a failure alert.
"""

import json
import smtplib
import subprocess
import sys
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GMAIL_USER     = "yg.amigoss@gmail.com"
GMAIL_APP_PASS = "eulmxoectnbkncwq"
TO_EMAIL       = "yg.amigoss@gmail.com"

BASE_DIR   = Path(__file__).parent
DATA_FILE  = BASE_DIR / "competitor_history.json"
COLLECT_PY = BASE_DIR / "collect_data.py"
PYTHON     = r"C:\Users\yoavl\AppData\Local\Programs\Python\Python313\python.exe"
TODAY      = str(date.today())
YESTERDAY  = str(date.today() - timedelta(days=1))

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def load_history() -> dict:
    if not DATA_FILE.exists():
        return {"asins": {}}
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def data_exists_for(target_date: str) -> bool:
    data = load_history()
    for asin_data in data["asins"].values():
        for snap in asin_data["snapshots"]:
            if snap["date"] == target_date:
                return True
    return False


def count_asins_for(target_date: str) -> int:
    data = load_history()
    count = 0
    for asin_data in data["asins"].values():
        for snap in asin_data["snapshots"]:
            if snap["date"] == target_date:
                count += 1
                break
    return count


def get_summary_for(target_date: str) -> list[dict]:
    data = load_history()
    rows = []
    for asin, asin_data in data["asins"].items():
        snap = next((s for s in asin_data["snapshots"] if s["date"] == target_date), None)
        if snap:
            rows.append({
                "brand": asin_data["brand"],
                "asin": asin,
                "is_mine": asin_data.get("is_mine", False),
                "bsr": snap.get("bsr_main"),
                "price": snap.get("buy_box_price"),
                "group": asin_data.get("parent_group", ""),
            })
    return rows


def run_collection() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [PYTHON, "-X", "utf8", str(COLLECT_PY), "--headless"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=BASE_DIR, timeout=300
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Collection timed out after 5 minutes."
    except Exception as e:
        return False, str(e)


def send_email(subject: str, html_body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = TO_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_bytes())


def build_success_html(collected_now: bool, rows: list[dict]) -> str:
    status_line = (
        "הנתונים <b>נאספו עכשיו</b> על ידי Health Check (המשימה הראשית לא רצה)"
        if collected_now else
        "הנתונים <b>נאספו בהצלחה</b> על ידי המשימה הראשית"
    )

    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["group"], []).append(r)

    tables_html = ""
    for group, members in groups.items():
        tables_html += f"<h3 style='color:#1B4F72;margin-bottom:4px'>{group}</h3>"
        tables_html += """
        <table style='border-collapse:collapse;width:100%;margin-bottom:16px;font-size:13px'>
          <tr style='background:#1B4F72;color:#fff'>
            <th style='padding:6px 10px;text-align:left'>Brand</th>
            <th style='padding:6px 10px;text-align:right'>BSR</th>
            <th style='padding:6px 10px;text-align:right'>Price</th>
          </tr>"""
        for m in sorted(members, key=lambda x: (x["bsr"] or 999999)):
            mine_style = "background:#D5F5E3;font-weight:bold" if m["is_mine"] else ""
            bsr_str   = f"#{m['bsr']:,}" if m["bsr"] else "N/A"
            price_str = f"${m['price']:.2f}" if m["price"] else "N/A"
            tables_html += f"""
          <tr style='{mine_style}'>
            <td style='padding:5px 10px;border-bottom:1px solid #eee'>{m['brand']}</td>
            <td style='padding:5px 10px;border-bottom:1px solid #eee;text-align:right'>{bsr_str}</td>
            <td style='padding:5px 10px;border-bottom:1px solid #eee;text-align:right'>{price_str}</td>
          </tr>"""
        tables_html += "</table>"

    warning = ""
    if collected_now:
        warning = """
        <div style='background:#FFF3CD;border:1px solid #FFC107;border-radius:6px;padding:10px 14px;margin-bottom:16px'>
          <b>שים לב:</b> המשימה היומית לא רצה — Health Check אסף את הנתונים במקומה.<br>
          ייתכן שצריך להגדיר מחדש את Scheduled Task. הרץ את <code>setup_scheduler.bat</code> כ-Administrator.
        </div>"""

    return f"""
    <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px'>
      <h2 style='color:#1B4F72'>YGA Competitor Tracker — {TODAY}</h2>
      <p style='color:#555'>{status_line}</p>
      {warning}
      {tables_html}
      <p style='color:#888;font-size:11px;margin-top:20px'>YGA Sports Auto-Report</p>
    </body></html>"""


def build_failure_html(error_output: str) -> str:
    return f"""
    <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px'>
      <h2 style='color:#C0392B'>YGA Tracker - FAILED to collect data for {TODAY}</h2>
      <p>גם Health Check ניסה לאסוף נתונים ונכשל.</p>
      <p><b>שגיאה:</b></p>
      <pre style='background:#f9f9f9;border:1px solid #ddd;padding:12px;font-size:12px;white-space:pre-wrap'>{error_output[:2000]}</pre>
      <p>הרץ ידנית: <code>collect_data.py --headless</code></p>
      <p style='color:#888;font-size:11px'>YGA Sports Auto-Report</p>
    </body></html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"[health_check] {TODAY} — checking data...")

    if GMAIL_APP_PASS == "REPLACE_WITH_APP_PASSWORD":
        print("[ERROR] Gmail App Password not configured in health_check.py")
        sys.exit(1)

    collected_now = False

    if data_exists_for(TODAY):
        print(f"[health_check] Data found for {TODAY} ({count_asins_for(TODAY)} ASINs). Sending report.")
    else:
        print(f"[health_check] No data for {TODAY}. Running collection...")
        ok, output = run_collection()
        if ok and data_exists_for(TODAY):
            print("[health_check] Collection succeeded.")
            collected_now = True
        else:
            print("[health_check] Collection FAILED. Sending failure alert.")
            send_email(
                subject=f"[YGA] FAILED to collect competitor data - {TODAY}",
                html_body=build_failure_html(output)
            )
            print("[health_check] Failure email sent.")
            sys.exit(1)

    rows = get_summary_for(TODAY)
    send_email(
        subject=f"[YGA] Competitor Report {TODAY}" + (" [auto-collected]" if collected_now else ""),
        html_body=build_success_html(collected_now, rows)
    )
    print("[health_check] Report email sent.")


if __name__ == "__main__":
    main()
