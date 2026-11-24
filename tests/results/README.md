# Kết quả benchmark

Benchmark luôn ghi kết quả trực tiếp vào thư mục này. Mỗi lần chạy ghi đè bốn bảng kết quả hiện tại; `config.csv` lưu thời điểm và cấu hình của lần chạy gần nhất.

| Bảng | Khi nào cần đọc |
| --- | --- |
| `comparison.csv` | So sánh chất lượng nghiệm giữa các thuật toán |
| `timing.csv` | Xem thời gian, trạng thái và lỗi từng lượt |
| `runs.csv` | Tra cứu đầy đủ dữ liệu từng lượt chạy |
| `config.csv` | Kiểm tra suite, ngân sách và seed |

Các bảng được cập nhật dần. Kiểm tra `not_run` trong bảng so sánh và cấu hình trước khi kết luận; kết quả cũ không được giữ tự động.

Xem [hướng dẫn benchmark](../README.md) cho lệnh chạy và ý nghĩa chi tiết các cột.
