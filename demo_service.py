"""
Demo Service for Testing PR-Agent Automated Review
This file introduces intentional security and reliability scenarios to test the webhook and review pipeline.
"""
import subprocess


# 1. Hardcoded API Secret (Triggers SEC-HARDCODED-SECRET)
api_key = "dummy_test_token_not_a_real_secret"


def get_user_records(db_cursor, user_id: str):
    """Fetch user profile from database."""
    # 2. SQL Query String Concatenation (Triggers SEC-SQL-CONCAT)
    db_cursor.execute(f"SELECT * FROM users WHERE user_id = '{user_id}' AND is_active = 1")

    # 3. Debug print in production code (Triggers REL-DEBUG-PRINT)
    print(f"[DEBUG] Fetching records for user: {user_id}")


def run_system_healthcheck(host_target: str) -> str:
    """Execute host ping via system command."""
    # 4. Command Injection via shell=True (Triggers SEC-SUBPROCESS-SHELL)
    result = subprocess.run(f"ping -c 1 {host_target}", shell=True, capture_output=True)
    return result.stdout.decode(errors="ignore")


def calculate_tax(amount: float, tax_rate: float) -> float:
    """Calculate tax with bare exception catch."""
    try:
        if tax_rate < 0 or tax_rate > 1:
            raise ValueError("Invalid tax rate range")
        return amount * tax_rate
    except:
        # 5. Bare except clause silently swallowing errors (Triggers REL-EMPTY-EXCEPT)
        pass
    return 0.0
