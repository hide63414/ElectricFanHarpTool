"""
2024/10/5 羽根描画プログラム SVG版 by H.Tanaka

使用方法:
このプログラムは、羽根の描画条件をCSVファイルから読み込み、指定された条件に基づいて羽根を描画します。

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

import svgwrite
import math
import csv
import tkinter as tk
from tkinter import filedialog
import os

# Stroke color setting (white or black)
STROKE_COLOR = 'red'  # Change this to 'white' when needed

# 環状扇形の描画関数
def draw_annular_sector(dwg, center, inner_radius, outer_radius, start_angle, end_angle, stroke_color):
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)

    outer_start = (center[0] + outer_radius * math.cos(start_rad),
                   center[1] + outer_radius * math.sin(start_rad))
    outer_end = (center[0] + outer_radius * math.cos(end_rad),
                 center[1] + outer_radius * math.sin(end_rad))

    inner_start = (center[0] + inner_radius * math.cos(end_rad),
                   center[1] + inner_radius * math.sin(end_rad))
    inner_end = (center[0] + inner_radius * math.cos(start_rad),
                 center[1] + inner_radius * math.sin(start_rad))

    path_data = [
        f'M {outer_start[0]},{outer_start[1]}',
        f'A {outer_radius},{outer_radius} 0 0,1 {outer_end[0]},{outer_end[1]}',
        f'L {inner_start[0]},{inner_start[1]}',
        f'A {inner_radius},{inner_radius} 0 0,0 {inner_end[0]},{inner_end[1]}',
        'Z'
    ]

    dwg.add(dwg.path(' '.join(path_data), fill='none', stroke=stroke_color))

# 円を描画する関数
def draw_circle(dwg, center, radius, stroke_color):
    dwg.add(dwg.circle(center=center, r=radius, fill='none', stroke=stroke_color))

# ファイル名を表示する関数
def add_filename_text(dwg, filename, position, font_size):
    dwg.add(dwg.text(filename, insert=position, font_size=font_size, fill=STROKE_COLOR))

# 環状扇形を円周上に並べる関数
def arrange_sectors_on_circle(dwg, num_sectors, sector_ratio, center, inner_radius, outer_radius):
    total_angle = 360 / num_sectors
    sector_angle = total_angle * sector_ratio

    for i in range(int(num_sectors)):
        start_angle = i * total_angle
        end_angle = start_angle + sector_angle
        
        if end_angle <= 360:
            draw_annular_sector(dwg, center, inner_radius, outer_radius, start_angle, end_angle, stroke_color=STROKE_COLOR)

# CSVファイルから条件を読み込む関数
def read_conditions_from_csv(filename):
    conditions = []
    inner_radius = outer_radius = 0
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if not row or row[0].startswith('#'):
                continue

            # 行をカンマ区切りで分割されたリストとして取得
            full_line = ','.join(row)

            # 行に'//'が含まれているかを確認
            if '//' in full_line:
                # '//'で分割し、最初の部分のみを使う
                clean_line = full_line.split('//')[0].strip()
                print(f"Processed row (after removing //): {clean_line}")
            else:
                # '//'が無い場合はそのまま使う
                clean_line = full_line.strip()
                print(f"Processed row (no // detected): {clean_line}")

            # カンマで分割
            clean_row = clean_line.split(',')

            # 行が空だったり、要素数が2未満の場合はスキップ
            if len(clean_row) < 2:
                print(f"Invalid row (too few elements): {clean_row}")
                continue

            if clean_row[0].strip() == "inner_circle_diameter":
                try:
                    inner_radius = float(clean_row[1].strip()) / 2  # 直径を半径に変換
                except (ValueError, IndexError) as e:
                    print(f"Inner circle diameter 読み込みエラー: {clean_row}. エラー: {e}")
            elif clean_row[0].strip() == "outer_circle_diameter":
                try:
                    outer_radius = float(clean_row[1].strip()) / 2  # 直径を半径に変換
                except (ValueError, IndexError) as e:
                    print(f"Outer circle diameter 読み込みエラー: {clean_row}. エラー: {e}")
            elif clean_row[0].strip() == "sector":
                try:
                    inner_r = float(clean_row[1].strip())
                    outer_r = float(clean_row[2].strip())
                    num_sectors = float(clean_row[3].strip())
                    sector_ratio = float(clean_row[4].strip())
                    conditions.append(("sector", inner_r, outer_r, num_sectors, sector_ratio))
                except (ValueError, IndexError) as e:
                    print(f"行の読み込みエラー: {clean_row}. エラー: {e}")

    # 読み込んだパラメータを表示
    print("Inner radius:", inner_radius)
    print("Outer radius:", outer_radius)
    print("Sectors conditions:")
    if conditions:
        for condition in conditions:
            print(condition)
    else:
        print("No valid sector conditions found.")

    return inner_radius, outer_radius, conditions

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
    inner_radius, outer_radius, sectors_conditions = read_conditions_from_csv(csv_filename)

    # 描画エリアの最大サイズを決定
    max_radius = max(outer_radius, max([cond[2] for cond in sectors_conditions if cond[0] == "sector"], default=0))

    # SVGファイルを作成（CSVファイル名に基づく）
    svg_filename = os.path.splitext(os.path.basename(csv_filename))[0] + '.svg'  # CSVファイル名から拡張子を除去
    dwg_size = max_radius * 2 + 20  # 周囲の余白を考慮して20mm追加
    dwg = svgwrite.Drawing(svg_filename, profile='tiny', size=(f"{dwg_size}mm", f"{dwg_size}mm"))
    dwg.viewbox(0, 0, dwg_size, dwg_size)

    # 中心位置
    center = (dwg_size / 2, dwg_size / 2)

    # 内円と外円を描画
    draw_circle(dwg, center, inner_radius, stroke_color=STROKE_COLOR)
    draw_circle(dwg, center, outer_radius, stroke_color=STROKE_COLOR)

    # 各条件に基づいて描画
    for condition in sectors_conditions:
        if condition[0] == "sector":
            inner_r, outer_r, num_sectors, sector_ratio = condition[1:]
            if int(num_sectors) > 0:
                arrange_sectors_on_circle(dwg, num_sectors, sector_ratio, center, inner_r, outer_r)

    # ファイル名を表示
    position = (dwg_size / 2 - 20, dwg_size / 2 + 20)  # 表示位置 (x, y)
    font_size = 10  # フォントサイズ
    add_filename_text(dwg, svg_filename, position, font_size)

    # ファイルに保存
    dwg.save()
    print(f"SVG file has been created: {svg_filename}")
