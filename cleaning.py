import pandas as pd


address2_entry_tuple = ('APEX', 'CARY', 'MORRISVILLE', 'RALEIGH', 'STE')        #   tuple containing common values found in the address2 column. for example 'APEX, NC' or 'STE 123'


def zip_clean(data_frame: pd.DataFrame, column: str):
    '''
    function that takes in a data frame and string value of the column you're wanting to clean the zipcode of.
    e.g. #####-####
    '''
    data_frame.loc[data_frame[column].str.len() == 9, column] = data_frame[column].str[:5] + '-' + data_frame[column].str[5:]       #   if the length of the value in the column in the dataframe is equal to 9, it splits the string so that it is the first 5 characters a hyphen followed by the last 4 characters


def is_address1(address: str) -> bool:
    '''
    function that determines whether an entry, address, starts or ends with a number.
    US addresses typically start with a number, and po boxes typically end with one.
    '''
    if not isinstance(address, str) or not address:       #   if address is not a string or is empty
        return False        #   returns False
    return address[0].isnumeric() or address[-1].isnumeric()        #   returns 'True' if address begins or ends with a numeric character


def is_address2(address: str) -> bool:
    '''
    a function that takes the values from address2 and determines whether they should belong in the address2 column
    '''
    if not isinstance(address, str) or not address:     #   if address is not a string or is empty
        return False        #   returns False
    address_list = address.upper().replace(',', ' ').replace('.', ' ').split()      #   makes address all uppercase, replaces all commas and periods with whitespace, and splits address into a list of characters between the beginning, whitespace, and end
    return any(x in address2_entry_tuple for x in address_list)     #   if any of the entries in address_list are also in address2_entry_tuple, returns True


def owner_address_reorder(name: str, address1: str, address2: str) -> list[str]:
    '''
    a function that takes the name and address data and organizes them into the order they should be.
    some names are segmented and inserted into the address columns
    '''
    if is_address1(address1):
        if is_address1(address2) or is_address2(address2):     #   if address1 and address2 both contain address information, then the order remains
            name = name
            address1 = address1
            address2 = address2
        else:       #   else address 2 contains a name and is joined with name
            name = name + address2
            address1 = address1
            address2 = ''
    else:
        if is_address2(address2):     #   if address1 isn't an address and address2 is correct, then address1 is joined with name and address1 is nulled
            name = name + address1
            address1 = ''
            address2 = address2
        elif is_address1(address2):     #   if address1 isn't an address and address2 is, then address1 is joined with name and address1 is replaced with address2
            name = name + address1
            address1 = address2
            address2 = ''
        else:       #   else address1 and address2 aren't address data and joined with name
            name = name + address1 + address2
            address1 = ''
            address2 = ''
    cleaned_values = [name, address1, address2]     #   outputs a list of the organized name and address data
    return cleaned_values

def owner_address_clean(data: pd.DataFrame, name: str, address1: str, address2: str) -> pd.DataFrame:
    '''
    applies the owner_address_reorder function to a dataset and replaces those values with the cleaned versions for each column
    '''
    data['clean'] = [owner_address_reorder(x, y, z) for x, y, z in zip(data[name], data[address1].fillna(''), data[address2].fillna(''))]       #   adds a temporary 'clean' column to the dataset and uses the owner_address_reorder function to clean the name and address data for owners. this saves the cleaned data as a list in the 'clean' column, which will have to be sorted. fillna was used to convert NaN data to '' so the function can work properly
    data[name] = data['clean'].apply(lambda x: x[0])        #   replaces the name data with the reordered data from the 'clean' column
    data[address1] = data['clean'].apply(lambda x: x[1])        #   replaces the address1 data with the reordered data from the 'clean' column
    data[address2] = data['clean'].apply(lambda x: x[2])        #   replaces the address2 data with the reordered data from the 'clean' column
    data = data.drop('clean', axis = 1)     #   drops the temporary 'clean' column after all data has been sorted

    return data     #   returns the cleaned owner address data


def contractor_address_reorder(address1: str, address2: str) -> list[str]:
    '''
    a function that switches the order of two address columns if address1 is an address or not (determined by is_address1 function)
    '''
    if is_address1(address1) and not is_address2(address1):       #   if address1 is an an address but not something like 'STE 123'
        return [address1, address2]     #   address1 should be first
    else:       #   if address1 is not an address
        return [address2, address1]     #   address2 should be first


def contractor_address_clean(data: pd.DataFrame, address1: str, address2: str) -> pd.DataFrame:
    data['clean'] = [contractor_address_reorder(x, y) for x, y in zip(data[address1], data[address2])]        #   adds a temporary 'clean' column to the dataset and uses the contractor_address_reorder function to clean the address1 and address2 data for contractors. this saves the cleaned data as a list in the 'clean' column, which will have to be sorted
    data[address1] = data['clean'].apply(lambda x: x[0])        #   replaces the address1 data with the reordered data from the 'clean' column
    data[address2] = data['clean'].apply(lambda x: x[1])        #   replaces the address2 data with the reordered data from the 'clean' column
    data = data.drop('clean', axis = 1)     #   drops the temporary 'clean' column after all data has been sorted

    return data     #   returns the cleaned contractor address data