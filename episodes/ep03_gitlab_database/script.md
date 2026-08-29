# EP03 — GitLab, 31 January 2017 — verbatim voice script

Written for someone who does not know what a database replica is, and never uses the
phrase. Every number spoken has a row in research.md SOURCES.

Two open loops, planted early and paid off late:

1. **Five safety nets.** Planted in the hook, enumerated in context, crossed off one by
   one through the back half of the breakdown.
2. **The accidental copy.** "The only copy left is one that nobody planned to make" at
   ~0:40; who made it, and why, lands at ~6:00 after all five nets have failed.

Visual policy: the long backup-hunt sequence alternates a recurring five-item checklist
with a different pictorial scene per net, so the episode's spine is a scoreboard the viewer
watches fill with crosses. No scene holds without something still moving at second
fifteen (gauge trembles, alarm pulses, loop orbits, stick cycles, counters turn).

---

## SECTION: hook

[VISUAL: stick pose="type" n="1" prop="desk" title="eleven at night, 31 January 2017" caption="five hours into a spam attack, one job left" cut="hard"]
It is eleven at night on the 31st of January, 2017.
An engineer at GitLab is five hours into fighting a spam attack, with one job left.
Wipe the broken spare database server, so it can be rebuilt.

[VISUAL: code body="db1.cluster.gitlab.com\ndb2.cluster.gitlab.com" syntax="on" highlight="0" lang="two machines" caption="the live server, and the spare" cut="hard"]
He runs the wipe on the wrong one.
[SFX: thud]

[VISUAL: metric_card value="300" sub="gigabytes of live database, gone in seconds" label="GITLAB.COM" field="on"]
Within seconds, around 300 gigabytes of GitLab.com's live production database is gone.
This is what backups are for.

[VISUAL: checklist items="the spare server|the daily export|the provider's snapshots|the daily disk photo|the copy for testing" title="five safety nets"]
GitLab has five separate safety nets for exactly this moment.
[PAUSE:0.6]
Not a single one of them works.

[VISUAL: title_card text="the only copy left was an accident" motif="clock:0.25" layout="right" sub="this is the story of how close it was"]
The only copy left is one that nobody planned to make.

## SECTION: context

[VISUAL: diagram nodes="[the code] --(lives in)--> [its own storage]; [everything else] --(lives in)--> [one database]" title="what GitLab keeps" cut="soft"]
Start with what GitLab actually is.
It is the place where software teams all over the world keep their work.
The code itself lives in its own separate storage, like paper in a filing room.
Everything else lives in one database.
Every project, every task, every comment, every user account.
Hold on to that split, because it decides what survives tonight.

[VISUAL: diagram nodes="[the live server] --(copies every change)--> [the spare]" title="two identical machines" flow="all"]
That database runs on two identical machines.
One of them answers everyone, the live server.
The other is a spare, holding a copy, ready to take over if the live one dies.
The live server writes a diary of every change it makes, and the spare reads along, a few pages behind.

[VISUAL: link left="the live server" right="the spare" title="if the spare falls too far behind"]
But if the spare falls too far behind, the diary pages it needs get thrown away, and the link breaks.
Then there is only one fix.
Wipe the spare completely, and copy everything across from scratch.
Remember that too.

[VISUAL: checklist items="the spare server|the daily export|the provider's snapshots|the daily disk photo|the copy for testing" marks="tick|tick|tick|tick|tick" title="five safety nets, on paper" reveal="26"]
Behind those two machines sit more nets.
Once every 24 hours, a full export of the database, sent to a storage service in the cloud.
Disk snapshots at their hosting provider, a copy-everything feature you switch on per machine.
A daily photograph of the database's whole disk, taken automatically every night.
And a copy of that photograph, shipped to a test environment, where engineers rehearse risky changes on realistic data.
Count the spare in, and there are five separate ways the data is supposed to survive.
On paper, this company is very hard to kill.

[VISUAL: dashboard cols="3" rows="2" title="and every net reported fine"]
But every net on that list shares one property.
Each was set up once, trusted, and never tested again.
Checking them was nobody's job.
[PAUSE:0.5]
Now, back to that Tuesday night.

## SECTION: breakdown

[VISUAL: gauge value="0.92" label="the database, that evening" title="Tuesday, six in the evening" cut="soft"]
At six that evening, the team notices GitLab.com is struggling.
Spammers are hammering the site, creating junk faster than the database can absorb it.
One single account turns out to be signing in from 47,000 different addresses.

[VISUAL: people n="10" highlight="1" title="and one job stranger than the rest" caption="a deletion, running quietly in the background"]
Part of the load turns out to be GitLab's own system, quietly deleting one of their own employees.
A troll had reported the account for abuse, and the machinery believed it.

[VISUAL: alarm title="nine in the evening" caption="writes locking up, parts of the site going down"]
[SFX: ping]
By nine, the database is locking up, and parts of the site are going down.

[VISUAL: link left="the live server" right="the spare" title="ten at night, a second alarm"]
[SFX: ping]
At ten, a second alarm.
Under all that load, the spare has fallen too far behind, and the copying has stopped dead.
The fallback of last resort is now broken too.

[VISUAL: stick pose="type" n="1" prop="desk" title="one engineer takes the rebuild" caption="an hour ago he told the team he was signing off"]
One engineer takes the rebuild.
He has been fighting the spam since the afternoon, and around eleven his time he had told the team he was about to sign off for the night.
Then the spare broke, and he stayed.

[VISUAL: servers n="2" bad="2" title="the fix for a broken spare" label="wipe it, then copy everything across fresh"]
The fix is the brutal one from earlier.
He wipes the spare clean, and starts the big copy from the live server.
Nothing happens.
No progress, no error, nothing.

[VISUAL: loop label="waiting, in silence" title="the tool was not stuck, just quiet"]
He cannot know it, but the copy tool is simply waiting, silently, as it sometimes does for up to 10 minutes.
Nothing in its documentation, or in the company's own guides, says so.
He tries settings, restarts things, tries again.
Silence.

[VISUAL: stick pose="look" n="1" title="close to midnight, one more idea" caption="maybe leftover files are blocking the copy"]
It is close to midnight when he has one more idea.
Maybe leftover files from the failed attempts are blocking the copy.
So, wipe the directory again, and go again.

[VISUAL: code body="db1.cluster.gitlab.com\ndb2.cluster.gitlab.com" syntax="on" highlight="0" lang="two machines" caption="one terminal open on each" cut="hard"]
He is logged in to both machines, and their names differ by one character.
[PAUSE:0.6]
He runs the wipe on the live one.
[SFX: thud]

[VISUAL: metric_card value="4.5" sub="gigabytes left, out of around 300" label="A SECOND OR TWO LATER"]
A second or two, and he sees it.
He kills the command at 11:27.
Of around 300 gigabytes, about 4.5 are left.
The live database is gone, and the spare is the empty box he wiped himself half an hour before.

[VISUAL: checklist items="the spare server|the daily export|the provider's snapshots|the daily disk photo|the copy for testing" marks="cross||||" title="now the safety nets"]
Now, the safety nets.
Net one, the spare server, is that empty box.
[SFX: tick]

[VISUAL: barrier label="failing silently, every single night" title="net two, the daily export"]
Net two, the daily export.
The team goes looking for the export files, and finds them a few bytes each.
The export tool had fallen a version behind the database itself, and the mismatch made it fail the instant it started.
It had been failing silently, every day, for nobody knows how long.

[VISUAL: mail title="the warnings were sent" caption="every failure emailed an alert, and every alert was rejected"]
Every failure did send a warning email.
The mail server on the receiving end rejected every one of them, for a missing security signature.
Nobody ever saw a single warning.

[VISUAL: metric_card value="0" sub="files in the cloud storage bucket" label="THE CLOUD COPY" count="off"]
And the bucket in the cloud, where those exports were supposed to land.
Empty.
[SFX: thud]
[PAUSE:0.6]

[VISUAL: switch state="off" title="net three, the provider's snapshots" label="never switched on for the database servers"]
Net three, the disk snapshots at the hosting provider.
[SFX: tick]
That feature is switched on machine by machine.
It was on for the file servers.
For the database servers, nobody had ever enabled it, because the other backups made it feel unnecessary.

[VISUAL: checklist items="the spare server|the daily export|the provider's snapshots|the daily disk photo|the copy for testing" marks="cross|cross|cross||" title="two nets left"]
Nets four and five, the daily disk photo, and its copy in the test environment.
[SFX: tick]
Both exist, and both ran on schedule, almost a full day ago.
Restoring from them means losing almost 24 hours of everyone's work.

[VISUAL: quote text="Out of five backup/replication techniques deployed none are working reliably or set up in the first place." source="GitLab's incident notes, written live that night" motif="checklist:one|two|three|four|five"]
Their own notes, written in public that night, put it in one sentence.
[PAUSE:0.5]

[SFX: riser]
[VISUAL: title_card text="except" layout="hero" mark="off" cut="hard"]
Except.
[PAUSE:0.7]

[VISUAL: stick pose="carry" n="1" prop="box" title="twenty past five, that afternoon" caption="one engineer, one experiment, one copy made by hand"]
Rewind to twenty past five that afternoon, before any of this began.
An engineer had wanted to test an idea for spreading the database's load.

[VISUAL: checklist items="scheduled|automatic|in the runbook|a backup at all" marks="cross|cross|cross|cross" title="what this copy was not" reveal="10"]
He needed realistic data, so he took a manual disk photo of production, and loaded it into the test environment.
Not scheduled, and not part of any procedure.
Just one person's copy, made by hand, for an unrelated experiment.
[PAUSE:0.6]

[VISUAL: title_card text="the same engineer" layout="hero" cut="hard"]
It is the same engineer.
The engineer who deleted the database had also, six hours earlier, made the only copy of it that survived.

[VISUAL: metric_card value="6" sub="hours old. the only copy that worked." label="THE ACCIDENT"]
Six hours old.
Everything after twenty past five is already lost, forever.

[VISUAL: clock fraction="0.75" label="around 18 hours to copy it back" title="the restore crawled"]
Restoring that copy is its own ordeal.
To save money, the test environment runs on the cheapest storage tier, throttled to about 60 megabits a second.
Copying the database back takes around 18 hours.

[VISUAL: metric_card value="5,000" sub="people watching them work, live on YouTube" label="THEY STREAMED IT"]
And they do it in the open.
The whole recovery goes out on a YouTube live stream, with the incident notes in a public document.
Around 5,000 people watch, and for several hours it is the second biggest live stream on the platform.

[VISUAL: timeline from="Tue 17:20" to="Wed 18:00" marks="the snapshot|the spam|the deletion|the copy back|back online" highlight="the deletion" title="the whole night, end to end"]
In the end, GitLab.com is down for about 18 hours.
The six hours after the snapshot never come back.
About 5,000 projects, about 5,000 comments, and around 700 new accounts, gone for good.

[VISUAL: title_card text="the code itself survived" motif="lock" layout="left" sub="the filing room was never touched"]
The code itself survived, in its separate storage, untouched.
What died was the six hours of record around it.

## SECTION: takeaway

[VISUAL: title_card text="this is not a story about one wrong terminal" motif="stick:slump" layout="right" cut="soft"]
It is tempting to make this a story about one tired engineer and one wrong terminal.
GitLab did not tell it that way, and they were right.
Their fix list is about making mistakes cheap to recover from, not impossible to make.

[VISUAL: checklist items="a pattern nobody tested|warnings nobody received|a feature nobody enabled|a copy nobody owned|a spare nobody could use" marks="cross|cross|cross|cross|cross" title="what nearly killed them" reveal="12"]
Because the deletion is not what nearly killed the company.
Five safety nets, rusting in silence, is what nearly killed the company.
Their postmortem asks why the backups were never tested, and the answer is one word.
Ownership.
Nobody owned proving they still worked.

[VISUAL: barrier gap="off" title="the Monday decision" label="restore one backup, onto a blank machine, this week"]
So here is the decision you can make on Monday.
Take the backup you trust most, and actually restore it, onto a blank machine.
Then write down whose job it is to prove it still restores next month.
A backup nobody has ever restored is not a backup.
It is a hope, with a schedule.

[VISUAL: end_card next="A 43 second network glitch split GitHub's database in two. Repairs took 24 hours." motif="link"]
Next time, a 43 second network hiccup splits GitHub's database in two, and putting it back together takes a full day.
Subscribe and it will turn up.
