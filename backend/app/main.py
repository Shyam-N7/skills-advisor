import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Render-friendly data loading
def load_json_data(filename: str, default_data: Any) -> Any:
    """Load JSON data with fallback to embedded defaults."""
    try:
        # Try to load from file first
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Try relative paths
        for path in [f"data/{filename}", f"../{filename}", f"../../data/{filename}"]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {filename}: {e}")
    
    return default_data

# Embedded fallback data (for when files aren't available)
FALLBACK_CAREERS = {
    "careers": [
        {
            "id": "data_analyst",
            "title": "Data Analyst",
            "summary": "Analyze data to produce insights, dashboards, and reports supporting business decisions.",
            "skills_required": {
                "L1": ["excel", "sql", "statistics_basics"],
                "L2": ["python", "pandas", "data_cleaning", "data_visualization"],
                "L3": ["storytelling", "dashboarding", "business_context"]
            },
            "salary_range_inr": {"junior": "4-7 LPA"}
        },
        {
            "id": "ui_ux_designer",
            "title": "UI/UX Designer",
            "summary": "Design user-centered interfaces, conduct research, create wireframes and prototypes.",
            "skills_required": {
                "L1": ["ux_principles", "visual_design_basics", "figma_basics"],
                "L2": ["wireframing", "prototyping", "user_research"],
                "L3": ["usability_testing", "design_systems", "handoff"]
            },
            "salary_range_inr": {"junior": "3.5-6 LPA"}
        },
        {
            "id": "cybersecurity_analyst",
            "title": "Cybersecurity Analyst",
            "summary": "Monitor and secure systems, identify vulnerabilities, respond to incidents.",
            "skills_required": {
                "L1": ["network_basics", "linux_basics", "security_fundamentals"],
                "L2": ["siem_basics", "threat_detection", "scripting_basics"],
                "L3": ["incident_response", "vulnerability_assessment", "cloud_security_basics"]
            },
            "salary_range_inr": {"junior": "4-7.5 LPA"}
        }
    ]
}

FALLBACK_MARKET = {
    "market": {
        "data_analyst": {
            "demand_score": 8.2,
            "growth_rate": "steady",
            "avg_time_to_hire_weeks": 6,
            "top_companies": ["TCS", "Accenture", "Flipkart", "Swiggy"],
            "hot_skills_up": ["sql", "excel", "python", "storytelling"]
        },
        "ui_ux_designer": {
            "demand_score": 7.5,
            "growth_rate": "rising",
            "avg_time_to_hire_weeks": 7,
            "top_companies": ["Zomato", "Paytm", "Zoho", "Freshworks"],
            "hot_skills_up": ["figma", "user_research", "prototyping"]
        },
        "cybersecurity_analyst": {
            "demand_score": 8.7,
            "growth_rate": "rising",
            "avg_time_to_hire_weeks": 5,
            "top_companies": ["Infosys", "Deloitte", "Wipro", "IBM"],
            "hot_skills_up": ["siem_basics", "linux", "incident_response"]
        }
    }
}

FALLBACK_QUIZ = {
    "questions": [
        {
            "id": "q1_interest",
            "text": "Which area interests you most?",
            "type": "single",
            "options": [
                "Working with data and numbers",
                "Designing user interfaces",
                "Cybersecurity and protecting systems"
            ]
        },
        {
            "id": "q2_hours",
            "text": "How many hours per week can you learn?",
            "type": "single",
            "options": ["<3", "3-5", "6-8", "9-12", "12+"]
        }
    ]
}

# Load data with fallbacks
CAREERS = load_json_data("careers_ontology.json", FALLBACK_CAREERS)["careers"]
MARKET = load_json_data("market_stub.json", FALLBACK_MARKET)["market"]
QUIZ_DATA = load_json_data("quiz_bank.json", FALLBACK_QUIZ)

# FastAPI app
app = FastAPI(
    title="Career Advisor Prototype API",
    version="0.2.0",
    description="AI-powered career guidance for Indian students"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class ProfileInput(BaseModel):
    interests: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    hours_per_week: int = Field(default=5, ge=1, le=40)
    budget_inr_per_month: int = Field(default=0, ge=0)
    city: str = Field(default="Other")
    learning_style: Optional[str] = Field(default="Videos")
    goal_text: Optional[str] = Field(default="")

class RecommendationItem(BaseModel):
    career_id: str
    title: str
    rationale: str
    confidence_pct: float = Field(ge=0, le=100)
    readiness_pct: float = Field(ge=0, le=100)
    missing_skills: List[str] = Field(default_factory=list)
    market_note: str
    alternatives: List[str] = Field(default_factory=list)
    estimated_timeline_months: int = Field(default=6)
    salary_range: str = Field(default="4-7 LPA")

class RecommendResponse(BaseModel):
    items: List[RecommendationItem]
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class GapRequest(BaseModel):
    career_id: str
    skills: List[str] = Field(default_factory=list)

class GapResponse(BaseModel):
    career_id: str
    career_title: str
    readiness_pct: float
    missing_by_level: Dict[str, List[str]]
    priority_skills: List[str] = Field(default_factory=list)

class RoadmapRequest(BaseModel):
    career_id: str
    hours_per_week: int = Field(default=5, ge=1, le=40)
    budget_inr_per_month: int = Field(default=0, ge=0)
    learning_style: Optional[str] = Field(default="Videos")

class RoadmapWeek(BaseModel):
    week: int
    focus: str
    resources: List[Dict[str, str]]
    practice: str
    mini_project: str

class RoadmapResponse(BaseModel):
    career_id: str
    career_title: str
    weeks: List[RoadmapWeek]
    interview_questions: List[str]
    resume_bullets: List[str]
    success_metrics: List[str] = Field(default_factory=list)

# Helper functions
def _career_by_id(cid: str) -> Optional[Dict[str, Any]]:
    for c in CAREERS:
        if c["id"] == cid:
            return c
    return None

def _skill_match_score(user_skills: List[str], career: Dict[str, Any]) -> float:
    if not career.get("skills_required"):
        return 0.0
    
    user_skills_lower = set(s.lower().strip() for s in user_skills)
    total_weight = 0
    matched_weight = 0
    
    level_weights = {"L1": 3, "L2": 2, "L3": 1}
    
    for level, weight in level_weights.items():
        required_skills = [s.lower().strip() for s in career["skills_required"].get(level, [])]
        total_weight += len(required_skills) * weight
        matched_skills = len([s for s in required_skills if s in user_skills_lower])
        matched_weight += matched_skills * weight
    
    return matched_weight / total_weight if total_weight > 0 else 0.0

def _hours_score(hours: int) -> float:
    if hours <= 3:
        return 0.3
    elif hours <= 6:
        return 0.6
    elif hours <= 10:
        return 0.8
    return 1.0

def _market_score(cid: str) -> float:
    info = MARKET.get(cid, {})
    demand = info.get("demand_score", 7.0)
    return max(0.0, min(1.0, demand / 10.0))

def _confidence_score(skill_match: float, market: float, hours: float, interests_match: float = 0.5) -> float:
    score = (0.4 * skill_match + 0.25 * market + 0.2 * hours + 0.15 * interests_match)
    return round(score * 100.0, 1)

def _readiness_and_missing(user_skills: List[str], career: Dict[str, Any]) -> Tuple[float, List[str], Dict[str, List[str]]]:
    user_skills_lower = set(s.lower().strip() for s in user_skills)
    missing_by_level = {}
    total_required = 0
    total_have = 0
    
    for level in ["L1", "L2", "L3"]:
        required_skills = [s.lower().strip() for s in career.get("skills_required", {}).get(level, [])]
        missing_skills = [s for s in required_skills if s not in user_skills_lower]
        missing_by_level[level] = missing_skills
        
        total_required += len(required_skills)
        total_have += len(required_skills) - len(missing_skills)
    
    readiness = (total_have / total_required * 100.0) if total_required > 0 else 0.0
    priority_missing = missing_by_level.get("L1", [])[:3]
    
    return round(readiness, 1), priority_missing, missing_by_level

def _market_note(cid: str) -> str:
    info = MARKET.get(cid, {})
    if not info:
        return "High growth field in India with good opportunities."
    
    companies = ", ".join(info.get("top_companies", [])[:3])
    return (f"Demand: {info.get('demand_score', 7)}/10 | "
            f"Growth: {info.get('growth_rate', 'steady')} | "
            f"Hiring time: ~{info.get('avg_time_to_hire_weeks', 6)} weeks | "
            f"Top companies: {companies}")

def _alternatives(career: Dict[str, Any]) -> List[str]:
    title_lower = career["title"].lower()
    if "data" in title_lower and "analyst" in title_lower:
        return ["Business Analyst", "Marketing Analyst", "Financial Analyst"]
    elif "designer" in title_lower:
        return ["Product Designer", "Visual Designer", "UX Researcher"]
    elif "cybersecurity" in title_lower:
        return ["Network Security", "Cloud Security", "Compliance Analyst"]
    return ["Related roles", "Internship opportunities", "Freelance path"]

def _generate_resources(focus: str, budget: int) -> List[Dict[str, str]]:
    resources = []
    if budget == 0:
        resources.extend([
            {"type": "Video", "name": f"YouTube: {focus} tutorials", "cost": "Free"},
            {"type": "Practice", "name": f"Free exercises for {focus}", "cost": "Free"}
        ])
    else:
        resources.extend([
            {"type": "Course", "name": f"Online course: {focus}", "cost": "₹500-1500"},
            {"type": "Book", "name": f"Book on {focus}", "cost": "₹300-800"}
        ])
    return resources

# API Endpoints
@app.get("/")
def root():
    return {
        "message": "Career Advisor Prototype API",
        "version": "0.2.0",
        "status": "running",
        "careers_available": len(CAREERS)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "careers_loaded": len(CAREERS),
        "market_data_available": len(MARKET) > 0,
        "quiz_questions": len(QUIZ_DATA.get("questions", [])),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/quiz")
def get_quiz():
    return {
        "questions": QUIZ_DATA.get("questions", []),
        "total_questions": len(QUIZ_DATA.get("questions", []))
    }

@app.post("/assess")
def assess_profile(profile: ProfileInput):
    interests_text = ' '.join(profile.interests).lower()
    
    derived_traits = {
        "data_oriented": int(any(keyword in interests_text for keyword in ["data", "numbers", "analysis"])),
        "design_oriented": int(any(keyword in interests_text for keyword in ["design", "ui", "ux"])),
        "security_oriented": int(any(keyword in interests_text for keyword in ["security", "cyber"])),
        "commitment_level": "High" if profile.hours_per_week >= 8 else "Medium" if profile.hours_per_week >= 5 else "Light"
    }
    
    strengths = []
    if profile.hours_per_week >= 8:
        strengths.append("High learning commitment")
    if len(profile.skills) >= 3:
        strengths.append("Good foundational skills")
    if profile.budget_inr_per_month > 1000:
        strengths.append("Investment ready")
    
    return {
        "profile": profile.model_dump(),
        "derived_traits": derived_traits,
        "strengths": strengths
    }

@app.post("/recommend", response_model=RecommendResponse)
def get_recommendations(profile: ProfileInput):
    if not CAREERS:
        raise HTTPException(status_code=500, detail="Career data not available")
    
    items = []
    interests_text = ' '.join(profile.interests).lower()
    
    for career in CAREERS:
        skill_match = _skill_match_score(profile.skills, career)
        hours_score = _hours_score(profile.hours_per_week)
        market_score = _market_score(career["id"])
        
        # Interest matching
        career_keywords = {
            "data_analyst": ["data", "numbers", "analysis"],
            "ui_ux_designer": ["design", "ui", "ux", "visual"],
            "cybersecurity_analyst": ["security", "cyber", "protect"]
        }
        
        interest_match = 0.8 if any(
            keyword in interests_text 
            for keyword in career_keywords.get(career["id"], [])
        ) else 0.3
        
        confidence = _confidence_score(skill_match, market_score, hours_score, interest_match)
        readiness, priority_missing, _ = _readiness_and_missing(profile.skills, career)
        
        rationale_parts = []
        if confidence >= 70:
            rationale_parts.append("Strong alignment with your profile.")
        elif confidence >= 50:
            rationale_parts.append("Good potential match with focused learning.")
        else:
            rationale_parts.append("Growing field with learning opportunities.")
        
        timeline_months = 6
        if readiness >= 70:
            timeline_months = 3
        elif readiness >= 40:
            timeline_months = 4
        else:
            timeline_months = 8
        
        items.append(RecommendationItem(
            career_id=career["id"],
            title=career["title"],
            rationale=" ".join(rationale_parts),
            confidence_pct=confidence,
            readiness_pct=readiness,
            missing_skills=priority_missing,
            market_note=_market_note(career["id"]),
            alternatives=_alternatives(career),
            estimated_timeline_months=timeline_months,
            salary_range=career.get("salary_range_inr", {}).get("junior", "4-7 LPA")
        ))
    
    items.sort(key=lambda x: (x.confidence_pct, x.readiness_pct), reverse=True)
    return RecommendResponse(items=items[:3])

@app.post("/gap", response_model=GapResponse)
def analyze_skill_gap(req: GapRequest):
    career = _career_by_id(req.career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Career '{req.career_id}' not found")
    
    readiness, priority_skills, missing_by_level = _readiness_and_missing(req.skills, career)
    
    return GapResponse(
        career_id=req.career_id,
        career_title=career["title"],
        readiness_pct=readiness,
        missing_by_level=missing_by_level,
        priority_skills=priority_skills
    )

@app.post("/roadmap", response_model=RoadmapResponse)
def generate_roadmap(req: RoadmapRequest):
    career = _career_by_id(req.career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Career '{req.career_id}' not found")
    
    roadmap_templates = {
        "data_analyst": [
            "Excel & SQL Fundamentals", "Statistics Basics", "Python Introduction",
            "Data Analysis with Pandas", "Data Visualization", "Business Storytelling",
            "Dashboard Creation", "Portfolio Building"
        ],
        "ui_ux_designer": [
            "UX Research Basics", "Figma Fundamentals", "Wireframing Skills",
            "Visual Design", "Prototyping", "User Testing",
            "Design Systems", "Portfolio Creation"
        ],
        "cybersecurity_analyst": [
            "Network Security Basics", "Linux Fundamentals", "Security Tools",
            "Threat Detection", "Incident Response", "Security Scripting",
            "Vulnerability Assessment", "Certification Prep"
        ]
    }
    
    focus_areas = roadmap_templates.get(req.career_id, [
        "Fundamentals", "Core Skills", "Practice", "Projects",
        "Advanced Skills", "Specialization", "Real Projects", "Career Prep"
    ])
    
    weeks = []
    for i, focus in enumerate(focus_areas, 1):
        resources = _generate_resources(focus, req.budget_inr_per_month)
        weeks.append(RoadmapWeek(
            week=i,
            focus=focus,
            resources=resources,
            practice=f"Complete 3-4 exercises for {focus}",
            mini_project=f"Build project demonstrating {focus}"
        ))
    
    interview_questions = [
        "Tell me about a project you built recently.",
        "How do you approach learning new technologies?",
        "Describe a challenge you overcame.",
        "Why are you interested in this field?",
        "How do you stay updated with industry trends?"
    ]
    
    resume_bullets = [
        f"Completed intensive 8-week {career['title']} program",
        f"Built portfolio of {len(weeks)} projects",
        f"Developed skills in key industry tools and practices"
    ]
    
    success_metrics = [
        "Complete all weekly projects",
        "Build a professional portfolio",
        "Pass practice interviews",
        "Network with industry professionals"
    ]
    
    return RoadmapResponse(
        career_id=req.career_id,
        career_title=career["title"],
        weeks=weeks,
        interview_questions=interview_questions,
        resume_bullets=resume_bullets,
        success_metrics=success_metrics
    )

# For Render deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)