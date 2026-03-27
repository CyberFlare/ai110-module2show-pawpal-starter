from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import date, timedelta, datetime


def fmt_time(time_str: str) -> str:
    """Convert HH:MM to 12-hour format e.g. '09:00' -> '9:00 AM'."""
    return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip("0")


@dataclass
class Task:
    title: str
    duration: int        # minutes
    priority: str        # 'high', 'medium', 'low'
    preferred_time: str  # HH:MM format e.g. '09:00' — pet's preferred time of day
    completed: bool = False
    frequency: str = 'once'          # 'once', 'daily', 'weekly'
    due_date: Optional[date] = None  # defaults to today if not set
    scheduled_time: Optional[str] = None  # assigned by Scheduler.generate_plan(); None until scheduled

    VALID_PRIORITIES = ('high', 'medium', 'low')
    VALID_FREQUENCIES = ('once', 'daily', 'weekly')

    def __post_init__(self):
        """Validate priority, preferred_time format, duration, frequency, and set due_date to today if not provided."""
        if self.priority not in self.VALID_PRIORITIES:
            raise ValueError(f"priority must be one of {self.VALID_PRIORITIES}")
        self._validate_time_format(self.preferred_time)
        if self.duration <= 0:
            raise ValueError("duration must be a positive number of minutes")
        if self.frequency not in self.VALID_FREQUENCIES:
            raise ValueError(f"frequency must be one of {self.VALID_FREQUENCIES}")
        if self.due_date is None:
            self.due_date = date.today()

    def _validate_time_format(self, time_str: str):
        """Raise ValueError if time_str is not valid HH:MM format."""
        parts = time_str.split(':')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("preferred_time must be in HH:MM format (e.g. '09:00')")
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("preferred_time must be a valid time (00:00 to 23:59)")

    def edit_task(self, title: str = None, duration: int = None,
                  priority: str = None, preferred_time: str = None,
                  frequency: str = None):
        """Update any subset of task fields. Only supplied (non-None) arguments are changed.
        Raises ValueError if any supplied value fails validation."""
        if title is not None:
            self.title = title
        if duration is not None:
            if duration <= 0:
                raise ValueError("duration must be a positive number of minutes")
            self.duration = duration
        if priority is not None:
            if priority not in self.VALID_PRIORITIES:
                raise ValueError(f"priority must be one of {self.VALID_PRIORITIES}")
            self.priority = priority
        if preferred_time is not None:
            self._validate_time_format(preferred_time)
            self.preferred_time = preferred_time
        if frequency is not None:
            if frequency not in self.VALID_FREQUENCIES:
                raise ValueError(f"frequency must be one of {self.VALID_FREQUENCIES}")
            self.frequency = frequency

    def next_occurrence(self) -> Optional['Task']:
        """Return a new Task due one period later (daily → +1 day, weekly → +7 days).
        Returns None if frequency is 'once'. All other fields are copied from this task."""
        if self.frequency == 'daily':
            next_due = self.due_date + timedelta(days=1)
        elif self.frequency == 'weekly':
            next_due = self.due_date + timedelta(weeks=1)
        else:
            return None
        return Task(
            title=self.title,
            duration=self.duration,
            priority=self.priority,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            due_date=next_due
        )

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def toggle_complete(self):
        """Flip completed between True and False. Use this to undo a completion without spawning a recurrence."""
        self.completed = not self.completed

    def is_high_priority(self) -> bool:
        """Return True if this task has high priority."""
        return self.priority == 'high'


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def __post_init__(self):
        """Validate that age is non-negative after dataclass initialization."""
        if self.age < 0:
            raise ValueError("age cannot be negative")

    def update_info(self, name: str = None, species: str = None, age: int = None):
        """Update any subset of the pet's name, species, or age."""
        if name is not None:
            self.name = name
        if species is not None:
            self.species = species
        if age is not None:
            if age < 0:
                raise ValueError("age cannot be negative")
            self.age = age

    def add_task(self, task: Task):
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task):
        """Remove a task from this pet's task list. Raises ValueError if the task is not found."""
        self.tasks.remove(task)

    def complete_task(self, task: Task):
        """Mark a task belonging to this pet as completed."""
        task.mark_complete()

    def get_completed_tasks(self) -> List[Task]:
        """Return all tasks for this pet that have been completed."""
        result = []
        for task in self.tasks:
            if task.completed:
                result.append(task)
        return result

    def get_pending_tasks(self) -> List[Task]:
        """Return all tasks for this pet that are not yet completed."""
        result = []
        for task in self.tasks:
            if not task.completed:
                result.append(task)
        return result


class Owner:
    VALID_TIMES = ('morning', 'afternoon', 'evening')

    def __init__(self, name: str, available_time: Dict[str, int], preferences: Dict[str, str], pets: List[Pet] = None):
        """Create an Owner with a name, time budget per slot, priority preferences per slot, and optional pet list.
        available_time: minutes free in each slot e.g. {"morning": 90, "afternoon": 30, "evening": 75}.
        preferences: which priority level the owner prefers to handle in each slot e.g. {"morning": "high", ...}."""
        self._validate_available_time(available_time)
        self._validate_preferences(preferences)
        self.name = name
        self.available_time = available_time  # e.g. {"morning": 60, "afternoon": 30, "evening": 45}
        self.preferences = preferences        # e.g. {"morning": "high", "afternoon": "low", "evening": "medium"}
        self.pets = pets if pets is not None else []

    def _validate_available_time(self, available_time: Dict[str, int]):
        """Raise ValueError if available_time is missing a slot or contains a negative value."""
        for time_of_day in self.VALID_TIMES:
            if time_of_day not in available_time:
                raise ValueError(f"available_time must include '{time_of_day}'")
            if available_time[time_of_day] < 0:
                raise ValueError(f"available_time for '{time_of_day}' cannot be negative")

    def set_available_time(self, morning: int, afternoon: int, evening: int):
        """Replace the owner's time budget for all three slots at once. Raises ValueError for negative values."""
        available_time = {"morning": morning, "afternoon": afternoon, "evening": evening}
        self._validate_available_time(available_time)
        self.available_time = available_time

    def get_available_time(self, time_of_day: str) -> int:
        """Return the owner's available minutes for the given time slot."""
        if time_of_day not in self.VALID_TIMES:
            raise ValueError(f"time_of_day must be one of {self.VALID_TIMES}")
        return self.available_time[time_of_day]

    def _validate_preferences(self, preferences: Dict[str, str]):
        """Raise ValueError if preferences is missing a slot or contains an invalid priority."""
        valid_priorities = ('high', 'medium', 'low')
        for time_of_day in self.VALID_TIMES:
            if time_of_day not in preferences:
                raise ValueError(f"preferences must include '{time_of_day}'")
            if preferences[time_of_day] not in valid_priorities:
                raise ValueError(f"preference for '{time_of_day}' must be one of {valid_priorities}")

    def update_preferences(self, morning: str, afternoon: str, evening: str):
        """Replace the owner's priority preference for all three slots. Each value must be 'high', 'medium', or 'low'."""
        preferences = {"morning": morning, "afternoon": afternoon, "evening": evening}
        self._validate_preferences(preferences)
        self.preferences = preferences

    def add_pet(self, pet: Pet):
        """Add a pet to the owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet: Pet):
        """Remove a pet from the owner's pet list."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return a flat list of every task across all of the owner's pets."""
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append(task)
        return result

    def add_pet_task(self, pet: Pet, task: Task):
        """Add a task to a specific pet owned by this owner."""
        pet.add_task(task)

    def remove_pet_task(self, pet: Pet, task: Task):
        """Remove a task from a specific pet owned by this owner."""
        pet.remove_task(task)


class Scheduler:
    PRIORITY_ORDER = {'high': 0, 'medium': 1, 'low': 2}

    def __init__(self, owner: Owner):
        """Set up the scheduler from an Owner. Loads all tasks and available time but does not
        build the schedule yet — call generate_plan() to produce the first schedule."""
        self.owner = owner
        self.tasks = owner.get_all_tasks()
        self.available_time = {
            'morning':   owner.available_time['morning'],
            'afternoon': owner.available_time['afternoon'],
            'evening':   owner.available_time['evening']
        }
        self.plan = {'morning': [], 'afternoon': [], 'evening': []}
        self.unscheduled_tasks = self.tasks.copy()
        self.time_used = {'morning': 0, 'afternoon': 0, 'evening': 0}
        self.reasoning = {'morning': [], 'afternoon': [], 'evening': [], 'unscheduled': []}
        self.task_pet_map = {}
        self.conflicts: List[str] = []
        self.occupied: Dict[str, list] = {'morning': [], 'afternoon': [], 'evening': []}

    def sort_tasks_by_priority(self) -> List[Task]:
        """Return a copy of all tasks sorted from highest to lowest priority."""
        return sorted(self.tasks, key=lambda t: self.PRIORITY_ORDER[t.priority])

    def sort_by_time(self) -> List[Task]:
        """Return a copy of all tasks sorted chronologically by preferred time (HH:MM)."""
        return sorted(self.tasks, key=lambda t: t.preferred_time)

    def _time_to_slot(self, time_str: str) -> str:
        """Map a HH:MM time string to the owner's morning/afternoon/evening slot."""
        hour = int(time_str.split(':')[0])
        if hour < 12:
            return 'morning'
        elif hour < 17:
            return 'afternoon'
        else:
            return 'evening'

    def filter_tasks(self, pet_name: str = None, completed: bool = None) -> List[Task]:
        """Return tasks matching the given filters. Pass pet_name to filter by pet,
        completed=True/False to filter by status, or combine both to narrow further."""
        result = []
        for task in self.tasks:
            if pet_name is not None and self.task_pet_map.get(id(task)) != pet_name:
                continue
            if completed is not None and task.completed != completed:
                continue
            result.append(task)
        return result

    def _slots_for_task(self, task: Task) -> List[str]:
        """Return slots in the order they should be tried for this task.
        High/medium use the pet's preferred time mapped to a slot.
        Low priority uses the owner's preferred slots instead."""
        owner_pref_order = {'high': 0, 'medium': 1, 'low': 2}

        if task.priority == 'low':
            return sorted(
                ('morning', 'afternoon', 'evening'),
                key=lambda s: owner_pref_order[self.owner.preferences[s]]
            )
        else:
            preferred_slot = self._time_to_slot(task.preferred_time)
            others = sorted(
                [s for s in ('morning', 'afternoon', 'evening') if s != preferred_slot],
                key=lambda s: self.available_time[s] - self.time_used[s],
                reverse=True
            )
            return [preferred_slot] + others

    # Clock minute where each slot begins — used to assign scheduled_time
    SLOT_STARTS = {'morning': 6 * 60, 'afternoon': 12 * 60, 'evening': 17 * 60}

    def _find_slot_time(self, slot: str, preferred_min: int, duration: int) -> Optional[int]:
        """Find the earliest available start time at or after preferred_min in the slot.
        Scans occupied intervals and shifts past any overlap.
        Returns start time in minutes, or None if the task cannot fit."""
        slot_start = self.SLOT_STARTS[slot]
        slot_end = slot_start + self.available_time[slot]
        start = max(preferred_min, slot_start)
        for occ_start, occ_end in sorted(self.occupied[slot]):
            if start + duration <= occ_start:
                break           # fits in the gap before this block
            if start < occ_end:
                start = occ_end  # push past this occupied block
        return start if start + duration <= slot_end else None

    def fit_tasks_into_time(self):
        """Greedily assign tasks to time slots by priority, recording reasoning for each decision.
        High/medium: scheduled at or near pet's preferred_time; shifted if occupied.
        Low: packed from the start of the owner's preferred slot."""
        self.plan = {'morning': [], 'afternoon': [], 'evening': []}
        self.unscheduled_tasks = []
        self.time_used = {'morning': 0, 'afternoon': 0, 'evening': 0}
        self.occupied = {'morning': [], 'afternoon': [], 'evening': []}
        self.reasoning = {'morning': [], 'afternoon': [], 'evening': [], 'unscheduled': []}

        for task in self.tasks:
            task.scheduled_time = None

        for task in self.sort_tasks_by_priority():
            if task.completed:
                continue
            preferred_min = int(task.preferred_time[:2]) * 60 + int(task.preferred_time[3:])
            scheduled = False

            for slot in self._slots_for_task(task):
                preferred_slot = self._time_to_slot(task.preferred_time)
                if task.priority != 'low' and slot == preferred_slot:
                    # Try preferred time first; if it falls outside the slot window, use slot start
                    start_min = self._find_slot_time(slot, preferred_min, task.duration)
                    if start_min is None:
                        start_min = self._find_slot_time(slot, self.SLOT_STARTS[slot], task.duration)
                else:
                    start_min = self._find_slot_time(slot, self.SLOT_STARTS[slot], task.duration)
                if start_min is not None:
                    self.plan[slot].append(task)
                    self.occupied[slot].append((start_min, start_min + task.duration))
                    self.time_used[slot] += task.duration
                    h, m = divmod(start_min, 60)
                    task.scheduled_time = f"{h:02d}:{m:02d}"

                    if task.priority == 'low':
                        note = f"owner preference -> {slot}"
                    elif slot == preferred_slot:
                        actual = fmt_time(task.scheduled_time)
                        note = f"pet preferred {fmt_time(task.preferred_time)}, scheduled {actual}"
                    else:
                        note = f"pet preferred {fmt_time(task.preferred_time)} ({preferred_slot}) full, moved to {slot}"
                    self.reasoning[slot].append(
                        f"[{self.task_pet_map.get(id(task), '?')}] '{task.title}' scheduled "
                        f"({task.duration} min, {task.priority} priority, {note})"
                    )
                    scheduled = True
                    break

            if not scheduled:
                self.unscheduled_tasks.append(task)
                self.reasoning['unscheduled'].append(
                    f"[{self.task_pet_map.get(id(task), '?')}] '{task.title}' could not fit anywhere "
                    f"— needs {task.duration} min"
                )

    def generate_plan(self):
        """Reload all tasks and available time from the owner, rebuild the schedule via
        fit_tasks_into_time(), and run conflict detection. Call this whenever the schedule should update."""
        self.tasks = self.owner.get_all_tasks()
        self.available_time = {
            'morning':   self.owner.available_time['morning'],
            'afternoon': self.owner.available_time['afternoon'],
            'evening':   self.owner.available_time['evening']
        }
        self.task_pet_map = {}
        for pet in self.owner.pets:
            for task in pet.tasks:
                self.task_pet_map[id(task)] = pet.name
        self.fit_tasks_into_time()
        self.conflicts = self.detect_conflicts()

    def add_task(self, pet: Pet, task: Task):
        """Add a task to a pet. Does not rebuild the schedule — call generate_plan() when ready."""
        self.owner.add_pet_task(pet, task)

    def remove_task(self, pet: Pet, task: Task):
        """Remove a task from a pet. Does not rebuild the schedule — call generate_plan() when ready."""
        self.owner.remove_pet_task(pet, task)

    def edit_task(self, task: Task, title: str = None, duration: int = None,
                  priority: str = None, preferred_time: str = None, frequency: str = None):
        """Edit fields on an existing task. Does not rebuild the schedule — call generate_plan() when ready."""
        task.edit_task(title=title, duration=duration, priority=priority, preferred_time=preferred_time, frequency=frequency)

    def complete_task(self, task: Task):
        """Mark a task as completed. If it is recurring, automatically creates the next occurrence
        and adds it to the pet's task list without rebuilding the schedule."""
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet_name = self.task_pet_map.get(id(task))
            for pet in self.owner.pets:
                if pet.name == pet_name:
                    self.owner.add_pet_task(pet, next_task)
                    self.tasks.append(next_task)
                    self.task_pet_map[id(next_task)] = pet.name
                    break

    def detect_conflicts(self) -> List[str]:
        """Check all scheduled tasks for time overlap. Returns a list of warning strings.
        Two tasks conflict if their time windows overlap:
            A.start < B.end  AND  B.start < A.end
        Works across pets and within the same pet."""
        warnings = []
        # Collect all scheduled tasks with their pet name
        scheduled = []
        for slot in ('morning', 'afternoon', 'evening'):
            for task in self.plan[slot]:
                scheduled.append(task)

        for i in range(len(scheduled)):
            for j in range(i + 1, len(scheduled)):
                a = scheduled[i]
                b = scheduled[j]
                a_start = int(a.preferred_time.split(':')[0]) * 60 + int(a.preferred_time.split(':')[1])
                a_end   = a_start + a.duration
                b_start = int(b.preferred_time.split(':')[0]) * 60 + int(b.preferred_time.split(':')[1])
                b_end   = b_start + b.duration
                if a_start < b_end and b_start < a_end:
                    a_pet = self.task_pet_map.get(id(a), '?')
                    b_pet = self.task_pet_map.get(id(b), '?')
                    warnings.append(
                        f"CONFLICT: [{a_pet}] '{a.title}' ({fmt_time(a.preferred_time)}, {a.duration} min) "
                        f"overlaps [{b_pet}] '{b.title}' ({fmt_time(b.preferred_time)}, {b.duration} min)"
                    )
        return warnings

    def get_remaining_time(self) -> Dict[str, int]:
        """Return the unused minutes remaining in each time slot."""
        result = {}
        for slot in ('morning', 'afternoon', 'evening'):
            result[slot] = self.available_time[slot] - self.time_used[slot]
        return result

    def get_total_remaining_time(self) -> int:
        """Return the total unused minutes across all time slots."""
        return sum(self.get_remaining_time().values())

    def get_total_time_used(self) -> int:
        """Return the total minutes consumed by scheduled tasks across all slots."""
        return sum(self.time_used.values())

    def get_total_available_time(self) -> int:
        """Return the total available minutes across all time slots."""
        return sum(self.available_time.values())

    def get_stats(self) -> Dict[str, int]:
        """Return a summary dict with totals for available, used, remaining, and scheduled/unscheduled task counts."""
        return {
            'total_available': self.get_total_available_time(),
            'total_used':      self.get_total_time_used(),
            'total_remaining': self.get_total_remaining_time(),
            'tasks_scheduled': sum(len(self.plan[slot]) for slot in self.plan),
            'tasks_unscheduled': len(self.unscheduled_tasks)
        }

    def display_plan(self):
        """Print each time slot's tasks in chronological order showing scheduled and preferred times,
        followed by any tasks that could not be placed in any slot."""
        for slot in ('morning', 'afternoon', 'evening'):
            print(f"\n{slot.capitalize()}:")
            if self.plan[slot]:
                for task in sorted(self.plan[slot], key=lambda t: t.scheduled_time or "99:99"):
                    pet_name = self.task_pet_map.get(id(task), '?')
                    sched = fmt_time(task.scheduled_time) if task.scheduled_time else "unscheduled"
                    print(f"  - [{pet_name}] {task.title} ({task.duration} min, {task.priority} priority) | scheduled {sched} | preferred {fmt_time(task.preferred_time)} | due {task.due_date}")
            else:
                print("  No tasks scheduled")
        if self.unscheduled_tasks:
            print("\nUnscheduled tasks:")
            for task in self.unscheduled_tasks:
                pet_name = self.task_pet_map.get(id(task), '?')
                print(f"  - [{pet_name}] {task.title} ({task.duration} min) | {fmt_time(task.preferred_time)} | due {task.due_date} -- could not fit anywhere")

    def get_reasoning(self):
        """Print the scheduling rationale for every task, explaining why it was placed in its slot
        or why it could not be scheduled."""
        for slot in ('morning', 'afternoon', 'evening'):
            print(f"\n{slot.capitalize()}:")
            for reason in self.reasoning[slot]:
                print(f"  - {reason}")
        if self.reasoning['unscheduled']:
            print("\nUnscheduled:")
            for reason in self.reasoning['unscheduled']:
                print(f"  - {reason}")
