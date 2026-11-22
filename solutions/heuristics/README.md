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
| `alns` | Phá hủy 10–50% thứ tự/lựa chọn đội rồi sửa; thích nghi trọng số của 9 tổ hợp destroy–repair |

Với `critical_path`, điểm ưu tiên được tính ngược thứ tự topo:

$$
b_i = d_i + \max_{j \in Succ(i)} b_j,
$$

trong đó giá trị max của tập rỗng bằng 0, chỉ xét các việc được chọn. Đây là heuristic dùng độ dài đường còn lại trên đồ thị tiền nhiệm, chưa tính hàng đợi của đội; không phải đường găng chính xác của lịch có giới hạn tài nguyên.

`lpt` là biến thể list scheduling có ràng buộc tiền nhiệm và đội hợp lệ. Không áp dụng các bảo đảm xấp xỉ của LPT trong bài toán máy song song đơn giản cho mô hình này.

SA dùng cùng công thức nhiệt độ và chấp nhận như [ALNS](../alns/README.md). Các lịch ưu tiên sau đổi chỗ hoặc xáo trộn được bộ giải mã sửa theo tiền nhiệm; luôn có lịch hợp lệ. Mọi phương pháp tìm kiếm giữ nghiệm tốt nhất từ greedy, nên không trả về nghiệm kém hơn greedy. Riêng hai phương pháp ưu tiên `lpt` và `critical_path` dựng một lịch độc lập, có thể kém greedy.

## Cấu trúc OOP

Mã dùng chung nằm trong [scheduling.hpp](../common/scheduling.hpp):

- `Problem`: đọc/kiểm tra dữ liệu, xây đồ thị, xác định tập công việc hợp lệ tối đa.
- `Schedule`: lưu lịch, so sánh mục tiêu và xuất kết quả.
- `ScheduleDecoder`: giải mã thứ tự ưu tiên và lựa chọn đội, bảo đảm thời gian sẵn sàng/tiền nhiệm/không chồng lấn.
- `HeuristicSolver`: lớp cơ sở, giữ RNG, decoder và quy tắc chấp nhận simulated annealing.
- `GreedySolver`, `PrioritySolver`, `MultiStartSolver`, `SimulatedAnnealingSolver`, `AlnsSolver`: các chiến lược giải.

[main.cpp](./main.cpp) chỉ chọn chiến lược, đọc tham số và xuất kết quả. [CLI ALNS cũ](../alns/main.cpp) tiếp tục hỗ trợ thứ tự tham số cũ. Toàn bộ mã C++ dùng thụt lề bốn dấu cách, tên mô tả rõ, có namespace và cấu hình [clang-format](../../.clang-format).

Bộ giải mã hiện chỉ nối việc vào cuối lịch đội, không chèn vào khoảng trống. Đây là hạn chế chung khi so sánh các chiến lược, đồng thời là hướng cải tiến riêng cho sau này.

## Biên dịch và chạy

Từ thư mục gốc:

```bash
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic solutions/heuristics/main.cpp -o solutions/heuristics/heuristics
# Tham số: thuật toán, số vòng lặp, seed
solutions/heuristics/heuristics critical_path 0 0 < tests/instances/sample.txt
solutions/heuristics/heuristics sa 2000 1 < tests/instances/sample.txt
solutions/heuristics/heuristics alns 2000 1 < tests/instances/sample.txt
```

`greedy`, `lpt`, `critical_path` không dùng số vòng lặp hoặc seed. Lịch xuất stdout theo đề bài; tóm tắt thuật toán/mục tiêu xuất stderr. Cùng seed tái lập trong cùng môi trường C++/thư viện chuẩn; không hứa cùng chuỗi ngẫu nhiên giữa mọi thư viện chuẩn khác nhau.

Chi phí và tổng thời gian phải nằm trong miền `long long`, các phép tính cần đủ khoảng an toàn để không tràn số. Dữ liệu benchmark sử dụng giá trị nhỏ, đã kiểm tra các cận đề bài.

## So sánh và kiểm thử

```bash
.venv/bin/python tests/test_cpp.py
.venv/bin/python tests/compare_heuristics.py
# Chỉ chạy stress, tăng ngân sách tìm kiếm
.venv/bin/python tests/compare_heuristics.py --suite stress --stress-iterations 2000
```

Mỗi lần so sánh ghi đè [benchmark.csv](../../tests/heuristic_results/benchmark.csv), chỉ ghi kết quả CSV; không sinh báo cáo Markdown, lịch riêng, log hoặc metadata. Bộ nhỏ mặc định 2000 vòng lặp, stress 200 vòng lặp. Thuật toán ngẫu nhiên chạy seed 1/2/3; các phương pháp tất định chỉ chạy một lần. Không chạy lại MILP mà dùng chứng minh đã lưu trong bộ benchmark hiện tại.

Xem [kết quả đo thực tế dạng CSV](../../tests/heuristic_results/benchmark.csv).
