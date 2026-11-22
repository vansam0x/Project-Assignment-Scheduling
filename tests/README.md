# Bộ dữ liệu và đánh giá

- [instances/](./instances/): mẫu đề, ca biên và dữ liệu ngẫu nhiên đã sinh.
- [generate.py](./generate.py): bộ sinh tái lập, seed `2026`, `2027`, `2028` cho mỗi kích thước.
- [check.py](./check.py): kiểm tra nghiệm độc lập với OR-Tools và mã C++.
- [benchmark.py](./benchmark.py): biên dịch C++, chạy MILP, greedy và ALNS rồi tạo báo cáo.
- [results/report.md](./results/report.md): kết quả lần chạy thực tế; CSV, cấu hình, lịch và log đi kèm trong cùng thư mục.
- [TIME_LIMIT_EVALUATION.md](./TIME_LIMIT_EVALUATION.md): so sánh ngân sách MILP 2, 10 và 30 giây mỗi pha. Báo cáo hiện tại dùng 10 giây; kết quả ban đầu được lưu trong [results_2s/](./results_2s/), lần thử riêng N=60 ở 30 giây nằm trong [results_30s/](./results_30s/).
- [stress/](./stress/README.md): 12 test lớn, đạt N=1000, Q=1000, M=500, K=100000; bộ chạy và kết quả riêng.

## Sinh dữ liệu và chạy

Chạy từ thư mục gốc với môi trường có OR-Tools và trình biên dịch g++ hỗ trợ C++17:

```bash
.venv/bin/python tests/generate.py
.venv/bin/python tests/benchmark.py --milp-seconds 2 --iterations 2000
```

Nếu không dùng môi trường ảo của dự án, thay `.venv/bin/python` bằng interpreter đã cài [requirements.txt](../solutions/milp/requirements.txt).

Bộ sinh giữ nguyên [sample.txt](./instances/sample.txt), ghi đè các test do nó quản lý. Benchmark ghi đè kết quả có cùng tên. Mỗi test chạy MILP một lần, greedy một lần và ALNS ba lần với seed 1/2/3. Cùng một instance và quy ước được dùng cho tất cả thuật toán.

Bộ sinh mặc định tạo cả nhóm stress riêng; benchmark trên chỉ chạy bộ nhỏ. Sinh và chạy riêng nhóm lớn:

```bash
.venv/bin/python tests/generate.py --suite stress
.venv/bin/python tests/stress/benchmark.py --iterations 200 --seeds 1 2 3
```

## Thiết kế test

| Nhóm | Cấu hình | Mục đích |
| --- | --- | --- |
| sample | Mẫu đề | Đối chiếu `(R,T,C) = (5,235,145)` |
| cycle | Chu trình và hậu duệ | Không công việc nào được chọn |
| missing_team | Gốc thiếu đội, chuỗi hậu duệ | Kiểm tra điều kiện chọn đủ tiền nhiệm |
| single_team | 4 công việc, 1 đội | Không chồng lấn; makespan tối ưu 11 |
| priority | Đội rẻ hơn nhưng sẵn sàng muộn | Kiểm tra ưu tiên makespan trước chi phí |
| cost_tie | Hai đội cùng thời điểm sẵn sàng | Kiểm tra tối thiểu chi phí, có chi phí âm |
| small | N=8, M=3, 3 seed | So sánh với nghiệm MILP được chứng minh tối ưu |
| medium | N=20, M=5, 3 seed | Tăng độ khó phân công và lập lịch |
| large | N=60, M=10, 3 seed | Quan sát giới hạn thời gian MILP |

Các test ngẫu nhiên là DAG: xáo trộn nhãn trước khi sinh cạnh với xác suất `2/N`. Mỗi công việc có ít nhất một đội; thời lượng 1–30, thời điểm sẵn sàng 1–20, chi phí 1–100. Xác suất một đội hợp lệ là 0.5 với small/medium và 0.3 với large. Đây là phân bố thử nhỏ, chưa đại diện đầy đủ cho giới hạn N=1000, M=500 hoặc dữ liệu thực tế.

Hai ca kiểm tra riêng mục tiêu (`priority`, `cost_tie`) dùng Q=0 để cô lập hành vi; đây là mở rộng ngoài cận Q≥1 trong đề, được cả hai chương trình hỗ trợ.

## Kiểm tra và cách đọc kết quả

Bộ kiểm tra xác nhận định dạng đầu ra, không lặp công việc, đội hợp lệ, thời điểm sẵn sàng, điều kiện tiền nhiệm, không chồng lấn và số công việc tối đa. Các ca biên và mẫu có thêm đối chiếu mục tiêu MILP với giá trị đã biết; mọi kết quả heuristic được đối chiếu để không tốt hơn giá trị MILP đã chứng minh tối ưu. Nếu bất kỳ kiểm tra nào sai, benchmark dừng bằng lỗi.

Để kiểm tra riêng một lịch:

```bash
.venv/bin/python tests/check.py tests/instances/sample.txt tests/results/sample_alns_1.out
```

`not_proven` nghĩa là MILP chưa chứng minh tối ưu trong ngân sách, không có nghĩa là bài toán vô nghiệm. MILP hiện dừng ngay ở pha chưa tối ưu và không xuất incumbent. Thời gian bao gồm khởi động subprocess, import OR-Tools và dựng mô hình; giới hạn SCIP áp dụng cho từng pha giải, không giới hạn thời gian dựng mô hình. Benchmark còn có timeout bên ngoài bằng `3 * milp_seconds + 10` giây.

Chỉ gọi một nghiệm ALNS là tối ưu trên instance khi cả ba mục tiêu khớp nghiệm đã được MILP chứng minh tối ưu. Với instance chưa có chứng minh, báo cáo chỉ so với baseline greedy và các seed khác.
