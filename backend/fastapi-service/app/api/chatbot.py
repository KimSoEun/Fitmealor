"""
Chatbot API endpoints for meal recommendation filtering
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import httpx
import json
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY environment variable is not set")


class ChatRequest(BaseModel):
    message: str
    language: str = "ko"  # "ko" or "en"


class MealFilters(BaseModel):
    maxCalories: Optional[int] = None
    minProtein: Optional[float] = None
    maxCarbs: Optional[float] = None
    maxFat: Optional[float] = None
    excludeIngredients: Optional[List[str]] = None
    includeIngredients: Optional[List[str]] = None
    preferHighProtein: Optional[bool] = None
    preferLowCarb: Optional[bool] = None


class ChatResponse(BaseModel):
    message: str
    filters: Optional[MealFilters] = None


@router.post("/chat", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Process user's chat message and extract meal filtering preferences using OpenAI
    """
    try:
        logger.info(f"Processing chat message: {request.message}")
        logger.info(f"Language: {request.language}")

        # Prepare OpenAI API request
        system_prompt = f"""You are a helpful meal recommendation assistant. Analyze the user's input about their condition, preferences, or dietary needs and extract structured filters.

Respond in JSON format with two fields:
1. "message": A friendly, conversational response to the user in {'English' if request.language == 'en' else 'Korean'}
2. "filters": An object with these optional fields:
   - maxCalories (number): Maximum calories per meal
   - minProtein (number): Minimum protein in grams
   - maxCarbs (number): Maximum carbs in grams
   - maxFat (number): Maximum fat in grams
   - excludeIngredients (string[]): Ingredients to avoid (in Korean)
   - includeIngredients (string[]): Ingredients to prefer (in Korean)
   - preferHighProtein (boolean): Prefer high protein meals
   - preferLowCarb (boolean): Prefer low carb meals

Example response:
{{
  "message": "I understand you want high protein meals! I'll filter the recommendations to show meals with at least 25g of protein.",
  "filters": {{
    "minProtein": 25,
    "preferHighProtein": true
  }}
}}"""

        async with httpx.AsyncClient(timeout=30.0) as client:
            openai_response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": request.message}
                    ],
                    "temperature": 0.7
                }
            )

        if openai_response.status_code != 200:
            logger.error(f"OpenAI API error: {openai_response.status_code} - {openai_response.text}")
            raise HTTPException(
                status_code=502,
                detail=f"OpenAI API request failed: {openai_response.status_code}"
            )

        data = openai_response.json()
        logger.info(f"OpenAI response: {data}")

        assistant_message = data["choices"][0]["message"]["content"]
        logger.info(f"Assistant message: {assistant_message}")

        # Parse the JSON response
        try:
            parsed_response = json.loads(assistant_message)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response content: {assistant_message}")
            # Return a friendly error message
            return ChatResponse(
                message="죄송합니다. 메시지를 이해하는데 문제가 있었습니다. 다시 시도해주세요." if request.language == "ko" else "Sorry, I had trouble understanding. Please try again.",
                filters=None
            )

        # Extract message and filters
        response_message = parsed_response.get("message", "")
        filters_dict = parsed_response.get("filters", {})

        # Convert filters to MealFilters model if present
        filters = None
        if filters_dict and isinstance(filters_dict, dict):
            filters = MealFilters(**filters_dict)
            logger.info(f"Extracted filters: {filters}")

        return ChatResponse(
            message=response_message,
            filters=filters
        )

    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out")
        raise HTTPException(
            status_code=504,
            detail="Request timed out. Please try again."
        )
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to communicate with AI service: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chatbot: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
