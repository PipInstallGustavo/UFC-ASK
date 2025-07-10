from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List, Optional

# classe com as funções e métodos do InMemoryVectorStore
class InMemoryStore:
    def __init__(self):
        self._embedding_function = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self._docs = []
        self._index = InMemoryVectorStore(self._embedding_function)

    #adicionar documentos no índice do BD vetorial
    def add_documents(self, docs):
        self._docs.extend(docs)
        self._index = InMemoryVectorStore.from_documents(self._docs, self._embedding_function)

    #função para fazer a busca de similaridade
    def similarity_search(self, query: str, k: int = 3):
        return self._index.similarity_search(query, k=k)

    #deletar um ou mais documentos do índice
    def delete_by_source(self, sources: List[str]):
        self._docs = [doc for doc in self._docs if doc.metadata.get("source") not in sources]
        self._index = InMemoryVectorStore.from_documents(self._docs, self._embedding_function)
        return True

    #listar todos os documentos
    def list_sources(self):
        return list({doc.metadata.get("source", "unknown") for doc in self._docs})

    #contar os documentos que estão disponíveis no índice
    def count_documents(self, source: str = None):
        return len(set(doc.metadata.get("source") for doc in self._docs))

