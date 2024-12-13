import os
import sys
import csv
import rasterio
import numpy as np
from PIL import Image
import traceback
import tkinter as tk
from tkinter import messagebox

def process_geotiff(geo_tiff_path):
    """
    Process a GeoTIFF file to generate JPEG, CSV, World file, and SIMA file
    GeoTIFFファイルを処理してJPEG、CSV、ワールドファイル、SIMAファイルを生成する
    """
    try:
        # Initialize processing and check file existence
        # 処理の初期化とファイルの存在確認
        print(f"処理を開始します: {geo_tiff_path}")
        print(f"カレントディレクトリ: {os.getcwd()}")
        
        if not os.path.exists(geo_tiff_path):
            raise FileNotFoundError(f"ファイルが見つかりません: {geo_tiff_path}")

        # Setup output file paths
        # 出力ファイルパスの設定
        base_dir = os.path.dirname(geo_tiff_path)
        file_name = os.path.splitext(os.path.basename(geo_tiff_path))[0]
        output_paths = {
            'csv': os.path.join(base_dir, f"{file_name}.csv"),
            'world': os.path.join(base_dir, f"{file_name}.tfw"),
            'sima': os.path.join(base_dir, f"{file_name}.sim"),
            'jpeg': os.path.join(base_dir, f"{file_name}.jpg")
        }

        with rasterio.open(geo_tiff_path) as src:
            # Get image information
            # 画像情報の取得
            print(f"画像情報:\n  サイズ: {src.width}x{src.height}\n  形式: {src.dtypes}\n  バンド数: {src.count}")
            
            # Read and normalize image data
            # 画像データの読み込みと正規化
            data = src.read()
            normalized = ((data - data.min()) * (255 / (data.max() - data.min()))).astype(np.uint8)
            
            # Convert to PIL Image based on band count
            # バンド数に応じてPIL Imageに変換
            if data.shape[0] == 1:
                img = Image.fromarray(normalized[0])
            else:
                rgb_data = normalized[:3]
                img = Image.fromarray(np.transpose(rgb_data, (1, 2, 0)))
            
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Save JPEG
            # JPEG形式で保存
            img.save(output_paths['jpeg'], 'JPEG', quality=95)

            # Extract georeference information
            # ジオリファレンス情報の抽出
            transform = src.transform
            corners = calculate_corners(src.width, src.height, transform)
            
            # Create output files
            # 出力ファイルの作成
            create_csv_file(output_paths['csv'], corners)
            create_world_file(output_paths['world'], transform, corners[0][1:])
            create_sima_file(output_paths['sima'], file_name, corners)

        print(f"\n処理が完了しました。")
        for key, path in output_paths.items():
            print(f"  {key.upper()}: {path}")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        traceback.print_exc()

def calculate_corners(width, height, transform):
    """
    Calculate corner coordinates of the image
    画像の四隅の座標を計算
    """
    # Extract transform components
    # 変換パラメータの抽出
    origin_x = transform.c
    origin_y = transform.f
    pixel_size_x = transform.a
    pixel_size_y = transform.e
    rotation_x = transform.b
    rotation_y = transform.d

    # Calculate corner coordinates
    # 四隅の座標を計算
    corners = [
        ("Upper Left", origin_x, origin_y),
        ("Upper Right", origin_x + width * pixel_size_x, origin_y + width * rotation_x),
        ("Lower Right", 
         origin_x + width * pixel_size_x + height * rotation_y,
         origin_y + width * rotation_x + height * pixel_size_y),
        ("Lower Left", origin_x + height * rotation_y, origin_y + height * pixel_size_y)
    ]
    return corners

def create_csv_file(csv_path, corners):
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Position', 'X', 'Y'])
        for corner in corners:
            writer.writerow(corner)

def create_world_file(world_path, transform, upper_left):
    with open(world_path, 'w') as f:
        f.write(f"{transform.a}\n")  # pixel size x
        f.write(f"{transform.b}\n")  # rotation x
        f.write(f"{transform.d}\n")  # rotation y
        f.write(f"{transform.e}\n")  # pixel size y
        f.write(f"{upper_left[0]}\n")  # upper left x
        f.write(f"{upper_left[1]}\n")  # upper left y

def create_sima_file(sima_path, file_name, corners):
    with open(sima_path, 'w') as f:
        f.write(f"ImageName={file_name}\n")
        for position, x, y in corners:
            f.write(f"{position}={x},{y}\n")

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            root = tk.Tk()
            root.withdraw()  # メインウィンドウを非表示
            messagebox.showinfo("使用方法", "GeoTIFFファイルをドラッグ＆ドロップしてください。")
            sys.exit(0)
        else:
            print(f"引数: {sys.argv}")
            geo_tiff_path = sys.argv[1]
            process_geotiff(geo_tiff_path)
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("完了", "処理が完了しました。")
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("エラー", f"予期せぬエラーが発生しました: {e}")
        traceback.print_exc()
