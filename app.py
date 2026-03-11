import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ----------------------
# Seitenlayout & Titel
# ----------------------
st.set_page_config(page_title="FitTrack", page_icon="💪", layout="wide")
st.title("💪 FitTrack – Dein persönlicher Trainingsplan")

# ----------------------
# Dateien
# ----------------------
USERS_FILE = "users.csv"
PLANS_FILE = "plans.csv"
HISTORY_FILE = "history.csv"

def load_csv(file, columns):
    if os.path.exists(file):
        df = pd.read_csv(file)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
    return df

users_df = load_csv(USERS_FILE, ["User","Password"])
plans_df = load_csv(PLANS_FILE, ["User","Planname","Trainingstag","Übungen","Sätze"])
history_df = load_csv(HISTORY_FILE, ["User","Plan","Trainingstag","Übung","Satz","Gewicht","Wiederholungen","RIR","Datum"])

# TEMPORÄRER PASSWORT-RESET
users_df.loc[users_df["User"]=="dein_username", "Password"] = "temp123"
users_df.to_csv(USERS_FILE, index=False)
st.write("Passwort wurde temporär auf 'temp123' gesetzt. Bitte melde dich damit an!")
st.stop()

# ----------------------
# Session State Init
# ----------------------
for key, default in [
    ("user_logged_in", False),
    ("username", ""),
    ("is_admin", False),
    ("current_plan", None),
    ("edit_plan", None)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------
# Abmelden-Funktion
# ----------------------
if st.session_state.user_logged_in:
    if st.sidebar.button("Abmelden"):
        st.session_state.user_logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.session_state.current_plan = None
        st.session_state.edit_plan = None
        st.experimental_rerun()

# ----------------------
# Login / Registrierung
# ----------------------
if not st.session_state.user_logged_in:
    st.sidebar.header("Login / Registrierung")
    mode = st.sidebar.radio("Modus", ["Login","Registrieren"])
    username_input = st.sidebar.text_input("Benutzername")
    password_input = st.sidebar.text_input("Passwort", type="password")

    # Registrierung
    if mode=="Registrieren" and st.sidebar.button("Registrieren"):
        if username_input.strip()=="" or password_input.strip()=="":
            st.sidebar.error("Bitte Benutzername & Passwort ausfüllen")
        elif username_input in users_df["User"].values:
            st.sidebar.error("Benutzername existiert bereits")
        else:
            users_df = pd.concat([users_df, pd.DataFrame([{
                "User": username_input,
                "Password": password_input
            }])], ignore_index=True)
            users_df.to_csv(USERS_FILE,index=False)
            st.sidebar.success("Registrierung erfolgreich! Bitte anmelden")

    # Login
    if st.sidebar.button("Anmelden"):
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
    # Kein st.stop() mehr – App läuft weiter
    st.stop()

# ----------------------
# Passwort ändern
# ----------------------
if st.session_state.user_logged_in and not st.session_state.is_admin:
    with st.sidebar.expander("🔑 Passwort ändern"):
        old_password = st.text_input("Altes Passwort", type="password", key="old_pw")
        new_password = st.text_input("Neues Passwort", type="password", key="new_pw")
        new_password_confirm = st.text_input("Neues Passwort bestätigen", type="password", key="new_pw_confirm")
        if st.button("Passwort aktualisieren"):
            row = users_df[(users_df["User"]==st.session_state.username) & (users_df["Password"]==old_password)]
            if row.empty:
                st.sidebar.error("Altes Passwort ist falsch!")
            elif new_password.strip() == "":
                st.sidebar.error("Neues Passwort darf nicht leer sein!")
            elif new_password != new_password_confirm:
                st.sidebar.error("Neue Passwörter stimmen nicht überein!")
            else:
                users_df.loc[users_df["User"]==st.session_state.username, "Password"] = new_password
                users_df.to_csv(USERS_FILE, index=False)
                st.sidebar.success("Passwort erfolgreich geändert!")

# ----------------------
# Admin Ansicht
# ----------------------
if st.session_state.is_admin:
    st.header("📋 Alle registrierten Accounts")
    st.dataframe(users_df)
    st.markdown("### Accounts löschen")
    for user in users_df["User"]:
        if user!="admin":
            cols = st.columns([4,1,1])
            cols[0].write(user)
            delete_key = f"del_user_{user}"
            confirm_key = f"confirm_del_user_{user}"
            
            if cols[1].button("Löschen", key=delete_key):
                st.session_state[confirm_key] = True
                
            if st.session_state.get(confirm_key, False):
                cols[2].write("⚠️ Bitte bestätigen")
                if cols[2].button("Ja, löschen", key=f"confirm_{user}"):
                    users_df = users_df[users_df["User"] != user]
                    users_df.to_csv(USERS_FILE, index=False)
                    plans_df = plans_df[plans_df["User"] != user]
                    plans_df.to_csv(PLANS_FILE, index=False)
                    history_df = history_df[history_df["User"] != user]
                    history_df.to_csv(HISTORY_FILE, index=False)
                    st.success(f"Account '{user}' gelöscht!")
                    st.session_state.pop(confirm_key, None)
                    st.experimental_rerun()
    st.stop()

# ----------------------
# Willkommen User
# ----------------------
st.header(f"Willkommen {st.session_state.username}")

# ----------------------
# Trainingsplan auswählen oder erstellen
# ----------------------
st.subheader("Trainingsplan auswählen oder erstellen")
user_plans = list(plans_df[plans_df["User"]==st.session_state.username]["Planname"].unique())

st.markdown("### Bestehende Trainingspläne")
if user_plans:
    for plan in user_plans:
        cols = st.columns([3,1,1])
        cols[0].write(plan)
        if cols[1].button("Bearbeiten", key=f"edit_{plan}"):
            st.session_state.edit_plan = plan
            st.experimental_rerun()
        if cols[2].button("Löschen", key=f"del_{plan}"):
            plans_df = plans_df[~((plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan))]
            plans_df.to_csv(PLANS_FILE,index=False)
            history_df = history_df[~((history_df["User"]==st.session_state.username) & (history_df["Plan"]==plan))]
            history_df.to_csv(HISTORY_FILE,index=False)
            st.success(f"Trainingsplan '{plan}' gelöscht!")
            st.experimental_rerun()
else:
    st.info("Keine Trainingspläne vorhanden")

# Dropdown für Auswahl oder neuen Plan erstellen
if user_plans:
    options = user_plans.copy()
    options.append("Neuen Plan erstellen")
    choice = st.selectbox("Trainingsplan auswählen oder erstellen", options)
else:
    choice = "Neuen Plan erstellen"

# ----------------------
# Plan erstellen oder bearbeiten
# ----------------------
if choice=="Neuen Plan erstellen" or st.session_state.edit_plan:
    if st.session_state.edit_plan:
        plan_name = st.session_state.edit_plan
        plan_days_df = plans_df[(plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan_name)]
        if plan_days_df.empty:
            st.warning("Dieser Plan existiert nicht mehr!")
            st.session_state.edit_plan = None
            st.experimental_rerun()
        else:
            st.subheader(f"✏️ Bearbeite Plan: {plan_name}")
            day_names = plan_days_df["Trainingstag"].tolist()
    else:
        st.subheader("📝 Neuen Trainingsplan erstellen")
        plan_name = st.text_input("Name des Trainingsplans")
        num_days = st.number_input("Anzahl Trainingstage", min_value=1, max_value=7, value=3, step=1)
        day_names = [st.text_input(f"Name Trainingstag {i+1}", value=f"Tag {i+1}") for i in range(num_days)]

    exercises_dict = {}
    sets_dict = {}
    for day in day_names:
        if st.session_state.edit_plan:
            day_row = plan_days_df[plan_days_df["Trainingstag"]==day].iloc[0]
            exercises_dict[day] = st.text_area(f"Übungen für {day} (kommagetrennt)", value=day_row.get("Übungen",""))
            sets_dict[day] = st.text_area(f"Sätze pro Übung für {day} (kommagetrennt)", value=day_row.get("Sätze",""))
        else:
            exercises_dict[day] = st.text_area(f"Übungen für {day} (kommagetrennt)")
            sets_dict[day] = st.text_area(f"Sätze pro Übung für {day} (kommagetrennt)")

    if st.button("Plan speichern"):
        plans_df = plans_df[~((plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan_name))]
        for day in day_names:
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": st.session_state.username,
                "Planname": plan_name,
                "Trainingstag": day,
                "Übungen": exercises_dict[day],
                "Sätze": sets_dict[day]
            }])], ignore_index=True)
        plans_df.to_csv(PLANS_FILE,index=False)
        st.success("Plan gespeichert!")
        st.session_state.edit_plan = None
        st.experimental_rerun()
else:
    st.session_state.current_plan = choice

# ----------------------
# Trainingsplan trainieren
# ----------------------
if st.session_state.current_plan and choice!="Neuen Plan erstellen":
    plan = st.session_state.current_plan
    plan_days = plans_df[(plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan)]
    day_choice = st.selectbox("Welchen Trainingstag trainieren?", plan_days["Trainingstag"].tolist())
    day_row = plan_days[plan_days["Trainingstag"]==day_choice].iloc[0]

    if pd.isna(day_row["Übungen"]) or day_row["Übungen"].strip()=="":
        st.warning("Für diesen Trainingstag wurden noch keine Übungen eingetragen!")
        exercises = []
        sets_list = []
    else:
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
        last_hist = history_df[(history_df["User"]==st.session_state.username) &
                               (history_df["Plan"]==plan) &
                               (history_df["Trainingstag"]==day_choice) &
                               (history_df["Übung"]==ex)]
        # Maximalperformance bestimmen
        max_perf = None
        if not last_hist.empty:
            last_hist["OneRM"] = last_hist.apply(lambda row: row["Gewicht"]*(1+(row["Wiederholungen"]-1)*0.033), axis=1)
            best_row = last_hist.loc[last_hist["OneRM"].idxmax()]
            st.info(f"Letztes Training (max Leistung): Gewicht {best_row['Gewicht']} kg, Wiederholungen {best_row['Wiederholungen']}, RIR {best_row.get('RIR','?')}")

        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{plan}_{day_choice}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{plan}_{day_choice}_{ex}_{i}_reps")
            rir = cols[2].number_input("RIR", min_value=0, step=1, key=f"{plan}_{day_choice}_{ex}_{i}_rir")
            if weight>0 and reps>0:
                completed_data.append({
                    "User": st.session_state.username,
                    "Plan": plan,
                    "Trainingstag": day_choice,
                    "Übung": ex,
                    "Satz": i+1,
                    "Gewicht": weight,
                    "Wiederholungen": reps,
                    "RIR": rir,
                    "Datum": datetime.now().strftime("%Y-%m-%d %H:%M")
                })

    if st.button("Training speichern"):
        if completed_data:
            df_new = pd.DataFrame(completed_data)
            history_df = pd.concat([history_df, df_new], ignore_index=True)
            history_df.to_csv(HISTORY_FILE, index=False)
            st.success("Training gespeichert!")
            st.balloons()

    st.header(f"📊 Trainingshistorie für {day_choice}")
    hist_user_day = history_df[
        (history_df["User"]==st.session_state.username) &
        (history_df["Plan"]==plan) &
        (history_df["Trainingstag"]==day_choice)
    ]
    st.dataframe(hist_user_day)
