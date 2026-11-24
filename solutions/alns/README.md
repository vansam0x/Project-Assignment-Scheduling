# ALNS bằng C++17

Thuật toán sử dụng cùng quy ước với [mô hình MILP](../milp/model.md). Đây là heuristic cho hai tiêu chí cuối; không chứng minh tối ưu makespan hay chi phí.

Xem thêm [các heuristic khác](../heuristics/README.md) và [kết quả so sánh dạng CSV](../../tests/results/).

## Xác định tập công việc tối đa

Loại các công việc không có đội và toàn bộ hậu duệ của chúng. Duyệt Kahn loại thêm công việc thuộc chu trình và hậu duệ của chu trình. Các công việc còn lại tạo thành DAG, có ít nhất một đội hợp lệ và chứa đủ tiền nhiệm. Do không có hạn chót, có thể xếp nối tiếp tất cả chúng theo thứ tự topo. Vì mọi công việc bị loại đều không thể xuất hiện trong nghiệm hợp lệ, tập còn lại là tập công việc tối đa và là duy nhất.

Vì vậy số công việc của ALNS là tối ưu chính xác; phần tìm kiếm chỉ so sánh cặp `(makespan, cost)` theo thứ tự từ điển.

## Biểu diễn và giải mã

Nghiệm lưu thứ tự công việc và đội được chọn. Bộ giải mã chọn công việc đang sẵn sàng theo độ ưu tiên trong thứ tự đó, rồi xếp vào cuối lịch đội tại thời điểm sớm nhất thỏa tiền nhiệm và thời điểm sẵn sàng. Cách nối vào cuối luôn bảo đảm không chồng lấn, nhưng không khai thác hết các khoảng trống giữa các công việc trên cùng đội; đây là một giới hạn của không gian tìm kiếm hiện tại.

## Destroy, repair và thích nghi

Mỗi vòng lặp xóa 10–50% công việc khỏi thứ tự ưu tiên và bỏ lựa chọn đội của chúng; các công việc giữ lại giữ thứ tự tương đối và đội. Công việc bị xóa được chèn lại vào các vị trí ngẫu nhiên; bộ giải mã luôn khôi phục thứ tự hợp lệ theo tiền nhiệm.

Ba toán tử destroy:

1. Chọn ngẫu nhiên.
2. Ưu tiên công việc kết thúc muộn (không phải phép xác định đường găng đầy đủ).
3. Ưu tiên công việc có chi phí phân công cao.

Ba chính sách repair cho các công việc bị xóa:

1. Chọn đội cho thời điểm hoàn thành sớm nhất, hòa thì chọn chi phí thấp.
2. Chọn đội rẻ nhất, hòa thì chọn thời điểm hoàn thành sớm.
3. Chọn theo thời điểm hoàn thành cộng nhiễu ngẫu nhiên, hòa thì chọn chi phí thấp.

Có 9 tổ hợp destroy–repair. Chọn bằng roulette theo trọng số, khởi tạo bằng 1. Sau mỗi lần dùng, cập nhật `w = 0.9*w + 0.1*reward`: thưởng 8 khi cải thiện nghiệm tốt nhất, 4 khi cải thiện nghiệm hiện tại, 1 khi được chấp nhận, 0.1 khi bị từ chối.

Tiêu chí chấp nhận cho phép bước xấu theo xác suất simulated annealing. Nhiệt độ giảm tuyến tính từ khoảng 5% makespan tốt nhất tới mức sàn 0.01; khi makespan bằng nhau, dùng chênh lệch chi phí chuẩn hóa để thăm dò. Nghiệm tốt nhất luôn được lưu và so sánh đúng thứ tự từ điển, dù nghiệm hiện tại có thể tạm thời xấu hơn.

Đây là ALNS với repair tham lam, chưa có regret-k insertion, giải bài toán con bằng MILP hay cơ chế restart. Không bảo đảm chất lượng đồng đều trên mọi dữ liệu.

## Chạy

Từ thư mục gốc dự án:

```bash
cmake -S . -B .build -DCMAKE_BUILD_TYPE=Release
cmake --build .build --target alns --parallel
# Tham số lần lượt: số vòng lặp và seed
.build/alns 2000 1 < tests/data/small/sample.txt
# Baseline tham lam, không chạy ALNS
.build/alns 0 0 < tests/data/small/sample.txt
```

Lịch xuất stdout theo đề bài, tóm tắt mục tiêu xuất stderr. Đầu vào dùng số nguyên và chỉ số hợp lệ như đề; chi phí/tổng thời gian phải nằm trong miền `long long` của C++. Bộ sinh test sử dụng chi phí nhỏ để tránh tràn số và giới hạn số học của bộ giải MILP.

Xem [bộ thử](../../tests/README.md) và [kết quả thực nghiệm](../../tests/results/).
