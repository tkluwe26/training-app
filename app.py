import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_cookies_manager import EncryptedCookieManager

# ----------------------
# Cookie Manager (für persistenten Login)
# ----------------------
cookies = EncryptedCookieManager(
    prefix="fittrack_",
    password="fittrack_secret_password"
)

if not cookies.ready():
    st.stop()

# ----------------------
# Seitenlayout
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
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(file, index=False)
    return df

users_df = load_csv(USERS_FILE, ["User","Password"])
plans_df = load_csv(PLANS_FILE, ["User","Planname","Trainingstag","Übungen","Sätze"])
history_df = load_csv(HISTORY_FILE, ["User","Plan","Trainingstag","Übung","Satz","Gewicht","Wiederholungen","RIR","Datum"])

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
# Auto Login über Cookie
# ----------------------
if not st.session_state.user_logged_in:
    if "username" in cookies:
        st.session_state.username = cookies["username"]
        st.session_state.user_logged_in = True
        st.session_state.is_admin = cookies["username"] == "admin"

# ----------------------
# Logout
# ----------------------
if st.session_state.user_logged_in:
    if st.sidebar.button("Abmelden"):
        st.session_state.user_logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.session_state.current_plan = None
        st.session_state.edit_plan = None

        if "username" in cookies:
            del cookies["username"]
            cookies.save()

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
    if mode=="Registrieren":
        if st.sidebar.button("Registrieren"):
            if username_input.strip()=="" or password_input.strip()=="":
                st.sidebar.error("Bitte Benutzername & Passwort eingeben")

            elif username_input in users_df["User"].values:
                st.sidebar.error("Benutzername existiert bereits")

            else:
                users_df = pd.concat([users_df, pd.DataFrame([{
                    "User": username_input,
                    "Password": password_input
                }])], ignore_index=True)

                users_df.to_csv(USERS_FILE, index=False)
                st.sidebar.success("Registrierung erfolgreich")

    # Login
    if st.sidebar.button("Anmelden"):

        if username_input=="admin" and password_input=="adminpasswort":
            st.session_state.user_logged_in = True
            st.session_state.username = "admin"
            st.session_state.is_admin = True

            cookies["username"] = "admin"
            cookies.save()

            st.experimental_rerun()

        else:
            row = users_df[(users_df["User"]==username_input) &
                           (users_df["Password"]==password_input)]

            if not row.empty:

                st.session_state.user_logged_in = True
                st.session_state.username = username_input

                cookies["username"] = username_input
                cookies.save()

                st.experimental_rerun()

            else:
                st.sidebar.error("Falsche Login-Daten")

    st.stop()

# ----------------------
# Admin Ansicht
# ----------------------
if st.session_state.is_admin:

    st.header("📋 Registrierte Accounts")

    st.dataframe(users_df)

    st.subheader("Accounts löschen")

    for user in users_df["User"]:
        if user != "admin":

            col1, col2 = st.columns([4,1])

            col1.write(user)

            if col2.button("Löschen", key=f"delete_{user}"):

                users_df = users_df[users_df["User"]!=user]
                users_df.to_csv(USERS_FILE,index=False)

                plans_df = plans_df[plans_df["User"]!=user]
                plans_df.to_csv(PLANS_FILE,index=False)

                history_df = history_df[history_df["User"]!=user]
                history_df.to_csv(HISTORY_FILE,index=False)

                st.success(f"{user} gelöscht")
                st.experimental_rerun()

    st.stop()

# ----------------------
# User Bereich
# ----------------------
st.header(f"Willkommen {st.session_state.username}")

user_plans = list(
    plans_df[plans_df["User"]==st.session_state.username]["Planname"].unique()
)

st.subheader("Trainingspläne")

# ----------------------
# Planliste
# ----------------------
if user_plans:

    for plan in user_plans:

        col1,col2,col3 = st.columns([3,1,1])

        col1.write(plan)

        if col2.button("Bearbeiten", key=f"edit_{plan}"):
            st.session_state.edit_plan = plan
            st.experimental_rerun()

        if col3.button("Löschen", key=f"del_{plan}"):

            plans_df = plans_df[
                ~((plans_df["User"]==st.session_state.username) &
                  (plans_df["Planname"]==plan))
            ]

            plans_df.to_csv(PLANS_FILE,index=False)

            history_df = history_df[
                ~((history_df["User"]==st.session_state.username) &
                  (history_df["Plan"]==plan))
            ]

            history_df.to_csv(HISTORY_FILE,index=False)

            st.experimental_rerun()

# ----------------------
# Plan auswählen
# ----------------------
if user_plans:

    options = user_plans + ["Neuen Plan erstellen"]
    choice = st.selectbox("Plan auswählen", options)

else:
    choice = "Neuen Plan erstellen"

# ----------------------
# Plan erstellen
# ----------------------
if choice=="Neuen Plan erstellen":

    st.subheader("Neuen Trainingsplan erstellen")

    plan_name = st.text_input("Planname")

    days = st.number_input("Trainingstage",1,7,3)

    day_names = []

    for i in range(days):
        day_names.append(
            st.text_input(f"Tag {i+1}", value=f"Tag {i+1}")
        )

    exercises_dict={}
    sets_dict={}

    for day in day_names:

        exercises_dict[day]=st.text_area(f"Übungen {day}")
        sets_dict[day]=st.text_area(f"Sätze {day}")

    if st.button("Plan speichern"):

        for day in day_names:

            plans_df = pd.concat([plans_df,pd.DataFrame([{

                "User":st.session_state.username,
                "Planname":plan_name,
                "Trainingstag":day,
                "Übungen":exercises_dict[day],
                "Sätze":sets_dict[day]

            }])])

        plans_df.to_csv(PLANS_FILE,index=False)

        st.success("Plan gespeichert")
        st.experimental_rerun()

# ----------------------
# Training
# ----------------------
elif choice!="Neuen Plan erstellen":

    plan=choice

    plan_days = plans_df[
        (plans_df["User"]==st.session_state.username) &
        (plans_df["Planname"]==plan)
    ]

    day_choice = st.selectbox(
        "Trainingstag",
        plan_days["Trainingstag"].tolist()
    )

    row = plan_days[plan_days["Trainingstag"]==day_choice].iloc[0]

    exercises = [x.strip() for x in row["Übungen"].split(",") if x.strip()]
    sets = [int(x.strip()) for x in row["Sätze"].split(",")]

    st.header(day_choice)

    completed=[]

    for i,ex in enumerate(exercises):

        st.subheader(ex)

        for s in range(sets[i]):

            col1,col2,col3,col4 = st.columns(4)

            col1.write(f"Satz {s+1}")

            weight = col2.number_input(
                "Gewicht",
                key=f"{ex}_{s}_w"
            )

            reps = col3.number_input(
                "Wiederholungen",
                key=f"{ex}_{s}_r"
            )

            rir = col4.number_input(
                "RIR",
                min_value=0,
                max_value=10,
                key=f"{ex}_{s}_rir"
            )

            if weight>0 or reps>0:

                completed.append({

                    "User":st.session_state.username,
                    "Plan":plan,
                    "Trainingstag":day_choice,
                    "Übung":ex,
                    "Satz":s+1,
                    "Gewicht":weight,
                    "Wiederholungen":reps,
                    "RIR":rir,
                    "Datum":datetime.now().strftime("%Y-%m-%d %H:%M")

                })

    if st.button("Training speichern"):

        df_new = pd.DataFrame(completed)

        history_df = pd.concat([history_df,df_new])

        history_df.to_csv(HISTORY_FILE,index=False)

        st.success("Training gespeichert")

    st.subheader("Trainingshistorie")

    hist = history_df[
        (history_df["User"]==st.session_state.username) &
        (history_df["Plan"]==plan) &
        (history_df["Trainingstag"]==day_choice)
    ]

    st.dataframe(hist)
