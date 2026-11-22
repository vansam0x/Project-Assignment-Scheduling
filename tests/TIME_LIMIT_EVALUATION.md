# Thử tăng giới hạn thời gian MILP

Ngày chạy: 22/11/2026. Giữ nguyên mô hình, dữ liệu, phiên bản OR-Tools/SCIP và cấu hình ALNS; chỉ tăng giới hạn thời gian MILP.

Bảng dưới chỉ đánh giá bộ 15 test ban đầu, tối đa N=60. Đã bổ sung [12 stress test](./stress/README.md) đạt N=1000, Q=1000, M=500, K=100000 và [kết quả greedy/ALNS riêng](./stress/results/report.md). Chưa chạy MILP trên nhóm stress; không suy rộng kết quả tăng thời gian dưới đây sang các giới hạn lớn này.

| Ngân sách mỗi pha | Phạm vi chạy | Chứng minh tối ưu đủ ba mục tiêu |
| --- | --- | --- |
| 2 giây | Toàn bộ 15 test | 12/15 |
| 10 giây | Toàn bộ 15 test | 12/15 |
| 30 giây | Chỉ 3 test N=60 chưa được chứng minh | 0/3 |

Cả ba test N=60 đều chứng minh được số công việc tối đa là 60. Ở cả ba mức ngân sách, SCIP dừng tại pha tối thiểu makespan với `FEASIBLE` (mã trạng thái 1), chưa đạt `OPTIMAL`; pha tối thiểu chi phí chưa được chạy.

| Test | Wall-clock 2 giây | Wall-clock 10 giây | Wall-clock 30 giây | Kết quả tại 30 giây |
| --- | ---: | ---: | ---: | --- |
| large_0 | 2.955s | 10.901s | 30.889s | Chưa chứng minh makespan tối ưu |
| large_1 | 2.534s | 10.655s | 30.541s | Chưa chứng minh makespan tối ưu |
| large_2 | 2.563s | 10.579s | 30.565s | Chưa chứng minh makespan tối ưu |

Wall-clock gồm khởi động Python, import OR-Tools, dựng mô hình và các pha đã chạy. Giới hạn áp dụng riêng cho từng pha, không phải toàn bộ tiến trình.

## Kết luận

Trong phạm vi thử này, tăng từ 2 lên 10 rồi 30 giây mỗi pha chưa làm tăng số test được chứng minh tối ưu. Điều này không có nghĩa các nghiệm tìm được không tối ưu hoặc tăng thêm thời gian sẽ không có tác dụng; chỉ có nghĩa chưa có chứng minh trong các ngân sách đã thử.

Mã hiện tại không lưu incumbent, cận dưới hoặc optimality gap khi có pha hết giờ. Vì vậy chưa thể kết luận liệu chất lượng nghiệm tạm có cải thiện khi tăng thời gian, cũng chưa thể so trực tiếp các nghiệm tạm đó với ALNS.

Bước cải tiến phù hợp tiếp theo là ghi lại incumbent/cận/gap và tiền xử lý tập công việc tối đa để bỏ pha đầu, cố định biến chọn. Những thay đổi đó chưa áp dụng trong lần thử này để giữ nguyên mô hình khi so ngân sách.

## Kết quả và cách tái lập

- [Kết quả 2 giây](./results_2s/report.md), [CSV](./results_2s/benchmark.csv), [cấu hình](./results_2s/metadata.json).
- [Kết quả 10 giây](./results/report.md), [CSV](./results/benchmark.csv), [cấu hình](./results/metadata.json).
- [CSV 30 giây](./results_30s/benchmark.csv), [cấu hình](./results_30s/metadata.json); log từng instance nằm cùng thư mục.

Từ thư mục gốc, tái lập toàn bộ mức 10 giây (ghi đè báo cáo hiện tại):

```bash
.venv/bin/python tests/benchmark.py --milp-seconds 10 --iterations 2000
```

Tái lập riêng một test ở mức 30 giây:

```bash
.venv/bin/python solutions/milp/solve.py --time-limit 30 < tests/instances/large_0.txt
```
