import os
import cohere
from dotenv import load_dotenv

load_dotenv()
co = cohere.Client(os.getenv("COHERE_API_KEY"))

async def obtener_ingredientes_cohere(plato: str):
    prompt = f"¿Cuáles son los ingredientes necesarios para preparar '{plato}'? Devuelve solo una lista con los nombres separados por comas."
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=100,
        temperature=0.4
    )
    texto = response.generations[0].text.strip()
    return [i.strip().lower() for i in texto.split(",") if i.strip()]