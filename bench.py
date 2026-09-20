from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Hỗ trợ hiển thị ký tự tiếng Việt trên môi trường Windows PowerShell
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

load_dotenv()

from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.models import Document
from src.store import EmbeddingStore

# Chọn backend mô hình nhúng (GeminiEmbedder / LocalEmbedder / MockEmbedder)
provider = os.getenv("EMBEDDING_PROVIDER", "mock")
if provider == "gemini":
    from src import GeminiEmbedder
    embedding_fn = GeminiEmbedder()
    print(f"Chay benchmark voi GeminiEmbedder ({embedding_fn._backend_name})...")
elif provider == "local":
    from src import LocalEmbedder
    embedding_fn = LocalEmbedder()
    print(f"Chay benchmark voi LocalEmbedder ({embedding_fn._backend_name})...")
else:
    from src import _mock_embed
    embedding_fn = _mock_embed
    print("Chay benchmark voi MockEmbedder...")

# Danh sách 3 file chính sách được chọn
TARGET_FILES = [
    Path("data/chinh_sach_doi_tra/tiktok-buyer-return-refund.md"),
    Path("data/chinh_sach_doi_tra/tiktok-return-methods.md"),
    Path("data/chinh_sach_doi_tra/tiktok-seller-return-refund.md"),
]

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Tách YAML frontmatter và nội dung thân văn bản."""
    parts = content.split("---")
    if len(parts) >= 3:
        fm_raw = parts[1]
        body = "---".join(parts[2:]).strip()
        metadata = {}
        for line in fm_raw.strip().split("\n"):
            line = line.strip()
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip().strip('"\'')
        return metadata, body
    return {}, content.strip()

def build_store(chunker: RecursiveChunker) -> tuple[EmbeddingStore, list[Document]]:
    store = EmbeddingStore(collection_name="tiktok_policy", embedding_fn=embedding_fn)
    all_docs = []

    for path in TARGET_FILES:
        if not path.exists():
            print(f"Cảnh báo: Không tìm thấy file {path}")
            continue

        # 1. Đọc file .md và tách frontmatter
        raw_text = path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(raw_text)
        doc_id = metadata.get("doc_id", path.stem)

        # 2. Chunk phần thân bằng RecursiveChunker
        chunks = chunker.chunk(body)
        for i, chunk in enumerate(chunks):
            doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk,
                metadata={
                    **metadata,
                    "doc_id": doc_id,
                    "chunk_index": i,
                },
            )
            all_docs.append(doc)

    # 3. Nạp tất cả Document vào EmbeddingStore
    store.add_documents(all_docs)
    return store, all_docs


def mock_llm(prompt: str) -> str:
    """Mô phỏng LLM phản hồi dựa trên ngữ cảnh được trích xuất."""
    match = re.search(r"--- NGỮ CẢNH ---\n(.*?)\n-----------------", prompt, re.DOTALL)
    if not match:
        return "Không có ngữ cảnh để trả lời."
    context = match.group(1).strip()
    return f"Theo thông tin trong tài liệu chính sách: {context[:250]}..."

def run_benchmark():
    chunker = RecursiveChunker(chunk_size=300)
    store, all_docs = build_store(chunker)

    output_lines = []
    header = f"=== BENCHMARK RETRIEVAL K4-L3B (Backend: {embedding_fn._backend_name}) ==="
    output_lines.append(header)
    output_lines.append(f"Số file nạp: {len(TARGET_FILES)}")
    output_lines.append(f"Tổng số chunks tạo thành: {len(all_docs)} (tổng trong store: {store.get_collection_size()})")
    output_lines.append("-" * 60)

    for doc in all_docs:
        output_lines.append(f"  [Chunk {doc.id}] (len: {len(doc.content)} ký tự): {doc.content[:80]}...")
    output_lines.append("=" * 60)

    # 5 câu hỏi benchmark đánh giá
    queries = [
    {
        "id": 1,
        "query": "Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng hoàn tiền sau khi nhận hàng?",
        "gold_answer": "Người mua có thể gửi yêu cầu trong vòng 15 ngày dương lịch sau khi trạng thái đơn hàng cập nhật thành 'Đã giao hàng'.",
        "expected_doc_id": "tiktok-buyer-return-refund",
        "filter": {"audience": "buyer"},
    },
    {
        "id": 2,
        "query": "Người bán có bao nhiêu ngày để xem xét và phản hồi yêu cầu trả hàng hoàn tiền của khách?",
        "gold_answer": "Người bán phải xem xét và xử lý trong vòng 1 ngày (1 ngày làm việc/dương lịch) kể từ khi nhận yêu cầu, nếu không sẽ được tự động phê duyệt.",
        "expected_doc_id": "tiktok-seller-return-refund",
        "filter": {"audience": "seller"},
    },
    {
        "id": 3,
        "query": "Có những phương thức trả lại gói hàng nào cho người mua trên TikTok Shop?",
        "gold_answer": "Có 3 phương thức: Gửi trả tại bưu cục, Lấy hàng tại nhà, và Tự gửi hàng.",
        "expected_doc_id": "tiktok-return-methods",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Nếu người bán không chấp nhận nhận lại kiện hàng hoàn trả sau 3 lần giao thì xử lý ra sao?",
        "gold_answer": "Đơn vị vận chuyển sẽ ngừng liên lạc với người bán và gói hàng sẽ bị tiêu hủy sau 7 ngày kể từ lần giao đầu tiên.",
        "expected_doc_id": "tiktok-return-methods",
        "filter": None,
    },
    {
        "id": 5,
        "query": "Sau khi nhận sản phẩm hoàn trả tại bưu cục hoặc tại nhà, người bán có mấy ngày để kiểm tra và từ chối?",
        "gold_answer": "Người bán có 2 ngày dương lịch sau khi nhận sản phẩm để từ chối nếu không đạt yêu cầu; quá hạn sẽ tự động được chấp thuận.",
        "expected_doc_id": "tiktok-seller-return-refund",
        "filter": {"audience": "seller"},
    },
]
    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)

    for q in queries:
        qid = q["id"]
        q_text = q["query"]
        gold = q["gold_answer"]
        q_filter = q["filter"]

        output_lines.append(f"\n[CÂU HỎI {qid}]: {q_text}")
        output_lines.append(f"Câu trả lời chuẩn (Gold Answer): {gold}")
        output_lines.append(f"Metadata filter: {q_filter}")

        # BƯỚC 3: Chạy query qua search_with_filter()
        results = store.search_with_filter(q_text, top_k=3, metadata_filter=q_filter)
        
        # BƯỚC 4: In top-3 kèm score và doc_id đối chiếu với Gold Answer
        output_lines.append("Top-3 Chunks tìm thấy:")
        for rank, r in enumerate(results, 1):
            doc_id = r.get("doc_id", r["metadata"].get("doc_id", ""))
            output_lines.append(f"  Top-{rank} (Score: {r['score']:.4f} | ID: {r['id']} | Doc: {doc_id}):")
            output_lines.append(f"    {r['content'][:140]}...")

        # Agent response
        agent_ans = agent.answer(q_text, top_k=3)
        output_lines.append(f"Agent response summary: {agent_ans[:180]}...")

        if q.get("ab_test"):
            output_lines.append("\n  >>> A/B TEST (Không áp dụng filter):")
            unfiltered_res = store.search(q_text, top_k=3)
            for rank, r in enumerate(unfiltered_res, 1):
                doc_id = r.get("doc_id", r["metadata"].get("doc_id", ""))
                output_lines.append(f"    [Không filter] Top-{rank} (Score: {r['score']:.4f} | ID: {r['id']} | Doc: {doc_id}):")
                output_lines.append(f"      {r['content'][:120]}...")

    report_text = "\n".join(output_lines)
    Path("ket_qua_benchmark.txt").write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    run_benchmark()
