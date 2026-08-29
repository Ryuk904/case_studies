# EP04 — GitHub, 21 October 2018 — verbatim voice script

Written for someone who does not know what a database primary or a failover is, and never
uses either phrase. Every number spoken has a row in research.md SOURCES.

The episode's one picture: two offices keep the same ledger, and only one is allowed to
hold the pen. For 43 seconds they cannot hear each other, and the second office, following
its emergency rulebook to the letter, picks up its own pen. When the phones come back,
both books hold entries the other has never seen.

Two open loops, planted early and paid off late:

1. **The guard's sharp edge.** The foreshadow quote lands in context ("remember that
   sentence"); the payoff is the takeaway's verdict quote — it behaved as configured.
2. **The anti-GitLab twist.** EP03 was five backups, none working. Planted in context
   ("because you watched the last episode, yes, the backups"); paid off mid-breakdown:
   every backup worked, tested daily, and the day still cost 24 hours — physics, not
   negligence.

Visual policy: the `coasts` stage (two depicted buildings, one cable, one pen badge)
recurs as the episode's spine; `ledgers` carries the split-brain picture; the failover
sequence (22:52–23:13) opts into the dark ambient bed. Renderer-emitted cues (`cue="on"`)
land the snap, the pen flight and the choice's cross at their true schedule-time moments.

---

## SECTION: hook

[VISUAL: coasts pen="left" crew="left" title="10:52 pm, Sunday, 21 October 2018" caption="routine maintenance, on a quiet network" cut="hard"]
It is 10:52 on a Sunday night, the 21st of October, 2018.

[VISUAL: coasts pen="left" snap="1.2" dead="left" cue="on" title="43 seconds" caption="one cable, gone dark" cut="hard"]
For 43 seconds, GitHub's main data centre, on America's East Coast, drops off the rest of its network.
[PAUSE:0.6]
43 seconds is nothing to a human, and an eternity to a machine.

[VISUAL: coasts pen="left" pen_to="right" pen_at="1.4" snap="0" heal="4.6" dead="left" cue="on" title="the emergency system reacts" caption="the master copy moves west"]
GitHub's automatic emergency system decides the East Coast is dead, and hands the master copy of GitHub's database to the West Coast.
Then the link comes back.
[PAUSE:0.6]

[VISUAL: ledgers left_n="5" right_n="18" left_until="0.5" tear="on" left_label="the East Coast copy" right_label="the West Coast copy" title="now there are two"]
Now there are two master copies.
Each is collecting changes the other has never seen.
There is no honest way to merge them.

[VISUAL: metric_card value="24h 11m" sub="to put one database back together" label="GITHUB.COM" field="on" count="off"]
Untangling it takes GitHub 24 hours and 11 minutes.

## SECTION: context

[VISUAL: title_card text="what GitHub keeps" motif="people:3" layout="left" sub="the world's code, and the record of making it" cut="soft"]
Start with what GitHub is.
It is the place where software teams all over the world keep their code and build it together.

[VISUAL: diagram nodes="[the code] --(lives in)--> [its own storage]; [everything else] --(lives in)--> [one set of databases]" title="two kinds of storage"]
The code itself lives in its own separate storage.
Everything else lives in databases.
Every discussion, every task, every account, every record of who changed what.

[VISUAL: servers n="6" bad="" title="not one database, many" label="split by job, some of them nearly five terabytes"]
Not one database, but many, split by job, some of them nearly five terabytes each.
Each has up to dozens of reading copies, so the crowd reading never slows down the one writer.

[VISUAL: coasts pen="left" title="two coasts, one pen" caption="one site takes the changes, everyone else reads along"]
Those databases run on America's East Coast, in GitHub's main data centre.
And there is a rule, the same rule banks and libraries have used forever.
However many copies of the record exist, only one of them is allowed to take new entries.
Call it holding the pen.
The East Coast holds the pen, and copies of everything stream out to a second site on the West Coast, and to machines in the cloud.

[VISUAL: stick pose="look" n="1" title="the night guard" caption="watching every copy, all day, every day"]
Now, who decides where the pen is.
Not a person.
GitHub runs a program called Orchestrator, a night guard that never sleeps, watching every database and its copies.
It runs on an election, a vote among machines on both coasts, so no single failure can confuse it.
If the building holding the pen ever burns down, Orchestrator hands the pen to a healthy copy, in seconds, without waking anyone up.

[VISUAL: quote text="It's possible for Orchestrator to implement topologies that applications are unable to support." source="GitHub's own post-incident analysis" motif="alarm"]
GitHub's engineers knew this guard had one sharp edge, and wrote it down.
The guard is allowed to build arrangements the rest of the system cannot actually live with.
Remember that sentence.

[VISUAL: vault every="1.5" stamps="00:00|04:00|08:00|12:00|16:00|20:00|and again|and again|every day" title="and yes, the backups" caption="a full copy every four hours, and a restore rehearsed daily"]
And because you watched the last episode, yes, the backups.
GitHub takes a full backup every four hours, keeps them for years, and rehearses restoring them at least once every single day.
Hold on to all of that.
It is Sunday night.

## SECTION: breakdown

[VISUAL: coasts pen="left" crew="left" title="10:52 pm, the maintenance" caption="a failing optical part, swapped on a Sunday night" cut="soft"]
The maintenance that night is genuinely routine.
A piece of optical network equipment on the East Coast is failing, and it is being replaced.

[VISUAL: coasts pen="left" snap="1.8" dead="left" cue="on" mood="dark" title="22:52" caption="the main site, cut off from its own network" cut="hard"]
At 22:52, universal time, the swap cuts the line between GitHub's network hub and the main data centre behind it.
The building is fine.
The database is fine.
But for 43 seconds, nothing outside can hear them.

[VISUAL: stick pose="look" n="3" title="the guards hold their vote" caption="the machines that can still hear each other decide" mood="dark"]
Orchestrator watches from both coasts, and from the cloud.
The guards who can still hear each other hold their vote.
The East Coast is silent, so the vote carries.
The main site is dead.
Hand the pen west.

[VISUAL: code body="promote <west coast copy>" prompt="on" syntax="on" hot="<west coast copy>" lang="an illustration, not GitHub's real console" caption="the decision, taken in seconds, by software" mood="dark"]
So that is what happens.
Across the West Coast, copy after copy is promoted to pen holder.
No human typed anything.
No human had even seen the first alert yet.

[VISUAL: coasts pen="right" snap="0" heal="1.6" cue="on" title="43 seconds later" caption="the cable heals, and the west now holds the pen"]
Then the 43 seconds end, and the cable comes back, as if nothing happened.
GitHub's applications immediately start sending every new change west, to the new pen holder.

[VISUAL: ledgers left_n="5" right_n="16" left_until="0.4" tear="on" left_label="stranded on the east" right_label="growing in the west" title="the trap, already sprung" mood="dark"]
And the trap is already sprung.
In its last few seconds as pen holder, the East Coast took writes that never made it into the westbound stream.
They exist in one building, on one coast, and nowhere else.
On one of their busiest clusters, that is 954 entries.
Real people's work, sitting in a copy that is no longer allowed to grow.

[VISUAL: nightdesk wake="2.6" title="22:54, the pagers" caption="two minutes after it was already over" mood="dark"]
[SFX: ping]
At 22:54, GitHub's monitoring wakes the humans.
Alerts are firing everywhere, and engineers start triaging.
Understand what the 43 seconds mean here.
By the time the first human even reads the first alert, the failover is history.

[VISUAL: stick pose="type" n="1" prop="desk" title="23:02, the map looks wrong" caption="the topology shows a west-only world"]
By 23:02, the first responders can see that many database clusters are in a shape nobody recognises.
They query the guard, and the answer comes back showing only West Coast servers.
At 23:07 they freeze all deployments.
By 23:13, the site status is red, and the database team is paged.

[VISUAL: fork blocked="left" left_label="hand the pen back east" right_label="keep the pen in the west" title="the choice" caption="one road would delete somebody's work"]
Now comes the decision the whole day turns on.
Option one, hand the pen straight back east, the arrangement everything was built for.
But the west has been writing for nearly 40 minutes, and the east is missing all of it.
Sending the pen back means throwing the west's entries away.
So option two, keep the pen in the west, and accept what that costs.

[VISUAL: quote text="Our strategy was to prioritize data integrity over site usability and time to recovery." source="GitHub's post-incident analysis" motif="lock"]
Their own analysis says it in one line.
Data first, speed second.
Nobody's work gets deleted to make the site come back sooner.

[VISUAL: crossing secs_per="2.4" from="the application, East Coast" to="the pen, West Coast" counter="round trips, just while you watched" title="what keeping the pen west costs"]
Most of GitHub's machinery still lives on the East Coast, and now every write it makes has to cross the continent and come back.
Pages crawl.
So GitHub deliberately switches off more of itself, pausing notifications and website publishing, rather than risk the data it has already accepted.

[VISUAL: clock fraction="0.8" label="terabytes, crawling out of deep storage" title="just past midnight, the rebuild begins"]
Just past midnight, the plan is set.
Rebuild the East Coast databases from backups, let them catch up, then hand the pen home.

[VISUAL: title_card text="every single backup works" motif="calendar:00:00|04:00|08:00|12:00" layout="left" sub="tested daily, exactly as designed" cut="soft"]
And here is the twist this channel earned last episode.
Every single backup works.
Tested daily, exactly as designed.

[VISUAL: haul n="3" crate="terabytes" speed="58" title="the problem is physics" caption="the backups were fine. the distance was not."]
The problem is physics.
The backups are multiple terabytes, they live in remote cloud storage, and hauling them out takes hours.

[VISUAL: title_card text="the estimate said two hours" motif="loop" layout="right" sub="recovery had other plans"]
Deep in the night, some databases are rebuilt and catching up.
GitHub tells the world recovery is about two hours away.

[VISUAL: clockwall title="11:12, the pen is home, and the site is lying" caption="every reading copy answers with a different hour"]
At 11:12 the pen does go home to the East Coast, and the site speeds up.
But dozens of reading copies are still hours behind.
Ask GitHub a question, and you might get this morning's truth, or last night's.
The site is up, and it is showing people the past.

[VISUAL: sunrise n="16" over="9" title="the morning rush arrives" caption="Europe wakes up, then America" mood="dark"]
And the two hour estimate assumed the copies catch up at a steady pace.
They do not, because it is now Monday morning.
Europe wakes up and starts pushing code, and the American coasts follow.
By early afternoon the delays are growing, not shrinking.

[VISUAL: clockwall state="caught" title="the fix that finally worked" caption="more reading copies, less load on each, and the answers agree again"]
The fix that works is almost boring.
GitHub provisions a crowd of fresh reading copies, and spreads the questions across them.
Relieved, the exhausted copies finally catch up, and at 16:24 the original arrangement is restored.

[VISUAL: metric_card value="5,000,000" sub="held-back notifications, waiting in the queue" label="THE BACKLOG"]
One job left.
Everything GitHub paused on Sunday night has been queueing for a day.
Over five million notifications, and 80 thousand website builds.

[VISUAL: mail shown="7" value="200,000" sub="expired in the queue, and were dropped" title="the flood comes with a cost"]
As the flood is released, about 200 thousand of those notifications turn out to have expired in the queue, and are dropped.
GitHub pauses again, extends their shelf life, and keeps going.

[VISUAL: timeline from="Sun 22:52" to="Mon 23:03" marks="the 43 seconds|the choice|the rebuild|the pen goes home|the backlog" highlight="the 43 seconds" title="24 hours and 11 minutes, end to end"]
They keep the status red, on purpose, until every queued job is processed and checked.
[SFX: riser]
At 23:03 on Monday night, GitHub goes green.
24 hours and 11 minutes after a cable blinked for 43 seconds.

[VISUAL: lock title="what was actually lost" label="no user data, a few seconds reconciled by hand"]
No user data was lost.
A few seconds of entries needed reconciling by hand, but nothing anyone stored was gone.
And the code itself sat untouched in its separate storage, all day.

## SECTION: takeaway

[VISUAL: quote text="Orchestrator's actions behaved as configured, despite our application tier being unable to support this topology change." source="GitHub's post-incident analysis" motif="stick:shrug" cut="soft"]
Here is the sentence that makes this episode worth your time.
The guard did not malfunction.
It behaved exactly as configured.
Nobody had told it that a pen moved across a continent is a pen the rest of the system cannot live with.

[VISUAL: coasts pen="left" title="the fix" caption="failovers may cross the room, never the country"]
GitHub's fix was not to fire the guard.
They changed its rulebook, so it can never again move the pen across a regional boundary on its own.
Fast, local failover stays.
The continent-sized move is simply no longer automatic.

[VISUAL: barrier gap="off" title="the Monday decision" label="find the automation allowed to outrun you"]
So here is the decision you can make on Monday.
Find the piece of automation in your system that can act faster than any human can react.
Write down the biggest decision it is allowed to take alone, and ask whether you have ever rehearsed living with that decision.
GitHub now runs those rehearsals on purpose, injecting failures before the failures inject themselves.

[VISUAL: end_card next="Roblox switches on one clever optimisation, and 50 million players lose their world for 73 hours." motif="switch"]
Next time, a performance optimisation takes Roblox offline for 73 hours, in front of 50 million daily players.
Subscribe and it will turn up.
