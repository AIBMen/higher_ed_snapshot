import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup

from .plot_structures import THEME, GENDER_SPLIT_SCALE, GRADUATION_RATE_SCALE, ACCEPTANCE_RATE_SCALE, EARNINGS_SCALE
from .utils import CleanForPlot
from .earnings import Earnings

'''
MultiMap: a Plotly Scattergeo object with multiple frames for different higher ed variables
- Male Admissions Share
- Male Enrollment Share (by level)
- Male Graduation Rate (by level)
- Male Degree Share (by level)
- Male Earnings
'''

'''
SET PLOT THEME
'''
pio.templates['THEME'] = THEME
pio.templates.default='THEME'

'''
Dict for configuring each frame
'''
MM_MAP = {
    # admissions
    'admissions': {
        'outcome_var': {
            # outcome_var[nm][0] = outcome_var_name, outcome_var[nm][1] = outcome_var_label, outcome_var[nm][2] = marker_color
            'admit_rate': ['accept_rate_men','<b>Male Acceptance Rate</b><br>',ACCEPTANCE_RATE_SCALE],
            'admit_share': ['men_admitted_share','<b>Male Share of Acceptances</b><br>',GENDER_SPLIT_SCALE]
        },
        # sizing[0] = sizing_var, sizing[2] is the df[sizing_var].apply() function
        'sizing': ['tot_enrolled',lambda x: np.median([8,x/300,30])],
        # sizing cutoff for schools to show
        'sizing_cutoff': 500,
        # specification[specification] = spec label name
        'specification': {},
        'hover_text': ('<b><u>{name}</u></b><br>' +
                        '(<i>{city}, {state}</i>)<br>' +
                        'In {rec_yr}, <b>{men_app} men</b> applied to {name},<br>' +
                        'and <b>{men_accepted} men</b>, or <b>{men_accept_rate}%</b> were admitted. In comparison,<br>' +
                        '<b>{women_accept_rate}%</b> of female applicants were accepted. Men made up<br>' +
                        '<b>{men_apply_share}%</b> of total applicants, and <b>{men_accept_share}%</b> of total admittees.<br><br>' +
                        '<b><u>Male Acceptance Rates</u></b>:<br>' +
                        '<b>{year0}</b>: {year0_rate}%<br>' +
                        '<b>{year1}</b>: {year1_rate}%<br>' +
                        '<b>{year2}</b>: {year2_rate}%<br>')
    },
    # enrollment
    'enrollment': {
        'outcome_var': {
            'male_enrollment_share': ['totmen_share','<b>Male Enrollment Share</b><br>({})',GENDER_SPLIT_SCALE],
        },
        'sizing': ['tot',lambda x: np.median([8,x/750,30])],
        'sizing_cutoff': 2000,
        'specification': {'undergrad': 'Undergraduate','grad': 'Graduate'},
        'hover_text': ('<b><u>{name}</u></b><br>' +
                        '(<i>{city}, {state}</i>)<br>' +
                        'In {rec_yr}, <b>{totmen} men</b> and <b>{totwomen} women</b> were<br>' +
                        'enrolled at {name}, meaning that<br>' +
                        'men made made up <b>{totmen_share}%</b> of total enrollment.<br><br>' +
                        '<b><u>Male Graduation Rates</u></b>:<br>' +
                        '<b>{year0}</b>: {year0_rate}%<br>' +
                        '<b>{year1}</b>: {year1_rate}%<br>' +
                        '<b>{year2}</b>: {year2_rate}%<br>' +
                        '<b>{year3}</b>: {year3_rate}%<br>')
    },
    # graduation
    'graduation': {
        'outcome_var': {
            'male_graduation_rate': ['gradrate_totmen','<b>Male Graduation Rate</b><br>({})',GRADUATION_RATE_SCALE],
        },
        'sizing': ['tot',lambda x: np.median([8,x/200,30])],
        'sizing_cutoff': 100,
        'specification': {'assc': "Associate's",'bach': "Bachelor's"},
        'hover_text': ('<b><u>{name}</u></b><br>' +
                        '(<i>{city}, {state}</i>)<br>' +
                        'By {rec_yr}, <b>{men_grad} men</b> who entered in {rec_yr_lag} had<br>' +
                        'graduated from {name}.<br>' +
                        'The male graduation rate in this cohort was <b>{male_grad_rate}%</b> and<br>' +
                        'the female graduation rate was <b>{female_grad_rate}%</b>. This means the<br>' +
                        'difference in graduation rates was <b>{diff_grad}</b> percentage points.<br><br>' +
                        '<b><u>Male Graduation Rates</u></b>:<br>' +
                        '<b>{year0}</b>: {year0_rate}%<br>' +
                        '<b>{year1}</b>: {year1_rate}%<br>' +
                        '<b>{year2}</b>: {year2_rate}%<br>')
    },
    # earnings
    'earnings': {
        'outcome_var': {
            'median': ['median','<b>Male Median Earnings</b><br>(6 Years After Enroll)',EARNINGS_SCALE],
            'mean': ['mean','<b>Male Mean Earnings</b><br>(6 Years After Enroll)',EARNINGS_SCALE]
        },
        'sizing': ['tot_enrolled',lambda x: np.median([8,x/300,30])], # we'll be merging with admissions
        'sizing_cutoff': 500,
        'specification': {},
        'hover_text': ('<b><u>{name}</u></b><br>' +
                        '(<i>{city}, {state}</i>)<br>' +
                        'For students who first enrolled at {name}<br>' +
                        'in 2013-2015, the <b>{spec} male student</b> was earning <b>${male_earn}</b><br>' +
                        'six years later, and the <b>{spec} female student</b> was earning<br>'
                        '<b>${female_earn}</b> (in 2025 dollars). This means the difference in<br>' +
                        'earnings was <b>${diff_earn}</b>.')
    }
}


class MultiMap:
    '''multiple higher ed outcomes, all on one map'''
    def __init__(self,most_recent_year):
        '''MultiMap
        
        :param most_recent_year:
         (*int*) most recent year available of data
        '''
        self.most_recent_year = most_recent_year
        self.frames = []
        self.fig = go.Figure()
    
    def data_viz(self,render='browser'):
        '''plots current figure.
        
        :param render: form of rendering. Options include:<br>
         ['plotly_mimetype', 'jupyterlab', 'nteract', 'vscode',
         'notebook', 'notebook_connected', 'kaggle', 'azure', 'colab',
         'cocalc', 'databricks', 'json', 'png', 'jpeg', 'jpg', 'svg',
         'pdf', 'browser', 'firefox', 'chrome', 'chromium', 'iframe',
         'iframe_connected', 'sphinx_gallery', 'sphinx_gallery_png']
        '''
        self.fig.show(renderer=render) # shows the plot
    
    def viz_to_html(self,fpath='',add_search_bar=True):
        '''converts current data viz to html
        
        :param fpath: output path for html file
        :param add_search_bar: bool that, when True, adds search bar to plot
        '''
        raw_plot = self.fig
        if add_search_bar:
            html_plot = pio.to_html(fig = raw_plot,
                                    auto_play=False,
                                   include_plotlyjs='cdn',
                                   full_html=True,
                                   config={'responsive': True})
            soup = BeautifulSoup(html_plot,'html.parser')
            # adding search box
            search_box = '''
                         <div style="position:absolute; top:100px; right:23.5px; z-index:1000;">
                        <input type="text" id="searchBox" placeholder="Search a school, then zoom in" style="padding:5px; width:200px;">
                        </div>
                         '''
            soup.body.insert(0, BeautifulSoup(search_box,'html.parser')) # add box
            # get unique plot id
            plot_id = soup.find('div',class_='plotly-graph-div')['id']
            # Add search query opacity update
            search_script = f'''
                            <script>
                            const plotId = "{plot_id}";
                            const input  = document.getElementById("searchBox");
                            const plotEl = document.getElementById(plotId);

                            const frames = plotEl.frames || plotEl._fullFrames || [];

                            input.addEventListener("input", function() {{
                                const q = this.value.toLowerCase();
                            
                                plotEl.data.forEach((trace, i) => {{
                                    
                                if (!trace.text) return;
                                const newOpacity = trace.text.map(txt =>
                                    txt.toLowerCase().includes(q) ? 0.7 : 0.05
                                );
                                Plotly.restyle(plotEl, {{
                                    "marker.opacity": [ newOpacity ]
                                }}, [ i ]);
                                }});
                            }});
                            </script>
                            '''

            soup.body.append(BeautifulSoup(search_script,'html.parser'))
            with open(fpath,'w') as plotf:
                plotf.write(str(soup))
        else:
            raw_plot.write_html(file=fpath,auto_play=False,include_plotlyjs='cdn')

    def _get_obj(self,subject='enrollment',years=None,poplimit=0,**kwargs)->pd.DataFrame:
        '''returns pandas dataframe of requested data
        
        :param subject: IPEDS data subject string; e.g., 'enrollment'
        :param years: range of years (iter), or sinlge year (int)
        :param poplimit: population limiter for visualization.
        :param kwargs: kwargs to pass on to CleanForPlot, like merge_with_char = True
        '''
        obj = CleanForPlot(subject=subject,years=years,poplimit=poplimit)._run_data(**kwargs)
        return obj

    def build_frame(self,
                    subject=None,
                    specification=None,
                    outcome_var=None,
                    rm_disk=False)->go.Frame:
        '''build frame of male higher ed variable
        
        :param subject: frame subject.
        :param specification: within-subject specification.
        :param outcome_var: variable used for marker colors. 
        :rm_disk: boolean to determine if raw data should be removed from disk when frame is finished building
        '''
        # SET CONST
        sbjct_cfg = MM_MAP[subject]

        outcome_var_cfg = sbjct_cfg['outcome_var'][outcome_var]
        var_alias = outcome_var_cfg[0]
        var_colorscale = outcome_var_cfg[2]

        sizing_cfg = sbjct_cfg['sizing']
        sizing_var = sizing_cfg[0]
        sizing_func = sizing_cfg[1]
        sizing_cutoff = sbjct_cfg['sizing_cutoff']

        hover_temp = sbjct_cfg['hover_text']

        spec_cfg = sbjct_cfg['specification']
        if len(spec_cfg.keys()) > 0:
            spec_label = spec_cfg[specification]
        var_label = outcome_var_cfg[1].format(spec_label) if specification is not None else outcome_var_cfg[1]

        # LOAD IN DATA
        # kwargs set
        kwrgs = {
            'merge_with_char': True,
            'rm_disk': rm_disk
        }
        if subject == 'enrollment':
            kwrgs['student_level'] = specification
        elif subject == 'graduation':
            kwrgs['degree_level'] = specification
        else:
            None
        # years to iterate, needed for hover label
        if subject in ['admissions','graduation']:
            years_iter = [self.most_recent_year - 20,self.most_recent_year - 10,self.most_recent_year]
        elif subject in ['enrollment','completion']:
            years_iter = [self.most_recent_year - 30,self.most_recent_year - 20,self.most_recent_year-10,self.most_recent_year]
        
        # GET DATA
        # all years
        df_tot = self._get_obj(subject=subject,
                           years=years_iter,
                           poplimit=0,
                           **kwrgs)
        # most recent year
        df = df_tot.loc[df_tot['year']==self.most_recent_year].query('latitude.notnull() and longitude.notnull()').copy()
        # set tots for grad and enrollment
        if subject in ['enrollment','graduation']:
            df['tot'] = df['totmen'] + df['totwomen']
        # filter out those below a certain size
        df = df.loc[df[sizing_var] >= sizing_cutoff]
        # outcome var
        df['outcome_var'] = df[var_alias]
        df_tot['outcome_var'] = df_tot[var_alias]
        df = df.loc[df['outcome_var'].notnull()] # ensure outcome_var is known
        df_tot = df_tot.loc[df_tot['outcome_var'].notnull()] # ensure outcome_var is known

        # HOVER LABEL
        # get all ids
        all_ids = df['id'].unique()
        text_dict = {id_: ['NA']*len(years_iter) for id_ in all_ids}
        for id_ in text_dict.keys():
            temp_df = df_tot.loc[df_tot['id']==id_]
            ctr = 0
            for yr in years_iter:
                v = temp_df.loc[temp_df['year']==yr, 'outcome_var']
                if len(v) == 0:
                    obs = 'NA'
                else:
                    obs = np.float64(v)
                text_dict[id_][ctr] = obs # add to dict
                ctr+=1
        # build hover text
        hovertext_arr = []
        for i_,r in df.iterrows():
            yr = self.most_recent_year
            nm = r['name']
            cty = r['city']
            st = r['state']
            v_map = text_dict[r['id']]
            if subject == 'admissions':
                hvtxt = hover_temp.format(
                    rec_yr=yr, name=nm, city=cty, state=st,
                    men_app=int(r['men_applied']), men_accepted=int(r['men_admitted']), men_accept_rate=round(r['accept_rate_men'],1),
                    women_accept_rate=round(r['accept_rate_women'],1), men_accept_share=round(r['men_admitted_share'],1), men_apply_share=round(r['men_applied_share'],1),
                    year0 = years_iter[0], year1 = years_iter[1], year2 = years_iter[2],
                    year0_rate = round(v_map[0],1) if isinstance(v_map[0],np.float64) else v_map[0],
                    year1_rate = round(v_map[1],1) if isinstance(v_map[1],np.float64) else v_map[1], 
                    year2_rate = round(v_map[2],1) if isinstance(v_map[2],np.float64) else v_map[2]
                )
            elif subject == 'enrollment':
                hvtxt = hover_temp.format(
                    rec_yr=yr, name=nm, city=cty, state=st,
                    totmen = int(r['totmen']), totwomen = int(r['totwomen']),
                    totmen_share = round(r['totmen_share'],1),
                    year0 = years_iter[0], year1 = years_iter[1], year2 = years_iter[2], year3 = years_iter[3],
                    year0_rate = round(v_map[0],1) if isinstance(v_map[0],np.float64) else v_map[0],
                    year1_rate = round(v_map[1],1) if isinstance(v_map[1],np.float64) else v_map[1], 
                    year2_rate = round(v_map[2],1) if isinstance(v_map[2],np.float64) else v_map[2],
                    year3_rate = round(v_map[3],1) if isinstance(v_map[2],np.float64) else v_map[3]
                )
            elif subject == 'graduation':
                yr_lag = yr - 6 if specification == 'bach' else yr - 3
                hvtxt = hover_temp.format(
                    rec_yr=yr, name=nm, city=cty, state=st, rec_yr_lag = yr_lag,
                    men_grad = int(r['totmen_graduated']),
                    male_grad_rate = round(r['gradrate_totmen'],1), female_grad_rate = round(r['gradrate_totwomen'],1),
                    diff_grad = round(r['gradrate_totmen'] - r['gradrate_totwomen'],1),
                    year0 = years_iter[0], year1 = years_iter[1], year2 = years_iter[2],
                    year0_rate = round(v_map[0],1) if isinstance(v_map[0],np.float64) else v_map[0],
                    year1_rate = round(v_map[1],1) if isinstance(v_map[1],np.float64) else v_map[1], 
                    year2_rate = round(v_map[2],1) if isinstance(v_map[2],np.float64) else v_map[2]
                )
            else:
                hvtxt = 'TO DO'
            hovertext_arr.append(hvtxt)
        # color bar
        # find weighted median of the marker var
        wtmed = int(np.median(
            np.sum(df['outcome_var'] * df[sizing_var]) / np.sum(df[sizing_var])
        ))
        bar_vals = [i for i in sorted([0,25,50,75,100,wtmed])]
        bar_text = {i: f'<b>Median ({i}%)' if i == wtmed else f'{i}%' for i in bar_vals}
        # BUILD DAT
        # scattergeo dat
        frm_dat= go.Scattergeo(
            locationmode='USA-states',
            lat=df['latitude'],
            lon=df['longitude'],
            text=hovertext_arr,
            hovertemplate='%{text}<extra></extra>',
            marker={
                'size': df[sizing_var].apply(sizing_func).round(1),
                'color': df['outcome_var'].round(1),
                'colorscale': var_colorscale,
                'colorbar': {'title': var_label,
                             'tickmode': 'array',
                             'tickvals': bar_vals,
                             'labelalias': bar_text,
                             'ticklen': 5,
                             'len': .6,
                             'x': 1,
                             'y': .9,
                             'xanchor': 'left',
                             'yanchor': 'top'},
                'opacity': .7,
                'line_color': 'black',
                'sizemode': 'diameter'
            }
        )
        # frame
        sbttl = re.sub(r'\<br\>',' <b>', var_label)
        frm = go.Frame(data=frm_dat,
                       name=var_label,
                       layout=go.Layout(title={'subtitle': {'text': f'Currently viewing: <b>{sbttl}'}}, 
                                        hoverlabel={'bgcolor': '#ffffff',
                                                    'align': 'left',
                                                    'bordercolor': 'black',
                                                    'font': {'color': '#1e4a4a'}},
                                        showlegend=False,
                                        margin={sd:95 if sd=='t' else 0 for sd in ['pad','l','r','t','b']})
                                        )
        self.frames.append(frm)
    
    def build_earnings_frame(self,
                            api_key = '',
                            outcome_var=None,
                            inflation_adjust=125.58)->go.Frame:
        '''build frame of earnings

        :api_key: College Scorecard API key string
        :param outcome_var: variable used for marker colors. Options include mean, median
        :param inflation_adjust: the PCE index for the most recent year. This will be divided
                                 by the 2022 index to bring 2022 estimates to modern dollars
        '''
        # SET CONST
        sbjct_cfg = MM_MAP['earnings']

        outcome_var_cfg = sbjct_cfg['outcome_var'][outcome_var]
        var_alias = outcome_var_cfg[0]
        var_label = outcome_var_cfg[1]
        var_colorscale = outcome_var_cfg[2]

        sizing_cfg = sbjct_cfg['sizing']
        sizing_var = sizing_cfg[0]
        sizing_func = sizing_cfg[1]
        sizing_cutoff = sbjct_cfg['sizing_cutoff']

        hover_temp = sbjct_cfg['hover_text']
        
        # LOAD IN DATA
        # earnings dat
        earn = Earnings(api_key=api_key)
        earn.get_wages(wage_var=outcome_var,poplimit=sizing_cutoff)
        dat = earn.earnings_dat
        male_earn_map = {id_:dat[id_][0] for id_ in dat.keys()} # male earnings
        female_earn_map = {id_:dat[id_][1] for id_ in dat.keys()} # female earnings
        # load admissions dat to map, known lon/lat
        df = self._get_obj(subject='admissions',
                           years=self.most_recent_year,
                           poplimit=0,
                           merge_with_char=True,
                           rm_disk=False).query('latitude.notnull() and longitude.notnull()')
        # filter out those below a size
        df = df.loc[df[sizing_var] >= sizing_cutoff]
        # MAP earnings
        df['male_earn'] = df['id'].map(male_earn_map)
        df['female_earn'] = df['id'].map(female_earn_map)
        # filter out those with unknown male earnings
        df = df.loc[df['male_earn'].notnull()]
        # INFLATION ADJUST, DATA ARE INFLATION ADJUSTED TO 2022 DOLLARS, NEED TO UPDATE TO 2025
        # We'll use the 2025 first quarter PCE
        # calculation is earnings * (125.58 / 116.11)
        df['male_earn'] = df['male_earn'] * (inflation_adjust / 116.11)
        df['female_earn'] = df['female_earn'] * (inflation_adjust / 116.11)

        # HOVER LABELS
        hovertext_arr = []
        for i_,r in df.iterrows():
            nm = r['name']
            cty = r['city']
            st = r['state']
            hvtxt = hover_temp.format(
                name=nm, city=cty, state=st,spec=var_alias,
                male_earn=int(r['male_earn']),
                female_earn=int(r['female_earn']) if r['female_earn'] is not None else 'NA',
                diff_earn=(int(r['male_earn'] - r['female_earn']))
            )
            hovertext_arr.append(hvtxt)
        #color bar and marker color
        # in order for this multiframe plot to work, we need to have all frames set between 0,100
        # due to some outliers, we'll first take the natural log, then normalize to 0,100
        df['male_earn_ln'] = df['male_earn'].apply(np.log)
        # now normalize
        male_earn_max = df['male_earn_ln'].max() 
        male_earn_min = df['male_earn_ln'].min()
        male_earn_diff = male_earn_max - male_earn_min
        df['male_earn_norm'] = 100 * (
            (df['male_earn_ln'] - male_earn_min) / male_earn_diff
        )
        # now we need to reverse-engineer the quarterly numbers for our labels
        reverse_norm = lambda x: np.exp((x/100 * male_earn_diff) + male_earn_min)
        # now we can add the median ticker
        med_wage = int(np.median(
            np.sum(df['male_earn'] * df[sizing_var]) / np.sum(df[sizing_var])
        ))
        # then, ln and normalize it
        med_wage_norm = 100 * (
            (np.log(med_wage) - male_earn_min) / male_earn_diff
        )
        # f'<b> Median (${med_wage//1000 * 1000})' if i == med_wage_norm else
        bar_vals = [i for i in sorted([0,25,50,75,99])]
        bar_text = {i: f'${int(reverse_norm(i)//1000 * 1000)}' for i in bar_vals}

        print(f'earnings, None: {len(df)}')
        # BUILD DAT
        # scattergeo dat
        frm_dat= go.Scattergeo(
            locationmode='USA-states',
            lat=df['latitude'],
            lon=df['longitude'],
            text=hovertext_arr,
            hovertemplate='%{text}<extra></extra>',
            marker={
                'size': df[sizing_var].apply(sizing_func).round(1),
                'color': df['male_earn_norm'],
                'colorscale': var_colorscale,
                'colorbar': {'title': var_label,
                             'tickmode': 'array',
                             'tickvals': bar_vals,
                             'labelalias': bar_text,
                             'ticklen': 5,
                             'len': .6,
                             'x': 1,
                             'y': .9,
                             'xanchor': 'left',
                             'yanchor': 'top'},
                'opacity': .7,
                'line_color': 'black',
                'sizemode': 'diameter'
            }
        )
        # frame
        sbttl = re.sub(r'\<br\>',' <b>', var_label)
        frm = go.Frame(data=frm_dat,
                       name=var_label,
                       layout=go.Layout(title={'subtitle': {'text': f'Currently viewing: <b>{sbttl}'}}, 
                                        hoverlabel={'bgcolor': '#ffffff',
                                                    'align': 'left',
                                                    'bordercolor': 'black',
                                                    'font': {'color': '#1e4a4a'}},
                                        showlegend=False,
                                        margin={sd:50 if sd=='t' else 0 for sd in ['pad','l','r','t','b']}))
        self.frames.append(frm)
    
    def build_multimap(self,
                       title='',
                       notes=''):
        '''build multimap plot based on stored frames'''
        # CREATE BUTTON DROPDOWN
        tabs = [
            {'method': 'animate',
             'label': frm.name,
             'args': [
                 [frm.name], {'mode': 'immediate',
                              'frame': {'duration': 0, 'redraw': True},
                              'transition': {'duration': 0}}
             ]} for frm in self.frames
        ]
        # create figure
        fig = go.Figure(data=self.frames[0].data,
                        frames=self.frames,
                        layout=self.frames[0].layout)
        # add tabs
        fig.update_layout(updatemenus=[
            {'buttons': tabs,
             'x': .99,
             'y': .95,
             'xanchor': 'left',
             'yanchor': 'top',
             'showactive': True,
             'bgcolor': "#F3F4F3",
             'bordercolor': '#1e4a4a',
             'font': {'color': '#1e4a4a'}}
        ])
        # add text
        fig.update_layout(title={'text': title})
        fig.add_annotation(text=notes,
                       showarrow=False,
                       align='right',
                       x=1,
                       xanchor='left',
                       yanchor='top',
                       y=.29)
        
        # update attr
        self.fig = fig

def build_map(most_recent_year=2023,
              collescorecard_key='',
              inflation_adjust=None,
              map_title='',
              map_notes='',
              fpath=''):
    '''builds map, downloads html to disk
    
    :param most_recent_year: most recent year of data available
    :param collegescorecard_key: College Scorecard API key string
    :param inflation_adjust: PCE inflation index, pegged at 2017, for the most recent year of data
    :param map_title: title of map
    :param map_notes: map figure notes
    :param fpath: output path for plotly map html
    '''
    mm = MultiMap(most_recent_year=most_recent_year) # init MultiMap

    mm.build_frame(subject='admissions',specification=None, outcome_var='admit_rate') # Admissions 
    mm.build_frame(subject='enrollment',specification='undergrad', outcome_var='male_enrollment_share') # Enrollment (Undergrad)
    mm.build_frame(subject='enrollment',specification='grad', outcome_var='male_enrollment_share') # Enrollment (Grad)
    mm.build_frame(subject='graduation',specification='bach', outcome_var='male_graduation_rate') # Graduation (Bachelor's)
    mm.build_frame(subject='graduation',specification='assc', outcome_var='male_graduation_rate') # Graduation (Associate's)
    mm.build_earnings_frame(api_key=collescorecard_key,outcome_var='median',inflation_adjust=inflation_adjust) # Earnings (6-years after enrollment)

    mm.build_multimap(title=map_title, # build map, title
                      notes=map_notes) # figure note
    
    mm.viz_to_html(fpath=fpath,add_search_bar=True) # convert plotly Figure object to html, add search bar



    
    
    

        
    