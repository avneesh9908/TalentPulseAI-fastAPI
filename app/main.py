from fastapi import FastAPI

app = FastAPI(title="TalentPulseAI Backend")

@app.get("/")
def root():
    return {"message": "TalentPulseAI API is running"}
