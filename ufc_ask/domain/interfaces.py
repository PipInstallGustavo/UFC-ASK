from abc import ABC, abstractmethod

#Interfaces
class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, k: int): ...

class LLM(ABC):
    @abstractmethod
    def generate(self, prompt: str): ...

class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, docs): ...

    @abstractmethod
    def similarity_search(self, query: str, k: int): ...

    @abstractmethod
    def delete_by_source(self, source: str): ...

    @abstractmethod
    def list_sources(self): ...

    @abstractmethod
    def count_documents(self): ...
