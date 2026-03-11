import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager


# ----------------------------
# CONFIG
# ----------------------------

st.set_page_config(
    page_title="FitTrack",
    page_icon="💪",
    layout="wide"
)

st.title("💪 FitTrack")


# ----------------------------
# COOKIE LOGIN
# ----------------------------

cookies = EncryptedCookieManager(
    prefix="fittrack_",
    password="super_secret_password"
)

if not cookies.ready():
    st.stop()


# ----------------------------
# FILES
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


users_df = load_csv(
    USERS_FILE,
    ["user", "password"]
)

plans_df = load_csv(
    PLANS_FILE,
    ["user", "plan", "day", "exercise", "sets"]
)

history_df = load_csv(
    HISTORY_FILE,
    ["user","plan","day","exercise","set","weight","reps","rir","date"]
)


# ----------------------------
# SESSION STATE
# ----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None


# ----------------------------
# AUTO LOGIN
# ----------------------------

if not st.session_state.logged_in:

    if "username" in cookies:
        st.session_state.logged_in = True
        st.session_state.username = cookies["username"]


# ----------------------------
# LOGOUT
# ----------------------------

def logout():

    st.session_state.logged_in = False
    st.session_state.username = None

    if "username" in cookies:
        del cookies["username"]
        cookies.save()

    st.rerun()


# ----------------------------
# LOGIN SCREEN
# ----------------------------

def login_screen():

    st.sidebar.header("Login")

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    mode = st.sidebar.radio("Mode", ["Login","Register"])

    if st.sidebar.button("Submit"):

        if mode == "Register":

            if username in users_df.user.values:
                st.sidebar.error("User exists")

            else:

                users_df.loc[len(users_df)] = [
                    username,
                    password
                ]

                users_df.to_csv(USERS_FILE,index=False)

                st.sidebar.success("Account created")

        else:

            row = users_df[
                (users_df.user == username) &
                (users_df.password == password)
            ]

            if not row.empty:

                st.session_state.logged_in = True
                st.session_state.username = username

                cookies["username"] = username
                cookies.save()

                st.rerun()

            else:

                st.sidebar.error("Wrong login")


# ----------------------------
# CREATE PLAN
# ----------------------------

def create_plan():

    st.subheader("Create new plan")

    plan = st.text_input("Plan name")
    day = st.text_input("Training day")
    exercise = st.text_input("Exercise")
    sets = st.number_input("Sets",1,10,3)

    if st.button("Add exercise"):

        plans_df.loc[len(plans_df)] = [
            st.session_state.username,
            plan,
            day,
            exercise,
            sets
        ]

        plans_df.to_csv(PLANS_FILE,index=False)

        st.success("Exercise added")


# ----------------------------
# PLAN LIST
# ----------------------------

def show_plans():

    user = st.session_state.username

    user_plans = plans_df[
        plans_df.user == user
    ].plan.unique()

    st.subheader("Your plans")

    if len(user_plans) == 0:
        st.info("No plans yet")

    for plan in user_plans:

        col1,col2 = st.columns([4,1])

        col1.write(plan)

        if col2.button("Delete",key=plan):

            plans_df.drop(
                plans_df[plans_df.plan == plan].index,
                inplace=True
            )

            plans_df.to_csv(PLANS_FILE,index=False)

            st.rerun()

    return user_plans


# ----------------------------
# TRAINING
# ----------------------------

def training(plan):

    user = st.session_state.username

    plan_rows = plans_df[
        (plans_df.user == user) &
        (plans_df.plan == plan)
    ]

    days = plan_rows.day.unique()

    day = st.selectbox("Training day",days)

    exercises = plan_rows[
        plan_rows.day == day
    ]

    st.header(day)

    results = []

    for _,row in exercises.iterrows():

        st.subheader(row.exercise)

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
                0,
                10,
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
            columns = history_df.columns
        )

        new_history = pd.concat([history_df,df])

        new_history.to_csv(HISTORY_FILE,index=False)

        st.success("Workout saved")


# ----------------------------
# HISTORY
# ----------------------------

def show_history():

    user = st.session_state.username

    st.subheader("History")

    hist = history_df[
        history_df.user == user
    ]

    st.dataframe(hist)


# ----------------------------
# MAIN APP
# ----------------------------

if not st.session_state.logged_in:

    login_screen()
    st.stop()

st.sidebar.button("Logout", on_click=logout)

st.header(f"Welcome {st.session_state.username}")

plans = show_plans()

options = list(plans) + ["Create new plan"]

choice = st.selectbox("Select plan", options)

if choice == "Create new plan":

    create_plan()

else:

    training(choice)

show_history()
