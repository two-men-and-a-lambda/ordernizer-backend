import pandas
from endpoints import *

def test():
    r = 'retail_test.csv'
    w = 'wholesale_test.csv'
    result = {'generate_result': [generate_result(r, w), pd.read_csv('generate_result.csv')], 'submit_sale': [submit_sale({'bananas': {'price': 10, 'units': 20}, 'apples': {'price': 30, 'units': 23}, 'timestamp': '2023-01-30 04:25:01'}, 'retail_test.csv'), pd.read_csv('submit_sale.csv')], 'submit_order': [submit_order({'bananas': {'price': 10, 'units': 20}, 'apples': {'price': 30, 'units': 100}, 'timestamp': '2023-01-30 04:25:01'}, 'wholesale_test.csv'), pd.read_csv('submit_order.csv')], 'submit_inventory': [submit_inventory({'bananas': 20, 'apples': 23, 'timestamp': '2023-01-30 04:25:01'}, 'retail_test.csv', 'wholesale_test.csv'), pd.read_csv('submit_inventory.csv')]}
    pass_fail_dict = {}
    for key, value in result.items():
        df1 = value[0]
        df2 = value[1]
        eq = df1.equals(df2)
        pass_fail_dict[key] = eq
        print('*'*50,key,'*'*50)
        if not eq:
            print('#'*50, 'FAIL', '#'*50)
        print('\nWHOLESALE:\n\n',pd.read_csv('wholesale_test.csv'))
        print('\nRETAIL:\n\n',pd.read_csv('retail_test.csv'))
        print('\nYOUR ANSWER:\n\n', df1)
        print('\nCORRECT ANSWER:\n\n', df2)
    print('\n\n')    
    for key, value in pass_fail_dict.items():
        print(key, ' '*(16-len(key)), 'PASS' if value else 'FAIL')
        

test()