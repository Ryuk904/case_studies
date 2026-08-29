# EP01 — Knight Capital

## Core hook & stake

On 1 August 2012, Knight Capital Americas deployed new code to SMARS, its automated equity
order router, so its customers could take part in the NYSE's new Retail Liquidity Program. The
deployment reached seven of eight servers. The eighth still carried Power Peg, code Knight had
stopped using in 2003, and the new release repurposed the very flag that activated it. 212
parent orders became over 4 million executions. Knight lost more than $460 million in 45
minutes.

## Why this episode works

Three independently defensible decisions stacked: keep retired code rather than delete it, reuse
a flag rather than add one, deploy by hand with no second review. Then two more twists most
retellings miss — the system emailed 97 warnings before the open and nobody read them, and the
attempted fix made it worse by spreading the bug from one server to eight.

## Titles
1. **Search-optimised:** The Knight Capital Deployment Failure: How $460M Vanished in 45 Minutes
2. **Curiosity / CTR:** They Deployed to 7 of 8 Servers. It Cost $460 Million.
3. **Punchy (<50 chars):** The $460M Deploy

## Thumbnail
- **Text overlay:** `7 OF 8`
- **Visual subject:** eight sketch server boxes, seven muted, the eighth in the failure accent
  (`pipeline/thumbnail.py --art servers`)

---

## PRIMARY SOURCE

**SEC Administrative Proceeding 34-70694**, *In the Matter of Knight Capital Americas LLC*,
16 October 2013. sec.gov returns HTTP 403 to automated fetches; the identical PDF is served at
`http://www.headlandstech.jp/static/file/34-70694.pdf` and was read in full for this episode.
Paragraph numbers below refer to that document.

## SOURCES — the contract

| Claim | ¶ | Verbatim |
|---|---|---|
| Loss over $460 million in ~45 min | 10 | "Knight's failures resulted in it accumulating an unintended multi-billion dollar portfolio of securities in approximately forty-five minutes on August 1 and, ultimately, Knight lost more than $460 million" |
| Knight ≈10% of US listed equity trading; SMARS ≈1%+ | 11 | "Knight's aggregate trading … generally represented approximately ten percent of all trading in listed U.S. equity securities. SMARS generally represented approximately one percent or more of all trading in listed U.S. equity securities." |
| KCG formed 1 July 2013 | 11 | "Knight was owned by Knight Capital Group, Inc. until July 1, 2013, when that entity and GETCO Holding Company, LLC combined to form KCG Holdings, Inc." |
| RLP due to start 1 Aug 2012; parent/child orders | 12 | "SMARS is an automated, high speed, algorithmic router… receive orders passed from other components of Knight's trading platform ('parent' orders) and then… send one or more representative (or 'child') orders to external venues" |
| **The repurposed flag** | 13 | "The new RLP code also repurposed a flag that was formerly used to activate the Power Peg code. Knight intended to delete the Power Peg code so that when this flag was set to 'yes,' the new RLP functionality—rather than Power Peg—would be engaged." |
| Power Peg still present and callable | 13 | "Despite the lack of use, the Power Peg functionality remained present and callable at the time of the RLP deployment." |
| **The stop condition, and the 2005 move** | 14 | "a cumulative quantity function counted the number of shares of the parent order that had been executed. This feature instructed the code to stop routing child orders after the parent order had been filled completely. In 2003, Knight ceased using the Power Peg functionality. In 2005, Knight moved the tracking of cumulative shares function… to an earlier point in the SMARS code sequence. Knight did not retest the Power Peg code after moving the cumulative quantity function" |
| Deploy began 27 July; 1 of 8 servers missed; no second review | 15 | "Beginning on July 27, 2012, Knight deployed the new RLP code in SMARS in stages… one of Knight's technicians did not copy the new code to one of the eight SMARS computer servers. Knight did not have a second technician review this deployment" |
| Seven correct, eighth triggered Power Peg | 16 | "The seven servers that received the new code processed these orders correctly. However, orders sent with the repurposed flag to the eighth server triggered the defective Power Peg code still present on that server." |
| **The system knew, and did not tell SMARS** | 16 | "Although one part of Knight's order handling system recognized that the parent orders had been filled, this information was not communicated to SMARS." |
| 212 parent orders → 4M executions, 154 stocks, 397M shares | 17 | "For the 212 incoming parent orders that were processed by the defective Power Peg code, SMARS sent millions of child orders, resulting in 4 million executions in 154 stocks for more than 397 million shares in approximately 45 minutes." |
| **The actual positions** | 17 | "Knight inadvertently assumed an approximately $3.5 billion net long position in 80 stocks and an approximately $3.15 billion net short position in 74 stocks. Ultimately, Knight realized a $460 million loss on these positions." |
| Market impact | 18 | "for 75 of the stocks, Knight's executions comprised more than 20 percent of the trading volume and contributed to price moves of greater than five percent." |
| **97 warning emails before the open** | 19 | "beginning at approximately 8:01 a.m. ET, an internal system at Knight generated automated e-mail messages (called 'BNET rejects') that referenced SMARS and identified an error described as 'Power Peg disabled.' Knight's system sent 97 of these e-mail messages to a group of Knight personnel before the 9:30 a.m. market open." |
| Nobody read them | 19 | "Knight did not design these types of messages to be system alerts, and Knight personnel generally did not review them when they were received." |
| The 212 arrived **before** the open, for the opening auction | 21 | "it did not apply to orders—such as the 212 orders described above—that Knight received before the market open and intended to send to participate in the opening auction at the primary listing exchange for the stock." |
| Why it was hard to see | 25 | "PMON relied entirely on human monitoring and did not generate automated alerts regarding the firm's financial exposure… PMON experienced delays during high volume events, such as the one experienced on August 1, resulting in reports that were inaccurate." |
| **The fix that made it worse** | 27 | "In one of its attempts to address the problem, Knight uninstalled the new RLP code from the seven servers where it had been deployed correctly. This action worsened the problem, causing additional incoming parent orders to activate the Power Peg code that was present on those servers, similar to what had already occurred on the eighth server." |

### Secondary — aftermath only, never a headline metric
| Claim | Source | Verbatim |
|---|---|---|
| $440M pre-tax loss (Knight's own figure) | [Wikipedia](https://en.wikipedia.org/wiki/Knight_Capital_Group) | "Knight Capital took a pre-tax loss of $440 million." |
| $400M rescue, 5 Aug 2012, led by Jefferies | ibid. | "On August 5, the company raised around $400 million from half a dozen investors led by Jefferies" |
| 75% of equity value erased **by the next day** | ibid. | "by the next day 75 percent of Knight's equity value had been erased" |
| $12M SEC penalty | [WilmerHale](https://www.wilmerhale.com/en/insights/client-alerts/knight-capital-settles-rule-15c3-5-violations-with-sec-agrees-to-pay-12-million) | "agreed to pay $12 million to settle charges" |
| *Teaser:* Cloudflare, 80% of traffic, 27 minutes | [Cloudflare](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/) | "we had lost 80% of our traffic"; "The outage was 27 minutes" |

## Corrections applied after review

- **"When the market opened, Knight received 212 small retail orders" was wrong.** ¶21 places
  their receipt *before* the open, queued for the opening auction. Fixed.
- **The 75% equity figure was in the hook, phrased as if it happened inside the 45 minutes.**
  It is a next-day figure from a secondary source. Moved to the takeaway and phrased to source.
- **Three details previously cut as unverified are in the primary order** and are now restored
  with citations: the 97 BNET reject emails (¶19), the rollback that spread Power Peg to all
  eight servers (¶27), and the 27 July deploy start (¶15).
- **"Power Peg written in 2003" was wrong** — ¶14 says 2003 is when Knight *ceased using* it.
- **"Several billion in unwanted positions" was attributed on screen to the SEC** but the wording
  was WilmerHale's. Replaced with the SEC's own ¶17 figures: $3.5bn net long, $3.15bn net short.

## ⚠ Unverified — do not use

- **"The deploy script failed silently when an SSH connection failed."** A reconstruction in
  [Speculative Branches](https://specbranch.com/posts/knight-capital/), not in the order. ¶15
  says only that a technician did not copy the code. Cut.
