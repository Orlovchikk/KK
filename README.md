## LinkLens - HR AI Helper

Bot - [@Orlovchik](https://github.com/Orlovchikk), Parser - [@valero-gv](https://github.com/valero-gv)

### 1. Введение

LinkLens - AI помощник, который анализирует активность кандидатов в социальных сетях и формирует психологические профили. Помогает обнаружить риски, такие как неподобающие высказывания, агрессивное поведение, аморальный контент, предотвращая наем неподходящих сотрудников.

### 2. Функциональное описание

Telegram Бот собирает информацию о странице в VK пользователя и присылает вывод, состоящий из пунктов:

- **Личные качества**
- **Интересы**
- **Потенциальные риски**

### 3. Архитектура приложения

Приложение имеет модульную структуру, где каждый компонент отвечает за определенные задачи:

- **`bot/main.py`**: Основной файл, управляющий логикой работы Telegram-бота. Обрабатывает команды и сообщения пользователей с использованием библиотеки aiogram, взаимодействует с базой данных и моделью GigaChat.
- **`bot/database.py`**: Подключение к базе данных PostgreSQL, используя библиотеку SQLAlchemy с поддержкой асинхронного доступа через asyncpg.
- **`bot/model.py`**: Обращение к GigaChat API через библиотеку gigachain-community.
- **`parser/main.go`**: Основной файл для парсера, реализованного на языке Go. Выполняет запросы к VK API.

### 4. Техническая реализация

#### 4.1 Инструменты разработки и библиотеки

- Язык: Python 3.11
- Библиотеки:
  - `aiogram`: Асинхронная библиотека для создания Telegram ботов.
  - `gigachain-community`: Фреймворк для интеграции модели GigaChat.
  - `sqlalchemy`: ORM для удобной работы с PostgreSQL.
  - `asyncpg`: Асинхронная библиотека для взаимодействия с PostgreSQL.
  - `requests`: Получение данных с URL-адреса.
  - `python-dotenv`: Загрузка переменных окружения из файла `.env`.
- Менеджер пакетов Python: Poetry
- Контейнеризация: Docker

### 5. Конфигурация Docker

- **`bot/Dockerfile`**: Образ на базе Python, устанавливает зависимости и запускает бота.
- **`parser/Dockerfile`**: Образ на базе Go, собирает и запускает парсер.
- **`docker-compose.yml`**: Определяет три сервиса:
  - `postgres`: Развертывает контейнер базы данных PostgreSQL.
  - `parser`: Стартует парсер.
  - `bot`: Запускает бота.

### 6. Развертывание и запуск

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Orlovchikk/LinkLens_HR_AI_Helper.git
```

2. Перейдите в директорию:

```bash
cd LinkLens_HR_AI_Helper/bot
```

3. Создайте файл `.env` и заполните по образцу `.env.example`, указав свои учетные данные для подключения к базе данных и токены для GigaChat API, Telegram Bot API:

```
BOT_TOKEN="telegram_bot_token"
SBER_TOKEN="gigachat_token"
HOST="postgres-LinkLens"
POSTGRES_DB="db_name"
PGUSER="dn_user"
POSTGRES_PASSWORD="db_password"
PORT=db_port
```

4. Перейдите в директорию:

```bash
cd LinkLens_HR_AI_Helper/parser
```

5. Создайте файл `.env` и заполните по образцу `.env.example`, указав токен для VK API:

```
VK_ACCESS_TOKEN="vk_access_token"
```

6. Запустите Docker Compose:

```bash
docker compose up -d
```

#### Ваш Telegram бот теперь работает!🥳 Попробуйте отправить команду `/start`.

### 7. Скриншоты, демонстрирующие работу приложения

**Пример:**

1. **Команда /start** ![Результат выполнения: `/start`](screenshots/screenshot1.jpg)

2. **Результат анализа профиля** ![Скриншот анализа профиля пользователя](screenshots/screenshot2.png)

3. **Подключение к общему балансу** ![Скриншот подключения к общему балансу](screenshots/screenshot3.png)
