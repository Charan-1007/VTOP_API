from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import time
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import random
import sys
import asyncio
import re
from typing import Optional

app = FastAPI()

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_methods=["GET"],  # Only allow GET requests
    allow_headers=["*"],  # Allows all headers
)

# Preload JavaScript files to avoid repeated disk I/O
def preload_script(path):
    with open(path, 'r') as f:
        return f.read()

CAPTCHA_SOLVER_SCRIPT = preload_script("utilities/captchasolver.js")
SEMESTER_SCRIPT = preload_script("utilities/scraper.js")
JS_SCRIPTS = {
    "Attendance": preload_script("utilities/Attendancescraper.js"),
    "Course": preload_script("utilities/Coursescraper.js"),
    "Marks": preload_script("utilities/Marksscraper.js"),
    "CGPA": preload_script("utilities/CGPAscraper.js"),
    "ExamSchedule": preload_script("utilities/ExamSchedulescraper.js"),
}

USER_AGENT_STRINGS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.2227.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
]

async def execute_javascript(page, script, semId: Optional[str] = None):
    """
    Executes a provided JavaScript string on the page.
    Optionally replaces standalone occurrences of 'semId' with the provided semId (wrapped as a string literal).
    Returns the parsed JSON if possible.
    """
    if semId:
        # Replace only standalone 'semId' occurrences using regex word boundaries.
        script = re.sub(r"\bsemId\b", f"'{semId}'", script)
    try:
        result = await page.evaluate(script)
        try:
            return json.loads(result)
        except Exception:
            return result
    except Exception as e:
        print(f"Error executing JS: {e}")
        return None

async def solve_captcha(page):
    """
    Executes the captcha solver JavaScript.
    """
    try:
        await page.evaluate(CAPTCHA_SOLVER_SCRIPT)
        print("Captcha solver executed.")
    except Exception as e:
        print(f"Error solving captcha: {e}")

async def check_for_errors(page):
    """
    Checks the page content for error messages quickly.
    Returns one of: "captcha", "login", "credentials", or None.
    """
    try:
        body_text = await page.inner_text("body", timeout=500)
        if "Invalid Captcha" in body_text:
            return "captcha"
        elif "Invalid LoginId/Password" in body_text:
            return "login"
        elif "Invalid credentials." in body_text:
            return "credentials"
        return None
    except PlaywrightTimeoutError:
        return None
    except Exception as e:
        print(f"Error checking errors: {e}")
        return None

async def get_vtop_data(username: str, password: str, semIndex: Optional[int] = None):
    Alldata = {}
    semId = None  # This will hold the actual semester ID after extraction
    
    async with async_playwright() as p:
        try:
            # Using headless mode to reduce rendering overhead
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=random.choice(USER_AGENT_STRINGS))
            page = await context.new_page()
            
            # Navigate to the initial page
            await page.goto("https://vtop.vit.ac.in/vtop/content", wait_until="domcontentloaded")
            await page.wait_for_selector("#stdForm", state="visible", timeout=5000)
            print("Login form loaded")
            
            # Click the login form and wait for navigation
            async with page.expect_navigation(timeout=5000):
                await page.click("#stdForm")
            await page.wait_for_selector(":has-text('VTOP Login')", state="visible", timeout=5000)
            print("Login page fully loaded")
            
            # Wait for the captcha element
            while True:
                try:
                    await page.wait_for_selector("#captchaStr", state="visible", timeout=1000)
                    print("Captcha found. Proceeding with login.")
                    break
                except PlaywrightTimeoutError:
                    print("Captcha not detected, reloading page quickly...")
                    await page.reload()
            
            # Fill credentials
            await page.fill("#username", username)
            await page.fill("#password", password)
            
            # Solve captcha and check for errors with minimal waiting
            print("Solving Captcha...")
            await solve_captcha(page)
            try:
                await page.wait_for_load_state("networkidle", timeout=3000)
            except PlaywrightTimeoutError:
                pass
            error_type = await check_for_errors(page)
            if error_type:
                if error_type == "captcha":
                    print("Invalid Captcha detected. Retrying captcha solver...")
                    max_retries = 5
                    for attempt in range(max_retries):
                        await solve_captcha(page)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=3000)
                        except PlaywrightTimeoutError:
                            pass
                        await asyncio.sleep(0.5)
                        error_type = await check_for_errors(page)
                        if not error_type and page.url.startswith("https://vtop.vit.ac.in/vtop/content"):
                            print("Captcha solved successfully.")
                            break
                        print(f"Retry {attempt+1} for captcha.")
                    else:
                        print("Max captcha retries exceeded. Exiting.")
                        await browser.close()
                        raise HTTPException(status_code=400, detail="Captcha solving failed.")
                elif error_type in ("login", "credentials"):
                    print(f"Error: {error_type} issue detected. Please check your credentials.")
                    await browser.close()
                    raise HTTPException(status_code=401, detail="Invalid credentials.")
                else:
                    print("Unknown error detected. Exiting.")
                    await browser.close()
                    raise HTTPException(status_code=500, detail="Unknown error occurred.")
            
            # Verify login by checking URL
            if not page.url.startswith("https://vtop.vit.ac.in/vtop/content"):
                print("Login unsuccessful. Exiting.")
                await browser.close()
                raise HTTPException(status_code=401, detail="Login failed.")
            
            print("Login successful. Proceeding to get data...")
            
            # Get semester data
            sem_data = await execute_javascript(page, SEMESTER_SCRIPT)
            if sem_data:
                Alldata['semester'] = sem_data
                try:
                    # Use semIndex if provided, otherwise default to 0 (first semester)
                    index = semIndex if semIndex is not None else 0
                    semId = sem_data["semesters"][index]["id"]
                except Exception as e:
                    print("Error extracting semId using semIndex:", e)
                    semId = None
            else:
                semId = None
                print("Failed to get semester data.")
            
            # Execute other JavaScript scrapers with the semId replaced
            for key, script in JS_SCRIPTS.items():
                data = await execute_javascript(page, script, semId)
                if data is not None:
                    Alldata[key] = data
            
            await browser.close()
            return Alldata
            
        except Exception as e:
            print(f"Error during scraping: {e}")
            raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/vtopdata")
async def get_data(
    username: str = Query(..., description="VTOP username"),
    password: str = Query(..., description="VTOP password"),
    semIndex: Optional[int] = Query(0, description="Semester index (0 for first, 1 for second, etc.)")
):
    try:
        data = await get_vtop_data(username, password, semIndex)
        return {
            "status": "success",
            "data": data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)