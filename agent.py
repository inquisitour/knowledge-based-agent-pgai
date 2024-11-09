import os
import numpy as np
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from data_processing import get_database_connection
from typing import List, Any
from langchain.schema import Document
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Securely fetch the API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

class EmbeddingRetriever(BaseModel):
    db_connection: Any = Field(..., description="Database connection for retrieving embeddings")
    embeddings: Any = Field(None, description="OpenAI embeddings model")

    def __init__(self, db_connection):
        super().__init__(db_connection=db_connection)
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-large", dimensions=1024)
        print("Embedding retriever initialized")

    def retrieve_similar_questions(self, query, k=10):
        query_vec = self.db_connection.execute("SELECT ai_generate_embedding('openai_embedding', %s)", (query,)).fetchone()[0]
        sql_query = """
        SELECT questions, answers
        FROM Unified_OphthalFAQs
        ORDER BY question_embedding <-> %s::VECTOR
        LIMIT %s
        """
        with self.db_connection.cursor() as cursor:
            cursor.execute(sql_query, (query_vec, k))
            results = cursor.fetchall()
            similar_questions = [{'question': row[0], 'answer': row[1]} for row in results]
        return similar_questions

    def get_relevant_documents(self, query: str) -> List[Document]:
        similar_questions = self.retrieve_similar_questions(query)
        documents = [Document(page_content=q['answer'], metadata={"question": q['question']}) for q in similar_questions]
        return documents

class OpenAIops:
    def __init__(self):
        self.chat_model = ChatOpenAI(api_key=os.environ["OPENAI_API_KEY"], model='gpt-4o', max_tokens=600)
        with get_database_connection() as conn:
            self.retriever = EmbeddingRetriever(conn)

        retriever_tool = Tool(
            name="EmbeddingRetriever",
            func=self.retriever.get_relevant_documents,
            description="Retrieves similar questions and answers from the database"
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are an AI assistant specializing in ophthalmology. Your task is to provide informative and contextual responses to user queries, utilizing the following steps:

            1. Context Understanding:
               - Analyze the user's current question in the context of the entire conversation history.
               - Identify any themes or topics that have been consistently discussed or are particularly relevant.

            2. Information Retrieval:
               - Use the EmbeddingRetriever tool to find relevant information from the ophthalmology database.
               - Consider both the current question and the overall context of the conversation when retrieving information.

            3. Response Generation:
               - Synthesize a comprehensive response that addresses the current question while also acknowledging and building upon previous interactions.
               - Ensure continuity in the conversation by referencing previous topics when relevant.
               - If the user is following up on a previous topic, provide more depth or clarification on that specific area.

            4. Follow-up Suggestions:
               - Based on the current topic and conversation history, suggest relevant follow-up questions or topics that the user might be interested in.
               - These suggestions should be natural extensions of the current conversation and should help guide the user towards a more comprehensive understanding of the topic.
               - Follow-up questions should be added from the starting of the conversation.
               
            5. Response Format:
               - You must present your response in at least 2-3 small paragraphs, keeping each paragraph concise for readability.
               - Use the "~" symbol at the end of each paragraph, except for the last one.
               - At the end of your response, suggest 3-4 relevant follow-up questions or topics from the patients perspective, prefixed with "📌".

            Remember, your goal is to provide accurate, contextual, and helpful information about ophthalmology, ensuring a coherent and engaging conversation flow.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        tools = [retriever_tool]
        self.agent = create_openai_tools_agent(
            llm=self.chat_model,
            tools=tools,
            prompt=self.prompt_template
        )

        self.agent_executor = AgentExecutor.from_agent_and_tools(self.agent, tools)
        print("OpenAI operations with LangChain agent initialized")

    def answer_question(self, user_question, chat_history):
        formatted_history = [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]
        response = self.agent_executor({
            "input": user_question,
            "chat_history": formatted_history
        })
        output = response["output"]
        print("Finishing up..!")
        return output

class ResponseAgent:
    def __init__(self):
        self.openaiops = OpenAIops()
        print("Response agent initialized")

    def answer_question(self, user_question, chat_history):
        return self.openaiops.answer_question(user_question, chat_history)

    def extract_follow_up_questions(self, response):
        follow_ups = []
        for line in response.split('\n'):
            if line.strip().startswith('📌'):
                follow_ups.append(line.strip()[1:].strip())
        return follow_ups