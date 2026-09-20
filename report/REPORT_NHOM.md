# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm L3B  
**Thành viên:** Trần Mạnh Hùng (chủ trì RecursiveChunker), cùng các thành viên Nhóm L3B  
**Ngày:** 20/09/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách đổi trả, hoàn tiền và phương thức vận chuyển trên sàn thương mại điện tử TikTok Shop Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
> Đây là chủ đề cốt lõi trong nghiệp vụ thương mại điện tử, có sự phân hóa rõ ràng về đối tượng (người mua và người bán) và chứa đựng các điều khoản, mốc thời gian chặt chẽ (1 ngày, 2 ngày, 3 ngày, 10 ngày, 14 ngày, 15 ngày). Việc xây dựng hệ thống RAG cho chủ đề này giúp kiểm chứng trực quan vai trò của việc phân tách tài liệu, đánh dấu siêu dữ liệu (`audience`) và hiệu quả của các chiến lược chia nhỏ (chunking).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Khi nào người mua có thể yêu cầu trả hàng hoàn tiền (`tiktok-buyer-return-refund.md`) | https://seller-vn.tiktok.com/university/essay?default_language=vi-VN&knowledge_id=2901402355762946 | 2026-09-20 / 2024-07-18 | 745 | `doc_id: tiktok-buyer-return-refund`, `audience: buyer`, `category: returns-refund`, `language: vi` |
| 2 | Phương thức trả hàng và hoàn tiền (`tiktok-return-methods.md`) | https://seller-vn.tiktok.com/university/essay?knowledge_id=1398156382422785&lang=vi-VN | 2026-09-20 / not-stated | 780 | `doc_id: tiktok-return-methods`, `audience: seller`, `category: return-method`, `language: vi` |
| 3 | Trả hàng và hoàn tiền dành cho người bán (`tiktok-seller-return-refund.md`) | https://seller-vn.tiktok.com/university/essay?course_type=1&from=search&identity=1&knowledge_id=1766935302801169&role=1 | 2026-09-20 / not-stated | 1,020 | `doc_id: tiktok-seller-return-refund`, `audience: seller`, `category: returns-refund`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `tiktok-buyer-return-refund` | Định danh tài liệu nguồn duy nhất, dùng để kiểm tra provenance và xóa tài liệu (`delete_document`). |
| `audience` | string | `buyer`, `seller` | **Cực kỳ quan trọng để lọc (filtering):** phân biệt quyền hạn và nghĩa vụ của Người mua và Người bán; tránh nhầm lẫn khi câu hỏi hỏi chung chung về "thời hạn trả hàng". |
| `category` | string | `returns-refund`, `return-method` | Phân loại mảng nội dung chính sách (điều kiện hoàn tiền vs quy trình vận chuyển giao nhận). |
| `retrieved_at` | string | `2026-09-20` | Giúp xác định độ mới và tính hiệu lực thời gian của chính sách. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính sách `tiktok-seller-return-refund.md` (chunk_size=200):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `tiktok-seller-return-refund.md` | FixedSizeChunker (`fixed_size`) | 6 | 185 ký tự | Kém. Cắt ngang các câu văn và tiêu đề mục, gây đứt mạch ngữ nghĩa. |
| `tiktok-seller-return-refund.md` | SentenceChunker (`by_sentences`) | 5 | 198 ký tự | Trung bình. Tách theo câu nhưng gom cả tiêu đề markdown vào câu tiếp theo. |
| `tiktok-seller-return-refund.md` | RecursiveChunker (`recursive`) | 4 | 240 ký tự | **Tốt nhất.** Tách tự nhiên ở ranh giới đoạn `\n\n`, giữ trọn vẹn mỗi mục quy định trong 1 chunk. |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Mạnh Hùng**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=300`) kết hợp `GeminiEmbedder` (`gemini-embedding-001`)
- **Mô tả & lý do chọn cho chủ đề này:** Sử dụng danh sách separator ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Chiến lược này cực kỳ thích hợp cho văn bản chính sách có cấu trúc tiêu đề Markdown, vì các mục quy định được chia tách tự nhiên theo khối đoạn văn và tiêu đề, đảm bảo không có chunk vụn và giữ trọn vẹn mối liên hệ giữa điều khoản và thời hạn xử lý.

**Thành viên 2 — Thành viên Nhóm L3B**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=250, overlap=50`)
- **Mô tả & lý do chọn:** Chiến lược cửa sổ trượt kích thước cố định. Đơn giản, đảm bảo độ dài đồng đều và hạn chế mất thông tin nhờ 50 ký tự gối đầu (overlap), nhưng ranh giới cắt đôi khi làm gãy ngang câu.

**Thành viên 3 — Thành viên Nhóm L3B**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=2`)
- **Mô tả & lý do chọn:** Nhóm các câu hoàn chỉnh thành chunk. Đảm bảo tính toàn vẹn cú pháp của câu, nhưng bỏ qua cấu trúc phân cấp tiêu đề Markdown.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Mạnh Hùng | RecursiveChunker + Gemini Embedder | **10 / 10** | Tôn trọng cấu trúc đoạn và đề mục Markdown; các chunk mang ngữ nghĩa trọn vẹn; điểm tương đồng ngữ nghĩa chính xác (vector 3072 chiều). | Cần điều chỉnh `chunk_size` phù hợp với độ dài trung bình của các section trong văn bản. |
| Thành viên 2 | FixedSizeChunker | 7 / 10 | Dễ triển khai, kiểm soát chặt chẽ giới hạn token; overlap giúp giữ được một phần ngữ cảnh. | Ranh giới cắt cơ học có thể chia đôi từ ngữ hoặc các con số điều khoản nhạy cảm. |
| Thành viên 3 | SentenceChunker | 8 / 10 | Câu văn nguyên vẹn, đọc tự nhiên. | Có thể gom tiêu đề `# Header` vào câu đầu tiên khiến embedding của tiêu đề bị pha loãng. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** kết hợp **`GeminiEmbedder`** là chiến lược tối ưu nhất cho bộ tài liệu chính sách này. Do tài liệu đã được chuẩn hóa theo các đề mục rõ ràng, việc ưu tiên ngắt ở ranh giới đoạn (`\n\n`) giúp mỗi chunk đại diện cho đúng một quy định hoàn chỉnh (ví dụ: một chunk về "Thời hạn gửi hàng trả", một chunk về "Kiểm tra hàng trả về"). Nhờ đó, vector embedding của chunk phản ánh tập trung chính xác chủ đề, giúp câu trả lời của RAG Agent không bị nhiễu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có thể yêu cầu trả hàng hoặc hoàn tiền trong những trường hợp nào? | Khi không nhận được sản phẩm; sản phẩm không tuân thủ hợp đồng mua bán; giao sai sản phẩm; thiếu hàng, bị lỗi hoặc không thể chấp nhận; sản phẩm khác mô tả; hoặc người bán không đáp ứng cam kết giao hàng. | `tiktok-buyer-return-refund#2` (Mục Các trường hợp được yêu cầu) |
| 2 | Thời hạn tối đa để người mua gửi yêu cầu trả hàng hoàn tiền là bao lâu? | Trong vòng 15 ngày dương lịch sau khi trạng thái đơn hàng được cập nhật thành “Đã giao hàng” (có ngoại lệ cho Thực phẩm & Đồ uống, Sữa công thức & Thực phẩm cho trẻ, Điện thoại & Máy tính bảng). | `tiktok-buyer-return-refund#1` (Mục Thời hạn gửi yêu cầu) |
| 3 | Người bán có bao nhiêu ngày để xem xét và phản hồi yêu cầu trả hàng hoàn tiền của khách? | Người bán phải xem xét yêu cầu trong vòng 1 ngày dương lịch (hoặc 1 ngày làm việc) kể từ khi nhận yêu cầu; nếu không, yêu cầu sẽ được tự động phê duyệt. | `tiktok-seller-return-refund#0` (Mục Xem xét yêu cầu) |
| 4 | Nếu nhân viên vận chuyển giao gói hàng trả lại cho người bán thất bại 3 lần thì xử lý như thế nào và ai chịu phí? | Nếu người bán không nhận gói trả lại sau 3 lần giao, đơn vị vận chuyển ngừng liên lạc và tiêu hủy gói sau 7 ngày tính từ lần giao đầu tiên. Nếu lỗi thuộc người bán, người bán chịu phí vận chuyển trả hàng. | `tiktok-return-methods#3` (Mục Trách nhiệm người bán và phí) |
| 5 | Người bán có bao nhiêu ngày để kiểm tra và từ chối hàng trả về đối với phương thức tự sắp xếp vận chuyển? | Với trả hàng tự sắp xếp, hạn là 14 ngày sau khi khách tải thông tin vận chuyển hoặc 2 ngày sau khi hàng được giao, tùy thời điểm nào đến trước; quá hạn thì yêu cầu tự động được chấp thuận. | `tiktok-seller-return-refund#2` (Mục Kiểm tra hàng trả về) |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Người mua có thể yêu cầu trả hàng trong trường hợp nào? | RecursiveChunker + Gemini Embedder | Có (Top-1: Score 0.8551) | Trả về trọn vẹn danh sách 6 trường hợp vi phạm hợp đồng/giao hàng. |
| 2 | Thời hạn tối đa để người mua gửi yêu cầu trả hàng? | RecursiveChunker (với filter `audience=buyer`) | Có (Top-1: Score 0.8447) | Cần tiền lọc `audience` để loại bỏ tài liệu quy định cho Người bán. |
| 3 | Người bán có bao nhiêu ngày để xem xét yêu cầu? | RecursiveChunker + Gemini Embedder | Có (Top-1: Score 0.8670) | Nêu rõ thời hạn 1 ngày và hệ quả tự động phê duyệt nếu bỏ quên. |
| 4 | Giao gói hàng thất bại 3 lần thì xử lý thế nào? | RecursiveChunker + Gemini Embedder | Có (Top-1: Score 0.8479) | Chứa đầy đủ thông tin: 3 lần giao, ngừng liên lạc, tiêu hủy sau 7 ngày, quy định chịu phí ship. |
| 5 | Thời hạn kiểm tra hàng trả về đối với tự sắp xếp? | RecursiveChunker + Gemini Embedder | Có (Top-1: Score 0.8271) | Thể hiện chính xác 2 mốc song song: 14 ngày kể từ khi tải mã hoặc 2 ngày sau khi giao. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất có ích, thể hiện rõ nhất qua kết quả A/B Test ở Câu hỏi 2:**
> Cả tài liệu của Người mua (`tiktok-buyer-return-refund.md`) và tài liệu của Người bán (`tiktok-seller-return-refund.md`) đều nhắc đến cụm từ khóa *"yêu cầu trả hàng hoàn tiền"* và mốc *"15 ngày"*.
> - **Khi KHÔNG dùng filter:** Tài liệu người bán (`tiktok-seller-return-refund#0`) đạt điểm tương đồng **0.8680**, chiếm vị trí Top-1, đẩy tài liệu chuẩn của người mua xuống Top-2 (score **0.8447**).
> - **Khi CÓ filter `{"audience": "buyer"}`:** Hệ thống lập tức loại bỏ tài liệu người bán và trả về tài liệu người mua ở Top-1 (score **0.8447**).
> Điều này khẳng định tiền lọc bằng metadata là yếu tố bắt buộc để đảm bảo độ chính xác trong các bài toán RAG nhiều vai trò.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Sự kết hợp giữa Clean Data và RecursiveChunker:** Làm sạch rác của scraper (menu, navbar, button footer) và giữ đúng định dạng tiêu đề Markdown `#` giúp `RecursiveChunker` tự động chia tài liệu thành các block tri thức chuẩn mực mà không cần viết custom parser phức tạp.
2. **Metadata Pre-filtering là yếu tố sống còn cho các domain có nhiều vai trò (buyer vs seller):** Thử nghiệm A/B trên Gemini Embedding chứng minh nếu không lọc trước, tài liệu sai vai trò có điểm tương đồng cao hơn (0.8680 vs 0.8447) sẽ chiếm dụng vị trí Top-1.
3. **Traceability trong RAG:** Khi mỗi chunk được gắn định danh nguồn (`doc_id`, tiêu đề), Agent có thể viện dẫn chính xác số thứ tự `[1]`, `[2]` để người dùng kiểm chứng lại với văn bản gốc.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ dữ liệu, nhưng `FixedSizeChunker` gặp hiện tượng "cắt đứt mạch câu" khiến điểm tương đồng bị tụt giảm khi câu hỏi rơi vào vị trí bị chia đôi; `SentenceChunker` bảo toàn được câu nhưng làm mất ngữ cảnh phân cấp của tiêu đề mục; trong khi `RecursiveChunker` tạo ra các chunk cân đối nhất cả về độ dài lẫn độ hoàn chỉnh ngữ nghĩa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm trường `product_type` vào metadata (ví dụ: `general`, `perishable_food`, `electronics`) để có thể lọc sâu hơn cho các trường hợp ngoại lệ (như danh mục thực phẩm hay điện thoại chỉ áp dụng thời hạn ngắn hơn hoặc không thể trả hàng).

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
