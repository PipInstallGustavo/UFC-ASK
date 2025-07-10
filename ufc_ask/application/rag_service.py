from typing import List

# Métodos Core da Aplicação do RAG
class RAGService:
    def __init__(self, vector_store, llm, prompt_builder):
        self.vector_store = vector_store
        self.llm = llm
        self.prompt_builder = prompt_builder

    #fazer pergunta e retornar uma resposta de acordo com a busca de similaridade 
    def ask_question(self, question: str, k: int = 3) -> dict:
        docs = self.vector_store.similarity_search(question, k=k)
        prompt = self.prompt_builder.build_prompt(question, docs)
        answer = self.llm.generate(prompt)

        # converter para string se necessário
        if hasattr(answer, "content"):
            answer = answer.content
        else:
            answer = str(answer)
        print("DEBUG >>>", type(answer), answer)


        return {
            "question": question,
            "answer": answer,
            "context_sources": [doc.metadata.get("source", "unknown") for doc in docs]
        }

    def add_documents(self, docs):
        self.vector_store.add_documents(docs)

    def delete_by_source(self, source: List[str]):
        return self.vector_store.delete_by_source(source)

    def list_sources(self):
        return self.vector_store.list_sources()

    def count_documents(self, source: str = None):
        return self.vector_store.count_documents(source)
