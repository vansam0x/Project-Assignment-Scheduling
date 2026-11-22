# Stress test theo giới hạn đề

Nhóm này nằm riêng trong [instances/](./instances/), không được quét bởi benchmark nhỏ. Giới hạn áp dụng: N,Q≤1000, M≤500, K≤100000. Có 12 instance: 6 cấu hình, mỗi cấu hình 2 seed dữ liệu (`2026`, `2027`).

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
.venv/bin/python tests/generate.py --suite stress
.venv/bin/python tests/stress/benchmark.py --iterations 200 --seeds 1 2 3
```

`tests/generate.py` mặc định sinh cả bộ nhỏ và stress (`--suite all`); dùng `--suite small` để chỉ sinh bộ nhỏ. Sinh lại ghi đè dữ liệu do bộ sinh quản lý, không sửa mẫu đề.

Benchmark stress biên dịch C++, kiểm tra hash và các cận/đặc điểm dữ liệu, chạy greedy cùng ALNS ba seed, rồi kiểm tra độc lập mọi nghiệm. Timeout mặc định 30 giây mỗi lượt, đổi bằng `--timeout`. Đây là kiểm thử hoạt động với ngân sách 200 vòng lặp, khác ngân sách 2000 vòng trong bộ nhỏ. Tăng `--iterations` để đánh giá chất lượng sâu hơn.

Kết quả chỉ ghi vào [benchmark.csv](./results/benchmark.csv), không sinh báo cáo Markdown, lịch riêng, log hoặc metadata. Không ghi đè kết quả của bộ nhỏ.

Kết quả sáu heuristic trên cùng dữ liệu nằm trong [CSV](../heuristic_results/benchmark.csv). Chạy `.venv/bin/python tests/compare_heuristics.py --suite stress` từ thư mục gốc để tái lập phần stress.

MILP theo cặp có thể sinh hàng triệu biến thứ tự trên nhóm này. Benchmark stress hiện chỉ chạy greedy/ALNS và thống kê kích thước MILP; chưa đo kết quả MILP trên các test lớn. Giới hạn SCIP mỗi pha không giới hạn thời gian/RAM dựng mô hình, nên cần ngân sách tài nguyên riêng trước khi chạy toàn bộ MILP trên nhóm max_dense/max_chain.
