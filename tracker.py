import asyncio
from playwright.async_api import async_playwright

# Сюди ви потім додасте реальні посилання на потрібні товари
TRACKING_LIST = [
    {"name": "Товар 1 (Приклад)", "url": "https://example.com"},
    {"name": "Товар 2 (Приклад)", "url": "https://example.org"}
]

async def check_product(page, item):
    print(f"Перевіряємо: {item['name']}...")
    try:
        # Перехід на сторінку товару
        await page.goto(item['url'], timeout=30000, wait_until="domcontentloaded")
        
        # --- ТУТ БУДЕ ВАША ЛОГІКА ПОШУКУ СЕЛЕКТОРІВ ---
        # Наприклад, пошук ціни, наявності та плашок "Акція" через page.locator()
        # Поки що ставимо демонстраційні дані для перевірки працездатності:
        
        price = "1250 грн"         # Тут буде реальний парсинг ціни
        old_price = "1500 грн"     # Для відстеження акцій
        in_stock = True            # Перевірка наявності
        
        discount = "Так (Акція!)" if old_price else "Ні"
        status = "В наявності" if in_stock else "Немає в наявності"
        
        return {
            "name": item['name'],
            "price": price,
            "discount": discount,
            "status": status,
            "url": item['url'],
            "success": True
        }
    except Exception as e:
        return {"name": item['name'], "success": False, "error": str(e)}

async def main():
    print("=== ЗАПУСК РОБОТА ТРЕКЕРА ЦІН ===")
    
    async with async_playwright() as p:
        # Headless=True обов'язковий, адже у GitHub немає екрана
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        results = []
        for item in TRACKING_LIST:
            res = await check_product(page, item)
            results.append(res)
            await asyncio.sleep(2) # Невелика пауза між запитами
            
        await browser.close()
    
    # === ФОРМУВАННЯ ФІНАЛЬНОГО ЗВІТУ ===
    print("\n" + "="*40)
    print("📋 ФІНАЛЬНИЙ ЗВІТ ПРО ЦІНИ ТА НАЯВНІСТЬ")
    print("="*40)
    
    for r in results:
        if r["success"]:
            print(f"📦 Товар: {r['name']}")
            print(f"💰 Поточна ціна: {r['price']}")
            print(f"🔥 Акція / Знижка: {r['discount']}")
            print(f"🔄 Статус: {r['status']}")
            print(f"🔗 Посилання: {r['url']}")
        else:
            print(f"❌ Не вдалося перевірити {r['name']}. Помилка: {r['error']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
