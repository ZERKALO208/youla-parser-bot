# Используем официальный Python 3.11 образ
FROM python:3.11-slim

# Устанавливаем зависимости для selenium и хрома
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium-driver \
    chromium

# Устанавливаем python библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект внутрь контейнера
COPY . /app
WORKDIR /app

# Запускаем бота
CMD ["python", "main.py"]
