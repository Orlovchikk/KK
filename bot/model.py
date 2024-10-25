from dotenv import load_dotenv
import os
from os.path import dirname, join
from langchain_community.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage

dotevn_path = join(dirname(__file__), ".env")
load_dotenv(dotevn_path)

sber = os.getenv("SBER_TOKEN")

model = GigaChat(
    credentials=sber,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_PERS",
)


def analyze_profile(data):
    result = model.invoke(
        [
            SystemMessage(
                content='На основании переданных данных, сделай вывод о личности пользователя. Вывод требуется в следующем формате:\
                        личные качества: [укажи личные качества человека, исходя из его профиля. soft skills],\
                        интересы: [перечисление интересов пользователя, на основе постов и групп],\
                        обратить внимание: [указание на потенциальные риски для репутации компании (например, проявления дискриминации, нетерпимости, агрессии, упоминание наркотиков и тд.). Если ничего не нашел, то напиши "не обнаружено"],\
                        Тебе будет дан json объект со значениями posts, где будут перечислено содержание последних постов пользователя и дата поста,\
                        а также группы, на которые подписан пользователь. При описании личных качество и интересов, ориентируйся больше на посты, \
                        а при опасных моментах и на посты, и на группы.\
                        Если для анализа не хватает данных, либо мало информации о человеке, то выведи сообщение "Недостаточно данных о пользователе" и все.'
            ),
            HumanMessage(content=data),
        ]
    )
    return result.content
