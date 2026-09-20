from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        context_blocks = []
        for i, res in enumerate(results, 1):
            source = res.get("metadata", {}).get("title") or res.get("id") or f"Tài liệu {i}"
            context_blocks.append(f"[{i}] ({source}):\n{res['content']}")
        context_str = "\n\n".join(context_blocks)

        prompt = (
            f"Bạn là trợ lý AI trả lời câu hỏi dựa trên cơ sở tri thức sau:\n\n"
            f"--- NGỮ CẢNH ---\n"
            f"{context_str}\n"
            f"-----------------\n\n"
            f"Câu hỏi: {question}\n\n"
            f"Yêu cầu:\n"
            f"- Chỉ trả lời dựa trên ngữ cảnh đã cung cấp ở trên.\n"
            f"- Hãy trích dẫn số thứ tự nguồn (ví dụ: [1], [2]) khi đưa ra thông tin.\n"
            f"- Nếu không có thông tin trong ngữ cảnh, hãy nói rõ rằng bạn không tìm thấy thông tin."
        )
        return self.llm_fn(prompt)
