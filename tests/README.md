# Bộ dữ liệu và kiểm thử

## Cấu trúc thư mục

```text
tests/
├── data/
│   ├── small/          # 15 test mẫu, ca biên và dữ liệu nhỏ
│   └── stress/         # 12 test lớn và manifest dữ liệu
├── scripts/            # Sinh dữ liệu, kiểm tra nghiệm và benchmark
├── unit/               # Kiểm thử tự động
└── results/
    ├── milp.csv        # MILP, greedy và ALNS trên bộ nhỏ
    ├── heuristics.csv  # Sáu heuristic trên cả hai bộ
    ├── stress.csv      # Greedy và ALNS trên stress test
    └── archive/        # Kết quả các lần thử giới hạn thời gian trước
```

- [data/small/](./data/small/): mẫu đề, ca biên và các nhóm N=8/20/60.
- [data/stress/](./data/stress/README.md): dữ liệu đạt N=1000, Q=1000, M=500, K=100000; thông số và hash nằm trong [manifest.json](./data/stress/manifest.json).
- [scripts/paths.py](./scripts/paths.py): khai báo tập trung đường dẫn dữ liệu và kết quả.
- [unit/test_cpp.py](./unit/test_cpp.py): kiểm tra ca biên, dữ liệu lỗi và tính tái lập seed cho các thuật toán C++.

## Lệnh chạy

Chạy từ thư mục gốc với OR-Tools và g++ hỗ trợ C++17. Nếu không dùng môi trường ảo của dự án, thay `.venv/bin/python` bằng interpreter đã cài [requirements.txt](../solutions/milp/requirements.txt).

```bash
# Sinh dữ liệu (giữ nguyên mẫu đề)
.venv/bin/python tests/scripts/generate.py
# Chỉ sinh bộ lớn hoặc bộ nhỏ
.venv/bin/python tests/scripts/generate.py --suite stress
.venv/bin/python tests/scripts/generate.py --suite small

# Chạy kiểm thử tự động
.venv/bin/python -m unittest discover -s tests/unit

# MILP, greedy, ALNS trên bộ nhỏ
.venv/bin/python tests/scripts/benchmark.py --milp-seconds 10 --iterations 2000

# Greedy, ALNS trên bộ lớn
.venv/bin/python tests/scripts/benchmark_stress.py --iterations 200 --seeds 1 2 3

# Sáu heuristic trên cả bộ nhỏ và bộ lớn
.venv/bin/python tests/scripts/compare_heuristics.py
```

Bộ sinh ghi đè dữ liệu do nó quản lý, giữ nguyên [sample.txt](./data/small/sample.txt). Benchmark kiểm tra mọi nghiệm trước khi ghi kết quả; chỉ xuất CSV, không sinh báo cáo Markdown, lịch riêng, log hoặc metadata. Chạy lại ghi đè CSV tương ứng; [archive/](./results/archive/) không bị ghi đè bởi các lệnh này.

## File kết quả

| File | Nội dung |
| --- | --- |
| [milp.csv](./results/milp.csv) | MILP, greedy và ALNS trên bộ nhỏ |
| [heuristics.csv](./results/heuristics.csv) | Sáu heuristic trên 27 test |
| [stress.csv](./results/stress.csv) | Greedy và ALNS trên 12 stress test |
| [milp_2s.csv](./results/archive/milp_2s.csv) | Kết quả đã chạy với giới hạn MILP 2 giây mỗi pha |
| [milp_30s.csv](./results/archive/milp_30s.csv) | Kết quả đã chạy riêng ba test N=60 với giới hạn MILP 30 giây mỗi pha |

Mỗi dòng là một lần chạy: tên instance, kích thước, thuật toán, seed, ngân sách, trạng thái, số công việc (`count`), thời điểm kết thúc (`makespan`), chi phí (`cost`) và thời gian wall-clock (`seconds`). CSV dùng dấu phẩy và có hàng tiêu đề. Một số CSV cũ trong archive có ít cột cấu hình hơn các lần chạy mới.

`not_proven` nghĩa là MILP chưa chứng minh tối ưu; `wall_timeout`/`timeout` nghĩa là tiến trình vượt thời gian bên ngoài. Các ô mục tiêu trống khi không có nghiệm được xuất và kiểm tra. Thời gian gồm khởi động, đọc dữ liệu và giải; không gồm biên dịch/kiểm tra nghiệm. Giới hạn SCIP áp dụng từng pha, không giới hạn thời gian dựng mô hình.

## Kiểm tra nghiệm riêng

Bộ kiểm tra xác nhận định dạng, không lặp công việc, đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm, không chồng lấn và số công việc tối đa. Benchmark MILP còn đối chiếu mẫu/ca biên với giá trị đã biết; script so sánh heuristic sử dụng chứng minh MILP trong [milp.csv](./results/milp.csv) làm tham chiếu.

Hai ca kiểm tra riêng mục tiêu trong bộ nhỏ dùng $Q = 0$ để cô lập hành vi, là mở rộng được cả hai chương trình hỗ trợ ngoài cận $1 \le Q$ trong đề.

Nếu muốn tự lưu và kiểm tra một lịch, biên dịch ALNS và tạo thư mục `.build` trước, rồi chạy:

```bash
solutions/alns/alns 2000 1 < tests/data/small/sample.txt > .build/sample.out
.venv/bin/python tests/scripts/check.py tests/data/small/sample.txt .build/sample.out
```
