from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from .rag import initialize_documents, split_docs, index_docs, retrieve_docs, answer_question

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

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inicializando documentos e Vector Store")
    try:
        docs = initialize_documents()
        chunks = split_docs(docs)
        index_docs(chunks)
        print(f"Inicialização completa. carregados {len(chunks)} chunks.")
    except Exception as e:
        print(f"Inicialização falhou {str(e)}")
        raise
    yield
    print("Fechando...")

app = FastAPI(
    title="UFC ASK",
    description="API for answering questions about Universidade Federal do Ceará",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "message": "UFC Student Assistant API",
        "status": "running",
        "endpoints": {
            "/ask": "POST with question to get answers",
            "/health": "GET to check API status"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
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
