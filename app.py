import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Trainings-App", layout="wide")
st.title("🏋️ Trainings-App Simplified")

# ----------------------
# Dateien
# ----------------------
USERS_FILE = "users.csv"
PLANS_FILE = "plans.csv"
HISTORY_FILE = "history.csv"

def load_csv(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
    return df

users_df = load_csv(USERS_FILE, ["Email","User","Password"])
plans_df = load_csv(PLANS_FILE, ["User","Planname","Trainingstag","Übungen","Sätze"])
history_df = load_csv(HISTORY_FILE, ["User","Plan","Trainingstag","Übung","Satz","Gewicht","Wiederholungen","Datum"])

# ----------------------
# Session State Init
# ----------------------
for key, default in [
    ("user_logged_in", False),
    ("username", ""),
    ("is_admin", False),
    ("creating_plan", False),
    ("new_plan_name", ""),
    ("num_days", 1),
    ("new_plan_days", []),
    ("exercises_dict", {}),
    ("sets_dict", {}),
    ("current_plan", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------
# Sidebar: Login / Registration
# ----------------------
st.sidebar.header("Login / Registrierung")
mode = st.sidebar.radio("Modus", ["Login","Registrieren"])

email_input = st.sidebar.text_input("E-Mail")
username_input = st.sidebar.text_input("Benutzername")
password_input = st.sidebar.text_input("Passwort", type="password")

# Registrierung
if mode=="Registrieren":
    if st.sidebar.button("Registrieren"):
        if username_input.strip()=="" or password_input.strip()=="" or email_input.strip()=="":
            st.sidebar.error("Bitte alles ausfüllen")
        elif username_input in users_df["User"].values:
            st.sidebar.error("Benutzername existiert bereits")
        else:
            users_df = pd.concat([users_df, pd.DataFrame([{
                "Email": email_input,
                "User": username_input,
                "Password": password_input
            }])], ignore_index=True)
            users_df.to_csv(USERS_FILE,index=False)
            st.sidebar.success("Registrierung erfolgreich! Bitte anmelden")
            st.stop()

# Login
if st.sidebar.button("Anmelden"):
    # Admin Login
    if username_input=="admin" and password_input=="adminpasswort":
        st.session_state.is_admin = True
        st.session_state.user_logged_in = True
        st.session_state.username = "admin"
        st.sidebar.success("Admin angemeldet")
    else:
        row = users_df[(users_df["User"]==username_input)&(users_df["Password"]==password_input)]
        if not row.empty:
            st.session_state.user_logged_in = True
            st.session_state.username = username_input
            st.session_state.is_admin = False
            st.sidebar.success(f"Willkommen {username_input}")
        else:
            st.sidebar.error("Benutzername oder Passwort falsch")

if not st.session_state.user_logged_in:
    st.stop()

# ----------------------
# Admin Ansicht
# ----------------------
if st.session_state.is_admin:
    st.header("📋 Alle registrierten Accounts")
    st.dataframe(users_df)
    st.stop()

# ----------------------
# Trainingsplan erstellen / auswählen
# ----------------------
st.header(f"Willkommen {st.session_state.username}")

if st.session_state.current_plan is None and not st.session_state.creating_plan:
    options = list(plans_df[plans_df["User"]==st.session_state.username]["Planname"].unique())
    options.append("Neuen Plan erstellen")
    choice = st.selectbox("Trainingsplan auswählen oder erstellen", options)
    if choice=="Neuen Plan erstellen":
        st.session_state.creating_plan = True
    else:
        st.session_state.current_plan = choice

# ----------------------
# Wizard: Neuer Trainingsplan
# ----------------------
if st.session_state.creating_plan:
    st.subheader("📝 Trainingsplan erstellen")

    # Planname
    st.session_state.new_plan_name = st.text_input("Name des Trainingsplans", st.session_state.new_plan_name)
    st.session_state.num_days = st.number_input("Anzahl Trainingstage", min_value=1, max_value=7, value=st.session_state.num_days, step=1)

    # Trainingstage benennen
    for i in range(st.session_state.num_days):
        day_name = st.text_input(f"Name Trainingstag {i+1}", key=f"day_{i}")
        if len(st.session_state.new_plan_days)<st.session_state.num_days:
            st.session_state.new_plan_days.append(day_name)

    # Übungen + Sätze
    for day in st.session_state.new_plan_days:
        st.subheader(day)
        st.session_state.exercises_dict[day] = st.text_area(f"Übungen für {day} (kommagetrennt)", st.session_state.exercises_dict.get(day,""))
        st.session_state.sets_dict[day] = st.text_area(f"Sätze pro Übung für {day} (kommagetrennt, Zahl pro Übung)", st.session_state.sets_dict.get(day,""))

    if st.button("Trainingsplan speichern"):
        for day in st.session_state.new_plan_days:
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": st.session_state.username,
                "Planname": st.session_state.new_plan_name,
                "Trainingstag": day,
                "Übungen": st.session_state.exercises_dict[day],
                "Sätze": st.session_state.sets_dict[day]
            }])], ignore_index=True)
        plans_df.to_csv(PLANS_FILE, index=False)
        st.session_state.creating_plan = False
        st.session_state.current_plan = st.session_state.new_plan_name
        st.session_state.new_plan_name = ""
        st.session_state.num_days = 1
        st.session_state.new_plan_days = []
        st.session_state.exercises_dict = {}
        st.session_state.sets_dict = {}
        st.experimental_rerun()

# ----------------------
# Trainingsplan trainieren
# ----------------------
if st.session_state.current_plan:
    plan = st.session_state.current_plan
    plan_days = plans_df[(plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan)]
    day_choice = st.selectbox("Welchen Trainingstag trainieren?", plan_days["Trainingstag"].tolist())

    day_row = plan_days[plan_days["Trainingstag"]==day_choice].iloc[0]
    exercises = [ex.strip() for ex in day_row["Übungen"].split(",") if ex.strip()]
    sets_list = []
    if day_row["Sätze"]:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in day_row["Sätze"].split(",")]
    if len(sets_list)<len(exercises):
        sets_list += [2]*(len(exercises)-len(sets_list))

    st.header(f"Training: {day_choice}")
    completed_data=[]
    for idx, ex in enumerate(exercises):
        num_sets = sets_list[idx]
        st.subheader(ex)
        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{plan}_{day_choice}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{plan}_{day_choice}_{ex}_{i}_reps")
            if weight>0 and reps>0:
                completed_data.append({
                    "User": st.session_state.username,
                    "Plan": plan,
                    "Trainingstag": day_choice,
                    "Übung": ex,
                    "Satz": i+1,
                    "Gewicht": weight,
                    "Wiederholungen": reps,
                    "Datum": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
    if st.button("Training speichern"):
        if completed_data:
            df_new = pd.DataFrame(completed_data)
            history_df = pd.concat([history_df, df_new], ignore_index=True)
            history_df.to_csv(HISTORY_FILE, index=False)
            st.success("Training gespeichert!")
            st.balloons()

    st.header("📊 Trainingshistorie")
    hist_user = history_df[history_df["User"]==st.session_state.username]
    st.dataframe(hist_user)
