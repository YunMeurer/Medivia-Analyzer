# Medivia Analyzer

Analyzer for gold and exp based of Medivia's Loot.txt file generated by the game client

## How to use
- Enable on Medivia options > console:
Automatically open Loot channel on login
Automatically save loot messages to text file
- Open the program at any time, it will start counting kills and loot from opened monsters froom the time the program is opened onwards, the same for the reset button
- Monsters NEED to be opened to count towards loot and exp

## Features
- Auto loot and exp calculator
- Count loot drops
- Count monster kills
- Session gold/hour and exp/hour, total gold and total exp with graphs
- Exclude monsters and items from the list and that will recalculate the session stats
- Can set custom prices for items that you will sell to players or that don't have a default value
- These custom prices and exclusions are saved even if app is closed in a config file
- Export sessions into a txt file to save, or to see drop rates, WIP
- Clicking with right button will show options to exclude items/monsters or go to the wiki page for the selected item/monster
- Double clicking some fields like price and names on exclude/custom tabs will allow editing directly on the table

## Database
Initially done by Dreamshade. I added all the rest of the monsters and exp values
https://github.com/Dreamshade-1911/dreamloot

Was updated on 241122 and based on Medivia wiki creature page
https://wiki.mediviastats.info/Creatures
Ordered by name