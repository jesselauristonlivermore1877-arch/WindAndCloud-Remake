import os
import struct

def analyze_grp_headers(idx_path, grp_path, num_frames=5):
    if not os.path.exists(idx_path) or not os.path.exists(grp_path):
        print(f"找不到檔案，請確認路徑: \n{idx_path}\n{grp_path}")
        return

    print(f"=== 分析 {os.path.basename(grp_path)} 的影格標頭 ===")
    with open(idx_path, 'rb') as f_idx, open(grp_path, 'rb') as f_grp:
        # 略過前 12 bytes 的總標頭
        f_idx.seek(12)
        
        for i in range(num_frames):
            # 讀取 4 bytes 的指標並轉換為整數
            ptr_bytes = f_idx.read(4)
            if not ptr_bytes or len(ptr_bytes) < 4: 
                break
            ptr = struct.unpack('<I', ptr_bytes)[0]
            
            # 拿著指標跳到 GRP 檔案對應的真實位置
            f_grp.seek(ptr)
            # 讀取該影格的前 16 bytes (這裡通常包含 寬、高、X偏移、Y偏移)
            header_bytes = f_grp.read(16) 
            
            hex_str = " ".join([f"{b:02X}" for b in header_bytes])
            print(f"Frame {i+1} (位於 GRP 0x{ptr:08X}): {hex_str}")
    print("=" * 40 + "\n")

if __name__ == "__main__":
    # 讀取你 D 槽的 IDX 與對應的 GRP
    idx_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.IDX"
    grp_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.GRP"
    
    idx_sfx = r"D:\风云天下会2023.11.18\WinC\WarSfx.IDX"
    grp_sfx = r"D:\风云天下会2023.11.18\WinC\WarSfx.GRP"
    
    analyze_grp_headers(idx_attack, grp_attack, 5)
    analyze_grp_headers(idx_sfx, grp_sfx, 5)