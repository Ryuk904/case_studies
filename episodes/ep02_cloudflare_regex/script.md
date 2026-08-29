# EP02 — Cloudflare, 2 July 2019 — verbatim voice script

Written for someone who does not know what a regular expression is, and never uses the
phrase. Every number spoken has a row in research.md SOURCES.

Three open loops, planted early and paid off late:

1. **The rule was never switched on.** Planted at 0:40, paid off at ~6:20.
2. **The fast lane.** Planted at the end of the context section, paid off when the change
   reaches every machine on earth in two seconds and again in the takeaway.
3. **The missing guard.** Not planted verbally at all — it lands as a reversal, because the
   whole middle of the episode has been establishing that everyone did their job correctly.

Visual policy for this episode: nine of the twenty-nine visuals animate a state *changing*
rather than showing a state that is true. The three longest holds are `backtrack`, `world`
and `gauge`, all of which are still moving at second fifteen.

---

## SECTION: hook

[VISUAL: windows bad="0.85" secs="2.4" at="1.6" code="502" title="2 July 2019" caption="most of the web, at the same moment" cut="hard"]
On the 2nd of July, 2019, a large part of the internet stopped answering.
If you tried to open a website that afternoon, a lot of them handed you an error page.

[VISUAL: metric_card value="20 MILLION" sub="websites and apps sit behind one company" label="CLOUDFLARE" field="on"]
More than 20 million websites and apps sit behind a single company called Cloudflare.

[VISUAL: people n="10" highlight="8" title="then eight tenths of it went dark" caption="for 27 minutes, four fifths of their traffic was simply gone"]
For 27 minutes, Cloudflare lost about 80 percent of its traffic.

[VISUAL: code file="regex.txt" lang="one rule" caption="one line. 132 characters. shown wrapped, because it does not fit."]
The cause was one line of text, inside the filter that is meant to keep attacks out.
It was 132 characters long.
[SFX: thud]
[PAUSE:0.6]

[VISUAL: title_card text="and the rule was never switched on" motif="switch:off" layout="right" sub="it was not blocking anything yet"]
That rule was never actually switched on.

## SECTION: context

[VISUAL: diagram nodes="[you] --(open a website)--> [Cloudflare] --(if it looks safe)--> [the website]" title="they sit in the middle" flow="all" cut="soft"]
Start with what this company actually does.
When you open a website that uses Cloudflare, you do not reach that website first.
You reach Cloudflare.
They look at your request, decide it is not an attack, and pass it on.

[VISUAL: metric_card value="44 BILLION" sub="attacks stopped on an average day" label="THAT IS THE JOB"]
That is the job.
In the three months up to this, they were stopping around 44 billion attacks a day.

[VISUAL: title_card text="a rule is a description of what an attack looks like" motif="checklist:looks like this|and this|and this" layout="left"]
The way they do it is with a long list of rules.
Each rule is a description of what one kind of attack looks like.
One of the common ones is somebody typing a piece of code into a box on a web page, hoping it will end up running inside somebody else's browser.
So there are rules that describe what that looks like.
Every request that arrives gets checked against all of them.

[VISUAL: metric_card value="476" sub="changes to those rules in 60 days" label="ONE EVERY THREE HOURS"]
New attacks appear constantly, so those descriptions change constantly too.
Over one sixty day stretch, they made 476 changes to them.
That is one every three hours.

[VISUAL: checklist items="their own staff first|then a few free customers|then a few paying ones|then everybody" marks="tick|tick|tick|tick" title="how their normal software goes out"]
Now, Cloudflare is careful about how new code reaches the world.
It goes first to a place where only their own staff will hit it.
Then a small group of customers who are not paying.
Then a small group who are.
Only then, everybody.

[VISUAL: checklist items="their own staff first|then a few free customers|then a few paying ones|then everybody" title="how a firewall rule goes out"]
That takes hours, sometimes days.
Firewall rules skip every single one of those steps.
Not by accident.
On purpose.

[VISUAL: title_card text="when an attack is already spreading you cannot wait a day" motif="clock:0.08" layout="hero"]
And the reason is completely sound.
When a new attack is already spreading, waiting a day to protect people is not an option.
So rule changes get a fast lane.
[PAUSE:0.5]
Hold on to the fast lane.

## SECTION: breakdown

[VISUAL: stick pose="type" n="1" prop="desk" title="early afternoon, a routine change" caption="one engineer, one small edit to the rules" cut="soft"]
Back to that Tuesday afternoon.
An engineer on the firewall team finishes a small change to those rules.
Another engineer reads it and approves it.

[VISUAL: checklist items="written|reviewed|approved|tests passed" marks="tick|tick|tick|tick" title="six minutes later, everything is green"]
Six minutes later the automated tests run, and everything passes.

[VISUAL: switch state="flip" at="2.4" title="five minutes after that, it goes out" label="nobody presses anything"]
Five minutes after that, the system sends it out on its own.
Nobody presses a button.
That is exactly how it is designed to work.

[VISUAL: world secs="2.29" at="1.1" title="and it goes everywhere" caption="2.29 seconds to reach every machine they own, in more than 180 cities"]
Cloudflare built their own way of pushing changes out, and it is genuinely remarkable.
Something changed in one place is live on every machine they own, in more than 180 cities, in about two seconds.
[PAUSE:0.5]
That is the fast lane.

[VISUAL: code body=".*.*=.*" lang="the part that mattered" highlight="0" caption="seven characters, out of a hundred and thirty two"]
Now, what was in that change.
Most of those 132 characters do not matter.
This bit does.
And you can read it out loud even if you have never seen anything like it before.
It says: find anything, then anything, then an equals sign, then anything.

[VISUAL: backtrack text="x=x" target="23" title="anything, followed by anything" caption="three characters. watch what it costs."]
And that is the whole problem.
Anything, followed by anything.
There is no single way to do that.
[PAUSE:0.5]
Take the shortest example there is.
Three characters.
An x, an equals sign, another x.
The machine has to decide where the first anything stops and the second one starts.
So it takes a guess.
It checks whether there is an equals sign where it expects one.
There is not, so it goes back, shuffles the boundary along, and guesses again.
For three characters, it does that 23 times before it is satisfied.
[PAUSE:0.6]

[VISUAL: backtrack text="x=xxxxxxxxxxxxxxxxxxxx" target="555" title="now make the string longer" caption="the count is not going up in a straight line" cut="hard"]
23 is nothing.
A computer does that instantly.
Now add one character.
It takes 33.
Add one more, and it is 45.
That is not going up in a straight line.
Every character you add multiplies the number of boundaries it has to try.
By twenty characters, it is 555.
[PAUSE:0.5]

[VISUAL: backtrack text="xxxxxxxxxxxxxxxxxxxx" target="4067" title="and the worst case is no answer at all" caption="twenty characters, and no equals sign anywhere"]
And it is worse when the answer turns out to be no.
Take the equals sign away entirely.
Now the machine has to try every single boundary before it can be sure.
That takes 4,067 attempts, to tell you that nothing matched.

[VISUAL: gauge value="0.99" label="every processor handling web traffic, worldwide" title="now run that on everything that arrives"]
Now remember where this rule lives.
It runs on every single request that comes in.
And real requests are not three characters long.
They are hundreds of characters, or thousands.
[PAUSE:0.6]
Across the entire network, the machines stopped having anything left over to answer with.

[VISUAL: windows bad="1.0" secs="1.8" at="1.0" code="502" title="which is what everybody else saw" caption="not the site you asked for"]
The computers were not down.
They were busy.
Busy trying every possible way to read a piece of text that was never going to match.

[VISUAL: stick pose="walk" travel="480" then="panic" at="3.2" n="1" title="three minutes after it went out" caption="the first alarm, then all of them at once"]
Three minutes after the change goes out, the first alarm fires.
Then every other alarm.
Somebody says out loud that they have lost 80 percent of their traffic.

[VISUAL: title_card text="the first theory in the room was that somebody was attacking them" motif="lock" layout="right"]
And the first thought in the room is that somebody is attacking them.
It takes about fifteen minutes to prove that nobody is.

[VISUAL: timeline title="from here it should have been quick" from="13:42" to="14:09" marks="change goes out|first alarm|it is our own filter|the switch" highlight="the switch"]
Because they have exactly the right tool for this.
One switch that turns the whole filter off, everywhere, at once.
Somebody proposes it.
[PAUSE:0.6]
And then five minutes go by.

[VISUAL: door label="their own login went through the thing that was broken" title="because they could not get in" arrive="2.6"]
To press that switch, they had to log in to their own internal system.
Their own internal system sat behind Cloudflare.
Which was, at that moment, not working.
[PAUSE:0.5]
And some of them could not have logged in anyway, because their access had already been switched off automatically for not using it often enough.

[VISUAL: metric_card value="27" sub="minutes, start to finish" label="AND THEN IT WAS OVER" field="on"]
Eventually somebody gets through and hits it.
Two minutes later the traffic is back.
Twenty-seven minutes, from the change going out to the traffic coming back.

[VISUAL: barrier label="taken out weeks earlier, by a change meant to make the filter faster" title="now, the part that is hardest to look at"]
There used to be a protection in this system.
Something that watched for a rule taking too long and stopped it before it ate the machine.
It had been taken out a few weeks earlier.
By mistake, during a tidy-up.
[PAUSE:0.6]
And the purpose of that tidy-up was to make the filter use less processing power.

[VISUAL: checklist items="does it catch attacks|does it block things it should not|how long does it take to answer" marks="tick|tick|" title="and the tests could not see it either"]
Second thing.
The tests really did check those rules.
They checked whether each one caught the attacks it was meant to catch, and whether it blocked anything it should not have.
Nothing anywhere measured how long a rule took to answer.

[VISUAL: switch state="off" title="and the rule was still switched off" label="real traffic through it, nothing blocked"]
And the third thing is the one from the very beginning.
That rule was not switched on.
It had gone out in a trial mode.
Real traffic passes through it, and nothing gets blocked.
They were watching to see how well it worked before letting it do anything at all.
[PAUSE:0.6]
But a rule on a trial run still has to run.
[SFX: thud]
And running it was the entire problem.

[VISUAL: quote text="Everything that occurred up to the point the rules were deployed was done correctly." source="Cloudflare's own postmortem, 12 July 2019" motif="checklist:+written|+reviewed|+approved|+tested"]
This is the sentence from their own writeup.

## SECTION: takeaway

[VISUAL: title_card text="this is not a story about one badly written line" motif="stick:slump" layout="left" cut="soft"]
It is tempting to make this a story about one badly written line.
That story is wrong.

[VISUAL: checklist items="a pattern that could take forever to answer|a guard removed to make things faster|tests that measured right and wrong, not cost|a fast lane with nothing at the end of it" marks="cross|cross|cross|cross" title="four ordinary decisions"]
Four ordinary things had to line up.
A pattern that could take forever to answer.
A guard removed while making things faster.
Tests that measured whether an answer was right, never what it cost.
And a fast lane, deliberately built, with nothing at the end of it.

[VISUAL: barrier gap="off" title="so go and find your own fast lane" label="then go and look at what actually stops it"]
Almost every system has a fast lane.
The hotfix, the emergency path, the thing that skips the checks.
That path is the one thing a careful rollout will never catch.
So go and look at what stops a change in it going wrong.
If the answer is that somebody would notice, you do not have a brake.
You have a hope.
[PAUSE:0.5]
Cloudflare put their guard back, and read all 3,868 of their rules by hand.

[VISUAL: end_card next="GitLab deleted their own database, then found all four backups had failed" motif="lock"]
Next time, a company deleted its own live database by accident.
Then found that all four of its backups had quietly stopped working.
Subscribe and it will turn up.
