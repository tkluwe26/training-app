import streamlit as st

st.title("🏋️ Mein Trainingsplan")

st.header("Heutiges Training")

exercises = {
    "Bench Press": 4,
    "Squats": 4,
    "Pull Ups": 3,
    "Shoulder Press": 3
}

for exercise, sets in exercises.items():
    st.subheader(exercise)
    
    for i in range(sets):
        st.checkbox(f"Satz {i+1}", key=f"{exercise}{i}")
