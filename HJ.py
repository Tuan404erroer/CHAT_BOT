from sentence_transformers import SentenceTransformer, util
import os

# 1. Tải model
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Đọc file dữ liệu txt
file_path = 'data.txt'

if not os.path.exists(file_path):
    print(f"Lỗi: Không tìm thấy file {file_path}")
else:
    with open(file_path, 'r', encoding='utf-8') as f:
        danh_sach_kien_thuc = [line.strip() for line in f if line.strip()]

    # 3. Biến toàn bộ kho kiến thức thành vector
    print(f"Đang xử lý {len(danh_sach_kien_thuc)} dòng dữ liệu...")
    vector_kho_kien_thuc = model.encode(danh_sach_kien_thuc)

    # 4. Nhập câu hỏi từ bàn phím
    while True:
        cau_hoi = input("\nNhập câu hỏi của bạn (hoặc gõ 'exit' để thoát): ")
        if cau_hoi.lower() == 'exit':
            break

        vector_cau_hoi = model.encode(cau_hoi)

        # 5. Thay đổi top_k thành 3 hoặc 4
        SO_LUONG_KET_QUA = 3 
        ket_qua = util.semantic_search(vector_cau_hoi, vector_kho_kien_thuc, top_k=SO_LUONG_KET_QUA)

        print(f"\n=== TOP {SO_LUONG_KET_QUA} CÂU TRẢ LỜI LIÊN QUAN NHẤT ===")
        
        # 6. Duyệt qua danh sách các kết quả trả về
        # ket_qua[0] chứa danh sách các "hit", mỗi hit là một dictionary
        for i, hit in enumerate(ket_qua[0]):
            id_cau_tra_loi = hit['corpus_id']
            diem_tin_cay = hit['score']
            noi_dung = danh_sach_kien_thuc[id_cau_tra_loi]
            
            print(f"{i+1}. [Độ chính xác: {diem_tin_cay:.4f}]")
            print(f"{noi_dung}")
            print("-" * 20) # Dấu gạch ngang để dễ nhìn, tương đương dấu enter cách đoạn