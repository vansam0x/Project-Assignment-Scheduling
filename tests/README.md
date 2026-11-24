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
    ├── config.csv     # Ngân sách, suite và seed của lần chạy gần nhất
    ├── runs.csv       # Chi tiết từng lượt chạy
    ├── comparison.csv # Chất lượng nghiệm, mỗi dòng một test
    ├── timing.csv     # Thời gian và trạng thái từng lượt
    └── README.md      # Hướng dẫn đọc và quản lý kết quả
```

- [data/small/](./data/small/): mẫu đề, ca biên và các nhóm N=8/20/60.
- [data/stress/](./data/stress/README.md): dữ liệu đạt N=1000, Q=1000, M=500, K=100000; thông số và hash nằm trong [manifest.json](./data/stress/manifest.json).
- [scripts/paths.py](./scripts/paths.py): khai báo tập trung đường dẫn dữ liệu và kết quả.
- [scripts/build_cpp.py](./scripts/build_cpp.py): build target C++ qua [CMakeLists.txt](../CMakeLists.txt); binary nằm trong `.build`.
- [unit/test_cpp.py](./unit/test_cpp.py): kiểm tra ca biên, dữ liệu lỗi và tính tái lập seed cho các thuật toán C++.

## Lệnh chạy

Chạy từ thư mục gốc với CMake từ 3.16, GCC hỗ trợ C++17 và OR-Tools. Script tự cấu hình CMake ở chế độ Release và build target cần dùng trước khi đo thời gian. Nếu không dùng môi trường ảo của dự án, thay `.venv/bin/python` bằng interpreter đã cài [requirements.txt](../solutions/milp/requirements.txt).

Script tìm `cmake` trong PATH, sau đó tìm bản cục bộ tại `.build/tools/cmake/bin/cmake` nếu có.

```bash
# Sinh dữ liệu (giữ nguyên mẫu đề)
.venv/bin/python tests/scripts/generate.py
# Chỉ sinh bộ lớn hoặc bộ nhỏ
.venv/bin/python tests/scripts/generate.py --suite stress
.venv/bin/python tests/scripts/generate.py --suite small

# Chạy kiểm thử tự động
.venv/bin/python -m unittest discover -s tests/unit

# So sánh tất cả thuật toán với cùng ngân sách (mặc định --suite all)
.venv/bin/python tests/scripts/benchmark.py --time-limit 30 --memory-mb 2048

# Chỉ chạy MILP trên toàn bộ test
.venv/bin/python tests/scripts/benchmark.py --suite all --milp-only --time-limit 300 --memory-mb 8192

# Chỉ chạy bộ lớn
.venv/bin/python tests/scripts/benchmark_stress.py --time-limit 30 --memory-mb 2048

```

Bộ sinh ghi đè dữ liệu do nó quản lý, giữ nguyên [sample.txt](./data/small/sample.txt). Benchmark kiểm tra nghiệm trước khi ghi. Mỗi lần gọi ghi đè bốn CSV trong [results/](./results/) và in đường dẫn ngay khi bắt đầu.

Trong lúc chạy, benchmark in log tiến độ ngay lập tức cho từng instance, thuật toán và seed, cùng giới hạn thời gian/bộ nhớ, trạng thái, bộ mục tiêu `(R, T, C)` và thời lượng. Các dòng `start` cho biết lượt đang chạy; các dòng `done` cho biết lượt đã kết thúc.

## File kết quả

Trong [results/](./results/):

| File | Nội dung |
| --- | --- |
| `config.csv` | Suite, giới hạn thời gian/bộ nhớ, seed và chế độ chỉ MILP |
| `runs.csv` | Mỗi dòng một lượt chạy, giữ đầy đủ thông tin chẩn đoán |
| `comparison.csv` | Mỗi dòng một test; mỗi thuật toán có bộ `(R, T, C)`, các cột số riêng, trạng thái, số lượt, số lượt có nghiệm, seed tốt nhất và số lần đạt nghiệm tốt nhất |
| `timing.csv` | Thời gian, trạng thái, pha dừng, ngân sách và lỗi của từng thuật toán/seed |

Các bảng được cập nhật sau mỗi lượt hoàn thành. Nếu ngắt giữa chừng, bảng phản ánh các lượt đã ghi; `not_run` nghĩa là chưa có lượt chạy, `no_solution` nghĩa là đã chạy nhưng chưa có nghiệm được kiểm tra. Nghiệm rỗng hợp lệ vẫn được ghi `(0, 0, 0)`.

Đọc `comparison.csv` trước: chọn nghiệm theo thứ tự **R lớn nhất → T nhỏ nhất → C nhỏ nhất**. `best_algorithms` liệt kê tất cả thuật toán đồng hạng tốt nhất trong những lượt đã hoàn thành, không khẳng định tối ưu toàn cục. Với thuật toán ngẫu nhiên, chọn nguyên bộ mục tiêu từ một lượt tốt nhất, không ghép trung bình các mục tiêu. `runs`, `valid_runs`, `best_seed`, `best_hits` cho biết số lượt, số lượt có nghiệm, seed đại diện và số lần đạt bộ tốt nhất. Kết quả tốt nhất của nhiều seed có tổng chi phí chạy lớn hơn một lượt MILP; xem `timing.csv` khi đánh giá tài nguyên.

`milp_proof=optimal` chỉ xuất hiện khi MILP chứng minh đủ ba mục tiêu; `not_proven` nghĩa là có nghiệm nhưng chưa chứng minh đủ. Ô trống nghĩa là chưa có nghiệm MILP. Trạng thái dừng vẫn được giữ kể cả khi khôi phục được nghiệm tạm.

Mỗi dòng là một lần chạy: tên instance, kích thước, thuật toán, seed, ngân sách, trạng thái, số công việc (`count`), thời điểm kết thúc (`makespan`), chi phí (`cost`) và thời gian wall-clock (`seconds`). CSV dùng dấu phẩy và có hàng tiêu đề.

Mọi thuật toán mặc định có tổng 30 giây và 2048 MiB không gian địa chỉ mỗi lượt chạy trên Linux. `optimal` xác nhận đủ ba mục tiêu; `feasible` có nghiệm khả thi nhưng chưa chứng minh tối ưu đủ ba mục tiêu. `no_solution` là chưa có nghiệm để xuất; `wall_timeout`/`timeout` là vượt giới hạn tiến trình bên ngoài. Các ô mục tiêu trống khi không có nghiệm được xuất và kiểm tra.

Các cột `count_optimal`, `makespan_optimal`, `cost_optimal` ghi mục tiêu nào đã được chứng minh. `phase` là pha dừng; `objective_value`, `best_bound`, `relative_gap` thuộc riêng pha đó. Gap được tính bằng `abs(objective_value - best_bound) / max(1, abs(objective_value))`; không phải gap chung cho cả ba mục tiêu. Giá trị trống nghĩa là không có cận/gap dùng được.

[benchmark.py](./scripts/benchmark.py), [compare_heuristics.py](./scripts/compare_heuristics.py) và [benchmark_stress.py](./scripts/benchmark_stress.py) dùng cùng bộ chạy và cùng tham số `--time-limit`/`--memory-mb`. Chỉ cần chạy một lệnh. Mỗi seed là một lượt độc lập, có toàn bộ ngân sách; mặc định seed 1/2/3 cho ALNS, SA và multistart, thuật toán tất định chạy một lần. Các thuật toán tìm kiếm chạy theo thời gian, cột `iterations` để trống. Chạy theo thời gian có thể cho kết quả khác nhau dù cùng seed do tốc độ máy.

Kết quả cũ không được giữ tự động; nếu cần lưu, hãy sao chép cả thư mục [results/](./results/) trước lần chạy tiếp theo. Xem [hướng dẫn kết quả](./results/README.md) để chọn bảng cần đọc.

`wall_limit_seconds` và `memory_limit_mb` ghi giới hạn thực tế trên từng dòng. `seconds` gồm khởi động, đọc dữ liệu, dựng mô hình và giải; không gồm biên dịch. MILP dùng thời gian còn lại cho các pha, không cấp riêng 30 giây mỗi pha. Bộ nhớ giới hạn bằng Linux `RLIMIT_AS` từ trước khi khởi động chương trình, khác RSS. `peak_rss_mb` chỉ có khi đo được. `build_seconds` và `solve_seconds` tách thời gian MILP. Bộ chạy có thể cần thêm ít thời gian để kết thúc tiến trình khi hết hạn. Các phương pháp dựng lịch có thể kết thúc sớm; các phương pháp tìm kiếm dừng giữa các vòng và xuất nghiệm tốt nhất, có chừa một khoảng ngắn cho xuất kết quả. Nếu buộc dừng trong một vòng, bộ chạy khôi phục nghiệm đã xuất gần nhất; ô mục tiêu trống nếu chưa có nghiệm để kiểm tra.

Các lượt chạy cũ chưa ghi thời gian tách hoặc giới hạn bộ nhớ có thể để trống các cột mới. Không suy diễn ô trống thành thời gian 0 hay một ngân sách đã được áp dụng.

## Kiểm tra nghiệm riêng

Bộ kiểm tra xác nhận định dạng, không lặp công việc, đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm và không chồng lấn. Heuristic phải đạt số công việc tối đa; nghiệm tạm MILP được phép có số công việc nhỏ hơn nếu pha đầu chưa chứng minh tối ưu, thể hiện bằng cờ trong CSV. Benchmark MILP còn đối chiếu nghiệm `optimal` của mẫu/ca biên với giá trị đã biết; script so sánh heuristic chỉ dùng dòng MILP `optimal` làm tham chiếu chứng minh.

Hai ca kiểm tra riêng mục tiêu trong bộ nhỏ dùng $Q = 0$ để cô lập hành vi, là mở rộng được cả hai chương trình hỗ trợ ngoài cận $1 \le Q$ trong đề.

Nếu muốn tự lưu và kiểm tra một lịch, build ALNS qua CMake trước, rồi chạy:

```bash
.build/alns 2000 1 < tests/data/small/sample.txt > .build/sample.out
.venv/bin/python tests/scripts/check.py tests/data/small/sample.txt .build/sample.out
```
