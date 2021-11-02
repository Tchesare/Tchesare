# Last updated: 2020-08-31

################################################################################
# Libraries
################################################################################
import requests
import re
import time
import json
import collections
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import seaborn as sns
import datetime
from datetime import datetime, date
import os

################################################################################
# Variables
################################################################################
# These and other URLs can be found here: https://confluence.refinitiv.com/display/QPS/QPS+-+URLs

# URLs for Prod server
url_get_curve_definition_prod = 'http://qps-curve-a205820-use1-production.apt-prod.aws-int.thomsonreuters.com/api/curve/zcCurveDefinitions'
url_get_zc_curve_prod = 'http://qps-curve-a205820-use1-production.apt-prod.aws-int.thomsonreuters.com/zcCurves/api/curve/zcCurves'
url_get_volatility_prod = 'http://qps-volsurfaceasl-205484-main-production.apt-prod.aws-int.thomsonreuters.com/request'
url_swaption_valuation_prod = 'http://qps-valuationasl-204937-main-production.apt-prod.aws-int.thomsonreuters.com/request/'

# URLs for PreProd server
url_get_curve_definition_preprod = 'http://qps-curve-a205820-use1-preproduction.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurveDefinitions'
url_get_zc_curve_preprod = 'http://qps-curve-a205820-use1-preproduction.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurves'
url_get_volatility_preprod = 'http://qps-volsurfaceasl-a205484-use1-preproduction.apt-preprod.aws-int.thomsonreuters.com /request'
url_swaption_valuation_preprod = 'http://qps-valuationasl-204937-main-preproduction.apt-preprod.aws-int.thomsonreuters.com/request'
url_CVA_valuation_preprod = "http://qps-dataprepservice-204920-main-preproduction.apt-preprod.aws-int.thomsonreuters.com/cva/calculate"

# URLs for QA server
url_get_curve_definition_QA = 'http://qps-curve-a205820-use1-qa.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurveDefinitions'
url_get_zc_curve_QA = 'http://qps-curve-a205820-use1-qa.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurves'
url_get_volatility_QA = 'http://qps-volsurfaceasl-205484-main-qa.apt-preprod.aws-int.thomsonreuters.com/request'
url_swaption_valuation_QA = 'http://qps-valuationasl-204937-main-qa.apt-preprod.aws-int.thomsonreuters.com/request'

# URLs for Dev server
url_get_curve_definition_dev = 'http://qps-curve-a205820-use1-development.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurveDefinitions'
url_get_zc_curve_dev = 'http://qps-curve-a205820-use1-development.apt-preprod.aws-int.thomsonreuters.com/api/curve/zcCurves'
url_get_volatility_dev = '  http://qps-volsurfaceasl-a205484-use1-development.apt-preprod.aws-int.thomsonreuters.com/request'
url_swaption_valuation_dev = 'http://qps-valuationasl-204937-main-development.apt-preprod.aws-int.thomsonreuters.com/request'
url_CVA_valuation_dev = "http://qps-dataprepservice-204920-main-development.apt-preprod.aws-int.thomsonreuters.com/cva/calculate"
# Note: for CVA, url_swaption_valuation_dev works with headers_CVA

url_genericpricer_dev = "http://qps-pricer-204484-main-development.apt-preprod.aws-int.thomsonreuters.com/api/calculate/price"

# URLs for Data Preparation Service
url_prepare = "http://qps-dataprepservice-204920-main-development.apt-preprod.aws-int.thomsonreuters.com/pricing/prepare"
url_CVA_prepare_dev = "http://qps-dataprepservice-204920-main-development.apt-preprod.aws-int.thomsonreuters.com/cva/prepare"

# Headers
headers = {"Content-type":"application/json",
    "Accept": "application/json",
    "X-Tr-Uuid": "PAXTRA-645406493",
    "X-Tr-ApplicationId": "QPSInternal"
    }

headers_CVA = {"Content-type":"application/json",
    "Accept": "application/json",
    "X-Tr-Uuid": "PADACT-001",
    "X-Tr-ApplicationId": "QPSInternal",
    "x-tr-api": "cva"
    }

################################################################################
# Functions
################################################################################
def parse_body(body):
    """Analyze the string, define if it stands for file name, and retrieve data into a json-like string
    If body is a string ending with ".json" or ".txt", then the file with such name is opened and text extracted
    If body is other string, then it is converted into json-like string
    If body is a dictionary, then it is converted into json-like string
    If the format is different, or is not recognized as json, False is returned
    
    Args:
        body: string
    
    Return:
        json-like string
    """
    body_output = False # pad a dummy value into an output variable
    if isinstance(body, str): # check if body variable is of string type
        if re.search(r'.+\.(json|txt)$',body.lower()): # check for ".json" or ".txt" at the end of the string
            with open(body, 'r', encoding='utf-8-sig') as f:
                try:
                    body_output = json.load(f) # load the request text from the file
                except:
                    print('body argument value does not satisfy json formatting!')

        else:
            try:
                false = False # this fixes a weird artifact sometimes called by eval(): False is converted to false.
                true = True
                body_output = eval(body) # convert string to json
            except:
                print('body argument value does not satisfy json formatting!')
                
    elif isinstance(body, dict):
        body_output = body
    else:
        print(f'{type(body)} is not supported as body argument. Only strings, dictionaries, .json & .txt files are supported!')

    body_output = json.dumps(body_output) # convert into json-like string
    return body_output


def post_request(url, headers, body, return_error_content=False):
    """
    Generic utility function: post a request and return the ouput in json format.
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body
        return_error_content: Boolean; if set to True, then json is returned regardless of response success
    
    Return:
        json object with response
    """
    body = parse_body(body)

    # This chunk of code checks if response is a success.
    # Two problems with response are possible:
    # (1) for wrong url, an error is returned - processed by try / except
    # (2) the server responded with error status code - processed by response.ok verification. In this case, response json is still returned
    try:
        response = requests.post(url=url, data=body, headers=headers) # post the request
        if response.ok: # check if response was a success
            print(f"Request successful.\n")
            json_response = response.json()
            
        else:
            print(f"Could not complete the request! Response content: {response.json()}\n")
            if return_error_content:
                json_response = response.json()
            else:
                json_response = False
    except:
        print('Could not complete the request! No response received. Check URL, internet and VPN connection.\n')
        json_response = False # pad a dummy value into an output variable
    return json_response


def get_curve_definition(url, headers, body):
    """
    Post a request for curve definitions to QPS, return a pandas dataframe
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body
    
    Return:
        pandas dataframe with curve definitions
    """

    json_response = post_request(url=url, headers=headers, body=body) # get the response in json format
    
    # This chunk of code parses the json response into a dataframe
    if json_response:
        curve_definition = json_response['data'][0]['curveDefinitions'] # extract the curve definitions into a list of dictionaries
        curve_definition_df = pd.DataFrame(curve_definition) # convert the list into pandas dataframe
    else:
        curve_definition_df = False # pad a dummy value into an output variable

    return curve_definition_df


def get_curve(url, headers, body):
    """
    Post a request for curve to QPS, return a pandas dataframe
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body
    
    Return:
        pandas dataframe with curve
    """

    json_response = post_request(url=url, headers=headers, body=body) # get the response in json format
    
    # This chunk of code parses the json response into a dataframe
    if json_response:
        dtenor = pd.DataFrame(json_response['data'][0])['curveDefinition']['discountingTenor'] # extractdiscounting tenor
        curves = json_response['data'][0]['curves'][dtenor]['curvePoints'] # extract the curve into a list of dictionaries
        curves_df = pd.DataFrame(curves) # convert the list into pandas dataframe
    else:
        curves_df = False # pad a dummy value into an output variable
    return curves_df


def price_swaption(url, headers, body):
    """
    Post a pricing request for a swaption to QPS and return a dictionary of outputs
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body
    
    Return:
        dictionary of labels and values
    """
    json_response = post_request(url=url, headers=headers, body=body) # get the response in json format

    if json_response:
        labels = json_response['headers'] # extract headers (using word "labels" to avoid naming conflict with headers in the request)
        data = json_response['data'][0] # extract values
        swaption_output = {labels[i]['name']:data[i] for i in range(len(labels))} # combine labels and values in a dictionary
    else:
        swaption_output = False
    return swaption_output

def price_swap(url, headers, body):
    """
    Post a pricing request for a swap to QPS and return a dictionary of outputs
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body

    Return:
        dictionary of labels and values
    """
    json_response = post_request(url=url, headers=headers, body=body) # get the response in json format

    if json_response:
        labels = json_response['headers'] # extract headers (using word "labels" to avoid naming conflict with headers in the request)
        paid_leg = json_response['data'][0] # extract values for PaidLeg
        received_leg = json_response['data'][1] # extract values for ReceivedLeg
        paid_leg_output = {labels[i]['name']:paid_leg[i] for i in range(len(labels))} # combine labels and values in a dictionary for PaidLeg
        received_leg_output = {labels[i]['name']:received_leg[i] for i in range(len(labels))} # combine labels and values in a dictionary for ReceivedLeg
        swap_output = {"paid_leg": paid_leg_output, "received_leg": received_leg_output} # combine paid leg and received leg in a dictionary
    else:
        swap_output = False
    return swap_output



def plot_chart(x_series, y_series, chart_title):
    """
    Time series line plot for curve
    Args:
        x_series: df column with time series format
        y_series: df column with values of curve
        chart_title: title of plot
    
    Return:
        time-series line plot
    """
    fig, ax = plt.subplots(figsize=(15, 5), dpi=100)
    x_series = pd.to_datetime(x_series)
    plt.plot(x_series, y_series, color='blue', alpha=0.5, linewidth=1, marker='o', markersize=3)
    
    plt.title(chart_title, fontsize=10)

    plt.axis([min(x_series), max(x_series), min(y_series)-0.001, max(y_series)+0.001])
#    leg = plt.legend(loc='best', numpoints=1, fancybox=True)
    
    years = mdates.YearLocator(4, month=1, day=1)   # every 4th year
    months = mdates.MonthLocator(6)  # every month
    yearsFmt = mdates.DateFormatter('%Y')
    
    # format the ticks
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)
#    ax.xaxis.set_minor_locator(months)

    # Don't allow the axis to be on top of data
    ax.set_axisbelow(True)
    # manipulate
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:,.3}'.format(x) for x in vals])
    
    ax.grid(color='0.75', linestyle='--', linewidth=0.5) # grid with parameter
    
#    fig.autofmt_xdate()
    for tick in ax.get_xticklabels():
        tick.set_rotation(0)

    plt.show()

def parse_surface(surface):
    """
    Utility function. Parse nested list containing volatility surface into a pandas dataframe
    
    Args:
        surface: nested list
    
    Return: pandas dataframe with volatility surface
    
    """
    columns = surface[0] # Extract first row for columns
    columns[0] = "DateOrTenor" # rename NaN
    surface_df = pd.DataFrame(surface[1:], columns=columns) # set up a dataframe
    surface_df.set_index('DateOrTenor', inplace=True) # set the index
    return surface_df
    
def get_volatility(url, headers, body):
    """
    Parse dictionary into a dictionary of dataframes, a list into a dataframe
    
    Args:
    url: string with url address
    headers: dictionary or json object with request headers
    body: string with json request body or with file name containing the json request body
        
    Return:
    pandas dataframe with volatility serface/cube
    """
    vol_obj = post_request(url, headers, body)['data'][0]['surface']
    
    if isinstance(vol_obj, dict):
        print('This is a volatility cube.')
        volatility = {}
        for key in vol_obj.keys():
            surface = parse_surface(vol_obj[key])
            volatility[key] = surface
    elif isinstance(vol_obj, list):
        print('This is a volatility surface.')
        volatility = parse_surface(vol_obj)
    else:
        print('volatility_object is neither a list nor a dictionary! Cannot parse.')
        
    return volatility

def write_to_excel(df, file_name, sheet_name, width_limit=50):
    """
    Generic utility function. Export dataframe to Excel file, auto-adjust column width
    Args:
        df: dataframe
        file_name: string, filename
        sheet_name: string, sheet_name
        width_limit: integer or float, max column width
    return:
        Excel sheet
    
    """
    writer = pd.ExcelWriter(file_name, engine='xlsxwriter', datetime_format='yyyy/mm/dd', date_format='yyyy/mm/dd')
    df.to_excel(writer, sheet_name=sheet_name)
    worksheet = writer.sheets[sheet_name]
    for idx, column in enumerate(df):
        series = df[column]
        max_len = max((
        series.astype(str).map(len).max(),  # len of largest item
        len(str(series.name)) # len of column name/header
        ))
        max_len = min(max_len, width_limit)+1 # reduce columns that are too wide 

        worksheet.set_column(idx+1, idx+1, max_len)  # set column width
    writer.save()

def test_swaption_bulk(url, headers, body, test_category, test_parameter, test_values, output_parameters, to_excel=True, rest=1000):
    """
    Bulk test of input parameters in swaption pricing.
    
    Args:
        url: string with url address
        headers: dictionary or json object with request headers
        body: string with json request body or with file name containing the json request body
        test_category: string, category of input parameter to be tested 
        test_parameter: string, input parameter to be tested
        test_values: list, values of test parameter to be tested 
        output_parameters: string with name of the output parameter, or list of strings
        to_excel: boolean, create Excel file if True
        rest: integer or float, pause between requests in ms
    
    Return:
        pandas dataframe with results of testing
        excel file with results of testing (if to_excel=True)
        
    """
    # List of mandatory fields. Should be monitored and updated.
    mandatory_fields = ['instrumentType', 'instrumentDefinition', 'settlementType',
                        'endDate', 'tenor', 'buySell', 'callPut','exerciseStyle',
                        'underlyingDefinition', 'exerciseSchedule', 'exerciseScheduleType']
    
    mandatory = {True:'Yes', False:'No'}[test_parameter in mandatory_fields] # check if input parameter is mandatory 

    output_list=[] #placeholder for a list of outputs
    false = False # this fixes a weird artifact sometimes called by eval(): False is converted to false.
    test_body=eval(parse_body(body))

    for value in test_values:
        test_body['universe'][0][test_category][test_parameter] = value # impute test value
        json_response = price_swaption(url=url, headers=headers, body=test_body) # send a pricing request
        if not json_response: # If not a valid response was received...
            diagnostic_response = post_request(url=url, headers=headers, body=test_body, return_error_content=True) # ... send a "diagnostic" request

        
        # Possible scenarios:
        # (1) Response successful and contains output parameter => retrieve the output value
        # (2) Response successful but does not contain output parameter => record 'Request successful, but output parameter not returned'
        # (3) Response not successful but contains some error message => record 'Error Message returned in json' and the message
        # (4) Response not successful and does not contain error message => record 'Request crashed'
        
        if isinstance(output_parameters, str): # Check if output_parameters is a string
            output_parameters = [output_parameters] # Convert into a list with single element
        
        
        for output_parameter in output_parameters: # Iterate over each output parameter
            
            if json_response:

                if output_parameter in json_response.keys(): # if Scenario 1
                    output_value = json_response[output_parameter] # extract the output value
                    message = '' # Space is used because this string can be concatenated with other one
                else: # if Scenario 2
                    output_value = None
                    message = 'Request successful, but output parameter not returned. '

                if ('ErrorMessage' in json_response.keys()):
                    if json_response['ErrorMessage']:
                        message = message + 'ErrorMessage returned as a part of response: ' + json_response['ErrorMessage'] # Extract the message that was returned in a 'ErrorMessage field

            else:
                output_value = None

                time.sleep(rest/1000) # Pause before next request
                if diagnostic_response: # if Scenario 3
                    message = f"Error Message returned in json: {diagnostic_response}" # return error message
                else: # If Scenario 4
                    message = "Request crashed"

            # In the next few lines quotes are added to input and output values if these are in string format
            # This is done purely for visualization (otherwise they are not distinguishable from numeric in Pandas)
            if value.__class__.__name__=='str':
                input_value = "\""+value+"\""
            else:
                input_value = value

            if output_value.__class__.__name__=='str':
                output_value = "\""+output_value+"\""

            # Collect the information for a row in a dictionary:
            output_line = {'Input Field': test_parameter,
                            'Mandatory': mandatory,
                            'Input Value': input_value, 
                            'Output Field': output_parameter,
                            'Output Value': output_value,
                            'Error Message': message}
            output_list.append(output_line) # Add a dictionary to a list
            time.sleep(rest/1000) # Pause before next request

    output_df = pd.DataFrame(output_list) # Convert output to dataframe
    output_df.index = range(1,len(output_df)+1)
    output_df.index.name = 'Nr'
    
    if to_excel==True:
        file_name = input('Input the file name for Excel sheet:\n')+'.xlsx' # Ask for the name of excel sheet
        output_excel_df = output_df.copy()
        output_excel_df['Status'] = ' ' # Add a column for status
        output_excel_df['Comment'] = ' ' # Add a column for comment
        write_to_excel(output_excel_df, file_name=file_name, sheet_name="Summary", width_limit=50)
    
    return output_df



#########################################################################################################################
# CVA functions - work in progress
#########################################################################################################################
def CVA_get_priceit_request(url, headers, body, file_name=None):
    """
    Take a CVA request to QPS, and get a Priceit request. Optionally, store the request in a json file.
    Args:
        url: string with url address
        headers: dictionary or json object with request headers (priceit version)
        body: string with json request body or with file name containing the json request body
        file_name: string, optional, name of the taret json file. If None, the priceit request is not saved in file
    Return:
        json-like object with priceit request
    """
    qps_body = eval(parse_body(body))
    qps_body['fields'] = ['PriceItJsonRequest']
    json_response = post_request(url=url, headers=headers, body=qps_body) # get the response in json format

    if json_response:
        labels = json_response['headers'] # extract headers (using word "labels" to avoid naming conflict with headers in the request)
        data = json_response['data'][0] # extract values
        qps_output = {labels[i]['name']:data[i] for i in range(len(labels))} # combine labels and values in a dictionary
    else:
        qps_output = False
        print("json response is not valid!")
    priceit_request = eval(qps_output['PriceItJsonRequest'])
    if file_name:
        with open(file_name, 'w') as file:
            json.dump(priceit_request, file)
    return priceit_request


def CVA_compare_instrument_definitions(qps_request, qps_to_priceit_request):
    """
    Compare portfolio of deals in qps request and qps-to-priceit request
        Args:
            qps_request - string with json request body or with file name containing the CVA QPS json request body
            qps_to_priceit_request - string with json request body or with file name containing the CVA Priceit json request body
        Return:
            Nested list with comparison. Each element of the list is a dictionary that represents each instrument in the portfolio
    """
    
    # Parse the request bodies to Python objects:
    qps = eval(parse_body(qps_request))
    qps_to_priceit = eval(parse_body(qps_to_priceit_request))
    
    # Retrieve portfolio sections:
    qps_ptf = qps['universe']
    qps_to_priceit_ptf = qps_to_priceit['portfolio']['dealList']
        
    # Compare number of deals in the portfolios:
    if len(qps_ptf) != len(qps_to_priceit_ptf):
        print(f"Number of deals in the portfolio does not match: {len(qps_ptf)} in QPS, {len(qps_to_priceit_ptf)} in Priceit-to-QPS")
        return False
    
    deals = [] # placeholder for set of deals

    # Check every matching pair of deals:
    for qps_deal, priceit_deal in zip(qps_ptf, qps_to_priceit_ptf):
        deal = [] # placeholder for a currently analyzed deal

        priceit_deal = priceit_deal['inputs']
        priceit_deal = {item['name']:item['value'] for item in priceit_deal} # transform section into more convenient form
        
        
        ####################################
        swap_types = {
                'fixed_float': ('Fixed', 'Float', 'FixedRate', 'FloatType'),
                'float_float': ('First', 'Second', 'Rate1', 'Rate2')
                }
        current_swap_type = qps_deal['instrumentDefinition']['legs'][0]['interestType'].lower() \
        + "_" \
        +  qps_deal['instrumentDefinition']['legs'][1]['interestType'].lower()
        
        swap = swap_types[current_swap_type]

        mapping = {
                "TenorOriginal":
                    ("qps_deal['instrumentDefinition']['tenor']",
                     "dates_to_tenor(datetime.strptime(priceit_deal['StartDate'], '%d/%m/%Y'),\
                     datetime.strptime(priceit_deal['EndDate'], '%d/%m/%Y'))"),
    
                "SettlementCcy":
                    ("qps_deal['instrumentDefinition']['settlementCcy']",
                     "priceit_deal['Currency']"),
    
                "InterestCcy":
                    ("qps_deal['instrumentDefinition']['interestPaymentCcy']",
                     "priceit_deal['Currency']"),
                
                "StartDate":
                    ("qps_deal['instrumentDefinition']['startDate']",
                     "datetime.strptime(priceit_deal['StartDate'], '%d/%m/%Y').date()"),
            
                "EndDate":
                    ("qps_deal['instrumentDefinition']['endDate']",
                     "datetime.strptime(priceit_deal['EndDate'], '%d/%m/%Y').date()"),
                
                # Leg 0
                "Leg0Direction":
                    ("qps_deal['instrumentDefinition']['legs'][0]['direction'].capitalize()",
                     "{'Pay':'Paid', 'Receive':'Received'}"+f"[priceit_deal['{swap[0]}PayRcv']]"),
                
                "Leg0Notional":
                    ("qps_deal['instrumentDefinition']['legs'][0]['notionalAmount']",
                     "priceit_deal['Notional']"),
                
                "Leg0Ccy":
                    ("qps_deal['instrumentDefinition']['legs'][0]['notionalCcy']",
                    "priceit_deal['Currency']"),
                
                "Leg0InterestPaymentFrequency":    
                    ("qps_deal['instrumentDefinition']['legs'][0]['interestPaymentFrequency']",
                     f"priceit_deal['{swap[0]}Frequency']"),
                
                "Leg0InterestType":
                    ("qps_deal['instrumentDefinition']['legs'][0]['interestType']",
                     r"{True: 'Float', False: 'Fixed'}"+f"['libor' in priceit_deal['{swap[2]}'].lower()]"),
                
                "Leg0NotionalExchange":
                    ("qps_deal['instrumentDefinition']['legs'][0]['notionalExchange']", 
                     "priceit_deal['NotionalEx']"),
                 
                "Leg0IndexName":
                    ("qps_deal['instrumentDefinition']['legs'][0]['indexName']",
                     "re.search('^(\w*).*', priceit_deal['Libor1']).group(1).upper()"),
                
                "Leg0Spread":
                    ("qps_deal['instrumentDefinition']['legs'][0]['spreadBp']",
                     f"float(re.search('^(.*)%+?$', priceit_deal['{swap[0]}Spread']).group(1))*100"),
                    
                "Leg0FixedRate":
                    ("qps_deal['instrumentDefinition']['legs'][0]['fixedRatePercent']",
                     f"re.search('^(.*)%+?$', priceit_deal['{swap[0]}Rate']).group(1)"),

                "Leg0DayCount":
                    (None,
                     f"priceit_deal['{swap[0]}Daycount']"),
                
                "Leg0IndexTenor":
                    (None,
                     f"None if '{swap[0]}' == 'Fixed' else priceit_deal['{swap[0]}Tenor']"),

                
                
                # Leg 1
                "Leg1Direction":
                    ("qps_deal['instrumentDefinition']['legs'][1]['direction'].capitalize()",
                     "{'Pay':'Paid', 'Receive':'Received'}"+f"[priceit_deal['{swap[1]}PayRcv']]"),
                
                "Leg1Notional":
                    ("qps_deal['instrumentDefinition']['legs'][1]['notionalAmount']",
                     "priceit_deal['Notional']"),
                
                "Leg1Ccy":
                    ("qps_deal['instrumentDefinition']['legs'][1]['notionalCcy']",
                    "priceit_deal['Currency']"),
                
                "Leg1InterestPaymentFrequency":    
                    ("qps_deal['instrumentDefinition']['legs'][1]['interestPaymentFrequency']",
                     f"priceit_deal['{swap[1]}Frequency']"),
                
                "Leg1InterestType":
                    ("qps_deal['instrumentDefinition']['legs'][1]['interestType']",
                     r"{True: 'Float', False: 'Fixed' }"+f"['libor' in priceit_deal['{swap[3]}'].lower()]"),
                    
                "Leg1NotionalExchange":
                    ("qps_deal['instrumentDefinition']['legs'][1]['notionalExchange']", 
                     "priceit_deal['NotionalEx']"),
                 
                "Leg1IndexName":
                    ("qps_deal['instrumentDefinition']['legs'][1]['indexName']",
                     f"priceit_deal['{swap[3]}']"),
                
                "Leg1Spread":
                    ("qps_deal['instrumentDefinition']['legs'][1]['spreadBp']",
                     f"float(re.search('^(.*)%+?$', priceit_deal['{swap[1]}Spread']).group(1))*100"),
                
                "Leg1FixedRate":
                    ("qps_deal['instrumentDefinition']['legs'][1]['fixedRatePercent']",
                     f"re.search('^(.*)%+?$', priceit_deal['{swap[1]}Rate']).group(1)"),
                
                "Leg1DayCount":
                    (None,
                     f"priceit_deal['{swap[1]}Daycount']"),
                
                "Leg1IndexTenor":
                    (None,
                     f"None if '{swap[1]}' == 'Fixed' else priceit_deal['{swap[1]}Tenor']"),
                
                "PricingRequest":
                    ("qps_deal",
                     "priceit_deal")
                    }
        
        for item in mapping:
            param = {"Param": item} # placeholder for a parameter being analyzed
            if mapping[item][0] is not None:
                try:
                    param["QPS_value"] = eval(mapping[item][0])
                except:
                    param["QPS_value"] = None
                
                
            if mapping[item][1] is not None:
                try:
                    param["QPS2Priceit_value"] = eval(mapping[item][1])
                except:
                    param["QPS2Priceit_value"] = None

                param["QPS_param"] = mapping[item][0]
                param["QPS2Priceit_param"] = mapping[item][1]

            deal.append(param)

        deals.append(deal)
            
    return deals


def dates_to_tenor(start_date, end_date):
    """
    Calculate difference between two dates in date format, convert into tenor format measured in years, months, days
    30/360 conventions is used
    """
    years = end_date.year - start_date.year
    months = end_date.month - start_date.month
    days = end_date.day - start_date.day
    if days < 0:
        days += 30
        months -= 1
    if months < 0:
        months +=12
        years -=1
    tenors = zip('YMD', (years, months, days))
    tenors = (str(number)+tenor for tenor, number in tenors if number !=0)
    tenors = ''.join(tenors)
    return tenors

def tenor_to_days(tenor):
    """
    convert tenor to approximate number of days using 30/360-style convention:
    360 days in a year, 30 days im a month, 7 days in a week
    """
    
    lst = list(re.search('(\d+)?(\D)?(\d+)?(\D)?(\d+)?(\D)?(\d+)?(\D)?', tenor).groups())
    lst = [item for item in lst if item is not None] # remove Nones
    labels = lst[1::2] # get labels
    numbers = lst[::2] # get numbers
    tenors_input = dict(zip(labels, numbers)) # combine in a dictionary
    tenors_input = {key.upper():int(value) for key, value in tenors_input.items()} # uppercase keys, integer values
    tenors = {key:0 for key in 'YMWD'} # dummy dictionary with 0s
    tenors.update(tenors_input) # add zeros to the dictionary
    lengths = {'Y':360, 'M':30, 'W':7, 'D':1} # lengths of periods in days
    days = sum([tenors[i]*lengths[i] for i in lengths.keys()])
    
    return days

def convert_tenor(tenor, valuation_date):
    """
    Convert tenor in from Priceit format to QPS format.
    Args:
        tenor - string, tenor as per Priceit
        valuation_date - string, valuation date, string, "YYYY-mm-dd" formatting
    Return:
        string, tenor as per QPS format
    """
    
    # We will first declare boolean variables for various cases 
    
    # Case 1: one-to-one mapping exists
    mapping = {'ON': '1D', 'TN': '2D', 'SN': '3D', 'SW': '1W'} # key as per Priceit, value as per QPS
    direct_mapping = tenor in mapping
    
    # Case 2: 6X12 quotation style:
    x_format = re.search(".*X(\d+)$", tenor.upper())

    # Case 3: 13M quotation style:
    month_format = re.search('^(\d+)[mM]$', tenor)

    # Case 4: tenor is in date format:
    date_format = "/" in tenor

    # Now we will apply transformation to QPS style:
    
    if direct_mapping:
        tenor_qps = mapping[tenor]
        
    elif x_format or month_format:
        search = x_format if x_format else month_format
        total_months = int(search.groups(1)[0])
        years = total_months//12
        months = total_months%12
        years_txt = str(years)+"Y" if years>0 else ""
        months_txt = str(months)+"M" if months>0 else ""
        tenor_qps = years_txt+months_txt

    elif date_format:
        start_date = datetime.strptime(valuation_date, '%Y-%m-%d')
        end_date = datetime.strptime(tenor, '%d/%m/%Y')
        tenor_qps = dates_to_tenor(start_date, end_date)
        
        # Drop days:
        search = re.search('(.*[a-zA-Z])\d+\w$', tenor_qps)
        tenor_qps = search.group(1) if search else tenor_qps
    else:
        tenor_qps = tenor
        
    return tenor_qps


def CVA_price_portfolio_in_QPS_adfin(url, headers, body, fields=['InstrumentDescription','MarketValueInDealCcy']):
    """
    Parse CVA request into a list of instrument definitions, get market value from QPS/Adfin for every instrument
    Args:
        url: string with url address
        headers: dictionary or json object with request headers (valuation version)
        body: string with CVA json request body or with file name containing the CVA json request body
        fields: optional, list with fields to be returned 
    Return:
        nested list with pricing response for every instrument in the portfolio. 
        Every element in the list is a dictionary with keys:
            'Response' - object returned by QPS/Adfin
            'Body' - request body used by QPS/Adfin
    """
    body = eval(parse_body(body))
    valuation_date = body['pricingParameters']['valuationDate']
    portfolio = body['universe']
    outputs = [] # placeholder for requests and responses
    for instrument in portfolio:
        deal={}
        instrument_type = instrument['instrumentType']
        instrument_definition = instrument['instrumentDefinition']

        # assemble the request
        instrument_body = {
            "fields": fields,
            "universe": [{
                "instrumentType": instrument_type,
                "instrumentDefinition": instrument_definition
            }],
            "pricingParameters": {
                "valuationDate": valuation_date
            }
        }
        
        # clean the request from odd terms
        del instrument_body['universe'][0]['instrumentDefinition']['interestPaymentCcy']
                
        deal['Response'] = price_swap(
            url=url,
            headers=headers,
            body=instrument_body)
        deal['Body'] = instrument_body
        outputs.append(deal)
    
    return outputs


def CVA_price_portfolio_in_piopil(piopil_path, body, piopil_name = 'pio_pil_13141.exe'):
    """
    Price the CVA request with pio_pil.
    Args:
        piopil_path: string, path to the folder where pio_pil.exe is located
        body: object, string or file name with CVA priceit request
        piopil_name: string, exact name of the pio_pil.exe file used
    Return:
        object with pricing response from pio_pil
    """
    
    request = eval(parse_body(body))
    request_file_name = 'request.json'
    response_file_name = 'output.json'
    with open(f"{piopil_path}\\{request_file_name}", 'w') as file:
        json.dump(request, file)
    os.system(f'cd /D {piopil_path} && {piopil_name} -jpprice {request_file_name} > {response_file_name}')#    response = parse_body(f"{piopil_path}\\{response_file_name}")
    with open(f"{piopil_path}\\{response_file_name}", 'r') as file:
        response = eval(file.read())
    os.remove(f"{piopil_path}\\{request_file_name}")
    os.remove(f"{piopil_path}\\{response_file_name}")
    return response


def CVA_full_comparison(url, headers_adfin, headers_priceit, piopil_path, body, piopil_name = 'pio_pil_13141.exe'):
    """
    Compare instrument definition and pricing in QPS/Adfin vs QPS/piopil
        Args:
            url: string with url address
            headers_adfin: dictionary or json object with request headers (valuation version)
            headers_priceit: dictionary or json object with request headers (priceit version)
            
            piopil_path: string, path to the folder where pio_pil.exe is located
            body: object, string or file name with CVA QPS request body
            piopil_name: string, exact name of the pio_pil.exe file used
        Return:
            Nested list with comparison. Each element of the list is a dictionary that represents each instrument in the portfolio
    """
    # Get the qps and priceit requests:
    qps_request = eval(parse_body(body))
    priceit_request = CVA_get_priceit_request(url=url, headers=headers_priceit, body=body)
    
    # Check for 'MarketValueInDealCcy' field, and update request if necessary
    if 'fields' in qps_request:
        if 'MarketValueInDealCcy' not in qps_request['fields']:
            qps_request['fields'].append('MarketValueInDealCcy')

    
    # Compare instrument definitions
    comparison = CVA_compare_instrument_definitions(qps_request, priceit_request)
    
    # Price the portfolios in qps/adfin and piopil:
    adfin_pricing = CVA_price_portfolio_in_QPS_adfin(url=url, headers=headers_adfin, body=qps_request)
    priceit_pricing = CVA_price_portfolio_in_piopil(piopil_path=piopil_path, body=priceit_request, piopil_name=piopil_name)
    
    # Add pricing with comparison
    for i in range(len(comparison)):
        qps_leg0_value = adfin_pricing[i]['Response']['paid_leg']['MarketValueInDealCcy']
        qps_leg1_value = adfin_pricing[i]['Response']['received_leg']['MarketValueInDealCcy']
        qps_swap_value = qps_leg1_value - qps_leg0_value
        priceit_swap_value = priceit_pricing['PortfolioPricesList'][i]['value']
        comparison[i].append({'Param': 'Leg0Value', 'QPS_value': qps_leg0_value, 'QPS2Priceit_value': None})
        comparison[i].append({'Param': 'Leg1Value', 'QPS_value': qps_leg1_value, 'QPS2Priceit_value': None})
        comparison[i].append({'Param': 'SwapValue', 'QPS_value': qps_swap_value, 'QPS2Priceit_value': priceit_swap_value})
    
    return comparison


def get_zc_curve_constituents(url, headers,  currency, valuation_date, discounting_tenor, index_tenor, eikon_key='2e533d420ea6412082a545a667efc0366747f411'):
    """
    Get the constituents and fixings for the yield curve.
    Important: Eikon must be running for this function to work properly!
    Args:
        url
        headers
        currency: string, currency code, e.g. 'EUR'
        valuation_date: string, date in the format: 'yyyy-mm-dd'
        discounting_tenor: string, discounting tenor, e.g. 'OIS'
        index_tenor: string, index_tenir, e.g. '3M'
        ek_key: string, eikon app key
    Return:
        nested list of curve constituents for a selected YC.
        Every element in the list is a tuple of 3 elements: (tenor, RIC, fixing) 
    """
    "get the dictionary of tenors and fixings for ZC curve constituents"
    
    import eikon as ek
    ek.set_app_key(eikon_key)
    
    # Correct tenors to priceit convention if necessary:
    discounting_tenor = '1Y' if discounting_tenor=='12M' else discounting_tenor
    index_tenor = '1Y' if index_tenor=='12M' else index_tenor
    
    # Set up the request, post the request and get the curve points:
    curve_request = {
        "universe": [
            {
                "curveParameters": {
                    "valuationDate": valuation_date,
                },
                "curveDefinition": {
                    "currency": currency,
                    "discountingTenor": discounting_tenor
                }
            }
        ],
        "outputs": [
            "Curves"
        ]
    }
    response = post_request(url, headers, curve_request)
    curve = response['data'][0]['curves'][index_tenor]['curvePoints']
    # Get the dictionary of tenors and constituents:
    curve = {point.get('tenor'):point.get('instruments')[0]['instrumentCode'] for point in curve if point.get('instruments') is not None}

    # Get the fixings from ek:
    constituents = list(curve.values())
    fixings = ek.get_timeseries(rics=constituents, fields='CLOSE', start_date=valuation_date, end_date=valuation_date)
    fixings.reset_index(inplace=True, drop=True)
    fixings = fixings.T.to_dict()[0]
    
    # Combine the tenors, rics and fixings to a nested list:
    output = [(tenor, instrument, fixings.get(instrument)) for tenor, instrument in curve.items()]
    
    #Convert to a dataframe
    output = pd.DataFrame(output, columns=['Tenor', 'RIC', 'Fixing'])
    output.set_index('Tenor', inplace=True)
    return output


def CVA_check_yield_curves(url_curve, headers_curve, body, eikon_key='2e533d420ea6412082a545a667efc0366747f411'):
    """
    Compare yield curve tenors and constituent fixing vs curve service and eikon
    Args:
        url_curve
        headers_curve
        body: object, string or file name with CVA Priceit request body

        
    """
    body = eval(parse_body(body))
    valuation_date = body['valuationDate']['value']

    # Reformat date from dd/mm/yyyy to yyyy-mm-dd string:
    day, month, year = re.search("^(\d+)/(\d+)/(\d+)", valuation_date).groups()    
    valuation_date = f"{year}-{month}-{day}"

    output = []
    for item in body['marketData']:
        if item['dataType'] == 'YLD':
            currency = item['underlying']['ccy']
            for curve in item['data']:
                if not curve['dataSubType'] == 'TEC':
                    tenor = curve.get('tenor')
                    priceit_curve = curve.get('value')
                    priceit_curve = pd.DataFrame(priceit_curve, columns=['Instrument', 'Tenor', 'Fixing'])
                    conversion_function = lambda x: convert_tenor(x, valuation_date)
                    priceit_curve['Tenor'] = priceit_curve['Tenor'].apply(conversion_function)
                    priceit_curve.set_index('Tenor', inplace=True)
                    priceit_curve['Fixing'] = priceit_curve['Fixing'].astype('float')

                    curve_service = get_zc_curve_constituents(
                        url=url_curve,
                        headers=headers_curve,
                        currency=currency,
                        valuation_date=valuation_date,
                        discounting_tenor=tenor,
                        index_tenor=tenor,
                        eikon_key=eikon_key
                    )

                    merged_df = pd.merge(
                        left=priceit_curve,
                        right=curve_service, 
                        how='outer', 
                        left_index=True, 
                        right_index=True, 
                        suffixes=('_Priceit', '_CurveService'))
                                        
                    merged_df['CurveCurrency'] = currency
                    merged_df['CurveTenor'] = tenor
                    merged_df['Difference'] = merged_df['Fixing_CurveService'] - merged_df['Fixing_Priceit']
                    merged_df = merged_df[['CurveCurrency', 'CurveTenor', 'Instrument', 'RIC', 'Fixing_Priceit', 'Fixing_CurveService', 'Difference']]
                    
                    output.append(merged_df)
    return output


def get_credit_curve(url, headers, currency, valuation_date, entity, eikon_key='2e533d420ea6412082a545a667efc0366747f411'):
    """
    Get the constituents and fixings for the credit curve.
    Important: Eikon must be running for this function to work properly!
    Args:
        url
        headers
        currency: string, currency code, e.g. 'EUR'
        valuation_date: string, date in the format: 'yyyy-mm-dd'
        entity: code of the entity with credit risk
        ek_key: string, eikon app key
    Return:
        pandas dataframe with credit curve 
    """
    
    import eikon as ek
    ek.set_app_key(eikon_key)
    
    
    # Set up the request to get the ric chain for credit curve: 
    credit_request = {
      "universe": [
        {
          "instrumentType": "CreditCurve",
          "curveDefinition": {
            "ReferenceEntityType":"issuerCode",
            "ReferenceEntity": entity,
            "creditCurveType": "CdsIssuerCurve",
            "creditCurveTypeFallbackLogic":
            [
              "CdsIssuerCurve"
            ],
            "currency":currency
          },
          "curveParameters": {
              "marketDataDate": valuation_date
          }
        }
      ],
      "outputs":[
        "headers",
        "Data",
        "Statuses",
        "MarketData"
        ]
    }
    
    # Get the chain ric:
    json_response = post_request(url=url, headers=headers, body=credit_request) # get the response in json format
    labels = json_response['headers'] # extract headers (using word "labels" to avoid naming conflict with headers in the request)
    data = json_response['data'][0] # extract values
    parsed_response = {labels[i]['name']:data[i] for i in range(len(labels))} # combine labels and values in a dictionary
    chain_ric = parsed_response['RIC']
    
    # Get the rics from the chain ric:
    rics_df, err = ek.get_data(instruments=chain_ric, fields="LONGLINK1") # отримати df з переліком ріків
    rics = rics_df['Instrument'].to_list()
    
    # Get the credit curve fixings
    fixings = ek.get_timeseries(rics=rics, fields=['CLOSE'], start_date=valuation_date, end_date=valuation_date).T
    # display(ek.get_data(instruments=chain_ric, fields='CF_CLOSE')[0]) # real-time
    
    # Add tenor:
    get_tenor = lambda x: re.search('^[^0-9]+(\d+[a-zA-Z])', x).group(1) # lambda expression that retireves tenor from ric
    fixings.reset_index(inplace=True, drop=False)
    fixings['Tenor'] = fixings['CLOSE'].apply(get_tenor)
    fixings.set_index('Tenor', inplace=True)
    fixings.columns = ['RIC', 'Fixing']
    fixings['ChainRIC'] = chain_ric

    fixings = fixings[['ChainRIC', 'RIC', 'Fixing']]
    
    return fixings


def CVA_check_credit_curves(url_curve, headers_curve, body, eikon_key='2e533d420ea6412082a545a667efc0366747f411'):
    """
    Compare credit curve tenors and constituent fixing vs eikon
    Args:
        url_curve
        headers_curve
        body: object, string or file name with CVA Priceit request body

        
    """
    body = eval(parse_body(body))
    valuation_date = body['valuationDate']['value']

    # Reformat date from dd/mm/yyyy to yyyy-mm-dd string:
    day, month, year = re.search("^(\d+)/(\d+)/(\d+)", valuation_date).groups()    
    valuation_date = f"{year}-{month}-{day}"

    output = []
    for item in body['marketData']:
        if item['dataType'] == 'CRD':
            currency = item['underlying']['ccy']
            entity = item['underlying']['code']
            
            priceit_curve = pd.DataFrame(item['data'][0]['value'])
            priceit_curve.columns = ['Tenor', 'Fixing']
            priceit_curve.set_index('Tenor', inplace=True)
            priceit_curve['Fixing'] = priceit_curve['Fixing'].astype('float')
            

            curve_service = get_credit_curve(
                url=url_curve,
                headers=headers_curve,
                currency=currency,
                valuation_date=valuation_date,
                entity=entity,
                eikon_key=eikon_key
            )

            merged_df = pd.merge(
                left=priceit_curve,
                right=curve_service, 
                how='outer', 
                left_index=True, 
                right_index=True, 
                suffixes=('_Priceit', '_CurveService'))
                                        
            merged_df['CurveCurrency'] = currency
            merged_df['Entity'] = entity

            merged_df['Difference'] = merged_df['Fixing_CurveService'] - merged_df['Fixing_Priceit']
            merged_df = merged_df[['Entity', 'CurveCurrency', 'ChainRIC', 'RIC', 'Fixing_Priceit', 'Fixing_CurveService', 'Difference']]                    
            output.append(merged_df)
    return output


def CVA_sw_volatilities(url_vol, headers_vol, qps_to_priceit_request):
    """
    Compare price-it volatility surfaces vs swaption volatility surfaces from qps
    Args:
        url_vol: string with url address
        headers_vol: dictionary or json object with request headers
        qps_to_priceit_request - string with json request body or with file name containing the CVA Priceit json request body

    """
    body_vol = {
        "universe": [
            {
                "underlyingType":"Swaption",
                "underlyingDefinition": {
                "instrumentCode": "EUR",
            },
                "surfaceParameters": {
                "XAxis":"Strike",
                "YAxis":"Tenor",
                "ZAxis":"Expiry",
                "calculationDate": '2020-07-06'
            },
                "surfaceLayout": {
                    "format": "Matrix"
                }
            }
        ]
    }


    # Parse the request volatility bodies to Python objects:
    qps_body_vol = eval(parse_body(body_vol))
    qps_to_priceit = eval(parse_body(qps_to_priceit_request))

    # Retrieve valuation date from price-it request:
    valuation_date = qps_to_priceit['valuationDate']['value']
    day, month, year = re.search("^(\d+)/(\d+)/(\d+)", valuation_date).groups()
    valuation_date = f"{year}-{month}-{day}"

    # Set valuation date:
    qps_body_vol["universe"][0]['surfaceParameters']['calculationDate'] = valuation_date

    # Retrieve volatility:
    qps_vol = get_volatility(url=url_vol, headers=headers_vol, body=qps_body_vol)
    priceit_vol = pd.DataFrame(qps_to_priceit['marketData'][3]['data'])

    # Retrieve ATM volatility from Price-it request:
    priceit_atm_vol = pd.DataFrame(list(priceit_vol['value'][priceit_vol['dataSubType'] == 'ATM'])[0])
    priceit_atm_vol.columns = priceit_atm_vol.iloc[0]
    priceit_atm_vol.drop(priceit_atm_vol.index[0], inplace=True)
    priceit_atm_vol.set_index('ATM', inplace=True)

    # Extract expiries
    expiry = list(priceit_atm_vol.columns)

    # Check ATM volatility for all available tenors:
    atm_vol_agg = collections.defaultdict(list)   # create dict for collection ATM volatilities from QPS and Price-it
    for tenor in qps_vol.keys():
        priceit_atm_vol_for_tenor = list(priceit_atm_vol.loc[tenor])
        priceit_atm_vol_for_tenor = [round(float(num), 2) for num in priceit_atm_vol_for_tenor]

        qps_atm_vol_for_tenor = list(qps_vol[tenor].iloc[:, 4])
        qps_atm_vol_for_tenor = [round(float(num), 2) for num in qps_atm_vol_for_tenor]

        atm_vol_agg['tenor'].append(tenor)
        atm_vol_agg['priceit_atm_vol'].append(priceit_atm_vol_for_tenor)
        atm_vol_agg['qps_atm_vol'].append(qps_atm_vol_for_tenor)

        priceit_atm_vol_agg = pd.DataFrame(atm_vol_agg['priceit_atm_vol'], index=atm_vol_agg['tenor'], columns=expiry)
        qps_atm_vol_agg = pd.DataFrame(atm_vol_agg['qps_atm_vol'], index=atm_vol_agg['tenor'], columns=expiry)

    print("-----------------------------------------------")
    print("ATM vol diff")
    labels = abs(priceit_atm_vol_agg - qps_atm_vol_agg)
    sns.heatmap(priceit_atm_vol_agg==qps_atm_vol_agg, cmap='RdYlGn', vmin=0, annot=labels, cbar=False)
    plt.show()

    # Check SML volatility for all available tenors:
    sml_vol_agg = collections.defaultdict(list)   # create dict for collection SMl volatilities from QPS and Price-it
    for tenor in qps_vol.keys():
        priceit_sml_vol = pd.DataFrame(list(priceit_vol['value'][priceit_vol['tenor']==tenor])[0])
        priceit_sml_vol.columns = priceit_sml_vol.iloc[0]
        priceit_sml_vol.drop(priceit_sml_vol.index[0], inplace=True)
        priceit_sml_vol.set_index(priceit_sml_vol.columns[0], inplace=True)
        priceit_sml_vol = priceit_sml_vol.astype(float)

        qps_sml_vol = qps_vol[tenor].drop('0.00', axis=1)
        qps_sml_vol.columns = list(priceit_sml_vol.columns)
        qps_sml_vol = qps_sml_vol.astype(float)

        sml_vol_agg['priceit_sml_vol'].append(priceit_sml_vol)
        sml_vol_agg['qps_sml_vol'].append(qps_sml_vol)

        print("-----------------------------------------------")
        print(f"{tenor}: SML vol diff")
        labels = abs(priceit_sml_vol - qps_sml_vol)
        sns.heatmap(priceit_sml_vol==qps_sml_vol, cmap='RdYlGn', vmin=0, annot=labels, cbar=False)
        plt.show()


    output = {"Price-it": {"ATM": priceit_atm_vol_agg,  "SML": sml_vol_agg['priceit_sml_vol']},
              "QPS":      {"ATM": qps_atm_vol_agg,      "SML": sml_vol_agg['qps_sml_vol']}}

    return output


def CVA_check_CSA(qps_request, qps_to_priceit_request):
    """
    Compare CSA parameters in qps request and qps-to-priceit request
    Args:
        qps_request - string with json request body or with file name containing the CVA QPS json request body
        qps_to_priceit_request - string with json request body or with file name containing the CVA Priceit json request body
    Return:
        Nested list with comparison. Each element of the list is a dictionary that represents each instrument in the portfolio
    """

    qps = eval(parse_body(qps_request))
    qps_to_priceit = eval(parse_body(qps_to_priceit_request))
    
    csa = [] # placeholder for the output
    # Get the CSA section from Priceit request:
    priceit_CSA = qps_to_priceit['portfolio']['xvaConfiguration']['nettingSetList'][0]['parameters']
    priceit_CSA = {item['name']: item['value'] for item in priceit_CSA}

    # Get the threshold:
    row = {}
    row['Param'] = 'Threshold'
    row['QPS_value'] = qps['csas'][0]['threshold']['amount']
    row['QPS2Priceit_value'] = int(priceit_CSA['cptThreshold'])
    csa.append(row)

    # Get the initial margin:
    row = {}
    row['Param'] = 'InitialMargin'
    row['QPS_value'] = qps['csas'][0]['initialMargin']['amount']
    row['QPS2Priceit_value'] = int(priceit_CSA['IA'])
    csa.append(row)

    # Get the minimum transfer:
    row = {}
    row['Param'] = 'MinimumTransfer'
    row['QPS_value'] = qps['csas'][0]['minimumTransfer']['amount']
    row['QPS2Priceit_value'] = int(priceit_CSA['mta'])
    csa.append(row)
    
    
    return csa


def plot_missing_values_timeline(dataframe, dif_column='Difference', label_column='CurveTenor'):
    """Plot the missing values for each indicator on a timeline
    
    Args:
        dataframe: dataframe with dataset, index being date range

    Returns: not applicable
    """
    label = dataframe.iloc[0][label_column]+" curve"
    df = dataframe[[dif_column]]
    df.columns = [label]
    fig = plt.figure(figsize=(20,len(dataframe.columns)/15))
    ax = sns.heatmap(df.isna().T, cmap=['green', 'crimson'], xticklabels=True, cbar=False)