# Giải bằng OR-Tools và SCIP

Phần phát biểu toán học nằm trong [model.md](./model.md). Mô tả đề bài nằm trong [README gốc](../../README.md).

Các lệnh bên dưới chạy từ thư mục gốc của dự án, dùng môi trường `.venv` đã có. Mã nguồn bộ giải nằm trong [solve.py](./solve.py).

## Chạy so sánh các thuật toán

Chạy MILP, năm heuristic và ALNS bằng một lệnh:

```bash
.venv/bin/python tests/scripts/benchmark.py --time-limit 30 --memory-mb 2048
```

Mỗi thuật toán và mỗi seed có cùng giới hạn **30 giây cho toàn tiến trình** và **2048 MiB không gian địa chỉ** trên Linux. Thời gian gồm khởi động, đọc dữ liệu, dựng mô hình và giải; không gồm biên dịch hoặc kiểm tra nghiệm. MILP chia thời gian còn lại cho ba pha theo thứ tự ưu tiên, không được cấp thêm 30 giây ở mỗi pha. ALNS, multistart và SA tìm kiếm theo thời gian; greedy, LPT và critical path có thể kết thúc sớm. Bộ chạy giữ nghiệm tốt nhất đã xuất và kiểm tra nếu tiến trình bị ngắt.

Đổi `--time-limit 60` để cấp tổng 60 giây, hoặc `--memory-mb 4096` để cấp 4 GiB cho **tất cả** thuật toán. Dùng `--suite small` hoặc `--suite stress` để chọn bộ dữ liệu; mặc định chạy cả hai. [benchmark_stress.py](../../tests/scripts/benchmark_stress.py) là lệnh tắt cho bộ stress, nhận cùng các tham số. [compare_heuristics.py](../../tests/scripts/compare_heuristics.py) là lệnh tương đương, chạy lại cả MILP và các thuật toán khác; không cần chạy nối tiếp hai lệnh.

Benchmark ghi bốn bảng CSV trực tiếp vào [thư mục kết quả](../../tests/results/): xem [hướng dẫn kết quả](../../tests/results/README.md). `comparison.csv` so sánh chất lượng nghiệm; `runs.csv` giữ các cờ chứng minh từng mục tiêu của MILP. `feasible` là nghiệm khả thi chưa chứng minh tối ưu đủ ba mục tiêu; chỉ `optimal` mới xác nhận cả ba.

## Chạy riêng một test

Chỉ dùng khi muốn kiểm tra trực tiếp bộ giải, không cần chạy benchmark:

```bash
.venv/bin/python solutions/milp/solve.py < tests/data/small/sample.txt
```

Kết quả chạy mẫu được SCIP chứng minh tối ưu: `R = 5`, `T = 235`, `C = 145`. Một nghiệm trả về là `(1,5,25)`, `(2,2,85)`, `(3,6,90)`, `(4,3,85)`, `(5,5,215)`; thời điểm bắt đầu công việc 5 có thể khác lịch minh họa mà vẫn đạt cùng ba giá trị mục tiêu.

Lịch được in ra stdout theo định dạng đề bài; giá trị mục tiêu, trạng thái và cận của pha đang giải được in ra stderr. Mặc định giới hạn 30 giây mỗi pha, tối đa ba pha, cộng thời gian dựng mô hình. Nếu hết giờ với nghiệm khả thi, chương trình xuất nghiệm tạm và dừng; chỉ tiếp tục sang pha sau khi pha trước đã được chứng minh tối ưu. Nếu pha sau chưa tìm được nghiệm mới, giữ lại nghiệm đã lưu từ pha trước.

Mô hình có `N + K` biến chọn và thêm $\sum_j\binom{|A_j|}{2}$ biến thứ tự, trong đó $A_j$ là tập công việc đội j làm được. Vì vậy mô hình MILP theo cặp này phù hợp để học mô hình hóa và giải các trường hợp nhỏ/vừa, không bảo đảm xử lý được giới hạn lớn nhất của đề. Với dữ liệu lớn, nên cân nhắc CP-SAT với optional intervals và `NoOverlap` để tránh mở rộng toàn bộ cặp công việc.

Xem [bộ test và lệnh benchmark](../../tests/README.md) và [kết quả CSV](../../tests/results/).
