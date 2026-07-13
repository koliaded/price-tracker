import asyncio
import re
import os
import requests
from playwright.async_api import async_playwright

# 🛒 ВАШ СПИСОК КОМПЛЕКТУЮЧИХ ДЛЯ СЕРВЕРА
TRACKING_LIST = [
    # --- ПРОЦЕСОРИ (CPU) ---
    {"category": "💻 CPU", "name": "Ryzen 9 9950X (Exe)", "url": "https://exe.ua/product-p663805/"},
    {"category": "💻 CPU", "name": "Ryzen 9 9950X (Rozetka)", "url": "https://hard.rozetka.com.ua/ua/processors-amd-151522085/p4548383908/"},
    {"category": "💻 CPU", "name": "Ryzen 9 9950X (Hotline)", "url": "https://hotline.ua/ua/computer-processory/amd-ryzen-5-5600x-100-100000065box/"},

    # --- МАТЕРИНСЬКІ ПЛАТИ ---
    {"category": "🔌 Материнка", "name": "Плата (Приклад Exe)", "url": "https://exe.ua/"},

    # --- ОПЕРАТИВНА ПАМ'ЯТЬ (RAM) ---
    {"category": "🧠 Оперативка", "name": "RAM (Приклад Rozetka)", "url": "https://rozetka.com.ua.ua/"},

    # --- НАКОПИЧУВАЧІ (SSD) ---
    {"category": "💽 Накопичувач SSD", "name": "SSD (Приклад Hotline)", "url": "https://hotline.ua/ua/"},

    # --- БЛОКИ ЖИВЛЕННЯ ---
    {"category": "⚡ Блок живлення", "name": "БЖ (Приклад)", "url": "https://exe.ua/"},

    # --- ОХОЛОДЖЕННЯ ---
    {"category": "❄️ Охолодження", "name": "Кулер/Водянка", "url": "https://exe.ua/"},

    # --- ВІДЕОКАРТИ (GPU) ---
    {"category": "🎮 Відеокарта", "name": "GPU для сервера", "url": "https://exe.ua/"}
]

async def check_product(page, item):
    url = item['url']
    url_lower = url.lower()
    
    # Пропускаємо заглушки
    if url in ["https://exe.ua/", "https://rozetka.com.ua.ua/", "https://hotline.ua/ua/"]:
        return None
        
    try:
        # Чекаємо довше (до 60 сек) і даємо 6 секунд на повне відмальовування цін
        await page.goto(url, timeout=60000, wait_until="load")
        await page.wait_for_timeout(6000)
        
        body_text = await page.inner_text('body')
        body_text_lower = body_text.lower()
        price = "Не знайдено"
        status = "⚪ Невідомо"
        
        # Rozetka
        if "rozetka.com.ua" in url_lower:
            for sel in ['p.product-prices__big', '.product-price__big', 'div.product-price']:
                if await page.locator(sel).count() > 0:
                    price = (await page.locator(sel).first.inner_text()).strip().replace('\n', ' ')
                    break
            status = "🔴 Немає" if "немає в наявності" in body_text_lower or "закінчився" in body_text_lower else "🟢 Є"

        # Hotline
        elif "hotline.ua" in url_lower:
            for sel in ['.price__value', '.price-md', '.price-lg', '.price-line__price', 'span.price-format']:
                if await page.locator(sel).count() > 0:
                    price = (await page.locator(sel).first.inner_text()).strip().replace('\n', ' ')
                    break
            status = "🔴 Немає" if "немає в магазинах" in body_text_lower or "знято з виробництва" in body_text_lower else "🟢 Є пропозиції"

        # Exe.ua
        else:
            for sel in ['.price-new', '.product-price .price', '.price', '.current-price']:
                if await page.locator(sel).count() > 0:
                    price = (await page.locator(sel).first.inner_text()).strip().replace('\n', ' ')
                    break
            status = "🟢 Є" if "в наявності" in body_text_lower or "купити" in body_text_lower else "🔴 Немає"

        return {
            "category": item['category'], "name": item['name'], 
            "price": price, "status": status, "url": url
        }
    except Exception as e:
        return {"category": item['category'], "name": item['name'], "price": "Помилка завантаження", "status": "❌", "url": url}

def send_telegram_message(text):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Помилка: Токени Telegram не знайдені в Secrets!")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("🔔 Звіт успішно надіслано в Telegram!")
        else:
            print(f"❌ Помилка відправки в Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Не вдалося надіслати повідомлення: {e}")

async def main():
    print("=== ЗАПУСК МОНІТОРИНГУ ДЛЯ СЕРВЕРА ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Додаємо маскування під звичайного користувача з України
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="uk-UA",
            timezone_id="Europe/Kiev"
        )
        await context.set_extra_http_headers({
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
        
        page = await context.new_page()
        
        results = []
        for item in TRACKING_LIST:
            res = await check_product(page, item)
            if res:
                results.append(res)
            await asyncio.sleep(5) # Робимо паузу 5 секунд між сайтами, щоб не забанили
            
        await browser.close()
    
    if not results:
        print("Немає реальних товарів для звіту.")
        return

    # Формуємо красиве повідомлення для Telegram
    msg = "📊 *ЗВІТ ПРО ЦІНИ НА КОМПЛЕКТУЮЧІ СЕРВЕРА*\n"
    msg += "=============================\n"
    
    current_cat = ""
    for r in results:
        if r["category"] != current_cat:
            current_cat = r["category"]
            msg += f"\n*{current_cat}*:\n"
        
        msg += f"• {r['name']}: *{r['price']}* ({r['status']})\n"
        
    msg += "\n=============================\n"
    msg += "🤖 Бот працює в штатному режимі."
    
    print(msg) # Вивід в консоль GitHub
    send_telegram_message(msg)

if __name__ == "__main__":
    asyncio.run(main())
