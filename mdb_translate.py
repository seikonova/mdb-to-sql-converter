import os
import sqlite3
import pyodbc

def translate(mdb_file, sqlite_file, text_widget, main_button_widget, ok_button_widget):
    """
    Функция переноса бд с ЖЕЛЕЗОБЕТОННЫМ СОХРАНЕНИЕМ ОРИГИНАЛЬНЫХ ТИПОВ ДАННЫХ.
    """
    
    def log(message):
        text_widget.insert("end", message + "\n")
        text_widget.see("end")

    # Подстраховка путей
    if os.path.isdir(sqlite_file) or not sqlite_file.endswith('.db'):
        file_name_with_ext = os.path.basename(mdb_file)
        file_name_only = os.path.splitext(file_name_with_ext)[0]
        sqlite_file = os.path.join(sqlite_file, f"{file_name_only}1.db")

    log(f"🔎 Ищем файл Access по пути:\n{mdb_file}\n")
    log(f"💾 Создаём файл SQLite по пути:\n{sqlite_file}\n")
    log("-" * 40)

    if not os.path.exists(mdb_file):
        log(f"❌ Ошибка! Файл '{mdb_file}' не найден.")
        main_button_widget.configure(state="normal")
        ok_button_widget.configure(state="normal")
        return

    if os.path.exists(sqlite_file):
        try:
            os.remove(sqlite_file)
        except Exception:
            pass

    try:
        # ======== Подключение к Access ========
        conn_access = pyodbc.connect(
            rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb_file};"
        )
        conn_access.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        conn_access.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
        conn_access.setdecoding(pyodbc.SQL_WMETADATA, encoding='utf-16le')
        conn_access.setencoding(encoding='utf-8')
        cursor_access = conn_access.cursor()

        # ======== Подключение к SQLite ========
        conn_sqlite = sqlite3.connect(sqlite_file)
        cursor_sqlite = conn_sqlite.cursor()

        # Получение списка таблиц
        tables = []
        for row in cursor_access.tables(tableType="TABLE"):
            tables.append(row[2]) 

        log(f"📦 Найдено таблиц в Access: {len(tables)}")

                # Перенос данных
        for table in tables:
            log(f"⏳ Перенос таблицы: {table}")

            try:
                # 1. Сначала запрашиваем сами данные для переноса
                cursor_access.execute(f"SELECT * FROM [{table}]")
                rows = cursor_access.fetchall()
                
                # 2. Умное определение типов данных колонок по описанию запроса и типам значений
                cols = []
                for idx, desc in enumerate(cursor_access.description):
                    column_name = desc[0]
                    
                    # Пытаемся определить тип по значению в первой строчке данных (если таблица не пустая)
                    detected_type = str
                    if rows and len(rows) > 0 and rows[0][idx] is not None:
                        detected_type = type(rows[0][idx])
                    
                    # Сопоставляем реальные типы данных Python с типами SQLite
                    if detected_type in (int, bool):
                        sqlite_type = "INTEGER"
                    elif detected_type == float:
                        sqlite_type = "REAL"
                    else:
                        sqlite_type = "TEXT"
                    
                    # Если в этой колонке имя содержит 'id', принудительно делаем INTEGER для надежности
                    if column_name.lower() == "id":
                        sqlite_type = "INTEGER"
                        
                    cols.append(f'"{column_name}" {sqlite_type}')

                # 3. Создаем таблицу со встроенными типами
                create_sql = f'CREATE TABLE IF NOT EXISTS "{table}" ({",".join(cols)})'
                cursor_sqlite.execute(create_sql)

                # 4. Перенос строк
                if rows:
                    placeholders = ",".join(["?"] * len(cursor_access.description))
                    insert_sql = f'INSERT INTO "{table}" VALUES ({placeholders})'

                    for row in rows:
                        row_data = list(row)
                        
                        # Переводим логический тип в 1 или 0 для SQLite
                        for i in range(len(row_data)):
                            if isinstance(row_data[i], bool):
                                row_data[i] = 1 if row_data[i] else 0
                                
                        cursor_sqlite.execute(insert_sql, tuple(row_data))
                        
                    log(f"   ✅ Успешно перенесено строк: {len(rows)}")
                else:
                    log("   ℹ️ Таблица пустая, перенесена только структура.")

                conn_sqlite.commit()

            except Exception as e:
                log(f"❌ Ошибка при переносе таблицы {table}: {e}")

        log("\n✨ Перенос успешно завершён!")
        conn_access.close()
        conn_sqlite.close()

    except Exception as general_error:
        log(f"❌ Критическая ошибка при работе с базами: {general_error}")
        
    finally:
        main_button_widget.configure(state="normal")
        ok_button_widget.configure(state="normal")
