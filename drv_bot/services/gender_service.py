import asyncio
import os
import json
import aiohttp
from dotenv import load_dotenv

load_dotenv()
GENDERIZE_API_KEY = os.getenv("GENDER_API")

# Path to the local gender dictionary
LOOKUP_FILE = "./gender_lookup.json"

# Ensure the file exists
if not os.path.exists(LOOKUP_FILE):
    with open(LOOKUP_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Safely load the file (after ensuring existence)
try:
    with open(LOOKUP_FILE, "r", encoding="utf-8") as f:
        LOCAL_GENDER_DICT = {k.lower(): v for k, v in json.load(f).items()}
except Exception as e:
    LOCAL_GENDER_DICT = {}
    print(f"Failed to load gender lookup file: {e}")


async def query_gender_api(name: str) -> dict | None:
    """
    Calls the genderize.io API for a name and returns full response.
    """
    url = f"https://api.genderize.io?name={name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
    return None


async def get_gender(name: str) -> str | None:
    """
    Returns a simplified label based on local data or genderize.io:
    - "female" if > 70% confidence
    - "femboy" if female between 40%–70%
    - "male" if detected as male
    """
    name_lower = name.lower()

    if name_lower in LOCAL_GENDER_DICT:
        return LOCAL_GENDER_DICT[name_lower]

    data = await query_gender_api(name_lower)

    if not data:
        print(f"from API genderize.io: No data found {data}")

        return None

    gender = data.get("gender")
    probability = data.get("probability", 0)
    print(f"{probability}% confidence")

    if gender == "female":
        if probability >= 0.95:
            return "female"
        elif 0.40 <= probability < 0.95:
            return "femboy"
    elif gender == "male":

        if probability >= 0.97:
            return "male"
        elif 0.40 <= probability < 0.97:
            return "femboy"
        return "femboy"

    return None


async def is_male(name: str) -> bool:
    """
    Returns True if gender is confidently male (>= 70%),
    or if locally marked as male.
    """
    name_lower = name.lower()

    if LOCAL_GENDER_DICT.get(name_lower) == "male":
        return True

    data = await query_gender_api(name_lower)
    if not data:
        return False


    return data.get("gender") == "male" and data.get("probability", 0) >= 0.70

# Test function for running the service directly
async def test_gender(name):
    result = await get_gender(name)
    print(f"Gender for '{name}': {result}")
if __name__ == "__main__":
    asyncio.run(test_gender("payam"))