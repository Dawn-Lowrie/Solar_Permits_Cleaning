import pandas as pd
import numpy as np


def extract_CPI_data(url: str) -> pd.DataFrame:
    '''
    uses pandas read_html function to read in data from an html format, selects the last table on the website (this should be the CPI data from my testing), and removes the last row since it includes unnecessary information
    '''
    tables: list[pd.DataFrame] = pd.read_html(url)       #   create a list of pandas dataframes of webscraped table data from the Bureau of Labor Statistics CPI data
    df = tables[-1]     #   select the last table (should be the table containing the CPI data)
    df = df[:-1]        #   remove the row with each entry stating 'X: Data unavailable due to the 2025 lapse in appropriations'
    return df       #   return the extracted CPI data as a pandas dataframe


def clean_CPI_data(df: pd.DataFrame) -> pd.DataFrame:
    '''
    function used for cleaning and transforming the CPI data from the BoLS so that it can be joined with existing data for inflation calculations based on the year and month
    '''
    df = df.drop(['HALF1', 'HALF2'], axis = 1)       #   remove the 'HALF1' and 'HALF2' columns from the dataframe as they are not necessary
    column_names = {'Jan': 1,       #   create list to change the month column names to their corresponding number (Jan->1, Feb->2, etc.)
                'Feb': 2,
                'Mar': 3,
                'Apr': 4,
                'May': 5,
                'Jun': 6,
                'Jul': 7,
                'Aug': 8,
                'Sep': 9,
                'Oct': 10,
                'Nov': 11,
                'Dec': 12}
    df.rename(columns = column_names, inplace = True)       #   replace the month names with those in the dict 'column_names'
    df = pd.melt(df,        #   use the melt function on the dataframe to rearrange its structure
                 id_vars = 'Year',      #   sets the 'Year' column as the identifier variables
                 var_name = 'Month',        #   sets the varibale column name to 'Month' (the variable column is the column headers except for 'Year')
                 value_name = 'CPI')        #   sets the value column name to 'CPI' (the value column is the data from the dataframe except for data from the 'Year' column)
    df.sort_values(['Year', 'Month'], axis = 0, ascending = True, inplace = True)       #   sorts the dataframe by year then month so all data should be grouped by month for each year in an ascending order
    df.reset_index(drop = True, inplace = True)     #   resets the index so the index follows the new order of data (this step is mostly taken to keep things neat and easier to understand)
    df['Month'] = df['Month'].map(str)      #   convert the 'Month' column to str datatype
    return df       #   returns the now cleaned dataframe


def replace_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    '''
    as of 8/10/2026 there exists one instance in the CPI data in Oct. 2025 where there is no entry (denoted with a value '-(X)').
    this function finds all instances of '-(X)' (in case data isn't collected for any future months) and uses numpy's interp function to conduct linear interpolation to fill in missing data
    '''
    missing_data_indice = df[df['CPI'] == '-(X)'].index.tolist()        #   extracts the indices for missing CPI data denoted by '-(X)' (data from Oct 2025 is missing due to the government shutdown)

    df = df.replace('-(X)', None)       #   replaces '-(X)' values with NULL so 'CPI' column can have a numeric datatype instead of string
    df['CPI'] = pd.to_numeric(df['CPI'])        #   changes the 'CPI' datatype to numeric

    temp_df = df.dropna()       #   creates a temporary dataframe where all NULL values are removed (if NULLS are left in, np.interp will return NULL values for that index instead of a calculated value)

    xp = np.array(temp_df.index.tolist(), dtype = 'float64')        #   creates a numpy array of all the indices with the datatype of 'float64' (np.interp throws an error if the dtype isn't 'float64')
    fp = np.array(temp_df['CPI'].values.tolist(), dtype = 'float64')        #   creates a numpy array of all the CPI data with the datatype 'float64' (np.interp throws an error if the dtype isn't 'float64')

    interp_list = np.interp(missing_data_indice, xp, fp).tolist()        #   creates a list of interpretted values from the missing_data_indice list

    #   replace all 'CPI' data with interpretted data from interp_list for the corresponding index
    for N in range(len(missing_data_indice)):       #   for the values in the range of the length of the missing_data_indice list
        df.loc[missing_data_indice[N], 'CPI'] = interp_list[N]      #   replace the CPI data of index missing_data_indice[N] with the Nth value in the interp_list

    df = df.dropna()        #   remove the trailing NULL columns from months without data (values for CPI data that hasn't been collected is NULL)
    return df       #   return the dataframe with missing CPI values estimated based on linear interpolation


def CPI_data(url: str) -> pd.DataFrame:
    '''
    function that extracts, cleans, and replaces missing data all at once.
    data is found at https://data.bls.gov/timeseries/CUUR0000SA0?years_option=all_years as of 8/10/26
    '''
    df = replace_missing_values(        #   replaces '-(X)' values with estimate
            clean_CPI_data(     #   cleans the extracted CPI data
                extract_CPI_data(url)       #   extracts the CPI data from the url
                )
            )
    
    return df       #   returns the final CPI data


def merge_CPI(df: pd.DataFrame, date_column_name: str, cpi_df: pd.DataFrame) -> pd.DataFrame:
    '''
    function that creates matching 'Year' and 'Month' columns to a dataset and combines it with the cpi data so that each datapoint should have their corresponding CPI value based on the year and month of a selected date column
    '''
    df['Year'] = pd.to_datetime(df[date_column_name]).dt.year       #   extract the year from the specified date column and save it to a new column 'Year'
    df['Year'] = df['Year'].map(str)        #   convert the 'Year' column to a str datatype
    df['Month'] = pd.to_datetime(df[date_column_name]).dt.month     #   extract the month from the specified date column and save it to a new column 'Month'
    df['Month'] = df['Month'].map(str)      #   conver the 'Month' column to a str datatype

    merged_df = pd.merge(df, cpi_df, on = ['Year', 'Month'], how = 'left')      #   join df with cpi_df on the shared year and month columns

    return merged_df        #   return the merged dataframe

def calculate_inflation_adjustment(df: pd.DataFrame, date_column_name: str, price_column_name: str, cpi_url: str):
    '''
    uses the CPI_data function to extract and clean CPI data from the Bereau of Labor Statistics (https://data.bls.gov/timeseries/CUUR0000SA0?years_option=all_years), merges that data with a given dataset on corresponding date column, then calculates the inflation amount based on the most recent data provided by the Bureau of Labor Statistics
    '''
    cpi_df = CPI_data(cpi_url)      #   uses the CPI_data function to extract and clean the consumer price data from the Bureau of Labor Statistics

    current_year, current_month, current_cpi = cpi_df.iloc[-1]['Year'], cpi_df.iloc[-1]['Month'], cpi_df.iloc[-1]['CPI']        #   extract the most recent year, month, and CPI data for labeling the inflation adjusted column and making the adjustment calculation

    df = merge_CPI(df, date_column_name, cpi_df)        #   use the merge_CPI function to merge df with the CPI data using the corresponding dates
    df[f'{price_column_name}_{current_month}_{current_year}'] = round((((current_cpi - df['CPI'])/df['CPI'])+1) * df[price_column_name], 2)     #   calculate the price adjusted for inflation and save it in a column with the month and date corresponding with the most recent CPI data used for the calculation

    df = df.drop(['Year', 'Month', 'CPI'], axis =1)     #   drop the 'Year', 'Month', and 'CPI' columns from the dataset after the inflation price was calculated
    return df       #   returns the dataframe with the newly calculated inflation adjusted column