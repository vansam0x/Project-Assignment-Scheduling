# Kết quả stress test

ALNS: 200 vòng lặp, seed [1, 2, 3]; timeout mỗi lượt 30 giây.
Thời gian subprocess gồm đọc dữ liệu và khởi động; không gồm biên dịch hoặc kiểm tra nghiệm.
MILP không chạy trên nhóm này; số biến thứ tự được tính trực tiếp từ dữ liệu, không dựng mô hình.

| Test | N/Q/M/K | Biến thứ tự MILP | Greedy T | ALNS tốt nhất (T,C) | T ALNS min–max | ALNS giây TB |
| --- | --- | ---: | ---: | --- | --- | ---: |
| scale200_2026 | 200/200/20/2000 | 99,705 | 7801 | (7801,88197) | 7801–7801 | 0.012 |
| scale200_2027 | 200/200/20/2000 | 99,471 | 6499 | (6499,88954) | 6499–6499 | 0.011 |
| scale500_2026 | 500/500/100/10000 | 499,893 | 4896 | (4896,199269) | 4896–4896 | 0.038 |
| scale500_2027 | 500/500/100/10000 | 498,449 | 5450 | (5426,169627) | 5426–5450 | 0.040 |
| max_dense_2026 | 1000/1000/500/100000 | 9,993,419 | 4722 | (4613,208924) | 4613–4722 | 0.203 |
| max_dense_2027 | 1000/1000/500/100000 | 9,988,681 | 4228 | (4228,227358) | 4228–4228 | 0.190 |
| max_sparse_2026 | 1000/1000/500/1000 | 951 | 6242 | (5891,490383) | 5891–6242 | 0.032 |
| max_sparse_2027 | 1000/1000/500/1000 | 1,005 | 6128 | (6128,512104) | 6128–6128 | 0.032 |
| bottleneck_2026 | 1000/1000/10/10000 | 4,995,000 | 52833 | (52833,508684) | 52833–52833 | 0.059 |
| bottleneck_2027 | 1000/1000/10/10000 | 4,995,000 | 50893 | (50893,503729) | 50893–50893 | 0.064 |
| max_chain_2026 | 1000/1000/500/100000 | 9,991,152 | 503147 | (503147,10287) | 503147–503147 | 0.174 |
| max_chain_2027 | 1000/1000/500/100000 | 9,988,092 | 505387 | (505387,10902) | 505387–505387 | 0.160 |

48/48 lượt xuất nghiệm đã qua kiểm tra độc lập, gồm xác nhận số công việc tối đa.
Chưa có chứng minh tối ưu makespan/chi phí. Best-of-seeds không đại diện cho giá trị trung bình.
Đây là smoke benchmark với ngân sách nhỏ; không dùng để kết luận ALNS đã hội tụ hoặc giải được mọi instance giới hạn lớn.

Chi tiết: [benchmark.csv](./benchmark.csv), [metadata.json](./metadata.json), [manifest dữ liệu](../manifest.json).
