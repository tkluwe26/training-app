import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Multi-User Trainings-App", layout="wide")
st.title("🏋️ Mehrbenutzer Trainings-App (stabil & Session State)")

# ------------------------------
# Admin Passwort
# ------------------------------
ADMIN_PASSWORD = "meinAdminPasswort"  # <-- Dein Admin-Passwort

# ------------------------------
# CSV-Dateien
# ------------------------------
users_file = "users.csv"
plans_file = "plans.csv"
history_file = "training_history.csv"

# ------------------------------
# CSV laden oder erstellen + Spalten prüfen
# ------------------------------
def load_csv(file_path, columns):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)  # Datei sofort anlegen
    # fehlende Spalten ergänzen
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df

users_df = load_csv(users_file, ["User", "Password"])
plans_df = load_csv(plans_file, ["User", "Planname", "Trainingstag", "Übungen", "Sätze"])
history_df = load_csv(history_file, ["User", "Plan", "Trainingstag", "Übung", "Satz", "Gewicht", "Wiederholungen", "Datum"])

# ------------------------------
# Session State initialisieren
# ------------------------------
if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
    st.session_state.is_admin = False
    st.session_state.username = ""
    st.session_state.current_plan = None

# ------------------------------
# Sidebar: Login oder Registrierung
# ------------------------------
st.sidebar.header("Anmeldung oder Registrierung")
mode = st.sidebar.radio("Modus", ["Login", "Registrieren"])

username_input = st.sidebar.text_input("Benutzername")
password_input = st.sidebar.text_input("Passwort", type="password")

# Registrierung
if mode == "Registrieren":
    register = st.sidebar.button("Registrieren")
    if register:
        if username_input.strip() == "" or password_input.strip() == "":
            st.sidebar.error("Benutzername und Passwort dürfen nicht leer sein")
        elif username_input in users_df["User"].values:
            st.sidebar.error("Benutzername existiert bereits")
        else:
            users_df = pd.concat([users_df, pd.DataFrame([{"User": username_input, "Password": password_input}])], ignore_index=True)
            users_df.to_csv(users_file, index=False)
            st.sidebar.success("Registrierung erfolgreich! Du kannst dich jetzt einloggen")
            st.stop()

# Login
login = st.sidebar.button("Anmelden")
if login:
    if password_input == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.session_state.user_logged_in = True
        st.session_state.username = "Admin"
        st.sidebar.success("Admin angemeldet")
    else:
        user_row = users_df[(users_df["User"] == username_input) & (users_df["Password"] == password_input)]
        if not user_row.empty:
            st.session_state.username = username_input
            st.session_state.is_admin = False
            st.session_state.user_logged_in = True
            st.sidebar.success(f"Willkommen {username_input}")
        else:
            st.sidebar.error("Benutzername oder Passwort falsch")

# ------------------------------
# Stop, wenn nicht eingeloggt
# ------------------------------
if not st.session_state.user_logged_in:
    st.stop()

# ------------------------------
# STARTFENSTER: Trainingsplan auswählen oder erstellen
# ------------------------------
st.header("🏋️ Trainingsplan auswählen oder erstellen")
if st.session_state.is_admin:
    user_filter = st.selectbox("Benutzer (Admin)", options=["Alle"] + users_df["User"].tolist())
else:
    user_filter = st.session_state.username

# Filter Trainingspläne
if st.session_state.is_admin and user_filter != "Alle":
    plans_user_df = plans_df[plans_df["User"] == user_filter]
elif not st.session_state.is_admin:
    plans_user_df = plans_df[plans_df["User"] == st.session_state.username]
else:
    plans_user_df = plans_df

plans_list = plans_user_df["Planname"].unique().tolist()
plans_list.append("Neuer Plan")

selected_plan = st.selectbox("Wähle einen Trainingsplan", plans_list)

# Neuer Plan erstellen
if selected_plan == "Neuer Plan" and not st.session_state.is_admin:
    new_plan_name = st.text_input("Name des neuen Trainingsplans")
    num_days = st.slider("Wie viele Trainingstage soll der Plan haben?", 1, 7, 3)
    create_plan = st.button("Plan erstellen")
    if create_plan and new_plan_name:
        for i in range(1, num_days + 1):
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": st.session_state.username,
                "Planname": new_plan_name,
                "Trainingstag": f"Tag {i}",
                "Übungen": "",
                "Sätze": ""
            }])], ignore_index=True)
        plans_df.to_csv(plans_file, index=False)
        st.success(f"Trainingsplan '{new_plan_name}' erstellt!")
        st.session_state.current_plan = new_plan_name

# Wenn bereits existierender Plan ausgewählt
if selected_plan != "Neuer Plan":
    st.session_state.current_plan = selected_plan

# ------------------------------
# Trainingsplan bearbeiten / Training durchführen
# ------------------------------
if st.session_state.current_plan:
    selected_plan = st.session_state.current_plan
    plan_days = plans_df[plans_df["Planname"] == selected_plan]
    if not st.session_state.is_admin:
        plan_days = plan_days[plan_days["User"] == st.session_state.username]
    elif st.session_state.is_admin and user_filter != "Alle":
        plan_days = plan_days[plan_days["User"] == user_filter]
    
    plan_days_list = plan_days["Trainingstag"].tolist()
    
    selected_day = st.selectbox("Welchen Trainingstag möchtest du heute trainieren?", plan_days_list)
    
    day_row = plans_df[(plans_df["Planname"] == selected_plan) &
                       (plans_df["Trainingstag"] == selected_day)].iloc[0]
    
    st.subheader(f"Übungen für {selected_day} bearbeiten")
    exercises_input = st.text_area("Übungen (kommagetrennt)", value=day_row["Übungen"], height=80)
    sets_input = st.text_area("Sätze pro Übung (kommagetrennt)", value=day_row["Sätze"], height=80)
    
    exercises = [ex.strip() for ex in exercises_input.split(",") if ex.strip()]
    sets_list = []
    if sets_input:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in sets_input.split(",")]
    if len(sets_list) < len(exercises):
        sets_list += [2] * (len(exercises) - len(sets_list))
    
    if st.button("Speichern"):
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Übungen"] = exercises_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Sätze"] = sets_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "User"] = st.session_state.username
        plans_df.to_csv(plans_file, index=False)
        st.success("Trainingstag gespeichert!")

    st.header(f"Training durchführen für {selected_day}")
    completed_data = []
    
    for idx, ex in enumerate(exercises):
        num_sets = sets_list[idx] if idx < len(sets_list) else 2
        st.subheader(ex)
        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{st.session_state.username}_{selected_plan}_{selected_day}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{st.session_state.username}_{selected_plan}_{selected_day}_{ex}_{i}_reps")
            if weight > 0 and reps > 0:
                completed_data.append({
                    "User": st.session_state.username,
                    "Plan": selected_plan,
                    "Trainingstag": selected_day,
                    "Übung": ex,
                    "Satz": i+1,
                    "Gewicht": weight,
                    "Wiederholungen": reps
                })
    
    if st.button("Training speichern ✅"):
        if not completed_data:
            st.warning("Bitte trage Gewicht und Wiederholungen für mindestens einen Satz ein!")
        else:
            today = datetime.today().strftime("%Y-%m-%d %H:%M")
            df_new = pd.DataFrame(completed_data)
            df_new["Datum"] = today
            history_df = pd.concat([history_df, df_new], ignore_index=True)
            history_df.to_csv(history_file, index=False)
            st.success(f"Training für {selected_day} gespeichert! 📈")
            st.balloons()
    
    st.header("📊 Trainingshistorie")
    df_hist = load_csv(history_file, ["User", "Plan", "Trainingstag", "Übung", "Satz", "Gewicht", "Wiederholungen", "Datum"])
    if not st.session_state.is_admin:
        df_hist_user = df_hist[df_hist["User"] == st.session_state.username]
    elif st.session_state.is_admin and user_filter != "Alle":
        df_hist_user = df_hist[df_hist["User"] == user_filter]
    else:
        df_hist_user = df_hist
    st.dataframe(df_hist_user)
    
    st.subheader("Fortschritte pro Übung")
    for ex in exercises:
        df_ex = df_hist_user[df_hist_user["Übung"] == ex]
        if not df_ex.empty:
            st.line_chart(df_ex[["Gewicht", "Wiederholungen"]])
