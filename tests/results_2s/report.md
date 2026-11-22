# Kết quả thực nghiệm

MILP: 2 giây mỗi pha (tối đa 3 pha); ALNS: 2000 vòng lặp, seed 1/2/3.
Thời gian là wall-clock của subprocess, gồm khởi động và dựng mô hình; không gồm biên dịch C++.
Mọi nghiệm xuất ra đã qua bộ kiểm tra độc lập: đội hợp lệ, thời điểm sẵn sàng, tiền nhiệm, không chồng lấn và số công việc tối đa.
MILP dừng khi chưa chứng minh tối ưu được ghi `not_proven`; mã hiện tại không xuất incumbent trong trường hợp này.

| Test | N | MILP (R,T,C) | MILP giây | Greedy (T,C) | ALNS tốt nhất (T,C) | T ALNS min–max | ALNS giây TB |
| --- | ---: | --- | ---: | --- | --- | --- | ---: |
| cost_tie | 1 | (1,3,-5) | 0.098 | (3,-5) | (3,-5) | 3–3 | 0.003 |
| cycle | 3 | (0,0,0) | 0.102 | (0,0) | (0,0) | 0–0 | 0.001 |
| large_0 | 60 | not_proven | 2.955 | (154,2683) | (135,2144) | 135–144 | 0.016 |
| large_1 | 60 | not_proven | 2.534 | (169,3236) | (133,2471) | 133–143 | 0.017 |
| large_2 | 60 | not_proven | 2.563 | (159,2776) | (130,2642) | 130–141 | 0.017 |
| medium_0 | 20 | (20,81,1035) | 1.500 | (100,967) | (85,895) | 85–88 | 0.007 |
| medium_1 | 20 | (20,81,969) | 1.055 | (104,1061) | (84,1023) | 84–86 | 0.007 |
| medium_2 | 20 | (20,103,925) | 1.260 | (131,926) | (103,980) | 103–107 | 0.007 |
| missing_team | 3 | (0,0,0) | 0.118 | (0,0) | (0,0) | 0–0 | 0.001 |
| priority | 1 | (1,3,10) | 0.093 | (3,10) | (3,10) | 3–3 | 0.002 |
| sample | 5 | (5,235,145) | 0.108 | (235,145) | (235,145) | 235–235 | 0.004 |
| single_team | 4 | (4,11,10) | 0.107 | (11,10) | (11,10) | 11–11 | 0.002 |
| small_0 | 8 | (8,63,424) | 0.113 | (92,428) | (63,424) | 63–63 | 0.003 |
| small_1 | 8 | (8,55,448) | 0.132 | (59,522) | (55,448) | 55–55 | 0.005 |
| small_2 | 8 | (8,66,319) | 0.196 | (72,319) | (66,319) | 66–66 | 0.004 |

ALNS tốt nhất là nghiệm tốt nhất trong ba lần chạy; không phải giá trị trung bình hoặc chứng minh tối ưu.
Khi makespan khác nhau, không so chi phí riêng lẻ để xếp hạng. Khi MILP chưa chứng minh tối ưu, chưa thể tính khoảng cách tới tối ưu.
Các ngân sách dừng khác nhau và Python/C++ có chi phí khởi động khác nhau; bảng này đánh giá thực dụng, không phải so sánh tốc độ thuật toán trong điều kiện đồng nhất.

Dữ liệu chi tiết: [benchmark.csv](./benchmark.csv); cấu hình: [metadata.json](./metadata.json).
