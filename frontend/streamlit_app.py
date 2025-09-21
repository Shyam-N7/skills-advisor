import json
import requests
import streamlit as st
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="AI Career Advisor - Find Your Perfect Tech Career",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .recommendation-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: black;
        background: #fafafa;
    }
    .success-metric {
        background: #d4edda;
        color: #fff;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        border-left: 4px solid #28a745;
    }
    .roadmap-week {
        background: #f8f9fa;
        color: black;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar configuration
st.sidebar.title("Settings")
backend_url = st.sidebar.text_input(
    "Backend URL", 
    value="http://localhost:8000",
    help="Change this to your deployed API URL"
)

# Test backend connection
try:
    response = requests.get(f"{backend_url}/health", timeout=5)
    if response.status_code == 200:
        health_data = response.json()
        st.sidebar.success(f"Backend Connected")
        st.sidebar.json({
            "Status": health_data.get("status", "unknown"),
            "Careers": health_data.get("careers_loaded", 0),
            "Quiz Questions": health_data.get("quiz_questions", 0)
        })
    else:
        st.sidebar.error("Backend connection failed")
except Exception as e:
    st.sidebar.error(f"Connection Error: {str(e)[:50]}...")

# Main header
st.markdown("""
<div class="main-header">
    <h1>AI Career Advisor</h1>
    <h3>Discover Your Perfect Tech Career Path in India</h3>
    <p>Get personalized recommendations, skill gap analysis, and 8-week learning roadmaps</p>
</div>
""", unsafe_allow_html=True)

# Create tabs for different features
tab1, tab2, tab3 = st.tabs(["Career Discovery", "Skill Analysis", "Learning Roadmap"])

with tab1:
    st.header("Find Your Ideal Career Path")
    
    # Feature 1: Enhanced Profile Assessment & Recommendations
    with st.form("profile_form", clear_on_submit=False):
        st.subheader("Tell Us About Yourself")
        
        col1, col2 = st.columns(2)
        
        with col1:
            interests = st.multiselect(
                "What interests you most?",
                [
                    "Working with data and numbers",
                    "Designing user interfaces", 
                    "Cybersecurity and protecting systems",
                    "Problem solving and analysis",
                    "Creative and visual work",
                    "Technology and programming"
                ],
                help="Select all that apply - this helps us understand your natural inclinations"
            )
            
            skills = st.multiselect(
                "Current Skills (select what you know)",
                [
                    "excel", "sql", "statistics_basics", "python", "pandas", 
                    "data_visualization", "ux_principles", "visual_design_basics",
                    "figma_basics", "wireframing", "prototyping", "linux_basics",
                    "network_basics", "security_fundamentals", "siem_basics",
                    "scripting_basics"
                ],
                help="Be honest - we'll help you bridge any gaps"
            )
            
            experience_level = st.selectbox(
                "Your Experience Level",
                ["Complete Beginner", "Some Exposure", "Basic Skills", "Intermediate"]
            )
        
        with col2:
            hours = st.slider(
                "Learning Hours per Week",
                min_value=2, max_value=25, value=8,
                help="How much time can you realistically commit?"
            )
            
            budget = st.selectbox(
                "Monthly Learning Budget (INR)",
                ["0 (Free resources only)", "500-1500", "1500-3500", "3500+"]
            )
            budget_map = {"0 (Free resources only)": 0, "500-1500": 1000, "1500-3500": 2500, "3500+": 5000}
            
            city = st.selectbox(
                "Your Location",
                ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Mumbai", "Chennai", "Other"]
            )
            
            learning_style = st.selectbox(
                "Preferred Learning Style",
                ["Videos & Tutorials", "Reading & Documentation", "Hands-on Projects", "Mixed Approach"]
            )
        
        goal_text = st.text_area(
            "Your Career Goal (Optional)",
            placeholder="e.g., Get a data analyst job at a tech company in 6 months, transition from non-tech to UX design...",
            help="The more specific, the better we can help you"
        )
        
        submitted = st.form_submit_button("Get My Career Recommendations", use_container_width=True)

    if submitted:
        profile_data = {
            "interests": interests,
            "skills": skills,
            "hours_per_week": hours,
            "budget_inr_per_month": budget_map[budget],
            "city": city,
            "learning_style": learning_style,
            "goal_text": goal_text,
            "experience_level": experience_level
        }
        
        # Show loading spinner
        with st.spinner("AI is analyzing your profile..."):
            time.sleep(1)  # Small delay for better UX
            
            try:
                # Get profile assessment
                assessment = requests.post(f"{backend_url}/assess", json=profile_data, timeout=15).json()
                
                # Get recommendations
                recommendations = requests.post(f"{backend_url}/recommend", json=profile_data, timeout=30).json()
                
                # Display assessment results
                st.success("Profile Analysis Complete!")
                
                st.subheader("Your Profile Insights")
                col1, col2, col3, col4 = st.columns(4)
                
                derived = assessment.get("derived_traits", {})
                with col1:
                    st.metric("Data Orientation", "High" if derived.get("data_oriented") else "Medium")
                with col2:
                    st.metric("Design Inclination", "High" if derived.get("design_oriented") else "Medium")  
                with col3:
                    st.metric("Security Interest", "High" if derived.get("security_oriented") else "Medium")
                with col4:
                    st.metric("Commitment Level", derived.get("commitment_level", "Medium"))
                
                if assessment.get("strengths"):
                    st.write("**Your Strengths:**")
                    for strength in assessment["strengths"]:
                        st.write(f"{strength}")
                
                # Display recommendations
                st.subheader("Your Top Career Matches")
                
                for idx, item in enumerate(recommendations.get("items", []), 1):
                    with st.container():
                        st.markdown(f"""
                        <div class="recommendation-card">
                            <h3>#{idx}. {item['title']}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([1, 1, 2])
                        
                        with col1:
                            st.metric("Confidence", f"{item['confidence_pct']}%", 
                                    delta=f"{item['confidence_pct'] - 50:.1f}" if item['confidence_pct'] > 50 else None)
                        
                        with col2:
                            st.metric("Readiness", f"{item['readiness_pct']}%",
                                    delta=f"{item['readiness_pct'] - 30:.1f}" if item['readiness_pct'] > 30 else None)
                        
                        with col3:
                            st.write(f"**Timeline:** {item.get('estimated_timeline_months', 6)} months")
                            st.write(f"**Salary Range:** {item.get('salary_range', '4-7 LPA')}")
                        
                        st.write(f"**Why this fits:** {item['rationale']}")
                        st.info(f"**Market Insight:** {item['market_note']}")
                        
                        if item.get("missing_skills"):
                            st.write(f"**Next skills to learn:** {', '.join(item['missing_skills'][:5])}")
                        
                        if item.get("alternatives"):
                            st.write(f"**Alternative paths:** {', '.join(item['alternatives'][:3])}")
                        
                        # Store recommendation data in session state for other tabs
                        if f"rec_{idx}" not in st.session_state:
                            st.session_state[f"rec_{idx}"] = item
                            st.session_state[f"profile_data"] = profile_data
                        
                        st.divider()
                
            except Exception as e:
                st.error(f"Error getting recommendations: {str(e)}")
                st.info("Make sure your backend is running and accessible")

with tab2:
    st.header("Detailed Skill Gap Analysis")
    st.write("Select a career to see your detailed skill gaps and readiness assessment")
    
    # Feature 2: Advanced Skill Gap Analysis
    career_options = {
        "data_analyst": "Data Analyst",
        "ui_ux_designer": "UI/UX Designer", 
        "cybersecurity_analyst": "Cybersecurity Analyst"
    }
    
    selected_career = st.selectbox(
        "Choose a career to analyze:",
        options=list(career_options.keys()),
        format_func=lambda x: career_options[x]
    )
    
    # Get current skills from session state or let user input
    if "profile_data" in st.session_state:
        current_skills = st.session_state["profile_data"]["skills"]
        st.write(f"**Using your skills from the assessment:** {', '.join(current_skills) if current_skills else 'No skills selected'}")
    else:
        current_skills = st.multiselect(
            "Select your current skills:",
            [
                "excel", "sql", "statistics_basics", "python", "pandas", 
                "data_visualization", "ux_principles", "visual_design_basics",
                "figma_basics", "wireframing", "prototyping", "linux_basics",
                "network_basics", "security_fundamentals", "siem_basics"
            ]
        )
    
    if st.button("Analyze My Skill Gaps", use_container_width=True):
        with st.spinner("Analyzing your skill gaps..."):
            try:
                gap_request = {
                    "career_id": selected_career,
                    "skills": current_skills
                }
                
                gap_response = requests.post(f"{backend_url}/gap", json=gap_request, timeout=15).json()
                
                st.success(f"Analysis complete for {gap_response['career_title']}")
                
                # Overall readiness
                col1, col2, col3 = st.columns(3)
                with col1:
                    readiness = gap_response['readiness_pct']
                    st.markdown(f"""
                    <div class="metric-container">
                        <h2>{readiness:.1f}%</h2>
                        <p>Overall Readiness</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-container">
                        <h3>{gap_response.get('estimated_time_to_ready', '4-6 months')}</h3>
                        <p>Time to Job-Ready</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    priority_count = len(gap_response.get('priority_skills', []))
                    st.markdown(f"""
                    <div class="metric-container">
                        <h3>{priority_count}</h3>
                        <p>Priority Skills to Learn</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Detailed breakdown by skill level
                st.subheader("Skill Gap Breakdown")
                
                missing_by_level = gap_response.get('missing_by_level', {})
                
                for level in ['L1', 'L2', 'L3']:
                    level_names = {
                        'L1': 'Foundation Skills',
                        'L2': 'Intermediate Skills', 
                        'L3': 'Advanced Skills'
                    }
                    
                    missing_skills = missing_by_level.get(level, [])
                    if missing_skills:
                        with st.expander(f"{level_names[level]} - {len(missing_skills)} skills needed"):
                            for skill in missing_skills:
                                st.write(f"• {skill.replace('_', ' ').title()}")
                    else:
                        st.success(f"{level_names[level]} - Complete!")
                
                # Priority recommendations
                if gap_response.get('priority_skills'):
                    st.subheader("Start With These Skills")
                    st.write("These are the most important skills to focus on first:")
                    
                    for i, skill in enumerate(gap_response['priority_skills'][:3], 1):
                        st.write(f"{i}. **{skill.replace('_', ' ').title()}** - Foundation skill")
                
                # Store gap analysis in session state
                st.session_state['gap_analysis'] = gap_response
                st.session_state['selected_career'] = selected_career
                
            except Exception as e:
                st.error(f"Error analyzing skill gaps: {str(e)}")

with tab3:
    st.header("Personalized Learning Roadmap")
    st.write("Get a detailed 8-week plan to build the skills you need")
    
    # Feature 3: Comprehensive Learning Roadmap
    with st.form("roadmap_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            roadmap_career = st.selectbox(
                "Select Career Path:",
                options=list(career_options.keys()),
                format_func=lambda x: career_options[x],
                key="roadmap_career"
            )
            
            roadmap_hours = st.slider(
                "Weekly Learning Hours:",
                min_value=3, max_value=20, value=8,
                key="roadmap_hours"
            )
        
        with col2:
            roadmap_budget = st.selectbox(
                "Monthly Budget (INR):",
                ["0", "1000", "2500", "5000"],
                key="roadmap_budget"
            )
            
            roadmap_style = st.selectbox(
                "Learning Style:",
                ["Videos", "Reading articles", "Hands-on practice"],
                key="roadmap_style"
            )
        
        roadmap_skills = st.multiselect(
            "Your Current Skills:",
            [
                "excel", "sql", "statistics_basics", "python", "pandas", 
                "data_visualization", "ux_principles", "visual_design_basics",
                "figma_basics", "wireframing", "prototyping", "linux_basics",
                "network_basics", "security_fundamentals", "siem_basics"
            ],
            default=st.session_state.get("profile_data", {}).get("skills", []),
            key="roadmap_skills"
        )
        
        generate_roadmap = st.form_submit_button("Generate My 8-Week Roadmap", use_container_width=True)
    
    if generate_roadmap:
        with st.spinner("Creating your personalized roadmap..."):
            try:
                roadmap_request = {
                    "career_id": roadmap_career,
                    "hours_per_week": roadmap_hours,
                    "budget_inr_per_month": int(roadmap_budget),
                    "learning_style": roadmap_style,
                    "current_skills": roadmap_skills
                }
                
                roadmap_response = requests.post(f"{backend_url}/roadmap", json=roadmap_request, timeout=30).json()
                
                st.success(f"Your personalized roadmap for {roadmap_response['career_title']} is ready!")
                
                # Roadmap overview
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Duration", "8 weeks")
                with col2:
                    st.metric("Weekly Commitment", f"{roadmap_hours} hours")
                with col3:
                    st.metric("Estimated Cost", roadmap_response.get('total_estimated_cost', '₹1000-3000'))
                
                # Weekly breakdown
                st.subheader("Weekly Learning Plan")
                
                for week_data in roadmap_response.get('weeks', []):
                    with st.expander(f"Week {week_data['week']}: {week_data['focus']}", expanded=week_data['week'] <= 2):
                        st.markdown(f"""
                        <div class="roadmap-week">
                            <h4>Focus: {week_data['focus']}</h4>
                            <p><strong>Time Allocation:</strong> {week_data.get('time_allocation', '5-7 hours')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Resources:**")
                            for resource in week_data.get('resources', []):
                                if isinstance(resource, dict):
                                    st.write(f"• **{resource.get('type', 'Resource')}:** {resource.get('name', 'N/A')} - *{resource.get('cost', 'Free')}*")
                                else:
                                    st.write(f"• {resource}")
                        
                        with col2:
                            st.write("**Practice:**")
                            st.write(week_data.get('practice', 'Complete exercises'))
                            
                            st.write("**Mini Project:**")
                            st.write(week_data.get('mini_project', 'Build a project'))
                
                # Success metrics
                if roadmap_response.get('success_metrics'):
                    st.subheader("Success Metrics")
                    st.write("Track your progress with these milestones:")
                    
                    for metric in roadmap_response['success_metrics']:
                        st.markdown(f"""
                        <div class="success-metric">
                            {metric}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Interview preparation
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Interview Questions to Practice")
                    for i, question in enumerate(roadmap_response.get('interview_questions', []), 1):
                        st.write(f"{i}. {question}")
                
                with col2:
                    st.subheader("Resume Bullets You'll Earn")
                    for bullet in roadmap_response.get('resume_bullets', []):
                        st.write(f"• {bullet}")
                
                # Download roadmap as text
                roadmap_text = f"""
                                    # {roadmap_response['career_title']} - 8 Week Learning Roadmap

                                    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                                    Weekly Commitment: {roadmap_hours} hours
                                    Budget: {roadmap_response.get('total_estimated_cost', '₹1000-3000')}

                                    ## Weekly Plan:
                                """
                for week in roadmap_response.get('weeks', []):
                    roadmap_text += f"""
                                        Week {week['week']}: {week['focus']}
                                        - Practice: {week.get('practice', '')}
                                        - Project: {week.get('mini_project', '')}
                                    """
                
                st.download_button(
                    label="Download Roadmap",
                    data=roadmap_text,
                    file_name=f"{roadmap_career}_roadmap_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Error generating roadmap: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; margin-top: 2rem;">
    <p><strong>AI Career Advisor</strong> - Empowering your tech career journey in India</p>
    <p>Built with ❤️ using FastAPI & Streamlit | <a href="{}" target="_blank">View API Docs</a></p>
</div>
""".format(backend_url + "/docs"), unsafe_allow_html=True)