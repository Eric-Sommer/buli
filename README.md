# buli #
Collects and analyzes

- game results
- attendance, Referee, Place and Date of Game
- lineups including subsitutes
- bookings
- goals

of German professional football matches.

## Source ##

Website German football magazine kicker.de

## Scope ##
- Bundesliga (1st Division): Since 1995
- 2.Bundesliga (2nd Division): Since 1997
- 3.Liga (3rd Division): Since 2008

The function `main()` runs through everything. The parameters (e.~g. what is a bad streak/a tough schedule?) are often arbitrary and can be easily adjusted.
1. Crawl infos `crawler()`. TThere is always one file for the matchday and one for each individual match.
2. Produce various stuff on the game result level (`game_analysis()`).
    1. Create a boxplot for each matchday showing the historical distribution of points across the league.
    2. `get_prob_abstieg()` shows for a given team, having given points at after a given matchday, how other teams with these points have fared historically at the end of the season.
    3. `schedule()` tries to investigate whether a tough schedule on the first or last matchdays makes a difference.
    4. `get_streaks()` shows all streaks of five games with no goals scored.
    5. `ewigetabelle()` calculates the cumulated table across all seasons. Not 100% accurate due to points subtracted from the FA.
    6. `aufbaugegner()` lists those teams who have lost frequently against teams in bad shape (defined as having 3 points from the last 5 games prior to their win).
3. `goal_analysis()` counts the top scorers.
4. `clean_booking_data` produces tables with all cards. No analysis here yet.


A special function `create_game_results_since_1963()` collects Bundesliga game results (i.e. without player outcomes) since its 1963 inception and calls `game_analysis()` with these data.




