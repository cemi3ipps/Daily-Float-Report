import os
from dotenv import load_dotenv
import sendgrid
from sendgrid.helpers.mail import Mail

# Import the real extraction functions
from main import login_and_test_v2
from main2 import login_vas
from main3 import login_and_get_cimb_balance

load_dotenv()
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
TO_EMAIL = os.getenv("SENDGRID_TO_EMAIL")

# --- Run extraction functions ---
def safe_float(val):
    try:
        if isinstance(val, str):
            val = val.replace(',', '')
        return float(val)
    except Exception:
        return None

print("Extracting V2 balance...")
V2_balance = safe_float(login_and_test_v2())
print("Extracting VAS balance...")
VAS_balance = safe_float(login_vas())
print("Extracting CIMB balance...")
CIMB_balance = safe_float(login_and_get_cimb_balance())

# --- Format report ---
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

if None not in (CIMB_balance, V2_balance, VAS_balance):
    result = CIMB_balance - (V2_balance + VAS_balance)
    report += f"\nCIMB - (V2 + VAS) = {result:,.2f} THB\n\n"
    if result >= 0:
        summary = f"CIMB balance is sufficient. Surplus: {result:,.2f} THB."
    else:
        summary = f"Warning: Combined V2 and VAS float exceeds CIMB account by {abs(result):,.2f} THB!"
    report += summary
else:
    report += "\nOne or more balances could not be extracted. Please check logs.\n"

print(report)

# --- Send email via SendGrid ---
if SENDGRID_API_KEY and FROM_EMAIL and TO_EMAIL:
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY.strip('"'))
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=TO_EMAIL,
        subject="Daily Float Reconciliation Report",
        plain_text_content=report
    )
    try:
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Failed to send email: {e}")
else:
    print("SendGrid credentials not set. Email not sent.")
