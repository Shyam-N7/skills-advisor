# Enhanced Personalized Career & Skills Advisor — Starter Repo

This is a ready-to-run **MVP prototype** for your Google Cloud GenAI Hackathon submission.

It includes:
- **FastAPI** backend with endpoints: `/assess`, `/recommend`, `/gap`, `/roadmap`, `/health`
- **Streamlit** frontend to collect inputs and show recommendations, skill gaps, and a roadmap
- **Sample data** (3 careers) + **market stub**
- **Prompt files** (matching, roadmap, coach) to plug into Vertex AI (later)

> ⚠️ For the hackathon demo you can keep this local. When ready, move the API to **Cloud Run**, host the UI on **Firebase Hosting**, and plug in **Vertex AI** (Gemini + Embeddings).

---

## Quickstart (Local)

### 1) Backend (FastAPI)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
This serves the API at `http://localhost:8000`. Test health:
```
curl http://localhost:8000/health
```

### 2) Frontend (Streamlit)
In a **new terminal**:
```bash
cd frontend
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Open the Streamlit URL shown in your terminal (usually `http://localhost:8501`).

> The UI defaults to backend URL `http://localhost:8000`. You can change it in the sidebar.

---

## What’s inside

```
career_advisor_prototype/
├─ README.md
├─ backend/
│  ├─ app/main.py
│  └─ requirements.txt
├─ frontend/
│  ├─ streamlit_app.py
│  └─ requirements.txt
├─ data/
│  ├─ careers_ontology.json
│  ├─ market_stub.json
│  └─ quiz_bank.json
└─ prompts/
   ├─ matching_prompt.txt
   ├─ roadmap_prompt.txt
   └─ coach_system_prompt.txt
```

- **`data/careers_ontology.json`** — 3 India-relevant roles with skills by level (L1/L2/L3), starter projects, courses, salary bands (INR), and metros.
- **`data/market_stub.json`** — demand score & hot/cooling skills for demo realism.
- **`data/quiz_bank.json`** — 10-question adaptive-ish intake seed.
- **`prompts/`** — copy-friendly prompts to use with Vertex AI (when you wire it).

---

## Roadmap to “production-style” demo

- Swap retrieval heuristic for **Vertex AI Text Embeddings** for career and profile vectors.
- Use **Gemini** with `prompts/matching_prompt.txt` to re-rank + explain + add confidence.
- Use **Gemini** with `prompts/roadmap_prompt.txt` to generate the 8-week plan.
- Add **Firebase Auth + Firestore** to persist profiles, recommendations, roadmaps, and chat history.
- Deploy API → **Cloud Run**; UI → **Firebase Hosting**.

Good luck at the hackathon! 🚀
