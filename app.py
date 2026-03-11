import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Mein Trainingsplan", layout="wide")
st.title("🏋️ Flexibler Trainingsplan")

# ------------------------------
# Trainingspläne auswählen oder neu erstellen
# ------------------------------
plans_file = "plans.csv"

if os.path.exists(plans_file):
    plans_df = pd.read_csv(plans_file)
    plans = plans_df["Planname"].unique().tolist()
else:
    plans = []

st.sidebar.header("Trainingsplan auswählen / erstellen")
selected_plan = st.sidebar.selectbox("Wähle einen Trainingsplan", options=plans + ["Neuer Plan"])

if selected_plan == "Neuer Plan":
    new_plan_name = st.sidebar.text_input("Name des neuen Trainingsplans")
    num_days = st.sidebar.slider("Wie viele Trainingstage soll der Plan haben?", 1, 7, 3)
    create_plan = st.sidebar.button("Plan erstellen")
    if create_plan and new_plan_name:
        plans.append(new_plan_name)
        # Grundstruktur speichern
        if os.path.exists(plans_file):
            plans_df = pd.read_csv(plans_file)
        else:
            plans_df = pd.DataFrame(columns=["Planname", "Trainingstag", "Übungen", "Sätze"])
        for i in range(1, num_days+1):
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "Planname": new_plan_name,
                "Trainingstag": f"Tag {i}",
                "Übungen": "",
                "Sätze": ""
            }])], ignore_index=True)
        plans_df.to_csv(plans_file, index=False)
        st.success(f"Trainingsplan '{new_plan_name}' erstellt!")
        selected_plan = new_plan_name

# ------------------------------
# Trainingsplan laden
# ------------------------------
if selected_plan and selected_plan != "Neuer Plan":
    plans_df = pd.read_csv(plans_file)
    plan_days = plans_df[plans_df["Planname"]==selected_plan]["Trainingstag"].tolist()
    selected_day = st.selectbox("Welchen Trainingstag möchtest du heute trainieren?", plan_days)
    
    day_row = plans_df[(plans_df["Planname"]==selected_plan) & (plans_df["Trainingstag"]==selected_day)].iloc[0]
    
    # Übungen und Sätze anpassen
    st.subheader(f"Übungen für {selected_day} bearbeiten")
    exercises_input = st.text_area("Übungen (kommagetrennt)", value=day_row["Übungen"], height=80)
    sets_input = st.text_area("Sätze pro Übung (kommagetrennt)", value=day_row["Sätze"], height=80)
    
    exercises = [ex.strip() for ex in exercises_input.split(",") if ex.strip()]
    sets_list = []
    if sets_input:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in sets_input.split(",")]
    if len(sets_list) < len(exercises):
        sets_list += [2]*(len(exercises)-len(sets_list))  # default 2 Sätze
    
    if st.button("Speichern"):
        plans_df.loc[(plans_df["Planname"]==selected_plan) & (plans_df["Trainingstag"]==selected_day), "Übungen"] = exercises_input
        plans_df.loc[(plans_df["Planname"]==selected_plan) & (plans_df["Trainingstag"]==selected_day), "Sätze"] = sets_input
        plans_df.to_csv(plans_file, index=False)
        st.success("Trainingstag gespeichert!")

    # ------------------------------
    # Training durchführen
    # ------------------------------
    st.header(f"Training durchführen für {selected_day}")
    completed_data = []
    
    for idx, ex in enumerate(exercises):
        num_sets = sets_list[idx] if idx < len(sets_list) else 2
        st.subheader(ex)
        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{selected_plan}_{selected_day}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{selected_plan}_{selected_day}_{ex}_{i}_reps")
            if weight > 0 and reps > 0:
                completed_data.append({
                    "Plan": selected_plan,
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
