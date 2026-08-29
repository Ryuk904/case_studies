# EP05 — Roblox, 28–31 October 2021

Everything above the first `## SECTION:` marker is front matter and never reaches the
voiceover. Notes on decisions that are not obvious from the lines themselves:

**"BoltDB" is never spoken.** HOUSE_STYLE §5 says to spell out anything the voice would
mangle and only use `BoltDB` if it has been *tested*, which costs quota this episode cannot
spare. The name appears on screen as a label instead, and the narration says "the log
store". Same for the acronyms in the source: no `NUMA`, no `NVMe`, no `iptables`, no `DNS`.
The pictures carry the proper nouns; the voice carries the plain language.

**Clock times are on screen, never spoken as clock times.** The source's own elapsed-time
markers imply three different start times for the 73-hour clock (research.md,
contradictions), so the narration speaks "73 hours" as Roblox's own headline figure and
speaks everything else as "the afternoon of the 28th", "a day in", "fifty hours in". The
subtraction never happens out loud.

**Renderer budget.** Six renderers were built for this story: `registry`, `funnel`,
`freelist`, `lockout`, `deadends`, `blindroom`. Four of them appear more than once, and
every repeat is a state change, not a reuse:

- `lockout` runs **half → closed → opening**: the shutter coming down at half past four,
  the shutter down for three days, the shutter ratcheting up ten percent at a time.
- `funnel` runs **poll → stream → freed**: four doorways, then one doorway seizing, then
  the same doorway spinning again as the backlog drains.
- `freelist` runs **growing → compact**: the inventory of empty shelves that has to be
  copied out before anything can be stored, and the same warehouse after compaction.
- `blindroom` runs **dark → fixed**, and that pair *is* the takeaway.

Inherited renderers are used six times in total and each is doing this story's job:
`metric_card` for three numbers that are the point, `switch` once for the rollout,
`diagram` once for what falls over when the registry does, `quote` twice, `end_card` once.
No `checklist` (§13 retires it), and no icon from EP01–EP04 is dropped in unchanged.

## SECTION: hook

[VISUAL: metric_card value="73" sub="hours offline" label="ROBLOX, OCTOBER 2021" field="on"]
On the 28th of October 2021, Roblox went down.
It came back online 73 hours later.
[PAUSE:0.7]

[VISUAL: lockout state="closed" hours="73" n="12" title="28 to 31 October 2021" mood="dark"]
Fifty million people play Roblox every day, and for three days, none of them could get in.
The thing that broke is the system that tells every part of Roblox where everything else is.
It is called Consul.
[PAUSE:0.8]

[VISUAL: switch state="flip" at="1.8" cue="on" photo="server_room" stage="room" title="The trigger was an improvement" label="switched on to use less of everything"]
There was no attack, and nobody shipped bad code.
The trigger was an improvement.
A feature switched on months earlier to use less processing power and less bandwidth.
It had been working exactly as promised.

[VISUAL: title_card text="Four wrong answers. Two and a half days." layout="hero" motif="stick:slump" sub="and a second fault nobody found until it was over"]
Working out why took four wrong answers and two and a half days.

## SECTION: context

[VISUAL: metric_card value="18,000" label="ROBLOX'S OWN HARDWARE" sub="servers, and 170,000 containers"]
Roblox does not rent its computers.
It builds and runs its own data centres, and by 2021 that meant over 18,000 servers and 170,000 containers.
At that size the hard problem stops being any single machine.

[VISUAL: registry state="ok" desk="where is everything?" title="Everything asks the same desk" caption="this is what Consul does"]
The hard problem is that every piece of software has to be able to find every other piece of software.
So Roblox runs a directory.
When a service needs to talk to another service, it asks the directory where that service currently lives.
Every service also checks in constantly to say that it is still healthy.
That is Consul, and hundreds of internal services depend on it.
[PAUSE:0.6]
Two other systems sit on top of it.
One decides which programs run on which machines, and the other hands out the passwords those programs need.
Both of them ask Consul first.
And there was one Consul cluster.
For all of it.

[VISUAL: funnel mode="poll" title="The old way: ask, and ask again"]
For years, a service found out about a change by asking.
And then asking again.
It works, and it is also thousands of machines asking the same question, forever.

[VISUAL: funnel mode="stream" span="90" title="The new way: one line, and it stays open" caption="Consul 1.10, streaming"]
So Roblox upgraded, to take advantage of a new feature called streaming.
Instead of everyone asking over and over, the directory keeps one line open and pushes changes down it as they happen.
Less asking, less answering, less bandwidth.
It is a genuinely good idea.
Roblox switched it on for a handful of services, watched it work, and over the following months switched it on for more.

[VISUAL: metric_card value="300" sub="milliseconds is a normal write" label="HEALTHY"]
And it worked.
A healthy write to the directory lands in under 300 milliseconds.
For months, that is exactly what the numbers said it was doing.

## SECTION: breakdown

[VISUAL: registry state="slow" desk="where is everything?" title="28 October, 13:37" mood="dark"]
On the afternoon of the 28th, one machine in the directory started running hot.
Writes that should have taken 300 milliseconds were taking 2 seconds.
Nobody was locked out yet.
At Roblox's scale a slow machine is ordinary, so the team did the ordinary thing and replaced it.
The new machine was just as slow.

[VISUAL: lockout state="half" readout="of players gone, in three hours" n="12" title="16:35" mood="dark"]
By twenty-five to five that afternoon, half the players were gone.
Here is why one slow directory takes down a whole platform.
If a service cannot find out where another service is, it cannot connect to it.
And if the system that starts programs and the system that holds the passwords both have to ask the directory first, then neither of them works either.

[VISUAL: diagram nodes="[Consul] --(where is it?)--> [every service]; [Consul] --(what runs where)--> [Nomad]; [Consul] --(secrets)--> [Vault]" highlight="Consul" title="One directory, and everything downstream of it"]
Roblox's own report puts it in one sentence.
The system failed because Consul was a single point of failure, and Consul was not healthy.
[PAUSE:0.8]

[VISUAL: deadends labels="bad hardware|bigger machines|our own traffic|smaller machines" every="14.0" cue="on" title="Four answers, in order" mood="dark"]
What follows is the part that makes this a three day outage instead of a three hour one.
The team formed a theory, tested it properly, and was wrong.
Four times.
[PAUSE:0.7]
Theory one: bad hardware.
New hardware did not help.
Theory two: Roblox had outgrown the servers the directory ran on.
So they replaced every one of them with machines that had twice as many processor cores and faster disks.
The directory was still slow.
[PAUSE:0.6]
Theory three: Roblox itself was the load.
They wiped the directory's state and restored it from a snapshot taken before any of this began.
They turned Roblox down to almost nothing, scaling services from hundreds of copies to single digits.
They slowed the health checks from every 60 seconds to every 10 minutes.
More than 24 hours in, there was almost nothing left to turn off.
It went unhealthy again.
[PAUSE:0.8]
Theory four: the bigger machines had made it worse.
They moved everything back onto the smaller ones.
That did not help either.

[VISUAL: funnel mode="stream" span="30" arrivals="9" backlog_label="writes waiting" cue="on" title="Inside the directory, not around it" mood="dark"]
Two days in, the team stopped looking at the directory from the outside and started looking at its insides.
Writes were not slow because the machine was slow.
Writes were slow because they were queueing behind each other.
[PAUSE:0.7]
The old way had every service asking its own question and getting its own answer.
The new way funnels all of those updates through one shared channel inside the software.
Under a heavy load of reading, that is cheaper.
Under a heavy load of reading and writing at the same time, everything piles up at the one doorway.
The company that makes Consul had tested streaming at this scale and never seen it.
It takes a very large number of open lines and a very high rate of change at once.
The faster machines made it worse.
More cores meant more things competing for the same doorway.

[VISUAL: funnel mode="freed" span="14" backlog0="42" title="15:51, on the 30th" caption="streaming disabled" cue="on"]
So they turned streaming off.
Writes went straight back to 300 milliseconds.
Fifty hours in, they finally had their answer.

[VISUAL: quote text="Despite the breakthrough, we were not yet out of the woods." source="Roblox, return to service report" motif="loop"]
Except that they did not.
Some machines, when they were elected to lead the cluster, were still slow.
The team could not work out why, so they made a pragmatic decision.
They rigged the system to stop those particular machines from staying in charge, and moved on.

[VISUAL: freelist target="960,000" parcel="16 kilobytes" list_label="free shelves to copy out first" span="42" title="What was wrong with those machines" mood="dark"]
The reason was found afterwards, by the engineers who wrote the software.
Consul keeps a running log of every change on disk.
To stop that log growing forever, it takes a snapshot every so often and deletes the old entries.
But the file never gets any smaller.
[PAUSE:0.7]
Think of a warehouse where a cleared shelf is never taken away.
It is added to a list of empty shelves kept by the door.
That list is normally a few lines long and nobody has ever had to care about it.
Now here is the rule of this warehouse.
Before you can put anything on a shelf, you rewrite the entire list of empty shelves.
[PAUSE:0.9]
On these machines, that list had grown to nearly a million entries.

[VISUAL: metric_card value="489" sub="megabytes of real data, inside a 4.2 gigabyte file" label="THE LOG STORE"]
The log file was 4.2 gigabytes.
The actual data in it was 489 megabytes.
The other 3.8 gigabytes was air.

[VISUAL: metric_card value="7.8" sub="megabytes of bookkeeping, before every single write" label="THE LIST OF EMPTY SHELVES"]
The list describing all that air came to 7.8 megabytes.
[PAUSE:0.7]
So every time the system wrote a new entry, 16 kilobytes or less, it wrote out that entire list first.
Nearly five hundred times more bookkeeping than content, on every single write.

[VISUAL: freelist state="compact" parcel="16 kilobytes" list_label="after compaction" title="The eventual repair"]
The fix, once it was understood, was to compact the file and give the empty space back.

[VISUAL: lockout state="opening" steps="10" every="3.4" readout="of players let back in" cue="on" title="31 October, back one slice at a time"]
Getting Roblox running again took another day, and most of it was not the directory.
The caches were cold, and the tool that fills them had only ever been asked to top them up.
Nobody had ever needed it to fill them from empty.
By five in the morning on the 31st, 61 hours in, the directory was healthy and so were the caches.
[PAUSE:0.6]
Then they let players back in deliberately slowly, a randomly chosen slice at a time, checking the load after every increase.
Roughly 10% more, then a check, then 10% more.
Some players worked out the scheme and started swapping the trick on Twitter to get in early.
At quarter to five that Sunday afternoon, everybody was back.

## SECTION: takeaway

[VISUAL: blindroom state="dark" machine="Consul" title="Why it took three days and not three hours" mood="dark"]
Two things went wrong inside the software, and both were genuinely hard to find.
But that is not really why this took three days.
It took three days because the instruments the team needed were plugged into the thing that was broken.
Roblox's monitoring depended on Consul.
So the moment Consul was unhealthy, the tools that would have shown them why went quiet too.

[VISUAL: quote text="Our telemetry systems no longer depend on the systems that they are configured to monitor." source="Roblox, return to service report" motif="link"]
That is the first fix Roblox lists, and it is the one worth taking away.

[VISUAL: blindroom state="fixed" machine="Consul" title="Its own supply"]
So here is the thing to go and check on Monday.
Open the dashboard you would reach for first in an outage, and find out what it runs on.
If the answer is the same cluster or the same network your product runs on, you do not have an instrument.
You have a mirror, and it goes dark at exactly the moment you need it.
[PAUSE:0.8]

[VISUAL: title_card text="A faster system is a differently fragile one." layout="hero" motif="gauge:0.35" sub="the optimisation itself was never the mistake"]
The optimisation was real, by the way.
It did use less processing power and less bandwidth, and Roblox says it means to switch it back on once it has been tested at their scale.
A performance improvement is not only a change in speed.
It is a change in how the thing fails.

[VISUAL: end_card next="A security update that was live for 78 minutes crashes 8.5 million computers." motif="world"]
If you want the next one, it is about the morning half the world's computers would not start.
Subscribe and it'll show up.
