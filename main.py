import telebot
import requests
import time
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from threading import Thread
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Хранение ID разрешённого пользователя
ALLOWED_USER_ID = 7777713334

# Флаг для отслеживания статуса парсинга
parsing_active = False

def get_phone(item_id):
    try:
        url = f"https://youla.ru/web-api/items/{item_id}/phone"
        headers = {
            "User-Agent": UserAgent().random,
            "Accept": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            phone = data.get("phone", "")
            if phone:
                return phone
    except Exception as e:
        print("Ошибка получения телефона:", e)
    return None

def is_user_without_reviews(soup):
    try:
        reviews_tag = soup.find("div", {"data-testid": "seller-rating-summary"})
        return reviews_tag is None
    except:
        return False

def parse_youla(min_views):
    url = "https://youla.ru"
    categories = [
        "turizm", "odezhda-obuv", "elektronika", "bytovaya-tehnika", 
        "detskiy-mir", "hobbi-otdyh-i-sport", "zhivotnye", "uslugi"
    ]

    results = []

    for category in categories:
        try:
            full_url = f"{url}/{category}"
            headers = {
                "User-Agent": UserAgent().random
            }
            response = requests.get(full_url, headers=headers)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            items = soup.select('a[href^="/item/"]')

            for item in items:
                try:
                    href = item.get("href")
                    item_url = url + href
                    item_id = href.split("/")[-1]

                    item_resp = requests.get(item_url, headers=headers)
                    item_soup = BeautifulSoup(item_resp.text, "html.parser")

                    if not is_user_without_reviews(item_soup):
                        continue

                    views_tag = item_soup.find("span", string=re.compile("Просмотров:"))
                    if views_tag:
                        views_match = re.search(r"Просмотров:\s*(\d+)", views_tag.text)
                        if views_match and int(views_match.group(1)) > min_views:
                            continue

                    title_tag = item_soup.find("h1")
                    price_tag = item_soup.find("h3")
                    title = title_tag.text.strip() if title_tag else "Без названия"
                    price = price_tag.text.strip() if price_tag else "Не указана"

                    phone = get_phone(item_id)
                    if not phone:
                        continue

                    result = {
                        "title": title,
                        "price": price,
                        "phone": phone,
                        "url": item_url
                    }

                    # Добавляем в список объявлений
                    results.append(result)

                except Exception as inner_error:
                    print("Ошибка при обработке объявления:", inner_error)

        except Exception as e:
            print("Ошибка при парсинге категории:", e)

    return results


@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.id != ALLOWED_USER_ID:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён.")
        return
    bot.send_message(message.chat.id, "👋 Бот запущен. Напиши /parse чтобы начать.")


@bot.message_handler(commands=['parse'])
def handle_parse(message):
    if message.chat.id != ALLOWED_USER_ID:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа.")
        return

    global parsing_active
    if parsing_active:
        bot.send_message(message.chat.id, "⏳ Парсинг уже идёт...")
        return

    parsing_active = True
    bot.send_message(message.chat.id, "🔍 Начинаю поиск объявлений...")

    def task():
        try:
            items = parse_youla(min_views=50)
            if not items:
                bot.send_message(message.chat.id, "❌ Ничего не найдено.")
            else:
                for item in items:
                    text = (
                        f"🛍 Название товара: {item['title']}\n"
                        f"💰 Цена: {item['price']}\n\n"
                        f"🔗 Ссылка: {item['url']}\n"
                        f"📞 Номер: {item['phone']}\n\n"
                        f"💬 Telegram: https://t.me/{item['phone'].replace('+', '')}?text="
                        f"Здравствуйте.%20Подскажите,%20пожалуйста,%20объявление%20о%20продаже%20{item['title']}%20за%20{item['price']}%20еще%20актуально?"
                    )
                    bot.send_message(message.chat.id, text)
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Ошибка парсинга: {e}")
        finally:
            global parsing_active
            parsing_active = False

    Thread(target=task).start()


bot.polling(none_stop=True)
