import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI, APIError, APITimeoutError

API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=API_KEY) if API_KEY else None
if client:
    print("LLM Writer: API Key detected: Yes")
else:
    print("LLM Writer: API Key detected: No")

SYSTEM_PROMPT = """
You are a senior CFO writing a financial executive summary in Arabic.
Your goal is to rewrite the provided financial analysis into a professional, concise, and high-level format suitable for a CEO or Board of Directors.
Tone: Professional, Neutral, Insightful, No emojis, No marketing fluff.
Language: Arabic only.

You will receive a JSON payload containing:
- summary: (Draft summary)
- kpis: (List of key performance indicators)
- risks: (List of identified risks)
- recommendations: (List of draft recommendations)

REQUIREMENTS:
1. DO NOT change the meaning of the data.
2. DO NOT invent numbers or metrics. Use only what is provided.
3. Rewrite the "summary" to be a single powerful paragraph highlighting the most critical insights (Revenue, Profit, Margin, and key risks).
4. Rewrite the "recommendations" to be strategic, actionable, and executive-level.
5. Output MUST be valid JSON with exactly two keys: "executive_summary" (string) and "executive_recommendations" (list of strings).
"""

async def write_executive_text(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Rewrites the financial analysis using OpenAI to produce executive-level text.
    Returns a dict with 'executive_summary' and 'executive_recommendations' or None on failure.
    Includes 1 retry mechanism.
    """
    if not client:
        print("LLM Writer: No OPENAI_API_KEY found. Skipping.")
        return None

    model = "gpt-4o" # Using a high-quality model for best Arabic writing
    
    # Prepare user content
    user_content = json.dumps(payload, ensure_ascii=False)

    async def call_api():
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"},
                temperature=0.3, # Low temperature for consistency
                timeout=10.0 # 10s strict timeout
            )
            content = response.choices[0].message.content
            if not content:
                print("LLM Writer: Empty response content.")
                return None
            
            data = json.loads(content)
            
            # Validate keys
            if "executive_summary" not in data or "executive_recommendations" not in data:
                print("LLM Writer: Missing expected keys in JSON response.")
                return None
            
            print(f"LLM: used {model} - Success")
            return data
            
        except APITimeoutError:
            print("LLM Writer: Request timed out.")
            raise # Trigger retry
        except json.JSONDecodeError:
            print("LLM Writer: Failed to decode JSON response.")
            raise # Trigger retry
        except Exception as e:
            print(f"LLM Writer Error: {e}")
            return None # Do not retry generic API errors immediately unless transient? simpler to just fail safe.
            
    # Retry logic (1 retry)
    for attempt in range(2):
        try:
            result = await call_api()
            if result:
                return result
        except Exception:
            if attempt == 0:
                print("LLM Writer: Retrying...")
                await asyncio.sleep(0.5)
            else:
                print("LLM Writer: Failed after retry.")
                
    return None
