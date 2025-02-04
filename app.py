from flask import Flask, render_template, request, send_file
import os
import csv
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

# Создаем папки, если их нет
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clear_folder(folder):
    """Удаляет все файлы в указанной папке."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Очищаем старые файлы перед новой загрузкой
        clear_folder(UPLOAD_FOLDER)
        clear_folder(OUTPUT_FOLDER)

        file = request.files["file"]
        file_names = request.form["file_names"]
        
        if not file or not file_names.strip():
            return "Ошибка: Файл не загружен или имена не указаны", 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Получаем список строк для каждой части (через запятую)
        rows_per_file = request.form["rows_per_file"]
        rows_list = list(map(int, rows_per_file.split(",")))

        # Получаем список имен файлов
        names_list = [name.strip() for name in file_names.split(",")]

        # Проверяем, хватает ли имен для частей
        if len(names_list) < len(rows_list):
            return "Ошибка: Количество имен файлов меньше, чем частей", 400

        # Разбиваем CSV
        split_csv(file_path, rows_list, names_list)

        # Архивируем результат
        zip_path = f"{OUTPUT_FOLDER}/split_files.zip"
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", OUTPUT_FOLDER)

        response = send_file(zip_path, as_attachment=True)

        # Очищаем файлы после отправки
        clear_folder(UPLOAD_FOLDER)
        clear_folder(OUTPUT_FOLDER)

        return response

    return render_template("index.html")

def split_csv(input_file, rows_list, names_list):
    file_count = {}
    used_names = set()

    with open(input_file, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)  

    # Удаляем заголовок (первую строку)
    rows = rows[1:]

    # Берем только первый столбец
    processed_rows = [["email"]] + [[row[0]] for row in rows if row]

    start_index = 0
    total_rows = len(processed_rows)

    for i, rows_per_file in enumerate(rows_list):
        if start_index >= total_rows:
            break

        base_name = names_list[i]

        # Если имя уже есть, добавляем номер
        if base_name in used_names:
            file_count[base_name] += 1
            file_name = f"{base_name}_{file_count[base_name]}"
        else:
            file_count[base_name] = 1
            file_name = base_name
            used_names.add(base_name)

        output_file_path = f"{OUTPUT_FOLDER}/{file_name}.csv"
        with open(output_file_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(processed_rows[start_index:start_index + rows_per_file])

        start_index += rows_per_file

    # Если остались неиспользованные строки – кидаем в extra.csv
    if start_index < total_rows:
        extra_file_path = f"{OUTPUT_FOLDER}/extra.csv"
        with open(extra_file_path, "w", newline="") as extra_file:
            writer = csv.writer(extra_file)
            writer.writerows(processed_rows[start_index:])  

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
