# EP01 — Knight Capital — verbatim voice script (v2, general audience)

Rewritten for a general audience and for retention. Facts are unchanged and every number
still has a row in research.md SOURCES, quoted from SEC Order 34-70694.

What changed from v1:
- Opens on a mystery instead of the answer. v1 gave away $460M and "seven of eight servers"
  in the first fifteen seconds, which is right for engineers and wrong for everyone else.
- Two open loops planted early (the 97 warnings, the fix that made it worse) and paid off late.
- Jargon replaced with analogy. No "order router", no "cumulative quantity function".
- Roughly double the visual beats, so nothing sits on screen long enough to go stale.

---

## SECTION: hook

[VISUAL: clock fraction="0.75" title="45 minutes"]
This is a story about 45 minutes.

[VISUAL: metric_card value="$460,000,000" sub="gone" label="1 AUGUST 2012" ]
In those 45 minutes, one of the largest trading firms in America destroyed itself.
[PAUSE:0.6]

[VISUAL: lock title="nobody attacked them" label="nothing was broken into"]
Nobody hacked them.
Nobody stole anything.

[VISUAL: calendar years="2003|2004|2005|2006|2007|2008|2009|2010|2011|2012" mark="0" title="somebody forgot to delete some code" note="written in 2003, never removed"]
The whole thing happened because of some old code nobody had deleted in nine years.
[SFX: thud]

[VISUAL: mail value="97" sub="warnings, before the market even opened" shown="7" title="and here is the part that hurts"]
And the really painful detail.
Their own systems tried to warn them 97 times that morning.
[PAUSE:0.5]
Nobody read a single one.

## SECTION: context

[VISUAL: title_card text="first, who they were" motif="checklist:who they were|what the machine did"]
To understand how 45 minutes does that much damage, you need two things.
Who this company was, and what their machine actually did.

[VISUAL: people n="10" highlight="1" title="one trade in ten" caption="roughly one in ten American stock trades went through Knight"]
Knight Capital was not a small firm.
Roughly one in every ten trades in American stocks went through them.

[VISUAL: diagram nodes="[you] --(buy 100 shares)--> [your broker] --(sends it on)--> [Knight]" title="where they sat"]
If you bought shares in 2012, your order probably passed through a company like this without you ever hearing their name.
They sat in the middle.
Buyers on one side, sellers on the other.

[VISUAL: title_card text="the machine had one job" motif="servers:1"]
And they had a machine to handle the orders.
Its job was simple to describe.

[VISUAL: diagram nodes="[one big order] --> [the machine]" title="a big order comes in"]
A big order arrives.
Say somebody wants fifty thousand shares.

[VISUAL: diagram nodes="[one big order] --> [the machine]; [the machine] --> [500 shares]; [the machine] --> [300 shares]; [the machine] --> [700 shares]" title="it chops it into pieces" flow="all"]
If you dump all fifty thousand onto the market at once, you move the price against yourself.
So the machine chopped it into hundreds of small pieces.
A few hundred shares here, a few hundred there.

[VISUAL: counter value="50000" label="stop when the tally gets here" title="and it kept a tally"]
And it kept a tally.
Every time a piece got filled, the tally went up.
When the tally reached fifty thousand, the machine stopped.
[PAUSE:0.6]

[VISUAL: title_card text="remember the tally" motif="counter"]
That tally is the whole story.
Keep it in your head.

## SECTION: breakdown

[VISUAL: timeline title="nine years of nothing going wrong" from="2003" to="2012" marks="old feature switched off|the tally is moved|nine quiet years" highlight="the tally is moved"]
Now go back to 2003.
The machine had an old feature in it called Power Peg.
Knight stopped using it that year.

[VISUAL: checklist items="stop using it|delete it" marks="tick|" title="but they never deleted it"]
But they never deleted it.
The code just sat there, switched off, waiting.

[VISUAL: switch state="off" title="think of a light switch" label="one you stopped using, still wired to something downstairs"]
Think of a light switch on your wall that you stopped using years ago.
You did not remove it.
You just stopped flipping it.
And it is still wired to something downstairs.

[VISUAL: quote text="In 2005, Knight moved the tracking of cumulative shares function in the Power Peg code to an earlier point in the SMARS code sequence." source="SEC Order 34-70694" motif="calendar:2005|2006|2007|2008"]
Then in 2005, somebody moved the tally.
They relocated it to a different part of the system.

[VISUAL: link left="Power Peg" right="the tally" title="the old feature was never reconnected"]
The old switched-off feature was never reconnected to it.
Nobody checked, because why would you check something that never runs.
[PAUSE:0.6]
For seven years, it did not matter.

[VISUAL: calendar years="2003|2004|2005|2006|2007|2008|2009|2010|2011|2012" mark="9" title="then, 2012" note="the New York Stock Exchange launches something new"]
Then comes 2012.
The New York Stock Exchange launches a new programme to get retail customers better prices.
Knight has to be ready for it on the 1st of August.

[VISUAL: title_card text="so they wrote new code" motif="stick:type"]
So the team writes the new code.
And then they make a decision that is going to sound completely reasonable.

[VISUAL: switch state="off" title="there was already a switch sitting there" label="it used to turn on Power Peg"]
They needed a switch to turn the new feature on.
There was already one sitting there, the one that used to turn on Power Peg.

[VISUAL: switch state="on" title="same switch, new job" label="from 2012 it turns on the new feature"]
So they reused it.
Same switch, new job.
[PAUSE:0.5]

[VISUAL: checklist items="the old feature was dead|the switch was free" marks="tick|tick" title="this is a normal thing to do"]
And honestly, this is a normal thing to do.
The old feature was dead.
The switch was free.

[VISUAL: checklist items="reuse the switch|delete what it used to control" marks="tick|" title="it only works if you do both"]
It only works if you actually delete the thing the switch used to control.
They meant to.

## SECTION: breakdown

[VISUAL: stick pose="carry" prop="box" prop_label="the new code" n="1" title="27 July: copying it across by hand" caption="eight computers, one technician, no checklist"]
The machine did not run on one computer.
It ran on eight.
Starting on the 27th of July, a technician copied the new code onto them by hand.

[VISUAL: servers n="8" bad="8" title="seven of eight" label="the eighth never got the new code"]
Seven of them got it.
[SFX: tick]
[PAUSE:0.7]
The eighth did not.

[VISUAL: checklist items="a second person checks the work|a written rule says they must|the system compares the eight" title="nobody checked"]
No second person checked the work.
There was no written rule saying anyone had to.
And nothing in the system compared the eight machines against each other.

[VISUAL: metric_card value="8:01 AM" sub="ninety minutes before the market opens" label="THE MORNING OF 1 AUGUST" count="off"]
Now, the morning of the 1st of August.
At one minute past eight, something starts happening.

[VISUAL: title_card text="Power Peg disabled" motif="mail:1" sub="the error message nobody was reading"]
Knight's systems begin sending automated emails.
Each one carries an error message.
Power Peg disabled.

[VISUAL: mail value="97" sub="emails, before the opening bell" shown="7" title="the smoke alarm nobody heard"]
Ninety-seven of those go out before the market opens.
[PAUSE:0.7]
They were not designed to be alarms.
They went to a mailbox people did not really read.

[VISUAL: alarm title="a smoke alarm going off in a room nobody uses" caption="ninety minutes, in real time"]
It is a smoke alarm going off in a room nobody walks into.
The warning was there, in real time, for ninety minutes.

[VISUAL: clock fraction="0.0" title="9:30" label="the market opens"]
Then the market opens.
And the switch gets flipped.

[VISUAL: diagram nodes="[the switch] --(on 7 machines)--> [the new feature]; [the switch] --(on machine 8)--> [Power Peg]" highlight="Power Peg" title="one switch, two meanings"]
On seven machines, that switch means run the new feature.
On the eighth, it still means the old thing.
It means wake up Power Peg.
[SFX: thud]

[VISUAL: counter value="50000" blank="on" label="nothing there" title="and Power Peg goes looking for its tally"]
And Power Peg starts doing its job.
It sends out a piece of the order.
The piece gets filled.
Then it goes to check the tally, to see whether it should stop.

[VISUAL: loop label="send. fill." title="the loop with no exit"]
The tally was moved in 2005.
So there is nothing there.
So it sends another piece.
And another.
And another.
[PAUSE:0.6]

[VISUAL: title_card text="it had no way to know it was finished" motif="servers:1"]
It was not broken, exactly.
It was doing precisely what it was built to do.
It just had no way of ever finding out it was done.

[VISUAL: quote text="Although one part of Knight's order handling system recognized that the parent orders had been filled, this information was not communicated to SMARS." source="SEC Order 34-70694" motif="link"]
And here is the eerie part.
Somewhere else in the building, Knight's systems knew.
Another part of the system had worked out the orders were already filled.
That information never reached the machine doing the buying.

[VISUAL: metric_card value="212" sub="customer orders went in" label="WHAT WENT IN"]
212 customer orders went into that machine.

[VISUAL: scale small="212" small_label="customer orders in" big="1400" big_label="trades out" title="212 in, four million out"]
Over four million trades came out.
[SFX: thud]

[VISUAL: metric_card value="397,000,000" sub="shares, in 45 minutes" label="ACROSS 154 DIFFERENT COMPANIES"]
397 million shares.
Across 154 different companies.
In 45 minutes.

[VISUAL: diagram nodes="[bought too much] --($3.5bn)--> [Knight]; [sold too much] --($3.15bn)--> [Knight]" highlight="Knight" title="what they were left holding"]
By the end of it Knight had accidentally bought three and a half billion dollars of stock it did not want.
And accidentally sold three billion it did not have.
Real money.
Real shares.

[VISUAL: stick pose="shrug" n="1" title="so why did nobody just stop it"]
Which raises the obvious question.
It ran for 45 minutes.
Why did nobody just turn it off.

[VISUAL: dashboard title="because nothing looked broken" caption="healthy computers, healthy network, orders filling"]
Partly because almost nothing looked broken.
The computers were healthy.
The network was fine.
Orders were arriving and being filled, exactly as the system was designed to fill them.

[VISUAL: title_card text="the tool that watched for this needed a human watching it" motif="alarm"]
The tool that was supposed to catch this needed a person watching a screen.
And under heavy load, it fell behind and started reporting numbers that were wrong.

[VISUAL: stick pose="type" n="1" title="then they tried to fix it" caption="they did the thing you would do"]
And then the team did the thing you would do.
They tried to undo the change.
[PAUSE:0.7]

[VISUAL: quote text="Knight uninstalled the new RLP code from the seven servers where it had been deployed correctly. This action worsened the problem." source="SEC Order 34-70694" motif="switch:on"]
They removed the new code from the seven machines where it had installed correctly.
Think about what that does.

[VISUAL: servers n="8" bad="1,2,3,4,5,6,7,8" title="the fix that made it worse" label="now the switch means the old thing on every one"]
Those seven machines now had no new feature either.
So the switch started meaning the old thing on all of them.
[SFX: thud]

[VISUAL: metric_card value="8" sub="machines now running the fault" label="IT HAD BEEN ONE" count="off"]
A problem that had been trapped on one machine was now running on all eight.

## SECTION: takeaway

[VISUAL: timeline title="what happened to the company" from="1 Aug 2012" to="Jul 2013" marks="the 45 minutes|rescued|absorbed|gone"]
By the end of the next day, three quarters of the company's value was gone.
Four days later they raised 400 million dollars just to survive the week.
Within a year the company had been swallowed by a merger and no longer existed under its own name.

[VISUAL: stick pose="slump" n="1" hot="1" title="it is tempting to blame the technician"]
It is very tempting to make this a story about one technician who missed one machine.
That story is wrong.

[VISUAL: checklist items="keep old code instead of deleting it|reuse a switch instead of adding one|copy files by hand, unchecked|send warnings where nobody looks" marks="cross|cross|cross|cross" title="four ordinary decisions"]
Four completely ordinary decisions had to line up.
Keep old code instead of deleting it.
Reuse a switch instead of adding a new one.
Copy files by hand with nothing checking the result.
And send warnings to a place nobody looks.

[VISUAL: title_card text="every one of those is a Tuesday afternoon" motif="clock:0.6"]
Not one of those is reckless.
Every single one of them is a Tuesday afternoon.

[VISUAL: switch state="off" title="old code is not switched off" label="it is waiting for somebody to flip a switch they think is free"]
The lesson is not that computers are dangerous.
It is that old code is never really switched off.
It is just waiting for somebody to flip a switch they think is free.

[VISUAL: end_card next="the one line of code that took 80 percent of Cloudflare's traffic offline" motif="servers:6"]
Next time, a single line of text took 80 percent of Cloudflare's traffic off the internet in 27 minutes.
It was one sentence long.
Subscribe and it will find you.
