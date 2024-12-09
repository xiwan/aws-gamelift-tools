# aws-gamelift-tools
A collection of GameLift tools

## multiple pools

a tool to demostrate how to benchmark the flexmatch service. Now it has serveral features.

+ json configuration
+ dynamically update rulesets and its association with flexmatch configurations
+ All-in-one and seperated rulesets, with side by side benchmark
+ The benchmark is implemented with threading models

### command-line
```
Options:
        -help: Show this help message
        -update: Update rulesets
        -json: Test json config
        -benchmark: Start a benchmark
```
Usually, multi-pools rulesets have timing advantage over the All-in-one ruleset.
```
## benchmark all-in-one:

Matchmaking Monitor for [Radiant-Dire-All] Done!
Complete Tickets: 79, Average Time: 15.03 seconds
Failed Tickets: 7, Average Time: 120.07 seconds

## benchmark multi-pools:

Matchmaking Monitor for [Radiant-Dire-Practice] Done!
Complete Tickets: 80, Average Time: 13.94 seconds
Failed Tickets: 0, Average Time: 0.00 seconds

Matchmaking Monitor for [Radiant-Dire-Classic] Done!
Complete Tickets: 74, Average Time: 14.37 seconds
Failed Tickets: 5, Average Time: 120.14 seconds

Matchmaking Monitor for [Radiant-Dire-Survival] Done!
Complete Tickets: 154, Average Time: 13.58 seconds
Failed Tickets: 2, Average Time: 120.06 seconds

```
