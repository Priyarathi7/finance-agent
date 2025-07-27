# langgraph_agent.py
from typing import TypedDict, List, Union
from langgraph.graph import StateGraph
from langchain.schema import HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Define the state structure
class GraphState(TypedDict):
    input: str
    response: str
    history: List[Union[HumanMessage, AIMessage]]
    context: dict

# Init LLM and memory
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key="AIzaSyBPDULDOrhFbhrE3yhTvL5Ja_Xchg-nBOQ")
memory = ConversationBufferMemory(memory_key="history", return_messages=True)
conversation = ConversationChain(llm=llm, memory=memory)

# Define step
def user_input_step(state: GraphState):
    user_input = state["input"]
    financial_context = state.get("context", {})

    # Inject financial data into the prompt
    context_prompt = f"""
    The user is seeking financial help or guidance. Here is their financial data:

    Bank Transactions: {json.dumps(financial_context.get('fetch_bank_transactions'), indent=2)}
    Credit Report: {json.dumps(financial_context.get('fetch_credit_report'), indent=2)}
    Mutual Fund Transactions: {json.dumps(financial_context.get('fetch_mf_transactions'), indent=2)}
    EPF Summary: {json.dumps(financial_context.get('fetch_epf_details'), indent=2)}
    Stock Transactions: {json.dumps(financial_context.get('fetch_stock_transactions'), indent=2)}
    Net Worth: {json.dumps(financial_context.get('fetch_net_worth'), indent=2)}

    Now respond to the user's query based on the above context.
    Query: {user_input}
    """

    response = conversation.predict(input=context_prompt)
    return {"response": response, "history": memory.chat_memory.messages, "context": financial_context}

# Build graph
def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("chat", user_input_step)
    graph.set_entry_point("chat")
    graph.set_finish_point("chat")
    return graph.compile()

graph = build_graph()

# Public method to invoke agent
def run_graph_agent(user_input: str, financial_context: dict) -> dict:
    state = {
        "input": user_input,
        "response": "",
        "history": [],
        "context": financial_context
    }
    output = graph.invoke(state)

    readable_history = [
        {"role": "user" if isinstance(msg, HumanMessage) else "ai", "message": msg.content}
        for msg in output["history"]
    ]
    print("--------------------------------History")
    print(readable_history)
    print("-------------------------------- Response")
    print(output["response"])
    return {
        "response": output["response"],
        "history": readable_history
    }
