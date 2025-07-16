from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from typing import List
import os

class PersistentChromaStore:
    def __init__(self, persist_directory="vector_db", collection_name="default"):
        self._embedding_function = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # self._embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._index = Chroma(
            collection_name=self._collection_name,
            embedding_function=self._embedding_function,
            persist_directory=self._persist_directory
        )

    def add_documents(self, docs: List[Document]):
        self._index.add_documents(docs)
        metadatas = [doc.metadata for doc in docs]
        print("metadatas: ",metadatas)
        self._index.persist()

    def similarity_search(self, query: str, k: int = 3):
        return self._index.similarity_search(query, k=k)

    def delete_by_source(self, sources: List[str]):
        for source in sources:
            self._index.delete(where={"source": source})
        self._index.persist()

    def count_documents(self):
        result = self._index.get()
        metadatas = result.get("metadatas", [])
        parent_docs = set()
        for meta in metadatas:
            if "parent_doc" in meta:
                parent_docs.add(meta["parent_doc"])
            elif "source" in meta:
                parent_docs.add(meta["source"])
        return len(parent_docs)

    def list_sources(self):
        result = self._index.get()
        # print("DEBUG metadatas:", result)
        # print("DEBUG metadatas:", result['metadatas'])
        metadatas = result['metadatas']
        unique_sources = {}

        for meta in metadatas:
            # print("debug: ", meta)
            source = meta.get('source', [])
            print("source: ", source)
            user = meta.get('user', [])
            print("user: ", user)
            insertion_time = meta.get('data_insercao', [])
            print("data_insercao: ", insertion_time)
            tipo = meta.get('tipo', "")
            if source:
                unique_sources[source] = {
                    "source": source,
                    "user": user,
                    "insertion_time": insertion_time,
                    "tipo": tipo
                }
        return list(unique_sources.values())

