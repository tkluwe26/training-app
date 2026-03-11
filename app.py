import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- Dateien ---
USERS_FILE = "users.csv"
PLANS_FILE = "plans.csv"
HISTORY_FILE = "history.csv"

# --- CSV Initialisierung ---
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["username","password"]).to_csv(USERS_FILE,index=False)
if not os.path.exists(PLANS_FILE):
    pd.DataFrame(columns=["username","plan_name","day_name","exercise","sets"]).to_csv(PLANS_FILE,index=False)
if not os.path.exists(HISTORY_FILE):
    pd.DataFrame(columns=["username","plan_name","day_name","exercise","weight","reps","rir","date"]).to_csv(HISTORY_FILE,index=False)

# --- Session-State Setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# --- Logout ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.admin_mode = False
    st.experimental_rerun()

# --- Registrierung ---
def register():
    st.subheader("Register")
    users_df = pd.read_csv(USERS_FILE)
    username = st.text_input("Username", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        if username in users_df["username"].values:
            st.error("Username already exists")
        else:
            users_df.loc[len(users_df)] = [username,password]
            users_df.to_csv(USERS_FILE,index=False)
            st.success("Registered successfully! Please login.")

# --- Login ---
def login():
    st.subheader("Login")
    users_df = pd.read_csv(USERS_FILE)
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if username=="admin" and password=="adminpasswort":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.admin_mode = True
            st.success("Logged in as admin")
        elif username in users_df["username"].values:
            user_row = users_df[users_df["username"]==username]
            if user_row["password"].values[0]==password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Logged in as {username}")
            else:
                st.error("Incorrect password")
        else:
            st.error("Username does not exist")
        st.experimental_rerun()

# --- Main ---
st.title("ProFitness Planner")

if not st.session_state.logged_in:
    tab = st.radio("Choose action",["Login","Register"])
    if tab=="Login":
        login()
    else:
        register()
else:
    st.write(f"Welcome {st.session_state.username}")
    if st.button("Logout"):
        logout()
