import csv
import os

# Получаем переменные окружения
input_file = os.getenv("INPUT_FILE")
rows_per_file = int(os.getenv("ROWS_PER_FILE", 100))  # По умолчанию 100 строк на файл

if not input_file:
    raise ValueError("Переменная окружения INPUT_FILE не задана!")

if not os.path.exists(input_file):
    raise FileNotFoundError(f"Файл {input_file} не найден!")

counter = 0
file_count = 1

# Извлекаем базовое имя файла
output_file_base_name = os.path.basename(input_file)
output_file_name = output_file_base_name.replace(".csv", "")

# Получаем путь к выходной папке
output_path = os.getenv("OUTPUT_PATH", os.path.dirname(input_file) + "/")

# Читаем и разбиваем файл
with open(input_file, "r") as file:
    reader = csv.reader(file)
    for row in reader:
        if counter < rows_per_file:
            output_file_path = f"{output_path}{output_file_name}_sliced_{file_count}.csv"
            with open(output_file_path, "a", newline="") as outfile:
                writer = csv.writer(outfile)
                writer.writerow(row)
                counter += 1
        else:
            file_count += 1
            counter = 1
            output_file_path = f"{output_path}{output_file_name}_sliced_{file_count}.csv"
            with open(output_file_path, "a", newline="") as outfile:
                writer = csv.writer(outfile)
                writer.writerow(row)

print("Файлы успешно созданы!")
