import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Multi-User Trainings-App", layout="wide")
st.title("🏋️ Mehrbenutzer Trainings-App mit Registrierung")

# ------------------------------
# Admin Passwort
# ------------------------------
ADMIN_PASSWORD = "meinAdminPasswort"  # <-- Hier dein Admin-Passwort eintragen

# ------------------------------
# CSV-Dateien
# ------------------------------
users_file = "users.csv"
plans_file = "plans.csv"
history_file = "training_history.csv"

# ------------------------------
# CSV-Dateien laden oder erstellen
# ------------------------------
if os.path.exists(users_file):
    users_df = pd.read_csv(users_file)
else:
    users_df = pd.DataFrame(columns=["User", "Password"])

if os.path.exists(plans_file):
    plans_df = pd.read_csv(plans_file)
else:
    plans_df = pd.DataFrame(columns=["User", "Planname", "Trainingstag", "Übungen", "Sätze"])

# ------------------------------
# Sidebar: Login oder Registrierung
# ------------------------------
st.sidebar.header("Anmeldung oder Registrierung")
mode = st.sidebar.radio("Modus", ["Login", "Registrieren"])

username = st.sidebar.text_input("Benutzername")
password = st.sidebar.text_input("Passwort", type="password")

if mode == "Registrieren":
    register = st.sidebar.button("Registrieren")
    if register:
        if username.strip() == "" or password.strip() == "":
            st.sidebar.error("Benutzername und Passwort dürfen nicht leer sein")
        elif username in users_df["User"].values:
            st.sidebar.error("Benutzername existiert bereits")
        else:
            users_df = pd.concat([users_df, pd.DataFrame([{"User": username, "Password": password}])], ignore_index=True)
            users_df.to_csv(users_file, index=False)
            st.sidebar.success("Registrierung erfolgreich! Du kannst dich jetzt einloggen")
            st.stop()

login = st.sidebar.button("Anmelden")
if login:
    if password == ADMIN_PASSWORD:
        is_admin = True
        st.sidebar.success("Admin angemeldet")
        user_logged_in = True
    else:
        is_admin = False
        user_row = users_df[(users_df["User"] == username) & (users_df["Password"] == password)]
        if not user_row.empty:
            st.sidebar.success(f"Willkommen {username}")
            user_logged_in = True
        else:
            st.sidebar.error("Benutzername oder Passwort falsch")
            user_logged_in = False
else:
    user_logged_in = False

if not user_logged_in:
    st.stop()

# ------------------------------
# Trainingsplan auswählen / erstellen
# ------------------------------
if is_admin:
    st.sidebar.info("Admin-Modus: Siehe alle Benutzerpläne")
    user_filter = st.sidebar.selectbox("Filter Benutzer (Admin)", options=["Alle"] + users_df["User"].tolist())
else:
    user_filter = username

# Filter Trainingspläne
if is_admin and user_filter != "Alle":
    plans_user_df = plans_df[plans_df["User"] == user_filter]
elif not is_admin:
    plans_user_df = plans_df[plans_df["User"] == username]
else:
    plans_user_df = plans_df  # Admin & Alle

plans = plans_user_df["Planname"].unique().tolist()
plans.append("Neuer Plan")

st.sidebar.header("Trainingsplan auswählen / erstellen")
selected_plan = st.sidebar.selectbox("Wähle einen Trainingsplan", plans)

# ------------------------------
# Neuen Plan erstellen
# ------------------------------
if selected_plan == "Neuer Plan" and not is_admin:
    new_plan_name = st.sidebar.text_input("Name des neuen Trainingsplans")
    num_days = st.sidebar.slider("Wie viele Trainingstage soll der Plan haben?", 1, 7, 3)
    create_plan = st.sidebar.button("Plan erstellen")
    if create_plan and new_plan_name:
        for i in range(1, num_days + 1):
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": username,
                "Planname": new_plan_name,
                "Trainingstag": f"Tag {i}",
                "Übungen": "",
                "Sätze": ""
            }])], ignore_index=True)
        plans_df.to_csv(plans_file, index=False)
        st.success(f"Trainingsplan '{new_plan_name}' erstellt!")
        selected_plan = new_plan_name

# ------------------------------
# Trainingsplan laden
# ------------------------------
if selected_plan != "Neuer Plan":
    plan_days = plans_df[plans_df["Planname"] == selected_plan]
    if not is_admin:
        plan_days = plan_days[plan_days["User"] == username]
    elif is_admin and user_filter != "Alle":
        plan_days = plan_days[plan_days["User"] == user_filter]
    
    plan_days_list = plan_days["Trainingstag"].tolist()
    
    selected_day = st.selectbox("Welchen Trainingstag möchtest du heute trainieren?", plan_days_list)
    
    day_row = plans_df[(plans_df["Planname"] == selected_plan) &
                       (plans_df["Trainingstag"] == selected_day)].iloc[0]
    
    # Übungen und Sätze bearbeiten
    st.subheader(f"Übungen für {selected_day} bearbeiten")
    exercises_input = st.text_area("Übungen (kommagetrennt)", value=day_row["Übungen"], height=80)
    sets_input = st.text_area("Sätze pro Übung (kommagetrennt)", value=day_row["Sätze"], height=80)
    
    exercises = [ex.strip() for ex in exercises_input.split(",") if ex.strip()]
    sets_list = []
    if sets_input:
        sets_list = [int(s.strip()) if s.strip().isdigit() else 2 for s in sets_input.split(",")]
    if len(sets_list) < len(exercises):
        sets_list += [2] * (len(exercises) - len(sets_list))
    
    if st.button("Speichern"):
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Übungen"] = exercises_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "Sätze"] = sets_input
        plans_df.loc[(plans_df["Planname"] == selected_plan) & (plans_df["Trainingstag"] == selected_day), "User"] = username
        plans_df.to_csv(plans_file, index=False)
        st.success("Trainingstag gespeichert!")

    # ------------------------------
    # Training durchführen
    # ------------------------------
    st.header(f"Training durchführen für {selected_day}")
    completed_data = []
    
    for idx, ex in enumerate(exercises):
        num_sets = sets_list[idx] if idx < len(sets_list) else 2
        st.subheader(ex)
        for i in range(num_sets):
            cols = st.columns(3)
            cols[0].write(f"Satz {i+1}")
            weight = cols[1].number_input("Gewicht (kg)", min_value=0.0, step=0.5, key=f"{username}_{selected_plan}_{selected_day}_{ex}_{i}_weight")
            reps = cols[2].number_input("Wiederholungen", min_value=0, step=1, key=f"{username}_{selected_plan}_{selected_day}_{ex}_{i}_reps")
            if weight > 0 and reps > 0:
                completed_data.append({
                    "User": username,
                    "Plan": selected_plan,
                    "Trainingstag": selected_day,
                    "Übung": ex,
                    "Satz": i+1,
                    "Gewicht": weight,
                    "Wiederholungen": reps
                })
    
    # ------------------------------
    # Training abspeichern
    # ------------------------------
    if st.button("Training speichern ✅"):
        if not completed_data:
            st.warning("Bitte trage Gewicht und Wiederholungen für mindestens einen Satz ein!")
        else:
            today = datetime.today().strftime("%Y-%m-%d %H:%M")
            df_new = pd.DataFrame(completed_data)
            df_new["Datum"] = today
            if os.path.exists(history_file):
                df_old = pd.read_csv(history_file)
                df = pd.concat([df_old, df_new], ignore_index=True)
            else:
                df = df_new
            df.to_csv(history_file, index=False)
            st.success(f"Training für {selected_day} gespeichert! 📈")
            st.balloons()
    
    # ------------------------------
    # Trainingshistorie anzeigen
    # ------------------------------
    st.header("📊 Trainingshistorie")
    if os.path.exists(history_file):
        df_hist = pd.read_csv(history_file)
        if not is_admin:
            df_hist_user = df_hist[df_hist["User"] == username]
        elif is_admin and user_filter != "Alle":
            df_hist_user = df_hist[df_hist["User"] == user_filter]
        else:
            df_hist_user = df_hist
        st.dataframe(df_hist_user)
        
        st.subheader("Fortschritte pro Übung")
        for ex in exercises:
            df_ex = df_hist_user[df_hist_user["Übung"] == ex]
            if not df_ex.empty:
                st.line_chart(df_ex[["Gewicht", "Wiederholungen"]])
    else:
        st.info("Noch keine Trainingshistorie vorhanden.")
