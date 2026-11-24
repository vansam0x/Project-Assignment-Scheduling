# Các heuristic lập lịch bằng C++17

Tất cả thuật toán sử dụng cùng [quy ước mô hình](../milp/model.md), xác định chính xác tập công việc tối đa trước khi tìm kiếm. Sau đó so sánh nghiệm theo thứ tự `(makespan, cost)`. Không có bảo đảm tối ưu cho hai tiêu chí này.

## Các thuật toán

| Tên CLI | Cách xây dựng hoặc cải thiện lịch |
| --- | --- |
| `greedy` | Duyệt theo thứ tự topo Kahn; chọn đội hoàn thành sớm nhất, hòa thì chọn chi phí thấp |
| `lpt` | Ưu tiên công việc có thời lượng dài hơn trong các công việc đang sẵn sàng; chọn đội như greedy |
| `critical_path` | Ưu tiên tổng thời lượng lớn nhất từ công việc tới một đỉnh kết thúc; chọn đội như greedy |
| `multistart` | Khởi tạo bằng greedy, lặp xáo trộn thứ tự ưu tiên rồi dựng lại toàn bộ lịch; 1/3 vòng dùng chọn đội có nhiễu thời gian |
| `sa` | Simulated annealing: đổi chỗ hai vị trí ưu tiên, bỏ lựa chọn đội của hai việc đó rồi giải mã lại; cho phép tạm nhận bước xấu |

ALNS được triển khai riêng trong [chương trình ALNS](../alns/README.md), không thuộc CLI heuristic này.

Với `critical_path`, điểm ưu tiên được tính ngược thứ tự topo:

$$
b_i = d_i + \max_{j \in Succ(i)} b_j,
$$

trong đó giá trị max của tập rỗng bằng 0, chỉ xét các việc được chọn. Đây là heuristic dùng độ dài đường còn lại trên đồ thị tiền nhiệm, chưa tính hàng đợi của đội; không phải đường găng chính xác của lịch có giới hạn tài nguyên.

`lpt` là biến thể list scheduling có ràng buộc tiền nhiệm và đội hợp lệ. Không áp dụng các bảo đảm xấp xỉ của LPT trong bài toán máy song song đơn giản cho mô hình này.

SA dùng cùng công thức nhiệt độ và chấp nhận như [ALNS](../alns/README.md). Các lịch ưu tiên sau đổi chỗ hoặc xáo trộn được bộ giải mã sửa theo tiền nhiệm; luôn có lịch hợp lệ. Mọi phương pháp tìm kiếm giữ nghiệm tốt nhất từ greedy, nên không trả về nghiệm kém hơn greedy. Riêng hai phương pháp ưu tiên `lpt` và `critical_path` dựng một lịch độc lập, có thể kém greedy.

Bộ giải mã hiện chỉ nối việc vào cuối lịch đội, không chèn vào khoảng trống. Đây là hạn chế chung khi so sánh các chiến lược, đồng thời là hướng cải tiến riêng cho sau này.

## Biên dịch và chạy

Từ thư mục gốc:

```bash
cmake -S . -B .build -DCMAKE_BUILD_TYPE=Release
cmake --build .build --target heuristics --parallel
# Tham số: thuật toán, số vòng lặp, seed
.build/heuristics critical_path 0 0 < tests/data/small/sample.txt
.build/heuristics sa 2000 1 < tests/data/small/sample.txt
```

`greedy`, `lpt`, `critical_path` không dùng số vòng lặp hoặc seed. Lịch xuất stdout theo đề bài; tóm tắt thuật toán/mục tiêu xuất stderr. Cùng seed tái lập trong cùng môi trường C++/thư viện chuẩn; không hứa cùng chuỗi ngẫu nhiên giữa mọi thư viện chuẩn khác nhau.

Chi phí và tổng thời gian phải nằm trong miền `long long`, các phép tính cần đủ khoảng an toàn để không tràn số. Dữ liệu benchmark sử dụng giá trị nhỏ, đã kiểm tra các cận đề bài.

## So sánh và kiểm thử

```bash
.venv/bin/python tests/unit/test_cpp.py
.venv/bin/python tests/scripts/compare_heuristics.py
# Chỉ chạy stress, tăng ngân sách tìm kiếm
.venv/bin/python tests/scripts/compare_heuristics.py --suite stress --time-limit 60 --memory-mb 4096
```

Script chạy lại MILP, năm heuristic và ALNS với cùng `--time-limit` (mặc định tổng 30 giây) và `--memory-mb` (mặc định 2048 MiB không gian địa chỉ) cho mỗi lượt. Chỉ cần một lệnh; không cần chạy MILP trước. ALNS, SA và multistart tìm kiếm theo thời gian, dùng seed 1/2/3; các phương pháp tất định chạy một lần và có thể kết thúc sớm. Kết quả của mỗi lần gọi được ghi trực tiếp vào [tests/results/](../../tests/results/README.md), gồm `config.csv`, `runs.csv`, `comparison.csv` và `timing.csv`; lần chạy mới ghi đè kết quả cũ. Trong chế độ giới hạn thời gian, cùng seed không bảo đảm cùng kết quả vì số vòng hoàn thành phụ thuộc tốc độ máy.

Xem [kết quả đo thực tế dạng CSV](../../tests/results/).
