from langchain_community.document_loaders import PDFPlumberLoader, WebBaseLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

import os

# Inicializar o vectore store, llm e modelo de embedding
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
vector_store = InMemoryVectorStore(embeddings)
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", convert_system_message_to_human=True)

template = '''
    You are an assistant for University Students, more specifically of the Universidade Federal do Ceará(UFC). 
    Your task is to answer students' questions about anything related to the University. 
    Most of them are new students, so they need help and your support. 
    Be as clear as possible and don't leave the main idea of the question in your answers.
    Use the following context to answer the questions. If you don't know, just say that you can't help with it.
    Don't communicate outside of Brazilian Portuguese, if the user is speaking in a different language, just answer, in portuguese, that you can't help.

    Question: {question}
    Context: {context}
    Answer:
'''

def initialize_documents():
    pdfs_folder = './pdfs/'
    urls = [
        'https://cc.ufc.br/pt/sobre-o-curso/',
        'https://cc.ufc.br/pt/sobre-o-curso/projeto-pedagogico/atividades-complementares/',
        'https://cc.ufc.br/pt/sobre-o-curso/projeto-pedagogico/trabalho-de-conclusao-de-curso/',
        'https://www.ufc.br/a-universidade',
        'https://www.ufc.br/ensino',
        'https://www.ufc.br/pesquisa',
        'https://www.ufc.br/extensao',
        'https://www.ufc.br/internacional',
        'https://www.ufc.br/ouvidoria',
        'https://acessoainformacao.ufc.br/pt/acesso-a-informacao/',
        'https://prograd.ufc.br/pt/ingresso-na-ufc/',
        'https://prograd.ufc.br/pt/perguntas-frequentes/admissao-de-graduados/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-de-apoio-a-projetos-de-graduacao/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-do-pet-sesu-programa-de-educacao-tutorial-secretaria-de-educacao-superior/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-do-pet-ufc-programa-de-educacao-tutorial-universidade-federal-do-ceara/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-do-pibid-programa-institucional-de-bolsa-de-iniciacao-a-docencia/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-do-pid-programa-de-iniciacao-a-docencia/',
        'https://prograd.ufc.br/pt/bolsas/bolsas-do-prp-programa-de-residencia-pedagogica/',
        'https://prograd.ufc.br/pt/cursos-de-graduacao/?limit=todas',
        'https://acessoainformacao.ufc.br/pt/servidores/',
        'https://prae.ufc.br/pt/residencia-universitaria/informacoes-sobre-o-programa-de-residencia-universitaria/',
        'https://www.ufc.br/restaurante',
        'https://prae.ufc.br/pt/dae/',
        'https://prae.ufc.br/pt/dae/mapsaude/?limit=todas',
        'https://prointer.ufc.br/pt/sobre-a-prointer/apresentacao/',
        'https://www.lesc-lab.com.br/embrapii/',
        'https://www.ufc.br/cultura-e-arte',
        'https://www.ufc.br/biblioteca',
        'https://webmail.ufc.br/',
        'https://www.ufc.br/acessibilidade/dicas-de-acessibilidade-no-portal-da-ufc',
        'https://www.ufc.br/acessibilidade/cartilha-de-acessibilidade-na-ufc-com-audiodescricao',
        'https://www.ufc.br/acessibilidade/acoes-de-acessibilidade-na-ufc',
        'https://www.ufc.br/acessibilidade/conceito-de-acessibilidade',
        'https://www.ufc.br/acessibilidade/secretaria-de-acessibilidade-ufc-inclui',
        'https://www.ufc.br/alunos',
        'https://acessibilidade.ufc.br/pt/sobre/publico-alvo/',
        'https://acessibilidade.ufc.br/pt/sobre/nossa-historia/',
    ]

    urls_docs = []
    for url in urls:
        try:
            loader = WebBaseLoader(url)
            urls_docs.extend(loader.load())
        except Exception as e:
            print(f"Falha ao carregar {url}: {str(e)}")

    pdfs_docs = []
    if os.path.exists(pdfs_folder):
        pdf_paths = [os.path.join(pdfs_folder, f) for f in os.listdir(pdfs_folder) if f.endswith('.pdf')]
        for path in pdf_paths:
            try:
                loader = PDFPlumberLoader(path)
                pdfs_docs.extend(loader.load())
            except Exception as e:
                print(f"Falha ao carregar {path}: {str(e)}")

    return urls_docs + pdfs_docs

def split_docs(docs):
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500,
        chunk_overlap=25,
        separators=["\n\n", "\n", ".", " ", ""],
        add_start_index=True
    )
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
