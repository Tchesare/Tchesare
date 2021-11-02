'''This Module is used to check of import works fine'''
print('Imported my_module...')

TEST = 'test_string'

def find_index(to_serach,target):
    '''returns the index of the target if available'''
    res = -1
    for i,value in enumerate(to_serach):
        if (value==target) : res=i      
    return res