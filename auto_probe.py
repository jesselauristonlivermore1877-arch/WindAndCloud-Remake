import os
import struct

def probe_grp_headers(idx_path, grp_path, num_frames=15):
    if not os.path.exists(idx_path) or not os.path.exists(grp_path):
        print(f"找不到檔案: \n{idx_path}\n{grp_path}")
        return

    print(f"=== 智冠 2D 引擎 Frame Header 自動解析探針 ===")
    with open(idx_path, 'rb') as f_idx, open(grp_path, 'rb') as f_grp:
        # 略過前 12 bytes 的 IDX 檔頭
        f_idx.seek(12)
        
        for i in range(num_frames):
            ptr_bytes = f_idx.read(4)
            if not ptr_bytes or len(ptr_bytes) < 4: 
                break
            ptr = struct.unpack('<I', ptr_bytes)[0]
            
            f_grp.seek(ptr)
            header_bytes = f_grp.read(16) 
            
            if len(header_bytes) < 16:
                break
                
            # 解碼格式: 寬(無號2), 高(無號2), X偏移(有號2), Y偏移(有號2)
            w, h, ox, oy = struct.unpack('<HHhh', header_bytes[:8])
            
            # 讀取後 8 個 bytes 查看有無隱藏參數
            extra_1, extra_2, extra_3, extra_4 = struct.unpack('<hhhh', header_bytes[8:16])

            hex_str = " ".join([f"{b:02X}" for b in header_bytes])
            print(f"Frame {i+1:03d} (GRP Offset: 0x{ptr:08X})")
            print(f"  [原始 Hex] {hex_str}")
            print(f"  [解析結果] 寬度={w:<3} 高度={h:<3} | X_Offset={ox:<4} Y_Offset={oy:<4}")
            print(f"  [剩餘參數] {extra_1}, {extra_2}, {extra_3}, {extra_4}")
            print("-" * 65)

if __name__ == "__main__":
    idx_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.IDX"
    grp_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.GRP"
    
    probe_grp_headers(idx_attack, grp_attack, 15)