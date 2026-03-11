import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Mein Trainingsplan", layout="wide")
st.title("🏋️ Mehrbenutzer Trainings-App")

# ------------------------------
# Admin-Passwort
# ------------------------------
ADMIN_PASSWORD = "deinGeheimesPasswort"  # <-- Hier dein Passwort eintragen

# ------------------------------
# Benutzeranmeldung
# ------------------------------
st.sidebar.header("Benutzeranmeldung")
username = st.sidebar.text_input("Dein Name")
admin_mode = st.sidebar.text_input("Admin Passwort (optional)", type="password")

if not username:
    st.warning("Bitte gib deinen Namen ein, um fortzufahren")
    st.stop()

is_admin = False
if admin_mode == ADMIN_PASSWORD and admin_mode != "":
    st.sidebar.success("Admin-Modus aktiviert")
    is_admin = True

# ------------------------------
# Dateinamen
# ------------------------------
plans_file = "plans.csv"
history_file = "training_history.csv"

# ------------------------------
# Trainingspläne laden oder erstellen
# ------------------------------
if os.path.exists(plans_file):
    plans_df = pd.read_csv(plans_file)
else:
    plans_df = pd.DataFrame(columns=["User", "Planname", "Trainingstag", "Übungen", "Sätze"])

# Filter nur für aktuellen Benutzer, außer Admin
if not is_admin:
    user_plans_df = plans_df[plans_df["User"] == username]
else:
    user_plans_df = plans_df  # Admin sieht alle

plans = user_plans_df["Planname"].unique().tolist()
plans.append("Neuer Plan")

st.sidebar.header("Trainingsplan auswählen / erstellen")
selected_plan = st.sidebar.selectbox("Wähle einen Trainingsplan", plans)

# ------------------------------
# Neuen Plan erstellen
# ------------------------------
if selected_plan == "Neuer Plan" and not is_admin:
    new_plan_name = st.sidebar.text_input("Name des neuen Trainingsplans")
    num_days = st.sidebar.slider("Wie viele Trainingstage soll der Plan haben?", 1, 7, 3)
    create_plan = st.sidebar.button("Plan erstellen")
    if create_plan and new_plan_name:
        for i in range(1, num_days + 1):
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": username,
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
if selected_plan != "Neuer Plan":
    plan_days = plans_df[plans_df["Planname"] == selected_plan]
    if not is_admin:
        plan_days = plan_days[plan_days["User"] == username]
    plan_days_list = plan_days["Trainingstag"].tolist()
    
    selected_day = st.selectbox("Welchen Trainingstag möchtest du heute trainieren?", plan_days_list)
    
    day_row = plans_df[(plans_df["Planname"] == selected_plan) &
                       (plans_df["Trainingstag"] == selected_day)].iloc[0]
    
    # Übungen und Sätze anpassen
    st.subheader(f"Übungen für {selected_day} bearbeiten")
    exercises_input = st.text_area("Übungen (kommagetrennt)", value=day_row["Übungen"], height=80)
    sets_input = st.text_area("Sätze pro Übung (kommagetrennt)", value=day_row["Sätze"], height=80)
    
    exercises = [ex.strip() for ex in exercises_input.split(",") if ex.strip()]
    sets_list = []
    if sets_input:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in sets_input.split(",")]
    if len(sets_list) < len(exercises):
        sets_list += [2] * (len(exercises) - len(sets_list))  # default 2 Sätze
    
    if st.button("Speichern"):
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Übungen"] = exercises_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Sätze"] = sets_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "User"] = username
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
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{username}_{selected_plan}_{selected_day}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{username}_{selected_plan}_{selected_day}_{ex}_{i}_reps")
            if weight > 0 and reps > 0:
                completed_data.append({
                    "User": username,
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
            today = datetime.today().strftime("%Y-%m-%d %H:%M")
            df_new = pd.DataFrame(completed_data)
            df_new["Datum"] = today
            if os.path.exists(history_file):
                df_old = pd.read_csv(history_file)
                df = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df = df_new
            df.to_csv(history_file, index=False)
            st.success(f"Training für {selected_day} gespeichert! 📈")
            st.balloons()
    
    # ------------------------------
    # Trainingshistorie anzeigen
    # ------------------------------
    st.header("📊 Trainingshistorie")
    if os.path.exists(history_file):
        df_hist = pd.read_csv(history_file)
        if not is_admin:
            df_hist_user = df_hist[df_hist["User"] == username]
        else:
            df_hist_user = df_hist
        st.dataframe(df_hist_user)
        
        st.subheader("Fortschritte pro Übung")
        for ex in exercises:
            df_ex = df_hist_user[df_hist_user["Übung"] == ex]
            if not df_ex.empty:
                st.line_chart(df_ex[["Gewicht", "Wiederholungen"]])
    else:
        st.info("Noch keine Trainingshistorie vorhanden.")
