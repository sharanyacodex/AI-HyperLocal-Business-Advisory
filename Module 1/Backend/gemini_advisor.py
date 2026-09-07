from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=GEMINI_API_KEY)


async def get_ai_business_advice(
    business_type,
    pincode,
    village_city,
    district,
    state,
    market_demand,
    competitor_count,
    population_density,
    purchasing_power,
    opportunity,
    profit_potential,
    risk_safety,
    feasibility_score,
    recommendation,
):

    prompt = f"""
You are an AI Rural Business Advisor.

Analyze the following business data and give simple,
practical advice to a small business owner.

Business:
{business_type}

Location:
{village_city}, {district}, {state}

Pincode:
{pincode}

Market Demand:
{market_demand}/100

Competitors:
{competitor_count}

Population Score:
{population_density}/100

Purchasing Power:
{purchasing_power}/100

Opportunity:
{opportunity}/100

Profit Potential:
{profit_potential}/100

Risk/Safety:
{risk_safety}/100

Feasibility Score:
{feasibility_score}/100

Recommendation:
{recommendation}

Give the answer in this format:

1. Business Verdict
2. Why this location is suitable
3. Main Competition Situation
4. 3 Practical Business Tips
5. Main Risk
6. Final Advice

Use very simple English.
Do not invent exact profit amounts.
Keep the answer short and useful.
"""

    try:

        chat = client.chats.create(
            model="gemini-3.7-flash"
        )

        response = chat.send_message(
            message=prompt
        )

        return {
            "success": True,
            "ai_business_advice": response.text
        }

    except Exception as e:

        print("GEMINI ERROR:", e)

        return {
            "success": False,
            "ai_business_advice": "",
            "message": "Gemini AI service unavailable."
        }