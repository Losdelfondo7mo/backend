from pydantic_settings import BaseSettings
from typing import List
import os

MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")