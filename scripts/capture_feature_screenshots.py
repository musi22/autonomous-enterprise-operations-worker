import asyncio
import os
import httpx
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:3000"
API_BASE = "http://127.0.0.1:8000"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "screenshots")

async def capture_all_feature_screenshots():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Reset DB to pristine state
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(f"{API_BASE}/api/v1/admin/reset-db")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Overview Dashboard
        try:
            print("[Screenshot] 1. Overview Dashboard...")
            await page.goto(BASE_URL, wait_until="networkidle")
            await page.click("button:has-text('Overview')")
            await page.wait_for_selector("text=Task Success Rate", timeout=8000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "01_overview_dashboard.png"))
        except Exception as e:
            print(f"Error 1: {e}")

        # 2. Autonomous Worker Execution
        try:
            print("[Screenshot] 2. Autonomous Worker Execution...")
            await page.click("button:has-text('Autonomous Worker')")
            await page.wait_for_selector("text=Run Autonomous Task", timeout=5000)
            await page.click("button:has-text('Run Autonomous Task')")
            await page.wait_for_selector("text=SUCCESS", timeout=25000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "02_autonomous_worker_execution.png"))
        except Exception as e:
            print(f"Error 2: {e}")

        # 3. Scenario Lab & Policy Enforcement
        try:
            print("[Screenshot] 3. Scenario Lab & Policy Enforcement...")
            await page.click("button:has-text('Scenario Lab')")
            await page.wait_for_selector("text=Scenarios (20)", timeout=5000)
            await page.click("button:has-text('Cross-Customer Order Access Attempt')")
            await page.click("button:has-text('Guarded Mode')")
            await page.click("button:has-text('Execute Guarded Agent')")
            await page.wait_for_selector("text=REJECTED_POLICY", timeout=15000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "03_scenario_lab_policy.png"))
        except Exception as e:
            print(f"Error 3: {e}")

        # 4. Trace Explorer & 9-Node Timeline
        try:
            print("[Screenshot] 4. Trace Explorer & 9-Node Timeline...")
            await page.click("button:has-text('Explore Full 9-Node Trace')")
            await page.wait_for_selector("text=LangGraph 9-Node Execution Timeline", timeout=10000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "04_trace_explorer_timeline.png"))
        except Exception as e:
            print(f"Error 4: {e}")

        # 5. Approval Inbox
        try:
            print("[Screenshot] 5. Approval Inbox...")
            await page.click("button:has-text('Approval Inbox')")
            await page.wait_for_selector("text=Human Approval Inbox", timeout=5000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "05_approval_inbox.png"))
        except Exception as e:
            print(f"Error 5: {e}")

        # 6. Benchmark & Release Gates
        try:
            print("[Screenshot] 6. Benchmark & Release Gates...")
            await page.click("button:has-text('Benchmark & Gates')")
            await page.wait_for_selector("text=Dual-Agent Comparative Benchmark", timeout=5000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "06_benchmark_comparison.png"))
        except Exception as e:
            print(f"Error 6: {e}")

        # 7. Evidence Ledger & Tamper Detection
        try:
            print("[Screenshot] 7. Evidence Ledger & Tamper Detection...")
            await page.click("button:has-text('Evidence Ledger')")
            await page.wait_for_selector("text=Tamper-Evident Cryptographic Evidence Ledger", timeout=5000)
            await page.click("button:has-text('Simulate DB Tampering')")
            await page.wait_for_selector("text=SECURITY ALERT: AUDIT TAMPERING OR CORRUPTION DETECTED!", timeout=10000)
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "07_evidence_ledger_tamper.png"))
        except Exception as e:
            print(f"Error 7: {e}")

        # 8. Synthetic ERP Sandbox Portal
        try:
            print("[Screenshot] 8. Synthetic ERP Sandbox Portal...")
            await page.goto(f"{API_BASE}/sandbox/finance", wait_until="networkidle")
            await page.screenshot(path=os.path.join(OUTPUT_DIR, "08_synthetic_erp_sandbox.png"))
        except Exception as e:
            print(f"Error 8: {e}")

        # Reset DB back to clean state
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(f"{API_BASE}/api/v1/admin/reset-db")

        await browser.close()
        print(f"\n[DONE] Feature screenshots captured in: {OUTPUT_DIR}")

if __name__ == "__main__":
    asyncio.run(capture_all_feature_screenshots())
