import json
import math
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Get the absolute path to the data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))

# Load data files with error handling
try:
    with open(os.path.join(DATA_DIR, "careers_ontology.json"), "r", encoding="utf-8") as f:
        CAREERS = json.load(f)["careers"]
except FileNotFoundError:
    CAREERS = []

try:
    with open(os.path.join(DATA_DIR, "market_stub.json"), "r", encoding="utf-8") as f:
        MARKET = json.load(f)["market"]
except FileNotFoundError:
    MARKET = {}

try:
    with open(os.path.join(DATA_DIR, "quiz_bank.json"), "r", encoding="utf-8") as f:
        QUIZ_DATA = json.load(f)
except FileNotFoundError:
    QUIZ_DATA = {"questions": []}

app = FastAPI(title="Career Advisor Prototype API", version="0.2.0", description="AI-powered career guidance for Indian students")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Enhanced Schemas ----------
class ProfileInput(BaseModel):
    interests: List[str] = Field(default_factory=list, description="User's career interests")
    skills: List[str] = Field(default_factory=list, description="Current skills")
    hours_per_week: int = Field(default=5, ge=1, le=40, description="Learning hours per week")
    budget_inr_per_month: int = Field(default=0, ge=0, description="Monthly learning budget in INR")
    city: str = Field(default="Other", description="Current city")
    learning_style: Optional[str] = Field(default="Videos", description="Preferred learning style")
    goal_text: Optional[str] = Field(default="", description="Career goal description")
    experience_level: Optional[str] = Field(default="Beginner", description="Current experience level")


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
    estimated_time_to_ready: str = Field(default="3-6 months")


class RoadmapRequest(BaseModel):
    career_id: str
    hours_per_week: int = Field(default=5, ge=1, le=40)
    budget_inr_per_month: int = Field(default=0, ge=0)
    learning_style: Optional[str] = Field(default="Videos")
    current_skills: List[str] = Field(default_factory=list)


class RoadmapWeek(BaseModel):
    week: int
    focus: str
    resources: List[Dict[str, str]]  # Enhanced with resource details
    practice: str
    mini_project: str
    time_allocation: str = Field(default="5-7 hours")


class RoadmapResponse(BaseModel):
    career_id: str
    career_title: str
    weeks: List[RoadmapWeek]
    interview_questions: List[str]
    resume_bullets: List[str]
    total_estimated_cost: str = Field(default="₹0-2000")
    success_metrics: List[str] = Field(default_factory=list)


class QuizResponse(BaseModel):
    questions: List[Dict[str, Any]]
    total_questions: int


class ProfileAssessment(BaseModel):
    profile: Dict[str, Any]
    derived_traits: Dict[str, Any]
    strengths: List[str] = Field(default_factory=list)
    recommendations_preview: List[str] = Field(default_factory=list)


# ---------- Enhanced Helper Functions ----------
def _career_by_id(cid: str) -> Optional[Dict[str, Any]]:
    """Find career by ID with error handling."""
    for c in CAREERS:
        if c["id"] == cid:
            return c
    return None


def _skill_match_score(user_skills: List[str], career: Dict[str, Any]) -> float:
    """Calculate skill match score with weighted levels."""
    if not career.get("skills_required"):
        return 0.0
        
    user_skills_lower = set(s.lower().strip() for s in user_skills)
    total_weight = 0
    matched_weight = 0
    
    # Weight L1 skills higher (they're more fundamental)
    level_weights = {"L1": 3, "L2": 2, "L3": 1}
    
    for level, weight in level_weights.items():
        required_skills = [s.lower().strip() for s in career["skills_required"].get(level, [])]
        total_weight += len(required_skills) * weight
        matched_skills = len([s for s in required_skills if s in user_skills_lower])
        matched_weight += matched_skills * weight
    
    return matched_weight / total_weight if total_weight > 0 else 0.0


def _hours_score(hours: int) -> float:
    """Score based on available learning hours."""
    if hours <= 3:
        return 0.3
    elif hours <= 6:
        return 0.6
    elif hours <= 10:
        return 0.8
    else:
        return 1.0


def _market_score(cid: str) -> float:
    """Get market demand score."""
    info = MARKET.get(cid, {})
    demand = info.get("demand_score", 5.0)
    return max(0.0, min(1.0, demand / 10.0))


def _confidence_score(skill_match: float, market: float, hours: float, interests_match: float = 0.5) -> float:
    """Calculate overall confidence with multiple factors."""
    score = (0.4 * skill_match + 0.25 * market + 0.2 * hours + 0.15 * interests_match)
    return round(score * 100.0, 1)


def _readiness_and_missing(user_skills: List[str], career: Dict[str, Any]) -> Tuple[float, List[str], Dict[str, List[str]]]:
    """Enhanced readiness calculation with priority skills."""
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
    
    # Priority is L1 skills first
    priority_missing = missing_by_level.get("L1", [])[:3]
    all_missing = sum(missing_by_level.values(), [])
    
    return round(readiness, 1), priority_missing, missing_by_level


def _enhanced_market_note(cid: str) -> str:
    """Enhanced market information."""
    info = MARKET.get(cid, {})
    if not info:
        return "Market data being updated - high growth field in India."
    
    companies = ", ".join(info.get("top_companies", [])[:3])
    return (f"Demand: {info.get('demand_score', 7)}/10 | "
            f"Growth: {info.get('growth_rate', 'steady')} | "
            f"Avg hire time: ~{info.get('avg_time_to_hire_weeks', 6)} weeks | "
            f"Top hirers: {companies}")


def _get_enhanced_alternatives(career: Dict[str, Any]) -> List[str]:
    """Get alternative career paths."""
    title_lower = career["title"].lower()
    
    if "data" in title_lower and "analyst" in title_lower:
        return ["Business Intelligence Analyst", "Marketing Analyst", "Financial Analyst"]
    elif "designer" in title_lower:
        return ["Product Designer", "Visual Designer", "UX Researcher"]
    elif "cybersecurity" in title_lower or "security" in title_lower:
        return ["Network Security Specialist", "Cloud Security Engineer", "Compliance Analyst"]
    else:
        return ["Related internship roles", "Freelance opportunities", "Certification programs"]


def _generate_enhanced_resources(focus: str, budget: int, learning_style: str) -> List[Dict[str, str]]:
    """Generate contextual learning resources."""
    resources = []
    
    if budget == 0:  # Free resources
        resources.extend([
            {"type": "Video", "name": f"YouTube: {focus} fundamentals", "cost": "Free"},
            {"type": "Practice", "name": f"Free online exercises for {focus}", "cost": "Free"}
        ])
    else:
        resources.extend([
            {"type": "Course", "name": f"Udemy/Coursera: {focus} course", "cost": "₹500-1500"},
            {"type": "Book", "name": f"Recommended book on {focus}", "cost": "₹300-800"}
        ])
    
    if learning_style == "Hands-on practice":
        resources.append({"type": "Project", "name": f"Build a {focus} project", "cost": "Free"})
    
    return resources


# ---------- API Endpoints ----------
@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "message": "Career Advisor Prototype API",
        "version": "0.2.0",
        "features": ["Profile Assessment", "Career Recommendations", "Skill Gap Analysis", "Learning Roadmaps"],
        "endpoints": ["/health", "/quiz", "/assess", "/recommend", "/gap", "/roadmap"]
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "careers_loaded": len(CAREERS),
        "market_data_available": len(MARKET) > 0,
        "quiz_questions": len(QUIZ_DATA.get("questions", [])),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/quiz", response_model=QuizResponse)
def get_quiz():
    """Get assessment quiz questions."""
    return QuizResponse(
        questions=QUIZ_DATA.get("questions", []),
        total_questions=len(QUIZ_DATA.get("questions", []))
    )


@app.post("/assess", response_model=ProfileAssessment)
def assess_profile(profile: ProfileInput):
    """Enhanced profile assessment with insights."""
    
    # Derive traits from interests and skills
    interests_text = ' '.join(profile.interests).lower()
    skills_text = ' '.join(profile.skills).lower()
    
    derived_traits = {
        "data_oriented": int(any(keyword in interests_text for keyword in ["data", "numbers", "analysis", "statistics"])),
        "design_oriented": int(any(keyword in interests_text for keyword in ["design", "ui", "ux", "visual"])),
        "security_oriented": int(any(keyword in interests_text for keyword in ["security", "cyber", "protect"])),
        "technical_skills": len([s for s in profile.skills if s in ["python", "sql", "linux", "figma"]]),
        "commitment_level": "High" if profile.hours_per_week >= 8 else "Medium" if profile.hours_per_week >= 5 else "Light"
    }
    
    # Generate strengths
    strengths = []
    if profile.hours_per_week >= 8:
        strengths.append("High learning commitment")
    if len(profile.skills) >= 3:
        strengths.append("Good foundational skills")
    if profile.budget_inr_per_month > 1000:
        strengths.append("Investment ready for premium resources")
    if profile.goal_text:
        strengths.append("Clear goal orientation")
    
    # Quick recommendations preview
    recommendations_preview = []
    if derived_traits["data_oriented"]:
        recommendations_preview.append("Data Analyst roles match your interests")
    if derived_traits["design_oriented"]:
        recommendations_preview.append("UI/UX Designer path looks promising")
    if derived_traits["security_oriented"]:
        recommendations_preview.append("Cybersecurity field aligns with your interests")
    
    return ProfileAssessment(
        profile=profile.model_dump(),
        derived_traits=derived_traits,
        strengths=strengths,
        recommendations_preview=recommendations_preview
    )


@app.post("/recommend", response_model=RecommendResponse)
def get_recommendations(profile: ProfileInput):
    """Generate top career recommendations."""
    if not CAREERS:
        raise HTTPException(status_code=500, detail="Career data not available")
    
    items = []
    interests_text = ' '.join(profile.interests).lower()
    
    for career in CAREERS:
        # Calculate various scores
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
        
        # Generate rationale
        rationale_parts = []
        if confidence >= 70:
            rationale_parts.append("Strong alignment with your profile.")
        elif confidence >= 50:
            rationale_parts.append("Good potential match with some skill building.")
        else:
            rationale_parts.append("Emerging opportunity requiring focused learning.")
        
        if profile.hours_per_week >= 8:
            rationale_parts.append("Your time commitment supports rapid progress.")
        
        # Timeline estimation
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
            market_note=_enhanced_market_note(career["id"]),
            alternatives=_get_enhanced_alternatives(career),
            estimated_timeline_months=timeline_months,
            salary_range=career.get("salary_range_inr", {}).get("junior", "4-7 LPA")
        ))
    
    # Sort by confidence, then readiness
    items.sort(key=lambda x: (x.confidence_pct, x.readiness_pct), reverse=True)
    
    return RecommendResponse(items=items[:3])


@app.post("/gap", response_model=GapResponse)
def analyze_skill_gap(req: GapRequest):
    """Detailed skill gap analysis."""
    career = _career_by_id(req.career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Career ID '{req.career_id}' not found")
    
    readiness, priority_skills, missing_by_level = _readiness_and_missing(req.skills, career)
    
    # Estimate time to ready
    total_missing = sum(len(skills) for skills in missing_by_level.values())
    if total_missing <= 3:
        time_estimate = "2-3 months"
    elif total_missing <= 6:
        time_estimate = "4-6 months"
    else:
        time_estimate = "6-12 months"
    
    return GapResponse(
        career_id=req.career_id,
        career_title=career["title"],
        readiness_pct=readiness,
        missing_by_level=missing_by_level,
        priority_skills=priority_skills,
        estimated_time_to_ready=time_estimate
    )


@app.post("/roadmap", response_model=RoadmapResponse)
def generate_roadmap(req: RoadmapRequest):
    """Generate detailed 8-week learning roadmap."""
    career = _career_by_id(req.career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Career ID '{req.career_id}' not found")
    
    # Enhanced roadmap templates
    roadmap_templates = {
        "data_analyst": [
            "Excel & Data Fundamentals", "SQL Basics & Practice", "Statistics & Analytics",
            "Python & Pandas", "Data Visualization", "Business Context & Storytelling",
            "Dashboard Building", "Portfolio & Interview Prep"
        ],
        "ui_ux_designer": [
            "UX Principles & Research", "Figma Basics", "Wireframing & User Flows",
            "Visual Design Fundamentals", "Prototyping & Testing", "Design Systems",
            "Advanced Figma & Handoff", "Portfolio & Case Studies"
        ],
        "cybersecurity_analyst": [
            "Networking & Linux Basics", "Security Fundamentals", "SIEM Tools Introduction",
            "Threat Detection Basics", "Incident Response", "Scripting for Security",
            "Vulnerability Assessment", "Certification Prep & Portfolio"
        ]
    }
    
    focus_areas = roadmap_templates.get(
        req.career_id,
        ["Fundamentals", "Core Skills", "Practice", "Projects", "Advanced Topics", 
         "Specialization", "Real-world Application", "Career Preparation"]
    )
    
    weeks = []
    for i, focus in enumerate(focus_areas, 1):
        resources = _generate_enhanced_resources(focus, req.budget_inr_per_month, req.learning_style)
        
        weeks.append(RoadmapWeek(
            week=i,
            focus=focus,
            resources=resources,
            practice=f"Complete 3-4 hands-on exercises for {focus}. Join online communities for peer learning.",
            mini_project=f"Build a mini-project demonstrating {focus}. Document your learning process.",
            time_allocation=f"{req.hours_per_week} hours spread across 4-5 days"
        ))
    
    # Enhanced interview questions
    interview_questions = [
        "Walk me through a recent project and the challenges you overcame.",
        "How do you approach learning new technologies in this field?",
        "Describe a time when you had to explain technical concepts to a non-technical audience.",
        "What interests you most about this role and our company?",
        "How do you stay updated with industry trends and best practices?"
    ]
    
    # Enhanced resume bullets
    resume_bullets = [
        f"Completed intensive 8-week {career['title']} program with hands-on projects",
        f"Built portfolio of {len(weeks)} projects demonstrating proficiency in key tools",
        f"Developed practical skills in {', '.join(career.get('skills_required', {}).get('L1', [])[:3])}"
    ]
    
    # Success metrics
    success_metrics = [
        f"Complete all {len(weeks)} weekly projects",
        "Build a portfolio with 3+ substantial projects",
        "Pass mock interviews with 70%+ confidence",
        "Network with 10+ professionals in the field"
    ]
    
    return RoadmapResponse(
        career_id=req.career_id,
        career_title=career["title"],
        weeks=weeks,
        interview_questions=interview_questions,
        resume_bullets=resume_bullets,
        total_estimated_cost=f"₹{req.budget_inr_per_month * 2}-{req.budget_inr_per_month * 2 + 3000}",
        success_metrics=success_metrics
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)