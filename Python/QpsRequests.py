from importlib.machinery import SourceFileLoader # for import of functions.py
f = SourceFileLoader('functions', 'C:/Users/U0168118/Documents/Automation/VsCode/Python/functions.py').load_module()  # for import of functions.py

import requests
import pandas as pd
import functools as fnctls

 #Content type must be included in the header
qpsHeaders = {'Content-Type' : 'application/json',
'X-Tr-ApplicationId' : 'QPSInternal',
'X-Tr-Uuid':'PAXTRA-645406493',
'X-Tr-Scope':'qps_internal_access' }   
    
url_post = "http://qps-valuationasl-204937-main-development.apt-preprod.aws-int.thomsonreuters.com/request/"

#the python dict request
qpsBasicReq = {"fields": ["CleanPrice", "FairPrice"], 

"outputs": ["headers","Data","Statuses"], 

"universe": [ { "instrumentType": "Bond", "instrumentDefinition": {  "instrumentCode": "185899AA9="  },    

 "pricingParameters": 

 { 
     "marketdataDate": "2020-10-22",
     "priceSide": "Mid",
     "CreditSpreadType": "TermStructure",
     "VolatilityType": "Flat",
     "StockFlatVolatilityTenor": "30D",

     "UseA4Pricer": "false",
     "UseMetadataFromEjv": "true",
     "UseAdditionalEjvMetadataFromAdc":"true"} 

 }]}


pricingdate="2020-10-27"
qpsBasicReq=f.modifyQpsRequestMarketDataDate(qpsBasicReq,pricingdate)


rics = ["74965L200=","185899AA9="]
fields =["CleanPrice","FairPrice","DeltaPercent","ConversionPeriodEndDates","ConversionRatios","UnderlyingAsset"]

# Retunrs a list of requests to be posted 
requestArray = map(lambda x: f.modifyQpsRequestRic (qpsBasicReq,x),rics)
requestArray = map(lambda req: f.modifyQpsRequestFields (req,fields),requestArray)


print(list(requestArray))

responseArray = map(lambda req : f.requestThenFormatQpsForPanda(url_post,qpsHeaders,req),requestArray)
for resp in responseArray:print(resp)  



responseArray2 = f.reqMultiQpsForPanda(basicReq=qpsBasicReq,ricList=rics,fieldList=fields)
print(responseArray2)




    