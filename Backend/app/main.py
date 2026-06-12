import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.config import BUYER_CONFIG, VENDOR_CONFIG
from app.graph import NegotiationState, build_graph, build_initial_state

app = FastAPI(title="Agentic Negotiation & Procurement Platform")

_GRAPH = build_graph()

NEGOTIATIONS: dict[str, NegotiationState] = {}


@app.get("/health")
def health_check():
    return {"status": "ok"}


def run_negotiation(transaction_id: str) -> None:
    state = NEGOTIATIONS[transaction_id]
    for updated_state in _GRAPH.stream(state, stream_mode="values"):
        NEGOTIATIONS[transaction_id] = updated_state


@app.post("/negotiations/start")
def start_negotiation(background_tasks: BackgroundTasks):
    transaction_id = str(uuid.uuid4())
    NEGOTIATIONS[transaction_id] = build_initial_state(transaction_id, VENDOR_CONFIG, BUYER_CONFIG)
    background_tasks.add_task(run_negotiation, transaction_id)
    return {"transaction_id": transaction_id}


@app.get("/negotiations/{transaction_id}")
def get_negotiation(transaction_id: str):
    state = NEGOTIATIONS.get(transaction_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    return {
        "transaction_id": state["transaction_id"],
        "status": state["status"],
        "turn": state["turn"],
        "messages": state["messages"],
        "invoice": state["invoice"],
    }
