# Project Assignment and Scheduling

So sánh mô hình MILP bằng OR-Tools/SCIP với ALNS và các heuristic trên cùng dữ liệu, từ test nhỏ đến giới hạn lớn của đề. Kết quả thực nghiệm được lưu dưới dạng CSV.

## Cấu trúc thư mục

```text
Project-Assignment-Scheduling/
├── CMakeLists.txt                # Build hai chương trình C++17
├── README.md
├── solutions/
│   ├── common/
│   │   └── scheduling.hpp       # Dữ liệu và bộ giải mã lịch dùng chung
│   ├── alns/
│   │   ├── main.cpp             # Thuật toán ALNS
│   │   └── README.md
│   ├── heuristics/
│   │   ├── main.cpp             # Greedy, LPT, Critical Path, multi-start, SA
│   │   └── README.md
│   └── milp/
│       ├── solve.py             # OR-Tools/SCIP
│       ├── model.md             # Phát biểu mô hình toán
│       ├── requirements.txt
│       └── README.md
├── tests/
│   ├── data/
│   │   ├── small/               # Mẫu đề và test nhỏ
│   │   └── stress/              # Test lớn và manifest dữ liệu
│   ├── scripts/                 # Sinh test, build, kiểm tra và benchmark
│   ├── unit/                    # Kiểm thử tự động
│   ├── results/                 # Kết quả CSV của lần chạy gần nhất
│   └── README.md
└── .build/                      # Binary và file build do CMake sinh, bỏ qua Git
```

## Build và chạy

Cần CMake từ 3.16 và GCC hỗ trợ C++17. Cấu hình build nằm trong [CMakeLists.txt](./CMakeLists.txt).

```bash
cmake -S . -B .build -DCMAKE_BUILD_TYPE=Release
cmake --build .build --parallel

.build/alns 2000 1 < tests/data/small/sample.txt
.build/heuristics sa 2000 1 < tests/data/small/sample.txt
```

Các script benchmark và kiểm thử tự build target cần thiết qua CMake, không cần biên dịch thủ công. Phần MILP dùng Python và [các thư viện riêng](./solutions/milp/requirements.txt). Xem [hướng dẫn kiểm thử](./tests/README.md) để chạy bộ dữ liệu và lưu kết quả CSV.

## Bài toán phân công và lập lịch dự án

Một dự án gồm **N công việc**, đánh số từ `1` đến `N`, cần được thực hiện bởi **M đội**, đánh số từ `1` đến `M`.

Thông tin của mỗi công việc và mỗi đội được cho như sau:

- `d(i)`: thời gian cần để hoàn thành công việc `i`.
- `s(j)`: thời điểm đội `j` bắt đầu sẵn sàng làm việc.
- Mỗi công việc chỉ có thể được thực hiện bởi một số đội nhất định. Với một cặp phân công hợp lệ `(i, j)`, `c(i, j)` là chi phí giao công việc `i` cho đội `j`.
- Có `Q` quan hệ trước–sau giữa các công việc. Mỗi cặp `(i, j)` có nghĩa là **công việc `j` chỉ được bắt đầu sau khi công việc `i` đã hoàn thành**.

### Yêu cầu

Lập lịch thực hiện các công việc. Với mỗi công việc được đưa vào lịch, cần xác định:

1. Đội được giao thực hiện công việc đó.
2. Thời điểm bắt đầu thực hiện.

Việc phân công phải phù hợp với khả năng thực hiện của đội, thời điểm đội sẵn sàng và các quan hệ trước–sau. Nếu công việc `i` bắt đầu tại thời điểm `u(i)`, nó hoàn thành tại thời điểm `u(i) + d(i)`.

### Mục tiêu tối ưu

Các tiêu chí được **ưu tiên theo đúng thứ tự** sau:

1. **Tối đa số công việc được lập lịch.**
2. Trong các lịch có số công việc lớn nhất, **tối thiểu thời điểm hoàn thành toàn bộ các công việc được lập lịch** (thời điểm kết thúc muộn nhất).
3. Trong các lịch cùng tối ưu hai tiêu chí trên, **tối thiểu tổng chi phí phân công**.

Nói cách khác, không được giảm số công việc để đổi lấy thời gian hoàn thành ngắn hơn, và không được kéo dài thời gian hoàn thành để đổi lấy chi phí thấp hơn khi số công việc giữ nguyên.

## Dữ liệu đầu vào

| Dòng | Nội dung | Ý nghĩa và giới hạn |
| --- | --- | --- |
| `1` | `N Q` | Số công việc và số quan hệ trước–sau; $1 \le N, Q \le 1000$. |
| `2` đến `Q + 1` | `i j` | Mỗi dòng mô tả một quan hệ: công việc `i` phải hoàn thành trước khi công việc `j` bắt đầu. |
| `Q + 2` | `d(1) d(2) ... d(N)` | Thời lượng của `N` công việc; $1 \le d(i) \le 1000$. |
| `Q + 3` | `M` | Số đội; $1 \le M \le 500$. |
| `Q + 4` | `s(1) s(2) ... s(M)` | Thời điểm sẵn sàng của `M` đội; $1 \le s(j) \le 1000$. |
| `Q + 5` | `K` | Số cặp phân công hợp lệ; $1 \le K \le 100000$. |
| `Q + 6` đến `Q + 5 + K` | `i j c(i,j)` | Đội `j` có thể thực hiện công việc `i` với chi phí `c(i,j)`. |

Chỉ những cặp công việc–đội được liệt kê trong `K` dòng cuối mới là các lựa chọn phân công hợp lệ. Đề gốc không nêu giới hạn giá trị của `c(i,j)`.

## Dữ liệu đầu ra

- Dòng đầu chứa số nguyên dương `R`: số công việc được lập lịch.
- `R` dòng tiếp theo, mỗi dòng chứa ba số nguyên dương `i j u`, nghĩa là:
  - Công việc `i` được giao cho đội `j`.
  - Công việc đó bắt đầu tại thời điểm `u`.

## Ví dụ

### Đầu vào

```text
5 4
1 2
1 4
2 5
3 5
60 45 120 150 20
6
100 20 65 40 25 90
13
1 4 20
1 5 30
1 6 10
2 2 25
2 5 30
3 1 20
3 6 70
4 2 10
4 3 10
4 5 20
5 1 40
5 2 20
5 5 10
```

### Đầu ra minh họa

```text
5
1 5 25
2 2 85
3 6 90
4 3 85
5 5 210
```

### Giải thích lịch minh họa

| Công việc | Đội thực hiện | Bắt đầu | Thời lượng | Kết thúc | Chi phí |
| --- | --- | --- | --- | --- | --- |
| 1 | 5 | 25 | 60 | 85 | 30 |
| 2 | 2 | 85 | 45 | 130 | 25 |
| 3 | 6 | 90 | 120 | 210 | 70 |
| 4 | 3 | 85 | 150 | 235 | 10 |
| 5 | 5 | 210 | 20 | 230 | 10 |

- Cả **5 công việc** đều được lập lịch.
- Công việc `2` và `4` bắt đầu khi công việc `1` vừa hoàn thành tại thời điểm `85`.
- Công việc `5` bắt đầu tại thời điểm `210`, sau khi cả công việc `2` và `3` đã hoàn thành.
- Các đội đều bắt đầu thực hiện công việc sau hoặc đúng thời điểm sẵn sàng.
- Thời điểm hoàn thành toàn bộ lịch là **235**; tổng chi phí phân công là **145**.

## Mô hình và lời giải

- [Phát biểu mô hình toán học MILP](./solutions/milp/model.md): biến, ràng buộc, mục tiêu và mối liên hệ với phương pháp đơn hình.
- [Lời giải bằng OR-Tools/SCIP](./solutions/milp/README.md): hướng dẫn chạy và kết quả kiểm chứng.
- [ALNS bằng C++](./solutions/alns/README.md): thuật toán thích nghi destroy–repair và baseline tham lam.
- [Các heuristic C++](./solutions/heuristics/README.md): greedy, LPT, Critical Path, multi-start và simulated annealing.
- [Bộ test và bộ sinh dữ liệu](./tests/README.md): kiểm tra nghiệm và tái lập thực nghiệm.
- [Hướng dẫn đọc bảng so sánh và kết quả CSV](./tests/README.md#file-kết-quả).
- [Thư mục kết quả](./tests/results/): luôn chứa kết quả của lần chạy gần nhất.
