# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Mạnh Hùng  
**MSSV:** 2A202602708  
**Nhóm:** Nhóm L3B  
**Ngày:** 20/09/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) nghĩa là hai vector embedding tạo với nhau một góc rất nhỏ trong không gian vector đa chiều, thể hiện hai đoạn văn bản có sự tương đồng rất lớn về mặt ý nghĩa ngữ nghĩa (semantic similarity), bất kể độ dài hay từ vựng bề mặt có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng muốn đổi áo vì kích cỡ bị chật."
- Câu B: "Người mua gửi yêu cầu trả hàng do chọn nhầm size sản phẩm."
- Tại sao tương đồng: Hai câu sử dụng từ ngữ hoàn toàn khác nhau ("đổi" vs "trả hàng", "kích cỡ bị chật" vs "nhầm size") nhưng cùng diễn đạt chung một bản chất ngữ nghĩa là yêu cầu đổi trả sản phẩm do vấn đề kích cỡ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng hóa trên sàn áp dụng trong 15 ngày."
- Câu B: "Thời tiết hôm nay ở Hà Nội có mưa rào và dông rải rác."
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn không liên quan (chính sách thương mại điện tử và dự báo thời tiết), vector embedding chỉ về hai hướng khác nhau trong không gian ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid phụ thuộc trực tiếp vào độ dài (độ lớn magnitude) của vector, khiến một đoạn văn ngắn và một đoạn văn dài dù cùng nghĩa vẫn bị tính khoảng cách rất xa nhau. Cosine similarity chuẩn hóa độ dài và chỉ đo góc định hướng giữa hai vector, giúp phản ánh thuần túy mức độ tương đồng ngữ nghĩa mà không bị sai lệch bởi độ dài câu chữ.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước nhảy sau mỗi chunk: `step = chunk_size - overlap = 500 - 50 = 450` ký tự.
> - Công thức số lượng chunk: `ceil((độ_dài - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / 450) = ceil(9950 / 450) = ceil(22.111...) = 23`.
> - Xác minh theo cửa sổ trượt: Chunk 0 bắt đầu từ 0, Chunk 1 từ 450, ..., Chunk 22 từ `22 * 450 = 9900` (kéo dài đến hết ký tự 10000).
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, bước nhảy giảm xuống `500 - 100 = 400`, số chunk tăng lên `ceil((10000 - 100) / 400) = ceil(9900 / 400) = 25 chunks` (tăng thêm 2 chunks). Người ta muốn tăng overlap khi văn bản chứa nhiều điều khoản logic, thực thể hoặc câu phức để tránh tình trạng ranh giới cắt chia đôi một mệnh đề quan trọng, giúp bảo toàn mạch ngữ cảnh liền mạch giữa các chunk phục vụ retrieval.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`FixedSizeChunker.chunk`** — hướng tiếp cận:
> Dùng vòng lặp cửa sổ trượt với bước nhảy `step = chunk_size - overlap`. Tại mỗi vị trí `start`, cắt chuỗi `text[start : start + chunk_size]` và append vào danh sách. Vòng lặp dừng sớm khi `start + chunk_size >= len(text)` để tránh tạo thêm chunk rỗng ở cuối. Nếu văn bản ngắn hơn `chunk_size`, trả về `[text]` ngay lập tức.

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `re.split(r"(?<=[.!?])(?:\s+|\n+)", text)` để tách văn bản ngay sau các dấu chấm, chấm than, chấm hỏi mà không làm mất dấu câu ở cuối câu. Gom các câu hợp lệ thành từng nhóm `max_sentences_per_chunk` câu và loại bỏ các khoảng trắng thừa. Xử lý ngoại lệ chuỗi rỗng bằng cách trả về danh sách rỗng `[]`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng danh sách phân tách theo thứ tự ưu tiên giảm dần `["\n\n", "\n", ". ", " ", ""]` để ưu tiên giữ nguyên cấu trúc đoạn văn, tiêu đề rồi mới đến câu và từ. Base case là khi chuỗi đã nhỏ hơn hoặc bằng `chunk_size` hoặc danh sách separator đã hết (cắt cứng theo `chunk_size`). Sau khi tách đệ quy, thuật toán thực hiện bước gom (merge) các mảnh nhỏ liền kề cho tới sát `chunk_size` để tránh tạo ra các chunk vụn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory dưới dạng danh sách các `dict` đã chuẩn hóa, mỗi bản ghi gồm `id`, `doc_id`, `content`, `metadata` và `embedding`. Do vector embedding đã được chuẩn hóa độ dài đơn vị (`||v|| = 1`), hàm tìm kiếm chỉ cần tính tích vô hướng (dot product) giữa vector truy vấn và từng vector tài liệu để ra đúng điểm cosine similarity, sau đó sắp xếp giảm dần và lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện tiền lọc (pre-filtering): lọc các bản ghi thỏa mãn toàn bộ cặp khóa-giá trị trong `metadata_filter` trước khi tính điểm tương đồng, đảm bảo không bị mất các vị trí trong top-k. `delete_document` xóa tất cả bản ghi có `doc_id` hoặc `metadata['doc_id']` khớp với ID được yêu cầu và trả về `True` nếu số lượng phần tử bị giảm đi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Truy xuất top-k chunk liên quan nhất từ `EmbeddingStore`, sau đó định dạng các chunk thành một khối ngữ cảnh có đánh số thứ tự `[1]`, `[2]`,... kèm tiêu đề nguồn văn bản. Tạo prompt chỉ dẫn LLM chỉ trả lời dựa trên ngữ cảnh được cung cấp và bắt buộc trích dẫn nguồn số thứ tự tương ứng, giúp câu trả lời minh bạch và truy vết được (traceable). Nếu store không có tài liệu, agent trả về thông báo không tìm thấy.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
==================== test session starts =====================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- V:\K4-DAY07-TranManhHung-2A202602708\.venv\Scripts\python.exe  
cachedir: .pytest_cache
rootdir: V:\K4-DAY07-TranManhHung-2A202602708
plugins: anyio-4.15.1
collected 42 items                                            

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list
 PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list
 PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

===================== 42 passed in 0.36s =====================
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua yêu cầu trả hàng do nhận sai sản phẩm. | Khách khiếu nại vì shop gửi nhầm hàng đã đặt. | cao | 0.8842 | Đúng |
| 2 | Thời hạn người mua gửi yêu cầu hoàn tiền là 15 ngày. | Khách hàng có hai tuần để gửi trả bưu kiện. | cao | 0.8125 | Đúng |
| 3 | Người bán chịu toàn bộ chi phí vận chuyển hoàn trả. | Tiền ship gửi trả hàng do người bán thanh toán. | cao | 0.8530 | Đúng |
| 4 | Kiểm tra hàng trả về tại bưu cục hoặc lấy tại nhà. | Công thức nướng bánh bông lan trứng muối thơm ngon. | thấp | 0.0412 | Đúng |
| 5 | Quy định tự động phê duyệt yêu cầu sau 1 ngày. | Huấn luyện mô hình mạng nơ-ron học sâu với PyTorch. | thấp | -0.0150 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là ở Cặp 1 và Cặp 3: dù hai câu hoàn toàn không dùng chung từ vựng trọng tâm ("người mua" vs "khách", "nhầm hàng" vs "sai sản phẩm", "phí vận chuyển" vs "tiền ship"), điểm tương đồng cosine vẫn đạt trên 0.85. Điều này chứng minh embedding model thực sự biểu diễn ngữ nghĩa trừu tượng (semantic space) chứ không đơn thuần chỉ là đếm tần suất từ khóa trùng lặp như các phương pháp lexical search cổ điển (BM25/TF-IDF).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **Cấu hình:** Sử dụng chiến lược **`RecursiveChunker`** (với `chunk_size=300`) thực hiện chia nhỏ trên đúng **3 tài liệu TikTok Shop**:
> 1. `tiktok-buyer-return-refund.md` (audience: buyer)
> 2. `tiktok-return-methods.md` (audience: seller)
> 3. `tiktok-seller-return-refund.md` (audience: seller)
>
> Tổng số chunks tạo thành: **13 chunks** | Backend embedding: **gemini-embedding-001**

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền sau khi nhận hàng? *(Filter: audience=buyer)* | `tiktok-buyer-return-refund#1`: Người mua có thể gửi yêu cầu trong vòng **15 ngày dương lịch** sau khi trạng thái đơn cập nhật "Đã giao hàng". | 0.8451 | Có (Chính xác) | Người mua có **15 ngày dương lịch** sau khi đơn cập nhật "Đã giao hàng" để gửi yêu cầu trả hàng hoặc hoàn tiền. |
| 2 | Người bán có bao nhiêu ngày để xem xét và phản hồi yêu cầu trả hàng hoàn tiền của khách? *(Filter: audience=seller)* | `tiktok-seller-return-refund#0`: # Xem xét yêu cầu — Người bán phải xem xét trong vòng **1 ngày dương lịch** kể từ khi nhận yêu cầu; nếu quá hạn sẽ tự động phê duyệt. | 0.8670 | Có (Chính xác) | Người bán có **1 ngày dương lịch** để xem xét; quá hạn hệ thống tự động phê duyệt yêu cầu cho người mua. |
| 3 | Có những phương thức trả lại gói hàng nào cho người mua trên TikTok Shop? | `tiktok-return-methods#3`: Người bán phải quản lý mọi tùy chọn trả hàng khách đã chọn. Nếu không nhận sau 3 lần giao, đơn vị vận chuyển tiêu hủy gói sau 7 ngày. | 0.7394 | Có (Liên quan) | Có 3 phương thức: Gửi tại điểm bưu cục, Lấy hàng tại nhà và Tự sắp xếp vận chuyển. |
| 4 | Nếu người bán không chấp nhận nhận lại kiện hàng hoàn trả sau 3 lần giao thì xử lý ra sao? | `tiktok-return-methods#3`: Người bán không nhận gói sau 3 lần giao → đơn vị vận chuyển **ngừng liên lạc** và **tiêu hủy gói sau 7 ngày** kể từ lần giao đầu. | 0.8311 | Có (Hoàn hảo) | Nếu giao thất bại 3 lần, đơn vị vận chuyển ngừng liên lạc và tiêu hủy gói sau 7 ngày; người bán chịu phí nếu lỗi thuộc trách nhiệm người bán. |
| 5 | Sau khi nhận sản phẩm hoàn trả tại bưu cục hoặc tại nhà, người bán có mấy ngày để kiểm tra và từ chối? *(Filter: audience=seller)* | `tiktok-seller-return-refund#2`: Người bán có **2 ngày dương lịch** sau khi nhận sản phẩm để từ chối nếu tình trạng không đạt yêu cầu; quá hạn tự động chấp thuận. | 0.8830 | Có (Chính xác) | Thời hạn là **2 ngày dương lịch** sau khi nhận hàng để từ chối; quá hạn hệ thống tự động chấp thuận hoàn trả. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua so sánh, tôi nhận thấy `RecursiveChunker` phát huy tối đa sức mạnh khi kết hợp với cấu trúc Markdown có sẵn tiêu đề (`#`, `##`). Nhờ ưu tiên cắt ở dấu `\n\n`, các đề mục quy định không bị băm nhỏ vụn mà được giữ trọn vẹn thành từng đơn vị kiến thức độc lập (self-contained chunk), giúp việc truy xuất vừa đạt điểm liên quan cao vừa cung cấp đầy đủ ngữ cảnh để LLM trích xuất câu trả lời chính xác.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
