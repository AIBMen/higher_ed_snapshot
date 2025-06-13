# Snapshot of Higher Education
by Ravan Hawrami for AIBM

`higher_ed_snapshot` is a public repo for creating:

- a map plot of male higher education outcomes.
- a table to query outcomes from.

I use NCES IPEDS (Integrated Postsecondary Education Data System), which hosts a collection of surveys annually conducted on a range of subjects, from finances and admissions to enrollment and graduation. 

Given there's no official API for collecting and cleaning multi-year aggregate results, I made the python package, `genpeds` to accomplish this goal. `genpeds` stands for the:
- [**gen**]dered [**p**]ostsecondary [**e**]ducation [**d**]ata [**s**]atrap

To learn more about using `genpeds` yourself, see the [pypi page here](https://pypi.org/project/genpeds/), and/or the [github repo here](https://github.com/rhawrami/genpeds/).

For plotting, I made a small package, `genplot`, which contains all the plotting and table-making logic we need for our aims.


## How to use/update

### 1. Clone this repo of course!
```bash
git clone git@github.com:AIBMen/higher_ed_snapshot.git
```

### 2. Set up the environment.

First, let's set up a virtual environment.
```bash
python -m venv venv
```
Then, activate (this will vary depending on your OS).
```bash
source venv/bin/activate
```
Now, we'll build our package.
```bash
pip install .
```
After that, you can set up your environmental variables, which the two scripts will be pulling from via `dotenv`. You'll need to have the following variables defined in a `.env` file:
- COLLEGE_SCORECARD_KEY (College Scorecard API key, which you can easily [get here](https://collegescorecard.ed.gov/data/api/))
- MOST_RECENT_YEAR (most recent year of IPEDS data available; as of June 2024, this should be 2023)
- INFLATION_ADJUST (PCE inflation index for the current year, indexed to 100 for 2017; we need to do this as the College Scorecard earnings estimates are stuck at 2022 estimates; you can find this estimate from [BLS FRED here](https://fred.stlouisfed.org/series/pcepi/21))
- MAP_TITLE (title for map)
- MAP_NOTE (notes for map)
- MAP_OUTPATH (file output path for map plot html)
- TABLE_OUTPATH (file output path for data table html)

As I said before, we'll create a `.env` file:
```bash
touch .env
```
And then, we'll add our variables to the file. Your file should look something like this:
```
COLLEGE_SCORECARD_KEY=77777777777777777777

MOST_RECENT_YEAR=2023

INFLATION_ADJUST=125.58

MAP_TITLE=Explore male characteristics and outcomes in higher education

MAP_NOTE=Source: NCES IPEDS &<br>College Scorecard

MAP_OUTPATH=HigherEdMap.html

TABLE_OUTPATH=HigherEdTable.html
```

### 3. Get the plots

Now you can just run the two scripts, and you'll have your map and table.
```bash
python scripts/build_map.py
```
```bash
python scripts/build_table.py
```

