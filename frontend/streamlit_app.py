import json
import requests
import streamlit as st

st.set_page_config(page_title="Career & Skills Advisor (MVP)", layout="wide")

st.sidebar.title("Settings")
backend_url = st.sidebar.text_input("Backend URL", value="http://localhost:8000")

st.title("🎓 Personalized Career & Skills Advisor — MVP")

st.markdown("Fill a quick profile and get Top-3 careers with confidence, skill-gap, and an 8-week roadmap.")

with st.form("profile_form"):
    interests = st.multiselect(
        "Your interests",
        ["Working with data and numbers", "Designing user interfaces", "Cybersecurity and protecting systems"]
    )
    skills = st.multiselect(
        "Skills you have (pick a few)",
        ["excel", "sql", "statistics_basics", "python", "pandas", "data_visualization",
         "ux_principles", "visual_design_basics", "figma_basics", "wireframing", "prototyping",
         "linux_basics", "network_basics", "security_fundamentals", "siem_basics"]
    )
    hours = st.slider("Hours you can learn per week", 1, 20, 6)
    budget = st.selectbox("Monthly learning budget (INR)", ["0", "500-1000", "1000-3000", "3000+"])
    budget_map = {"0": 0, "500-1000": 1000, "1000-3000": 3000, "3000+": 5000}
    city = st.selectbox("City", ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Other"])
    learning_style = st.selectbox("Preferred learning style", ["Videos", "Reading articles", "Hands-on practice"])
    goal_text = st.text_area("Your 3-month goal (optional)", placeholder="e.g., Get an internship")
    submitted = st.form_submit_button("Get Recommendations")

if submitted:
    profile = {
        "interests": interests,
        "skills": skills,
        "hours_per_week": hours,
        "budget_inr_per_month": budget_map[budget],
        "city": city,
        "learning_style": learning_style,
        "goal_text": goal_text
    }

    with st.spinner("Scoring your profile..."):
        try:
            _ = requests.post(f"{backend_url}/assess", json=profile, timeout=15).json()
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

    with st.spinner("Computing recommendations..."):
        rec = requests.post(f"{backend_url}/recommend", json=profile, timeout=30).json()

    st.subheader("Top Recommendations")
    cols = st.columns(3)
    for idx, item in enumerate(rec.get("items", [])):
        with cols[idx]:
            st.metric(label=f"{item['title']}", value=f"{item['confidence_pct']}% confidence")
            st.caption(item["market_note"])
            st.write("**Why this fits**:", item["rationale"])
            st.write("**Readiness**:", f"{item['readiness_pct']}%")
            if item["missing_skills"]:
                st.write("**Next skills to learn**:", ", ".join(item["missing_skills"]))
            if item["alternatives"]:
                st.write("**Alternative paths**:", ", ".join(item["alternatives"]))

            # Skill gap button
            if st.button(f"Show Skill Gap – {item['title']}", key=f"gap_{item['career_id']}"):
                gap_req = {"career_id": item["career_id"], "skills": skills}
                gap = requests.post(f"{backend_url}/gap", json=gap_req, timeout=15).json()
                st.info(f"Readiness: {gap['readiness_pct']}%")
                st.json(gap["missing_by_level"])

            # Roadmap button
            if st.button(f"Generate 8-week Roadmap – {item['title']}", key=f"road_{item['career_id']}"):
                r_req = {"career_id": item["career_id"], "hours_per_week": hours,
                         "budget_inr_per_month": budget_map[budget], "learning_style": learning_style}
                plan = requests.post(f"{backend_url}/roadmap", json=r_req, timeout=30).json()
                st.success("Roadmap generated")
                for w in plan.get("weeks", []):
                    with st.expander(f"Week {w['week']}: {w['focus']}"):
                        st.write("**Resources:**")
                        for r in w["resources"]:
                            st.write(f"- {r}")
                        st.write("**Practice:**", w["practice"])
                        st.write("**Mini-project:**", w["mini_project"])
                st.write("**Interview questions:**")
                st.write("\n".join([f"- {q}" for q in plan.get("interview_questions", [])]))
                st.write("**Resume bullets:**")
                st.write("\n".join([f"- {b}" for b in plan.get("resume_bullets", [])]))
