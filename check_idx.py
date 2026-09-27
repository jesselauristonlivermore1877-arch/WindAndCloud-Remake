import os

def hex_dump(filepath, num_bytes=256):
    if not os.path.exists(filepath):
        print(f"找不到檔案: {filepath}")
        return

    print(f"=== 解析檔案: {filepath} ===")
    with open(filepath, 'rb') as f:
        data = f.read(num_bytes)
        
        # 以 16-byte 為一行印出 Hex 碼，方便肉眼尋找規律
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_str = " ".join([f"{b:02X}" for b in chunk])
            print(f"Offset {i:04X}: {hex_str}")
    print("=" * 40 + "\n")

if __name__ == "__main__":
    # 根據你截圖的 D 槽路徑，直接寫死絕對路徑
    path_wcattack = r"D:\风云天下会2023.11.18\WinC\WCAttack.IDX"
    path_warsfx = r"D:\风云天下会2023.11.18\WinC\WarSfx.IDX"
    
    hex_dump(path_wcattack, 256)
    hex_dump(path_warsfx, 256)