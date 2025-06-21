from fastapi import FastAPI, HTTPException, Body, Depends
from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader
from pydantic import BaseModel
from typing import List
from typing import Optional
from dotenv import load_dotenv
import os

from .rag import split_docs, index_docs, retrieve_docs, answer_question, splitter, vector_store
from .verify_token import verify_token, require_role

# Usando a chave de api do google ai studio
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Modelos de Pergunta e Resposta
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    context_sources: Optional[list[str]] = None

# Schemas de PDFs e URLs
class URLsRequest(BaseModel):
    urls: List[str]

class PDFsRequest(BaseModel):
    filepaths: List[str]
    

# Helper functions
def split_and_tag(docs, source):
    for doc in docs:
        doc.metadata["source"] = source
    return splitter.split_documents(docs)

def rebuild_index():
    vector_store._index = vector_store._embedding_function.embed_documents(
        [doc.page_content for doc in vector_store._docs]
    )

def delete_by_source(source):
    vector_store._documents = [doc for doc in vector_store._documents if doc.metadata.get("source") != source]
    rebuild_index()

app = FastAPI(
    title="UFC ASK",
    description="API for answering questions about Universidade Federal do Ceará",
    version="1.0.0",
    # lifespan=lifespan
)


# Routes
@app.get("/")
async def root():
    return {
        "message": "UFC Student Assistant API",
        "status": "running",
    }

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, payload: dict = Depends(require_role(['admin','estudante']))):
    try:
        related_docs = retrieve_docs(request.question)
        ans = answer_question(request.question, related_docs)
        return AnswerResponse(
            question=request.question,
            answer=ans.content,
            context_sources=[doc.metadata.get('source', 'unknown') for doc in related_docs]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add/urls")
def add_urls(req: URLsRequest, payload: dict = Depends(require_role(['admin']))):
    results = []
    for url in req.urls:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()  # Isso retorna uma lista de Document!
            vector_store.add_documents(docs)  # adiciona no vector store
            results.append({"url": url, "status": "success"})
        except Exception as e:
            results.append({"url": url, "status": f"failed: {str(e)}"})
    return {"results": results}


@app.post("/add/pdfs")
def add_pdfs(req: PDFsRequest,payload: dict = Depends(require_role(['admin']))):
    results = []
    for filepath in req.filepaths:
        try:
            loader = PDFPlumberLoader(filepath)
            docs = loader.load()
            # Adicionando os metadados de origem
            for doc in docs:
                doc.metadata["source"] = filepath
            vector_store.add_documents(docs)
            results.append({"pdf": filepath, "status": "added"})
        except Exception as e:
            results.append({"pdf": filepath, "status": f"failed: {str(e)}"})
    return {"results": results}

@app.delete("/delete/by-source")
def delete_by_source(
    source: str = Body(..., embed=True, description="Source URL or filepath to delete"),
    payload: dict = Depends(require_role(['admin']))
):
    '''Deleta o documento'''
    try:
        ids_to_delete = []
        for doc_id, doc in vector_store.store.items():
            if ('metadata' in doc 
                and isinstance(doc['metadata'], dict)
                and doc['metadata'].get('source') == source):
                ids_to_delete.append(doc_id)
        
        if ids_to_delete:
            vector_store.delete(ids=ids_to_delete)
        
        return {
            "deleted": len(ids_to_delete),
            "message": f"Deleted {len(ids_to_delete)} documents from source '{source}'"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/list-sources")
def list_sources(payload: dict = Depends(require_role(['admin']))):
    """Lista todos os documentos do Vector Store"""
    try:
        sources = set()
        for doc in vector_store.store.values():
            if 'metadata' in doc and isinstance(doc['metadata'], dict):
                source = doc['metadata'].get('source')
                if source:
                    sources.add(source)
        return {"sources": list(sources)}
    except Exception as e:
        return {"error": str(e)}

@app.get("/count-documents")
def count_documents(source: str = None,payload: dict = Depends(require_role(['admin']))):
    '''Conta todos os documentos disponíveis no vector store'''
    try:
        count = 0
        for doc in vector_store.store.values():
            if not source:
                count += 1
            elif ('metadata' in doc 
                  and isinstance(doc['metadata'], dict)
                  and doc['metadata'].get('source') == source):
                count += 1
        return {"count": count}
    except Exception as e:
        return {"error": str(e)}

  
@app.post("/reset")
def reset_vector_store(payload: dict = Depends(require_role(['admin']))):
    '''Reseta o vector store'''
    global vector_store
    vector_store = vector_store
    return {"status": "vector store resetado com sucesso"}