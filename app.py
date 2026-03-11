import streamlit as st
import pandas as pd
import os

# Datei für User-Daten
USERS_FILE = "users.csv"

# CSV initialisieren, falls sie nicht existiert
if not os.path.exists(USERS_FILE):
    pd.DataFrame(columns=["username","password"]).to_csv(USERS_FILE,index=False)

# User-Daten laden
users_df = pd.read_csv(USERS_FILE)

# Session-State für Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False

# Logout Funktion
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.admin_mode = False
    st.experimental_rerun()

# Registrierung
def register():
    st.subheader("Register")
    username = st.text_input("Username", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        if username in users_df["username"].values:
            st.error("Username already exists")
        else:
            users_df.loc[len(users_df)] = [username,password]
            users_df.to_csv(USERS_FILE,index=False)
            st.success("Registered successfully! Please login.")

# Login
def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        global users_df
        # Admin Login
        if username=="admin" and password=="adminpasswort":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.admin_mode = True
        # Normaler User
        elif username in users_df["username"].values and users_df.loc[users_df["username"]==username,"password"].values[0]==password:
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Invalid credentials")
        st.experimental_rerun()

# Admin Panel
def admin_panel():
    st.subheader("Admin Panel: All Users")
    st.write(users_df)

# Main App
if not st.session_state.logged_in:
    st.title("Multi-User App")
    action = st.radio("Choose action", ["Login","Register"])
    if action=="Login":
        login()
    else:
        register()
else:
    st.write(f"Welcome {st.session_state.username}!")
    if st.session_state.admin_mode:
        admin_panel()
    st.success("Glückwunsch, der Login hat funktioniert!")
    if st.button("Logout"):
        logout()
