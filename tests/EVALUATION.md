# Đánh giá mô hình MILP và thuật toán ALNS

Lần chạy ban đầu ngày 22/11/2026 (2 giây mỗi pha) sử dụng 15 instance, gồm 6 test mẫu/biên và 9 test ngẫu nhiên (N=8,20,60; mỗi nhóm 3 seed). Mỗi instance chạy MILP một lần, greedy một lần và ALNS ba lần: tổng cộng 75 lượt. Có 72 lượt xuất nghiệm, tất cả qua kiểm tra độc lập; 3 lượt MILP dừng vì chưa chứng minh tối ưu trong ngân sách. Xem [bảng kết quả 2 giây](./results_2s/report.md), [CSV chi tiết 2 giây](./results_2s/benchmark.csv) và [cấu hình 2 giây](./results_2s/metadata.json). Kết quả chạy lại với 10 giây mỗi pha nằm trong [bảng hiện tại](./results/report.md); đối chiếu các ngân sách tại [đánh giá tăng thời gian](./TIME_LIMIT_EVALUATION.md).

## MILP: đúng mô hình, có chứng minh nhưng tăng độ khó nhanh

SCIP chứng minh tối ưu từ điển được 12/15 instance với giới hạn 2 giây mỗi pha. Mẫu đạt `(R,T,C)=(5,235,145)`. Các ca chu trình, thiếu đội, không chồng lấn, ưu tiên thời gian và hòa thời gian để chọn chi phí đều cho kết quả đúng với giá trị đã biết.

Ba instance N=20 được giải tối ưu, tổng thời gian subprocess khoảng 1.05–1.50 giây. Cả ba instance N=60 đều chưa chứng minh tối ưu, tổng thời gian khoảng 2.53–2.95 giây. Đây là kết quả với ngân sách thử ngắn, không phải khẳng định SCIP không thể giải chúng nếu tăng thời gian. Mã hiện tại không xuất incumbent khi có pha chưa được chứng minh tối ưu, nên bảng không có nghiệm MILP để đối chiếu trực tiếp trên các ca này.

Điểm yếu cấu trúc là số biến thứ tự tăng theo tổng số cặp công việc có thể giao cho cùng đội. Dữ liệu nhiều đội hợp lệ hoặc nhiều công việc sẽ làm mô hình lớn. Chưa thử N=1000 hay K ở giới hạn đề, nên chưa có bằng chứng về khả năng mở rộng đến kích thước đó.

## ALNS: nghiệm nhanh, chất lượng phụ thuộc kích thước và seed

ALNS xác định chính xác tập công việc tối đa bằng xử lý đồ thị trước khi tìm kiếm. Với 2000 vòng lặp, cả ba seed đều khớp đủ ba mục tiêu tối ưu trên 6 ca mẫu/biên và 3 ca N=8. Tổng cộng ALNS khớp tối ưu trên 9 trong 12 instance có chứng minh của MILP.

Ở N=20, nghiệm tốt nhất trong ba seed có kết quả:

| Instance | T tối ưu | T ALNS | Khoảng cách T | Chi phí ALNS / tối ưu khi T bằng nhau |
| --- | ---: | ---: | ---: | --- |
| medium_0 | 81 | 85 | 4.94% | Không so khoảng cách chi phí vì T khác nhau |
| medium_1 | 81 | 84 | 3.70% | Không so khoảng cách chi phí vì T khác nhau |
| medium_2 | 103 | 103 | 0% | 980 / 925, cao hơn 5.95% |

Khoảng cách makespan được tính `(T_ALNS - T_opt) / T_opt`. Chi phí thấp hơn khi makespan cao hơn không làm nghiệm tốt hơn theo mục tiêu từ điển; chẳng hạn medium_0 có chi phí ALNS 895 nhỏ hơn 1035 nhưng vẫn kém nghiệm MILP do kết thúc muộn hơn.

Ở N=60 chưa biết giá trị tối ưu, chỉ so sánh với baseline greedy dùng cùng bộ giải mã nhưng không tìm kiếm:

| Instance | T greedy | T ALNS tốt nhất | Giảm T so với greedy | T qua ba seed |
| --- | ---: | ---: | ---: | --- |
| large_0 | 154 | 135 | 12.34% | 135–144 |
| large_1 | 169 | 133 | 21.30% | 133–143 |
| large_2 | 159 | 130 | 18.24% | 130–141 |

Mỗi lượt ALNS N=60 mất khoảng 0.016–0.018 giây trong môi trường thử. Đây là thời gian subprocess rất ngắn, có nhiễu đo; không nên suy ra hệ số tăng tốc cố định so với MILP. Ngân sách ALNS là số vòng lặp trong khi MILP là thời gian mỗi pha, và chi phí khởi động C++/Python khác nhau.

## Diễn giải và hướng cải tiến

MILP phù hợp làm mô hình tham chiếu và cung cấp nghiệm tối ưu cho các ca nhỏ/vừa. ALNS hiện tại cho nghiệm khả thi nhanh và cải thiện rõ so với greedy trên bộ dữ liệu ngẫu nhiên, nhưng chưa đạt tối ưu trên các ca N=20 và chưa có bảo đảm cho hai tiêu chí cuối.

Có thể khai thác tính chất tập công việc tối đa để cố định các biến chọn trong MILP, bỏ pha tối đa số lượng và loại trước công việc không thể thực hiện. Đây là cải tiến được đề xuất, chưa áp dụng vào mô hình MILP hiện tại để kết quả ở bảng phản ánh đúng phiên bản đã chạy.

Với ALNS, các bước tiếp theo đáng thử là chèn vào khoảng trống của lịch đội, regret-k repair, phá hủy theo đường găng và tăng ngân sách tìm kiếm. Để đánh giá riêng giá trị của cơ chế thích nghi, cần thêm ablation giữ trọng số cố định; so sánh hiện tại chỉ cho thấy hiệu quả tổng thể so với greedy, chưa tách được đóng góp của từng thành phần ALNS.

Trước khi dùng cho dữ liệu lớn, cần mở rộng số seed/instance, thêm đồ thị có mật độ khác nhau, thay đổi mức khan hiếm đội, và đo dưới ngân sách wall-clock bằng nhau. Các kết luận trên chỉ áp dụng cho bộ thử đã công bố, không đại diện cho mọi instance của bài toán.
