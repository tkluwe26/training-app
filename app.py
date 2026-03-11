import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="FitTrack", page_icon="💪", layout="wide")

st.title("💪 FitTrack")


# ----------------------------
# Dateien
# ----------------------------

USERS_FILE = "users.csv"
PLANS_FILE = "plans.csv"
HISTORY_FILE = "history.csv"


def load_csv(file, columns):

    if os.path.exists(file):
        return pd.read_csv(file)

    df = pd.DataFrame(columns=columns)
    df.to_csv(file, index=False)
    return df


users_df = load_csv(USERS_FILE, ["user", "password"])
plans_df = load_csv(PLANS_FILE, ["user", "plan", "day", "exercise", "sets"])
history_df = load_csv(
    HISTORY_FILE,
    ["user","plan","day","exercise","set","weight","reps","rir","date"]
)


# ----------------------------
# Session State
# ----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None


# ----------------------------
# Logout
# ----------------------------

def logout():

    st.session_state.logged_in = False
    st.session_state.username = None

    st.rerun()


# ----------------------------
# Login / Register
# ----------------------------

def login_screen():

    st.subheader("Login")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:

        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")

        if st.button("Login"):

            row = users_df[
                (users_df.user == user) &
                (users_df.password == pw)
            ]

            if not row.empty:

                st.session_state.logged_in = True
                st.session_state.username = user

                st.rerun()

            else:
                st.error("Wrong login")

    with tab2:

        new_user = st.text_input("New username")
        new_pw = st.text_input("New password", type="password")

        if st.button("Register"):

            if new_user in users_df.user.values:
                st.error("Username exists")

            else:

                users_df.loc[len(users_df)] = [new_user, new_pw]
                users_df.to_csv(USERS_FILE, index=False)

                st.success("Account created")


# ----------------------------
# Admin Panel
# ----------------------------

def admin_panel():

    st.subheader("Admin Panel")

    st.write(users_df)

    for user in users_df.user:

        if user == "admin":
            continue

        if st.button(f"Delete {user}"):

            users_df.drop(
                users_df[users_df.user == user].index,
                inplace=True
            )

            users_df.to_csv(USERS_FILE, index=False)

            st.rerun()


# ----------------------------
# Plan erstellen
# ----------------------------

def create_plan():

    st.subheader("Create plan")

    plan_name = st.text_input("Plan name")

    num_days = st.number_input("Training days",1,7,3)

    exercises_data = []

    for d in range(num_days):

        st.markdown(f"### Day {d+1}")

        day_name = st.text_input(
            "Day name",
            key=f"dayname{d}"
        )

        num_ex = st.number_input(
            "Exercises",
            1,10,3,
            key=f"exnum{d}"
        )

        for e in range(num_ex):

            ex = st.text_input(
                "Exercise",
                key=f"ex{d}{e}"
            )

            sets = st.number_input(
                "Sets",
                1,10,3,
                key=f"sets{d}{e}"
            )

            exercises_data.append(
                [day_name, ex, sets]
            )

    if st.button("Save plan"):

        for row in exercises_data:

            plans_df.loc[len(plans_df)] = [
                st.session_state.username,
                plan_name,
                row[0],
                row[1],
                row[2]
            ]

        plans_df.to_csv(PLANS_FILE, index=False)

        st.success("Plan saved")


# ----------------------------
# Planliste
# ----------------------------

def show_plans():

    user = st.session_state.username

    user_plans = plans_df[
        plans_df.user == user
    ].plan.unique()

    st.subheader("Your Plans")

    if len(user_plans) == 0:
        st.info("No plans yet")
        return None

    plan = st.selectbox("Select plan", user_plans)

    col1,col2 = st.columns(2)

    if col1.button("Delete plan"):

        plans_df.drop(
            plans_df[plans_df.plan == plan].index,
            inplace=True
        )

        plans_df.to_csv(PLANS_FILE, index=False)

        st.rerun()

    if col2.button("Edit plan"):

        edit_plan(plan)

    return plan


# ----------------------------
# Plan bearbeiten
# ----------------------------

def edit_plan(plan):

    st.subheader("Edit plan")

    plan_rows = plans_df[
        plans_df.plan == plan
    ]

    for i,row in plan_rows.iterrows():

        ex = st.text_input(
            "Exercise",
            value=row.exercise,
            key=f"edit_ex{i}"
        )

        sets = st.number_input(
            "Sets",
            1,10,
            value=int(row.sets),
            key=f"edit_sets{i}"
        )

        plans_df.at[i,"exercise"] = ex
        plans_df.at[i,"sets"] = sets

    if st.button("Save changes"):

        plans_df.to_csv(PLANS_FILE,index=False)

        st.success("Plan updated")


# ----------------------------
# Training
# ----------------------------

def training(plan):

    user = st.session_state.username

    plan_rows = plans_df[
        (plans_df.user == user) &
        (plans_df.plan == plan)
    ]

    days = plan_rows.day.unique()

    day = st.selectbox("Training day", days)

    exercises = plan_rows[
        plan_rows.day == day
    ]

    results = []

    for _,row in exercises.iterrows():

        st.markdown(f"### {row.exercise}")

        for s in range(int(row.sets)):

            c1,c2,c3,c4 = st.columns(4)

            c1.write(f"Set {s+1}")

            weight = c2.number_input(
                "Weight",
                key=f"{row.exercise}{s}w"
            )

            reps = c3.number_input(
                "Reps",
                key=f"{row.exercise}{s}r"
            )

            rir = c4.number_input(
                "RIR",
                0,10,
                key=f"{row.exercise}{s}rir"
            )

            if weight or reps:

                results.append([
                    user,
                    plan,
                    day,
                    row.exercise,
                    s+1,
                    weight,
                    reps,
                    rir,
                    datetime.now()
                ])

    if st.button("Save workout"):

        df = pd.DataFrame(
            results,
            columns=history_df.columns
        )

        new_hist = pd.concat([history_df,df])

        new_hist.to_csv(HISTORY_FILE,index=False)

        st.success("Workout saved")


# ----------------------------
# Historie
# ----------------------------

def show_history(plan):

    user = st.session_state.username

    hist = history_df[
        (history_df.user == user) &
        (history_df.plan == plan)
    ]

    if hist.empty:
        return

    st.subheader("Training History")

    day = st.selectbox(
        "History day",
        hist.day.unique()
    )

    st.dataframe(
        hist[hist.day == day]
    )


# ----------------------------
# APP FLOW
# ----------------------------

if not st.session_state.logged_in:

    login_screen()
    st.stop()


st.sidebar.write(f"Logged in as **{st.session_state.username}**")
st.sidebar.button("Logout", on_click=logout)


if st.session_state.username == "admin":

    admin_panel()

st.divider()

if st.button("Create new plan"):
    create_plan()

plan = show_plans()

if plan:

    training(plan)

    show_history(plan)
