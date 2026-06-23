import customtkinter as ctk
import urllib.parse
import threading
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

# Настройки внешнего вида
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def find_product_position(keyword, target_article):
    output_box.configure(state="normal")
    output_box.delete("0.0", "end")
    output_box.insert("end", "👀 Запускаем визуальный сканер страницы...\n\n")
    output_box.configure(state="disabled")

    try:
        # Переводим в строку, чтобы было проще искать совпадения в тексте
        target_article = str(int(target_article)) 
    except ValueError:
        update_output("❌ Ошибка: Артикул должен состоять только из цифр!\n")
        button.configure(state="normal", text="Погнали 🚀")
        return

    encoded_query = urllib.parse.quote(keyword)
    human_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"

    try:
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            try:
                page.goto(human_url, timeout=30000)
                update_output("⏳ Ждем прогрузки (10 сек). Если будет капча - ткни в нее!\n")
                page.wait_for_timeout(10000) 
                
                # ПРОБЛЕМА 1: Проверяем, не кинул ли нас ВБ сразу в карточку товара
                if "/detail.aspx" in page.url:
                    if target_article in page.url:
                        update_output("⚡ ВБ автоматически перекинул нас в карточку товара!\n")
                        update_output(f"✅ Товар {target_article} - АБСОЛЮТНЫЙ ЛИДЕР (Позиция 1)!\n")
                    else:
                        update_output("❌ ВБ перекинул на другой товар. Нашего тут нет.\n")
                    
                    browser.close()
                    button.configure(state="normal", text="Погнали 🚀")
                    return

                # ПРОБЛЕМА 2: Ищем в обычном каталоге
                update_output("📜 Листаем вниз, чтобы загрузить все карточки...\n")
                for _ in range(5):
                    page.mouse.wheel(0, 1500)
                    page.wait_for_timeout(1000)
                
                # Внедряем JavaScript, который соберет артикулы прямо с экрана
                articles_on_page = page.evaluate("""() => {
                    let items = [];
                    // ВБ хранит артикул в параметре data-nm-id
                    document.querySelectorAll('[data-nm-id]').forEach(el => items.push(el.getAttribute('data-nm-id')));
                    
                    return [...new Set(items)]; // Возвращаем список без дубликатов
                }""")
                
            except Exception as e:
                update_output(f"⚠️ Ошибка на странице: {e}\n")
                articles_on_page = []

            browser.close()

            # Подводим итоги
            if not articles_on_page:
                update_output("❌ Не удалось считать карточки с экрана. Возможно, страница пуста.\n")
            else:
                try:
                    # Ищем наш артикул в списке собранных
                    index = articles_on_page.index(target_article)
                    absolute_position = index + 1
                    
                    update_output(f"✅ Товар {target_article} найден на первой странице!\n")
                    update_output(f"📍 Позиция на полке: {absolute_position} (из {len(articles_on_page)} загруженных)\n")
                except ValueError:
                    update_output(f"❌ Товар не найден среди первых {len(articles_on_page)} позиций выдачи.\n")
                    
    except Exception as e:
        update_output(f"❌ Системная ошибка: {e}\n")

    button.configure(state="normal", text="Погнали 🚀")

def update_output(text):
    output_box.configure(state="normal")
    output_box.insert("end", text)
    output_box.see("end")
    output_box.configure(state="disabled")

def start_search_thread():
    query = entry_query.get()
    article = entry_article.get()
    
    if not query or not article:
        update_output("⚠️ Заполни оба поля!\n")
        return

    button.configure(state="disabled", text="Ищем...")
    
    thread = threading.Thread(target=find_product_position, args=(query, article))
    thread.start()

# --- ИНТЕРФЕЙС ПРИЛОЖЕНИЯ ---
app = ctk.CTk()
app.geometry("450x550")
app.title("WB Scanner")

label_title = ctk.CTkLabel(app, text="Поиск товара WB", font=("Arial", 20, "bold"))
label_title.pack(pady=(20, 10))

entry_query = ctk.CTkEntry(app, placeholder_text="Введи запрос", width=350, height=40)
entry_query.pack(pady=10)

entry_article = ctk.CTkEntry(app, placeholder_text="Введи артикул (только цифры)", width=350, height=40)
entry_article.pack(pady=10)

button = ctk.CTkButton(app, text="Погнали 🚀", command=start_search_thread, width=350, height=45, font=("Arial", 16, "bold"))
button.pack(pady=20)

output_box = ctk.CTkTextbox(app, width=350, height=200, state="disabled", font=("Arial", 14))
output_box.pack(pady=10)

app.mainloop()