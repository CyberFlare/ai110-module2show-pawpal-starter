import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, fmt_time

# 30-minute interval options in HH:MM; displayed as 12-hour AM/PM via fmt_time
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]

def _nearest_time_index(time_str: str) -> int:
    """Return the index in TIME_OPTIONS closest to the given HH:MM string."""
    h, m = map(int, time_str.split(':'))
    mins = h * 60 + m
    return min(range(len(TIME_OPTIONS)),
               key=lambda i: abs(int(TIME_OPTIONS[i][:2]) * 60 + int(TIME_OPTIONS[i][3:]) - mins))

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Session State Init ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "editing_task" not in st.session_state:
    st.session_state.editing_task = None  # (pet_index, task_index)
if "plan_generated" not in st.session_state:
    st.session_state.plan_generated = False
if "needs_regenerate" not in st.session_state:
    st.session_state.needs_regenerate = False


# =============================================
# SECTION 1: Owner Setup
# =============================================
st.header("Owner Setup")

if st.session_state.owner is None:
    with st.form("owner_form"):
        name = st.text_input("Your name")

        st.markdown("**Available time per slot (minutes)**")
        col1, col2, col3 = st.columns(3)
        with col1:
            morning_time = st.number_input("Morning", min_value=0, value=60)
        with col2:
            afternoon_time = st.number_input("Afternoon", min_value=0, value=30)
        with col3:
            evening_time = st.number_input("Evening", min_value=0, value=45)

        st.markdown("**Your preference level per slot**")
        col4, col5, col6 = st.columns(3)
        with col4:
            morning_pref = st.selectbox("Morning pref", ["high", "medium", "low"], key="mp")
        with col5:
            afternoon_pref = st.selectbox("Afternoon pref", ["high", "medium", "low"], index=2, key="ap")
        with col6:
            evening_pref = st.selectbox("Evening pref", ["high", "medium", "low"], index=1, key="ep")

        if st.form_submit_button("Create Owner") and name:
            st.session_state.owner = Owner(
                name=name,
                available_time={"morning": morning_time, "afternoon": afternoon_time, "evening": evening_time},
                preferences={"morning": morning_pref, "afternoon": afternoon_pref, "evening": evening_pref}
            )
            st.session_state.scheduler = Scheduler(st.session_state.owner)
            st.rerun()

else:
    owner = st.session_state.owner
    st.success(f"Owner: **{owner.name}**")

    with st.expander("Edit available time & preferences"):
        with st.form("edit_owner_form"):
            st.markdown("**Available time per slot (minutes)**")
            col1, col2, col3 = st.columns(3)
            with col1:
                new_morning_time = st.number_input("Morning", min_value=0, value=owner.available_time["morning"], key="et_m")
            with col2:
                new_afternoon_time = st.number_input("Afternoon", min_value=0, value=owner.available_time["afternoon"], key="et_a")
            with col3:
                new_evening_time = st.number_input("Evening", min_value=0, value=owner.available_time["evening"], key="et_e")

            st.markdown("**Preference level per slot**")
            prefs = ["high", "medium", "low"]
            col4, col5, col6 = st.columns(3)
            with col4:
                new_morning_pref = st.selectbox("Morning pref", prefs, index=prefs.index(owner.preferences["morning"]), key="ep_m")
            with col5:
                new_afternoon_pref = st.selectbox("Afternoon pref", prefs, index=prefs.index(owner.preferences["afternoon"]), key="ep_a")
            with col6:
                new_evening_pref = st.selectbox("Evening pref", prefs, index=prefs.index(owner.preferences["evening"]), key="ep_e")

            if st.form_submit_button("Save Changes"):
                owner.set_available_time(new_morning_time, new_afternoon_time, new_evening_time)
                owner.update_preferences(new_morning_pref, new_afternoon_pref, new_evening_pref)
                st.session_state.needs_regenerate = True
                st.rerun()

    st.caption(
        f"Time — Morning: {owner.available_time['morning']} min | "
        f"Afternoon: {owner.available_time['afternoon']} min | "
        f"Evening: {owner.available_time['evening']} min"
    )
    st.caption(
        f"Preferences — Morning: {owner.preferences['morning']} | "
        f"Afternoon: {owner.preferences['afternoon']} | "
        f"Evening: {owner.preferences['evening']}"
    )

    if st.button("Reset owner"):
        st.session_state.owner = None
        st.session_state.scheduler = None
        st.rerun()

st.divider()

if st.session_state.owner is None:
    st.info("Create an owner above to get started.")
    st.stop()

owner = st.session_state.owner
scheduler = st.session_state.scheduler


# =============================================
# SECTION 2: Add a Pet
# =============================================
st.header("Pets")

with st.form("pet_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Other"])
    with col3:
        age = st.number_input("Age", min_value=0, value=1)

    if st.form_submit_button("Add Pet") and pet_name:
        owner.add_pet(Pet(name=pet_name, species=species, age=age))
        st.session_state.needs_regenerate = True
        st.rerun()

if owner.pets:
    for pet in owner.pets:
        st.markdown(f"- **{pet.name}** ({pet.species}, {pet.age} yrs) — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()


# =============================================
# SECTION 3: Tasks
# =============================================
st.header("Tasks")

if not owner.pets:
    st.warning("Add a pet before adding tasks.")
else:
    # --- Add Task Form ---
    with st.form("task_form"):
        pet_names = [p.name for p in owner.pets]
        selected_pet_name = st.selectbox("Assign to pet", pet_names)

        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title")
            priority = st.selectbox("Priority", ["high", "medium", "low"])
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, value=20)
            preferred_time = st.selectbox("Preferred time", TIME_OPTIONS, index=TIME_OPTIONS.index("09:00"), format_func=fmt_time)

        if st.form_submit_button("Add Task") and task_title:
            selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)
            scheduler.add_task(selected_pet, Task(
                title=task_title,
                duration=int(duration),
                priority=priority,
                preferred_time=preferred_time,
                frequency=frequency
            ))
            st.session_state.needs_regenerate = True
            st.rerun()

    # --- Task List with Edit / Remove ---
    for pet_i, pet in enumerate(owner.pets):
        if pet.tasks:
            st.markdown(f"**{pet.name}'s tasks:**")
            for task_i, task in enumerate(pet.tasks):
                col1, col2, col3, col4 = st.columns([4, 1.2, 1.2, 1.5])
                with col1:
                    star = "⭐ " if task.is_high_priority() else ""
                    freq_label = f" 🔁 {task.frequency}" if task.frequency != "once" else ""
                    date_label = f" | due {task.due_date}" if task.frequency != "once" else ""
                    if task.completed:
                        st.markdown(f"~~{star}{task.title}~~ — {task.duration} min, {task.priority} priority, {fmt_time(task.preferred_time)}{freq_label}{date_label} ✅")
                    else:
                        st.markdown(f"{star}{task.title} — {task.duration} min, {task.priority} priority, {fmt_time(task.preferred_time)}{freq_label}{date_label}")
                with col2:
                    btn_label = "Undo" if task.completed else "Done"
                    if st.button(btn_label, key=f"done_{pet_i}_{task_i}"):
                        if task.completed:
                            task.toggle_complete()  # just undo, no recurrence
                        else:
                            scheduler.complete_task(task)  # marks done + silently adds next if recurring
                        st.session_state.needs_regenerate = True
                        st.rerun()
                with col3:
                    if st.button("Edit", key=f"edit_{pet_i}_{task_i}"):
                        st.session_state.editing_task = (pet_i, task_i)
                        st.rerun()
                with col4:
                    if st.button("Remove", key=f"remove_{pet_i}_{task_i}"):
                        scheduler.remove_task(pet, task)
                        if st.session_state.editing_task == (pet_i, task_i):
                            st.session_state.editing_task = None
                        st.session_state.needs_regenerate = True
                        st.rerun()

    # --- Inline Edit Form ---
    if st.session_state.editing_task is not None:
        pet_i, task_i = st.session_state.editing_task
        pet = owner.pets[pet_i]
        task = pet.tasks[task_i]

        st.divider()
        st.markdown(f"**Editing:** {task.title} ({pet.name})")
        with st.form("edit_task_form"):
            prefs = ["high", "medium", "low"]
            freqs = ["once", "daily", "weekly"]
            col1, col2 = st.columns(2)
            with col1:
                new_title = st.text_input("Title", value=task.title)
                new_priority = st.selectbox("Priority", prefs, index=prefs.index(task.priority))
                new_frequency = st.selectbox("Frequency", freqs, index=freqs.index(task.frequency))
            with col2:
                new_duration = st.number_input("Duration (min)", min_value=1, value=task.duration)
                new_time = st.selectbox("Preferred time", TIME_OPTIONS, index=_nearest_time_index(task.preferred_time), format_func=fmt_time)

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("Save"):
                    scheduler.edit_task(
                        task,
                        title=new_title,
                        duration=int(new_duration),
                        priority=new_priority,
                        preferred_time=new_time,
                        frequency=new_frequency
                    )
                    st.session_state.editing_task = None
                    st.session_state.needs_regenerate = True
                    st.rerun()
            with col_cancel:
                if st.form_submit_button("Cancel"):
                    st.session_state.editing_task = None
                    st.rerun()

st.divider()


# =============================================
# SECTION 4: Generate Schedule
# =============================================
st.header("Daily Schedule")

btn_label = "Regenerate Schedule" if (st.session_state.plan_generated and st.session_state.needs_regenerate) else "Generate Schedule"

if st.button(btn_label, type="primary"):
    scheduler.generate_plan()
    st.session_state.plan_generated = True
    st.session_state.needs_regenerate = False
    st.rerun()

if st.session_state.needs_regenerate and st.session_state.plan_generated:
    st.warning("Tasks or settings have changed — regenerate to update the schedule.")

if st.session_state.plan_generated and scheduler.plan and any(scheduler.plan[s] for s in scheduler.plan):
    stats = scheduler.get_stats()

    if scheduler.conflicts:
        st.error("⚠️ Time Conflicts Detected:")
        for warning in scheduler.conflicts:
            st.markdown(f"- {warning}")

    for slot in ("morning", "afternoon", "evening"):
        st.subheader(slot.capitalize())
        if scheduler.plan[slot]:
            sorted_tasks = sorted(scheduler.plan[slot], key=lambda t: t.scheduled_time or "99:99")
            for task in sorted_tasks:
                pet_name = scheduler.task_pet_map.get(id(task), "?")
                indicator = "⭐ " if task.is_high_priority() else ""
                freq_label = f" 🔁 {task.frequency}" if task.frequency != "once" else ""
                sched = fmt_time(task.scheduled_time) if task.scheduled_time else "—"
                st.markdown(f"- {indicator}**[{pet_name}]** {task.title} ({task.duration} min, {task.priority} priority) | scheduled {sched} | preferred {fmt_time(task.preferred_time)} | due {task.due_date}{freq_label}")
        else:
            st.caption("No tasks scheduled.")

    if scheduler.unscheduled_tasks:
        st.warning("Could not fit:")
        for task in scheduler.unscheduled_tasks:
            pet_name = scheduler.task_pet_map.get(id(task), "?")
            st.markdown(f"- [{pet_name}] {task.title} ({task.duration} min)")

    st.divider()
    st.subheader("Reasoning")
    for slot in ("morning", "afternoon", "evening"):
        if scheduler.reasoning[slot]:
            st.markdown(f"**{slot.capitalize()}**")
            for reason in scheduler.reasoning[slot]:
                st.caption(f"- {reason}")
    if scheduler.reasoning["unscheduled"]:
        st.markdown("**Unscheduled**")
        for reason in scheduler.reasoning["unscheduled"]:
            st.caption(f"- {reason}")

    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("Time Used", f"{stats['total_used']} min")
    col2.metric("Time Remaining", f"{stats['total_remaining']} min")
    col3.metric("Tasks Scheduled", f"{stats['tasks_scheduled']} / {stats['tasks_scheduled'] + stats['tasks_unscheduled']}")
elif not st.session_state.plan_generated:
    st.info("Add tasks and click Generate Schedule.")
