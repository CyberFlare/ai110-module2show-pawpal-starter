# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
My initial UML deisgn contains 4 classes: Owner, Pet, Task, and Schedule. Owner stores user info and available time, Pet stores pet details, and Task represents care activities with duration and priority. Schedule manages tasks and generates the daily plan based on time and priority.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it. \
Yes, added a link between owners and pets. Owners keep track of what pets they own. Added a link betweeen a task and a pet since each pet has tasks needed to be fulfilled to take care of them. 


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most? \
Scheduler considers the time each slot's time budget (morning, afternoon, evening). It considers the tasks priority. If a task has a high or medium priorty, they are scheduled first and are scheduled at the pet's preferred time. If a task  has a low priority, then it takes into account of the owner's preferences of when they want to do tasks.


**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario? \
One tradeoff the scheduler makes is that it schedules greedily by priority, meaning high-priority tasks are placed first without reconsidering later. This can cause lower-priority tasks to be left unscheduled even if a different arrangement could fit everything. This tradeoff could be reasonable because important tasks like feeding or medication should take priority over less critical tasks.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?\
I used AI for speeding up brainstorming. I had the idea of how I wanted the UML to work but I just had AI write it out for me since it was faster under my constraints. I used to help write, debug, and refactor code under my supervisions. Prompts that were specific in describing what I wanted were helpful in getting the AI to produce good results.


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?\
Initially, the scheduler placed all tasks at the start of each time slot, ignoring preferred times. This caused tasks like a 7:00 AM walk to be scheduled at 6:00 AM instead. I identified this issue by checking that scheduled times didn’t match the intended preferences. I then directed a fix so tasks are scheduled at their preferred time when possible, only falling back to the slot start if needed. 
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?\
I tested that tasks and pets behave correctly, like marking tasks complete, adding tasks, and handling valid inputs. These tests were important because scheduling and other features rely on this core behavior working properly.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?\
I am confident that the scheduler works correctly for most normal use cases. Some edge cases I would like to test if I had more time is full schedules or repeated tasks.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?\
I'm satisfied with how the project handles priorities and preferred times while still fitting tasks into available slots. I'm also satisfied with how the UI turned out and how users can interact with it.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?\
If I had another iteration, I would add a calendar blocking feature for the owner (similar to When2Meet) to allow more precise preferred times instead of just morning, afternoon, or evening.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?\
One important thing I learned is that working with AI requires careful checking and guidance, since it can produce working code that doesn’t fully match the intended behavior.