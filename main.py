from pawpal_system import Owner, Pet, Task, Scheduler, fmt_time

# -----------------------------------------------
# Setup: Alex owns two pets and has limited time
# Morning: 90 min (6:00–7:30 AM, before work)
# Afternoon: 30 min (12:00–12:30 PM, lunch)
# Evening: 75 min (6:00–7:15 PM, after work)
# Owner prefers high-priority tasks in evening, medium in morning
# -----------------------------------------------

buddy = Pet(name="Buddy", species="Dog", age=3)
luna  = Pet(name="Luna",  species="Cat", age=2)

# Buddy — active dog, needs walks and feeding
buddy.add_task(Task("Morning Walk",    duration=30, priority="high",   preferred_time="06:30", frequency="daily"))
buddy.add_task(Task("Breakfast",       duration=10, priority="high",   preferred_time="07:00"))
buddy.add_task(Task("Evening Walk",    duration=20, priority="high",   preferred_time="18:30"))
buddy.add_task(Task("Dinner",         duration=10, priority="high",   preferred_time="18:00"))
buddy.add_task(Task("Teeth Brushing", duration=10, priority="low",    preferred_time="07:15", frequency="weekly"))

# Luna — needs feeding and daily vet meds; creates two scheduling conflicts
# CONFLICT 1: Luna's Breakfast and Buddy's Breakfast both at 07:00
luna.add_task(Task("Breakfast",        duration=5,  priority="medium", preferred_time="07:00"))
luna.add_task(Task("Litter Box",       duration=10, priority="medium", preferred_time="12:00"))
# CONFLICT 2: Vet Medication and Buddy's Dinner both at 18:00
luna.add_task(Task("Vet Medication",   duration=5,  priority="high",   preferred_time="18:00"))
luna.add_task(Task("Evening Playtime", duration=20, priority="low",    preferred_time="19:00"))
# Monthly Bath — 35 min, can't fit in any slot after other tasks are scheduled
luna.add_task(Task("Monthly Bath",     duration=35, priority="low",    preferred_time="14:00", frequency="weekly"))

owner = Owner(
    name="Alex",
    available_time={"morning": 90, "afternoon": 30, "evening": 75},
    preferences={"morning": "medium", "afternoon": "low", "evening": "high"},
    pets=[buddy, luna]
)

scheduler = Scheduler(owner)
scheduler.generate_plan()

# Mark Morning Walk complete (recurring — next occurrence auto-added)
scheduler.complete_task(buddy.tasks[0])

# -----------------------------------------------
print("=" * 45)
print("  CONFLICT DETECTION")
print("=" * 45)
if scheduler.conflicts:
    for warning in scheduler.conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

# -----------------------------------------------
print("\n" + "=" * 45)
print("  SORTED BY TIME (chronological)")
print("=" * 45)
for task in scheduler.sort_by_time():
    pet = scheduler.task_pet_map.get(id(task), "?")
    status = "done" if task.completed else "    "
    print(f"  [{status}] {fmt_time(task.preferred_time)}  {task.title} ({pet})")

# -----------------------------------------------
print("\n" + "=" * 45)
print("  SORTED BY PRIORITY (high -> low)")
print("=" * 45)
for task in scheduler.sort_tasks_by_priority():
    pet = scheduler.task_pet_map.get(id(task), "?")
    print(f"  [{task.priority:<6}] {task.title} ({pet})")

# -----------------------------------------------
print("\n" + "=" * 45)
print("  FILTER: Buddy's tasks")
print("=" * 45)
for task in scheduler.filter_tasks(pet_name="Buddy"):
    print(f"  {task.title} ({task.priority}, preferred {fmt_time(task.preferred_time)})")

# -----------------------------------------------
print("\n" + "=" * 45)
print("  FILTER: Completed tasks")
print("=" * 45)
completed = scheduler.filter_tasks(completed=True)
if completed:
    for task in completed:
        pet = scheduler.task_pet_map.get(id(task), "?")
        print(f"  {task.title} ({pet})")
else:
    print("  None")

# -----------------------------------------------
print("\n" + "=" * 45)
print("  FILTER: Buddy's pending tasks")
print("=" * 45)
for task in scheduler.filter_tasks(pet_name="Buddy", completed=False):
    print(f"  {task.title} ({task.priority}, preferred {fmt_time(task.preferred_time)})")

# -----------------------------------------------
print("\n" + "=" * 45)
print("        Today's Schedule")
print("=" * 45)
scheduler.display_plan()

print("\n" + "=" * 45)
stats = scheduler.get_stats()
print(f"  Time used:         {stats['total_used']} min")
print(f"  Time remaining:    {stats['total_remaining']} min")
print(f"  Tasks scheduled:   {stats['tasks_scheduled']}")
print(f"  Tasks unscheduled: {stats['tasks_unscheduled']}")
print("=" * 45)
