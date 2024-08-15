from llama_index.agent.openai import OpenAIAgent
from llama_index.core.tools import FunctionTool
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from openai import OpenAI
from groq import Groq
import resend
## ENVIRONMENT
os.environ['OPENAI_API_KEY'] = ''
YOUR_API_KEY = ""
groqClient = Groq(
    api_key="",
)
perplexityClient = OpenAI(api_key="", base_url="https://api.perplexity.ai")
resend.api_key = ""


## NOTE DOCS
documents = SimpleDirectoryReader("notes").load_data()
index = VectorStoreIndex.from_documents(documents)

## TOOLS
def describe_image(prompt_for_describe_image: str) -> str:
    """
    Describe the image that is in the person's view. A prompt/question will be asked and the tool will answer that.
    """

    return request_vision(prompt_for_describe_image)

def search_tool(what_to_search: str) -> str:
    """
    Search something based on what the user wants to search
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are an artificial intelligence assistant and you need to "
                "engage in a helpful, detailed, polite conversation with a user."
            ),
        },
        {
            "role": "user",
            "content": (
                what_to_search
            ),
        },
    ]
    response = perplexityClient.chat.completions.create(
        model="sonar-small-online",
        messages=messages,
    )

    return response.choices[0].message.content

def text_tool(phone_number: str, thing_to_text: str) -> str:
    """
    Text tool to message someone something based on what the user wants to tell the person. SMS message
    """

    return 'I have texted. You wanted to text: ' + str(thing_to_text)

def email_tool(email: str, thing_to_email: str) -> str:
    """
    Email tool to email someone something based on what the user wants to tell the person. Email Tool
    """

    params = {
        "from": "PeronsalAssitant <onboarding@resend.dev>",
        "to": [email],
        "subject": "Message through PA",
        "html": f"<strong>{thing_to_email}</strong>",
    }
    email = resend.Emails.send(params)

    return 'I have emailed.'

def answer_tool(prompt_question: str) -> str:
    """
    Answer tool is answering a prompt that does not require using a search tool and nothing has to be searched. The prompt is whatever the user asks for. Its for answering questions
    """

    chat_completion = groqClient.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt_question,
            }
        ],
        model="mixtral-8x7b-32768",
    )

    return chat_completion.choices[0].message.content

def note_tool(notes_to_take: str) -> str:
    """
    Take notes tool. Based on what the person wants to take a note on it will add it to a database
    """
    with open('notes/notes.text', 'a') as file:
        file.write(notes_to_take + '\n')

    # update the documents incase they have more conversations
    refreshed_docs = index.refresh_ref_docs(
        documents=documents, update_kwargs={"delete_kwargs": {"delete_from_docstore": True}}
    )   

    return 'Took the notes. The notes you took: ' + notes_to_take

def retrieve_notes_tool(thing_retrieve: str) -> str:
    """
    Retrieve notes from a text file which has information that can be retrieved from past conversations. Imagine this is a notepad where people can view past information they had.
    """

    # RAG for asking the text file and answer questions extremely quickly
    query_engine = index.as_query_engine()
    response = query_engine.query(thing_retrieve)

    return 'From notes I got: ' + str(response)

## init all the tools
function_tool = FunctionTool.from_defaults(fn=describe_image)
function_tool1 = FunctionTool.from_defaults(fn=search_tool)
function_tool2 = FunctionTool.from_defaults(fn=text_tool)
function_tool3 = FunctionTool.from_defaults(fn=email_tool)
function_tool4 = FunctionTool.from_defaults(fn=answer_tool)
function_tool5 = FunctionTool.from_defaults(fn=note_tool)
function_tool6 = FunctionTool.from_defaults(fn=retrieve_notes_tool)

# put tools in a list and create an agent
tools = [function_tool, function_tool1, function_tool2, function_tool3, function_tool4, function_tool5, function_tool6]
agent = OpenAIAgent.from_tools(tools, verbose=True)

# use agent
response = agent.chat(
    "Retrieve my location from note pad"
)
#os.system("say '" +str(response) + "'")
print(str(response))
