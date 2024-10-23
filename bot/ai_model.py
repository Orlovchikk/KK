import json
import os
from os.path import dirname, join

from dotenv import load_dotenv
from langchain_community.chat_models import GigaChat
from langchain_core.messages import HumanMessage

dotevn_path = join(dirname(__file__), ".env")
load_dotenv(dotevn_path)

sber = os.getenv("SBER_TOKEN")

model = GigaChat(
    credentials=sber,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS",
)

class Model():
    def analyze_profile(data):
        # model.invoke([HumanMessage(content="Привет!")])
        return 'model answer'
