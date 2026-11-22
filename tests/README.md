# Bộ dữ liệu và cách chạy

- [instances/](./instances/): mẫu đề, ca biên và dữ liệu ngẫu nhiên nhỏ.
- [generate.py](./generate.py): bộ sinh dữ liệu tái lập bằng seed.
- [check.py](./check.py): kiểm tra nghiệm độc lập với OR-Tools và mã C++.
- [benchmark.py](./benchmark.py): chạy MILP, greedy, ALNS và ghi CSV.
- [compare_heuristics.py](./compare_heuristics.py): chạy sáu heuristic C++ trên bộ nhỏ/stress và ghi CSV.
- [test_cpp.py](./test_cpp.py): kiểm thử C++, ca biên, dữ liệu lỗi và seed.
- [stress/](./stress/README.md): 12 test lớn, đạt N=1000, Q=1000, M=500, K=100000.

## Chạy

Từ thư mục gốc, với OR-Tools và g++ hỗ trợ C++17:

```bash
.venv/bin/python tests/generate.py
.venv/bin/python tests/benchmark.py --milp-seconds 10 --iterations 2000
.venv/bin/python tests/test_cpp.py
.venv/bin/python tests/compare_heuristics.py
```

Sinh và chạy riêng nhóm lớn:

```bash
.venv/bin/python tests/generate.py --suite stress
.venv/bin/python tests/stress/benchmark.py --iterations 200 --seeds 1 2 3
```

Bộ sinh mặc định tạo cả bộ nhỏ và stress, giữ nguyên mẫu đề; dùng `--suite small` để chỉ sinh bộ nhỏ. Nếu không dùng môi trường ảo của dự án, thay `.venv/bin/python` bằng interpreter đã cài [requirements.txt](../solutions/milp/requirements.txt).

Các script benchmark chỉ ghi kết quả CSV, không sinh báo cáo Markdown, lịch riêng, log hoặc metadata. Chạy lại ghi đè CSV tương ứng; dữ liệu trong bộ nhớ vẫn được kiểm tra trước khi ghi kết quả.

## File kết quả

| CSV | Nội dung |
| --- | --- |
| [results/benchmark.csv](./results/benchmark.csv) | MILP, greedy và ALNS trên bộ nhỏ |
| [results_2s/benchmark.csv](./results_2s/benchmark.csv) | Kết quả đã chạy với MILP 2 giây mỗi pha |
| [results_30s/benchmark.csv](./results_30s/benchmark.csv) | Kết quả đã chạy riêng ba test N=60 với MILP 30 giây mỗi pha |
| [heuristic_results/benchmark.csv](./heuristic_results/benchmark.csv) | Sáu heuristic trên 27 test |
| [stress/results/benchmark.csv](./stress/results/benchmark.csv) | Greedy/ALNS trên stress test |

Mỗi dòng tương ứng một lần chạy: tên instance, kích thước, thuật toán, seed, trạng thái, số công việc (`count`), thời điểm kết thúc (`makespan`), tổng chi phí (`cost`) và thời gian wall-clock (`seconds`). Các lần chạy mới ghi thêm ngân sách vòng lặp/giới hạn pha khi phù hợp. CSV dùng dấu phẩy, có hàng tiêu đề; có thể mở bằng trình đọc CSV hoặc bảng tính.

`not_proven` nghĩa là MILP chưa chứng minh tối ưu, không có nghĩa vô nghiệm. `wall_timeout`/`timeout` nghĩa là tiến trình vượt thời gian bên ngoài. Các ô mục tiêu trống khi không có nghiệm được xuất và kiểm tra; không thay bằng 0. Thời gian gồm khởi động, đọc dữ liệu và giải, không gồm biên dịch/kiểm tra nghiệm. Giới hạn SCIP áp dụng từng pha, không giới hạn thời gian dựng mô hình.

## Thiết kế test và kiểm tra

Bộ nhỏ có mẫu đề, chu trình, thiếu đội, một đội làm nhiều việc, ưu tiên makespan trước chi phí và chi phí âm. Các nhóm ngẫu nhiên có N=8/20/60, ba seed mỗi nhóm. Hai ca kiểm tra riêng mục tiêu dùng Q=0 để cô lập hành vi, là mở rộng được cả hai chương trình hỗ trợ ngoài cận Q≥1 trong đề.

Bộ kiểm tra xác nhận định dạng, không lặp công việc, đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm, không chồng lấn và số công việc tối đa. Benchmark MILP còn đối chiếu mục tiêu của mẫu/ca biên với giá trị đã biết. So sánh heuristic dùng các nghiệm MILP đã được chứng minh trong CSV hiện tại làm tham chiếu kiểm tra; không tự chạy lại MILP.

Để kiểm tra riêng một lịch mà bạn chủ động lưu:

```bash
solutions/alns/alns 2000 1 < tests/instances/sample.txt > .build/sample.out
.venv/bin/python tests/check.py tests/instances/sample.txt .build/sample.out
```

Lệnh này cần binary ALNS đã biên dịch và thư mục `.build` đã tồn tại. Các script benchmark không tự lưu lịch riêng.
