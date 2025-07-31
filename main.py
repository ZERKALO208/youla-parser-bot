import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import urllib.parse

# Вставь сюда свой Telegram ID (только ты сможешь пользоваться ботом)
ALLOWED_USERS = [7777713334]

BOT_TOKEN = "ВАШ_ТОКЕН_ТУТ"  # Замени на свой токен бота

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

MAX_VIEWS = 50  # Можно менять через переменные окружения или тут

def is_allowed(user_id):
    return user_id in ALLOWED_USERS

def create_whatsapp_link(phone, name, price):
    text = f"Здравствуйте. Подскажите, пожалуйста, объявление о продаже {name} за {price} еще актуально?"
    text_encoded = urllib.parse.quote(text)
    phone_clean = phone.replace("+", "").replace(" ", "").replace("-", "")
    return f"https://wa.me/{phone_clean}?text={text_encoded}"

def create_telegram_link(phone, name, price):
    text = f"Здравствуйте. Подскажите, пожалуйста, объявление о продаже {name} за {price} еще актуально?"
    text_encoded = urllib.parse.quote(text)
    return f"https://t.me/share/url?url=tg://&text={text_encoded}"

async def send_advertisement(ad):
    name = ad['name']
    price = ad['price']
    link = ad['link']
    phone = ad['phone']

    whatsapp_link = create_whatsapp_link(phone, name, price)
    telegram_link = create_telegram_link(phone, name, price)

    message = (
        f"🛍 Название товара: {name}\n"
        f"💰 Цена: {price}\n\n"
        f"🔗 Ссылка: [Открыть ссылку]({link})\n"
        f"📞 Номер: {phone}\n\n"
        f"🟢 WhatsApp API: [Связаться в WA]({whatsapp_link})\n"
        f"📨 Телеграм: [Связаться в ТГ]({telegram_link})"
    )
    return message

async def parse_youla():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    ads = []

    # Здесь можно добавить список категорий Youla
    categories = [
        "https://youla.ru/moskva?q=&max_view=50"  # пример категории с фильтром по просмотрам
        # Добавь другие категории при необходимости
    ]

    for category_url in categories:
        driver.get(category_url)
        time.sleep(3)  # Ждем загрузки страницы

        items = driver.find_elements(By.CSS_SELECTOR, "a.snippet-link")
        for item in items:
            try:
                link = item.get_attribute("href")
                name = item.find_element(By.CSS_SELECTOR, ".snippet-title").text
                price = item.find_element(By.CSS_SELECTOR, ".price").text

                driver.get(link)
                time.sleep(2)

                # Номер телефона (в зависимости от сайта, может понадобиться дополнительный парсинг)
                phone = driver.find_element(By.CSS_SELECTOR, ".seller-phone").text

                # Проверка отзывов продавца (пример, нужно подстроить под сайт)
                reviews = driver.find_elements(By.CSS_SELECTOR, ".seller-reviews")
                if reviews:
                    continue  # пропускаем если есть отзывы

                # Добавляем в список объявлений
