import os
import sys
import json
import datetime
import asyncio
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

# Setup Paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) # server/
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
REPORT_DIR = os.path.join(BASE_DIR, 'reports')

os.makedirs(REPORT_DIR, exist_ok=True)

# Setup Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

async def main():
    # Read input file path from args
    if len(sys.argv) < 2:
        print("Error: No input file provided", file=sys.stderr)
        sys.exit(1)
        
    input_path = sys.argv[1]
    with open(input_path, 'r', encoding='utf-8') as f:
        context_data = json.load(f)

    # 1. Render HTML
    template = env.get_template('report.html')
    
    if 'timestamp' not in context_data:
        context_data['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
    html_content = template.render(**context_data)
    
    # 2. Generate PDF
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp_str}.pdf"
    output_path = os.path.join(REPORT_DIR, filename)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch() 
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.set_content(html_content)
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "40px", "right": "40px", "bottom": "40px", "left": "40px"}
        )
        await browser.close()
    
    # Print filename to stdout for caller to capture
    print(filename)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
