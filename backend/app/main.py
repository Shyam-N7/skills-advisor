from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

app = FastAPI(title="Career Advisor API", version="1.0", description="AI-powered career guidance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Embedded data to avoid file dependencies
CAREERS_DATA = [
    {
        "id": "data_analyst",
        "title": "Data Analyst",
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
        "skills_required": {
            "L1": ["network_basics", "linux_basics", "security_fundamentals"],
            "L2": ["siem_basics", "threat_detection", "scripting_basics"],
            "L3": ["incident_response", "vulnerability_assessment", "cloud_security_basics"]
        },
        "salary_range_inr": {"junior": "4-7.5 LPA"}
    }
]

MARKET_DATA = {
    "data_analyst": {
        "demand_score": 8.2, "growth_rate": "steady", "avg_time_to_hire_weeks": 6,
        "top_companies": ["TCS", "Accenture", "Flipkart", "Swiggy"],
        "hot_skills_up": ["sql", "excel", "python", "storytelling"]
    },
    "ui_ux_designer": {
        "demand_score": 7.5, "growth_rate": "rising", "avg_time_to_hire_weeks": 7,
        "top_companies": ["Zomato", "Paytm", "Zoho", "Freshworks"],
        "hot_skills_up": ["figma", "user_research", "prototyping"]
    },
    "cybersecurity_analyst": {
        "demand_score": 8.7, "growth_rate": "rising", "avg_time_to_hire_weeks": 5,
        "top_companies": ["Infosys", "Deloitte", "Wipro", "IBM"],
        "hot_skills_up": ["siem_basics", "linux", "incident_response"]
    }
}

QUIZ_DATA = {
    "questions": [
        {
            "id": "q1_interest",
            "text": "Which area interests you most?",
            "type": "single",
            "options": ["Working with data and numbers", "Designing user interfaces", "Cybersecurity and protecting systems"]
        },
        {
            "id": "q2_hours", 
            "text": "How many hours per week can you learn?",
            "type": "single",
            "options": ["<3", "3-5", "6-8", "9-12", "12+"]
        }
    ]
}

def get_career_by_id(career_id: str):
    return next((c for c in CAREERS_DATA if c['id'] == career_id), None)

def calculate_skill_match(user_skills: List[str], career: Dict[str, Any]) -> float:
    """Calculate skill match score"""
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

def calculate_readiness(user_skills: List[str], career: Dict[str, Any]):
    """Calculate readiness and missing skills"""
    user_skills_lower = set(s.lower().strip() for s in user_skills)
    missing_by_level = {}
    total_required = 0
    total_have = 0
    
    for level in ["L1", "L2", "L3"]:
        required_skills = [s.lower().strip() for s in career["skills_required"].get(level, [])]
        missing_skills = [s for s in required_skills if s not in user_skills_lower]
        missing_by_level[level] = missing_skills
        
        total_required += len(required_skills)
        total_have += len(required_skills) - len(missing_skills)
    
    readiness = (total_have / total_required * 100.0) if total_required > 0 else 0.0
    priority_missing = missing_by_level.get("L1", [])[:3]
    
    return round(readiness, 1), priority_missing, missing_by_level

def get_market_note(career_id: str) -> str:
    """Generate market insight note"""
    info = MARKET_DATA.get(career_id, {})
    if not info:
        return "High growth field in India with good opportunities."
    
    companies = ", ".join(info.get("top_companies", [])[:3])
    return (f"Demand: {info.get('demand_score', 7)}/10 | "
            f"Growth: {info.get('growth_rate', 'steady')} | "
            f"Hiring time: ~{info.get('avg_time_to_hire_weeks', 6)} weeks | "
            f"Top companies: {companies}")

@app.get("/")
def root():
    return {
        "message": "Career Advisor Prototype API",
        "version": "1.0",
        "status": "running",
        "careers_available": len(CAREERS_DATA)
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "careers_loaded": len(CAREERS_DATA),
        "market_data_available": len(MARKET_DATA) > 0,
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
def assess_profile(profile: dict):
    """Assess user profile and derive traits"""
    interests_text = ' '.join(profile.get('interests', [])).lower()
    
    derived_traits = {
        "data_oriented": 1 if any(k in interests_text for k in ["data", "numbers", "analysis"]) else 0,
        "design_oriented": 1 if any(k in interests_text for k in ["design", "ui", "ux"]) else 0,
        "security_oriented": 1 if any(k in interests_text for k in ["security", "cyber"]) else 0,
        "commitment_level": "High" if profile.get('hours_per_week', 5) >= 8 else "Medium"
    }
    
    strengths = []
    if profile.get('hours_per_week', 5) >= 8:
        strengths.append("High learning commitment")
    if len(profile.get('skills', [])) >= 3:
        strengths.append("Good foundational skills")
    if profile.get('budget_inr_per_month', 0) > 1000:
        strengths.append("Investment ready")
    
    return {
        "profile": profile,
        "derived_traits": derived_traits,
        "strengths": strengths
    }

@app.post("/recommend")
def get_recommendations(profile: dict):
    """Generate career recommendations"""
    user_skills = profile.get('skills', [])
    interests = ' '.join(profile.get('interests', [])).lower()
    hours_per_week = profile.get('hours_per_week', 5)
    
    items = []
    
    for career in CAREERS_DATA:
        # Calculate scores
        skill_match = calculate_skill_match(user_skills, career)
        
        # Interest matching
        career_keywords = {
            "data_analyst": ["data", "numbers", "analysis"],
            "ui_ux_designer": ["design", "ui", "ux", "visual"],
            "cybersecurity_analyst": ["security", "cyber", "protect"]
        }
        
        interest_match = 0.8 if any(k in interests for k in career_keywords.get(career['id'], [])) else 0.3
        
        # Hours score
        hours_score = 1.0 if hours_per_week >= 10 else 0.8 if hours_per_week >= 6 else 0.5
        
        # Market score
        market_info = MARKET_DATA.get(career['id'], {})
        market_score = market_info.get('demand_score', 7.0) / 10.0
        
        # Overall confidence
        confidence = int((skill_match * 0.4 + interest_match * 0.25 + market_score * 0.2 + hours_score * 0.15) * 100)
        
        # Readiness calculation
        readiness, priority_missing, _ = calculate_readiness(user_skills, career)
        
        # Generate rationale
        if confidence >= 70:
            rationale = "Strong alignment with your profile and interests."
        elif confidence >= 50:
            rationale = "Good potential match with focused skill development."
        else:
            rationale = "Growing field with learning opportunities."
        
        # Timeline estimation
        timeline_months = 3 if readiness >= 70 else 4 if readiness >= 40 else 6
        
        items.append({
            "career_id": career['id'],
            "title": career['title'],
            "confidence_pct": confidence,
            "readiness_pct": readiness,
            "rationale": rationale,
            "missing_skills": priority_missing,
            "market_note": get_market_note(career['id']),
            "alternatives": ["Related roles", "Internship path", "Freelance opportunities"],
            "estimated_timeline_months": timeline_months,
            "salary_range": career['salary_range_inr']['junior']
        })
    
    # Sort by confidence
    items.sort(key=lambda x: x['confidence_pct'], reverse=True)
    
    return {
        "items": items[:3],
        "generated_at": datetime.now().isoformat()
    }

@app.post("/gap")
def analyze_skill_gap(request: dict):
    """Analyze skill gaps for a specific career"""
    career_id = request.get('career_id')
    user_skills = request.get('skills', [])
    
    career = get_career_by_id(career_id)
    if not career:
        return {"error": "Career not found"}
    
    readiness, priority_skills, missing_by_level = calculate_readiness(user_skills, career)
    
    return {
        "career_id": career_id,
        "career_title": career['title'],
        "readiness_pct": readiness,
        "missing_by_level": missing_by_level,
        "priority_skills": priority_skills
    }

@app.post("/roadmap")
def generate_roadmap(request: dict):
    """Generate 8-week learning roadmap"""
    career_id = request.get('career_id')
    hours_per_week = request.get('hours_per_week', 5)
    budget = request.get('budget_inr_per_month', 0)
    
    career = get_career_by_id(career_id)
    if not career:
        return {"error": "Career not found"}
    
    # Roadmap templates
    roadmap_templates = {
        "data_analyst": [
            "Excel & SQL Fundamentals", "Statistics Basics", "Python Introduction",
            "Data Analysis with Pandas", "Data Visualization", "Business Storytelling",
            "Dashboard Creation", "Portfolio Building"
        ],
        "ui_ux_designer": [
            "UX Research Basics", "Figma Fundamentals", "Wireframing Skills",
            "Visual Design Principles", "Prototyping", "User Testing",
            "Design Systems", "Portfolio Creation"
        ],
        "cybersecurity_analyst": [
            "Network Security Basics", "Linux Fundamentals", "Security Tools",
            "Threat Detection", "Incident Response", "Security Scripting",
            "Vulnerability Assessment", "Certification Prep"
        ]
    }
    
    focus_areas = roadmap_templates.get(career_id, [
        "Week 1 Focus", "Week 2 Focus", "Week 3 Focus", "Week 4 Focus",
        "Week 5 Focus", "Week 6 Focus", "Week 7 Focus", "Week 8 Focus"
    ])
    
    weeks = []
    for i, focus in enumerate(focus_areas, 1):
        # Generate resources based on budget
        resources = []
        if budget == 0:
            resources = [
                {"type": "Video", "name": f"YouTube tutorials: {focus}", "cost": "Free"},
                {"type": "Practice", "name": f"Free exercises for {focus}", "cost": "Free"}
            ]
        else:
            resources = [
                {"type": "Course", "name": f"Online course: {focus}", "cost": "₹500-1500"},
                {"type": "Book", "name": f"Reference book: {focus}", "cost": "₹300-800"}
            ]
        
        weeks.append({
            "week": i,
            "focus": focus,
            "resources": resources,
            "practice": f"Complete 3-4 exercises on {focus}",
            "mini_project": f"Build a small project demonstrating {focus}"
        })
    
    interview_questions = [
        "Tell me about a recent project you worked on.",
        "How do you approach learning new technologies?",
        "Describe a challenging problem you solved.",
        "Why are you interested in this field?",
        "How do you stay updated with industry trends?"
    ]
    
    resume_bullets = [
        f"Completed intensive 8-week {career['title']} program",
        f"Built portfolio with {len(weeks)} practical projects",
        "Developed industry-relevant skills and practical experience"
    ]
    
    success_metrics = [
        "Complete all weekly projects",
        "Build a professional portfolio",
        "Practice mock interviews",
        "Network with industry professionals"
    ]
    
    return {
        "career_id": career_id,
        "career_title": career['title'],
        "weeks": weeks,
        "interview_questions": interview_questions,
        "resume_bullets": resume_bullets,
        "success_metrics": success_metrics
    }

# For deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)