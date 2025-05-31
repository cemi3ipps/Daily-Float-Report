import os
import certifi
# Patch for SSL certificate errors with SendGrid
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
# If you still get SSL errors, try running this script with Python 3.10–3.12, as some newer/older versions may have SSL bugs.
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail
import schedule
import time
from datetime import datetime, timedelta
import pytz

# Import the real extraction functions
from main import login_and_test_v2
from main2 import login_vas
from main3 import login_and_get_cimb_balance

load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
TO_EMAIL = [email.strip() for email in os.getenv("SENDGRID_TO_EMAIL", "").split(",") if email.strip()]

def safe_float(val):
    try:
        if isinstance(val, str):
            val = val.replace(',', '')
        return float(val)
    except Exception:
        return None

def run_report():
    print("Extracting V2 balance...")
    V2_balance = safe_float(login_and_test_v2())
    print("Extracting VAS balance...")
    VAS_balance = safe_float(login_vas())
    print("Extracting CIMB balance...")
    CIMB_balance = safe_float(login_and_get_cimb_balance())

    report = f"""
Daily Float Reconciliation Report\n\n"""
    if CIMB_balance is not None:
        report += f"CIMB Balance: {CIMB_balance:,.2f} THB\n"
    else:
        report += f"CIMB Balance: ERROR\n"
    if V2_balance is not None:
        report += f"V2 Balance: {V2_balance:,.2f} THB\n"
    else:
        report += f"V2 Balance: ERROR\n"
    if VAS_balance is not None:
        report += f"VAS Balance: {VAS_balance:,.2f} THB\n"
    else:
        report += f"VAS Balance: ERROR\n"

    report_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    html_report = f'''
<html>
  <head>
    <style>
      body {{ font-family: Arial, sans-serif; }}
      .report-table {{ border-collapse: collapse; width: 400px; margin: 18px 0; }}
      .report-table th, .report-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
      .report-table th {{ background-color: #f2f2f2; font-weight: bold; }}
      .ok {{ color: #228B22; font-weight: bold; }}
      .warn {{ color: #B22222; font-weight: bold; }}
      .error {{ color: #B22222; font-weight: bold; }}
    </style>
  </head>
  <body>
    <h2>Daily Float Reconciliation Report for {report_date}</h2>
    <table class="report-table">
      <tr><th>Account</th><th>Balance (THB)</th></tr>
      <tr><td>CIMB</td><td>{(f"{CIMB_balance:,.2f}" if CIMB_balance is not None else '<span class="error">ERROR</span>')}</td></tr>
      <tr><td>V2</td><td>{(f"{V2_balance:,.2f}" if V2_balance is not None else '<span class="error">ERROR</span>')}</td></tr>
      <tr><td>VAS</td><td>{(f"{VAS_balance:,.2f}" if VAS_balance is not None else '<span class="error">ERROR</span>')}</td></tr>
    </table>
'''

    if None not in (CIMB_balance, V2_balance, VAS_balance):
        result = CIMB_balance - (V2_balance + VAS_balance)
        report += f"\nCIMB - (V2 + VAS) = {result:,.2f} THB\n\n"
        if result >= 0:
            summary = f"CIMB balance is sufficient. Surplus: {result:,.2f} THB."
            html_report += f'<p class="ok">CIMB - (V2 + VAS) = {result:,.2f} THB</p>'
            html_report += f'<p class="ok">CIMB balance is sufficient. Surplus: {result:,.2f} THB.</p>'
        else:
            summary = f"Warning: Combined V2 and VAS float exceeds CIMB account by {abs(result):,.2f} THB!"
            html_report += f'<p class="warn">CIMB - (V2 + VAS) = {result:,.2f} THB</p>'
            html_report += f'<p class="warn">Warning: Combined V2 and VAS float exceeds CIMB account by {abs(result):,.2f} THB!</p>'
        report += summary
    else:
        report += "\nOne or more balances could not be extracted. Please check logs.\n"
        html_report += '<p class="error">One or more balances could not be extracted. Please check logs.</p>'

    html_report += '</body></html>'

    print(report)

    # --- Send email via SendGrid ---
    if SENDGRID_API_KEY and FROM_EMAIL and TO_EMAIL:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY.strip('"'))
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=TO_EMAIL,
            subject=f"Daily Float Reconciliation Report for {report_date}",
            plain_text_content=report,
            html_content=html_report
        )
        try:
            response = sg.send(message)
            print(f"Email sent! Status code: {response.status_code}")
        except Exception as e:
            print(f"Failed to send email: {e}")
    else:
        print("SendGrid credentials not set. Email not sent.")

    # --- Clean up downloads directory ---
    import glob
    downloads_dir = os.path.join(os.path.dirname(__file__), "downloads")
    for file_path in glob.glob(os.path.join(downloads_dir, "*")):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Could not delete {file_path}: {e}")


if __name__ == "__main__":
    # Check if running in development mode for one-time execution
    environment = os.getenv("ENVIRONMENT", "").lower()
    if environment == "development":
        print("Running in development mode - executing report once...")
        run_report()
        print("Development run completed. Exiting.")
        exit(0)
    
    # Always use Asia/Bangkok time for scheduling
    BANGKOK_TZ = pytz.timezone("Asia/Bangkok")
    print("Scheduler started. Waiting for next run at 00:15 Asia/Bangkok time...")
    last_run_date = None
    while True:
        now_bangkok = datetime.now(BANGKOK_TZ)
        # Run only once per day at 00:15
        if now_bangkok.hour == 0 and now_bangkok.minute == 15:
            if last_run_date != now_bangkok.date():
                run_report()
                last_run_date = now_bangkok.date()
        print("Waiting for next run...")
        time.sleep(30)