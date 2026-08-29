# EP05 — publishing assets

Trimmed per HOUSE_STYLE §12: measured traffic is Direct 60% / External 20% / Playlists 20%
and **YouTube search 0%**, so this is written for someone who has already clicked.

## Title

| | EP01 | EP02 | EP03 | EP04 | EP05 |
|---|---|---|---|---|---|
| Title says | They forgot to delete some code | They did everything right | They deleted the wrong database | Nobody touched anything — the safety system did it | They made it faster, and it never came back up |
| Failure was | code nobody deleted | code everybody approved | safety nets nobody tested | a failover nobody could undo | an optimisation that worked |

**Chosen:** Roblox Made One Thing Faster. It Was Offline for 73 Hours.

Alternates: *The Optimisation That Took Roblox Down for Three Days* · *73 Hours Offline*

## Description

Roblox switched on a feature designed to use less processing power and less bandwidth. It
worked exactly as promised for months. Then it took the whole platform offline for 73 hours,
in front of fifty million daily players.

The hard part was not fixing it. It was finding it. Four separate theories, each one
reasonable, each one wrong, and a second fault underneath the first that nobody found until
after the outage was over. Underneath all of it, the reason three hours became three days:
the monitoring that would have shown the cause was itself built on the system that was down.

CHAPTERS
<!-- Generated from out/chapters.txt after the full render. Do NOT hand-write these.
     The dry render's timings are estimates and must never be published. -->

SOURCE
Roblox, "Roblox Return to Service 10/28-10/31 2021"
https://about.roblox.com/newsroom/2022/01/roblox-return-to-service-10-28-10-31-2021

Every number in this video comes from that report. Where it contradicts itself, the video
says so.

IMAGE CREDITS
Photographic plates used under Creative Commons Attribution 2.0, treated and composited:
- Warehouse — nSeika — https://www.flickr.com/photos/33542052@N07/8096899965
- Paper — FeatheredTar — https://www.flickr.com/photos/55915190@N00/2302651444
- Crowd — Mark Hodson Photos — https://www.flickr.com/photos/20538653@N00/3388029136
- Turnstile — ell brown — https://www.flickr.com/photos/39415781@N06/4388675372
- Arcade — Dominic's pics — https://www.flickr.com/photos/64097751@N00/1128788988
- Server room, office, control room — public domain

**This block is the licence condition on five CC BY plates, not a courtesy. Removing it
breaks the licence.**

## Tags

roblox outage, roblox down, consul, hashicorp, postmortem, incident review, site reliability, distributed systems, service discovery, outage analysis, engineering failure, case study, boltdb, observability, monitoring

## Pinned comment

The two causes are sequential, not stacked. The streaming contention came first; the
conditions it created are what grew the free-page list; and that list is why turning
streaming off did not end the outage. Roblox's report is worth reading in full.
