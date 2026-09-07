---
description: Refactor code without changing behaviour by accident — extractions, moves, decompositions, deletions, "simplifications". Use when splitting a large function, lifting a rule into a module, unifying duplicated code, clearing a lint backlog, putting a schema on an untyped boundary, or making any change whose whole claim is "this behaves the same". Covers proving equivalence by running both versions, the failure shapes moved code actually has, mutation-verifying every test you write, and the traps in the tooling that make a broken change look green.
---

# Refactor safely

A refactor's entire claim is **"this behaves the same"**. That claim is not provable by reading, and the ways it fails are specific and repeatable. This is what they are and how to catch them.

Everything here was paid for. The examples are real and the numbers are measured.

## Before you start: establish what is actually there

Four questions set the size and the shape of the change. Each is cheap to answer and expensive to guess.

### Is the code you are about to touch even reachable?

Extraction makes code look considered. A carefully named module with tests reads as load-bearing whether or not anything calls it.

**Find the producer before you touch the consumer.** Grep for who emits the input, not just who handles it.

> Four `else if` arms handling `thinking` / `thinking_start` / `thinking_delta` / `thinking_stop` were extracted into a clean, tested module. Three of them were unreachable: the backend never sent `thinking_start`, so the client never opened a bubble and discarded every delta. A bug filed against one of those arms — argued entirely from the code, with no observation of the app — got a correct fix for a path production cannot reach. One `grep` for the producer would have caught it.

Reachability is also what tells you whether "no test covers this" means *write one* or *delete it*.

### "Was it ever wired?" is a question for the history, not the code

Reading tells you a branch cannot fire today. It does not tell you whether it fired last year — and that is the difference between *dead, delete it* and *broken, fix it*. The two want opposite changes, and the code in front of you cannot distinguish them.

`git log -S "<field or symbol>" -- <the file that would have to supply it>` answers it directly: every commit where that string entered or left that file.

> Three middlewares resolved a tenant from token claims read off the request's user object. That object is built from a database row and carries no claims, so the branches were unreachable — but an issue had sat open precisely because nobody could say whether the claims *used to* arrive and something later broke the pipeline. `git log -S` on the field, against the file that hydrates the user, returned **nothing**: in that file's entire history it has never handled it. Dead on arrival, not broken later — which is what made deleting them correct rather than a papering-over of a real regression.

An empty result is a strong answer. A non-empty one hands you the commit that removed the wiring, which is a different investigation entirely.

### Count the copies before you fix one

Deleting or correcting a rule at the site a reviewer named leaves the sites they did not. Worse than leaving all of them: the fixed one reads as *handled*, so the concept looks addressed.

> One question — "which tenant does this belong to?" — was answered by three separate functions. A boundary check was added to the one that was reported. A later round found a working cross-tenant sequence through the second. A round after that found the third, still un-checked, unreachable only by accident of which route guarded its caller. The same shape, three times, in one change.

Before fixing, grep for the *concept*, not the symbol: every place that answers the same question, however it spells it. Fix them together or unify them into one function in the same change — a partial unification is a trap that reads as a fix.

### When findings keep arriving in the same shape, change the rule

The same lesson arrives again during review, one round at a time. A reviewer who finds a new way past your check every round is telling you the check enumerates BAD forms — and there is always one more form than anyone will list.

> A bubble left open when a turn ended was fixed at each exit. Three were patched; review found a fourth; a fifth would have been silent. The rule moved into the one function every terminal frame passes through, so an exit nobody has written yet is covered.

Enumerate what is **permitted** instead, and report everything else. It fails closed. And **name the invariant you now depend on** — "ending a turn means writing a terminal frame through this writer" — then test *that*, because it is the part a future change breaks without noticing.

### Someone else may be refactoring the same file, and open work does not show it

A backlog-clearing refactor — a lint rule, a rename, a type applied across a package — is exactly the kind of work several people pick the same target for. Checking open pull requests finds only what has already been published.

> Four collisions in one sweep. The last one had **not been open** when the file was chosen; it merged first, removed the same annotations, and did it better. The whole change was discarded — its tests were the only part that did not overlap, and they only survived because they were separated out into their own change.

Two things follow. Announce the file before starting, in whatever place the work is coordinated. And when the collision happens anyway, **split rather than merge**: keep only the part that does not overlap, say plainly that the rest was superseded, and close the original. A conflict resolution between two versions of the same refactor is worth less than either version.

## When a lint rule or a gate is what triggered the change

Clearing a backlog is refactoring — the claim is still "this behaves the same" — and it has its own failure modes, because the thing that complained can also answer.

### Let the constraint tell you how large the change is

When a refactor is triggered by something that can answer — a failing test, a type error, a lint rule, a CI gate — the size of the change is a measurement, not a judgement. It gets guessed instead, and a guess that runs large buys a rewrite the constraint never asked for.

> `react-hooks/refs` flagged two byte-identical inline handlers reading `terminalRef.current`. Extracting them into one `useCallback` — the obvious fix, and a genuine de-duplication — **did not clear the warning**. Nor did dropping the `.current` read so the callback touched no ref: passing the ref *object* was enough to keep it. The real objection was that `sidebarBtn`, a 30-line JSX factory called 13 times during render, was handed a ref-touching function; only turning it into a component cleared both. Each wrong guess cost one run to disprove and would have cost a rewrite to assume.

Make the smallest version, re-run the thing that complained, read what it says. *Then* decide how far to go. The corollary is worth as much: when the small version **does** clear it, you have been told the large one was scope you invented.

### A warning is a symptom. Ask who the victim is before silencing it

The fastest way to clear a backlog wrong is to treat each finding as a formatting complaint. Some of them are sitting on a live defect, and the warning is the only thing pointing at it.

> Two warnings in a batch of hundreds turned out to be user-visible bugs. A "cannot modify during render" on a global registration: two hooks were writing the *same* window key, so the later one won and the Stop button had never cancelled anything in the browser. A "cannot access during render" on a memo: a date window computed once at mount, so a long-lived tab queried the wrong day after midnight. Both had a comment nearby asserting the opposite of what the code did.

For each finding ask **what breaks if the rule is right**. If the answer is "nothing observable", it is a cleanup. If you cannot answer it, that is the one to read closely.

### Turning a rule off needs the same evidence as fixing it

"Too noisy" is a reason to look, not a verdict. Disabling a rule is a claim that none of its findings matter, which is an assertion about every one of them.

> Two rules produced 115 of 158 findings and buried the four that report runtime-wrong behaviour. Before switching them off, all 103 findings of the louder one were audited for the single shape that is unambiguously a bug; none matched. That audit is what made the decision defensible, and it is recorded next to the `off` — including how to re-enable it to work the backlog.

Record the reason **per rule**. Two rules disabled in one commit for one shared reason is usually one real reason and one unexamined one: a rule whose diagnostic describes a cost that exists whether or not your build runs the tool it names is not the same case as a rule that cannot be true in your build at all.

## Proving equivalence: run both, do not reason

Copy the OLD code verbatim into a throwaway harness, run it beside the new code over generated inputs, compare whole results, report the count, then delete the harness.

- **Generate the inputs, do not choose them.** Enumerate or randomise over the shapes the code actually sees — missing keys, genuine zeros, empty arrays, `null` elements, both spellings of a field, several turns of accumulated state. The cases you would think to write by hand are the ones you already believe are equal.
- **"Equivalent given the guard above" is precisely the reasoning that fails.** In one extraction, `reasoningPart(content)` looked identical to `content[0]?.type === 'reasoning'` under a `length === 1` check. It is not — that helper dereferences each part, so a lone `null` THREW where `?.` returned false, inside a React `setMessages` updater where a throw breaks the render. Reasoning said equivalent; 2,520 generated arrangements found two that were not (measured on a real refactor).
- **A throw is an outcome.** Wrap both sides and compare `ok:<value>` against `threw:<message>`. A harness that dies on the first exception is not measuring; and "both sides throw identically" is a real result worth stating.
- **Compare at the caller's boundary**, and compare the WHOLE result (`JSON.stringify` both sides), not the fields you suspect.
- **Fold state too.** Single-shot cases cannot reach a list the rule itself built. Run randomised *sequences* against a growing accumulator.
- **State the count.** "255 pairs and 2,217 sequenced applications, 0 differences, 22 reaching the same thrown error on both sides" is what lets a change merge, and "140,000 comparisons, 0 differences" is what let a token-accounting extraction feeding billing merge with confidence (measured on a real refactor). "I read it carefully" is not, and neither is a green suite that only ever tested the new code.

The rest of this section is about the harness itself, which is code you wrote in the same sitting and under the same assumptions as the change.

### Mutation-verify the harness before you trust its zero

A harness that reports 0 differences and *cannot* report anything else is worse than no harness.

> Mutating one word in the new implementation — storing `thought.trim()` instead of `thought` — produced 12 and 178 differences across the two sweeps. That number is what makes the 0 mean something.

**Pick the mutation case so it can actually differ.** A break-check that fails to break says nothing about the harness and looks exactly like a harness that is broken.

> A transposition check swapped `label` and `title` at call site 3 and reported **0 differing fields** — because that site's label and title were both the string `'Solutions'`. The harness was fine; the case could not distinguish anything. Choosing the site programmatically (`findIndex(o => o.label !== o.title)`) reported 2, which is the answer that means something.

**Derive the expected count from the generators, never from your own arithmetic.** `expect(all.length).toBeGreaterThan(2000)` on a sweep I had estimated at 2×2×4×3×3×3×3 failed at 1296 — the assertion caught my multiplication, which is the only reason the number published later was the real one.

### A zero is a claim about your generator, not about the code

The generator is the part that fails, and it fails silently: a shape it never produces is a difference the harness cannot see. Reasoning is not what catches this — **mutating each edited line is**. A mutation that produces 0 differences means the generator is blind there, and the fix is the generator, not the code.

> One comparison reported 5,440 comparisons / 0 differences. Four mutations of the lines that changed: two produced hundreds of differences, **two produced zero**. No generated input carried both alternatives of a fallback chain, and none carried a falsy-but-not-nullish value. Neither line was even part of the change — but the harness had been reading as coverage of the whole function. Another reported 99/0 for a walk whose intermediate paths were always empty; adding a pre-existing scalar there found a `TypeError` that two environment variables were enough to trigger at startup.

Run one mutation per edited line before publishing the count. Then say which shapes the generator produces.

The blind spots repeat, and they are worth generating deliberately:

- **a pre-existing value where the code expects to create one** — not just an empty container, but a scalar, an array, a `0`, and an object, at an *intermediate* step of a walk
- **both alternatives of an `||` / `??` chain present at once** — with one, the order cannot be observed and swapping it stays green
- **falsy but not nullish** (`0`, `''`, `false`, `NaN`) — the only shapes that separate `||` from `??`
- **the field carried on the prototype instead of owned** — `Object.create({field})`, a class with a getter, a subclass
- **keys every object already has** — `constructor`, `__proto__`, `toString`. `JSON.parse('{"__proto__":…}')` makes one; an object *literal* does not, which is its own trap below
- **the same value at two positions** — first and last, so "reads the first" is distinguishable from "reads the last" *and* from "reads whichever one has a value"

### A comparison that compares nothing reports zero

A loop that iterates is not a loop that compares. When the value on one side is unreachable — a helper that no longer exists, an accessor that returns nothing, a guard that skips — the count keeps rising and every case is skipped.

Make the harness **throw where it cannot compare** rather than continue. A zero you cannot distinguish from an absence is not a measurement, and it is indistinguishable from success at exactly the moment you most want to trust it.

### When the call's FORM changes, the values are not the whole of it

Positional arguments becoming named props, a function call becoming a JSX element, a helper becoming a method — the *surrounding* expression changes with the call, and a harness that walks the arguments is blind to it.

> Converting a render-time factory to a component was checked by parsing both trees and comparing every argument against its new prop: 91 values across 13 call sites, 89 identical, 2 changed as intended, 0 unexpected. It read as complete and was not. Two sites had gone from `{isAdmin && f(...)}` to `{isAdmin && (<C ... />)}`, and **nothing in that comparison looked at the condition** — a button could have started rendering for the wrong users with all seven of its values still matching. Collecting each site's chain of enclosing `&&` operands and ternary conditions and comparing those too: 13/13 identical. It only got checked because someone asked whether I was sure.

Ask what the old form carried that was not an argument: the guard around it, the position in a list, the `key`, what it was nested inside.

### An exemption inside the harness is an unmeasured claim wearing the harness's authority

Every real comparison has rows that changed on purpose. Marking them "as intended" and moving on is how the one thing you actually rewrote becomes the one thing nothing ran.

> The 2 intended differences above were the two handlers replaced by one shared callback, checked by reading them side by side — they looked equivalent, and the helper I substituted was literally the same expression. Running them instead, over eight generated worlds (visible or not × mounted at click × still mounted when the timer fires): 8/8 identical. The same harness scored the variant I had written first and reverted — dropping a guard so the callback touched no ref — at **2 of 8 worlds different**, one of them the ordinary case of opening the panel. Reading had said both were fine.

Exempt a row from the *comparison* if you must, then measure it separately. Never exempt it from being measured.

### The predicate that excuses a difference is itself under test

Any harness comparing a narrowed or widened implementation needs a rule for "this input was out of scope anyway". That rule is code you wrote in the same sitting, under the same assumption as the change — and it fails in the one direction that stays silent.

**If the predicate is narrower than the contract it is filtering for, it excuses exactly the differences the change introduced.** The harness then reports zero, and the zero is an artefact of your belief rather than of the code.

Derive the predicate from the new declaration, mechanically. Where it disagrees with what you assumed the field holds, that disagreement is the finding — not noise to filter out before measuring.

### The harness measures what it covers, and reads like it covers everything

This is the trap that costs the most, because the artefact is genuinely impressive.

> A 2,472-comparison harness proved a pure rule equivalent. The PR shipped with **three** equivalence defects, all in the four dispatch arms *around* that rule, which the harness never ran. Review found them one per round. A harness scoped to the easiest piece reads as coverage of the whole change — say explicitly what it did not measure.

## The shapes moving code actually breaks

Every equivalence defect in that PR was the same shape: **work that used to happen before a call now happens inside a callback.** That is the family — relocating an expression changes *when* it runs, and nothing in a suite runs the two orderings. Check each of these by name.

### Evaluation order and throw sites

Moving an expression inside a `setMessages` updater, a promise callback, or a lazily-invoked builder moves *where it throws*. In React that is the difference between an error the turn's `catch` handles and one that breaks the render.

> `(data.content || '').trim()` at the call site threw on a truthy non-string and the turn's catch took it. The same expression inside the updater throws during a render instead — strictly worse. Reproducing the old throw site faithfully would have needed a cast, so the throw was *removed* rather than relocated: narrow with `typeof` before the call. That is a behaviour change, and it was written down as one.

### A fix that relocates code relocates the race

Moving a write out of render and into a lifecycle hook, or out of a callback and into an effect, does not remove the window — it moves it. The new window is invisible for the same reason the old one was: nothing in the suite runs the two orderings.

> A ref written during render was moved into a passive effect to satisfy a purity rule. That closed the "a discarded render leaves a stale value" window and opened a worse one: child effects run **before** the parent's, so any child reading through that ref on a commit where it re-runs saw the previous value. Measured, not reasoned — a probe rendering the same shape recorded `['v1:v1', 'v2:v1']` for the passive write against `['v1:v1', 'v2:v2']` for the render write, and awaiting inside the child did **not** escape it, because the ref is read synchronously before the await suspends. A layout-phase write closed both.

Write the twelve-line probe. Ordering questions have exact answers and they are cheap to obtain; every plausible-sounding argument about them in that session was wrong.

### Call counts and idempotence under re-invocation

React may invoke a state updater more than once — StrictMode double-invokes, a discarded render replays. A builder called *inside* an updater mints a fresh id per invocation.

> The base minted the uuid outside the updater but built the message inside it, so adoption built nothing and every invocation shared one id. A fix that hoisted the whole message out built a message and a `Date` on adoption that the base never built; a fix that left the builder inside minted two ids. Memoising — `candidate ??= build()` — gets both, and a test asserts *one build however many times the updater runs* rather than where the statement sits.

**Which result the framework keeps is not a contract to lean on.** Assert the property that survives every answer: repeated evaluation must not produce a second object.

### Logging you silently drop, and silence you silently create

- Debug logs are behaviour. If the extraction cannot import the logger, **inject it**; do not quietly delete the traces.
- Log calls **evaluate their arguments even when the logger is a no-op**. `dlog('x', data.delta.length)` throws for a missing `delta` in production, where `dlog` compiles to `() => {}`. That is how "just a log line" becomes a crash — and how removing one becomes a behaviour change.
- **Removing a throw can create a silent failure.** If the only remaining signal is a dev-only logger, a production build now drops the input with no trace at all. Reach for `console.warn`.
- **Before claiming the throw was loud, find the `catch`.** In the case above I wrote — in commit messages, two PR bodies, and this file — that the old throw "killed the turn". It did not: the `try` sat *inside* the per-frame loop, so the throw was caught, logged to `console.error`, and the next frame was parsed. The real change was one `console.error` per bad frame becoming none, and one frame's render being skipped or not. A throw's blast radius is decided by where it is caught, and that is three lines to check and easy to assume instead.

## Replacing a direct property access

`x.field`, `out[key] = value`, `arms[type]?.()` — each of these consults or writes through the prototype chain, and any helper, guard, walker or table you write to replace one picks an answer silently. The wrong answer raises nothing, and the example that comes to mind first is usually the one that cannot tell.

### Own property or prototype chain is a decision, and the wrong answer is invisible

`x.field` reads through the prototype. Any reader you write to replace it — a helper, a guard, a path walker — silently picks one or the other, and which is correct depends on **what the value is**:

- **data whose keys came from outside** — a JSON column, a parsed body, a config file — wants **own properties only**. The keys are data, and an inherited name is somebody else's.
- **an object whose class is part of the contract** — a thrown `Error`, an SDK response, anything with accessors — wants the **chain**. An `Error` subclass exposing `message` as a prototype getter is ordinary, and own-only reading loses it.

> A path reader written for a Json column was reused on thrown errors. `class E extends Error { get message() {…} }` then read as *no message at all*, from the function whose job is to turn a thrown error into one line. Six generated error shapes, four differed.

The trap on the way to fixing it: **an `Error` subclass is the case that does NOT regress**, because `Error.prototype.toString()` reads the getter and a `String(err)` fallback recovers it. What actually breaks is a thrown value that is *not* an Error carrying the field on a prototype. A test built from the obvious example passes either way.

### Fixing a prototype hazard in one builder can create one in the next

`out[key] = value` invokes the setter, and `__proto__` has one. Building with `Object.fromEntries` (or `defineProperty`) makes the key data instead. But the moment one builder starts *preserving* such a key, every other builder downstream receives it — and the ones still assigning turn it back into a prototype swap.

> A merge was fixed to keep `__proto__` as data. A redaction pass further along built its result with `redacted[key] = …`, so the key became a prototype replacement again — on the object the public getter hands to its callers. The exposure existed *because* of the earlier fix, and a reviewer's "there is no other unsafe write here" was wrong.

After fixing one, grep the file for every computed-key assignment and every `for…in`, and check what each now receives.

`defineProperty` is not a drop-in for assignment either: with `configurable: true` it **throws on a sealed object** where assignment succeeds. Assign to an existing own writable data property, and define only when creating one.

### A dispatch table on an object literal answers for keys you never wrote

`arms[event.type]?.(event)` on an object literal reaches `Object.prototype` for `constructor`, `__proto__`, `toString`. Use a `Map`, and make it the single source for both the "do I handle this?" predicate and the dispatch, so the two cannot drift.

## Removing code: absence of an input is not a test

Deletion is the refactor whose verification most often does not exist, because the usual move — run the suite, watch it stay green — is exactly what a deletion produces whether it is safe or not.

### A deleted branch cannot be pinned by a test that gives it no input

To prove a removal, put the removed code **back** and watch something fail. If nothing does, the deletion is unverified no matter how green the suite is. And the test that would catch it has to supply the input the deleted branch consumed — which is the input every other test omits, because the surrounding code never produces it.

> Dead branches reading three spellings of a claim off an object were deleted. Restoring them left **5,076 tests green**, including a unit test written for that middleware and an end-to-end test written for that exact property. Both passed a realistic object — one with no claim on it — so the restored branch had nothing to read and fell through to the same answer. Nothing in the suite could tell the two versions apart.
>
> The test that works puts the claim **on the object anyway** and asserts it is ignored. It casts, because the field is deliberately no longer on the type — and that is the point: a value the type denies can still arrive at runtime, and must not count. Break-verified against each spelling separately, each one fails it alone.

The general form: **a removal is verified by an input that only the removed code would have noticed.** Constructing that input usually means stepping outside the types, which feels wrong and is the correct instinct inverted — the types are what you just changed.

### Delete the declaration and let the compiler enumerate the readers

When you believe a declared field, prop or option is unused, do not grep for it and conclude. Remove the declaration and compile. The compiler finds every reader, including the ones that "work" today by silently receiving `undefined`.

> Removing four dead fields from a request-type augmentation surfaced two live defects that had been shipping for months. A feature-flag endpoint read user and org identity from two of them, so **every flag was evaluated with no context at all** — user allowlists never matched, and the percentage rollout hashed the same literal for everyone — while the response reported that empty context back to the caller as though it were the context used. Two audit log lines recorded `undefined` as the actor. The same file used the correct field in seven other places, so nothing looked wrong.

A dead declaration is not merely clutter. It is a type-checked licence for a permanently-undefined read, and it hides exactly the class of bug that has no symptom.

## Putting a type or a schema on a boundary

Replacing an untyped edge — a request body, a stored row, a dependency's response — with a parsed one is still a refactor, and its claim is still "this behaves the same". It fails differently from an extraction, because what changes is *what arrives* rather than where the code sits.

### A parser returns a different kind of nothing

Consumers of an untyped read are written in terms of truthiness: `||` fallbacks, ternaries, early returns on absence. A parser redraws the line between absent and merely falsy, and every one of those branches moves with it. Two directions, both silent:

- **Coercing inside the parser** hands the consumer a value that is no longer falsy — a rendered zero, a formatted empty thing — so it takes the branch the fallback owned. Let the schema declare the **type**; leave the coercion where the consumer already performs it.
- **Nullish and falsy are not the same test.** Swapping in `??` where the original used truthiness keeps the empty string, the zero, the `false` the original discarded.

Expect this at *every* site the parser feeds, not at one. It is the most repeatable defect of this kind of change, and each instance looks locally correct.

### One unreadable element must not discard the collection

The instinct when typing a list is to declare the element type and let the parse fail. That turns one malformed entry into an empty collection — and empty is usually rendered, counted or iterated as *nothing here*, where the untyped code carried on with everything else.

**A validation layer stricter than the code it replaces is a regression wearing the costume of a hardening.** Drop the element, keep the rest, and ask what the caller does with a shorter collection versus an absent one — those are different answers, and only one is what you meant.

### Declarations describe the contract; shipped code describes the behaviour

A cast over a dependency's type is where dead code hides. The branches beneath it were usually written to defend against a shape that dependency never produces — and its type definitions cannot tell you so, because they describe what is *permitted*, not what is *emitted*.

When you remove a cast, read the dependency's compiled source for the value in question, and treat what it constructs as the fact.

### A storage layer can give one language-level value several meanings

Absent, explicitly null, and *the encoding of* null can be distinct states in a store, mapped from a single `null` in the language. Which one the old code was writing is not visible in the old code.

Write each candidate to a scratch store and read the column back. Reasoning produces a confident answer here, and a reviewer will reason to the opposite one with equal confidence; an artefact ends that in a way no explanation does.

## Caching, and the boundary you are enforcing

Adding a cache is a "same behaviour, less work" claim, which puts it squarely in this file. It fails in a way extraction does not: the value goes stale, and staleness of *some* values is a correctness bug rather than a delay.

**Before memoising, ask whether the cached value IS the rule.** A cache over an input is a performance decision. A cache over the thing being enforced converts the enforcement into "enforced as of some time ago", which for a boundary is another word for not enforced.

> A membership lookup was memoised for five minutes so a delivery path would not query per event. Membership was the boundary the whole change existed to enforce — so for five minutes after someone moved between groups, their new work kept arriving at the group they had left. The exact leak the change prevented, arriving through the change. Removing the positive cache cost nothing measurable, because the query only ran when a decision actually turned on it.

Two follow-ons worth stating, both learned the same day:

- **Cache the failures.** A lookup that throws and is not cached is re-attempted per call, so an outage becomes a query storm on a path nothing awaits. A cached failure also fails in the safe direction if your rule denies on "unknown".
- **Ask what the caller needs before caching for it.** Restricting *when* the expensive call happens — only when a decision depends on it — is often the whole optimisation, and it has no staleness at all.

## Tests you write during a refactor

**Break-verify every one.** Mutate what it covers and watch it go red. A test that cannot fail is documentation with a green tick. All of the following were observed.

### It cannot discriminate — it passes with the change reverted

- **It passes for a different reason than you think.** "Drops a delta that arrives before any start" asserted the list was unchanged — which holds with the guard deleted, because the id lookup refuses `null` anyway. Assert what the guard actually protects.
- **It asserts text, not behaviour.** An AST or source assertion that the writer "mentions `openThinkingIndex`" survives the branch being disabled with `if (false &&`. Delete it and say why, rather than leave it reading as coverage.
- **The fake filters on the very criterion under test.** A stub that selects using the same condition the change introduces returns nothing when the *old* code omits it — so the test written to catch the old behaviour passes, for the exact opposite of its reason. A fake must behave like the real dependency, applying whatever the caller actually passed; not like your expectation of the call.
- **The fixture is too simple to discriminate.** A collection holding one element cannot tell a search apart from an index, so a mutation between them stays green. Build fixtures from the shape production sends — the multiplicity, the ordering, the neighbours — rather than the minimum the assertion needs.
- **The fixture you build with a literal may not contain what you think.** `{ __proto__: x }` in an object literal *sets the prototype*; it does not create a key. A fixture built that way to test `__proto__` handling contains no `__proto__` at all, and the test cannot fail. Build it from a string — `JSON.parse('{"__proto__":…}')` — and assert the fixture has the shape before asserting what the code does with it. This is the same trap the change is fixing, appearing inside the test written to prove the fix.
- **An empty result cannot tell "handled" from "never happened".** A test that stubs a dependency to fail and then asserts the output is empty passes just as well when the call is removed entirely — because *not calling* produces the same empty. Assert that the call **happened**, with the arguments it should have had. In one file, mutating the dependency call away left two of three failure tests green; asserting the call fixed all three. The same file had **nothing** asserting the request itself, so pointing a query at entirely the wrong collection passed all fifteen cases.
- **A negative assertion passes on absence.** "Does not carry this field" holds when the object is missing, when it is empty, and when the field was merely renamed. Assert the **whole permitted set** instead: it catches the rename and the unexpected addition as well, and it fails closed on the form nobody predicted.
- **The route you exercise must be the route that runs the code.** Reaching for an end-to-end test to cover a middleware change only works if the response actually reflects the middleware's output. If it does not, the test passes with the change reverted — which is the check, and it takes one mutation to run.

### It discriminates, but it pins the wrong thing

- **It pins a bug as correct.** State the property, then confirm the implementation agrees, then check the property is the one you want. A test asserting the current order of two messages is fine — as long as the comment says whether that order is *right*, not just *current*.
- **Its comment describes history that never happened.** "Preserved from the code this replaced" — the code it replaced *threw* at that point. The comment is what the next reader believes.
- **Its name claims a property its assertions never reach.** A test called "does not take an organisation from a token claim" asserted a database row, through a route that does not run the middleware in question. It was green, it was truthful about the row, and it proved nothing about the claim. The name is what the next person believes it covers — and a name that outruns the assertion is worse than no test, because it closes the question. Two successive rewrites of that one test both did it; write down what the test does **not** establish, and where that property is pinned instead.

**Search for existing coverage before adding some.** A weaker duplicate of a check that already exists is worse than nothing, because it reads as coverage.

**Ask whether the property is one you want before pinning it.** The characteristic mistake of a long refactoring session is writing tests that *describe* what you have just built rather than interrogate it. They pass immediately, they read as careful coverage, and they make the defect permanent — the more thorough they look, the longer it survives. Before asserting a behaviour, say plainly whether it is better or worse than the one it replaced.

## The mutation sweep is the thing that checks all of the above, and it fails too

Break-verifying a harness or a suite means editing the tree, running, and restoring, dozens of times. Both halves go wrong silently, and a sweep that never really ran is indistinguishable from a sweep that found nothing.

**Counting:**

- **The mutation did not apply.** A patch that silently failed produces a green run indistinguishable from a coverage gap. Assert the marker landed, use absolute paths, and `cmp` the file back to its backup between cases.
- **The sweep counted redness wrong.** Distinct from the above, and it looks identical: the patches applied, the tests failed, and the script reported **0 red for all six mutations** because it scraped the runner's summary line with `grep -oE '[0-9]+ failed'` and got nothing back. Six real gaps that were not gaps. Count by **exit code** — `run() { npx vitest run … >/tmp/out 2>&1; echo $?; }` — and print the baseline (`0`) and the restored final (`0`) around the sweep, so a run that never executed cannot pass for a run that found nothing. Recounted that way: 4, 8, 2, 2, 2, 2.

**Restoring** — the destructive half, and the one that takes your own work with it:

- **Commit before you mutate — every time, no exceptions.** The restore step does not distinguish your mutation from your uncommitted work. Twice in one session a restore rolled a file back to the last commit and took real fixes with it; both times the work had been written minutes earlier and was not yet committed. The checkpoint costs one command and is the only thing that makes the restore safe.
- **`git checkout <ref> -- file` can fail** and leave you measuring the wrong version. That produced two invalid measurements in one session. Prefer index-free file copies for temporary swaps, and verify the swap landed (`grep` for something only that version has).
- **`git checkout -- file` as the undo step fails destructively.** It shares `index.lock` with every sibling clone on the machine, and a `git status` from another one is enough to break it. Mid-sweep it left a live mutation — `aria-label={title}` — in the tree, and only an explicit `diff -q` against a saved copy caught it; without that, later cases score against an accumulating mutation and read as *more* coverage. Save a pristine copy first, restore with `cp`, and assert `diff -q` after **every** case rather than at the end.
- **A restore run from the wrong directory reports success and does nothing.** `git checkout -- backend/src/x.ts` issued from inside `backend/` cannot resolve that path — it errors — and a `git diff --quiet` in the same directory then answers about a path that does not exist, so the sweep prints `restored`. Five false "restored" reports in one session, each caught only by re-checking. Use `git -C <repo-root>` for both the restore **and** the verification, and never let a `cd` earlier in the same command decide where they run.
- **A copy you made for comparison is not restored by restoring the original.** A sweep that rebuilds the "new" side per case but never resets it leaves the last mutation in that copy. The next baseline run then reports differences that are not in the code — 60 of them, in a comparison I had just measured at 0. Regenerate every derived file, or assert it matches its source.

## Claims that nothing executes: comments, plans, premises

Prose in the repository is unchecked by construction. During a refactor you are reading it anyway, which makes it the cheapest bug detector available — and the easiest thing to leave pointing the wrong way.

### A comment that disagrees with the code is a finding

Not stale prose to tidy while you are in there. Someone wrote it because it was true, or because they believed it — and the gap between it and the code is where the defect is.

Three in one session, each sitting on something real:

> *"Get recent events (for debugging, admin only)"* on a route with no admin check — it returned the whole event ring, payloads intact, to any authenticated caller.
>
> *"The only reader is `authToken` below"* on a ref — `authToken` was passed as a prop to three children, whose effects called it before the parent's ran.
>
> *"Stop button uses the same global hook the fast-mode runtime uses, since only one of the two is mounted at a time"* — three lines above a call site whose own comment said all runtimes are always mounted.

Two of those comments were written **by me, in the change under review**, and both were describing an intention rather than the code. When you write one, check it against the code as carefully as you would check someone else's — a comment you author is the one a future reader trusts most and the one nothing tests.

### Do not let a plan or a design note become the stale one

A design document committed with the change is read as the specification. If the change grew past it — and a reviewed change usually does — the document now instructs the next person to undo what review taught you.

> A plan file called for a memoised lookup. Review established that memoising that particular value was the defect. The plan shipped unchanged in the same branch, so the repository contained a spec telling its next reader to reintroduce the cache.

Re-read it after the review, not before.

### Verify the premise, not just the conclusion

A finding is *claim + reason*, and they fail independently. Whatever you accept as a premise becomes the justification a future reader inherits.

> "Commit X broke streamed thinking" — the symptom was real, the cause was not. The branches X deleted matched a flat event shape the SDK never sends; they were already dead, and X's own message said so. Filing it as a regression would have sent someone to revert a commit that removed dead code.

Trace the reason into the source, link by link, before writing it into a commit message or an issue. This applies hardest to findings you *agree* with.

**A conclusion can be right while its example is not**, and which one you believe decides what you test. A reviewer was correct that an own-property read was wrong, and gave an example that does not actually regress. Building the test from the example produced a test that passed with the fix reverted; building it from the shape that *does* regress produced one that fails. Same finding, opposite outcomes.

**Check the negative claims too.** "There is no other instance of this", "nothing else touches that path", "this is unreachable" — these carry the same authority as the positive findings and get read straight into a decision to stop looking. One "there is no fourth unsafe write here" was wrong, and the fourth existed *because* of a fix earlier in the same change. A negative claim costs one grep to confirm and is the cheapest place a review goes quietly wrong.

**Two reviewers agreeing is not two checks** when both reached the answer the same way. "Equivalent for every input" survived both of us reading it; generating twenty-two shapes found one where it is not. Agreement between readings is one reading with two signatures — the second check has to be of a different kind.

## When the evidence itself is wrong

### The tooling does not tell you when it failed

- **`git add` can fail silently.** An `index.lock` collision with another process, an error swallowed by `2>/dev/null`, and only the test file gets committed — pushing a test for an implementation that is not there. `git status` showed `M ` and ` M` side by side and it still got pushed. **Check what is staged before committing, and what the commit contains before pushing.**
- **Piping hides exit codes.** `tsc --noEmit | grep -c error` reports 0 for a clean run *and* a broken one. Check `$?`.
- **A stale `node_modules` lies about your own tooling.** A lint rule "did not exist" — the installed plugin was three majors behind the lockfile. Re-install before concluding a rule is unavailable.
- **CI may not run what you assume.** Check the job list. A build step that no job runs is a step nothing checks.
- **Timing is not evidence.** A before/after pair of a noisy measurement is one sample. `5.6s → 886ms` looked like proof that a stub removed a network call, until the *unstubbed* file ran in 1.02s. Justify the change by what it does — the call happens or it does not — never by the clock.
- **A slow tool is not a broken tool.** A reviewer process that produced one line in 45 minutes was diagnosed as "the prompt never reached it, it is waiting on stdin" — that line turned out to be its normal first output, present in every successful run too. The actual cause was a load average of 36 from other work on the machine. Before declaring a tool broken from its output, check the same output in a run that worked.

### What a green suite does not prove

A passing suite proves the code you thought about still behaves. It does not prove the app boots, the route is still wired, the middleware still runs in the order the framework needs, or that the request the real client sends still arrives in the shape the handler expects. For a change that touches something EVERY request or EVERY caller passes through — a route entry point, a middleware, a handler signature, a shared function with many call sites — **start the stack and drive the real path**.

- **Drive the actual endpoint or screen**, not a unit test standing in for it. A route registration that no longer matches its handler's signature type-checks and ships.
- **Exercise both directions**: the happy path AND the rejection the change affects. A validation change that only ever sees valid input is half-tested.
- **Vary what the change assumes.** One request of one shape tests a single point.
- **Name what you could NOT exercise locally, and why** — an interactive login, a route gated off by an env flag, a path that needs a deploy. Silence reads as "the run covered everything".

**Something already answering on the port may not be what you started.** Where several checkouts of one repository run side by side, a service that responds is not evidence that *yours* responds — you can drive another copy end to end and report it as verification of your change. A start script that derives its repo root from its own location starts the WRONG checkout, and a service already listening makes "already up" look like success. Bring up your own instance on its own port and its own store, and confirm the running process's working directory before believing anything it tells you.

**You verified your branch; what merges is a different artefact.** CI runs against the branch. Commits landing on the mainline between your last sync and the merge produce a combination nobody has executed. Update locally after merging and run the gate again on the result.

## The record you leave

- **Say what you did not measure.** Every count you publish invites the reader to assume the rest was covered too.
- **Attribute honestly.** If a round's finding was a defect in your own earlier fix, say so — it tells the human which commits to read hardest.
- **A plan that describes work not done is worse than one admitting the gap**, because the plan is what a reader checks the change against. And a correction can overcorrect: check the new sentence against the code as carefully as the old one.
