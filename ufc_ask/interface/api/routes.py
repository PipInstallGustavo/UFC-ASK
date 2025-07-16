from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader

from ufc_ask.application.rag_service import RAGService
from ufc_ask.infrastructure.vector.chroma_store import PersistentChromaStore
from ufc_ask.infrastructure.llm.gemini_llm import GeminiLLM
from ufc_ask.infrastructure.context.prompt_builder import PromptBuilder
from .auth import require_role

import os

from datetime import datetime

# === Request/Response Schemas ===

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    context_sources: Optional[list[str]] = None

class URLsRequest(BaseModel):
    urls: List[str]

class PDFsRequest(BaseModel):
    filepaths: List[str]

# === Init ===

router = APIRouter()
rag = RAGService(PersistentChromaStore(), GeminiLLM(), PromptBuilder())

# === Routes ===

@router.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest, payload: dict = Depends(require_role(['admin', 'estudante']))):
    try:
        result = rag.ask_question(request.question)
        return AnswerResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add/urls")
# def add_urls(req: URLsRequest, payload: dict = Depends(require_role(['admin']))):
#     results = []
#     for url in req.urls:
#         data_adicao = None
#         try:
#             loader = WebBaseLoader(url)
#             docs = loader.load()
#             rag.add_documents(docs)
#             data_adicao = datetime.now().strftime("%d/%m/%Y %H:%M")
#             results.append({"url": url, "status": "success", "data_insercao":data_adicao, "user":payload['sub']  })
#         except Exception as e:
#             results.append({"url": url, "status": f"failed: {str(e)}"})
#     return {"results": results, "Qtd_urls_adicionadas": len(results)}

@router.post("/add/urls")
def add_urls(req: URLsRequest, payload: dict = Depends(require_role(['admin']))):
    results = []
    for url in req.urls:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            data_insercao = datetime.now().strftime("%d/%m/%Y %H:%M")
            for doc in docs:
                doc.metadata["source"] = url
                doc.metadata["user"] = payload["sub"]
                doc.metadata["data_insercao"] = data_insercao
                doc.metadata["tipo"] = "url"
            rag.add_documents(docs)
            results.append({
                "url": url,
                "status": "success",
                "data_insercao": data_insercao,
                "user": payload["sub"]
            })
        except Exception as e:
            results.append({"url": url, "status": f"failed: {str(e)}"})
    return {"results": results, "Qtd_urls_adicionadas": len(results)}


# @router.post("/add/pdfs")
# def add_pdfs(req: PDFsRequest, payload: dict = Depends(require_role(['admin']))):
#     results = []
#     data_insercao = None
#     for filepath in req.filepaths:
#         try:
#             if not os.path.isfile(filepath):
#                 raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

#             loader = PDFPlumberLoader(filepath)
#             docs = loader.load()

#             # usa apenas o nome do arquivo como metadado visível
#             filename = os.path.basename(filepath)
#             for doc in docs:
#                 doc.metadata["source"] = filename

#             rag.add_documents(docs)
#             data_adicao = datetime.now().strftime("%d/%m/%Y %H:%M")
#             results.append({"pdf": filename, "status": "adicionado", "user": payload['sub'], "data_adicao": data_adicao})
#         except Exception as e:
#             results.append({"pdf": filepath, "status": f"falhou: {str(e)}"})
#     return {"results": results, "qtd_pdfs_adicionados": len(results)}

@router.post("/add/pdfs")
def add_pdfs(req: PDFsRequest, payload: dict = Depends(require_role(['admin']))):
    results = []
    for filepath in req.filepaths:
        try:
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

            loader = PDFPlumberLoader(filepath)
            docs = loader.load()

            filename = os.path.basename(filepath)
            data_adicao = datetime.now().strftime("%d/%m/%Y %H:%M")
            for doc in docs:
                doc.metadata["source"] = filename
                doc.metadata["user"] = payload["sub"]
                doc.metadata["data_insercao"] = data_adicao
                doc.metadata["tipo"] = "pdf"

            rag.add_documents(docs)
            results.append({
                "pdf": filename,
                "status": "adicionado",
                "user": payload["sub"],
                "data_adicao": data_adicao
            })
        except Exception as e:
            results.append({"pdf": filepath, "status": f"falhou: {str(e)}"})
    return {"results": results, "qtd_pdfs_adicionados": len(results)}


@router.delete("/delete/by-source")
def delete_by_source(source: List[str] = Body(...), payload: dict = Depends(require_role(['admin']))):
    try:
        rag.delete_by_source(source)
        return {"message": f"Documentos deletados da fonte '{source}'"}
    except Exception as e:
        return {"error": str(e)}

    
@router.get("/list-sources")
def list_sources(payload: dict = Depends(require_role(['admin']))):
    try:
        return {"fontes": rag.list_sources()}
    except Exception as e:
        return {"error": str(e)}


@router.get("/count-documents")
def count_documents(payload: dict = Depends(require_role(['admin']))):
    try:
        return {"Quantidade total de documentos": rag.count_documents()}
    except Exception as e:
        return {"error": str(e)}




