import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Trainings-App Wizard", layout="wide")
st.title("🏋️ Trainings-App (Wizard-Modus)")

# ------------------------------
# Admin Passwort
# ------------------------------
ADMIN_PASSWORD = "meinAdminPasswort"

# ------------------------------
# CSV-Dateien
# ------------------------------
users_file = "users.csv"
plans_file = "plans.csv"
history_file = "training_history.csv"

def load_csv(file_path, columns):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file_path, index=False)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df

users_df = load_csv(users_file, ["User", "Password"])
plans_df = load_csv(plans_file, ["User","Planname","Trainingstag","Übungen","Sätze"])
history_df = load_csv(history_file, ["User","Plan","Trainingstag","Übung","Satz","Gewicht","Wiederholungen","Datum"])

# ------------------------------
# Session State Initialisierung
# ------------------------------
for key, default in [
    ("user_logged_in", False),
    ("is_admin", False),
    ("username", ""),
    ("current_plan", None),
    ("creating_plan", False),
    ("new_plan_days", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ------------------------------
# Sidebar Login/Registrierung
# ------------------------------
st.sidebar.header("Login oder Registrierung")
mode = st.sidebar.radio("Modus", ["Login","Registrieren"])
username_input = st.sidebar.text_input("Benutzername")
password_input = st.sidebar.text_input("Passwort", type="password")

if mode=="Registrieren":
    if st.sidebar.button("Registrieren"):
        if username_input.strip()=="" or password_input.strip()=="":
            st.sidebar.error("Benutzername/Passwort darf nicht leer sein")
        elif username_input in users_df["User"].values:
            st.sidebar.error("Benutzer existiert bereits")
        else:
            users_df = pd.concat([users_df,pd.DataFrame([{"User":username_input,"Password":password_input}])],ignore_index=True)
            users_df.to_csv(users_file,index=False)
            st.sidebar.success("Registrierung erfolgreich! Bitte anmelden")
            st.stop()

if st.sidebar.button("Anmelden"):
    if password_input == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.session_state.user_logged_in = True
        st.session_state.username = "Admin"
        st.sidebar.success("Admin angemeldet")
    else:
        row = users_df[(users_df["User"]==username_input)&(users_df["Password"]==password_input)]
        if not row.empty:
            st.session_state.username = username_input
            st.session_state.user_logged_in = True
            st.session_state.is_admin = False
            st.sidebar.success(f"Willkommen {username_input}")
        else:
            st.sidebar.error("Benutzername oder Passwort falsch")

if not st.session_state.user_logged_in:
    st.stop()

# ------------------------------
# Startfenster: Plan auswählen oder erstellen
# ------------------------------
if not st.session_state.creating_plan and st.session_state.current_plan is None:
    st.header("🏋️ Trainingsplan auswählen oder neu erstellen")
    
    if st.session_state.is_admin:
        user_filter = st.selectbox("Benutzer (Admin)", options=["Alle"] + users_df["User"].tolist())
    else:
        user_filter = st.session_state.username

    if st.session_state.is_admin and user_filter!="Alle":
        plans_user_df = plans_df[plans_df["User"]==user_filter]
    elif not st.session_state.is_admin:
        plans_user_df = plans_df[plans_df["User"]==st.session_state.username]
    else:
        plans_user_df = plans_df

    plans_list = plans_user_df["Planname"].unique().tolist()
    plans_list.append("Neuer Plan")
    selected_plan = st.selectbox("Trainingsplan auswählen", plans_list)

    if selected_plan=="Neuer Plan":
        if st.button("Neuen Plan erstellen"):
            st.session_state.creating_plan = True
            st.session_state.new_plan_days = []
    else:
        st.session_state.current_plan = selected_plan

# ------------------------------
# Neuer Plan Wizard
# ------------------------------
if st.session_state.creating_plan:
    st.header("📝 Neuen Trainingsplan erstellen")
    new_plan_name = st.text_input("Name des Trainingsplans")
    num_days = st.slider("Anzahl Trainingstage",1,7,3)

    # Trainingstage benennen
    while len(st.session_state.new_plan_days) < num_days:
        day_name = st.text_input(f"Name für Trainingstag {len(st.session_state.new_plan_days)+1}", key=f"day_name_{len(st.session_state.new_plan_days)+1}")
        if st.button(f"Tag {len(st.session_state.new_plan_days)+1} speichern"):
            if day_name.strip()!="":
                st.session_state.new_plan_days.append(day_name)
                st.experimental_rerun()
    
    # Übungen/Sätze für jeden Tag
    if len(st.session_state.new_plan_days)==num_days:
        exercises_dict = {}
        sets_dict = {}
        for day in st.session_state.new_plan_days:
            st.subheader(day)
            exercises_dict[day] = st.text_area(f"Übungen für {day} (kommagetrennt)", key=f"{day}_ex")
            sets_dict[day] = st.text_area(f"Sätze pro Übung für {day} (kommagetrennt)", key=f"{day}_sets")
        
        if st.button("Trainingsplan speichern"):
            for day in st.session_state.new_plan_days:
                plans_df = pd.concat([plans_df,pd.DataFrame([{
                    "User": st.session_state.username,
                    "Planname": new_plan_name,
                    "Trainingstag": day,
                    "Übungen": exercises_dict[day],
                    "Sätze": sets_dict[day]
                }])],ignore_index=True)
            plans_df.to_csv(plans_file,index=False)
            st.success("Trainingsplan erstellt!")
            st.session_state.creating_plan = False
            st.session_state.current_plan = None
            st.experimental_rerun()

# ------------------------------
# Trainingsplan auswählen und trainieren
# ------------------------------
if st.session_state.current_plan:
    selected_plan = st.session_state.current_plan
    plan_days = plans_df[plans_df["Planname"]==selected_plan]
    if not st.session_state.is_admin:
        plan_days = plan_days[plan_days["User"]==st.session_state.username]
    elif st.session_state.is_admin and user_filter!="Alle":
        plan_days = plan_days[plan_days["User"]==user_filter]
    
    plan_days_list = plan_days["Trainingstag"].tolist()
    selected_day = st.selectbox("Welchen Trainingstag trainieren?", plan_days_list)
    
    day_row = plans_df[(plans_df["Planname"]==selected_plan) & (plans_df["Trainingstag"]==selected_day)].iloc[0]
    exercises = [ex.strip() for ex in day_row["Übungen"].split(",") if ex.strip()]
    sets_list = []
    if day_row["Sätze"]:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in day_row["Sätze"].split(",")]
    if len(sets_list)<len(exercises):
        sets_list += [2]*(len(exercises)-len(sets_list))

    st.header(f"Training: {selected_day}")
    completed_data=[]
    for idx, ex in enumerate(exercises):
        num_sets = sets_list[idx]
        st.subheader(ex)
        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{selected_plan}_{selected_day}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{selected_plan}_{selected_day}_{ex}_{i}_reps")
            if weight>0 and reps>0:
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
        if completed_data:
            today = datetime.today().strftime("%Y-%m-%d %H:%M")
            df_new = pd.DataFrame(completed_data)
            df_new["Datum"]=today
            history_df = pd.concat([history_df,df_new],ignore_index=True)
            history_df.to_csv(history_file,index=False)
            st.success("Training gespeichert!")
            st.balloons()
        else:
            st.warning("Bitte mindestens einen Satz mit Gewicht & Wiederholungen eintragen")

    st.header("📊 Trainingshistorie")
    df_hist = load_csv(history_file, ["User","Plan","Trainingstag","Übung","Satz","Gewicht","Wiederholungen","Datum"])
    df_hist_user = df_hist[df_hist["User"]==st.session_state.username] if not st.session_state.is_admin else df_hist
    st.dataframe(df_hist_user)
