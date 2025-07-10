#Classe do prompt
class PromptBuilder:
    TEMPLATE = """
    Você é um assistente para estudantes da Universidade Federal do Ceará (UFC).
    Sua tarefa é responder perguntas sobre a UFC, com clareza e precisão.
    Utilize o seguinte contexto para responder. Caso não saiba, diga que não pode ajudar.

    Pergunta: {question}
    Contexto: {context}
    Resposta:
    """

    def build_prompt(self, question, docs):
        context = "\n\n".join([doc.page_content for doc in docs])
        return self.TEMPLATE.format(question=question, context=context)
