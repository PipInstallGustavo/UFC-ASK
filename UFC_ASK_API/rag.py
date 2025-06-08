from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os

# Inicializar o vector store, llm, splitter e modelo de embedding
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

vector_store = InMemoryVectorStore(embeddings)

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", convert_system_message_to_human=True)

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=500,
    chunk_overlap=25,
    separators=["\n\n", "\n", ".", " ", ""],
    add_start_index=True
)

template = '''
    You are an assistant for University Students, more specifically of the Universidade Federal do Ceará(UFC). 
    Your task is to answer students' questions about anything related to the University. 
    Most of them are new students, so they need help and your support. 
    Be as clear as possible and don't leave the main idea of the question in your answers.
    Use the following context to answer the questions. If you don't know or don't have any source, just say that you can't help with it because you lack information.
    Don't communicate outside of Brazilian Portuguese, if the user is speaking in a different language, just answer, in portuguese, that you can't help.

    Question: {question}
    Context: {context}
    Answer:
'''

def split_docs(docs):
    return splitter.split_documents(docs)

def index_docs(splitted_docs):
    vector_store.add_documents(splitted_docs)

def retrieve_docs(query, k=3):
    return vector_store.similarity_search(query, k=k)

def answer_question(question, documents):
    context = '\n\n'.join([doc.page_content for doc in documents])
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return chain.invoke({"question": question, "context": context})