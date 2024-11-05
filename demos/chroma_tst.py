# from cwe_parser import load_cwe_from_xml
# from dotenv import load_dotenv
# import os
# load_dotenv()
# tmp = load_cwe_from_xml(os.getenv('CWE_SRC'))
# print(tmp)


# import chromadb
# chroma_client = chromadb.Client()

# # switch `create_collection` to `get_or_create_collection` to avoid creating a new collection every time
# collection = chroma_client.get_or_create_collection(name="my_collection")

# # switch `add` to `upsert` to avoid adding the same documents every time
# collection.upsert(
#     documents=tmp,
#     ids=["id1", "id2"]
# )

# results = collection.query(
#     query_texts=["This is a query document about cookies"], # Chroma will embed this for you
#     n_results=8 # how many results to return
# )

# print(results)


import getpass
import os
from dotenv import load_dotenv

load_dotenv()


def _set_env(key: str):
    if key not in os.environ:
        os.environ[key] = getpass.getpass(f"{key}:")


_set_env("ANTHROPIC_API_KEY")

# !!!!!!!!!!!!!! RETRIEVER !!!!!!!!!!!!!!
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic

from cwe_parser import load_cwe_from_xml
from langchain_community.document_loaders import UnstructuredXMLLoader

tmp = load_cwe_from_xml(os.getenv('CWE_SRC'))
print(tmp)
# exit()

# urls = [
#     "https://lilianweng.github.io/posts/2023-06-23-agent/",
#     # "https://lilianweng.github.io/posts/2023-03-15-prompt-engineering/",
#     # "https://lilianweng.github.io/posts/2023-10-25-adv-attack-llm/",
# ]

# docs = [WebBaseLoader(url).load() for url in urls]
# # print(docs)
# docs_list = [item for sublist in docs for item in sublist]
# print(docs_list)
# exit()

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)
# doc_splits = text_splitter.split_documents(docs_list)
doc_splits = text_splitter.split_documents(tmp)



# Add to vectorDB
vectorstore = Chroma.from_documents(
    documents=doc_splits,
    collection_name="rag-chroma",
    embedding=OpenAIEmbeddings(),
)
retriever = vectorstore.as_retriever()

question = "cookie"
ret = retriever.invoke(question)
print(ret[0])