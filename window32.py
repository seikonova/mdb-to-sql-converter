import os
import threading
import customtkinter as ctk
from customtkinter import filedialog
from mdb_translate import translate

# Настройки темы
ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("system")

# Функции кнопок
def folder_path():
    """Выбор папки для сохранения с автоматическим взятием имени из первого поля."""
    chosen_folder = filedialog.askdirectory(title='Выберите папку для сохранения')
    if chosen_folder:
        # 1. Считываем путь из первого поля ввода
        current_mdb = entrymdb.get().strip()
        
        if current_mdb:
            # Если файл выбран, достаем его чистое имя (например, "Materials")
            file_name_with_ext = os.path.basename(current_mdb)
            file_name_only = os.path.splitext(file_name_with_ext)[0]
            new_sqlite_name = f"{file_name_only}1.db"
        else:
            # Если первое поле пустое, берем имя по умолчанию
            new_sqlite_name = "Materials1.db"
            
        # 2. Объединяем выбранную папку и собранное имя файла
        full_db_path = os.path.join(chosen_folder, new_sqlite_name)
        
        # 3. Выписываем готовый путь во второе поле
        entrydbpath.delete(0, 'end')
        entrydbpath.insert(0, full_db_path)


def file_path():
    """Выбор исходного файла Access и автоподстановка имени для SQLite."""
    chosen_file = filedialog.askopenfilename(
        title="Выберите базу данных Access",
        filetypes=[
            ("База данных Access", "*.mdb *.accdb"),
            ("Все файлы", "*.*"),
        ]
    )
    if chosen_file:
        # 1. Записываем путь к Access в первое поле
        entrymdb.delete(0, 'end')
        entrymdb.insert(0, chosen_file)
        
        # 2. Получаем папку, где лежит этот файл
        folder_path = os.path.dirname(chosen_file)
        
        # 3. Получаем чистое имя файла без расширения (например, из "Materials.mdb" делаем "Materials")
        file_name_with_ext = os.path.basename(chosen_file)
        file_name_only = os.path.splitext(file_name_with_ext)[0]
        
        # 4. Собираем новое имя: старое имя + "1" + ".db" (получится "Materials1.db")
        new_sqlite_name = f"{file_name_only}1.db"
        
        # 5. Объединяем папку и новое имя файла в один полный путь
        full_db_path = os.path.join(folder_path, new_sqlite_name)
        
        # 6. Выписываем готовый результат во второе поле
        entrydbpath.delete(0, 'end')
        entrydbpath.insert(0, full_db_path)


def open_log_window_and_start():
    """Создает отдельное окно для логов и запускает процесс переноса в потоке."""
    mdb_val = entrymdb.get().strip()
    sqlite_val = entrydbpath.get().strip()

    # 1. Создаем отдельное всплывающее окно логов (CTkToplevel)
    log_window = ctk.CTkToplevel(app)
    log_window.title("Лог переноса данных")
    log_window.geometry("500x380")
    log_window.resizable(False, False)
    
    # Жестко фиксируем окно поверх остальных
    log_window.attributes("-topmost", True)
    log_window.focus_set()

    # 2. Добавляем текстовое поле для логов
    log_textbox = ctk.CTkTextbox(log_window, width=460, height=260, font=ctk.CTkFont(size=12))
    log_textbox.pack(padx=20, pady=(20, 10))
    log_textbox.insert("1.0", "🚀 Инициализация переноса...\n\n")

    # 3. Добавляем кнопку ОК, которая изначально ЗАБЛОКИРОВАНА (state="disabled")
    ok_button = ctk.CTkButton(
        log_window,
        text="ОК",
        font=ctk.CTkFont(size=14, weight="bold"),
        width=120,
        height=35,
        state="disabled", # 👈 Выключена при создании
        command=log_window.destroy 
    )
    ok_button.pack(pady=(0, 20))

    # Блокируем кнопку на главном окне на время работы
    start_button.configure(state="disabled")
    
    # 4. Запускаем перевод в фоновом потоке. Теперь мы передаем и ok_button тоже!
    threading.Thread(
        target=translate, 
        args=(mdb_val, sqlite_val, log_textbox, start_button, ok_button), 
        daemon=True
    ).start()


# Настройка главного окна
app = ctk.CTk()
app.title("Конвертер Access в SQLite")
app.geometry("600x240") 
app.resizable(False, False)

# Заголовок
label_title = ctk.CTkLabel(
    app,
    text="Перенос Базы Данных",
    font=ctk.CTkFont(size=22, weight="bold"),
)
label_title.place(x=50, y=22)

# Поля ввода
entrymdb = ctk.CTkEntry(
    app,
    width=400,
    placeholder_text='Выберите бд',
    placeholder_text_color="gray",
)
entrymdb.place(x=50, y=70)

entrydbpath = ctk.CTkEntry(
    app,
    width=400,
    placeholder_text='Путь сохранения',
    placeholder_text_color="gray",
)
entrydbpath.place(x=50, y=120)

# Кнопки выбора путей
app.select_btn1 = ctk.CTkButton(
    app,
    text='выбрать',
    font=ctk.CTkFont(size=10),
    height=27,
    width=60,
    command=file_path,
)
app.select_btn1.place(x=455, y=70)

app.select_btn2 = ctk.CTkButton(
    app,
    text='выбрать',
    font=ctk.CTkFont(size=10),
    height=27,
    width=60,
    command=folder_path,
)
app.select_btn2.place(x=455, y=120)

# Кнопка запуска переноса
start_button = ctk.CTkButton(
    app,
    text="Запустить перенос",
    font=ctk.CTkFont(size=15, weight="bold"),
    height=40,
    width=200,
    command=open_log_window_and_start, 
)
start_button.place(x=350, y=170)

app.mainloop()
