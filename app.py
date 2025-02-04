from flask import Flask, render_template, request, send_file
import os
import csv
import shutil
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["file"]
        file_names = request.form["file_names"]  # Получаем имена файлов
        if not file or not file_names.strip():
            return "Ошибка: Файл не загружен или имена не указаны", 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Получаем список строк для каждой части (через запятую)
        rows_per_file = request.form["rows_per_file"]
        rows_list = list(map(int, rows_per_file.split(",")))

        # Получаем список имен файлов
        names_list = file_names.split(",")

        # Проверяем, хватает ли имен для частей
        if len(names_list) < len(rows_list):
            return "Ошибка: Количество имен файлов меньше, чем частей", 400

        # Разбиваем CSV
        split_csv(file_path, rows_list, names_list)

        # Архивируем результат
        zip_path = "output/split_files.zip"
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", OUTPUT_FOLDER)

        return send_file(zip_path, as_attachment=True)

    return render_template("index.html")

def split_csv(input_file, rows_list, names_list):
    file_count = 0

    with open(input_file, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)  # Загружаем весь CSV в память

    start_index = 0
    total_rows = len(rows)

    for i, rows_per_file in enumerate(rows_list):
        if start_index >= total_rows:
            break

        output_file_path = f"{OUTPUT_FOLDER}/{names_list[i].strip()}.csv"
        with open(output_file_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(rows[start_index:start_index + rows_per_file])

        start_index += rows_per_file
        file_count += 1

    # Если остались неиспользованные строки – кидаем в extra.csv
    if start_index < total_rows:
        extra_file_path = f"{OUTPUT_FOLDER}/extra.csv"
        with open(extra_file_path, "w", newline="") as extra_file:
            writer = csv.writer(extra_file)
            writer.writerows(rows[start_index:])  # Записываем все оставшиеся строки

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
