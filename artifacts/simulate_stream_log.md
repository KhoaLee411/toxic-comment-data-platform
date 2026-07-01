# Giả Lập Luồng Stream và Kafka CDC

Trong luồng xử lý thời gian thực (Stream Processing), chúng ta cần một công cụ giả lập các bình luận độc hại đổ về hệ thống liên tục. Kịch bản dưới đây minh họa việc chạy giả lập và xác nhận dữ liệu đã được Debezium bắt (CDC) và đẩy thành công vào Kafka.

## 1. Chạy Script Giả Lập (Simulate Stream)

Tốc độ insert (thời gian nghỉ) được tạm thời tinh chỉnh xuống `0.1s` (thay vì 2s) để nhanh chóng bơm dữ liệu thử nghiệm vào hệ thống.

**Lệnh thực thi:**
```bash
python utils/simulate_stream.py
```

**Output Log (Trích xuất):**
```text
2026-07-02 00:28:16.962 | INFO     | __main__:main:61 - Inserted row 26: {'comment_text': '"\n\nEXCUSE ME PLEASE TAKE A MOMENT AND READ SOME INFO ABOUT ME BELOW...', 'labels': 0}
2026-07-02 00:28:17.064 | INFO     | __main__:main:61 - Inserted row 27: {'comment_text': 'I did not forge anyoones signature. I copied and pasted something from his archives...', 'labels': 0}
...
2026-07-02 00:28:23.721 | INFO     | __main__:main:61 - Inserted row 92: {'comment_text': 'dont mind this weapon giy he shall not be here mooch longer he is a jew hater...', 'labels': 1}
2026-07-02 00:28:23.824 | INFO     | __main__:main:61 - Inserted row 93: {'comment_text': 'Yep, as I said, Bite me, Hitler, err... Scrapiron. Disappear it to make you look...', 'labels': 1}
```
*(Script đã thực hiện insert liên tục các dòng comment (kể cả có chứa nội dung độc hại - label 1) trực tiếp vào bảng `stream.raw_comments` của PostgreSQL)*

## 2. Kiểm Tra Lượng Tin Nhắn (Messages) Trên Kafka Topic

Sau khoảng 10 giây giả lập, chúng ta dừng script lại và kiểm tra trực tiếp bên trong Kafka Broker xem Debezium đã kịp bắt các sự kiện INSERT đó và đẩy vào Kafka chưa.

**Lệnh kiểm tra Offset (Số lượng tin nhắn) trên Topic Kafka:**
```bash
docker exec stream-broker kafka-run-class kafka.tools.GetOffsetShell \
  --bootstrap-server localhost:9092 \
  --topic toxic_comments.stream.raw_comments
```

**Output thu được:**
```text
toxic_comments.stream.raw_comments:0:94
```

👉 **Kết luận:** 
- Con số `94` ở đuôi đại diện cho **số lượng message/sự kiện đã đổ vào Kafka** ở phân vùng số 0 (partition 0).
- Nó khớp hoàn toàn với số lượng record mà script Python vừa chèn (row 0 đến 93).
- Điều này chứng minh Debezium hoạt động hoàn hảo: Khi Postgres có data mới, gần như ngay tức khắc data đó được đóng gói thành message và tồn tại an toàn trong hệ sinh thái Kafka, sẵn sàng cho các luồng xử lý Spark Streaming phía sau.
