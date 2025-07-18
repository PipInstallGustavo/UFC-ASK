from fastapi import APIRouter, Body, Depends, HTTPException,UploadFile, File
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
import pytz

fuso_brasilia = pytz.timezone("America/Sao_Paulo")

# === Request/Response Schemas ===

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    question: str
    answer: str
    context_sources: Optional[list[str]] = None

class URLsRequest(BaseModel):
    urls: List[str]

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
def add_urls(req: URLsRequest, payload: dict = Depends(require_role(['admin']))):
    results = []
    for url in req.urls:
        try:
            loader = WebBaseLoader(url)
            docs = loader.load()
            data_insercao = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M")
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


@router.post("/add/pdfs")
async def add_pdfs(files: List[UploadFile] = File(...), payload: dict = Depends(require_role(['admin']))):
    results = []
    for uploaded_file in files:
        try:
            # Salva temporariamente o PDF
            contents = await uploaded_file.read()
            temp_path = f"/tmp/{uploaded_file.filename}"
            with open(temp_path, "wb") as f:
                f.write(contents)

            # Carrega o conteúdo do PDF
            loader = PDFPlumberLoader(temp_path)
            docs = loader.load()

            # Metadados
            filename = uploaded_file.filename
            data_adicao = datetime.now(fuso_brasilia).strftime("%d/%m/%Y %H:%M")
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

            os.remove(temp_path)

        except Exception as e:
            results.append({
                "pdf": uploaded_file.filename,
                "status": f"falhou: {str(e)}"
            })

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




