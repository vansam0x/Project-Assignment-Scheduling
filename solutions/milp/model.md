# Phát biểu mô hình MILP


Đơn hình (simplex) giải bài toán quy hoạch tuyến tính với biến liên tục. Bài toán này cần quyết định rời rạc về việc chọn công việc, chọn đội và thứ tự làm việc, nên không thể dùng đơn hình thuần túy để bảo đảm nghiệm hợp lệ. Ta phát biểu MILP; OR-Tools gọi SCIP để giải bài toán nguyên. Nới các biến nhị phân về đoạn `[0,1]` chỉ cho bài toán LP nới lỏng, có thể cho phân công phân số.

### Quy ước của mô hình

- Mỗi đội chỉ thực hiện tối đa một công việc tại một thời điểm; công việc không bị ngắt giữa chừng.
- Chọn một công việc thì phải chọn tất cả tiền nhiệm của nó. Công việc kế tiếp có thể bắt đầu ngay lúc tiền nhiệm kết thúc.
- Thời gian bắt đầu là số nguyên không âm. Các thời điểm sẵn sàng dương bảo đảm công việc được chọn bắt đầu tại thời điểm dương.
- Mã nguồn đọc chi phí nguyên, có thể âm. Nếu dữ liệu có chi phí thập phân hữu hạn, cần đổi sang đơn vị nguyên trước khi chạy. Nếu lặp một cặp công việc–đội, giữ chi phí nhỏ nhất.
- Khi không chọn được công việc nào, xuất `0` và quy ước makespan bằng `0`, mở rộng quy định “R nguyên dương” để biểu diễn trường hợp này.

Hai quy ước đầu là cách diễn giải được dùng cho lời giải này; đề gốc chưa khẳng định rõ chúng.

### Tập hợp, hằng số và biến

Gọi `A` là tập các cặp phân công hợp lệ, `E` là tập quan hệ trước–sau. Đặt:

\[
H=\max_j s_j+\sum_i d_i,\qquad B=H+\max_i d_i.
\]

`H` là cận trên đủ lớn: mọi tập công việc khả thi có thể được thực hiện nối tiếp theo thứ tự topo sau khi tất cả đội sẵn sàng. Vì thời lượng dương, các công việc nằm trong chu trình trước–sau không thể được chọn.

| Biến | Miền | Ý nghĩa |
| --- | --- | --- |
| \(y_i\) | \(\{0,1\}\) | Có chọn công việc i hay không |
| \(x_{ij}\), \((i,j)\in A\) | \(\{0,1\}\) | Giao công việc i cho đội j |
| \(u_i\) | \(\mathbb Z_{\ge0}\) | Thời điểm bắt đầu; bằng 0 khi không chọn |
| \(T\) | \(\mathbb Z\cap[0,H]\) | Thời điểm hoàn thành toàn bộ lịch |
| \(z_{abj}\), \(a<b\), \((a,j),(b,j)\in A\) | \(\{0,1\}\) | Nếu cả hai giao cho j, giá trị 1 nghĩa là a làm trước b |

### Các ràng buộc tuyến tính

Mỗi công việc được chọn có đúng một đội hợp lệ:

\[
\sum_{j:(i,j)\in A}x_{ij}=y_i\quad\forall i.
\]

Nếu không có đội hợp lệ, tổng rỗng bằng 0, buộc công việc không được chọn.

Giới hạn thời gian và thời điểm đội sẵn sàng:

\[
0\le u_i\le(H-d_i)y_i,\qquad
u_i\ge s_j-H(1-x_{ij})\quad\forall(i,j)\in A.
\]

Quan hệ trước–sau và điều kiện chọn tiền nhiệm:

\[
y_b\le y_a,\qquad
u_b\ge u_a+d_a-B(1-y_b)\quad\forall(a,b)\in E.
\]

Với mỗi đội j và cặp công việc a < b mà đội có thể thực hiện, đặt \(L_{abj}=2-x_{aj}-x_{bj}\). Không cho hai công việc chồng lấn:

\[
u_a+d_a\le u_b+B(1-z_{abj}+L_{abj}),
\]
\[
u_b+d_b\le u_a+B(z_{abj}+L_{abj}).
\]

Khi cả hai công việc giao cho j, `L=0` và một trong hai thứ tự phải được thỏa mãn. Nếu một công việc không giao cho j, cả hai bất đẳng thức được vô hiệu hóa bởi cận B.

Makespan:

\[
T\ge u_i+d_i y_i\quad\forall i,\qquad 0\le T\le H.
\]

### Ba lần giải theo thứ tự ưu tiên

1. Tối đa \(R=\sum_i y_i\), thu được \(R^*\).
2. Thêm \(\sum_i y_i=R^*\), tối thiểu \(T\), thu được \(T^*\).
3. Giữ hai giá trị trên, tối thiểu \(C=\sum_{(i,j)\in A}c_{ij}x_{ij}\).

Cách này bảo đảm ưu tiên từ điển, không cần chọn trọng số rất lớn cho hàm mục tiêu. Chỉ chuyển sang bước tiếp theo khi SCIP trả về `OPTIMAL`; giới hạn thời gian có thể khiến chương trình dừng với thông báo chưa chứng minh được tối ưu. SCIP sử dụng tính toán dấu phẩy động và dung sai số; dữ liệu chi phí cực lớn cần được đổi đơn vị phù hợp.
