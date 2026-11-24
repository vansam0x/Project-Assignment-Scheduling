# Stress test theo giới hạn đề

Nhóm này nằm riêng trong [thư mục dữ liệu này](./), không được quét bởi benchmark nhỏ. Giới hạn áp dụng: $N,Q \le 1000, M \le 500, K \le 100000$. Có 12 instance: 6 cấu hình, mỗi cấu hình 2 seed dữ liệu (`2026`, `2027`).

| Nhóm | N | Q | M | K | Cấu trúc |
| --- | ---: | ---: | ---: | ---: | --- |
| scale200 | 200 | 200 | 20 | 2000 | DAG ngẫu nhiên |
| scale500 | 500 | 500 | 100 | 10000 | DAG ngẫu nhiên |
| max_dense | 1000 | 1000 | 500 | 100000 | Đồng thời đạt cả bốn cận, nhiều đội hợp lệ |
| max_sparse | 1000 | 1000 | 500 | 1000 | Đạt N/Q/M tối đa, mỗi việc đúng một đội |
| bottleneck | 1000 | 1000 | 10 | 10000 | Mỗi đội làm được mọi việc, khan hiếm tài nguyên |
| max_chain | 1000 | 1000 | 500 | 100000 | Chuỗi 999 cạnh bao phủ mọi việc, thêm một cạnh thuận |

Bộ sinh xáo nhãn công việc và chỉ thêm cạnh thuận theo một hoán vị topo. Mỗi công việc có ít nhất một đội, các cặp phân công không lặp, số cạnh và số cặp phân công đúng chính xác Q/K. Thời lượng, thời điểm sẵn sàng và chi phí được sinh trong 1–1000. Mọi instance này có số công việc tối đa bằng N; các ca thiếu đội/chu trình được kiểm tra trong bộ nhỏ.

[manifest.json](./manifest.json) lưu cấu hình, seed, SHA-256 và số biến thứ tự/ràng buộc không chồng lấn MILP tính trực tiếp từ dữ liệu. Các số này là số lượng cấu trúc, không phải đo RAM hay thời gian giải MILP.

## Sinh lại và kiểm thử

Từ thư mục gốc:

```bash
.venv/bin/python tests/scripts/generate.py --suite stress
.venv/bin/python tests/scripts/benchmark_stress.py --time-limit 30 --memory-mb 2048 --seeds 1 2 3
```

`tests/scripts/generate.py` mặc định sinh cả bộ nhỏ và stress (`--suite all`); dùng `--suite small` để chỉ sinh bộ nhỏ. Sinh lại ghi đè dữ liệu do bộ sinh quản lý, không sửa mẫu đề.

Benchmark kiểm tra hash và các cận dữ liệu, rồi chạy MILP, greedy, LPT, critical path, multistart, SA và ALNS trên cả 12 instance. Không bỏ test theo số biến dự kiến; mọi nghiệm đều được kiểm tra độc lập.

Ngân sách chung cho mỗi thuật toán và mỗi seed trên Linux:

- `--time-limit 30`: tổng 30 giây cho tiến trình, gồm khởi động, đọc dữ liệu, dựng mô hình và giải. MILP dùng thời gian còn lại cho ba pha; các phương pháp tìm kiếm lặp tới hạn, có chừa thời gian xuất nghiệm. Các phương pháp dựng lịch được phép kết thúc sớm.
- `--memory-mb 2048`: tối đa 2048 MiB không gian địa chỉ (`RLIMIT_AS`), áp dụng trước khi khởi động mọi tiến trình con; không phải RSS.
- `--seeds 1 2 3`: ba lượt độc lập cho ALNS, SA và multistart. Các phương pháp tất định chỉ chạy một lần.

Các lượt chạy tuần tự để không cộng dồn bộ nhớ. Ví dụ muốn tăng ngân sách, sửa thành `--time-limit 60 --memory-mb 4096` trong cùng lệnh. Biên dịch và kiểm tra nghiệm không nằm trong ngân sách thuật toán.

`wall_timeout`, `memory_limit`, `process_error` ghi nguyên nhân dừng; ô mục tiêu trống nếu chưa có nghiệm, không thay bằng 0. Bộ chạy khôi phục nghiệm tốt nhất đã xuất hoàn chỉnh khi bị ngắt, rồi kiểm tra nghiệm đó. Cận/gap MILP chỉ thuộc pha đang giải, không phải toàn bộ ba mục tiêu.

Kết quả được ghi sau mỗi lượt trong thư mục đợt chạy riêng: `runs.csv`, `comparison.csv`, `timing.csv` và `config.csv`. Xem [hướng dẫn kết quả](../../README.md#file-kết-quả). CSV cũ được giữ nguyên, không cập nhật hoặc trộn với lần chạy mới.

Kết quả OR-Tools ở đây thuộc mô hình MILP theo cặp dùng SCIP. Thời gian dựng mô hình và giới hạn tài nguyên là một phần của phép đo, không đại diện cho mọi mô hình hay bộ giải khác trong OR-Tools.
