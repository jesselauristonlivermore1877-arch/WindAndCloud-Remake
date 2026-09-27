import os
import struct

def probe_action(idx_path, grp_path, action_id, num_frames=20):
    with open(idx_path, 'rb') as f_idx, open(grp_path, 'rb') as f_grp:
        # 檔頭 12 bytes。每個 Action 佔用 8 bytes (2 個 32-bit 指標)
        f_idx.seek(12 + action_id * 8)
        
        ptr1_bytes = f_idx.read(4)
        ptr2_bytes = f_idx.read(4)
        
        if not ptr1_bytes or not ptr2_bytes:
            return
            
        offset_array_ptr = struct.unpack('<I', ptr1_bytes)[0]
        frame_data_ptr = struct.unpack('<I', ptr2_bytes)[0]
        
        print(f"=== 掃描招式 ID: {action_id} ===")
        print(f"影格陣列指標: 0x{offset_array_ptr:08X} | 圖檔區塊指標: 0x{frame_data_ptr:08X}")
        
        # 讀取每個 Frame 的相對偏移量
        f_grp.seek(offset_array_ptr)
        frame_offsets = []
        for _ in range(num_frames):
            off_bytes = f_grp.read(4)
            if not off_bytes: break
            frame_offsets.append(struct.unpack('<I', off_bytes)[0])
            
        # 進入每張圖檔的 Header 尋找座標
        for i, relative_off in enumerate(frame_offsets):
            actual_pos = frame_data_ptr + relative_off
            f_grp.seek(actual_pos)
            header = f_grp.read(32) 
            
            if len(header) < 32: continue
            
            hex_str = " ".join([f"{b:02X}" for b in header])
            # 解碼為 16 個有號整數 (Signed Short)，用來肉眼捕捉負數座標
            shorts = struct.unpack('<16h', header)
            
            print(f"  Frame {i+1:03d} (位址 0x{actual_pos:08X})")
            print(f"    Hex碼: {hex_str}")
            print(f"    16-bit整數解析: {shorts}")
            
        print("=" * 65 + "\n")

if __name__ == "__main__":
    idx_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.IDX"
    grp_attack = r"D:\风云天下会2023.11.18\WinC\WCAttack.GRP"
    
    # 掃描 118, 119, 120，確保不會因為 0-index 或 1-index 錯過目標
    for aid in [118, 119, 120]:
        probe_action(idx_attack, grp_attack, aid, num_frames=20)