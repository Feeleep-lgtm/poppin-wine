# chatbot/utils.py 

from langchain.retrievers.web_research import WebResearchRetriever
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from openai import OpenAI
import os 
import logging
import traceback


# Set Chroma path from environment variable
CHROMA_PATH = os.getenv("CHROMA_PERSISTENT_PATH", "chroma")
print(f"Chroma path: {CHROMA_PATH}")

# Define prompt template
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}
Do  not provide responses for questions not related to wines, individuals in the wine industry or the wine industry in general.
Simply let the user know you cannot provide respones to queries outside of your set parameters
---

Answer the question based on the above context: {question}
"""

logger = logging.getLogger(__name__)

# Query the Chroma database or use web research if needed
def query_chroma_db(query_text):
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    results = db.similarity_search_with_relevance_scores(query_text, k=3)
    print(" similarity_search_with_relevance_scores results ", results)
    if len(results) == 0 or results[0][1] < 0.7:
        # If no sufficient results, perform web research
        vectorstore = Chroma(embedding_function=embedding_function, persist_directory=CHROMA_PATH)
        llm = ChatOpenAI(temperature=0)
        search = GoogleSearchAPIWrapper(k=3)
        web_research_retriever = WebResearchRetriever.from_llm(vectorstore=vectorstore, llm=llm, search=search)
        qa_chain = RetrievalQAWithSourcesChain.from_chain_type(llm, retriever=web_research_retriever)
        result = qa_chain({"question": query_text})
        answer = result['answer']
        print('result...', result)
        # sources = result['sources']
        # sources_text = "source(s):\n".join([f"- ({source.get('link', 'No link')})" for source in sources])
        return f"{answer}"

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    model = ChatOpenAI()
    response_text = model.predict(prompt)
    sources = [doc.metadata.get("source", None) for doc, _ in results]
    sources_text = "\n".join([f"- {source}" for source in sources if source])
    # return f"{response_text}\n\nSources:\n{sources_text}"
    return f"{response_text}"


def ask_openai(message):
    client = OpenAI(
        # defaults to os.environ.get("OPENAI_API_KEY")
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who only answers related to the field of wines and winery(provided answers not related to this may be harmful to the user). Let the user know you cannot answer questions outside this field if a question asked outside the field of wines or related field."},
            {"role": "user", "content": message},
        ]
    )
    answer = response.choices[0].message.content.strip()
    return answer

