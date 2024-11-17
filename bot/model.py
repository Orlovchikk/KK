import os
from os.path import dirname, join

from dotenv import load_dotenv
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import SystemMessage, HumanMessage

dotevn_path = join(dirname(__file__), ".env")
load_dotenv(dotevn_path)

sber = os.getenv("SBER_TOKEN")

model = GigaChat(
    credentials=sber,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS",
)


async def analyze_profile(data):
    result = model.invoke(
        [
            SystemMessage(
                content=f"На основании переданных данных сделай вывод о личности пользователя. \
                        Тебе будет предоставлен JSON-объект с полями posts, в котором перечислено содержание последних постов пользователя и даты этих постов, \
                        а также группы, на которые подписан пользователь. При описании личных качеств и интересов ориентируйся в первую очередь на посты, \
                        а при оценке рисков учитывай как посты, так и группы.\
                        Если для анализа недостаточно данных или информации о человеке слишком мало, выведи сообщение 'Недостаточно данных о пользователе.' и завершай.\
                        Формат вывода должен быть следующим:\
                        ```Личные качества: [укажи личные качества человека, исходя из его профиля (soft skills)].\
                        Интересы: [перечисление интересов пользователя, основанных на его постах и группах].]\
                        Обратить внимание: [указание на потенциальные риски для репутации компании, такие как неподобающие высказывания, агрессивное поведение или аморальный контент.\
                        Если ничего не найдено, напиши 'не обнаружено'].```\
                        Данные для анализа: ```json \
                        {data}\
                        ```"
            ),
        ]
    )
    return result.content
