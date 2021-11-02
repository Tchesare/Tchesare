print('Hello World')

from functions import *

print(string_list_to_float_list(['0','1']))

print(string_list_to_float_list(['okmpokpo','1']))

cap_dict = load_json_from_file(r'C:\VSCODE\Python\NoteBook\cap_response_with_details.json')

for item in cap_dict['data']:
    print(item.keys())
    #dict_keys(['pricerUrl', 'pricerRequest'])