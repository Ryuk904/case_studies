# EP02 — Cloudflare, 2 July 2019

## Core hook & stake

On 2 July 2019 an engineer on Cloudflare's firewall team deployed a routine update to the
WAF Managed Rules — a change to the rules that detect cross-site scripting. One of the new
rules contained a regular expression, 132 characters long, whose critical fragment reduces
to `.*.*=.*`. That fragment asks the matching engine to try every way of splitting a string
in two, so the work it does grows super-linearly with the length of the input. Deployed
through Quicksilver, Cloudflare's key-value store, it reached every machine on the network
in seconds. CPU pinned to nearly 100% on every core serving HTTP/HTTPS worldwide, customers
got 502s, and Cloudflare lost about 80% of its traffic. The service was down for 27 minutes.
The rule had been pushed in "simulate" mode — it was not blocking anything. It still had to
run.

## Why this episode works

It rhymes with EP01 without repeating it. Knight was code nobody deleted; Cloudflare was
code everybody approved. Cloudflare's own sentence is the thesis of the episode: *"Everything
that occurred up to the point the rules were deployed was done 'correctly'."*

Four twists most retellings miss:

1. **The guard had been removed weeks earlier** — by a refactor whose purpose was to make
   the WAF use *less* CPU (¶"What went wrong", item 2).
2. **The rule was never switched on.** Simulate mode: real traffic passes through, nothing
   is blocked. The rule still executes.
3. **They were locked out of their own building.** Access was down, so the team could not
   authenticate to the internal control panel; some SREs' credentials had already timed out
   for security reasons; Jira and the build system were unreachable.
4. **The fix was fast because the deploy was fast.** 13:42 out, 14:07 killed, 14:09 recovered.
   Quicksilver's p99 of 2.29s to every machine on earth is the *feature*, and it is also the
   reason one bad line reached every machine on earth.

## Titles

1. **Search-optimised:** How One Line of Code Took Down 20% of the Internet for 27 Minutes
2. **Curiosity / CTR:** They Wrote One Line of Text. It Broke the Internet for 27 Minutes.
3. **Punchy (<50 chars):** 132 Characters

See `seo.md` for the shipping title and why.

## Thumbnail

- **Text overlay:** `132 CHARACTERS` / `27 MINUTES`
- **Visual subject:** one line of text glowing on a near-black field, the frame around it
  buckling. See `thumbnail_prompt.md`.

---

## PRIMARY SOURCE

**John Graham-Cumming, "Details of the Cloudflare outage on July 2, 2019",** The Cloudflare
Blog, 12 July 2019. Fetched in full and read end to end.
https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/

Graham-Cumming was Cloudflare's CTO and is named in the post as the person who wrote the Lua
WAF this outage happened inside. It is a company postmortem written by the author of the
failing component, which is as close to first-hand as an incident source gets.

**Secondary primary source for scale only:** Cloudflare, Inc. **Form S-1**, filed with the
SEC on 15 August 2019 — the company's own registration statement, six weeks after the outage.
https://www.sec.gov/Archives/edgar/data/1477333/000119312519222176/d735023ds1.htm

## SOURCES — the contract

Every number spoken in `script.md` has a row here with the verbatim sentence containing it.

| Claim | Source | Verbatim |
|---|---|---|
| **The outage lasted 27 minutes** | CF postmortem | "the real story of how the Cloudflare service went down for 27 minutes is much more complex than 'a regular expression went bad'" |
| **They lost 80% of their traffic** | CF postmortem | "a leader in our Solutions Engineering group told me we had lost 80% of our traffic" |
| CPU pinned across the whole network | CF postmortem | "we deployed a new rule in our WAF Managed Rules that caused CPUs to become exhausted on every CPU core that handles HTTP/HTTPS traffic on the Cloudflare network worldwide" |
| CPU spiked to nearly 100% | CF postmortem | "The following graph shows CPUs dedicated to serving HTTP/HTTPS traffic spiking to nearly 100% usage across the servers in our network." |
| Customers saw a 502 | CF postmortem | "This resulted in our customers (and their customers) seeing a 502 error page when visiting any Cloudflare domain." |
| **The regular expression** | CF postmortem | "The regular expression that was at the heart of the outage is …" — the expression itself is transcribed verbatim into **`regex.txt`** beside this file, which is what the episode renders. It is kept there rather than inline because it is dense in pipe characters and a markdown table is the worst possible place to store a string whose correctness matters. |
| The part that mattered | CF postmortem | "The critical part is `.*(?:.*=.*)`." … "we can safely ignore it and treat the pattern as `.*.*=.*`" |
| **23 steps to match `x=x`** | CF postmortem | "It takes 23 steps for this match to happen." |
| Growth is not linear | CF postmortem | "what happens if the string is changed from x=x to x=xx ? This time is takes 33 steps to match. And if the input is x=xxx it takes 45. That's not linear." |
| **555 steps for 20 characters** | CF postmortem | "With 20 x 's after the = the engine takes 555 steps to match!" |
| **4,067 steps when it does not match** | CF postmortem | "if the x= was missing, so the string was just 20 x 's, the engine would take 4,067 steps to find the pattern doesn't match" |
| Worse with a semicolon: 5,353 steps | CF postmortem | "Matching x= followed by 20 x 's takes 5,353 steps." |
| The change was for XSS detection | CF postmortem | "At 13:42 an engineer working on the firewall team deployed a minor change to the rules for XSS detection via an automatic process." |
| **13:31 merged, 13:37 tests green, 13:42 deployed** | CF postmortem | "At 13:31 an engineer on the team had merged a Pull Request containing the change after it was approved." / "At 13:37 TeamCity built the rules and ran the tests, giving it the green light." / "With the tests passing, TeamCity automatically began deploying the change at 13:42." |
| First page 3 minutes later | CF postmortem | "Three minutes later the first PagerDuty page went out indicating a fault with the WAF." |
| **14:00 WAF identified, 14:02 kill switch proposed** | CF postmortem | "At 14:00 the WAF was identified as the component causing the problem and an attack dismissed as a possibility." / "At 14:02 the entire team looked at me when it was proposed that we use a 'global terminate'" |
| **14:07 killed, 14:09 recovered** | CF postmortem | "Eventually, a team member executed the global WAF termination at 14:07 and by 14:09 traffic levels and CPU were back to expected levels worldwide." |
| 14:52 WAF back on | CF postmortem | "At 14:52 we were 100% satisfied that we understood the cause and had a fix in place and the WAF was re-enabled globally." |
| **The rule was in simulate mode** | CF postmortem | "This particular change was to be deployed in 'simulate' mode where real customer traffic passes through the rule but nothing is blocked." |
| Simulate mode still executes | CF postmortem | "But even in the simulate mode the rules actually need to execute and in this case the rule contained a regular expression that consumed excessive CPU." |
| **476 change requests in 60 days, one every 3 hours** | CF postmortem | "In the last 60 days, 476 change requests have been handled for the WAF Managed Rules (averaging one every 3 hours)." |
| WAF deliberately skips the staged rollout | CF postmortem | "But, by design, the WAF doesn't use this process because of the need to respond rapidly to threats." |
| The staged rollout it skipped | CF postmortem | "deployment to what we call the 'animal PoPs' occurs: DOG, PIG, and the Canaries" |
| **Quicksilver spans more than 180 cities** | CF postmortem | "we ran into operational issues with it and wrote our own KV store that is replicated across our more than 180 cities" |
| **p99 of 2.29 seconds to every machine worldwide** | CF postmortem | "On average, we hit a p99 of 2.29s for a change to be distributed to every machine worldwide." |
| Quicksilver moves ~350 changes a second | CF postmortem | "On average Quicksilver distributes about 350 changes per second." |
| **The engine had no protection against a runaway** | CF postmortem | "The Lua WAF uses PCRE internally, and it uses backtracking for matching and has no mechanism to protect against a runaway expression." |
| **Everything was done correctly** | CF postmortem | "Everything that occurred up to the point the rules were deployed was done 'correctly': a pull request was raised, it was approved, CI/CD built the code and tested it, a change request was submitted with an SOP detailing rollout and rollback, and the rollout was executed." |
| **The guard was removed by a refactor to save CPU** | CF postmortem | "A protection that would have helped prevent excessive CPU use by a regular expression was removed by mistake during a refactoring of the WAF weeks prior—a refactoring that was part of making the WAF use less CPU." |
| The tests could not see it | CF postmortem | "What it didn't do was test for runaway CPU utilization by the WAF and examining the log files from previous WAF builds shows that no increase in test suite run time was observed with the rule that would ultimately cause CPU exhaustion on our edge." |
| The test suite gap, listed as a cause | CF postmortem | "The test suite didn't have a way of identifying excessive CPU consumption." |
| **They were locked out of their own systems** | CF postmortem | "We use our own products and with our Access service down we couldn't authenticate to our internal control panel (and once we were back we'd discover that some members of the team had lost access because of a security feature that disables their credentials if they don't use the internal control panel frequently)." |
| …and out of Jira and the build system | CF postmortem | "And we couldn't get to other internal services like Jira or the build system. To get to them, we had to use a bypass mechanism that wasn't frequently used" |
| Customers locked out too | CF postmortem | "Our customers were unable to access the Cloudflare Dashboard or API because they pass through the Cloudflare edge." |
| **3,868 rules re-inspected by hand** | CF postmortem | "Manually inspecting all 3,868 rules in the WAF Managed Rules to find and correct any other instances of possible excessive backtracking. (Inspection complete)" |
| The guard was put back | CF postmortem | "Re-introduce the excessive CPU usage protection that got removed. (Done)" |
| They planned to change engine | CF postmortem | "Switching to either the re2 or Rust regex engine which both have run-time guarantees. (ETA: July 31)" |
| First global outage in six years | CF postmortem | "It was even more upsetting because we haven't had a global outage for six years." |
| **The linear-time solution has existed since 1968** | CF postmortem | "The solution to this problem has been known since 1968 when Ken Thompson wrote a paper titled 'Programming Techniques: Regular expression search algorithm'." |
| **More than 20 million websites and apps** | Cloudflare S-1 | "The over 20 million Internet properties (e.g., domains, websites, application programming interface (API), and mobile applications) on our network…" |
| Network reach | Cloudflare S-1 | "Today, our network spans 193 cities in over 90 countries and interconnects with over 8,000 networks globally" |
| 44 billion threats blocked a day | Cloudflare S-1 | "We leverage these insights to block cyber threats every day, which in the three months ended June 30, 2019 averaged approximately 44 billion per day." |

### Derived, not quoted — and flagged as such

- **"132 characters"** is a character count of the verbatim regular expression above, done in
  Python (`len()` of the exact string). It is arithmetic on a primary source, not an estimate,
  but it is not a number Cloudflare printed. If it is ever wrong, it is wrong because the
  string was transcribed wrong — the string is in this ledger so it can be re-checked.
Every other spoken interval is likewise subtraction on the quoted timestamps, and none of
them is stated as a duration in the post. Listed here so they can be re-checked:

| Spoken as | Arithmetic |
|---|---|
| "six minutes later the automated tests run" | 13:31 merged → 13:37 tests green |
| "five minutes after that, the system sends it out" | 13:37 → 13:42 deployed |
| "three minutes after the change goes out, the first alarm fires" | stated in the post: "Three minutes later the first PagerDuty page went out" |
| "about fifteen minutes to prove that nobody is" | 13:45 first page → 14:00 attack dismissed |
| "and then five minutes go by" | 14:02 kill switch proposed → 14:07 executed |
| "two minutes later the traffic is back" | 14:07 → 14:09 |
| "twenty-seven minutes" | 13:42 → 14:09, and stated outright as "27 minutes" |

---

## ⚠ Contradiction inside the primary source — do not use either figure

The appendix gives **two different step counts for `x=x` against `.*.*=.*;`** (the version with
a trailing semicolon):

> "This time the backtracking would have been catastrophic. To match x=x takes **90** steps
> instead of 23."

…and eight paragraphs later:

> "Changing the catastrophic example .\*.\*=.\*; to .\*?.\*?=.\*?; doesn't change its run time at
> all. x=x still takes **555** steps"

555 is also the figure given for a *20-character* input against the non-semicolon pattern, so
the second mention looks like a copy-paste slip. **Neither number is spoken in the episode.**
The semicolon variant is cut entirely — the episode uses only the uncontested chain
23 → 33 → 45 → 555 → 4,067.

## ⚠ Unverified — do not use

- **"Cloudflare handles X% of all web traffic."** Widely quoted, not in either primary source.
  The S-1's "over 20 million Internet properties" is the defensible scale figure and it is
  what the script uses.
- **Any dollar figure for the outage.** Cloudflare never published one and no filing quantifies
  it. There is no cost number in this episode, deliberately — EP01 had one and EP02 does not,
  and inventing one to match would be the single easiest way to break the channel's contract.
- **The engineer's name.** Not published, and naming a person for a system failure is against
  HOUSE_STYLE §1 regardless.
- **"The regex was written by an intern / junior."** Not in the source. The post says only
  "an engineer working on the firewall team", and the whole thesis is that the process
  approved it.
