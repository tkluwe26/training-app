import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager

# -------------------------
# Cookie Manager
# -------------------------

cookies = EncryptedCookieManager(
    prefix="fittrack_",
    password="fittrack_secret"
)

if not cookies.ready():
    st.stop()

# -------------------------
# Page
# -------------------------

st.set_page_config(
    page_title="FitTrack",
    page_icon="💪",
    layout="wide"
)

st.title("💪 FitTrack")

# -------------------------
# Files
# -------------------------

USERS_FILE="users.csv"
PLANS_FILE="plans.csv"
HISTORY_FILE="history.csv"


def load_csv(file,cols):

    if os.path.exists(file):
        return pd.read_csv(file)

    df=pd.DataFrame(columns=cols)
    df.to_csv(file,index=False)
    return df


users_df=load_csv(USERS_FILE,["user","password"])

plans_df=load_csv(
    PLANS_FILE,
    ["user","plan","day","exercise","sets"]
)

history_df=load_csv(
    HISTORY_FILE,
    ["user","plan","day","exercise","set","weight","reps","rir","date"]
)

# -------------------------
# Session
# -------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False

if "username" not in st.session_state:
    st.session_state.username=None

# -------------------------
# Auto Login
# -------------------------

if not st.session_state.logged_in:

    if "username" in cookies:

        st.session_state.logged_in=True
        st.session_state.username=cookies["username"]

# -------------------------
# Logout
# -------------------------

if st.session_state.logged_in:

    if st.sidebar.button("Logout"):

        st.session_state.logged_in=False
        st.session_state.username=None

        if "username" in cookies:
            del cookies["username"]
            cookies.save()

        st.rerun()

# -------------------------
# Login
# -------------------------

if not st.session_state.logged_in:

    st.sidebar.header("Login")

    username=st.sidebar.text_input("Username")
    password=st.sidebar.text_input("Password",type="password")

    mode=st.sidebar.radio("Mode",["Login","Register"])

    if st.sidebar.button("Submit"):

        if mode=="Register":

            if username in users_df["user"].values:

                st.sidebar.error("User exists")

            else:

                users_df.loc[len(users_df)]=[username,password]

                users_df.to_csv(USERS_FILE,index=False)

                st.sidebar.success("Account created")

        else:

            row=users_df[
                (users_df.user==username) &
                (users_df.password==password)
            ]

            if not row.empty:

                st.session_state.logged_in=True
                st.session_state.username=username

                cookies["username"]=username
                cookies.save()

                st.rerun()

            else:

                st.sidebar.error("Wrong login")

    st.stop()

# -------------------------
# Welcome
# -------------------------

st.header(f"Welcome {st.session_state.username}")

# -------------------------
# Plans
# -------------------------

user=st.session_state.username

user_plans=plans_df[
    plans_df.user==user
]["plan"].unique()

st.subheader("Plans")

if len(user_plans)>0:

    for plan in user_plans:

        col1,col2=st.columns([4,1])

        col1.write(plan)

        if col2.button("Delete",key=plan):

            plans_df=plans_df[plans_df.plan!=plan]
            plans_df.to_csv(PLANS_FILE,index=False)

            st.rerun()

# -------------------------
# Plan Select
# -------------------------

options=list(user_plans)+["Create new"]

choice=st.selectbox("Select plan",options)

# -------------------------
# Create Plan
# -------------------------

if choice=="Create new":

    st.subheader("Create Plan")

    plan_name=st.text_input("Plan name")

    day=st.text_input("Training day")

    exercise=st.text_input("Exercise")

    sets=st.number_input("Sets",1,10,3)

    if st.button("Add exercise"):

        plans_df.loc[len(plans_df)]=[
            user,
            plan_name,
            day,
            exercise,
            sets
        ]

        plans_df.to_csv(PLANS_FILE,index=False)

        st.success("Exercise added")

# -------------------------
# Training
# -------------------------

else:

    plan=choice

    plan_rows=plans_df[
        (plans_df.user==user)&
        (plans_df.plan==plan)
    ]

    days=plan_rows.day.unique()

    day_choice=st.selectbox("Day",days)

    exercises=plan_rows[
        plan_rows.day==day_choice
    ]

    st.header(day_choice)

    results=[]

    for _,row in exercises.iterrows():

        st.subheader(row.exercise)

        for s in range(int(row.sets)):

            c1,c2,c3,c4=st.columns(4)

            c1.write(f"Set {s+1}")

            weight=c2.number_input(
                "Weight",
                key=f"{row.exercise}{s}w"
            )

            reps=c3.number_input(
                "Reps",
                key=f"{row.exercise}{s}r"
            )

            rir=c4.number_input(
                "RIR",
                0,
                10,
                key=f"{row.exercise}{s}rir"
            )

            if weight or reps:

                results.append([
                    user,
                    plan,
                    day_choice,
                    row.exercise,
                    s+1,
                    weight,
                    reps,
                    rir,
                    datetime.now()
                ])

    if st.button("Save workout"):

        df=pd.DataFrame(
            results,
            columns=history_df.columns
        )

        history_df=pd.concat([history_df,df])

        history_df.to_csv(HISTORY_FILE,index=False)

        st.success("Workout saved")

# -------------------------
# History
# -------------------------

st.subheader("History")

hist=history_df[
    (history_df.user==user)
]

st.dataframe(hist)
