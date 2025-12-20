Инструкция по использованию моделей LLM-сервиса SciBox

В этой инструкции показано, как получить список моделей и выполнить запросы к ним с помощью curl. Вместо реального токена используйте переменную окружения или подставляйте свой токен в заголовке Authorization.

0. Swagger и базовые URL

Swagger: по домену https://llm.t1v.scibox.tech/ или по IP http://45.145.191.148:4000/.

Endpoint списка моделей (пример по IP): http://45.145.191.148:4000/v1/models.

Вы можете использовать либо домен без порта, либо IP с портом 4000. В командах ниже оставлен IP с портом, но доменное имя также будет работать без указания порта.

Доступные модели и RPS

bge-m3 — 7 RPS. Эмбеддинг‑модель для поиска и ранжирования.

qwen3-coder-30b-a3b-instruct-fp8 — 2 RPS. Инструкционная кодовая модель.

qwen3-32b-awq — 2 RPS. Универсальная чат‑модель.

Ограничение по RPS распространяется на одну команду (workspace). Если несколько членов команды шлют запросы параллельно, они делят общий лимит, поэтому при нагрузочных сценариях синхронизируйте отправку или ставьте очереди/ретраи.

1. Получение списка моделей

curl -H "Authorization: Bearer <YOUR_TOKEN>" \

    https://llm.t1v.scibox.tech/v1/models

Пример ответа:

{

  "data": [

    {"id": "qwen3-32b-awq", ...},

    {"id": "qwen3-coder-30b-a3b-instruct-fp8", ...},

    {"id": "bge-m3", ...}

  ],

  "object": "list"

}

---

2. Запрос к чат-моделям

Доступные чатовые модели:

qwen3-32b-awq — универсальная чат‑модель (2 RPS). Хорошо справляется с обобщёнными задачами: Q&A, суммаризация, рассуждения, инструкции, диалоги.

qwen3-coder-30b-a3b-instruct-fp8 — инструкционная модель для кода (2 RPS). Лучше работает на задачах ревью, генерации и объяснения кода, но тоже умеет отвечать на общие вопросы.

Обе модели используют endpoint /v1/chat/completions (совместим с OpenAI). Поддерживается потоковая выдача через параметр stream: true. Ключевые параметры: messages, temperature, top_p, max_tokens, presence_penalty, frequency_penalty.

2.1 qwen3-32b-awq (универсальная)

curl -X POST \

    -H "Authorization: Bearer <YOUR_TOKEN>" \

    -H "Content-Type: application/json" \

    https://llm.t1v.scibox.tech/v1/chat/completions \

    -d '{

    "model": "qwen3-32b-awq",

    "messages": [

    {"role":"system","content":"Ты дружелюбный помощник"},

    {"role":"user","content":"Расскажи анекдот"}

    ],

    "temperature": 0.7,

    "top_p": 0.9,

    "max_tokens": 256

    }'

У qwen3-32b-awqподдерживается режим reasoning/thinking. По умолчанию он включён и модель может возвращать дополнительные рассуждения. Чтобы отключить reasoning и получить только ответ, добавьте в system prompt маркер /no_think(например, {"role": "system", "content": "/no_think Ты дружелюбный помощник"}).

2.2 qwen3-coder-30b-a3b-instruct-fp8 (код-ассистент)

curl -X POST \

    -H "Authorization: Bearer <YOUR_TOKEN>" \

    -H "Content-Type: application/json" \

    https://llm.t1v.scibox.tech/v1/chat/completions \

    -d '{

    "model": "qwen3-coder-30b-a3b-instruct-fp8",

    "messages": [

    {"role":"system","content":"Ты помощник, который пишет и объясняет код"},

    {"role":"user","content":"Напиши функцию на Python, которая проверяет палиндром"}

    ],

    "temperature": 0.2,

    "top_p": 0.8,

    "max_tokens": 400

    }'

2.3 Потоковый ответ (stream)

curl -N -X POST \

    -H "Authorization: Bearer <YOUR_TOKEN>" \

    -H "Content-Type: application/json" \

    https://llm.t1v.scibox.tech/v1/chat/completions \

    -d '{

    "model": "qwen3-32b-awq",

    "messages": [{"role":"user","content":"Сделай краткое резюме книги Война и мир"}],

    "stream": true,

    "max_tokens": 400

    }'

Ответ приходит чанками (SSE). Каждая строка начинается с data: и содержит частичный фрагмент. Поток завершается сообщением data: [DONE].

---

3. Запрос к эмбеддинг‑модели bge-m3

Что это за модель:

bge-m3 — многоязычная эмбеддинг‑модель (векторизации текста) от BAAI из семейства BGE. Она возвращает числовые вектора для текста и не генерирует ответы в стиле чат‑моделей.

Подходит для задач: поиска и ранжирования (retrieval), классификации, кластеризации, дедупликации.

В этом API для неё доступен endpoint: /v1/embeddings.

Пример: эмбеддинг одной строки

curl -X POST \

    -H "Authorization: Bearer <YOUR_TOKEN>" \

    -H "Content-Type: application/json" \

    https://llm.t1v.scibox.tech/v1/embeddings \

    -d '{

    "model": "bge-m3",

    "input": "Напиши короткое стихотворение про осень"

    }'

Пример: батч из нескольких текстов

curl -X POST \

    -H "Authorization: Bearer <YOUR_TOKEN>" \

    -H "Content-Type: application/json" \

    https://llm.t1v.scibox.tech/v1/embeddings \

    -d '{

    "model": "bge-m3",

    "input": [

    "Что такое квантовая запутанность?",

    "Квантовая запутанность — это корреляция состояний частиц"

    ]

    }'

Ответ содержит массив эмбеддингов. Для поиска схожести вычисляйте метрику (например, косинусное сходство) на клиентской стороне.

---

4. Советы по использованию

Всегда указывайте заголовок Authorization: Bearer <YOUR_TOKEN>.

Заголовок Content-Type: application/json обязателен при POST-запросах.

В случае ошибки InternalServerError или 429 попробуйте повторить запрос через несколько секунд или переключиться на другую модель.

Параметры (max_tokens, temperature и др.) можно настроить по своему усмотрению. Рекомендуем посмотреть раздел «Best practices по параметрам» в репозиториях моделей.

---

5. Примеры с OpenAI Python client

Ниже показано, как использовать совместимый клиент openai (ветка openai>=1.0.0) с вашим API.

Установка:

pip install --upgrade openai

Базовый URL: можно домен без порта по HTTPS (https://llm.t1v.scibox.tech/v1) или IP с портом (http://45.145.191.148:4000/v1).

5.1 Chat Completions (non‑stream)

from openai import OpenAI

API_KEY = "<YOUR_TOKEN>"

# Вариант с доменом без порта (HTTPS):

BASE_URL = "https://llm.t1v.scibox.tech/v1"

# Альтернатива с IP:порт

# BASE_URL = "http://45.145.191.148:4000/v1"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

resp = client.chat.completions.create(

    model="qwen3-32b-awq",

    messages=[

    {"role": "system", "content": "Ты дружелюбный помощник"},

    {"role": "user", "content": "Расскажи анекдот"},

    ],

    temperature=0.7,

    top_p=0.9,

    max_tokens=256,

)

print(resp.choices[0].message.content)

Для задач ревью/генерации кода замените model на qwen3-coder-30b-a3b-instruct-fp8 и, при необходимости, скорректируйте temperature/max_tokens.

5.2 Chat Completions (stream)

from openai import OpenAI

client = OpenAI(api_key="<YOUR_TOKEN>", base_url="https://llm.t1v.scibox.tech/v1")

with client.chat.completions.stream(

    model="qwen3-32b-awq",

    messages=[{"role": "user", "content": "Сделай краткое резюме книги Война и мир"}],

    max_tokens=400,

) as stream:

    for event in stream:

    if event.type == "chunk":

    delta = getattr(event.chunk.choices[0].delta, "content", None)

    if delta:

    print(delta, end="", flush=True)

    elif event.type == "message.completed":

    print()  # newline

5.3 Embeddings

from openai import OpenAI

client = OpenAI(api_key="<YOUR_TOKEN>", base_url="https://llm.t1v.scibox.tech/v1")

emb = client.embeddings.create(

    model="bge-m3",

    input=[

    "Что такое квантовая запутанность?",

    "Квантовая запутанность — это корреляция состояний частиц",

    ],

)

print(len(emb.data), len(emb.data[0].embedding))

---

6. Поддержка и статусы ответов

Часы работы поддержки: будни с 09:00 до 18:00 (по Москве). В нерабочее время проблемы принимаются, но обработка начнётся утром следующего рабочего дня.

Перед обращением: соберите curl/request-id, таймстемпы, модель, нагрузку по RPS и текст ошибки. Часто помогает повторить запрос с меньшим числом параллельных вызовов.

Типовые статусы и что делать:

200 OK — запрос успешен, ничего делать не нужно.

400 Bad Request — проверьте JSON и список параметров (messages, model, input, пр.). Исправьте payload.

401 Unauthorized — отсутствует или неверен токен. Перепроверьте заголовок Authorization.

403 Forbidden — токен не имеет доступа к выбранной модели. Уточните доступы в поддержке.

404 Not Found — неверный URL или модель. Убедитесь, что используете https://llm.t1v.scibox.tech/v1.

429 Too Many Requests — превышен лимит RPS/квота. Уменьшите параллельность, добавьте экспоненциальный бектoff и убедитесь, что команда не превышает общие ограничения.

500/502/503 — ошибка на стороне сервиса. Повторите через 5–15 секунд; если сохраняется, отправьте лог поддержки.

Если после самостоятельных попыток проблема не решена, зафиксируйте максимум деталей и обратитесь в поддержку в рабочие часы; так вы ускорите разбор.

sk-5NTsD4a9Rif0Cwk4-p5pZQ
