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
    ├── heuristics.csv  # MILP, năm heuristic và ALNS riêng
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
.venv/bin/python tests/scripts/benchmark.py --milp-seconds 30 --iterations 2000

# Greedy, ALNS trên bộ lớn
.venv/bin/python tests/scripts/benchmark_stress.py --iterations 200 --seeds 1 2 3

# Ghép MILP đã chạy với năm heuristic và chương trình ALNS riêng
.venv/bin/python tests/scripts/compare_heuristics.py
```

Bộ sinh ghi đè dữ liệu do nó quản lý, giữ nguyên [sample.txt](./data/small/sample.txt). Benchmark kiểm tra mọi nghiệm trước khi ghi kết quả; chỉ xuất CSV, không sinh báo cáo Markdown, lịch riêng, log hoặc metadata. Chạy lại ghi đè CSV tương ứng; [archive/](./results/archive/) không bị ghi đè bởi các lệnh này.

## File kết quả

| File | Nội dung |
| --- | --- |
| [milp.csv](./results/milp.csv) | MILP, greedy và ALNS trên bộ nhỏ |
| [heuristics.csv](./results/heuristics.csv) | MILP, năm heuristic và ALNS riêng trên cùng instance |
| [stress.csv](./results/stress.csv) | Greedy và ALNS trên 12 stress test |
| [milp_30s.csv](./results/archive/milp_30s.csv) | Kết quả đã chạy riêng ba test N=60 với giới hạn MILP 30 giây mỗi pha |

Mỗi dòng là một lần chạy: tên instance, kích thước, thuật toán, seed, ngân sách, trạng thái, số công việc (`count`), thời điểm kết thúc (`makespan`), chi phí (`cost`) và thời gian wall-clock (`seconds`). CSV dùng dấu phẩy và có hàng tiêu đề. Một số CSV cũ trong archive có ít cột cấu hình hơn các lần chạy mới.

MILP mặc định chạy 30 giây mỗi pha. `optimal` xác nhận đủ ba mục tiêu; `feasible` có nghiệm khả thi nhưng chưa chứng minh tối ưu đủ ba mục tiêu. `no_solution` là chưa có nghiệm để xuất; `wall_timeout`/`timeout` là vượt giới hạn tiến trình bên ngoài. Các ô mục tiêu trống khi không có nghiệm được xuất và kiểm tra. CSV cũ trong archive dùng `not_proven` khi chưa chứng minh tối ưu và không lưu nghiệm tạm.

Các cột `count_optimal`, `makespan_optimal`, `cost_optimal` ghi mục tiêu nào đã được chứng minh. `phase` là pha dừng; `objective_value`, `best_bound`, `relative_gap` thuộc riêng pha đó. Gap được tính bằng `abs(objective_value - best_bound) / max(1, abs(objective_value))`; không phải gap chung cho cả ba mục tiêu. Giá trị trống nghĩa là không có cận/gap dùng được.

Script so sánh lấy các dòng MILP từ [milp.csv](./results/milp.csv), ghép cùng năm heuristic và ALNS vào [heuristics.csv](./results/heuristics.csv); không tự chạy lại MILP. MILP hiện chạy trên 15 test thuộc bộ nhỏ. Với 12 stress test, dòng MILP được đánh dấu `not_run`, không giả làm timeout hoặc nghiệm tối ưu.

Thời gian gồm khởi động, đọc dữ liệu và giải; không gồm biên dịch/kiểm tra nghiệm. Giới hạn SCIP áp dụng từng pha, không giới hạn thời gian dựng mô hình. Các ngân sách MILP và heuristic khác nhau; CSV không hàm ý so sánh cùng thời gian chạy.

## Kiểm tra nghiệm riêng

Bộ kiểm tra xác nhận định dạng, không lặp công việc, đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm và không chồng lấn. Heuristic phải đạt số công việc tối đa; nghiệm tạm MILP được phép có số công việc nhỏ hơn nếu pha đầu chưa chứng minh tối ưu, thể hiện bằng cờ trong CSV. Benchmark MILP còn đối chiếu nghiệm `optimal` của mẫu/ca biên với giá trị đã biết; script so sánh heuristic chỉ dùng dòng MILP `optimal` làm tham chiếu chứng minh.

Hai ca kiểm tra riêng mục tiêu trong bộ nhỏ dùng $Q = 0$ để cô lập hành vi, là mở rộng được cả hai chương trình hỗ trợ ngoài cận $1 \le Q$ trong đề.

Nếu muốn tự lưu và kiểm tra một lịch, biên dịch ALNS và tạo thư mục `.build` trước, rồi chạy:

```bash
solutions/alns/alns 2000 1 < tests/data/small/sample.txt > .build/sample.out
.venv/bin/python tests/scripts/check.py tests/data/small/sample.txt .build/sample.out
```
