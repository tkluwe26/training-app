# ----------------------
# Trainingsplan auswählen oder neuen erstellen + löschen
# ----------------------
st.subheader("Trainingsplan auswählen oder erstellen")
user_plans = list(plans_df[plans_df["User"]==st.session_state.username]["Planname"].unique())

# Löschen-Funktion mit Bestätigung
st.markdown("### Bestehende Trainingspläne")
if user_plans:
    for plan in user_plans:
        cols = st.columns([4,1])
        cols[0].write(plan)
        if cols[1].button("Löschen", key=f"del_{plan}"):
            if st.confirm(f"Willst du den Plan '{plan}' wirklich löschen? Dies löscht auch die Trainingshistorie."):
                # Plan löschen
                plans_df = plans_df[~((plans_df["User"]==st.session_state.username) & (plans_df["Planname"]==plan))]
                plans_df.to_csv(PLANS_FILE,index=False)
                # Historie löschen
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
    # Wenn keine Pläne mehr existieren, direkt "Neuen Plan erstellen"
    choice = "Neuen Plan erstellen"

# ----------------------
# Neuen Plan erstellen
# ----------------------
if choice=="Neuen Plan erstellen":
    st.subheader("📝 Neuen Trainingsplan erstellen")
    
    plan_name = st.text_input("Name des Trainingsplans")
    num_days = st.number_input("Anzahl Trainingstage", min_value=1, max_value=7, value=3, step=1)

    day_names = [st.text_input(f"Name Trainingstag {i+1}", value=f"Tag {i+1}") for i in range(num_days)]

    exercises_dict = {}
    sets_dict = {}
    for day in day_names:
        st.markdown(f"### {day}")
        exercises_dict[day] = st.text_area(f"Übungen für {day} (kommagetrennt)")
        sets_dict[day] = st.text_area(f"Sätze pro Übung für {day} (kommagetrennt)")

    if st.button("Trainingsplan speichern"):
        for day in day_names:
            plans_df = pd.concat([plans_df, pd.DataFrame([{
                "User": st.session_state.username,
                "Planname": plan_name,
                "Trainingstag": day,
                "Übungen": exercises_dict[day],
                "Sätze": sets_dict[day]
            }])], ignore_index=True)
        plans_df.to_csv(PLANS_FILE, index=False)
        st.success("Trainingsplan gespeichert!")
        st.experimental_rerun()

else:
    st.session_state.current_plan = choice
