import os
import struct

def hex_dump(data, length=16):
    print("Offset(h)  00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  Decoded Text")
    print("-" * 70)
    for i in range(0, len(data), length):
        chunk = data[i:i+length]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        # 將無法顯示的 ASCII 替換為點
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f'{i:08X}   {hex_str:<{length*3}} {ascii_str}')

def main():
    # 這裡可以替換成你想測試的 IDX 檔案，例如 WCAni.IDX 或 WCAttack.IDX
    file_path = "WCAttack.IDX"
    
    if not os.path.exists(file_path):
        print(f"找不到檔案: {file_path}，請確認路徑是否正確。")
        return

    with open(file_path, 'rb') as f:
        # 只讀取前 256 bytes 來分析檔案結構
        data = f.read(256)

    print(f"=== {file_path} 原始 Hex Dump ===")
    hex_dump(data)

    print("\n=== 嘗試解析為 32-bit 無號整數 (通常是資料在 GRP/Data 檔中的 Offset 或 Size) ===")
    for i in range(0, min(64, len(data)), 4):
        val = struct.unpack('<I', data[i:i+4])[0]
        print(f"Bytes [{i:02X}-{i+3:02X}]: {val}")

    print("\n=== 嘗試解析為 16-bit 有號整數 (通常是 Width, Height, X_Offset, Y_Offset) ===")
    # 偏移量可能是負數，所以用有號整數 ('<h') 來解
    for i in range(0, min(64, len(data)), 2):
        val = struct.unpack('<h', data[i:i+2])[0]
        print(f"Bytes [{i:02X}-{i+1:02X}]: {val}")

if __name__ == "__main__":
    main()