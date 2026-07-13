import asyncio
import re
from playwright.async_api import async_playwright

# 🛒 СЮДИ ВСТАВЛЯЙТЕ СВОЇ РЕАЛЬНІ ПОСИЛАННЯ НА ТОВАРИ З РОЗЕТКИ, ХОТЛАЙНУ ТА ЕКСЕ
TRACKING_LIST = [
    {
        "name": "Процесор AMD (Приклад Exe.ua)", 
        "url": "https://exe.ua/product-p663805/"
    },
    {
        "name": "Товар на Rozetka (Приклад)", 
        "url": "https://rozetka.com.ua/ua/asus-90mr00u2-m00ay0/p412197771/"
    },
    {
        "name": "Товар на Hotline (Приклад)", 
        "url": "https://hotline.ua/ua/computer-processory/amd-ryzen-5-5600x-100-100000065box/"
    }
]

async def check_product(page, item):
    url = item['url']
    url_lower = url.lower()
    print(f"🔎 Перевіряємо сторінку: {url}")
    
    try:
        # Перехід на сайт з таймаутом 45 секунд
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000) # Очікування завантаження скриптів
        
        body_text = await page.inner_text('body')
        body_text_lower = body_text.lower()
        
        price = "Не знайдено"
        status = "⚪ Невідомо"
        discount = "Ні"
        
        # --- 1. ЛОГІКА ДЛЯ ROZETKA ---
        if "rozetka.com.ua" in url_lower:
            # Шукаємо ціну через популярні класи Розетки
            for sel in ['.product-price__big', '.product-prices__big', '.product-trade-price']:
                if await page.locator(sel).count() > 0:
                    text = await page.locator(sel).first.inner_text()
                    if any(char.isdigit() for char in text):
                        price = text.strip().replace('\n', ' ')
                        break
            
            if "немає в наявності" in body_text_lower or "закінчився" in body_text_lower:
                status = "🔴 Немає в наявності"
            else:
                status = "🟢 В наявності"

        # --- 2. ЛОГІКА ДЛЯ HOTLINE ---
        elif "hotline.ua" in url_lower:
            # Hotline — агрегатор, шукаємо діапазон або стартову ціну
            for sel in ['.price-line__price', 'span.price-format', '.content-title__price']:
                if await page.locator(sel).count() > 0:
                    text = await page.locator(sel).first.inner_text()
                    if any(char.isdigit() for char in text):
                        price = text.strip().replace('\n', ' ')
                        break
            
            if "немає в магазинах" in body_text_lower or "немає пропозицій" in body_text_lower:
                status = "🔴 Немає в магазинах"
            else:
                status = "🟢 Є пропозиції від магазинів"

        # --- 3. ЛОГІКА ДЛЯ EXE.UA ---
        else:
            price_elements = await page.locator('.price, .product-price, .new-price, .current-price').all_inner_texts()
            if price_elements:
                price = price_elements[0].strip().replace('\n', ' ')
            
            if "в наявності" in body_text_lower or "є в наявності" in body_text_lower:
                status = "🟢 В наявності"
            elif "під замовлення" in body_text_lower:
                status = "🟡 Під замовлення"
            else:
                status = "🔴 Немає в наявності"

        # --- УНІВЕРСАЛЬНИЙ РЕЗЕРВНИЙ ПОШУК ЦІНИ ---
        # Якщо специфічні класи не спрацювали, шукаємо будь-які цифри поруч із "грн"
        if price == "Не знайдено":
            match = re.search(r'(\d[\d\s ]*)\s*грн', body_text)
            if match:
                price = f"{match.group(1).strip()} грн"

        # Перевірка акцій (спільна для всіх)
        if "акція" in body_text_lower or "знижка" in body_text_lower or "скидка" in body_text_lower:
            discount = "🔥 Так (Діє акційна ціна!)"

        return {
            "name": item['name'], "price": price, "discount": discount,
            "status": status, "url": url, "success": True
        }
        
    except Exception as e:
        return {"name": item['name'], "success": False, "error": str(e)}

async def main():
    print("=== ЗАПУСК УНІВЕРСАЛЬНОГО ТРЕКЕРА ЦІН ===")
    
    async with async_playwright() as p:
        # Емуляція реального комп'ютера, щоб сайти не блокували робота
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        
        results = []
        for item in TRACKING_LIST:
            res = await check_product(page, item)
            results.append(res)
            await asyncio.sleep(4) # Пауза 4 секунди, щоб уникнути блокувань
            
        await browser.close()
    
    # === ГЕНЕРАЦІЯ ФІНАЛЬНОГО ЗВІТУ ===
    print("\n" + "="*60)
    print("📋 ЗВІТ ПРО МОНІТОРИНГ ЦІН (УСІ САЙТИ)")
    print("="*60)
    
    for r in results:
        if r["success"]:
            print(f"📦 Товар: {r['name']}")
            print(f"💰 Ціна: {r['price']}")
            print(f"⚡ Статус: {r['status']}")
            print(f"🎈 Акція: {r['discount']}")
            print(f"🔗 Посилання: {r['url']}")
        else:
            print(f"❌ Помилка перевірки для '{r['name']}': {r['error']}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
