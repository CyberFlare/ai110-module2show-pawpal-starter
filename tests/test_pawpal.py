from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_status():
    task = Task(title="Walk", duration=30, priority="high", preferred_time="08:00")
    assert task.completed == False
    task.mark_complete()
    assert task.completed == True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="Dog", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Walk", duration=30, priority="high", preferred_time="08:00"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order():
    """Tasks with different preferred_times should come back earliest-first."""
    pet = Pet(name="Buddy", species="Dog", age=3)
    t1 = Task(title="Evening Walk",   duration=20, priority="low",    preferred_time="18:00")
    t2 = Task(title="Morning Feed",   duration=10, priority="high",   preferred_time="07:00")
    t3 = Task(title="Afternoon Meds", duration=15, priority="medium", preferred_time="13:00")
    for t in (t1, t2, t3):
        pet.add_task(t)

    owner = Owner(
        name="Alex",
        available_time={"morning": 120, "afternoon": 60, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time()

    times = [t.preferred_time for t in sorted_tasks]
    assert times == sorted(times), f"Expected chronological order, got {times}"


def test_sort_by_time_handles_identical_times():
    """Two tasks at the same preferred_time should both appear (order between them is stable)."""
    pet = Pet(name="Cat", species="Cat", age=2)
    t1 = Task(title="Feed A", duration=5, priority="high",   preferred_time="08:00")
    t2 = Task(title="Feed B", duration=5, priority="medium", preferred_time="08:00")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(
        name="Sam",
        available_time={"morning": 60, "afternoon": 30, "evening": 30},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time()

    assert len(sorted_tasks) == 2
    assert sorted_tasks[0].preferred_time == "08:00"
    assert sorted_tasks[1].preferred_time == "08:00"


def test_sort_tasks_by_priority_high_before_low():
    """High-priority tasks must appear before low-priority tasks in the sorted list."""
    pet = Pet(name="Rex", species="Dog", age=5)
    low_task  = Task(title="Low",  duration=10, priority="low",  preferred_time="09:00")
    high_task = Task(title="High", duration=10, priority="high", preferred_time="09:00")
    pet.add_task(low_task)
    pet.add_task(high_task)

    owner = Owner(
        name="Jo",
        available_time={"morning": 60, "afternoon": 30, "evening": 30},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    result = scheduler.sort_tasks_by_priority()

    assert result[0].priority == "high"
    assert result[-1].priority == "low"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_complete_daily_task_creates_next_day_occurrence():
    """Completing a daily task should add a new task due tomorrow to the pet's list."""
    today = date.today()
    pet = Pet(name="Buddy", species="Dog", age=3)
    daily = Task(title="Walk", duration=30, priority="high",
                 preferred_time="08:00", frequency="daily", due_date=today)
    pet.add_task(daily)

    owner = Owner(
        name="Alex",
        available_time={"morning": 120, "afternoon": 60, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduler.complete_task(daily)

    # Original task is marked done
    assert daily.completed is True

    # A second task should now exist for tomorrow
    assert len(pet.tasks) == 2
    next_task = pet.tasks[1]
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.title == "Walk"
    assert next_task.frequency == "daily"
    assert next_task.completed is False


def test_complete_once_task_does_not_create_recurrence():
    """Completing a one-off task must NOT add any new task to the pet's list."""
    pet = Pet(name="Buddy", species="Dog", age=3)
    once = Task(title="Vet Visit", duration=60, priority="high",
                preferred_time="10:00", frequency="once")
    pet.add_task(once)

    owner = Owner(
        name="Alex",
        available_time={"morning": 120, "afternoon": 60, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduler.complete_task(once)

    assert len(pet.tasks) == 1  # no new task spawned
    assert once.completed is True


def test_complete_weekly_task_creates_next_week_occurrence():
    """Completing a weekly task should add a new task due 7 days later."""
    today = date.today()
    pet = Pet(name="Buddy", species="Dog", age=3)
    weekly = Task(title="Bath", duration=45, priority="medium",
                  preferred_time="09:00", frequency="weekly", due_date=today)
    pet.add_task(weekly)

    owner = Owner(
        name="Alex",
        available_time={"morning": 120, "afternoon": 60, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()
    scheduler.complete_task(weekly)

    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == today + timedelta(weeks=1)


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_overlapping_preferred_times():
    """Two tasks whose preferred_time windows overlap should appear in scheduler.conflicts."""
    pet = Pet(name="Buddy", species="Dog", age=3)
    # Both start at 07:00, each 60 min — windows overlap completely
    t1 = Task(title="Walk",  duration=60, priority="high", preferred_time="07:00")
    t2 = Task(title="Feed",  duration=60, priority="high", preferred_time="07:00")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(
        name="Alex",
        available_time={"morning": 180, "afternoon": 60, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.conflicts) > 0, "Expected at least one conflict to be reported"


def test_detect_conflicts_no_false_positive_for_non_overlapping_times():
    """Tasks in different time windows must NOT be flagged as conflicts."""
    pet = Pet(name="Buddy", species="Dog", age=3)
    t1 = Task(title="Morning Walk", duration=30, priority="high",   preferred_time="07:00")
    t2 = Task(title="Evening Feed", duration=30, priority="medium", preferred_time="18:00")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(
        name="Alex",
        available_time={"morning": 60, "afternoon": 30, "evening": 60},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert scheduler.conflicts == [], f"Unexpected conflicts: {scheduler.conflicts}"


def test_detect_conflicts_adjacent_tasks_are_not_conflicts():
    """Tasks whose preferred-time windows are adjacent (end == start) must NOT be flagged.
    The scheduler clamps both tasks to fit inside the morning slot, but detect_conflicts
    compares preferred_time windows: 08:00–08:30 vs 08:30–09:00. The strict < operator
    means end==start is not an overlap."""
    pet = Pet(name="Buddy", species="Dog", age=3)
    t1 = Task(title="Feed",  duration=30, priority="high", preferred_time="08:00")
    t2 = Task(title="Walk",  duration=30, priority="high", preferred_time="08:30")
    pet.add_task(t1)
    pet.add_task(t2)

    owner = Owner(
        name="Alex",
        available_time={"morning": 120, "afternoon": 30, "evening": 30},
        preferences={"morning": "high", "afternoon": "medium", "evening": "low"},
        pets=[pet],
    )
    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert scheduler.conflicts == [], f"Adjacent tasks should not conflict: {scheduler.conflicts}"
