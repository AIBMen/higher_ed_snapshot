from genplot.multimap import build_map
from dotenv import load_dotenv
import os
load_dotenv() # load college scorecard API key to env

'''
Build the map, output to html
'''

# get arguments
# - most recent year of data
# - College Scorecard key
# - most recent year PCE index (pegged at 2017 := 100 index)
# - map title
# - map notes
# - html output path name

# Most recent year of data
most_rec_yr = os.getenv('MOST_RECENT_YEAR')
most_rec_yr = int(most_rec_yr)


# College Scorecard API key
# NAME THE KEY "COLLEGE_SCORECARD_KEY" in your .env file
college_scorecard_key = os.getenv('COLLEGE_SCORECARD_KEY')

# most recent year PCE index
# you can find this here: https://fred.stlouisfed.org/series/pcepi/21
inflation_adjust = os.getenv('INFLATION_ADJUST')
inflation_adjust = float(inflation_adjust)

# Map title
title = os.getenv('MAP_TITLE')

# Map notes
notes = os.getenv('MAP_NOTE')

# HTML output path
out_path = os.getenv('MAP_OUTPATH')
out = os.path.join('docs',out_path)


if __name__=='__main__':
    build_map(most_recent_year=most_rec_yr,
              collescorecard_key=college_scorecard_key,
              inflation_adjust=inflation_adjust,
              map_title=title,
              map_notes=notes,
              fpath=out)