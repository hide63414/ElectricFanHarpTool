"""
2024/10/6 羽根描画データからWAVファイル生成プログラム by H.Tanaka

使用方法:
このプログラムは、羽根の描画条件をCSVファイルから読み込み、指定された条件に基づいてWAVファイルを生成します。

CSVファイルのフォーマット:
- 内円、外円の直径を指定します。
- 扇形の条件は以下の通りです:
  - 内側半径
  - 外側半径
  - 1周分割数（小数指定可能）
  - 穴比率（小数指定）

注意点:
- 1周分割数は小数で指定できますが、整数に満たない部分は描画されません。
- CSVファイルの先頭に#がある行はコメントとして扱われ、無視されます。
- 行内に//以降の部分もコメントとして扱われ、無視されます。

例:
# これはコメント行です
inner_circle_diameter,10
outer_circle_diameter,20
sector,5,10,4.5,0.2  // この行は扇形の条件を指定
"""

import wave
import struct
import csv
import tkinter as tk
from tkinter import filedialog
import os

# Fixed parameters
SAMPLING_RATE = 44000  # 44kHz sampling rate
RPM = 600  # Rotation speed in revolutions per minute
SECONDS_PER_SECTOR = 0.5  # Evaluate each sector for 0.5 seconds (can be changed)
AMPLITUDE = 32767  # Max amplitude for 16-bit PCM audio

# 環状扇形が指定した半径で存在するかどうかを評価する関数
def evaluate_angle_presence(sectors_conditions, radius, samples_per_sector):
    evaluation_results = []

    # degrees_per_sampleをサンプリングレートを使って計算
    degrees_per_sample = 360 * (RPM / 60) / SAMPLING_RATE

    for sample in range(samples_per_sector):  # samples_per_sectorを使用
        evaluation_value = -0.5  # Initial value if the sector is absent
        current_angle = (sample * degrees_per_sample) % 360  # Current angle for this sample

        for condition in sectors_conditions:
            if condition[0] == "sector":
                inner_r, outer_r, num_sectors, sector_ratio = condition[1:]
                if inner_r <= radius <= outer_r:  # Check if the radius is within the sector range
                    total_angle = 360 / num_sectors
                    sector_angle = total_angle * sector_ratio

                    for i in range(int(num_sectors)):
                        start_angle = i * total_angle
                        end_angle = start_angle + sector_angle

                        if start_angle <= current_angle < end_angle:
                            evaluation_value = 0.5  # Sector is present at this angle
                            break
            if evaluation_value == 0.5:
                break

        evaluation_results.append(evaluation_value)

    return evaluation_results


# WAVファイルに評価結果を書き込む関数
def save_evaluation_to_wav(filename, all_sectors_results):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(SAMPLING_RATE)  # 44kHz

        for sector_results in all_sectors_results:
            for value in sector_results:
                # Convert the evaluation value (-0.5 or 0.5) to 16-bit PCM
                sample_value = int(value * AMPLITUDE)
                wav_file.writeframes(struct.pack('<h', sample_value))

    print(f"WAV file has been created: {filename}")

# CSVファイルから条件を読み込む関数
def read_conditions_from_csv(filename):
    conditions = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if not row or row[0].startswith('#'):
                continue

            full_line = ','.join(row)
            if '//' in full_line:
                clean_line = full_line.split('//')[0].strip()
            else:
                clean_line = full_line.strip()

            clean_row = clean_line.split(',')

            if len(clean_row) < 2:
                continue

            if clean_row[0].strip() == "sector":
                try:
                    inner_r = float(clean_row[1].strip())
                    outer_r = float(clean_row[2].strip())
                    num_sectors = float(clean_row[3].strip())
                    sector_ratio = float(clean_row[4].strip())
                    conditions.append(("sector", inner_r, outer_r, num_sectors, sector_ratio))
                except (ValueError, IndexError) as e:
                    print(f"Error reading row: {clean_row}. Error: {e}")

    return conditions

# CSVファイルを選択する関数
def select_csv_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
    return file_path

# メインプログラム
if __name__ == "__main__":
    # CSVファイルを選択
    csv_filename = select_csv_file()
    if not csv_filename:
        print("No CSV file selected. Exiting program.")
        exit()

    # CSVファイルから条件を読み込む
    sectors_conditions = read_conditions_from_csv(csv_filename)

    # すべてのセクターの結果を保持するリスト
    all_sectors_results = []

    # 各セクターの中間半径を使って評価し、結果を保存
    for condition in sectors_conditions:
        if condition[0] == "sector":
            inner_r = condition[1]
            outer_r = condition[2]
            evaluation_radius = (inner_r + outer_r) / 2  # 内径と外径の中間を評価半径とする

            # 1秒間のサンプル数を計算（SECONDS_PER_SECTORに基づく）
            samples_per_sector = int(SAMPLING_RATE * SECONDS_PER_SECTOR)

            # 評価を実行
            sector_results = evaluate_angle_presence([condition], evaluation_radius, samples_per_sector)
            all_sectors_results.append(sector_results)

    # 保存するWAVファイルの名前を条件CSVファイル名に基づいて生成
    output_wav_filename = os.path.splitext(csv_filename)[0] + ".wav"
    
    # WAVファイルに保存
    save_evaluation_to_wav(output_wav_filename, all_sectors_results)