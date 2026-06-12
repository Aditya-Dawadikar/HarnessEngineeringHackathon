from fastapi import FastAPI

app = FastAPI(title="Agentic Negotiation & Procurement Platform")


@app.get("/health")
def health_check():
    return {"status": "ok"}
