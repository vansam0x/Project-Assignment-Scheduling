# Giải bằng OR-Tools và SCIP

Phần phát biểu toán học nằm trong [model.md](./model.md). Mô tả đề bài nằm trong [README gốc](../../README.md).

Các lệnh bên dưới chạy từ thư mục gốc của dự án:

Mã nguồn: [solve.py](./solve.py). Dữ liệu mẫu dùng chung: [sample.txt](../../tests/data/small/sample.txt).

```bash
python -m pip install -r solutions/milp/requirements.txt
python solutions/milp/solve.py < tests/data/small/sample.txt
# Mặc định: giới hạn 30 giây cho mỗi pha tối ưu
python solutions/milp/solve.py --time-limit 30 < tests/data/small/sample.txt
```

Nếu dùng môi trường ảo đã tạo trong dự án, thay `python` bằng `.venv/bin/python`.

Kết quả chạy mẫu được SCIP chứng minh tối ưu: `R = 5`, `T = 235`, `C = 145`. Một nghiệm trả về là `(1,5,25)`, `(2,2,85)`, `(3,6,90)`, `(4,3,85)`, `(5,5,215)`; thời điểm bắt đầu công việc 5 có thể khác lịch minh họa mà vẫn đạt cùng ba giá trị mục tiêu.

Lịch được in ra stdout theo định dạng đề bài; giá trị mục tiêu, trạng thái và cận của pha đang giải được in ra stderr. Mặc định giới hạn 30 giây mỗi pha, tối đa ba pha, cộng thời gian dựng mô hình. Nếu hết giờ với nghiệm khả thi, chương trình xuất nghiệm tạm và dừng; chỉ tiếp tục sang pha sau khi pha trước đã được chứng minh tối ưu. Nếu pha sau chưa tìm được nghiệm mới, giữ lại nghiệm đã lưu từ pha trước.

Chạy MILP rồi ghép với năm heuristic và ALNS riêng trong cùng CSV:

```bash
.venv/bin/python tests/scripts/benchmark.py --milp-seconds 30
.venv/bin/python tests/scripts/compare_heuristics.py
```

[milp.csv](../../tests/results/milp.csv) chứa kết quả MILP và các cờ chứng minh từng mục tiêu. [heuristics.csv](../../tests/results/heuristics.csv) ghép các dòng MILP đó với kết quả của các thuật toán khác. `feasible` là nghiệm khả thi chưa chứng minh tối ưu đủ ba mục tiêu; chỉ `optimal` mới xác nhận cả ba.

Mô hình có `N + K` biến chọn và thêm $\sum_j\binom{|A_j|}{2}$ biến thứ tự, trong đó $A_j$ là tập công việc đội j làm được. Vì vậy mô hình MILP theo cặp này phù hợp để học mô hình hóa và giải các trường hợp nhỏ/vừa, không bảo đảm xử lý được giới hạn lớn nhất của đề. Với dữ liệu lớn, nên cân nhắc CP-SAT với optional intervals và `NoOverlap` để tránh mở rộng toàn bộ cặp công việc.

Xem [bộ test và lệnh benchmark](../../tests/README.md) và [kết quả CSV](../../tests/results/milp.csv).
