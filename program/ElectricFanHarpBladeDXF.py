"""
2024/10/5 羽根描画プログラム DXF版 by H.Tanaka

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

import ezdxf
import math
import csv
import tkinter as tk
from tkinter import filedialog
import os

# 環状扇形の描画関数
def draw_annular_sector(msp, center, inner_radius, outer_radius, start_angle, end_angle):
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

    # 環状扇形を三角形のセグメントとして描画
    msp.add_lwpolyline([outer_start, outer_end, inner_start, inner_end], close=True)

# 円を描画する関数
def draw_circle(msp, center, radius):
    num_points = 100  # 円の近似に使用するポイントの数
    points = [(center[0] + radius * math.cos(2 * math.pi / num_points * i),
               center[1] + radius * math.sin(2 * math.pi / num_points * i)) for i in range(num_points)]
    msp.add_lwpolyline(points, close=True)

# 環状扇形を円周上に並べる関数
def arrange_sectors_on_circle(msp, num_sectors, sector_ratio, center, inner_radius, outer_radius):
    total_angle = 360 / num_sectors
    sector_angle = total_angle * sector_ratio

    for i in range(int(num_sectors)):
        start_angle = i * total_angle
        end_angle = start_angle + sector_angle
        
        if end_angle <= 360:
            draw_annular_sector(msp, center, inner_radius, outer_radius, start_angle, end_angle)

# CSVファイルから条件を読み込む関数
def read_conditions_from_csv(filename):
    conditions = []
    inner_radius = outer_radius = 0
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

            if clean_row[0].strip() == "inner_circle_diameter":
                try:
                    inner_radius = float(clean_row[1].strip()) / 2
                except (ValueError, IndexError):
                    continue
            elif clean_row[0].strip() == "outer_circle_diameter":
                try:
                    outer_radius = float(clean_row[1].strip()) / 2
                except (ValueError, IndexError):
                    continue
            elif clean_row[0].strip() == "sector":
                try:
                    inner_r = float(clean_row[1].strip())
                    outer_r = float(clean_row[2].strip())
                    num_sectors = float(clean_row[3].strip())
                    sector_ratio = float(clean_row[4].strip())
                    conditions.append(("sector", inner_r, outer_r, num_sectors, sector_ratio))
                except (ValueError, IndexError):
                    continue

    return inner_radius, outer_radius, conditions

# CSVファイルを選択する関数
def select_csv_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
    return file_path

# メインプログラム
if __name__ == "__main__":
    csv_filename = select_csv_file()
    if not csv_filename:
        print("No CSV file selected. Exiting program.")
        exit()

    inner_radius, outer_radius, sectors_conditions = read_conditions_from_csv(csv_filename)

    # DXFファイルを作成（CSVファイル名に基づく）
    dxf_filename = os.path.splitext(os.path.basename(csv_filename))[0] + '.dxf'
    doc = ezdxf.new()
    msp = doc.modelspace()

    center = (0, 0)

    # 内円と外円を描画
    draw_circle(msp, center, inner_radius)
    draw_circle(msp, center, outer_radius)

    # 各条件に基づいて描画
    for condition in sectors_conditions:
        if condition[0] == "sector":
            inner_r, outer_r, num_sectors, sector_ratio = condition[1:]
            if int(num_sectors) > 0:
                arrange_sectors_on_circle(msp, num_sectors, sector_ratio, center, inner_r, outer_r)

    # DXFファイルに保存
    doc.saveas(dxf_filename)
    print(f"DXF file has been created: {dxf_filename}")
