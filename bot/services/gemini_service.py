import asyncio
import logging

import google.generativeai as genai

from bot.prompts import SYSTEM_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self, api_key: str, model: str) -> None:
        genai.configure(api_key=api_key)
        self._model_name = model

    def _generate_sync(
        self,
        user_target: str,
        user_context: str,
        user_details: str,
        user_length: str,
    ) -> str:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            user_target=user_target,
            user_context=user_context,
            user_details=user_details or "не указаны",
            user_length=user_length,
        )
        model = genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system_prompt,
        )
        response = model.generate_content(
            "Напиши сообщение согласно инструкции.",
            generation_config=genai.GenerationConfig(
                temperature=0.85,
                max_output_tokens=1200,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Gemini returned empty response")
        return text

    async def generate_love_message(
        self,
        user_target: str,
        user_context: str,
        user_details: str,
        user_length: str,
    ) -> str:
        logger.info("Requesting Gemini generation with model %s", self._model_name)
        return await asyncio.to_thread(
            self._generate_sync,
            user_target,
            user_context,
            user_details,
            user_length,
        )
