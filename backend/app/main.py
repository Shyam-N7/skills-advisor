import json
import math
import os
from typing import List, Dict, Any, Optional, Tuple

from fastapi import FastAPI, Body
from pydantic import BaseModel, Field

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

with open(os.path.join(DATA_DIR, "careers_ontology.json"), "r", encoding="utf-8") as f:
    CAREERS = json.load(f)["careers"]

with open(os.path.join(DATA_DIR, "market_stub.json"), "r", encoding="utf-8") as f:
    MARKET = json.load(f)["market"]

app = FastAPI(title="Career Advisor Prototype API", version="0.1.0")


# ---------- Schemas ----------
class ProfileInput(BaseModel):
    interests: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    hours_per_week: int = 5
    budget_inr_per_month: int = 0
    city: str = "Other"
    learning_style: Optional[str] = "Videos"
    goal_text: Optional[str] = ""


class RecommendationItem(BaseModel):
    career_id: str
    title: str
    rationale: str
    confidence_pct: float
    readiness_pct: float
    missing_skills: List[str] = Field(default_factory=list)
    market_note: str
    alternatives: List[str] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    items: List[RecommendationItem]


class GapRequest(BaseModel):
    career_id: str
    skills: List[str] = Field(default_factory=list)


class GapResponse(BaseModel):
    career_id: str
    readiness_pct: float
    missing_by_level: Dict[str, List[str]]


class RoadmapRequest(BaseModel):
    career_id: str
    hours_per_week: int = 5
    budget_inr_per_month: int = 0
    learning_style: Optional[str] = "Videos"


class RoadmapWeek(BaseModel):
    week: int
    focus: str
    resources: List[str]
    practice: str
    mini_project: str


class RoadmapResponse(BaseModel):
    career_id: str
    weeks: List[RoadmapWeek]
    interview_questions: List[str]
    resume_bullets: List[str]


# ---------- Helpers ----------
def _career_by_id(cid: str) -> Optional[Dict[str, Any]]:
    for c in CAREERS:
        if c["id"] == cid:
            return c
    return None


def _skill_match_score(user_skills: List[str], career: Dict[str, Any]) -> float:
    """Simple match: fraction of required skills (across L1/L2/L3) the user already has."""
    required = set(sum([career["skills_required"]["L1"],
                        career["skills_required"]["L2"],
                        career["skills_required"]["L3"]], []))
    have = set([s.lower() for s in user_skills])
    if not required:
        return 0.0
    return len(required.intersection(have)) / len(required)


def _hours_score(hours: int) -> float:
    # 0..1 mapping; >=12 hrs/week is ideal
    return max(0.0, min(1.0, hours / 12.0))


def _market_score(cid: str) -> float:
    info = MARKET.get(cid)
    if not info:
        return 0.5
    # Normalize demand_score (0..10) to (0..1)
    return max(0.0, min(1.0, float(info.get("demand_score", 5.0)) / 10.0))


def _confidence(skill_match: float, market: float, hours: float) -> float:
    # Weighted sum → percentage
    score = 0.5 * skill_match + 0.3 * market + 0.2 * hours
    return round(score * 100.0, 1)


def _readiness_and_missing(user_skills: List[str], career: Dict[str, Any]) -> Tuple[float, List[str], Dict[str, List[str]]]:
    have = set([s.lower() for s in user_skills])
    missing_by_level = {}
    total_required = 0
    total_have = 0
    for level in ["L1", "L2", "L3"]:
        req = [s.lower() for s in career["skills_required"].get(level, [])]
        miss = [s for s in req if s not in have]
        missing_by_level[level] = miss
        total_required += len(req)
        total_have += len([s for s in req if s in have])
    readiness = (total_have / total_required * 100.0) if total_required else 0.0
    missing_flat = sum([missing_by_level["L1"], missing_by_level["L2"], missing_by_level["L3"]], [])
    return round(readiness, 1), missing_flat, missing_by_level


def _market_note(cid: str) -> str:
    info = MARKET.get(cid)
    if not info:
        return "Market data unavailable."
    return (f"Demand score {info['demand_score']}/10; growth {info['growth_rate']}; "
            f"avg time to hire ~{info['avg_time_to_hire_weeks']} weeks; "
            f"hot skills: {', '.join(info['hot_skills_up'])}.")


def _alternatives(career: Dict[str, Any]) -> List[str]:
    # Simple heuristics for alt paths
    title = career["title"].lower()
    if "analyst" in title and "data" in title:
        return ["Business Analyst (Entry)", "Analytics Engineer (Junior)"]
    if "designer" in title:
        return ["UX Research Intern", "Product Design Intern"]
    if "cybersecurity" in title or "soc" in title:
        return ["IT Support → SOC L1", "Cloud Fundamentals → Security"]
    return ["Internship route", "Freelance starter gigs"]


# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"ok": True, "careers_loaded": len(CAREERS)}


@app.post("/assess")
def assess(profile: ProfileInput):
    # Simple echo + derived traits
    derived = {
        "is_data_inclined": int(any(k in ' '.join(profile.interests).lower() for k in ["data", "numbers", "analysis"])),
        "is_design_inclined": int(any(k in ' '.join(profile.interests).lower() for k in ["design", "ui", "ux"])),
        "is_security_inclined": int(any(k in ' '.join(profile.interests).lower() for k in ["security", "cyber"])),
    }
    return {"profile": profile.model_dump(), "derived": derived}


@app.post("/recommend", response_model=RecommendResponse)
def recommend(profile: ProfileInput):
    items: List[RecommendationItem] = []
    for c in CAREERS:
        sm = _skill_match_score(profile.skills, c)
        hs = _hours_score(profile.hours_per_week)
        ms = _market_score(c["id"])
        conf = _confidence(sm, ms, hs)

        readiness, missing_flat, _ = _readiness_and_missing(profile.skills, c)

        rationale_bits = []
        if sm >= 0.4:
            rationale_bits.append("Your current skills align well with essentials for this role.")
        else:
            rationale_bits.append("You have a starting foundation and clear gaps to close.")

        if profile.hours_per_week >= 6:
            rationale_bits.append("Your weekly time commitment supports steady progress.")
        else:
            rationale_bits.append("With limited weekly time, we’ll prioritize the highest-impact skills.")

        market = _market_note(c["id"])
        alts = _alternatives(c)

        items.append(RecommendationItem(
            career_id=c["id"],
            title=c["title"],
            rationale=" ".join(rationale_bits),
            confidence_pct=conf,
            readiness_pct=readiness,
            missing_skills=missing_flat[:6],
            market_note=market,
            alternatives=alts
        ))

    # Sort by confidence, then readiness
    items.sort(key=lambda it: (it.confidence_pct, it.readiness_pct), reverse=True)
    return RecommendResponse(items=items[:3])


@app.post("/gap", response_model=GapResponse)
def gap(req: GapRequest):
    career = _career_by_id(req.career_id)
    if not career:
        return GapResponse(career_id=req.career_id, readiness_pct=0.0, missing_by_level={"L1": [], "L2": [], "L3": []})
    readiness, _, missing_by_level = _readiness_and_missing(req.skills, career)
    return GapResponse(career_id=req.career_id, readiness_pct=readiness, missing_by_level=missing_by_level)


@app.post("/roadmap", response_model=RoadmapResponse)
def roadmap(req: RoadmapRequest):
    career = _career_by_id(req.career_id)
    if not career:
        return RoadmapResponse(career_id=req.career_id, weeks=[], interview_questions=[], resume_bullets=[])

    # Stubbed deterministic plan (replace with Gemini later)
    base_focus = {
        "data_analyst": ["Excel & SQL basics", "Statistics basics", "Python/pandas", "Data cleaning",
                         "Visualization", "Storytelling", "Dashboarding", "Portfolio polish"],
        "ui_ux_designer": ["UX principles", "Figma basics", "Wireframing", "Prototyping",
                           "User research", "Usability testing", "Design systems", "Portfolio polish"],
        "cybersecurity_analyst": ["Linux & networks", "Security fundamentals", "SIEM basics", "Threat detection",
                                  "Scripting basics", "Incident response", "Vuln assessment", "Cloud security basics"]
    }
    focus = base_focus.get(req.career_id, ["Foundations", "Practice", "Project 1", "Project 2",
                                           "Intermediate", "Applied", "Capstone", "Polish"])

    weeks = []
    for i, f in enumerate(focus, start=1):
        weeks.append(RoadmapWeek(
            week=i,
            focus=f,
            resources=[
                "YouTube playlist (free) relevant to: " + f,
                "MOOC/Article (budget-friendly)"
            ],
            practice=f"Complete 2–3 exercises for: {f}",
            mini_project=f"Mini-project demonstrating: {f}"
        ))

    interview_qs = [
        "Tell me about a project you built recently and the trade-offs you made.",
        "Describe a challenging problem and how you approached it.",
        "How do you stay current with the field?",
        "Walk through your process for solving an unfamiliar task.",
        "Explain a concept from this domain to a non-expert."
    ]
    resume_bullets = [
        "Built a portfolio project demonstrating [[CORE SKILL]].",
        "Completed 8-week plan with consistent weekly deliverables.",
        "Developed practical understanding of [[DOMAIN]] tools and workflows."
    ]

    return RoadmapResponse(career_id=req.career_id, weeks=weeks,
                           interview_questions=interview_qs, resume_bullets=resume_bullets)
