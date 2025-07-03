import requests
import us
import json
from typing import Dict, List, Any

'''
In this script, I define the Earnings class, which collects school-level earnings 
data from the College Scorecard.
The Earnings class takes in a College Scorecard API key, which
you can get here: https://collegescorecard.ed.gov/data/api-documentation/ 
It's easy to get.

As of now, only median and mean earnings 6 years after enrollment, 
by gender, are provided. Over time, I may build out the variables offered
'''

# STATES ABBR to KEY MAP
states_dict = us.states.mapping(from_field='abbr',to_field='name')
states_dict['DC'] = 'District of Columbia'
# states_abbr
states_abbr = list(states_dict.keys())

# WAGE VARIABLE MAPPINGS
wage_var_dict = {
    'median': ['latest.earnings.6_yrs_after_entry.median_earnings_male',
               'latest.earnings.6_yrs_after_entry.median_earnings_non_male'],
    'mean': ['latest.earnings.6_yrs_after_entry.mean_earnings.male_students',
             'latest.earnings.6_yrs_after_entry.mean_earnings.female_students']
}

class Earnings:
    '''Earnings data from colleges'''
    def __init__(self,
                 api_key: str = None):
        '''College Scorecard Earnings data.
        
        :param api_key: College Scorecard API key
        '''
        self.api_key = api_key
        self.earnings_dat = None

    def get_wages(self,
                  wage_var: str = 'median',
                  poplimit: int = 300) -> Dict[str,List[str]]:
        '''returns male and female wages for schools, all states, in dict format.

        Format follows...
            {school1_id: [male1_earnings,female1_earnings],
        school2_id: [male2_earnings,female2_earnings]}

        :param var: 
         wage variable to be collected. Can be a list of variables. Options include<br>['mean','median']
        
        :param poplimit: enrollment lower bound. Exact measure is:<br>
         'Enrollment of undergraduate certificate/degree-seeking students'
        '''
        #URL
        base_request = 'https://api.data.gov/ed/collegescorecard/v1/schools.json' # base 
        params = {}

        #PARAMETERS
        # api key
        params['api_key'] = self.api_key
        # variable
        wage_var_nm = wage_var_dict[wage_var]
        v_1 = wage_var_nm[0] # male
        v_2 = wage_var_nm[1] # female
        params['fields'] = f'id,school.name,{v_1},{v_2}' # id, name, male_earn,female_earn
        # poplimit
        params['latest.student.size__range'] = f'{poplimit}..' # range lower bound
        # load max results per page (100)
        RESULTS_PER_PAGE = 100
        params['per_page'] = RESULTS_PER_PAGE 

        # REQUESTS
        wage_data = {} # empty dict, we'll fill
        # request first page twice to check how many pages there'll be
        r = requests.get(base_request,params=params).json()
        num_schools = r['metadata']['total']

        if num_schools <= 100: # no need to iter over pages
            res = r['results']
            pg_dat = {str(schl['id']): (schl[v_1],schl[v_2]) for schl in res} # add entries
            for schl,v in pg_dat.items():
                    if v[0] is not None:
                            wage_data[schl]= v # add entries to main dict

        elif num_schools > 100:
            pgs_to_iter = num_schools // RESULTS_PER_PAGE + 1 # add one to get the final remainder
            for pg_num in range(pgs_to_iter):
                pg_param = params.copy()
                pg_param['page'] = pg_num

                res = requests.get(base_request,params=pg_param).json()['results'] # request dat
                pg_dat = {
                        str(schl['id']): (schl[v_1],schl[v_2]) for schl in res
                    } # add entries
                
                for schl,v in pg_dat.items():
                        if v[0] is not None:
                            wage_data[schl]= v # add entries to main dict
        else:
             raise ValueError('Wrong link? Wrong API key?')

        self.earnings_dat = wage_data

    def earnings_to_json(self, 
                         fpath: str = 'earnings.json') -> None:
         '''converts earnings data to json
         
         :param fpath: file path
         '''
         with open(fpath,'w') as file:
              json.dump(self.earnings_dat,file)
            




    
