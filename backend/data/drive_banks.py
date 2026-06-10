from __future__ import annotations

# ─────────────────────── Capgemini Exceller x Software Development Engineer ───────────────────────
#
# Capgemini's own campus drive leans on scenario-based technical screening and
# pseudo-code reasoning over memorised syntax - "how would you reason through
# this", not "which keyword goes here". The technical set below mirrors that:
# the MCQ sections favour reasoning-over-a-snippet and complexity trade-offs
# over trivia, and the System Design section is left fully open-ended, the
# same "explain your thinking out loud" shape Capgemini's own scenario round
# actually runs in.

_CAP_SDE_TECHNICAL: tuple[dict, ...] = (
    # ---- Easy (01-06): warm-up, direct recall - 60s each ----
    {
        "section": "DSA", "difficulty": "Easy", "format": "MCQ", "time_limit": 60,
        "prompt": "You need to repeatedly check whether a value has been seen before, in a collection that may grow large. Which structure gives you that check in roughly constant time?",
        "code_snippet": None,
        "options": {"A": "A sorted array, checked with binary search", "B": "A hash set", "C": "A singly linked list", "D": "A min-heap"},
        "answer": "B",
        "justification": {
            "whyCorrect": "A hash set looks a value up by its hash, which costs roughly constant time regardless of how many values it already holds - exactly the shape a repeated 'have I seen this before' check needs.",
            "whyAIsWrong": "Binary search needs the array kept sorted, and inserting into a sorted array costs linear time per insert - the lookup is fast but the upkeep is not.",
            "whyCIsWrong": "A linked list has no structure to skip past values - checking membership means walking it from the front every time, which is linear in its length.",
            "whyDIsWrong": "A heap is built to give you the smallest (or largest) item quickly, not to answer 'is this value in here' - that still costs a linear scan.",
        },
        "focus_skill": "sde.hashing",
    },
    {
        "section": "Core CS", "difficulty": "Easy", "format": "MCQ", "time_limit": 60,
        "prompt": "A class keeps its internal data private and only exposes a small set of methods to work with it. Which OOP idea is this most directly an example of?",
        "code_snippet": None,
        "options": {"A": "Inheritance", "B": "Polymorphism", "C": "Encapsulation", "D": "Abstraction"},
        "answer": "C",
        "justification": {
            "whyCorrect": "Encapsulation is exactly this - bundling data with the methods that operate on it, and hiding that data behind a controlled interface so the rest of the program cannot reach in and corrupt it directly.",
            "whyAIsWrong": "Inheritance is about one class building on another's structure and behaviour - it says nothing about whether that data is hidden or exposed.",
            "whyBIsWrong": "Polymorphism is about the same call behaving differently depending on the object it runs on - a separate concern from whether the data behind it is hidden.",
            "whyDIsWrong": "Abstraction is about exposing only what matters and hiding the rest of the *complexity* - close in spirit, but the question describes the mechanism (hiding data behind methods), which is encapsulation's job specifically.",
        },
        "focus_skill": "sde.oop",
    },
    {
        "section": "DSA", "difficulty": "Easy", "format": "MCQ", "time_limit": 60,
        "prompt": "A print queue has to process jobs in exactly the order they arrived. Which structure naturally enforces that?",
        "code_snippet": None,
        "options": {"A": "A stack", "B": "A queue", "C": "A binary search tree", "D": "A graph"},
        "answer": "B",
        "justification": {
            "whyCorrect": "A queue is first-in-first-out by definition - the first job pushed onto it is the first one that comes back out, which is exactly 'process in arrival order'.",
            "whyAIsWrong": "A stack is last-in-first-out - the most recently added job would jump the line ahead of ones that arrived earlier, the opposite of what is needed here.",
            "whyCIsWrong": "A binary search tree orders things by key value, not by arrival time - it would reorder the jobs around whatever you used as the key.",
            "whyDIsWrong": "A graph models relationships between items, not an ordered sequence to work through - there's no built-in 'next in line' concept to lean on.",
        },
        "focus_skill": "sde.linked_lists",
    },
    {
        "section": "Code Output", "difficulty": "Easy", "format": "MCQ", "time_limit": 60,
        "prompt": "What does this print?",
        "code_snippet": "total = 0\nfor i in range(1, 5):\n    total += i\nprint(total)",
        "options": {"A": "9", "B": "10", "C": "15", "D": "Error - range needs three arguments"},
        "answer": "B",
        "justification": {
            "whyCorrect": "range(1, 5) walks 1, 2, 3, 4 - their sum is 10, and that is what total holds when the loop ends.",
            "whyAIsWrong": "9 is what you'd get from 2 + 3 + 4 - the kind of slip that happens when the first value in the range gets skipped by mistake.",
            "whyCIsWrong": "15 is 1 + 2 + 3 + 4 + 5 - the sum you would get if the range went up to and included 5, which range(1, 5) does not.",
            "whyDIsWrong": "range works perfectly well with two arguments - a start and a stop - and stops one short of that second value, which is exactly what is happening here.",
        },
        "focus_skill": "sde.python_core",
    },
    {
        "section": "Core CS", "difficulty": "Easy", "format": "MCQ", "time_limit": 60,
        "prompt": "In a relational database, what is a foreign key actually for?",
        "code_snippet": None,
        "options": {"A": "It uniquely identifies each row in its own table", "B": "It speeds up text searches on a column", "C": "It points from a row in one table to the row it relates to in another", "D": "It encrypts sensitive columns at rest"},
        "answer": "C",
        "justification": {
            "whyCorrect": "A foreign key is a column (or set of columns) in one table that references the primary key of another - it is the mechanism that links related rows across tables and keeps that link honest.",
            "whyAIsWrong": "That description is the primary key's job - uniquely identifying a row within its own table, not connecting it to another one.",
            "whyBIsWrong": "That is what an index does - foreign keys are about relationships between tables, not search speed, though a foreign key column is often indexed too.",
            "whyDIsWrong": "Encryption is a storage and security concern handled separately - a foreign key's only job is describing how rows in different tables relate to each other.",
        },
        "focus_skill": "sde.dbms_sql",
    },
    {
        "section": "System Design", "difficulty": "Easy", "format": "Open-Ended", "time_limit": 120,
        "prompt": "Say you had to build a basic URL shortener - the kind that turns a long link into a short one and redirects people back to the original. Walk through the core pieces you would need and roughly how a request would flow through them.",
        "code_snippet": None,
        "options": None,
        "answer": None,
        "justification": None,
        "evaluation_rubric": "Looks for: a sense of what gets stored (the mapping between short code and original URL), how a short code gets generated (and what happens if it collides with one that exists), and what happens on the read path when someone visits the short link (lookup, then redirect). A strong answer reasons about the read-heavy nature of the system even at this small scale, without needing to reach for buzzwords.",
        "focus_skill": "sde.hld_system_design",
    },
    # ---- Medium (07-14): application, debugging, analysis - 90s each ----
    {
        "section": "DSA", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "You're given an array of a million integers and need to find the one value that appears more than once, using as little extra memory as you reasonably can. Which approach fits best?",
        "code_snippet": None,
        "options": {"A": "Sort the array, then scan for two equal neighbours", "B": "Compare every pair of elements", "C": "Build a hash set while scanning once, and report the first value already in it", "D": "Build a binary search tree from the elements one at a time"},
        "answer": "C",
        "justification": {
            "whyCorrect": "A single pass with a hash set gives you the answer in roughly linear time, and you stop the moment you hit a value you have already recorded - the most direct route to 'find the repeat' without doing more work than the problem needs.",
            "whyAIsWrong": "Sorting first works and uses less extra memory, but it costs roughly N log N comparisons where the hash-set pass costs roughly N - a real difference at a million elements, and the question specifically asked for an approach that 'fits best', not merely one that works.",
            "whyBIsWrong": "Comparing every pair is roughly N-squared work - at a million elements that is on the order of a trillion comparisons, far past what any reasonable approach should cost.",
            "whyDIsWrong": "Building a tree element by element can degrade to roughly N-squared work in the worst case (a poorly balanced tree), and it is solving a harder problem - full ordering - than the one actually being asked.",
        },
        "focus_skill": "sde.hashing",
    },
    {
        "section": "Core CS", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "Two parts of the same application need to run independently but also share data and crash together if something goes badly wrong. What are you actually describing?",
        "code_snippet": None,
        "options": {"A": "Two separate processes communicating over a socket", "B": "Two threads within the same process", "C": "Two virtual machines on the same host", "D": "Two independent services behind a load balancer"},
        "answer": "B",
        "justification": {
            "whyCorrect": "Threads within one process share that process's memory directly (which is how they share data so easily) and live or die with it (which is why a fatal fault in one can take the whole process - and every thread in it - down together.",
            "whyAIsWrong": "Separate processes are isolated by design - sharing data between them takes deliberate work (a sockets, pipes, shared memory) and a crash in one does not, by itself, take the other down.",
            "whyCIsWrong": "Virtual machines are isolated even more strongly than processes - they do not share memory directly at all, and one going down has no direct effect on the other.",
            "whyDIsWrong": "Independent services behind a load balancer are deliberately decoupled - the entire point of that arrangement is that one failing should not bring the other down with it.",
        },
        "focus_skill": "sde.os_basics",
    },
    {
        "section": "DSA", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "You need to reverse a singly linked list in place - no new list, no array copy. What's the shape of an approach that actually does that?",
        "code_snippet": None,
        "options": {"A": "Walk the list once, pushing each value onto a stack, then pop them back into a new list", "B": "Walk the list once, re-pointing each node's `next` to the node before it as you go, tracking the previous node as you move forward", "C": "Read every value into an array, sort it in reverse, and rebuild the list", "D": "Recursively call reverse on the whole list until it returns the same list back"},
        "answer": "B",
        "justification": {
            "whyCorrect": "This is the in-place shape the question is asking for - one pass, three pointers (previous, current, next), each node's link gets flipped to point backward as you walk forward, and no second structure is ever built.",
            "whyAIsWrong": "This does reverse the order, but it builds a stack and a new list along the way - exactly the extra structures the question ruled out by asking for an in-place approach.",
            "whyCIsWrong": "Sorting reverses the list only if it happened to already be sorted forward - for an arbitrary list, sorting in reverse produces a different order entirely, not the original order backwards.",
            "whyDIsWrong": "That description doesn't actually do anything - a function that calls itself on the same input and returns what it's given back is not reversing, it is just describing a no-op recursion.",
        },
        "focus_skill": "sde.linked_lists",
    },
    {
        "section": "Code Output", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "What does this print?",
        "code_snippet": "def mystery(n, memo={}):\n    if n in memo:\n        return memo[n]\n    if n <= 1:\n        return n\n    memo[n] = mystery(n - 1, memo) + mystery(n - 2, memo)\n    return memo[n]\n\nprint(mystery(6))",
        "options": {"A": "5", "B": "6", "C": "8", "D": "13"},
        "answer": "C",
        "justification": {
            "whyCorrect": "This is Fibonacci with memoisation: mystery(0)=0, mystery(1)=1, and each later value is the sum of the two before it - 0,1,1,2,3,5,8 - so mystery(6) is 8.",
            "whyAIsWrong": "5 is mystery(5), not mystery(6) - an easy slip if you stop counting one step early.",
            "whyBIsWrong": "6 is the input value n itself, not the value the function returns for it - mystery(n) computes a Fibonacci number, it does not echo n back.",
            "whyDIsWrong": "13 is mystery(7) - one step further along the same sequence than what was actually asked for.",
        },
        "focus_skill": "sde.dynamic_programming",
    },
    {
        "section": "Core CS", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "A table storing customer orders repeats the customer's full address on every single order row. What problem does that set up, and what's the standard fix?",
        "code_snippet": None,
        "options": {"A": "It risks inconsistent data when an address changes - the fix is to move address into its own table and reference it by key", "B": "It slows down inserts - the fix is to add more indexes to the orders table", "C": "It wastes disk space only - the fix is to compress the address column", "D": "It is actually the correct design, since joins are expensive and should be avoided"},
        "answer": "A",
        "justification": {
            "whyCorrect": "Repeating the same address across many rows means an update has to find and change every copy - miss one, and you now have two different addresses on file for the same customer. Pulling address into its own table and referencing it by key is exactly what normalisation is for: one place to update, every row stays consistent.",
            "whyBIsWrong": "Indexes help you find rows faster - they do nothing about the actual problem here, which is that the same fact is stored in many places and can drift out of sync.",
            "whyCIsWrong": "Wasted space is a real side effect, but it is the smaller of the two problems - the bigger one is that the same fact living in many places can quietly disagree with itself over time.",
            "whyDIsWrong": "Joins have a cost, but a design that trades data consistency away to avoid them is generally the wrong trade - the standard answer is to normalise first, and only denormalise deliberately once you have a measured reason to.",
        },
        "focus_skill": "sde.dbms_sql",
    },
    {
        "section": "System Design", "difficulty": "Medium", "format": "Open-Ended", "time_limit": 120,
        "prompt": "You're building the backend for a feature that lets users upload profile photos, and the same image has to appear in three places in the UI at different sizes. How would you handle storing it and serving those three variants efficiently?",
        "code_snippet": None,
        "options": None,
        "answer": None,
        "justification": None,
        "evaluation_rubric": "Looks for: separating storage from serving (storing one original, generating/caching resized variants rather than storing all three separately and then re-uploading them), a sense of where the variants live (CDN, object store), and what happens on the read path when a variant is requested. A strong answer reasons about why re-generating on every read is wasteful and how you would only do that work once per original.",
        "focus_skill": "sde.hld_system_design",
    },
    {
        "section": "System Design", "difficulty": "Medium", "format": "Open-Ended", "time_limit": 120,
        "prompt": "An API is getting hammered by a small number of clients sending far more requests than everyone else, and it's starting to slow things down for everyone. How would you design something that keeps that fair, and what would you have to decide about how strict it is?",
        "code_snippet": None,
        "options": None,
        "answer": None,
        "justification": None,
        "evaluation_rubric": "Looks for: naming the actual mechanism (a rate limiter - token bucket, sliding window, or similar), where it would sit (at the edge, before requests reach the real work), what it keys on (per client, per IP, per API key), and what happens to a request that goes over the limit (reject outright, queue, or degrade gracefully). A strong answer also weighs the trade-off of being too strict versus too lenient, rather than treating 'add a limiter' as the whole answer.",
        "focus_skill": "sde.hld_system_design",
    },
    {
        "section": "DSA", "difficulty": "Medium", "format": "MCQ", "time_limit": 90,
        "prompt": "How would you check whether a singly linked list loops back on itself somewhere, without using any extra data structure to track nodes you've already seen?",
        "code_snippet": None,
        "options": {"A": "Walk the list with two pointers, one moving twice as fast as the other - if they ever meet, there's a loop", "B": "Walk the list once and count the nodes - if the count seems too high, there's a loop", "C": "Reverse the list and see if you end up back at the original head", "D": "Store every node's memory address in a list and check for repeats at the end"},
        "answer": "A",
        "justification": {
            "whyCorrect": "This is the classic 'fast and slow pointer' approach - in a list with a loop, the faster pointer eventually laps the slower one and they land on the same node; in a list without one, the faster pointer simply reaches the end first. It needs nothing beyond two pointers.",
            "whyBIsWrong": "If the list loops, there is no end to count up to - the walk never terminates, so 'count seems too high' never actually resolves into an answer.",
            "whyCIsWrong": "Reversing a list that loops back on itself runs into the same problem reversing any infinite structure would - there's no final node to anchor the reversal at.",
            "whyDIsWrong": "This works, but it is exactly the kind of extra structure (a growing list of seen addresses) the question explicitly ruled out - and it costs memory proportional to the list's length where the two-pointer approach costs none.",
        },
        "focus_skill": "sde.linked_lists",
    },
    # ---- Hard (15-20): synthesis, complex DSA, design - 120s each ----
    {
        "section": "DSA", "difficulty": "Hard", "format": "MCQ", "time_limit": 120,
        "prompt": "You need the shortest path, by total travel time, between two stations in a transit network where each connecting leg takes a different amount of time. Which approach actually accounts for those different leg times correctly?",
        "code_snippet": None,
        "options": {"A": "A plain breadth-first search counting the number of stops", "B": "Dijkstra's algorithm, always expanding from the station with the smallest known total time so far", "C": "A depth-first search that tries every possible route and keeps the shortest", "D": "Sort all the legs by travel time and pick the shortest ones until you reach the destination"},
        "answer": "B",
        "justification": {
            "whyCorrect": "Dijkstra's approach builds up the shortest known time to each station by always expanding the one currently cheapest to reach - which is exactly what 'shortest by total travel time, where legs differ in cost' calls for.",
            "whyAIsWrong": "Plain breadth-first search finds the path with the fewest stops, treating every leg as if it cost the same - it has no way to account for one leg taking five minutes and another taking fifty.",
            "whyCIsWrong": "Trying every route does eventually find the shortest one, but its cost grows explosively with the size of the network - it 'works' in the same sense that checking every possible password works, just not at any size that matters.",
            "whyDIsWrong": "Picking the cheapest legs greedily, without regard to whether they actually connect into a path to the destination, can easily strand you somewhere with no way to finish the journey - shortest-path needs to reason about connected routes, not isolated leg costs.",
        },
        "focus_skill": "sde.graphs",
    },
    {
        "section": "Core CS", "difficulty": "Hard", "format": "MCQ", "time_limit": 120,
        "prompt": "Two transactions hit the same row at the same time - one reading it, one updating it mid-flight - and the reader ends up seeing a value that the writer later rolled back. What's this kind of problem generally called, and what's the database-level fix?",
        "code_snippet": None,
        "options": {"A": "A deadlock - fixed by adding more indexes", "B": "A dirty read - fixed by raising the transaction's isolation level so it cannot see uncommitted changes", "C": "A race condition - fixed by rewriting the query in a different language", "D": "Data corruption - fixed by restoring from the most recent backup"},
        "answer": "B",
        "justification": {
            "whyCorrect": "Seeing a value another transaction wrote but later undid is the textbook definition of a dirty read - and the standard fix is exactly what it sounds like: raise the isolation level so a transaction is only ever shown changes that have actually been committed.",
            "whyAIsWrong": "A deadlock is two transactions stuck waiting on each other's locks, neither able to proceed - a different failure shape entirely, and indexes have nothing to do with fixing either one.",
            "whyCIsWrong": "'Race condition' is the right general family of problem, but the specific symptom described - reading a value that gets rolled back - has a name and a known database-level fix; reaching for a language rewrite skips past both.",
            "whyDIsWrong": "Nothing here is actually corrupted - the data the reader saw was real at the moment it read it, just not final. A backup restore is solving a problem that did not occur.",
        },
        "focus_skill": "sde.dbms_sql",
    },
    {
        "section": "System Design", "difficulty": "Hard", "format": "Open-Ended", "time_limit": 120,
        "prompt": "You're asked to design the layer that sits in front of a database and serves the same handful of values to millions of reads a second, with the underlying data changing only occasionally. What would you build, and how would you keep what it serves from going stale?",
        "code_snippet": None,
        "options": None,
        "answer": None,
        "justification": None,
        "evaluation_rubric": "Looks for: identifying this as a caching problem (an in-memory layer in front of the database), reasoning about what gets cached and for how long, and - the part that actually separates a strong answer from a surface one - a real plan for invalidation: what happens when the underlying value changes (expire on a timer, invalidate on write, or some mix), and what a reader sees in the gap before that catches up. Bonus for noticing the trade-off between serving slightly-stale data fast versus always-fresh data slow.",
        "focus_skill": "sde.hld_system_design",
    },
    {
        "section": "System Design", "difficulty": "Hard", "format": "Open-Ended", "time_limit": 120,
        "prompt": "Picture the backend behind a ride-hailing app's matching screen - the part that finds a nearby driver for a rider and connects them. What pieces would that system need, and what's the trickiest part of getting it right?",
        "code_snippet": None,
        "options": None,
        "answer": None,
        "justification": None,
        "evaluation_rubric": "Looks for: a sense of the moving parts (tracking where drivers currently are, finding ones near a given rider, deciding which one to offer the ride to first, and handling the back-and-forth of an offer being accepted or declined). The strongest answers single out the genuinely hard part on their own - that two riders' searches can both land on the same nearby driver at once, and the system has to resolve that race without double-booking anyone or leaving a driver hanging.",
        "focus_skill": "sde.hld_system_design",
    },
    {
        "section": "Code Output", "difficulty": "Hard", "format": "MCQ", "time_limit": 120,
        "prompt": "What does this print?",
        "code_snippet": "def make_counters():\n    counters = []\n    for i in range(3):\n        counters.append(lambda: i)\n    return counters\n\nprint([c() for c in make_counters()])",
        "options": {"A": "[0, 1, 2]", "B": "[2, 2, 2]", "C": "[0, 0, 0]", "D": "Error - i is not defined outside the loop"},
        "answer": "B",
        "justification": {
            "whyCorrect": "Each lambda doesn't capture the *value* of i at the moment it's created - it captures the variable i itself, and looks it up only when called. By the time any of them run, the loop has finished and i is sitting at its final value, 2 - so all three report the same thing.",
            "whyAIsWrong": "This is what you'd get if each lambda froze i's value at creation time - which feels intuitive, but is not how closures over loop variables work in this kind of code.",
            "whyCIsWrong": "0 would only show up if the lambdas somehow ran before the loop started, which they can't - they're called only after make_counters returns the finished list.",
            "whyDIsWrong": "i is very much still defined - loop variables in this kind of loop don't go out of scope when the loop ends, which is in fact the whole reason this surprising behaviour happens at all.",
        },
        "focus_skill": "sde.python_core",
    },
    {
        "section": "Code Output", "difficulty": "Hard", "format": "MCQ", "time_limit": 120,
        "prompt": "Two threads both run `counter += 1` on the same shared variable, a thousand times each, with no locking around it. What's the most likely outcome, and why?",
        "code_snippet": "counter = 0\n\ndef bump():\n    global counter\n    for _ in range(1000):\n        counter += 1\n\n# bump() is run on two threads at the same time, then we print(counter)",
        "options": {"A": "It always prints 2000, since each thread does exactly 1000 increments", "B": "It often prints something less than 2000, because `counter += 1` is really read-modify-write, and the two threads can interleave those steps and overwrite each other's update", "C": "It crashes, because two threads cannot touch the same variable", "D": "It prints 1000, because the second thread's updates simply replace the first thread's"},
        "answer": "B",
        "justification": {
            "whyCorrect": "`counter += 1` is not one atomic step - it reads the current value, adds one, and writes the result back. If both threads read the same value before either writes its update back, one increment effectively gets lost. Run enough times, and the final count lands somewhere under 2000, by an amount that varies run to run.",
            "whyAIsWrong": "That's what you'd get if the two thousand increments happened one at a time with nothing overlapping - which is precisely the guarantee that's missing without a lock around the read-modify-write.",
            "whyCIsWrong": "Threads sharing a plain variable like this is completely legal and won't crash - it will just produce a wrong, inconsistent answer, which is the more dangerous outcome because it looks like it's working.",
            "whyDIsWrong": "Neither thread's work simply vanishes wholesale - what's lost is individual increments here and there, whenever the two threads' read-modify-write steps happen to overlap, not one thread's entire contribution.",
        },
        "focus_skill": "sde.os_basics",
    },
)


# Capgemini's own materials describe their screening as AMCAT-pattern - a mix
# of numerical, logical and verbal reasoning that leans toward spotting a
# pattern quickly over grinding through long arithmetic. The split below (8
# numerical, 7 logical, 5 verbal) follows the spec's drive-specific weighting
# for this one; the questions themselves favour the kind of "see the rule,
# apply it" framing AMCAT-style screens are known for.
_CAP_APTITUDE: tuple[dict, ...] = (
    {"section": "Numerical", "kind": "numerical", "prompt": "A train 150 metres long crosses a platform 350 metres long in 25 seconds. What is its speed in km/h?",
     "options": ["54 km/h", "60 km/h", "72 km/h", "80 km/h"], "answer": "72 km/h",
     "explainer": "Total distance covered is 150 + 350 = 500 m in 25 s, which is 20 m/s - and 20 x 3.6 = 72 km/h."},
    {"section": "Numerical", "kind": "numerical", "prompt": "A shop takes 20 percent off, then another 10 percent off the new price. What is the overall discount?",
     "options": ["18%", "28%", "30%", "32%"], "answer": "28%",
     "explainer": "The price ends at 0.8 x 0.9 = 0.72 of the original, a 28 percent drop overall - the two discounts do not simply add to 30 percent because the second one applies to an already-reduced price."},
    {"section": "Numerical", "kind": "numerical", "prompt": "A can finish a job in 12 days, B can finish the same job in 18 days. Working together, how many days will it take them?",
     "options": ["6 days", "7.2 days", "8 days", "9 days"], "answer": "7.2 days",
     "explainer": "A does 1/12 of the job per day, B does 1/18 - together that's 1/12 + 1/18 = 5/36 of the job per day, so the whole job takes 36/5 = 7.2 days."},
    {"section": "Numerical", "kind": "numerical", "prompt": "A shopkeeper buys an item for 800 rupees and sells it for 1000 rupees. What is the profit percentage?",
     "options": ["20%", "25%", "12.5%", "30%"], "answer": "25%",
     "explainer": "Profit is 1000 - 800 = 200, and profit percentage is always measured against the cost price: 200/800 = 25%."},
    {"section": "Numerical", "kind": "numerical", "prompt": "Two numbers are in the ratio 3:5, and their sum is 96. What is the larger number?",
     "options": ["36", "48", "56", "60"], "answer": "60",
     "explainer": "The numbers are 3 parts and 5 parts of a whole that totals 8 parts. Each part is 96/8 = 12, so the larger number is 5 x 12 = 60."},
    {"section": "Numerical", "kind": "numerical", "prompt": "The average of five numbers is 24. If one number is removed, the average of the remaining four becomes 22. What was the removed number?",
     "options": ["28", "30", "32", "36"], "answer": "32",
     "explainer": "The five numbers total 5 x 24 = 120, and the remaining four total 4 x 22 = 88 - so the removed number is 120 - 88 = 32."},
    {"section": "Numerical", "kind": "numerical", "prompt": "A sum of money becomes 1.21 times itself in 2 years at a certain rate of compound interest, compounded annually. What is the annual rate?",
     "options": ["8%", "10%", "11%", "12%"], "answer": "10%",
     "explainer": "If the rate is r, then (1 + r)^2 = 1.21, so 1 + r = 1.1, giving r = 10% - a number worth recognising on sight (1.1 squared is 1.21)."},
    {"section": "Numerical", "kind": "numerical", "prompt": "A father is currently three times as old as his son. In 12 years, he will be twice as old as his son. What is the son's current age?",
     "options": ["10", "12", "14", "16"], "answer": "12",
     "explainer": "Let the son's age be x, so the father's is 3x. In 12 years: 3x + 12 = 2(x + 12), which gives 3x + 12 = 2x + 24, so x = 12."},
    {"section": "Logical", "kind": "logical", "prompt": "Look at the series 3, 7, 15, 31, 63. What comes next?",
     "options": ["95", "111", "127", "135"], "answer": "127",
     "explainer": "Each term is double the one before it, plus one: 63 x 2 + 1 = 127."},
    {"section": "Logical", "kind": "logical", "prompt": "If CODING is written as DPEJOH, how would FLOWER be written under the same rule?",
     "options": ["GMPXFS", "GMPWFS", "FLOWFR", "GNQYFT"], "answer": "GMPXFS",
     "explainer": "Each letter shifts one place forward in the alphabet: F->G, L->M, O->P, W->X, E->F, R->S, giving GMPXFS."},
    {"section": "Logical", "kind": "logical", "prompt": "A is the brother of B. B is the sister of C. C is the father of D. How is A related to D?",
     "options": ["Uncle", "Father", "Grandfather", "Brother"], "answer": "Uncle",
     "explainer": "A, B and C are siblings, and C is D's parent - which makes A, C's sibling, an uncle to D."},
    {"section": "Logical", "kind": "logical", "prompt": "All pens are pencils. Some pencils are erasers. Which conclusion follows?",
     "options": ["All pens are erasers", "Some pencils are pens", "No pens are erasers", "All erasers are pencils"], "answer": "Some pencils are pens",
     "explainer": "'All pens are pencils' means every pen sits inside the pencil group - so at least some pencils (the ones that are pens) are pens. The other options all claim more than the two statements actually guarantee."},
    {"section": "Logical", "kind": "logical", "prompt": "Starting from her house, Meera walks 6 km north, then 8 km east. How far is she from her starting point in a straight line?",
     "options": ["10 km", "12 km", "14 km", "9 km"], "answer": "10 km",
     "explainer": "The two legs form a right angle, so the straight-line distance is the hypotenuse: the square root of (6 squared + 8 squared) = the square root of 100 = 10 km - the well-known 6-8-10 triangle."},
    {"section": "Logical", "kind": "logical", "prompt": "Five friends sit in a row. Raj sits to the immediate right of Priya, who sits at one end. Aman sits between Raj and Sita. Who sits at the other end if Vikram is the fifth?",
     "options": ["Aman", "Raj", "Sita", "Vikram"], "answer": "Vikram",
     "explainer": "Priya anchors one end; Raj sits immediately to her right, then Aman, then Sita follows the order 'Aman sits between Raj and Sita' - that fills four seats in sequence (Priya, Raj, Aman, Sita), leaving Vikram for the only seat left, the other end."},
    {"section": "Logical", "kind": "logical", "prompt": "Which one of these does not belong with the others: Square, Triangle, Circle, Cube?",
     "options": ["Square", "Triangle", "Circle", "Cube"], "answer": "Cube",
     "explainer": "A square, triangle and circle are all flat, two-dimensional shapes - a cube is the odd one out as the only three-dimensional solid in the group."},
    {"section": "Verbal", "kind": "verbal", "prompt": "Which word is closest in meaning to 'meticulous'?",
     "options": ["Careless", "Thorough", "Hurried", "Indifferent"], "answer": "Thorough",
     "explainer": "'Meticulous' describes close, careful attention to detail - 'thorough' sits nearest that meaning of the four."},
    {"section": "Verbal", "kind": "verbal", "prompt": "Which word is most nearly opposite in meaning to 'reluctant'?",
     "options": ["Hesitant", "Willing", "Cautious", "Doubtful"], "answer": "Willing",
     "explainer": "'Reluctant' means unwilling or hesitant to do something - 'willing' sits at the opposite end of that scale; the other three options all lean toward the same hesitant meaning as the original word."},
    {"section": "Verbal", "kind": "verbal", "prompt": "Choose the option that best completes the sentence: 'Despite the heavy rain, the team decided to ___ with the outdoor event as planned.'",
     "options": ["give up", "do away", "go ahead", "look up"], "answer": "go ahead",
     "explainer": "'Go ahead with' means to proceed with something as planned, which fits the sentence's meaning - the other phrasal verbs either mean the opposite (give up, do away with) or do not fit the context at all (look up)."},
    {"section": "Verbal", "kind": "verbal", "prompt": "Identify the part of the sentence that contains an error: 'Neither of the candidates (A) have submitted (B) their final report (C) before the deadline (D).'",
     "options": ["Part A", "Part B", "Part C", "Part D"], "answer": "Part B",
     "explainer": "'Neither' is singular, so it takes a singular verb - the sentence should read 'has submitted', not 'have submitted'. The other three parts are grammatically sound."},
    {"section": "Verbal", "kind": "verbal", "prompt": "Choose the one-word substitute for 'a person who knows many languages':",
     "options": ["Linguist", "Polyglot", "Interpreter", "Bilingual"], "answer": "Polyglot",
     "explainer": "A 'polyglot' is specifically someone who knows and uses several languages. A linguist studies language as a field, an interpreter translates speech, and 'bilingual' describes knowing exactly two languages - none names the general 'many languages' case as precisely."},
)


# Capgemini's behavioural round runs in a structured STAR format and circles
# back to how a fresher actually behaves on a delivery team - not abstract
# "tell me about yourself" prompts, but the specific situations an SDE meets
# in their first year: an unfamiliar codebase, a code review pushback, a
# deadline that suddenly moved, a teammate who is stuck. These twenty are
# written to that brief.
_CAP_SDE_BEHAVIORAL: tuple[str, ...] = (
    "Tell me about a time you had to work with a codebase someone else wrote, with little to no documentation. How did you go about understanding it before changing anything?",
    "Describe a situation where your code passed your own testing but broke something else once it was merged. What did you do once you found out?",
    "Give an example of a time a senior engineer pushed back hard on something you wrote in a code review. How did you respond in the moment, and afterward?",
    "Tell me about a time a deadline moved up with little warning. How did you decide what to cut, delay, or push back on?",
    "Describe a time you noticed a teammate was stuck on something for longer than they should have been. What did you do?",
    "Tell me about a bug that took you far longer to find than you expected. What finally cracked it open?",
    "Give an example of a time you had to choose between doing something the 'right' way and doing it the fast way under pressure. What did you decide, and how did it turn out?",
    "Describe a time you disagreed with a technical decision your team had already made. Did you raise it, and what happened either way?",
    "Tell me about a time you had to pick up a new tool, language, or framework quickly to get something done. How did you approach learning it on the fly?",
    "Give an example of a time you had to explain a technical problem to someone who was not technical - a manager, a client, a teammate from another team. How did you adjust how you explained it?",
    "Describe a situation where something you built started getting used in a way you had not planned for. How did you handle that?",
    "Tell me about a time you made an estimate that turned out to be way off. What did you learn about how you estimate?",
    "Give an example of a time you had to give a teammate feedback on their code or approach that you knew they might not want to hear.",
    "Describe a moment where you realised partway through a task that your original approach was not going to work. What did you do next?",
    "Tell me about a time you had to balance two things competing for your attention - a feature you were building and a production issue that came up. How did you decide what to do first?",
    "Give an example of a time you asked for help on something, rather than spending longer trying to solve it alone. What made you decide to ask?",
    "Describe a project where the requirements kept shifting partway through. How did you keep your work from becoming wasted effort?",
    "Tell me about a time you found a problem in something that was already considered 'done' and shipped. What did you do about it?",
    "Give an example of a time you had to work alongside someone whose working style was very different from yours. How did you find a way to collaborate well?",
    "Describe a time you took on something slightly outside your usual responsibilities because it needed doing. What pushed you to step up?",
)


# Capgemini's HR conversations are known for circling back to "why this
# company specifically" and how a candidate's own direction lines up with the
# kind of long-tenure, project-rotation career a large consulting firm
# actually offers - distinct from a product company's "why do you want to
# build this thing" framing. These twenty follow the spec's four groupings,
# with `{role}` left as the one templated slot the router fills with the
# learner's actual target role.
_CAP_HR: tuple[dict, ...] = (
    # Career direction & role fit (6)
    {"group": "Career direction & role fit", "template": "Why Capgemini, and why a {role} role here specifically - what makes this feel like the right next step for you?"},
    {"group": "Career direction & role fit", "template": "Where do you see yourself three years from now, and how does starting as a {role} fit into getting there?"},
    {"group": "Career direction & role fit", "template": "What drew you toward {role} work in the first place, rather than a different kind of role you could have aimed for?"},
    {"group": "Career direction & role fit", "template": "What part of {role} work do you think you would find most challenging in your first six months, and how would you approach that?"},
    {"group": "Career direction & role fit", "template": "What does doing {role} work well look like to you, beyond just getting the assigned task done?"},
    {"group": "Career direction & role fit", "template": "If you had to pick one skill you most want to grow in over your first year as a {role}, what would it be and why that one?"},
    # Company-specific culture alignment (5)
    {"group": "Company culture alignment", "template": "Capgemini works across many industries and moves people between projects as the business needs shift. How do you feel about not knowing exactly what you will be working on a year from now?"},
    {"group": "Company culture alignment", "template": "A lot of consulting work means representing the company in front of a client, not just writing code for an internal team. How would you prepare yourself for that side of the job?"},
    {"group": "Company culture alignment", "template": "Large organisations like this one run on structured processes - sign-offs, documentation, defined handoffs. How do you feel about working inside that kind of structure?"},
    {"group": "Company culture alignment", "template": "You would likely be working alongside people from very different backgrounds, time zones and working styles on any given project. What have you done before that prepared you for that?"},
    {"group": "Company culture alignment", "template": "What have you read or heard about how Capgemini operates that made you want to work here specifically, rather than at a similar firm?"},
    # Strengths, weaknesses, conflict resolution (5)
    {"group": "Strengths, weaknesses, conflict resolution", "template": "What would you say is your biggest strength as a {role}, and can you point to something specific that shows it?"},
    {"group": "Strengths, weaknesses, conflict resolution", "template": "What is something about how you work that you are actively trying to improve right now?"},
    {"group": "Strengths, weaknesses, conflict resolution", "template": "Tell me about a time you and a colleague saw the same problem completely differently. How did the two of you land somewhere you could both work with?"},
    {"group": "Strengths, weaknesses, conflict resolution", "template": "How do you usually handle a situation where you think you are right but the rest of the room disagrees with you?"},
    {"group": "Strengths, weaknesses, conflict resolution", "template": "What kind of feedback do you find hardest to hear, and how do you try to sit with it rather than push back on it right away?"},
    # Salary, relocation, commitment, follow-through (4)
    {"group": "Salary, relocation, commitment, follow-through", "template": "This role may involve relocating to wherever the project needs you to be, sometimes on short notice. How do you feel about that?"},
    {"group": "Salary, relocation, commitment, follow-through", "template": "What matters most to you in choosing where to start your career - is it the role, the company, the location, the compensation, or some mix, and how would you weigh them against each other?"},
    {"group": "Salary, relocation, commitment, follow-through", "template": "How long would you want to stay in a {role} position before looking to move into something else, and what would make you feel ready for that move?"},
    {"group": "Salary, relocation, commitment, follow-through", "template": "If you got an offer from us and another company at the same time, what would actually decide it for you?"},
)


TECHNICAL_BANKS: dict[tuple[str, str], tuple[dict, ...]] = {
    ("cap_exceller", "Software Development Engineer"): _CAP_SDE_TECHNICAL,
}

APTITUDE_BANKS: dict[str, tuple[dict, ...]] = {
    "cap_exceller": _CAP_APTITUDE,
}

BEHAVIORAL_BANKS: dict[tuple[str, str], tuple[str, ...]] = {
    ("cap_exceller", "Software Development Engineer"): _CAP_SDE_BEHAVIORAL,
}

HR_BANKS: dict[str, tuple[dict, ...]] = {
    "cap_exceller": _CAP_HR,
}


def technical_bank(drive_key: str, role: str) -> tuple[dict, ...] | None:
    return TECHNICAL_BANKS.get((drive_key, role))


def aptitude_bank(drive_key: str) -> tuple[dict, ...] | None:
    return APTITUDE_BANKS.get(drive_key)


def behavioral_bank(drive_key: str, role: str) -> tuple[str, ...] | None:
    return BEHAVIORAL_BANKS.get((drive_key, role))


def hr_bank(drive_key: str) -> tuple[dict, ...] | None:
    return HR_BANKS.get(drive_key)
