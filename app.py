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

# --- Daten laden ---
users_df = pd.read_csv(USERS_FILE)
plans_df = pd.read_csv(PLANS_FILE)
history_df = pd.read_csv(HISTORY_FILE)

# --- Session-State Setup ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "admin_mode" not in st.session_state:
    st.session_state.admin_mode = False
if "create_step" not in st.session_state:
    st.session_state.create_step = 0
if "new_plan" not in st.session_state:
    st.session_state.new_plan = {}

# --- Logout ---
def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.admin_mode = False
    st.experimental_rerun()

# --- Registrierung ---
def register():
    st.subheader("Register")
    username = st.text_input("Username", key="reg_user")
    password = st.text_input("Password", type="password", key="reg_pass")
    if st.button("Register"):
        global users_df
        if username in users_df["username"].values:
            st.error("Username already exists")
        else:
            users_df.loc[len(users_df)] = [username,password]
            users_df.to_csv(USERS_FILE,index=False)
            st.success("Registered successfully! Please login.")

# --- Login ---
def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        global users_df
        if username=="admin" and password=="adminpasswort":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.admin_mode = True
        elif username in users_df["username"].values and users_df.loc[users_df["username"]==username,"password"].values[0]==password:
            st.session_state.logged_in = True
            st.session_state.username = username
        else:
            st.error("Invalid credentials")
        st.experimental_rerun()

# --- Admin Panel ---
def admin_panel():
    st.subheader("Admin Panel: Users")
    st.write(users_df)
    delete_user = st.selectbox("Select user to delete", [""] + list(users_df["username"]))
    if st.button("Delete user"):
        if delete_user and delete_user != "admin":
            users_df.drop(users_df[users_df["username"]==delete_user].index,inplace=True)
            users_df.to_csv(USERS_FILE,index=False)
            st.success(f"Deleted user {delete_user}")
            st.experimental_rerun()

# --- Schritt-für-Schritt Plan-Erstellung ---
def create_plan():
    st.subheader("Create a new plan")
    # Schritt 1: Planname + Anzahl Tage
    if st.session_state.create_step==0:
        plan_name = st.text_input("Plan name", key="plan_name_input")
        num_days = st.number_input("Number of training days", 1, 7, 3, key="num_days_input")
        if st.button("Next"):
            st.session_state.new_plan = {"name":plan_name,"num_days":num_days,"days":[]}
            for _ in range(num_days):
                st.session_state.new_plan["days"].append({"day_name":"","exercises":[]})
            st.session_state.create_step=1
            st.experimental_rerun()
    # Schritt 2: Day Names
    elif st.session_state.create_step==1:
        st.write("Name your training days")
        for i,day in enumerate(st.session_state.new_plan["days"]):
            day_name = st.text_input(f"Day {i+1} name", key=f"dayname_{i}", value=day["day_name"])
            st.session_state.new_plan["days"][i]["day_name"] = day_name
        if st.button("Next"):
            st.session_state.create_step = 2
            st.experimental_rerun()
    # Schritt 3: Exercises
    elif st.session_state.create_step==2:
        st.write("Add exercises per day")
        for i,day in enumerate(st.session_state.new_plan["days"]):
            st.markdown(f"### {day['day_name']}")
            num_ex = st.number_input(f"Number of exercises for {day['day_name']}",1,10,len(day["exercises"]) if day["exercises"] else 1,key=f"numex_{i}")
            while len(day["exercises"])<num_ex:
                day["exercises"].append({"name":"","sets":1})
            for j,ex in enumerate(day["exercises"]):
                ex_name = st.text_input(f"Exercise {j+1} name", key=f"ex_{i}_{j}", value=ex["name"])
                sets = st.number_input(f"Sets for {ex_name or 'exercise'}",1,10,ex["sets"], key=f"sets_{i}_{j}")
                ex["name"] = ex_name
                ex["sets"] = sets
        if st.button("Save plan"):
            # CSV speichern
            global plans_df
            for day in st.session_state.new_plan["days"]:
                for ex in day["exercises"]:
                    plans_df.loc[len(plans_df)] = [
                        st.session_state.username,
                        st.session_state.new_plan["name"],
                        day["day_name"],
                        ex["name"],
                        ex["sets"]
                    ]
            plans_df.to_csv(PLANS_FILE,index=False)
            st.success("Plan saved")
            st.session_state.create_step=0
            st.session_state.new_plan={}
            st.experimental_rerun()

# --- Training durchführen ---
def train_plan():
    st.subheader("Train a plan")
    user_plans = plans_df[plans_df["username"]==st.session_state.username]["plan_name"].unique()
    plan_selected = st.selectbox("Plan",[""]+list(user_plans))
    if plan_selected:
        plan_days = plans_df[(plans_df["username"]==st.session_state.username)&(plans_df["plan_name"]==plan_selected)]["day_name"].unique()
        day_selected = st.selectbox("Training day",[""]+list(plan_days))
        if day_selected:
            day_exs = plans_df[(plans_df["username"]==st.session_state.username)&
                               (plans_df["plan_name"]==plan_selected)&
                               (plans_df["day_name"]==day_selected)]
            st.write(f"### {day_selected} exercises")
            for idx,row in day_exs.iterrows():
                weight = st.number_input(f"Weight {row['exercise']}",value=0,key=f"w_{idx}")
                reps = st.number_input(f"Reps {row['exercise']}",value=0,key=f"r_{idx}")
                rir = st.number_input(f"RIR {row['exercise']}",value=0,key=f"rir_{idx}")
                if st.button(f"Save {row['exercise']}",key=f"save_{idx}"):
                    global history_df
                    history_df.loc[len(history_df)] = [
                        st.session_state.username,
                        plan_selected,
                        day_selected,
                        row["exercise"],
                        weight,
                        reps,
                        rir,
                        datetime.now().strftime("%Y-%m-%d %H:%M")
                    ]
                    history_df.to_csv(HISTORY_FILE,index=False)
                    st.success(f"Saved {row['exercise']}")

# --- Trainingshistorie pro Tag ---
def view_history():
    st.subheader("Training History")
    user_plans = plans_df[plans_df["username"]==st.session_state.username]["plan_name"].unique()
    plan_selected = st.selectbox("Plan to view history",[""]+list(user_plans),key="hist_plan")
    if plan_selected:
        plan_days = plans_df[(plans_df["username"]==st.session_state.username)&(plans_df["plan_name"]==plan_selected)]["day_name"].unique()
        day_selected = st.selectbox("Day to view history",[""]+list(plan_days),key="hist_day")
        if day_selected:
            day_hist = history_df[(history_df["username"]==st.session_state.username)&
                                  (history_df["plan_name"]==plan_selected)&
                                  (history_df["day_name"]==day_selected)]
            st.write(day_hist)

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
    if st.session_state.admin_mode:
        admin_panel()
    st.write("---")
    col1,col2 = st.columns(2)
    with col1:
        create_plan()
    with col2:
        train_plan()
        view_history()
