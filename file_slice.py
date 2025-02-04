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
        rows_per_file = int(request.form["rows_per_file"])

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Разбиваем CSV
            split_csv(file_path, rows_per_file)

            # Архивируем результат
            zip_path = "output/split_files.zip"
            shutil.make_archive(zip_path.replace(".zip", ""), "zip", OUTPUT_FOLDER)

            return send_file(zip_path, as_attachment=True)

    return render_template("index.html")

def split_csv(input_file, rows_per_file):
    counter = 0
    file_count = 1

    output_file_base_name = os.path.basename(input_file)
    output_file_name = output_file_base_name.replace(".csv", "")

    with open(input_file, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            if counter < rows_per_file:
                output_file_path = f"{OUTPUT_FOLDER}/{output_file_name}_sliced_{file_count}.csv"
                with open(output_file_path, "a", newline="") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(row)
                    counter += 1
            else:
                file_count += 1
                counter = 1
                output_file_path = f"{OUTPUT_FOLDER}/{output_file_name}_sliced_{file_count}.csv"
                with open(output_file_path, "a", newline="") as outfile:
                    writer = csv.writer(outfile)
                    writer.writerow(row)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
