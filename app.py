import streamlit as st
import pandas as pd
from datetime import datetime
import os
import altair as alt

st.set_page_config(page_title="FitTrack", page_icon="💪", layout="wide")
st.title("Progress – Training by Till 💪")

# ----------------------
# Dateien
# ----------------------

USERS_FILE = "users.csv"
PLANS_FILE = "plans.csv"
HISTORY_FILE = "history.csv"
AUTOSAVE_FILE = "autosave.csv"
TRAINING_AUTOSAVE_FILE = "training_autosave.csv"


# ----------------------
# CSV Loader
# ----------------------

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


# ----------------------
# Autosave Trainingsplan
# ----------------------

def load_autosave():
    if os.path.exists(AUTOSAVE_FILE):
        return pd.read_csv(AUTOSAVE_FILE)
    else:
        return pd.DataFrame(columns=["User","Planname","Trainingstag","Übungen","Sätze"])

autosave_df = load_autosave()

def save_autosave():
    autosave_df.to_csv(AUTOSAVE_FILE, index=False)


# ----------------------
# Autosave Training
# ----------------------

def load_training_autosave():
    if os.path.exists(TRAINING_AUTOSAVE_FILE):
        return pd.read_csv(TRAINING_AUTOSAVE_FILE)
    else:
        return pd.DataFrame(columns=[
            "User","Plan","Trainingstag","Übung","Satz",
            "Gewicht","Wiederholungen","RIR"
        ])

training_autosave_df = load_training_autosave()

def save_training_autosave():
    training_autosave_df.to_csv(TRAINING_AUTOSAVE_FILE, index=False)


# ----------------------
# Session State
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
# Login
# ----------------------

if not st.session_state.user_logged_in:

    st.sidebar.header("Login / Registrierung")

    mode = st.sidebar.radio("Modus", ["Login","Registrieren"])

    username_input = st.sidebar.text_input("Benutzername")
    password_input = st.sidebar.text_input("Passwort", type="password")

    if mode=="Registrieren" and st.sidebar.button("Registrieren"):

        if username_input in users_df["User"].values:
            st.sidebar.error("Benutzer existiert bereits")

        else:

            users_df = pd.concat([users_df,pd.DataFrame([{
                "User":username_input,
                "Password":password_input
            }])],ignore_index=True)

            users_df.to_csv(USERS_FILE,index=False)

            st.sidebar.success("Registrierung erfolgreich")


    if st.sidebar.button("Anmelden"):

        row = users_df[
            (users_df["User"]==username_input) &
            (users_df["Password"]==password_input)
        ]

        if not row.empty:

            st.session_state.user_logged_in=True
            st.session_state.username=username_input

            st.rerun()

        else:

            st.sidebar.error("Login fehlgeschlagen")

    st.stop()


# ----------------------
# User
# ----------------------

st.header(f"Willkommen {st.session_state.username}")

user_plans = list(
    plans_df[
        plans_df["User"]==st.session_state.username
    ]["Planname"].unique()
)

st.subheader("Trainingsplan auswählen")

if user_plans:

    options=user_plans+["Neuen Plan erstellen"]

    choice=st.selectbox("Plan",options)

else:

    choice="Neuen Plan erstellen"


# ----------------------
# Plan erstellen / bearbeiten
# ----------------------

if choice=="Neuen Plan erstellen":

    st.subheader("Neuer Plan")

    plan_name=st.text_input("Planname")

    num_days=st.number_input("Trainingstage",1,7,3)

    day_names=[
        st.text_input(f"Tag {i+1}",value=f"Tag {i+1}",key=f"day{i}")
        for i in range(num_days)
    ]

    exercises_dict={}
    sets_dict={}

    for day in day_names:

        autosave_row=autosave_df[
            (autosave_df["User"]==st.session_state.username) &
            (autosave_df["Planname"]==plan_name) &
            (autosave_df["Trainingstag"]==day)
        ]

        default_ex = autosave_row["Übungen"].values[0] if not autosave_row.empty else ""
        default_sets = autosave_row["Sätze"].values[0] if not autosave_row.empty else ""

        exercises_dict[day]=st.text_area(
            f"Übungen {day}",
            value=default_ex
        )

        sets_dict[day]=st.text_area(
            f"Sätze {day}",
            value=default_sets
        )

        if not autosave_row.empty:

            autosave_df.loc[autosave_row.index,"Übungen"]=exercises_dict[day]
            autosave_df.loc[autosave_row.index,"Sätze"]=sets_dict[day]

        else:

            autosave_df=pd.concat([
                autosave_df,
                pd.DataFrame([{
                    "User":st.session_state.username,
                    "Planname":plan_name,
                    "Trainingstag":day,
                    "Übungen":exercises_dict[day],
                    "Sätze":sets_dict[day]
                }])
            ])

    save_autosave()

    if st.button("Plan speichern"):

        for day in day_names:

            plans_df=pd.concat([
                plans_df,
                pd.DataFrame([{
                    "User":st.session_state.username,
                    "Planname":plan_name,
                    "Trainingstag":day,
                    "Übungen":exercises_dict[day],
                    "Sätze":sets_dict[day]
                }])
            ])

        plans_df.to_csv(PLANS_FILE,index=False)

        autosave_df.drop(
            autosave_df[
                autosave_df["Planname"]==plan_name
            ].index,
            inplace=True
        )

        save_autosave()

        st.success("Plan gespeichert")

        st.experimental_rerun()

else:

    st.session_state.current_plan=choice


# ----------------------
# Training
# ----------------------

if st.session_state.current_plan:

    plan=st.session_state.current_plan

    plan_days=plans_df[
        (plans_df["User"]==st.session_state.username) &
        (plans_df["Planname"]==plan)
    ]

    day_choice=st.selectbox(
        "Trainingstag",
        plan_days["Trainingstag"].tolist()
    )

    day_row=plan_days[
        plan_days["Trainingstag"]==day_choice
    ].iloc[0]

    exercises=[ex.strip() for ex in day_row["Übungen"].split(",") if ex.strip()]

    sets_list=[int(s) for s in day_row["Sätze"].split(",")]
    
    completed_data=[]
    
    for idx, ex in enumerate(exercises):

    st.subheader(ex)

    # Letztes Training anzeigen
    last_hist = history_df[
        (history_df["User"] == st.session_state.username) &
        (history_df["Plan"] == plan) &
        (history_df["Trainingstag"] == day_choice) &
        (history_df["Übung"] == ex)
    ]

    previous_pr = None

    if not last_hist.empty:
        last_hist = last_hist.copy()
        last_hist["OneRM"] = last_hist["Gewicht"] * (1 + (last_hist["Wiederholungen"] - 1) * 0.033)
        best_row = last_hist.loc[last_hist["OneRM"].idxmax()]
        previous_pr = best_row["OneRM"]
        st.info(
            f"Letztes Training: {best_row['Gewicht']} kg × {best_row['Wiederholungen']} (RIR {best_row.get('RIR','?')})"
        )

    # Anzahl der Sätze (sicherstellen, dass Sets existieren)
    try:
        num_sets = sets_list[idx]
    except IndexError:
        num_sets = 2  # Standardwert, falls Sätze fehlen

    for i in range(num_sets):

        cols = st.columns(3)

        weight = cols[1].number_input(
            "Gewicht (kg)",
            min_value=0.0,
            step=0.5,
            key=f"{plan}_{day_choice}_{ex}_{i}_weight"
        )

        reps = cols[2].number_input(
            "Wiederholungen",
            min_value=0,
            step=1,
            key=f"{plan}_{day_choice}_{ex}_{i}_reps"
        )

        rir = cols[2].number_input(
            "RIR",
            min_value=0,
            step=1,
            key=f"{plan}_{day_choice}_{ex}_{i}_rir"
        )

        # PR-Check + Belohnung
        if weight > 0 and reps > 0:
            current_orm = weight * (1 + (reps - 1) * 0.033)

            pr_key = f"{plan}_{day_choice}_{ex}_pr"
            if st.session_state.get(pr_key, 0) < current_orm:
                st.session_state[pr_key] = current_orm
                st.success("🏆 Neuer Personal Record!")
                st.balloons()

            # Autosave in session_state
            autosave_key = f"{plan}_{day_choice}_{ex}_{i}"
            st.session_state[autosave_key] = {"weight": weight, "reps": reps, "rir": rir}

            completed_data.append({
                "User": st.session_state.username,
                "Plan": plan,
                "Trainingstag": day_choice,
                "Übung": ex,
                "Satz": i + 1,
                "Gewicht": weight,
                "Wiederholungen": reps,
                "RIR": rir,
                "Datum": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

            save_training_autosave()

            if weight>0 and reps>0:

                completed_data.append({
                    "User":st.session_state.username,
                    "Plan":plan,
                    "Trainingstag":day_choice,
                    "Übung":ex,
                    "Satz":i+1,
                    "Gewicht":weight,
                    "Wiederholungen":reps,
                    "RIR":rir,
                    "Datum":datetime.now().strftime("%Y-%m-%d %H:%M")
                })


# ----------------------
# Training speichern
# ----------------------

    if st.button("Training speichern"):

        if completed_data:

            df_new=pd.DataFrame(completed_data)

            history_df=pd.concat([history_df,df_new])

            history_df.to_csv(HISTORY_FILE,index=False)

            training_autosave_df.drop(
                training_autosave_df[
                    (training_autosave_df["User"]==st.session_state.username) &
                    (training_autosave_df["Plan"]==plan) &
                    (training_autosave_df["Trainingstag"]==day_choice)
                ].index,
                inplace=True
            )

            save_training_autosave()

            st.success("Training gespeichert")

            st.balloons()


# ----------------------
# Progress Graph
# ----------------------

hist_user_day=history_df[
    (history_df["User"]==st.session_state.username) &
    (history_df["Plan"]==plan)&
    (history_df["Trainingstag"] == day_choice)
]

st.subheader("Progress")

for ex in hist_user_day["Übung"].unique():

    exercise_hist=hist_user_day[
        hist_user_day["Übung"]==ex
    ].copy()

    if len(exercise_hist)>1:

        exercise_hist["Datum"]=pd.to_datetime(exercise_hist["Datum"])

        exercise_hist["OneRM"]=exercise_hist["Gewicht"]*(
            1+(exercise_hist["Wiederholungen"]-1)*0.033
        )

        exercise_hist["Datum_only"]=exercise_hist["Datum"].dt.date

        exercise_hist=(
            exercise_hist
            .sort_values("OneRM")
            .groupby("Datum_only")
            .tail(1)
        )

        chart=alt.Chart(exercise_hist).mark_line(point=True).encode(
            x="Datum:T",
            y="OneRM:Q"
        ).properties(
            title=ex
        )

        st.altair_chart(chart,use_container_width=True)
