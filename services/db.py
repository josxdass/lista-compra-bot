import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["listaCompra"]
productos = db["productos"]

def insertar_producto(nombre: str):
    productos.insert_one({"nombre": nombre.lower()})

def borrar_producto(nombre: str) -> bool:
    result = productos.delete_one({"nombre": nombre.lower()})
    return result.deleted_count > 0

def obtener_lista():
    return [p["nombre"] for p in productos.find()]

def vaciar_lista():
    productos.delete_many({})