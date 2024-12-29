import openai
from openai import AsyncOpenAI
from PIL import Image
import io
import logging
from config import config
import requests

openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class ContentGeneration:
    @staticmethod
    async def generate_text(prompt: str, model: str = "gpt-3.5-turbo") -> str:
        try:
            response = await openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Ошибка генерации текста: {e}")
            return "Произошла ошибка при генерации текста."

    @staticmethod
    async def generate_image(prompt: str, size: str = "1024x1024") -> io.BytesIO:
        try:
            response = await openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            image = Image.open(io.BytesIO(requests.get(image_url).content))
            output = io.BytesIO()
            image.save(output, format='PNG')
            output.seek(0)
            return output
        except Exception as e:
            logging.error(f"Ошибка генерации изображения: {e}")
            return None

