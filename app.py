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
        if not file:
            return "Ошибка: Файл не загружен", 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Получаем список строк для каждой части (через запятую)
        rows_per_file = request.form["rows_per_file"]
        rows_list = list(map(int, rows_per_file.split(",")))  # Преобразуем в список чисел

        # Разбиваем CSV
        split_csv(file_path, rows_list)

        # Архивируем результат
        zip_path = "output/split_files.zip"
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", OUTPUT_FOLDER)

        return send_file(zip_path, as_attachment=True)

    return render_template("index.html")

def split_csv(input_file, rows_list):
    file_count = 1
    output_file_base_name = os.path.basename(input_file).replace(".csv", "")

    with open(input_file, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)  # Загружаем весь CSV в память

    start_index = 0
    for rows_per_file in rows_list:
        if start_index >= len(rows):  # Если файл уже закончился, выходим
            break

        output_file_path = f"{OUTPUT_FOLDER}/{output_file_base_name}_part_{file_count}.csv"
        with open(output_file_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(rows[start_index:start_index + rows_per_file])  # Записываем нужное количество строк

        start_index += rows_per_file
        file_count += 1

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
