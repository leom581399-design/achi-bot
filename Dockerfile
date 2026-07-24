# ACHI BOT uchun konteyner tasviri (Fly.io, Railway va boshqa Docker-asosidagi
# hostinglarda ishlatish uchun).
FROM python:3.11-slim

# Python loglari darhol chiqishi uchun (buferlashsiz)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bot HTTP server emas - Telegram bilan "polling" orqali gaplashadi,
# shu sabab hech qanday portni ochish/EXPOSE qilish shart emas.
CMD ["python", "main.py"]
