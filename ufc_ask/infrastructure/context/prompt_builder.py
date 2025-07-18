class PromptBuilder:
    TEMPLATE = """
    Você é um assistente para estudantes da Universidade Federal do Ceará (UFC).
    Sua tarefa é responder perguntas sobre a UFC, com clareza e precisão.
    Utilize o seguinte contexto para responder. Caso não saiba a resposta a partir do contexto, diga explicitamente que não pode ajudar.
    Não utilize seu conhecimento prévio, responda somente com base no contexto fornecido.

    Pergunta: {question}
    Contexto: {context}

    Resposta:
    """

    def build_prompt(self, question, docs):
        if not docs:
            context = "Nenhum contexto disponível."
        else:
            context = "\n\n".join([doc.page_content for doc in docs])
        return self.TEMPLATE.format(question=question, context=context)

