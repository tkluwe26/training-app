import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Mein Trainingsplan", layout="wide")
st.title("🏋️ Mein Trainingsplan")

# ------------------------------
# Trainingstage definieren (Standard)
# ------------------------------
default_training_days = {
    "Push": ["Bench Press", "Shoulder Press", "Dumbbell Fly"],
    "Pull": ["Pull Ups", "Barbell Row", "Biceps Curl"],
    "Legs": ["Squats", "Lunges", "Leg Press"],
    "Full Body": ["Deadlift", "Push Ups", "Plank"]
}

# ------------------------------
# Trainingstag auswählen
# ------------------------------
selected_day = st.selectbox("Welchen Trainingstag möchtest du heute machen?", list(default_training_days.keys()))

# ------------------------------
# Übungen anpassen direkt auf dem Handy
# ------------------------------
st.subheader(f"Übungen für {selected_day} (bearbeiten)")
# Übungen als kommagetrennte Liste
default_exercises = ", ".join(default_training_days[selected_day])
exercise_input = st.text_area("Trage hier die Übungen ein, getrennt durch Komma", value=default_exercises, height=80)
exercises = [ex.strip() for ex in exercise_input.split(",") if ex.strip()]

# ------------------------------
# Training durchführen mit Gewicht und Wiederholungen
# ------------------------------
st.header(f"Training durchführen für {selected_day}")
completed_data = []

for ex in exercises:
    st.subheader(ex)
    for i in range(2):  # 2 Sätze pro Übung
        cols = st.columns(3)
        cols[0].write(f"Satz {i+1}")
        weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{selected_day}_{ex}_{i}_weight")
        reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{selected_day}_{ex}_{i}_reps")
        if weight > 0 and reps > 0:
            completed_data.append({
                "Trainingstag": selected_day,
                "Übung": ex,
                "Satz": i+1,
                "Gewicht": weight,
                "Wiederholungen": reps
            })

# ------------------------------
# Training abspeichern
# ------------------------------
if st.button("Training speichern ✅"):
    if not completed_data:
        st.warning("Bitte trage Gewicht und Wiederholungen für mindestens einen Satz ein!")
    else:
        file_name = "training_history.csv"
        today = datetime.today().strftime("%Y-%m-%d %H:%M")
        df_new = pd.DataFrame(completed_data)
        df_new["Datum"] = today
        if os.path.exists(file_name):
            df_old = pd.read_csv(file_name)
            df = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(file_name, index=False)
        st.success(f"Training für {selected_day} gespeichert! 📈")
        st.balloons()

# ------------------------------
# Trainingshistorie anzeigen
# ------------------------------
st.header("📊 Trainingshistorie")
if os.path.exists("training_history.csv"):
    df_hist = pd.read_csv("training_history.csv")
    st.dataframe(df_hist)
    
    st.subheader("Fortschritte pro Übung")
    for ex in exercises:
        df_ex = df_hist[df_hist["Übung"] == ex]
        if not df_ex.empty:
            st.line_chart(df_ex[["Gewicht", "Wiederholungen"]])
else:
    st.info("Noch keine Trainingshistorie vorhanden.")
