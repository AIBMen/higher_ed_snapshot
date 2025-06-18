from .utils import CleanForPlot, int_value_handler
from .earnings import Earnings

'''
In this module, we'll build our data table,
using the (aptly named) DataTable Javascript library
'''

COLS2KEEP = {
    'admissions': {
        'name': 'School','year': 'Year','id': 'ID','city': 'City','state': 'State',
        'tot_enrolled': 'FirstYearEnroll','men_enrolled': 'FirstYearMaleEnroll', 'men_admitted': 'MaleAdmittees',
        'men_applied': 'MaleApplicants', 'men_applied_share': 'MaleApplicantShare', 'men_admitted_share': 'MaleAdmitShare',
        'accept_rate_men': 'MaleAdmitRate','accept_rate_women': 'FemaleAdmitRate',
        'yield_rate_men': 'MaleYieldRate','yield_rate_women': 'FemaleYieldRate',
    },
    'enrollment_U': {
        'name': 'School','year': 'Year','id': 'ID','city': 'City','state': 'State',
        'totmen':'MaleEnrollment','totwomen':'FemaleEnrollment',
        'totmen_share':'MaleEnrollShare'
    },
    'enrollment_G': {
        'name': 'School','year': 'Year','id': 'ID','city': 'City','state': 'State',
        'totmen':'MaleEnrollment','totwomen':'FemaleEnrollment',
        'totmen_share':'MaleEnrollShare'
    },
    'graduation_assc': {
        'name': 'School','year': 'Year','id': 'ID','city': 'City','state': 'State',
        'totmen': 'MaleCohort','totwomen': 'FemaleCohort', 
        'totmen_graduated': 'MaleGrads', 'totwomen_graduated': 'FemaleGrads',
        'gradrate_totmen':'MaleGradRate','gradrate_totwomen': 'FemaleGradRate',
    },
    'graduation_bach': {
        'name': 'School','year': 'Year','id': 'ID','city': 'City','state': 'State',
        'totmen': 'MaleCohort','totwomen': 'FemaleCohort', 
        'totmen_graduated': 'MaleGrads', 'totwomen_graduated': 'FemaleGrads',
        'gradrate_totmen':'MaleGradRate','gradrate_totwomen': 'FemaleGradRate',
    }
}


'''
EdDataTable uses DataTables JS to make 
a queryable table of NCES IPEDS data
'''
class EdDataTable:
    '''Higher Ed Data Table'''
    def __init__(self,most_recent_year):
        '''JS DataTable
        
        :param most_recent_year: most recent year of data available
        '''
        self.most_recent_year = most_recent_year
        self.dataframes = {}

    def generate_df(self,
                    earnings_api_key='COLLEGE_SCORECARD_KEY',
                    inflation_adjust=125.58):
        '''generates higher ed dataframe 
        
        :param earnings_api_key: College Scorecard API key string.
        :param inflation_adjust: the PCE index for the most recent year. This will be divided
                                 by the 2022 index to bring 2022 estimates to modern dollars
        '''
        rcyr = self.most_recent_year
        #init objs
        cfg = {
            'admissions': {'sbj': 'admissions','kwrgs': {'see_progress': False},
                           'yrs': [rcyr-20,rcyr-10,rcyr]},
            'enrollment_U': {'sbj': 'enrollment','kwrgs': {'student_level': 'undergrad'},
                             'yrs': [rcyr-30,rcyr-20,rcyr-10,rcyr]},
            'enrollment_G': {'sbj': 'enrollment','kwrgs': {'student_level': 'grad'},
                             'yrs': [rcyr-30,rcyr-20,rcyr-10,rcyr]},
            'graduation_assc': {'sbj': 'graduation','kwrgs': {'degree_level': 'assc'},
                                'yrs': [rcyr-20,rcyr-10,rcyr]},
            'graduation_bach': {'sbj': 'graduation','kwrgs': {'degree_level': 'bach'},
                                'yrs': [rcyr-20,rcyr-10,rcyr]}
        }
        general_kwrgs = {'rm_disk': False,'merge_with_char': True}
        # get dat
        for i in cfg.keys():
            i_cfg = cfg[i]
            df = CleanForPlot(subject=i_cfg['sbj'],
                             years=i_cfg['yrs'],
                             poplimit=500)._run_data(**i_cfg['kwrgs'],
                                                   **general_kwrgs)
            df = df.reindex(columns=COLS2KEEP[i].keys())
            df = df.rename(columns=COLS2KEEP[i])
            for col in df.columns:
                if col not in ['Year','ID','School','City','State']:
                    df[col] = df[col].apply(int_value_handler)
                    if 'Share' in col or 'Rate' in col:
                        df[col] = df[col].astype(str) + '%'
            df = df.sort_values(by='Year',ignore_index=True)
            self.dataframes[i] = df.drop_duplicates()
        # add earnings now
        earn = Earnings(api_key=earnings_api_key)
        earn.get_wages(wage_var='median',poplimit=500)
        dat = earn.earnings_dat
        male_earn_map = {id_:dat[id_][0] for id_ in dat.keys()} # male earnings
        female_earn_map = {id_:dat[id_][1] for id_ in dat.keys()} # female earnings
        earn_df = CleanForPlot(subject='admissions',
                               years=self.most_recent_year,poplimit=0)._run_data(merge_with_char=True,
                                                                      rm_disk=False).loc[:,['name','id','city','state']]
        earn_df['MaleEarnings'] = earn_df['id'].map(male_earn_map)
        earn_df['FemaleEarnings'] = earn_df['id'].map(female_earn_map)
        earn_df = earn_df.rename(columns={'name': 'School','id': 'ID','city': 'City','state': 'State'}) # rename cols
         # filter out those with unknown male earnings
        earn_df = earn_df.loc[earn_df['MaleEarnings'].notnull()]
        # INFLATION ADJUST, DATA ARE INFLATION ADJUSTED TO 2022 DOLLARS, NEED TO UPDATE TO 2025
        # We'll use the 2025 first quarter PCE
        # calculation is earnings * (125.58 / 116.11)
        earn_df['MaleEarnings'] = earn_df['MaleEarnings'] * (inflation_adjust / 116.11)
        earn_df['FemaleEarnings'] = earn_df['FemaleEarnings'] * (inflation_adjust / 116.11)
        # round now
        for col in ['MaleEarnings','FemaleEarnings']:
            earn_df[col] = '$' + earn_df[col].apply(int_value_handler).astype(str)
        self.dataframes['earnings'] = earn_df.drop_duplicates()
        
    
    def generate_datatable(self,out_path=''):
        '''generates datatable, outputs html
        
        :out_path: output path for table html
        '''
        cfg = {
            'admissions': ('Admissions','Source: NCES IPEDS.'),
            'enrollment_U': ('Enrollment (Undergrad)','Source: NCES IPEDS. Note: Enrollment includes total part-time and full-time enrollment.'),
            'enrollment_G': ('Enrollment (Grad)','Source: NCES IPEDS. Note: Enrollment includes total part-time and full-time enrollment. "Graduate" includes graduate and first-professional enrollment.'),
            'graduation_bach': ("Graduation (Bach.)",'Source: NCES IPEDS. Note: Graduation rates measure the share of men/women who graduated within six years of enrollment'),
            'graduation_assc': ("Graduation (Assc.)",'Source: NCES IPEDS. Note: Graduation rates measure the share of men/women who graduated within three years of enrollment.'),
            'earnings': ("Median Earnings",'Source: College Scorecard. Note: Median Earnings were taken in 2020 and 2021, six years after students first enrolled. Earnings data were taken from individuals that received federal aid, were working, and were not enrolled in school. Earnings were adjusted to 2025 dollars using the PCE Chain-Type Price Index.')
        }
        nav_tabs = ''
        tab_panes = ''
        dts = ''
        ctr = 1
        for sbjct,df in self.dataframes.items():
            df_html = df.to_html(table_id=sbjct,
                                 classes='cell-border display compact hover table table-striped',
                                 index=False,
                                 na_rep='NA')
            # we have to add the footnotes
            colspan = len(df.columns)
            note = cfg[sbjct][1]
            df_html = df_html.replace(
                            '</tbody>',
                            f'''
                            </tbody>
                            <tfoot>
                            <tr>
                                <td colspan="{colspan}">
                                <small class="text-muted">{note}</small>
                                </td>
                            </tr>
                            </tfoot>
                            '''
                            )
            #nav tabs
            nav_tab = f'''
                        <li class="nav-item" role="presentation">
                                        <button
                                            class="nav-link {'active' if ctr == 1 else ''}"
                                            id="table{ctr}-tab"
                                            data-bs-toggle="tab"
                                            data-bs-target="#table{ctr}"
                                            type="button"
                                            role="tab"
                                            aria-controls="table{ctr}"
                                            aria-selected="{'true' if ctr == 1 else 'false'}"
                                        >{cfg[sbjct][0]}</button>
                                        </li>
                       '''
            nav_tabs = nav_tabs + nav_tab
            # tab panes
            tab_pane = f'''
                        <div
                        class="tab-pane fade {'show active' if ctr == 1 else ''}"
                        id="table{ctr}"
                        role="tabpanel"
                        aria-labelledby="table{ctr}-tab"
                        >
                        {df_html}
                        </div>
                        '''
            tab_panes += tab_pane
            # dt_init
            dt = f'''
                    var table{ctr} = $('#{sbjct}').DataTable({{
                        dom: 'Bfrtip',
                        language: {{
                                search: "",                       
                                searchPlaceholder: "Search a school",
                            }},
                        buttons: [
                                    {{ extend: 'copy',  className: 'btn btn-sm btn-dt-teal' }},
                                    {{ extend: 'csv',   className: 'btn btn-sm btn-dt-teal' }},
                                    {{ extend: 'excel', className: 'btn btn-sm btn-dt-teal' }}
                                ],
                        pageLength: 25,
                        scrollX: true,
                        scrollY: '500px'
                    }});
                 '''
            dts = dts + dt

            ctr += 1

        dataTable = f'''
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                        <meta charset="UTF-8">
                        <title>IPEDS DataTables</title>

                        <!-- Bootstrap CSS -->
                        <link
                            href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css"
                            rel="stylesheet"
                            integrity="sha384-…"
                            crossorigin="anonymous"
                        />

                        <!-- DataTables + Buttons CSS -->
                        <link
                            href="https://cdn.datatables.net/v/bs5/dt-2.3.1/b-3.2.3/b-html5-3.2.3/b-print-3.2.3/datatables.min.css"
                            rel="stylesheet"
                        />
                        <style>
                            /* ==== Nav-Tabs ==== */
                            .nav-tabs .nav-link {{
                            font-family: 'Georgia', serif;
                            color: #06474D !important;
                            }}
                            .nav-tabs .nav-link:hover {{
                            color: #05292C !important;
                            }}
                            .nav-tabs .nav-link.active {{
                            color: #06474D !important;
                            border-color: #06474D #06474D #fff !important;
                            }}

                            /* ==== Pagination ==== */
                            .dataTables_wrapper .dataTables_paginate .pagination .page-item.active .page-link {{
                            background-color: #06474D !important;
                            border-color:     #06474D !important;
                            color:            #fff     !important;
                            }}
                            .dataTables_wrapper .dataTables_paginate .pagination .page-item .page-link:hover {{
                            background-color: #05292C !important;
                            border-color:     #05292C !important;
                            color:            #fff     !important;
                            }}

                            /* ==== Export Buttons ==== */
                            .btn-dt-teal {{
                            background-color: #06474D !important;
                            border-color:     #06474D !important;
                            color:            #fff     !important;
                            }}
                            .btn-dt-teal:hover,
                            .btn-dt-teal:focus {{
                            background-color: #05292C !important;  
                            border-color:     #05292C !important;
                            color:            #fff     !important;
                            }}

                            /* ==== Tab styling ==== */
                            .tab-content,
                            .tab-pane {{
                            font-family: 'Georgia', serif;
                            color:        #05292C; 
                            }}
                            
                            /* ==== Table styling ==== */
                            table.dataTable th,
                            table.dataTable td {{
                            font-family: 'Helvetica';
                            color:        #000000 ;
                            }}
                            table.dataTable th:first-child,

                            table.dataTable td:first-child {{
                            position: sticky;
                            left: 0;
                            z-index: 2; 
                            }}
                        </style>
                        </head>
                        <body class="p-4">

                        <ul class="nav nav-tabs" id="myTab" role="tablist">
                        {nav_tabs}
                        </ul>

                        <div class="tab-content" id="myTabContent">
                        {tab_panes}
                        </div>

                        <!-- JS dependencies at end for faster load -->
                        <script
                            src="https://code.jquery.com/jquery-3.7.0.min.js"
                            integrity="sha256-…"
                            crossorigin="anonymous">
                        </script>
                        <script
                            src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"
                            integrity="sha384-…"
                            crossorigin="anonymous">
                        </script>
                        <script
                            src="https://cdn.datatables.net/v/bs5/dt-2.3.1/b-3.2.3/b-html5-3.2.3/b-print-3.2.3/datatables.min.js">
                        </script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js"></script>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>

                        <script>
                        $(document).ready(function() {{
                                {dts}
                            }});
                        </script>
                        </body>
                        </html>
                     '''

        with open(out_path,'w') as dtf:
            dtf.write(dataTable)
            

def build_table(most_recent_year=2023,
                collescorecard_key='',
                inflation_adjust=None,
                fpath=''):
    '''build IPEDS DataTable
    
    :param most_recent_year: most recent year of data available
    :param collegescorecard_key: College Scorecard API key string
    :param inflation_adjust: PCE inflation index, pegged at 2017, for the most recent year of data
    :param fpath: output path for datatable
    '''
    dt = EdDataTable(most_recent_year=most_recent_year)
    dt.generate_df(
        earnings_api_key=collescorecard_key,
        inflation_adjust=inflation_adjust
    )
    dt.generate_datatable(out_path=fpath)