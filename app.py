from flask import Flask, render_template, request, send_file, jsonify
import os
import csv
import shutil
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

# Создаем папки, если их нет (важно для Render)
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

        file = request.files.get("file")
        file_names = request.form.get("file_names")
        action = request.form.get("action")

        if not file or not file_names.strip():
            return "Ошибка: Файл не загружен или имена не указаны", 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        if action == "split_equally":
            parts_count = len(file_names.split(","))
            rows_list = calculate_equal_parts(file_path, parts_count)
        else:
            rows_per_file = request.form.get("rows_per_file")
            rows_list = list(map(int, rows_per_file.split(",")))

        names_list = [name.strip() for name in file_names.split(",")]

        if len(names_list) < len(rows_list):
            return "Ошибка: Количество имен файлов меньше, чем частей", 400

        action_type = request.form.get("action_type")
        if action_type == "filter_email":
            split_csv_only_email(file_path, rows_list, names_list)
        elif action_type == "split_contacts":
            split_csv_keep_all_columns(file_path, rows_list, names_list)

        # Архивируем результат
        zip_path = f"{OUTPUT_FOLDER}/split_files.zip"
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", OUTPUT_FOLDER)

        response = send_file(zip_path, as_attachment=True)

        # Очищаем файлы после отправки
        clear_folder(UPLOAD_FOLDER)
        clear_folder(OUTPUT_FOLDER)

        return response

    return render_template("index.html")

@app.route("/calculate_equal_parts", methods=["POST"])
def calculate_equal_parts_api():
    """API для вычисления равных частей (используется кнопкой "Разделить поровну")."""
    file = request.files.get("file")
    parts_count = request.form.get("parts_count", type=int)

    if not file or parts_count <= 0:
        return jsonify({"error": "Неверные данные"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(file_path)

    rows_list = calculate_equal_parts(file_path, parts_count)
    return jsonify({"rows_per_file": ",".join(map(str, rows_list))})

def calculate_equal_parts(file_path, parts_count):
    """Вычисляет, сколько строк должно быть в каждой части при равномерном разделении."""
    with open(file_path, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    total_rows = len(rows) - 1  # Убираем заголовок
    base_count = total_rows // parts_count
    remainder = total_rows % parts_count

    rows_list = [base_count] * parts_count
    extra_indices = random.sample(range(parts_count), remainder)

    for index in extra_indices:
        rows_list[index] += 1

    return rows_list

def split_csv_only_email(input_file, rows_list, names_list):
    """Оставляет только 2-й столбец (Email), удаляет заголовок и добавляет 'email' в каждую часть."""
    with open(input_file, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    email_data = [row[1] for row in rows[1:] if len(row) > 1]

    split_and_save(email_data, rows_list, names_list, "email")

def split_csv_keep_all_columns(input_file, rows_list, names_list):
    """Оставляет все столбцы, но удаляет заголовок и добавляет 'email' в каждую часть."""
    with open(input_file, "r", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    data = rows[1:]

    split_and_save(data, rows_list, names_list, "email")

def split_and_save(data, rows_list, names_list, header):
    """Разделяет данные и сохраняет в CSV."""
    file_count = {}
    used_names = set()
    start_index = 0
    total_rows = len(data)

    for i, rows_per_file in enumerate(rows_list):
        if start_index >= total_rows:
            break

        base_name = names_list[i]
        file_name = get_unique_filename(base_name, used_names, file_count)

        output_file_path = f"{OUTPUT_FOLDER}/{file_name}.csv"
        with open(output_file_path, "w", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow([header])
            writer.writerows([[row] if isinstance(row, str) else row for row in data[start_index:start_index + rows_per_file]])

        start_index += rows_per_file

    # Если остались неиспользованные контакты, сохраняем их в extra.csv
    if start_index < total_rows:
        extra_file_path = f"{OUTPUT_FOLDER}/extra.csv"
        with open(extra_file_path, "w", newline="") as extra_file:
            writer = csv.writer(extra_file)
            writer.writerow([header])
            writer.writerows([[row] if isinstance(row, str) else row for row in data[start_index:]])

def get_unique_filename(base_name, used_names, file_count):
    """Генерирует уникальное имя файла, если имена повторяются."""
    if base_name in used_names:
        file_count[base_name] += 1
        return f"{base_name}_{file_count[base_name]}"
    else:
        file_count[base_name] = 1
        used_names.add(base_name)
        return base_name

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
