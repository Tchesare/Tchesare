
################################################################################
# Libraries
################################################################################
from functools import reduce,partial
from numpy.random import uniform
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
import  datetime as dt
import os
import copy
import eikon as ekObj
import jmespath

print('Imported functions.py module...')

################################################################################
# Utlilities Functions :::::::::::::::::::::::::::::::::::::::::::::::::::::::::
################################################################################

def generateEikonObject():
    ekObj.set_app_key('68665d71d1bb431aac39185b6153951aa479bec6')
    return ekObj

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

def read_content_file(file_path=r'C:\VSCODE\no_path_request_file.json'):
    '''
        Reads the content of a file
        If not possible returns none
    '''
    try :

        with open(file_path)  as f:  
            file_contents = f.read() 

    #IOError – file cannot be opened //
    #  EOFError – When the input reaches the end of a file and no more data can be read
    # ValueError – function receives an argument that has the right type but an invalid value

    except (IOError, ValueError, EOFError,FileNotFoundError)  as err :
        print (f'Error in read_content_file --> {err}') 

    else:
        return file_contents 

def is_json(myjson): 
    '''Test if a string is a json like string'''
    try:
        json.loads(myjson)
    except ValueError as e:
        return False
    return True

def parse_payload(payload) :
    ''' 
        Body is either a Json-Like string or a dictionnary
        If it is the case, it sends back the payload a json like string
        esle returns None

    '''
    if isinstance(payload,dict): # to json like string if it is a dict
      return json.dumps(payload,indent=2)

    if isinstance(payload,str) : #If a string then 
      
      if is_json(payload) : 
        return payload
      else :
        return None  

    else:
      return None #Not a string at all then None  

def json_string_to_dict(body):
    ''' 
        Body is a json like strings
        If it is the case, it sends back the body as a dict
        esle returns None

    '''
    #try to  parse the body using loads method from json python lib:
    try:
        dict_body = json.loads(body)

    except json.JSONDecodeError as err:  
        print(f'JSONDecodeError when parsing the string {err}')

    else:
        # the result is a Python dictionary:
        return dict_body 

def load_json_from_file(file_path=r'C:\VSCODE\no_path_request_file.json'):
    '''
    Genral Utility : loads a json from specified file as a dict
        Inputs :  file path
        Outputs : python dict (to be posted to qps...)

    '''
    file_contents=read_content_file(file_path)
        
    try :             
            request =  json.loads(file_contents)

    except Exception as err :
        
        print (f'Exception in load_json_from_file --> {err}')
        # return {'Exception in load_json_from_file' : str(err)}
    
    else :
        return request 

def IsDefined(value) : 
    if isinstance(value, (int, float)): return True
    else :
        if (value) :  #undefined: if the value is not defined and it's undefined # null# empty str: '' #0: number zero #NaN: not a number,false*/
            if str(value).strip() =="null" : return False
            elif str(value).strip() == "undefined" :  return False
            elif str(value).strip() == "#NA":return False
            elif str(value).strip() == "#NaN":return False
            elif str(value).strip() == "nan":return False
            elif str(value).strip() == "":return False
            else : return True


# takes a vector of float and recue the decimals : ex: [1.3236522,2.326598]--->[1.32,2.33]
def formatDecimalsVector  (vector,num) :
    if len(vector) >0 :
        return list(map(lambda x : round(float(x),num),vector) )#up to  num decimals
    
    else : 
        return np.array(["Empty vector"])

#If service return null as value we want to see it so we set res as value
def formatBrutResult(value,type):
    """
    Generic utility function. Returns value in the format specified by type
    Args:value, type
    return: value in the 'good' format
    """
    if IsDefined(value) : 
        if type ==  "DateTime" or type =="String" or type =="string" :
            return str(value) 
        elif type ==  "Float" or type =="Integer" or type =="string" :
            return round(float(value),4)

        elif type == "FloatArray" :                                                         #console
                    #We format the array so that we do not have that much decimals
            return formatDecimalsVector(value,4)

        elif type == "Object" :    # The field underlyingAsset is an json object                                                     #console
                    #We format the array so that we do not have that much decimals
            return json.dumps(value)#res=formatDecimalsVector(value,4);

        else : return value


def dictToDataFrame(myDict):
    """ Generic utility function:  takes a python dict and returns a dataframe
    Args: python dict
    Return: panda dataframe
    """
    try:
     df = pd.DataFrame.from_dict(myDict)
    except Exception as ex: 
        print('Exception Raised in dictToDataFrame : '+str(ex))

        return pd.DataFrame.from_dict({'myDict':'Exception Raised in dictToDataFrame'})
    else : 
        return df 


def stringDateToNumOfDays(dateAsString):
    """Generic utility function: from dates gives the number of days from 1970
    as integers and rates
    Args:date format like 2020-10-15
    Return:integer
    """

    base = 3600*24*1000000000 # numberof nano seconds in 1 day
    numOfNanoSec = pd.to_datetime(dateAsString).value # num of nanno sec from 1 jan 1970
    return (numOfNanoSec/base)

def NumOfDaystoStringDate(dateAsInteger):
    """Generic utility function: from d the number of days from 1970 gives the date
    Args:integer
    Return:date format like 2020-10-15 
    """
    df = pd.to_datetime(dateAsInteger, unit='D', origin='1970-01-01')
    res=df.ctime() 
    return res

def mergeDataFrameCurves(curvedf1, curvedf2,fieldOntoMerge =['tenor']):
    """Generic utility function: merges two dataframe to compare them
    Args:dataframes
    Return:one dataframe containing all the data 
    """
    try:

        result=pd.merge(curvedf1,curvedf2, on = fieldOntoMerge, how = "outer")
        # make tenor column index
        result.set_index('tenor', inplace=True)
                    
    except Exception as ex: 
        print('Exception Raised in mergeDataFrameCurves : '+str(ex))
        return pd.DataFrame.from_dict([{'mergeDataFrameCurves':'Exception Raised'+str(ex)}])
     
    else : return result 



def dataFrameToNpArray(df):
        """Takes a date frame ans sent the nparray associated 
        Args:dataFrame:
        Return:list of data frame values
        """
        array = np.array(df.dropna().values)
        return array

def dataFrameToList (dataFrame)  :
        """Takes a date frame ans sent the list associated 
        Args:dataFrame:
        Return:list of data frame values
        """
    
        dataList = dataFrame.dropna().values.tolist()

        return    dataList  



def getCleanKey (dicty,key='FieldValue'):
     """Generic utility function : Used for returning either the key or none if there is no such key in dict, for all key in dict
     Args : 
        a dict : {'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.258896}, 'BondFloor':.......}} 
        a key  : 'FieldValue'
     Returns :  a value : with filtered fields like  {'BondPrice':  'FieldValue': 2.258896}} if only one fields BondPrice si selected
     or {'BondPrice':    none }} if BondPrice has no fieldvalue key 
     """
     if key  in dicty.keys() : return dicty[key] 
     else : return 'none' 
    #  else : return {key:{'NoSuchKey': {'emptyKey':'EmptyValue'}}

getValueFromDictByListPath = partial(reduce, lambda d, k: d[k])

def getValueFromDictByPathN (inputDict,pathToKey)  : 

    """Generic utility function:  returns the key value from path.
    Args:inputDict: the dictionnary
    pathToKey : the path of the key we want the value
    Return:value of the key,
    """
    path=pathToKey.split('.') #list of string specifying the path
    
    try :
        res= getValueFromDictByListPath(path,inputDict)
    except Exception as ex: 
        print ('Exception Raised in getValueFromDictByPath :' + str(ex))
        return ''
       
    else:  return res


def filterDict(dicty,keyList):
    """Generic utility function: filter a dict regarding a lsit of keys
    Args :dicty:  as a dict       
         keyList : as a list (e.g ['PricingAnalysisOutput','YieldsOutput','StockOverviewOutput'])
    Returns:filtered dict : as dict {key:value,,,,,,,key:value}
    """
    return {key:value for key, value in dicty.items() if key in keyList}


def stringToInteger(myString) : return int(myString) if myString.isnumeric() else myString

def splitMulitple(pathToKey):
    """Generic utility function : splits a pth into words an list indexes ex : data[0].bid[1].vol -->[data,0,bid,1,vol]
    Args : 
        a  string representing a path
    """
    # splitedPath0 = re.split("[ .\\[\\]-]+|(?<=\\d)(?=\\D)", pathToKey); #print(splitedPath)
    splitedPath0 = re.split("[ .\\[\\]-]", pathToKey); #print(splitedPath)
    
    splitedPath= list(filter(None, splitedPath0))

    splitedPath=[stringToInteger(x) for x in splitedPath]

    return splitedPath

def getValueFromDictByPath(myDict,pathToKey):
    """Generic utility function:  returns the key value from path.
    Args:inputDict: the dictionnary
    pathToKey : the path of the key we want the value
    Return:value of the key,
    """

    
    tDict = myDict ;    # print(myDict) 
    
    try:  
        splitedPath =splitMulitple(pathToKey)                    
        for char in  splitedPath :
            # print(char)
            tDict=tDict[char]

    except Exception as ex: 
        print ('Exception Raised in getValueFromDictByPathN :' + str(ex))
        return None
 
    else :return tDict    



def get_value_ByKeyPath(myDict,pathToKey) :
    """Generic utility function: returns the key with pathToKey path in the python dictionnary myDict 
    Args : 
        pathtoKey : the string taht specifies the path
        myDict : the pyton dict that stores the pair key/value we look gor

    Return: the key (a dict,a string, an integer, an array.....)
    """
    try:  
        result_Key = jmespath.search(pathToKey,myDict)     
                       
    except Exception as ex: 
        print ('Exception Raised in get_key_value_by_path :' + str(ex))
        return None
 
    else :
        return result_Key     


def get_key_value_by_path(my_dict,path_to_key) :
    """Generic utility function: returns the key with pathToKey path in the python dictionnary myDict 
    Args : 
        pathtoKey : the string taht specifies the path
        myDict : the pyton dict that stores the pair key/value we look gor

    Return: the key (a dict,a string, an integer, an array.....)
    """
    try:  
        result_Key = jmespath.search(path_to_key,my_dict)     
                       
    except Exception as ex: 
        print ('Exception Raised in get_key_value_by_path :' + str(ex))
        return None
 
    else :
        return result_Key  

def generate_seed():  
    time.sleep(0.000001)  
    now_start = dt.datetime.now()
    return now_start.microsecond


def generate_uniform_ab_rnd_numbers(n=1,min=0,max=1,seed=None) :
    """Generic utility function: returns a uniform 1d  array of rnd numbers in [a,b]
    """
    if seed is None : seed=generate_seed()  
        
    np.random.seed(seed)

    uniform_ab= np.random.uniform(min,max,n)
 
    return uniform_ab 

def date_string_to_date_object(date_string):

    """Generic utility function: gets a date in either or the format here 
        ["%m/%d/%Y","%Y/%m/%d", "%d-%m-%Y", "%Y%m%d","%Y-%m-%d","%Y-%d-%m"]
        and sends back a date object
        if not possible then return None
    """
    accepted_fmt=["%m/%d/%Y","%Y/%m/%d", "%d-%m-%Y", "%Y%m%d","%Y-%m-%d","%Y-%d-%m"]

    for fmt in accepted_fmt :
        try:
            return dt.datetime.strptime(date_string, fmt).date()

        except Exception :
            continue

def convert_date_to_qps_format(date_string):
    """Generic utility function: gets a date in either or the format here 
        ["%m/%d/%Y","%Y/%m/%d", "%d-%m-%Y", "%Y%m%d","%Y-%m-%d","%Y-%d-%m"]
        and sends it ack to the QPS supported one '%Y-%m-%d'
        if not possible then return None
    """
    qps_fmt='%Y-%m-%d'# "2021-03-22"

    dt_object=date_string_to_date_object(date_string)

    try:
        return  dt_object.strftime(qps_fmt)

    except Exception as err: 
        print(f'Error in < convert_date_to_qps_format > function --> {err}')

# def to_integer_from_1900(dt_time):
#     """
#         GEneral utility : returns dates in an adfin format i.e days from 1900
#         Input : dt_time as a datetime object
#         Ouptut : integer rpresenting the num of days from date to 1 jan 1900
#     """
    
#     first_jan_00 = dt.date(1899, 12, 31)
#     delta = dt_time - first_jan_00
#     return(delta.days)

def datetime_to_int(datetime_obj):
    """
        GEneral utility : returns dates in an excel integer format i.e days from 30 dec 1899
        Input : datetime_obj as a datetime object
        Ouptut : integer rpresenting the num of days from  30 dec 1899 datetime_obj 
    """
    first_jan_1900 = dt.datetime(1899, 12, 30)

    try : 
        dt_delta = datetime_obj - first_jan_1900

    except Exception as err: 
        print(f'Error in < datetime_to_int > function --> {err}')

    else : 
            return dt_delta.days    

def convert_date_to_adfin_format(date_string):
    """Generic utility function: gets a date in either or the format here 
        ["%m/%d/%Y","%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"]and sends it ack to the ADFIN supported one
        i.e integers 
        Example : 21-06-2017 returns 42907
    """
    new_date =convert_date_to_qps_format(date_string)

    new_date_int = datetime_to_int(new_date) 

    return new_date_int

def get_template_request(template_request_path=None):
    '''
    Genral Utility : get_template__request from specified file
        Inputs :  file path
        Outputs : basic  request 

    '''
    try : 

        f = open(template_request_path) if (template_request_path is not None) else  open(r'C:\VSCODE\no_path_request_file.json')
    
        request =  json.load(f) ; #display(zcCurveRequest)  

    except Exception as ex :
        # print(str(x) + " is Not a float")
        request = {'error in get_template_request' : str(ex)}
     
    return request  


def dump_dict_to_file(dict_to_save,saving_file_path=None):

    '''Genral Utility : dump a python dict and then saves the json-string to the sepcified file 
        Arg :python dict , path of the file that will regiter the json-string

        OUtput : None

    '''
    #Opening the file in write mode

    try :

        with open (saving_file_path,'w') as f:
            json.dump(dict_to_save,f,indent=2)

    except (IOError, ValueError, EOFError,FileNotFoundError)  as err :
        print (f'Error in dump_dict_to_file --> {err}') 


def cast_to_float(x):
    '''
    Genral Utility :tries to cast anything that is castable to a float
        Inputs :  object
        Outputs : object as a float if possible

    '''
    try : 
        return float(x)

    except Exception  as err:

        print(f'Error in < cast_to_float > function --> {err}\n')
        return x

def string_list_to_float_list(string_list): 
    '''
    Genral Utility : returnt of strings
        Outputs : list of s the list of string like [NOne,'1.0000',...,'0.659877'] //[2Y3M,'1.2323',..,'0.565']
        in the  format [None,1.0000,...,0.659877] or [2Y3M,1.2323,..,0.565];
        used for cap volsurfs
        Inputs :        lisflaot '''
    try : 
        return  [cast_to_float(x) for x in string_list] 

    except Exception as err :
        print(f'Error in < string_list_to_float_list > function --> {err}')
        
def substract_float_list (float_list_1,float_list_2) :
    '''
    Genral Utility : substract two list of floats which are in the  format [None,1.0000,...,0.659877] or [2Y3M,1.2323,..,0.565];
        used for cap volsurfs
        Inputs :  float_list_1,float_list_2      
        Outputs : list of flaot '''
    try:
        #s-d if each of the two elements are floats else we concatenate them
        return [round(s-d, 3) if (isinstance(s, float) & isinstance(d, float)) else str(s) + '-' +str(d) for (s, d) in zip(float_list_1,float_list_2)]
    
    except Exception as ex:
        print(f' Exception in substract_float_list :  {ex}')


def zip_headers_data(headers,data)   :
    '''
        Zips the headers int this form[{}]
    '''
    # my_dict={}
    my_dict=[]

    try:

        for header,value in zip(headers,data) : my_dict.append((header['name'],value))#my_dict.update({h['name']:v}) 

    except Exception as err :

        print(f'Exception in zip_headers_data --> {err}')

    else :
        
        return my_dict    


################################################################################
# Qps env
################################################################################

url_post = "http://qps-valuationasl-204937-main-development.apt-preprod.aws-int.thomsonreuters.com/request/"
url_prod = "http://qps-valuationasl-204937-main-production.apt-prod.aws-int.thomsonreuters.com/request/"


#Content type must be included in the header
qpsHeaders = {'Content-Type' : 'application/json',
'X-Tr-ApplicationId' : 'QPSInternal',
'X-Tr-Uuid':'PAXTRA-645406493',
'X-Tr-Scope':'qps_internal_access' }

#ConvB default request
qpsRequest = {"fields": ["CleanPrice", "FairPrice"], "outputs": [        "headers",        "Data",        "Statuses"    ], "universe":          [ {        "instrumentType": "Bond",        "instrumentDefinition": {       "instrumentCode": "74965L200="  },           "pricingParameters": {  "UseMetadataFromEjv": "true","UseAdditionalEjvMetadataFromAdc":"true", "marketdataDate": "2019-06-25", "priceSide": "Mid","ComputeCashFlowWithReportCcy": "false",    "convertibleBondParameters":    { "UseA4Pricer": "false"}   }    }]}
 
################################################################################
# Qps Functions
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
            except Exception as ex:
                print(ex)
                print('body argument value does not satisfy json formatting!')
                
    elif isinstance(body, dict):
        body_output = body
    else:
        print(f'{type(body)} is not supported as body argument. Only strings, dictionaries, .json & .txt files are supported!')

    body_output = json.dumps(body_output) # convert into json-like string
    return body_output

def postQPSrequest0(url=url_post, headers=qpsHeaders, body=qpsRequest , return_error_content=False):
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
    # we  use a defult response for the algorithm that extracts values in returnOutputsAsArray are ok
    
    try:
        response = requests.post(url=url, data=body, headers=headers) # post the request
        if response.ok: # check if response was a success
            #print(f"Request successful.\n")
            json_response = response.json()          
        else:
            print(f"Could not complete the request! Response content: {response.json()}\n")
            json_response =  {"headers": [{"type": "String","name": "response.ko"}],"data": [["Could not complete the request! Response content:" + json.dumps(response.json())]],"statuses": [[0]]}
    
    except Exception as ex:
        print(ex)
        # print('Could not complete the request! No response received. Check URL, internet and VPN connection.\n')
        #json_response = 'No response received from Service!' # pad a dummy value into an output variable
        json_response =  {"headers": [{"type": "String","name": "Exception in postQPSrequest "}],"data": [["No response received"]],"statuses": [[0]]}
    
    return json_response

def postQPSrequest(url=url_post, headers=qpsHeaders, body=qpsRequest , return_error_content=False):
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
    

    try:
        body = parse_body(body)
        response = requests.post(url=url, data=body, headers=headers) # post the request
        json_response = response.json()

    except Exception as ex:
        print(ex)
        # print('Could not complete the request! No response received. Check URL, internet and VPN connection.\n')
        #json_response = 'No response received from Service!' # pad a dummy value into an output variable
        json_response =  {"headers": [{"type": "String","name": "Exception in postQPSrequest "}],"data": [["No response received"]],"statuses": [[0]]}
    
    return json_response

def post_request_to_qps(url_to_post,payload,headers_to_post):
    '''
        General utility : post a python dict as a request to a qps URL
        Args :
            url_to_post 
            payload: python dict / json like string
            headers to attach  post
        Returns : None if error   
    '''

    # #either a dict or a json-like string to be tasfromed to a dict
    # is_dict_payload = isinstance(payload, str) 

    #QPS accepts only json string-like objects !!!
    final_payload = parse_payload(payload)

    try:
        # r=requests.post(url_to_post,data=json.dumps(payload),headers=headers_to_post)
        r=requests.post(url_to_post,data=final_payload,headers=headers_to_post)

    except ConnectionError as err:
    # manage connection errors from python lib
        print (f'ConnectionError in post_request_to_qps --> {err}')

    except requests.exceptions.RequestException as err:
    # manage requests errors from request lib
        print (f'RequestException in post_request_to_qps --> {err}') 

    except requests.exceptions.Timeout as err:
    # manage requests time outs
        print (f'Timeout in post_request_to_qps --> {err}')    

    except requests.exceptions.InvalidURL as err:
    # manage requests time outs
        print (f'InvalidURL in post_request_to_qps --> {err}')
        
    else : 
        return r
        #  return r.json()  if r.ok else r.text

def process_qps_response(response_from_service,data_path='data[0]',headers_path='headers') :
    ''' Verifieds the response object has a json and is ok otherwise sends None
        retruns the data key of the json value from the response and the headers value
        response can be none / have a status ok/ or not
        Args : 
            response object from qps
            path of data key
            path of headers key
    '''
    if response_from_service is None :
        print('None response from service')
        return 'No Data','No Headers'

    elif not response_from_service.ok :
        print('Not ok  response from service')
        return response_from_service.text,f'Response code :{response_from_service.status_code}'
    else : 
        r_json =response_from_service.json()

        data= get_key_value_by_path(r_json,data_path) if (data_path is not None ) else None

        headers = get_key_value_by_path(r_json,headers_path) if headers_path is not None else None

        return headers,data 
 

def return_qps_response_as_dict (parsedResponse):
        """
        Generic utility function: takes a json response from QPS and return the ouput in dict format.
        Args:
            parsedResponse:qps response from convb service
        Return:
            response as a dict like : {{'name': 'RIC', 'value': '68269GAA5='},...,{'name': 'Parity', 'value': 65.8052048}}
        """
    
        try:
                data=parsedResponse['data'][0] #=[value1, value2,... …]

                # Headers
                headers = parsedResponse['headers'] ; #[{name:field1,type:t1}]

                
        except Exception as ex: 

                print('Exception Raised in returnConvBQpsResponseAsDict')
                print(str(ex))
                print(parsedResponse)

                # myDict={'myDict':ex}
                
                myDict={'RIC': str(ex)}
                # print(myDict)

                return myDict        

        else : 

                #Copying the dict for immutability of the request
                myDict ={}# copy.deepcopy(headers)
                
                # [{}.update({'name':h['name'],'value':d}) for (h,d) in zipQps]
                for (h,v) in zip(headers,data) : myDict.update({h['name']:v})               

                return myDict

#returnOutputsAsArray  : Takes the response from qps and returns an array :  [(name )AverageLife,(diff) 0.00260,(Tolerance ) 1]
def returnQpsOutputsAsArray (parsedResponse):

    try:
        brutResult=parsedResponse['data'][0] #=[value1, value2,... …]
        # Headers
        headers = parsedResponse['headers'] ; #[{name:field1,type:t1}]

    except Exception as ex: 
        print ('Exception Raised in returnQpsOutputsAsArray ')
        print(ex)
        result=['No response from QPS',parsedResponse]
        return result
    else:    
        #We get here : [field1,value1,t1]
        result = map(lambda x, y: [x["name"],formatBrutResult(y,x["type"]), x["type"]], headers, brutResult) 

        #console.log(" metlArray  is " )
        #console.log(metlArray )
    
        return list(result)
    
#Modifies the currency for the curve def request
def modifyCurveDefCurrency(curveDefReq,currency):
    new_req = copy.deepcopy(curveDefReq)
    new_req["universe"][0]['currency']=currency
    return new_req

#Modifies the field for the curve def request
def modifyCurveDefField(curveDefReq,fieldname,fieldValue):
    new_req = copy.deepcopy(curveDefReq)
    new_req["universe"][0][fieldname]=fieldValue
    return new_req 

def  getQpsCurveAsDataFrame (parsedResponse,fields=['tenor','endDate','ratePercent','discountFactor'] ) :
    """Generic utility function:  response from curve service and return the ouput in dataframe.
    Args:parsedResponse: parsed response from QPS
    Return:DataFrame like like : [x['tenor'],x['endDate'],x['ratePercent'],x['discountFactor']],
    """
    try:
        # getting the curv points as a dict
        curvPoints=parsedResponse['data'][0]['curvePoints']
        curveId=parsedResponse['data'][0]['curveDefinition']['id']
    except Exception as ex:  

        print ("Exception Raised in getQpsCurveAsDataFrame")
        print(ex)
        print(parsedResponse)
        curvPoints =[{k:'NaN' for k in fields}]#[{"tenor": "100Y",'endDate':'2100-01-01',"ratePercent": 1000000.0,'discountFactor':1000000 }]
        return dictToDataFrame(curvPoints)
        
    else:
        df0 = dictToDataFrame(curvPoints)
        df=  df0[fields]
        df.columns.name=curveId 
 
    return df

def  getQpsCurveAsDataFramebyPath (parsedResponse,path,fields=['tenor','endDate','ratePercent','discountFactor'] ) :
    """Generic utility function:  response from curve service and return the ouput in dataframe.
    Args:parsedResponse: parsed response from QPS
    Path : place where curvpoints stands in the dict response
    Return:DataFrame like like : [x['tenor'],x['endDate'],x['ratePercent'],x['discountFactor']],
    """
    # getting the curv points as a dict
    curvPoints=getValueFromDictByPath(parsedResponse,path)
    curveId=getValueFromDictByPath(parsedResponse,'itemId')

    try:
        df0 = dictToDataFrame(curvPoints)
        df=  df0[fields]
        df.columns.name=curveId 

    except Exception as ex:  

        print ("Exception Raised in getQpsCurveAsDataFrame :" + str(ex))
        print(parsedResponse)
        curvPoints =[{k:'NaN' for k in fields}]#[{"tenor": "100Y",'endDate':'2100-01-01',"ratePercent": 1000000.0,'discountFactor':1000000 }]
        df= dictToDataFrame(curvPoints)
        
    return df    

def getQpsCurveAsCleanNpArray(resp,columnNames):
    """Generic utility function: tkaes the curve service request and transfrom it into an np array with dates 
    as integers and rates
    Args:Takes a qps responses, and the column names related to it (date,yields,rate....)
    Return:A npArray"""

    qpsCurveDf0=getQpsCurveAsDataFrame(resp,columnNames)
    # print(qpsCurveDf0)

    # To remove duplicates and keep last occurences, use keep.
    qpsCurveDf=qpsCurveDf0.drop_duplicates(subset=['endDate'], keep='last')
    # print(qpsCurveDf)

    #Date to integer to be onterpolated
    qpsCurveDf['endDate']=qpsCurveDf['endDate'].transform(lambda x :pd.to_datetime(x).value/86400000000000 )

    qpsArray =np.array(qpsCurveDf.values)

    return qpsArray


def getQpsCurveAsCleanNpArrayFromID(curvUrl,curvRequest,id,fieldList=['endDate','ratePercent']):
    """
    Generic utility function: from an id curve returns qps curv as an np array with dates 
    as integers and rates

    Args:
        Takes a qps url, a request,an id and fields(related to qps curve values)

    Return:
        A npArray 
    """
    newReq=modifyQpsCurveId(curvRequest,id)
    resp=postQPSrequest(url= curvUrl,body=newReq)
    qpsArray=getQpsCurveAsCleanNpArray(resp,fieldList)
    return qpsArray

#returnOutputsAsArray  : Takes the response from MdsCurve and returns an array 
def  returnCurveDefAsList (parsedResponse) :
    """Generic utility function:  response from mdscurve service and return the ouput in array.
    Args:parsedResponse: parsed response from MDS
    Return:Array like : x['name'],x['chainRic'],x['id'],x['firstHistoricalAvailabilityDate'],
    """

    try:
        d=parsedResponse['curveDefinitionResponses'][0]['curveDefinitions']

    except Exception as ex:  

        print ("Exception Raised in returnCurveDefAsList")
        print(ex)
        metlArray =[parsedResponse] 
        
    else:  
        #Test if response has curve points
        if len(d)>0:
            curvDef=d[0]
            #a point is like : {'id': 'b2386ce6-a13e-4cdc-b48d-59ffb47a10b4', 'chainRic': '0#AAAUSDAGEBMK=', 'issuer': None, 'name': 'AAA Rating US.......
            metlArray = [curvDef['name'],curvDef['chainRic'],curvDef['id'],curvDef['firstHistoricalAvailabilityDate']]

            print (metlArray)
        else : metlArray =['No definiton from Mds']    

        # return headers + list(metlArray)
        return metlArray

#returnOutputsAsArray  : Takes the response from MdsCurve and returns an array 
def  returnMdsCurveDef (parsedResponse) :
    """Generic utility function:  response from mdscurve service and return the ouput in array.
    Args:parsedResponse: parsed response from MDS
    Return:Array like : x['name'],x['chainRic'],x['id'],x['firstHistoricalAvailabilityDate'],
    """

    try:

        d=parsedResponse['curveDefinitionResponses'][0]['curveDefinitions']

    except Exception as ex:
        print ("Exception Raised in returnMdsCurveDef ")
        print(ex)
        myDict ={'Response From MDS': parsedResponse}
        
    else:  
        #Test if response has curve points
        if len(d)>0:
            curvDef=d[0]
            #a point is like : {'id': 'b2386ce6-a13e-4cdc-b48d-59ffb47a10b4', 'chainRic': '0#AAAUSDAGEBMK=', 'issuer': None, 'name': 'AAA Rating US.......
            myDict = curvDef

            # print (myDict)
        else : myDict ={'curveDefinitions': 'parsedResponse'}   

        # return headers + list(metlArray)
        return myDict

#returnOutputsAsArray  : Takes the response from Curve Service Def and returns an dict
def  returnCurveDef (parsedResponse) :
    """Generic utility function:  response from curveDef service and return the ouput in array.
    Args:parsedResponse: parsed response from MDS
    Return:Dictionnary with all definitions like :{'name': 'Lithuania GOV Par Benchmark Curve', 'issuerType': 'Sovereign', 'country': 'LT', 'source': '                                               Refinitiv', 'currency': 'EUR', 'curveSubType': 'Government Bond Par', 'id': 'bc263351-c805-4ed2-886e-8173e7140119'},
    """

    try:

        d=parsedResponse['data'][0]['curveDefinitions']

    except  Exception as ex:  

        print ("Exception Raised in returnCurveDef")
        print(ex)
        dictOfDef=[parsedResponse] 
        
    else:  
        #Test if response has curve points
        if len(d)>0:
            dictOfDef =d[0]#[curvDef['name'],curvDef['issuerType'],curvDef['id'],curvDef['currency']]

            # print (dictOfDef)
        else : dictOfDef ={'name': 'No definition'} 

        # return headers + list(metlArray)
        return dictOfDef

#returnResponseDataForPanda  : Takes the response from qps and returns an simple vector with formatted data [value1, value 2....]
def returnResponseDataForPanda (parsedResponse):

        brutResult=parsedResponse['data'][0] #=[value1, value2,... …]

        # Headers
        headers = parsedResponse['headers'] ; #[{name:field1,type:t1}]

        #We get here : [field1,field2....]
        #myHeaders = map(lambda x: x["name"], headers) 

        #We get here : [value1,value2...] formatted regarding the type
        myData = map(lambda x, y:formatBrutResult(y,x["type"]), headers, brutResult)

        #console.log(" metlArray  is " )
        #console.log(metlArray )
        return list(myData)

# Function to combine two function which it accepts  as argument
def composite_function(f, g): 
    return lambda x,y,z: f(g(x,y,z))

#We pipeline the two function 
# returnOutputsAsArray(postQPSrequest(url, headers, body, return_error_content=False))
requestThenFormatQps =composite_function(returnQpsOutputsAsArray, postQPSrequest) #
requestThenFormatQpsForPanda =composite_function(returnResponseDataForPanda, postQPSrequest)


def modifyQpsRequestRic(req,ric):
    new_req = copy.deepcopy(req)
    new_req["universe"][0]["instrumentDefinition"]["instrumentCode"]=ric
    return new_req

def modifyQpsRequestMarketDataDate(req,date):#date is in thsi formt yyyy-mm-dd, ex : 2020-10-05
    new_req = copy.deepcopy(req)
    new_req["universe"][0]["pricingParameters"]["marketdataDate"]=date
    return new_req

#fields is an array of strings related to qps fields, ex : ["CleanPrice","FairPrice","DeltaPercent","VegaPercent","ProbabilityOfMaturityPercent"]
def modifyQpsRequestFields(req,fields):
    new_req = copy.deepcopy(req)
    new_req["fields"]=fields
    return new_req

def modifyPricingInputQpsRequest(req,dictOfFieldsValues) :
    
    """  
     Generic utility function : Used for overriding pricing params in qps request 
     Args :      
            a qpsrequest : {'fields': ['CleanPrice', 'FairPrice'], 'outputs': ['headers'.....'universe': [{'instrumentType': 'Bond', 'instrumentDefinition': {'instrumentCode': '185899AA9='}, 'pricingParameters': 
            a dict containing the field and values to override  : {'stockFlatVolatilityPercent':'15',....,'flatCreditSpreadBp':'200'}
        Returns :    
             a qpsRequest : with pricingparam  fields overiden 
      """
    new_req = copy.deepcopy(req)
    for key in dictOfFieldsValues.keys() :new_req["universe"][0]["pricingParameters"][key]=str(dictOfFieldsValues[key])
    return new_req

def modifyQpsConvBPricingParametersRequest(req,listOfkeysToModify,listOfvaluesToUpdate) :
    """Generic utility function : Used for overriding cinvB pricingParameters in qps request 
    Args : 
        a convB  request
        a list of keys 
        a list of values   
        Returns  a curve request with CurveParameter  fields overiden 
    """
    try:
        copyOfReq=copy.deepcopy(req) 
        myDict = copy.deepcopy(req['universe'][0]['pricingParameters'])
        # print(myDict)
    except Exception as ex:
        print ('Exception Raised in modifyQpsConvBPricingParametersRequest ')
        print(ex)
        return req
    else :
        dictOfKeyValues=zip(listOfkeysToModify, listOfvaluesToUpdate)
        myDict.update(dictOfKeyValues)
  
        copyOfReq['universe'][0]['pricingParameters']=myDict

        return copyOfReq

def modifyQpsCurveDefinitionRequest(req,listOfkeysToModify,listOvaluesToUpdate) :
    """Generic utility function : Used for overriding curveParameters in qps request for Curve
    Args : 
        a curve request
        a list of keys 
        a list of values   
        Returns  a curve request with CurveDefinition fields overiden 
    """
    try:    
        copyOfReq=copy.deepcopy(req) 
        # myDict = copy.deepcopy(req['universe'][0]['curveDefinition'])
        myDict = copyOfReq['universe'][0]['curveDefinition']
        # print(myDict)
    except Exception as ex:
        print ('Exception Raised in modifyQpsCurveDefinitionRequest :'+str(ex))
        return req
    else :
        myDict.update(dict(zip(listOfkeysToModify, listOvaluesToUpdate)))
        # print(myDict)

        # copyOfReq['universe'][0]['curveDefinition']=myDict

        return copyOfReq

def modifyQpsCurveParametersRequest(req,listOfkeysToModify,listOvaluesToUpdate) :
    """Generic utility function : Used for overriding curveParameters in qps request for Curve
    Args : 
        a curve request
        a list of keys 
        a list of values   
        Returns  a curve request with CurveParameter  fields overiden 
    """
    try:
        copyOfReq=copy.deepcopy(req) 
        myDict = copy.deepcopy(req['universe'][0]['curveParameters'])
        # print(myDict)
    except Exception as ex:
        print ('Exception Raised in modifyQpsCurveParametersRequest ')
        print(ex)
        return req
    else :
        myDict.update(dict(zip(listOfkeysToModify, listOvaluesToUpdate)))
        # print(myDict)      

        copyOfReq['universe'][0]['curveParameters']=myDict

        return copyOfReq

def modifyQpsParametersRequest(req,path,listOfkeysToModify,listOvaluesToUpdate) :
    """Generic utility function : Used for overriding qpsParameters in qps request for any service
    Args : 
        a  request
        a path showing the place where to override
        a list of keys 
        a list of values   
        Returns  a request with Parameter  fields overiden 
    """

    copyOfReq=copy.deepcopy(req) 
    myDict = getValueFromDictByPath(copyOfReq,path)        # print(myDict)

    try:
            myDict.update(dict(zip(listOfkeysToModify, listOvaluesToUpdate)))
        
    except Exception as ex:
            print ('Exception Raised in modifyQpsCurveParametersRequest :'+ str(ex))
            print(req)
            return req

    else :return copyOfReq
        
        # print(myDict)      

    

def modifyMDSQchainRicField(req,chainRicName):
    new_req = copy.deepcopy(req)
    new_req["curveDefinitionRequests"][0]['filter']['chainRic']=chainRicName
    return new_req

def modifyQpsCurveId(req,id='4f502658-0071-4b99-b4f4-bcce564bb80a'):
    new_req = copy.deepcopy(req)
    new_req["universe"][0]["curveDefinition"]["id"]=id
    return new_req

def reqMultiQpsForPanda(qpsUrl=url_post , basicReq=qpsRequest,ricList=["74965L200="],fieldList=["CleanPrice"]) :

        """
        Generic utility function : Takes 2 lists of fields and rics and request qps to get for each ric the pricing

        Args :

            qpsUrl  : url to post reauest
            basicReq : default request ot be modified
            ricList : list of rics
            fieldList : list of fields

        Returns :     

            array : matrix with nth line containg pricing of  nth ric     

        """

        # Retunrs a list of requests to be posted 
        requestArray = map(lambda x: modifyQpsRequestRic (basicReq,x),ricList) #list of requests with rics
        requestArray = map(lambda req: modifyQpsRequestFields (req,fieldList),requestArray) #list of requests with fields

        #returns a list of list :
        #[[value11,value12...],[value21,value22...],[value31,value32...]] , valueij is the jth field for ith ric
        responseArray = map(lambda req : requestThenFormatQpsForPanda(qpsUrl,qpsHeaders,req),requestArray)
        return list(responseArray) 


def reqMultiQpsForPandaFromRequestArray(qpsUrl=url_post , requestArray=[]) :
        """
        Generic utility function : Takes 2 lists of fields and rics and request qps to get for each ric the pricing
        Args :qpsUrl  : url to post reauest
            requestArray : list of request to send
            fieldList : list of fields
        Returns :array : matrix with nth line containg pricing of  nth ric     
        """
        #returns a list of list :
        #[[value11,value12...],[value21,value22...],[value31,value32...]] , valueij is the jth field for ith ric
        responseArray = map(lambda req : requestThenFormatQpsForPanda(qpsUrl,qpsHeaders,req),requestArray)
        return list(responseArray) 



def compareQpsCurveValuesToRta(rtaArray,qpsArray):
        """Generic utility function : Takes 2 curves and gets the difference in percentqge to the first array
        Args :rtaArray  : first curve,qpsArray : second curve
        Returns :array : dates and relative difference in percentage
        """
        # interpolation of qps rates at rta dates
        dates= rtaArray[:,0]
        stringDates = np.vectorize(NumOfDaystoStringDate)(dates)
        rates= rtaArray[:,1]

        qpsRatesToRtaDates =np.interp(dates,qpsArray[:,0],qpsArray[:,1])
        
        # compute the Diff Rates at rta dates
        diff0=np.subtract(rates,qpsRatesToRtaDates)

        #dividing diff by rta values to get the ratio of differences
        diff=np.divide(diff0,rates)
        # diff=np.divide(diff0,rates)

        diff1=np.absolute(np.multiply(diff,100))

        # return array of rta dates with diff between interpolated QPS and rta
        res = np.column_stack((stringDates,diff1))
        
        return res



################################################################################
# RTA
################################################################################
def generateEjvSectorChainRic(currency='EUR',ejvSector=['NFI','AGE','SUP','HLH','IND','TEC','COMM','UTI'],ratings=['AAA','AA','A','BBB','BB','B','CCC','CC','C']):
    return ['0#'+r+currency+s +'BMK='for r in ratings for s in ejvSector ] 

def get_real_time(ekObject,rics=['US10YT=RR'],fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1']):
        """Get the fixings for the rics unformatted
        Important: Eikon must be running for this function to work properly!
        Args:
            rics: list of string
            fields :list of string
            ekObject: necessary to get data
        Return:pandas dataframe to be used either for get_realtimeAsDataFrame or get_realtimeAsList or as an nparray
        """      
        try:

            data_object=ekObject.get_data(instruments=rics,fields=fields)# real-time tuple containing
            # (  Instrument GV4_TEXT  MATUR_DATE  RT_YIELD_1  SEC_YLD_1
            #  0  US10YT=RR   10Y     2031-08-15      1.2903     1.2886,
            #  None)
            fixings=data_object[0]

        except Exception as ex: 
                stringRics = ' '.join([str(item) for item in rics]) 
                print ("Exception Raised in get_real_time using rics " + stringRics)
                print(ex)
                # myDict={'Instrument':['none'] ,'GV4_TEXT':'100Y','MATUR_DATE':['2100-01-01'],'PRIMACT_1': [1000000],'RT_YIELD_1': [1000000],'SEC_YLD_1': [1000000]}
                myDict =[{k:'NaN' for k in fields}]
                return pd.DataFrame(myDict)
                
        else: 
            
            # fixings=ek.get_data(instruments=rics,fields=fields)[0]
            # fixings=ek.get_data(instruments=rics,fields=fields)[0] # real-time
            # df= pd.DataFrame(fixings,index=rics,columns=fields)
            # print(fixings)
            df= pd.DataFrame(fixings)

        return df   

def get_realtime_as_dataframe(eikon_object,rics=['US10YT=RR'],fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1']):#, eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
        """
        Get the fixings for the rics
        Important: Eikon must be running for this function to work properly!
        Args:
            rics: list of string
            fields :list of string
            ekObject: necessary to get data
        Return:
            pandas dataframe with real time data
        """
        df0= get_real_time(eikon_object,rics,fields)#.dropna(how='all')

        df=df0.set_index('Instrument')

        return df      


# def get_realtime_as_dataframe(eikon_object,rics=['US10YT=RR'],fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1']):#, eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
#         """
#         Get the fixings for the rics
#         Important: Eikon must be running for this function to work properly!
#         Args:
#             rics: list of string
#             fields :list of string
#             ekObject: necessary to get data
#         Return:
#             pandas dataframe with real time data
#         """
#         df0= get_real_time(eikon_object,rics,fields)#.dropna(how='all')

#         df=pd.DataFrame(df0,index=rics,columns=fields)
#         return df

def get_realtimeAsNpArray(rics=['US10YT=RR'],fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1'],eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
    return dataFrameToNpArray(get_real_time(rics,fields,eikon_key))    

def get_realtimeAsList(rics=['US10YT=RR'],fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1'],eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
    """
         Get the fixings for the rics
         Important: Eikon must be running for this function to work properly!
         Args:
             rics: list of string
             fields :list of string
             ek_key: string, eikon app key
         Return:
             pandas dataframe with real time data
         """
    return dataFrameToList(get_real_time(rics,fields,eikon_key)) 


def get_historicaldata_ricList(valuation_date='2020-11-25T10:00:00',rics=['US10YT=RR'],fields=['CLOSE'], eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
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
        ek.set_app_key('68665d71d1bb431aac39185b6153951aa479bec6')
        
        # Get the credit curve fixings
        fixings = ek.get_timeseries(rics=rics, fields=fields, start_date=valuation_date, end_date=valuation_date).T
        
        # display(ek.get_data(instruments=chain_ric, fields='CF_CLOSE')[0]) # real-time
        
        # Add tenor:
        get_tenor = lambda x: re.search('^[^0-9]+(\d+[a-zA-Z])', x).group(1) # lambda expression that retireves tenor from ric
        fixings.reset_index(inplace=True, drop=False)
        fixings['Tenor'] = fixings['CLOSE'].apply(get_tenor)
        fixings.set_index('Tenor', inplace=True)
        fixings.columns = ['RIC', 'Fixing']
        #fixings['ChainRIC'] = chainRic

        fixings = fixings[['ChainRIC', 'RIC', 'Fixing']]
    
        return fixings

# def getCurve_AsDataFrame1(curvName='0#AEURBMK=',fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1'],eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
#     """Generic utility function : return a curve in a dataframe type
#         Args :curvName,fields
#         Returns : dataframe qith curve data
#     """
#     chainRic = get_rta_chain_ric(chainRic=curvName)
#     dataCurve = get_realtimeAsDataFrame(chainRic,fields)
#     dataCurve.columns.name = curvName
#     # return  get_realtimeAsDataFrame(rics=get_rta_chain_ric(chainRic=curvName),fields=fields)   
#     return dataCurve
     

def getCurve_AsNpArray(curvName='0#AEURBMK=',fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1'],eikon_key='68665d71d1bb431aac39185b6153951aa479bec6'):
    return  get_realtimeAsNpArray(rics=get_rta_chain_ric(chainRic=curvName),fields=fields) 


# :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::Nw Rta Functions:::::::::::::::::::::::::::::::::::::::::::::::::::
#::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
   
def get_rta_chain_ric(ekObject,chainRic='0#AAFINEURBMK=',fields=['LONGLINK1']):
        """Get the chainric components
        Important: Eikon must be running for this function to work properly!
        Args: ekObject-->cession of eikon,chainric--> name of the curve 
        Return:list of rics to be used either for get_realtimeAsDataFrame or get_realtimeAsList or as an nparray
        """   
        try: rics_df, err = ekObject.get_data(chainRic, fields=fields) # отримати df з переліком ріків

        except Exception as ex: 
                print ("Exception Raised in get_rta_chain_ric using chainric name " + chainRic)
                print(ex)
                rics =  ['XAU=']

        else : rics = rics_df['Instrument'].to_list()

        return rics






def getRtaCurveAsDataFrame(eikonObject,curvName='0#AEURBMK=',fields=['GV4_TEXT','MATUR_DATE','RT_YIELD_1','SEC_YLD_1']):
        """Generic utility function : return a curve in a dataframe type
        Args :curvName,fields
        Returns : dataframe qith curve data
        """
        # chainRic constituents
        chainRic = get_rta_chain_ric(eikonObject,chainRic=curvName)

        # chainric  dataconstituents as a brut dataframe
        dataCurve = get_real_time(eikonObject,chainRic,fields)
        
        #Add thename of the curve 
        dataCurve.columns.name = curvName

        # cleaning the data
        curve= dataCurve.dropna()
        # curve.columns.name = curvName
    
        return curve

def getRtaCurveAsCleanNpArray(eikonObject,curvName,fields=['MATUR_DATE','RT_YIELD_1']):
    """Generic utility function: returns npArray from rtaas integers and rates
    Args:Takes a curvname, and the column of fieldsrelated to it (date,yields,rate....)
    Return:A npArray with dates and rates"""
    
    rtaCurveDf=getRtaCurveAsDataFrame(eikonObject,curvName,fields)
    
    #so we get number of days from 1 jan 1970 for any date
    rtaCurveDf['MATUR_DATE']=rtaCurveDf['MATUR_DATE'].transform(stringDateToNumOfDays) 

    rtaArray =rtaCurveDf.to_numpy()
    return rtaArray


################################################################################
# Tracs env
################################################################################

url_tracsConvB = "http://tracs-web-dtc-cps.int.thomsonreuters.com/tracsweb/plugin.svc/convb/Calculate/json2"

tracsHeaders = {'Content-Type' : 'application/json',
'X-TRACS-UserId':'SL1-28ZKFPE',
'X-TRACS-ApplicationId':'TRACS-DEV' }   


tracsKeys = ['Messages', 'TermsAndConditions', 'PricingAnalysisOutput', 'DatesOutput', 'YieldsOutput', 'MarketPrice', 'StockPrice', 'StockOverviewOutput', 'TimeMeasures']

basicReq0 = { "BondId":"XXXXXXXXXXXXX=","View":"","BondPriceType":"MarketPrice","PriceType":"Mid","SolveFor":"Price","IsCashQuoted":"false","ECreditType":"CreditCurve","VolType":"Flat","DeltaType":"Percent","GammaType":"Pts","DividendSource":"Multi","VolTermstructureType":"Historical","VolWithStock":"No","IsCdsFlatSpreadApplied":"false","CdsCurveType":"CdsSectorCurve","SelectedIndustrialSector":"OTHER FIN","ShockParameters":{"Legs":[],"SelectFlags":["true"]},"ScenarioAnalysis":{"Legs":[],"SelectFlags":["true","true"]}}


################################################################################
# Tracs Functions
################################################################################


#///////////////////////////////////////Tracs  fields of requests
tracsKeys = ['BondId', 'Messages', 'TermsAndConditions', 'PricingAnalysisOutput', 'DatesOutput', 'YieldsOutput', 'MarketPrice', 'StockPrice', 'StockOverviewOutput', 'SelectedZcCurve', 'AvailableZcCurves', 'AvailableEquityZcCurves', 'RiskCurvesOutput', 'PriceGridCurveOutput', 'IsImpliedVolAvailable', 'ReferenceData', 'IsCdsCurveAvailable', 'StockBorrowRate', 'BondRecoveryRate', 'SolveFor', 'VolType', 'FlatVolTenor', 'CheapnessType', 'NbrBonds', 'DeltaType', 'GammaType', 'ECreditType', 'VolTermStructureType', 'IsMiniCalc', 'TimeMeasures', 'CrossSpotRate', 'CrossCurrency', 'BondPriceType', 'CrossSpotRateQuotationType', 'DividendSource', 'Proceeds', 'CdsCurveType', 'SelectedIndustrialSector']
allTracsSubKeys = ['BondPrice', 'BondDirtyPrice', 'BondCleanPrice', 'BondFloor', 'OptionValue', 'Accrued', 'Parity', 'Premium', 'DollarPremium', 'CheapnessPct', 'HedgeRatio', 'FlatSpread', 'FlatSpreadTenor', 'DirtyPriceAmount', 'CleanPriceAmount', 'StockVolatility', 'BondCredit', 'ImpliedVolatility', 'ImpliedSpread', 'IsConvCashQuoted', 'CurrentYield', 'IsCentsQuoted', 'ExpectedLife', 'BreakEven', 'EffectiveDuration', 'EffectiveConvexity', 'SpreadDuration', 'SpreadConvexity', 'CallProba', 'PutProba', 'MatProba', 'ForcedConvProba', 'ConvProba', 'Delta', 'Gamma', 'Vega', 'Theta', 'Rho', 'Omicron', 'Chi', 'PriceType', 'PriceSourceRic', 'Bid', 'Ask', 'PriceQuotationType', 'PriceQuotationTime', 'PriceQuotationDate', 'PriceEarning', 'YieldToMaturity', 'YieldToWorst', 'YieldToBest', 'YieldToCall', 'YieldToPut', 'Yield', 'YieldDateToMaturity', 'YieldDateToWorst', 'YieldDateToCall', 'StockClose', 'VolatilityCurve', 'FxVolatility', 'IsDualCurrency', 'DividendTable', 'DividendForcastTable', 'DividendType', 'DividendProtectionType', 'DividendYield', 'DividendYieldGrowth', 'DividendYieldGrowthDate', 'StockOnDefault', 'AdvModelInputsTable', 'VolWithStock', 'SpreadDecay', 'FxStockCorrel', 'StockCurrency', 'FxVolTenorSelected', 'FxVolTenors']    

defaultKeys=['DatesOutput','PricingAnalysisOutput','YieldsOutput','TermsAndConditions']
defaultFields =  ['Ric','SettlementDate','BondPrice']
#////////////////////////////////////////////////////


def modifyTracsRequestField(req,field,value): 
    """Generic utility function: modifies the request by assigning value to key
    Args:Takes a dict, req , like { "BondId":"46647MRA3=","View":"","BondPriceType":"MarketPrice","PriceType":"Mid"}
    Return:A new dict with assigned value to key  field
    """
    new_req = copy.deepcopy(req)
    new_req[field]=str(value)
    return new_req


    # req[field]=value
    # return req

def modifyTracsRequestFromDict(req,dictOfFieldValues): 
    """Generic utility function: modifies the request by assigning each  value to each key from the dict
    Args:Takes a dict, req , like { "BondId":"46647MRA3=","View":"","BondPriceType":"MarketPrice","PriceType":"Mid"}
    Takes a dict of field values like : {BondId:XXXXXX, StockPrice : 150,....}
    Return:A new req dict with assigned values to key  fields
    """
    # new_req = copy.deepcopy(req)
    new_req=req.copy()
    for k in dictOfFieldValues.keys() : new_req=modifyTracsRequestField(new_req,k,dictOfFieldValues[k])
    return new_req



def modifyTracsRequestFieldLists(req,ListdictOfFieldValues): 
    """Generic utility function: modifies a request by assigning to a list of fields a list of values
    Args:Takes a dict, req , like { "BondId":"46647MRA3=","View":"","BondPriceType":"MarketPrice","PriceType":"Mid"}
    Return:A new list of dict with assigned value to key for one or several fields one or several values
    """
    requestArray = [modifyTracsRequestFromDict(req,dicty) for dicty in ListdictOfFieldValues]
    return requestArray

def postTracs_request(url=url_tracsConvB, headers=tracsHeaders, body=basicReq0 , return_error_content=False):

    """
    Generic utility function: post a request and return the ouput in json format.

        Args:
            url: string with url address, default is convb
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
    # we  use a defult response for the algorithm that extracts values in returnOutputsAsArray are ok
    
    try:
        response = requests.post(url=url, data=body, headers=headers) # post the request
        if response.ok: # check if response was a success
            #print(f"Request successful.\n")
            #json.loads() method, which is used for parse valid JSON String into Python dictionary.
            #encoding in utf-8-sig to remove the \ufeff frrm json response, then loads to get a json 
            json_response =json.loads( str(response.content, 'utf-8-sig') )
        else:
            print(f"Could not complete the request! Response content: {response.json()}\n")
            json_response =  {"headers": "none","data":  json.dumps(response.json()),"statuses":"none"}
    except Exception as ex:
        print(ex)
        print('Could not complete the request! No response received. Check URL, internet and VPN connection.\n')
        #json_response = 'No response received from Service!' # pad a dummy value into an output variable
        json_response =  {"headers": "none","data": "none","statuses":"none"}
    
    return json_response




def mergeTracsRespAsFlatDict (tracsResponse,subTracsKeys=defaultKeys) :
    """
    Generic utility function: #Merges the tacs response in flat dict
    Args :
    
         tracsresponse:  as a dict       
         subkeys : as a list (e.g ['PricingAnalysisOutput','YieldsOutput','StockOverviewOutput'])
    Returns:
         flattened tracs response  : as a flat dict {key:value,,,,,,,key:value}
    """
    # ListDict = [tracsResponse[k]  for k in subTracskeys  ]
    ListDict = [getCleanKey(dicty=tracsResponse,key=k) for k in subTracsKeys]
    return reduce(lambda d1,d2 : {**d1,**d2},ListDict,{})

def filterFieldsFromFlattenedResp (flatTracsResp,fieldList=defaultFields) :
        """
        Generic utility function : Takes all the flattened resp from tracs and filter only desired fields

        Args :
        
            flatTracsResp as a dict : {'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.258896}, 'BondFloor':.......}} 
            reducedPricingKeys : as a list (e.g ['BondPrice','BondFloor'])

        Returns :     

             flat dict with filtered fields : like  {'BondPrice':  'FieldValue': 2.258896}} if only one fields BondPrice si selected

                                              or {'BondPrice':   2.258896,BreakEven': none }} if breakeven is also selected but has no fieldvalue key 
                                              
        """

        return {key:getCleanKey(dicty=value) for key, value in flatTracsResp.items() if key in fieldList}

def returnTracsOutputsAsArray (dictResponse):  
        """
        Generic utility function :used to transform a flat dict to array
        
        Args :
        
            a flat dict : like {'BondPrice': 2.232363, 'BondFloor': 0.9851789999999999, 'OptionValue': 1.2471839999999998, 'BreakEven': 'none', 'YieldToMaturity': 0.0}

        Returns :     

             an array  : containing only the values '[2.232363, 0.9851789999999999, 1.2471839999999998, 'none', 0.0, 115.97999999999999]'
        
         """
        return [value for key, value in dictResponse.items()]      

def reqMultiTracsForPanda(tracsUrl,basicReq,ricList,fieldList) :

        """
        Generic utility function : Takes 2 lists of fields and rics and request tracs to get for each ric the pricing

        Args :
        
            tracsUrl  : url to post reauest
            basicReq : default request ot be modified
            ricList : list of rics
            fieldList : list of fields

        Returns :     

            array : matrix with nth line containg pricing of  nth ric     

        """
    

        requestArray = map(lambda x: modifyTracsRequestField (basicReq,'BondId',x),ricList)

        responseArray = map(lambda req : postTracs_request(body=req),requestArray)

        flatResponseArray = map(mergeTracsRespAsFlatDict,responseArray)

        reducedflatResponseArray = map(lambda x : filterFieldsFromFlattenedResp(x,fieldList),flatResponseArray)
       
        reducedflatResponseArrayForPanda = list(map(returnTracsOutputsAsArray,reducedflatResponseArray))

        return reducedflatResponseArrayForPanda

        

def reqMultiTracs(tracsUrl,requestArray,tracsKeys=defaultKeys,fieldList=defaultFields) :
    
        """
        Generic utility function : Takes 2 lists of fields and rics and request tracs to get for each ric the pricing

        Args :
        
            tracsUrl  : url to post reauest
            requestArray : an array containing all the requests to be sent
            fieldList : list of fields to be compared

        Returns :     

            array : list of dict. Nth item is containg pricing of  nth ric  as a dict   

        """
        responseArray = [postTracs_request(body=req) for req in requestArray]

        flatResponseArray = [mergeTracsRespAsFlatDict(tracsResponse=resp,subTracsKeys=tracsKeys) for resp in responseArray]

        reducedflatResponseArray = [filterFieldsFromFlattenedResp(flatResp,fieldList=fieldList) for flatResp in flatResponseArray]
       
        # reducedflatResponseArrayForPanda = list(map(returnTracsOutputsAsArray,reducedflatResponseArray))

        return reducedflatResponseArray




