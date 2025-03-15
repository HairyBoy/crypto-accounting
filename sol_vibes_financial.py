import pandas as pd


# TODO: ADD CASHOUT 


def calculate_transaction_data(data):
    
    data_dict = {}
    
    data = data.copy()
    
    data_dict['receipts'] = calculate_transaction_type(data, 'RECEIVE')
    data_dict['rewards'] = calculate_transaction_type(data, 'MULTI_TOKEN_TRADE')
    data_dict['transfers'] = calculate_transaction_type(data, 'TRANSFER')
    data_dict['payments'] = calculate_transaction_type(data, 'SEND')
    data_dict['stakings'] = calculate_transaction_type(data, 'STAKE')
    data_dict['investments'] = calculate_transaction_type(data, 'INVESTMENT')
    data_dict['trades'] = calculate_trades(data)
    
    
    return data_dict


'''
For a given transaction type, calculate the amount of currency moved, the cost basis of the amount moved,
and the realized gains and losses (separate), for each currency in the data set
'''
def calculate_transaction_type(data, transaction_type):

    # Filter the data to only transactions of the type desired
    data = (data[data['Type'] == transaction_type]).copy()

    # Using the transaction type, determine the direction of the currency transfer in order to read data from the correct column from the transactions table
    currency_directions = {
        'RECEIVE': 'Received',
        'MULTI_TOKEN_TRADE': 'Received',
        'TRANSFER': 'Received',
        'SEND': 'Sent',
        'STAKE': 'Sent',
        'INVESTMENT': 'Received' # this is a custom one i made
    }
    cur_dir = currency_directions[transaction_type]

    # Create a dictionary to hold the processed transaction information for each currency
    info_dict = {}
    
    # Loop through each unique currency of the data set (of the currencies that were sent in the desired direction)
    for currency in set(data[cur_dir + ' Currency']):

        # Filter data for just this currency
        cur_data = data[data[cur_dir + ' Currency'] == currency]
        # Create a dictionary entry to hold this currency's data
        info_dict[currency] = {}

        # Sum up the quantity sent/received
        qty = sum(cur_data[cur_dir + ' Quantity'])
        # Sum up the cost basis of the quantity sent/received
        cb = sum(cur_data[cur_dir + ' Cost Basis (USD)'])
        # Sum up the realized gains of the quantity sent/received
        rg = sum(cur_data[cur_data['Realized Return (USD)'] > 0]['Realized Return (USD)'])
        # Sum up the realized losses of the quantity sent/received
        rl = sum(cur_data[cur_data['Realized Return (USD)'] < 0]['Realized Return (USD)'])

        # Store values in the dictionary entry for this currency
        info_dict[currency]['qty'] = qty
        info_dict[currency]['cb'] = cb
        info_dict[currency]['rg'] = rg
        info_dict[currency]['rl'] = rl

    return info_dict

'''
For transaction type TRADE, calculate the amount of currency moved, the cost basis of the amount moved,
and the realized gains and losses (separate), for each currency in the data set
'''
def calculate_trades(data):

    # Filter the data to only transactions of the type desired
    data = (data[data['Type'] == 'TRADE']).copy()

    # Create a dictionary to hold the processed transaction information for each currency
    trd_dict = {}

    # Make a list of all the currencies involved in trades
    currency_list = list(data[data['Type'] == 'TRADE']['Sent Currency']) + list(data[data['Type'] == 'TRADE']['Received Currency']) 

    # Loop through each unique currency of the data set
    for currency in set(currency_list):

        # Create a dictionary entry to hold this currency's data
        trd_dict[currency] = {}

        # Sum up the quantity sent
        sent_qty = sum(data[data['Sent Currency'] == currency]['Sent Quantity'])
        # Sum up the cost basis of the quantity sent
        sent_cb = sum(data[data['Sent Currency'] == currency]['Sent Cost Basis (USD)'])
        # Sum up the realized gains of the quantity sent
        sent_rg = sum(data[(data['Sent Currency'] == currency) & (data['Realized Return (USD)'] > 0)]['Realized Return (USD)'])
        # Sum up the realized losses of the quantity sent
        sent_rl = sum(data[(data['Sent Currency'] == currency) & (data['Realized Return (USD)'] < 0)]['Realized Return (USD)'])
        # Sum up the quantity received
        rec_qty = sum(data[data['Received Currency'] == currency]['Received Quantity'])
        # Sum up the cost basis of the quantity received
        rec_cb = sum(data[data['Received Currency'] == currency]['Received Cost Basis (USD)'])

        # Store values in the dictionary entry for this currency
        trd_dict[currency]['sen_qty'] = sent_qty
        trd_dict[currency]['sen_cb'] = sent_cb
        trd_dict[currency]['rg'] = sent_rg
        trd_dict[currency]['rl'] = sent_rl
        trd_dict[currency]['rec_qty'] = rec_qty
        trd_dict[currency]['rec_cb'] = rec_cb

    return trd_dict

def income_table(transaction_data):

    income_rows = []
    revenue = 0
    
    receipts = transaction_data['receipts']
    for token in receipts:
        revenue += receipts[token]['cb']
        income_rows.append([(token + ' receipts'), receipts[token]['cb']])
    rewards = transaction_data['rewards']
    for token in rewards:
        revenue += rewards[token]['cb']
        income_rows.append([(token + ' rewards'), rewards[token]['cb']])
    trades = transaction_data['trades']
    for token in trades:
        if(trades[token]['rg'] != 0):
            revenue += trades[token]['rg']
            income_rows.append([(token + ' trades'), trades[token]['rg']])
    income_rows.append(['Total', revenue])
    
    df = pd.DataFrame(income_rows, columns=['Source', 'Amount'])
    return df

def pl_table(transaction_data):

    # Create a list that will hold entries for the dataframe of income and expense line items
    data_rows = []
    
    # Set up a variable to keep a running total of total revenue
    revenue = 0
    # Set up a variable to keep a running total of total expenses
    expenses = 0

    # Add a line item for the receipts of each type of token
    receipts = transaction_data['receipts']
    for token in receipts:
        revenue += receipts[token]['cb']
        data_rows.append(['Income', (token + ' receipts'), receipts[token]['cb']])

    # Add a line item for the rewards of each type of token
    rewards = transaction_data['rewards']
    for token in rewards:
        revenue += rewards[token]['cb']
        data_rows.append(['Income', (token + ' rewards'), rewards[token]['cb']])

    # Add a line item for the trades of each type of token
    trades = transaction_data['trades']
    for token in trades:
        if(trades[token]['rg'] != 0):
            revenue += trades[token]['rg']
            data_rows.append(['Income', (token + ' trades (realized gains)'), trades[token]['rg']])
        if(trades[token]['rl'] != 0):
            expenses += trades[token]['rl']
            data_rows.append(['Expense', (token + ' trades (realized losses)'), trades[token]['rl']])

    # Add line items for the payments of each type of token
    payments = transaction_data['payments']
    for token in payments:
        revenue += payments[token]['rg']
        expenses += payments[token]['cb'] + payments[token]['rg'] + payments[token]['rl'] # Add the fair market value to expenses
        expenses += -payments[token]['rl'] # Add realized losses to expenses
        data_rows.append(['Income', (token + ' payments (realized gains)'), payments[token]['rg']])
        data_rows.append(['Expense', (token + ' payments (realized losses)'), -payments[token]['rl']])
        data_rows.append(['Expense', (token + ' payments (fair market value)'), payments[token]['cb']+payments[token]['rg']+payments[token]['rl']])

    # Print out the summary of revenue and expenses
    print('-Total Revenue: ', revenue, '\n')
    print('-Total Expenses: ', expenses, '\n')
    print('Profit: ', revenue - expenses)

    # Turn the list of lists into a structured dataframe and return the dataframe
    df = pd.DataFrame(data_rows, columns=['Type', 'Source', 'Amount'])
    return df

def accounting_stats(transaction_data):
    
    
    print('Accounting Profit/Loss\n')
    
    print('Income (USD):')
    revenue = 0
    receipts = transaction_data['receipts']
    for token in receipts:
        revenue += receipts[token]['cb']
        print('---', token, 'receipts:\t', receipts[token]['cb'])
        
    rewards = transaction_data['rewards']
    for token in rewards:
        revenue += rewards[token]['cb']
        print('---', token, 'rewards:\t', rewards[token]['cb'])
        
    trades = transaction_data['trades']
    for token in trades:
        if(trades[token]['rg'] != 0):
            revenue += trades[token]['rg']
            print('---', token, 'trades:\t', trades[token]['rg'])

    payments = transaction_data['payments']
    for token in payments:
        revenue += payments[token]['rg']
        print('---', token, 'payments (realized gains):\t', payments[token]['rg'])
            
    print('-Total: ', revenue, '\n')
    
    
    print('Expenses (USD):')
    expenses = 0
    payments = transaction_data['payments']
    for token in payments:
        expenses += payments[token]['cb']
        print('---', token, 'payments (fair market value):\t', payments[token]['cb'] + payments[token]['rl'] + payments[token]['rg'])
        print('---', token, 'payments (realized losses):\t', -payments[token]['rl'])

    trades = transaction_data['trades']
    for token in trades:
        if(trades[token]['rl'] != 0):
            revenue += trades[token]['rl']
            print('---', token, 'trades:\t', trades[token]['rl'])
            
    print('-Total: ', expenses, '\n')
    
    
    print('Profit: ', revenue - expenses)

    
def asset_flow_table(data):
    
    data = data.copy()

    token_list = []
    for x in data:
        for y in data[x]:
            if(y==y): # removes the NaN values
                token_list.append(y)
    
    token_flows = []
    
    for token in set(token_list):
        
        token_df = {}
        
        token_df['name'] = token
        
        for trans_type in ['receipts', 'rewards', 'payments', 'investments']:
            try:
                token_df[trans_type] = data[trans_type][token]['qty']
            except KeyError:
                token_df[trans_type] = 0
                
        try:
            token_df['trade_for'] = data['trades'][token]['rec_qty']
        except KeyError:
            token_df['trade_for'] = 0
            
        try:
            token_df['trade_away'] = data['trades'][token]['sen_qty']
        except KeyError:
            token_df['trade_away'] = 0

        # TODO: fix 
        token_df['cash_out'] = 0
        
        token_flows.append(token_df)
        
    df = pd.DataFrame(token_flows)
    
    df['total_positive'] = df['receipts'] + df['rewards'] + df['investments'] + df['trade_for']
    df['total_negative'] = df['payments'] + df['trade_away']
    df['net_flow'] = df['total_positive'] - df['total_negative']

    return(df)