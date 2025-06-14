import pandas as pd
import plotly.graph_objects as go
from genpeds import Admissions, Enrollment, Completion, Graduation

'''
In this module, we define the CleanForPlot class,
which will abstract away some of the necessary data cleaning.
'''

'''
This dictionary provides the data necessary to create the dataframes needed for our plots.
- cls: the subject data class
- poplimit_eval_var: string to feed into pd.DataFrame().eval(), to filter by population-floor
- cols_to_keep: cols needed for final plots
'''
PLOTS_DICT = {
    'admissions': {
        'cls': Admissions,
        'poplimit_eval_var': 'pop_4_cutoff = tot_enrolled',
        'cols_to_keep': ['year','id','name','city','state','latitude','longitude',
                         'tot_enrolled','men_enrolled', 'men_admitted',
                         'men_applied', 'men_applied_share', 'men_admitted_share',
                         'accept_rate_men','accept_rate_women',
                         'yield_rate_men','yield_rate_women',
                         'sat_rw_25','sat_rw_75','sat_math_25','sat_math_75',
                         'act_eng_25','act_eng_75','act_math_25','act_math_75',
                         'act_comp_25','act_comp_75']
    },

    'enrollment': {
        'cls': Enrollment,
        'poplimit_eval_var': 'pop_4_cutoff = totmen + totwomen',
        'cols_to_keep': ['year','id','name','city','state','studentlevel','latitude','longitude',
                         'totmen','totwomen','totmen_share',
                         'wtmen','wtwomen','bkmen','bkwomen',
                         'asnmen','asnwomen','hspmen','hspwomen']
    },

    'completion': {
        'cls': Completion,
        'poplimit_eval_var': 'pop_4_cutoff = totmen + totwomen',
        'cols_to_keep': ['year','id','name','city','state','deglevel','latitude','longitude',
                         'cip','cip_description',
                         'totmen','totwomen','totmen_share',
                         'wtmen','wtwomen','bkmen','bkwomen',
                         'asnmen','asnwomen','hspmen','hspwomen']
    },

    'graduation': {
        'cls': Graduation,
        'poplimit_eval_var': 'pop_4_cutoff = totmen + totwomen',
        'cols_to_keep': ['year','id','name','city','state','deglevel','latitude','longitude',
                         'totmen','totwomen', 'totmen_graduated', 'totwomen_graduated',
                         'wtmen','wtwomen','bkmen','bkwomen',
                         'asnmen','asnwomen','hspmen','hspwomen',
                         'gradrate_totmen','gradrate_totwomen',
                         'gradrate_wtmen','gradrate_wtwomen',
                         'gradrate_bkmen','gradrate_bkwomen',
                         'gradrate_asnmen','gradrate_asnwomen',
                         'gradrate_hspmen','gradrate_hspwomen']
    }
}

'''
CleanForPlot provides the data cleaning necessary for our final plots.
It takes in a subject string, includes ['admissions','enrollment','completion','graduation'].
It takes in an inclusive year range in tuple form, or a single year
'''
class CleanForPlot:
    '''Data cleaning for plots.'''
    def __init__(self,subject,years,poplimit):
        '''Data cleaning for plots.
        
        :param subject::
         (*str*) plot subject. options include:<br>['admissions','enrollment','completion','graduation']
        
        :param years::
         (*tuple* or *int*) year range or single year. ranges available vary by subject.
        
        :param poplimit::
         (*int*) population limit for schools to be included. populations include both men and women.
        '''
        self.subject = subject
        self.years = years
        self.poplimit = poplimit
        
        self.plot_dict = PLOTS_DICT[self.subject]
        self.cls = self.plot_dict['cls']
        self.c2k = self.plot_dict['cols_to_keep']
        self.viz = go.Figure()
    
    def _run_data(self,**kwargs) -> pd.DataFrame:
        '''runs data, limits data by poplimit, and returns dataframe for a subject.
        
        **kwargs are passed onto the  'run' method for each class. 
        '''
        df = self.cls(self.years).run(**kwargs) # get dat

        # poplimit cutoff, based on most recent year, 
        # and simultaneously filter to schools present in most recent year
        if isinstance(self.years,tuple):
            start,end = self.years
        elif isinstance(self.years,list):
            start,end = sorted(self.years)[0],sorted(self.years)[-1]
        elif isinstance(self.years,int):
            end = self.years
        else:
            raise TypeError('years param should be int or tuple.')
        df = df.eval(self.plot_dict['poplimit_eval_var']) # create number to condition poplimit on
        ids_to_include = df.loc[(df['year'] == end) &
                                (df['pop_4_cutoff'] >= self.poplimit), 'id'].unique()
        df = df.loc[df['id'].isin(ids_to_include)] # filter cols

        # return data, with cols to keep
        # some cols may not be in specified dataset though, ie. lon
        cols2keep = [col for col in self.c2k if col in df.columns]
        return df.loc[:, cols2keep]    

    def data_viz(self,render='browser'):
        '''plots current figure.
        
        :param render: form of rendering. Options include:<br>
         ['plotly_mimetype', 'jupyterlab', 'nteract', 'vscode',
         'notebook', 'notebook_connected', 'kaggle', 'azure', 'colab',
         'cocalc', 'databricks', 'json', 'png', 'jpeg', 'jpg', 'svg',
         'pdf', 'browser', 'firefox', 'chrome', 'chromium', 'iframe',
         'iframe_connected', 'sphinx_gallery', 'sphinx_gallery_png']
        '''
        self.viz.show(renderer=render) # shows the plot
