resp = {'TestingField': {'FromData': False},'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.3484309999999997}, 'BondFloor': {'FromData': False, 'Status': 'Computed', 
'FieldValue': 0.984868}, 'OptionValue': {'FromData': False, 'Status': 'Computed', 'FieldValue': 1.363564}, 'Parity': {'FromData': False, 'Status': 'Computed', 'FieldValue': 229.359293812}, 'Premium': {'FromData': False, 'Status': 'Computed', 'FieldValue': -56.400284314631925}, 'CurrentYield': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.0}, 'IsCentsQuoted': {'FromData': True, 'Status': 'Data', 'FieldValue': False}, 'ExpectedLife': {'FromData': False, 'Status': 'Computed', 'FieldValue': 1.7785104019350828}, 
 'EffectiveDuration': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.225430879686248}, 'EffectiveConvexity': {'FromData': False, 'Status': 
'Computed', 'FieldValue': 0.0}, 'SpreadDuration': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.24580634951431968}, 'SpreadConvexity': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.0}, 'CallProba': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.0}, 'PutProba': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.0}, 'MatProba': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.24226012451497636}, 'ForcedConvProba': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.0}, 'ConvProba': {'FromData': False, 'Status': 'Computed', 
'FieldValue': 0.6827582688527541}, 'Delta': {'FromData': False, 'Status': 'Computed', 'FieldValue': 93.02052793634996}, 'Gamma': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.8580091017238093e-05}, 'Vega': {'FromData': False, 'Status': 'Computed', 'FieldValue': 0.472353381909727}, 'Theta': {'FromData': False, 'Status': 'Computed', 'FieldValue': -0.014133799140864767}, 'Rho': {'FromData': False, 'Status': 'Computed', 'FieldValue': -0.5288239521803462}}

#takes a dict like {'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.3484309999999997}
def fx (dctnry,key,subkey):
        return {key:dctnry[key][subkey]}


# tests igf the dict has a key value
def testKeyValue(dicty,key) : 
        return True  if key in dicty.keys() else False
  

# smalldict = {'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.3484309999999997}}
# x = fx(resp,'BondPrice','FieldValue')

# print(x)

# reducedPricingDict3 = {key: resp[key]['FieldValue'] for key in resp.keys()}
# #each elts of resp is  a dict like :  {'BondPrice': {'FromData': False, 'Status': 'Computed', 'FieldValue': 2.3484309999999997}
# #reducedPricingDict3 = map(lambda dctnry,key :fx (dctnry,key,'FieldValue'),resp,resp.keys())
# print(dict(reducedPricingDict3))

#pricingDictKeys= pricingDict.keys()   #["PricingAnalysisOutput.BondPrice.FieldValue"]
reducedPricingKeys = ['TestingField','BondPrice',  'BondFloor','hjhkhkjhkjhnk']

print('\n ')

#reducedPricingDict = {key: testKeyValue(resp,key) for key in reducedPricingKeys and  resp.keys() }
reducedPricingDict = {key:value for key, value in resp.items() if key in reducedPricingKeys}

print('\n ')
print(reducedPricingDict)



#reducedPricingDict2 = {key: testKeyValue(reducedPricingDict[key],'FieldValue') for key in reducedPricingDict.keys()}   
reducedPricingDict2 = {key:value['FieldValue'] for key,value in reducedPricingDict.items() if 'FieldValue' in value.keys()} 
print('\n ')
print(reducedPricingDict2)