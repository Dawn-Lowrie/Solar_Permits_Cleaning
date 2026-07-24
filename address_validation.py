import googlemaps       #   library googlemaps API
import pandas as pd         #   library pandas

def validate_address(key, data, address_column, city_column):
    '''
    a function that uses the googlemaps address validation using address and city data from a dataset
    '''
    validation = key.addressvalidation(     #   use the google maps api to validate address with personal api key
        data[address_column],       #   take the address column from the data
        regionCode = 'US',      #   set regionCode to 'US' since all addresses are in th US
        locality = data[city_column] if pd.notna(data[city_column]) else '',        #   take the city column from the data if it is not empty otherwise use '' (one instance where city name is na, which throws an error if not accounted for)
        enableUspsCass = True)      #   sets USPS CASS to True to improve validation accuracy
    return validation

def apply_address_validation(dataframe: pd.DataFrame, address_column: str, city_column:str, googlemaps_key: str, existing_data: pd.DataFrame | None = None, primary_key: str | None = None) -> pd.DataFrame:
    '''
    a function that applies the validate_address function to an entire dataset based on address and city data
    if address validation has already been ran on a previous version of the data, this function only applies address validation to new columns based on a primary key ('permitnum' for solar permits dataset)
    '''
    gmaps_key = googlemaps.Client(key = googlemaps_key)     #   google maps api key
    if existing_data is None:       #   if no existing data is given then all rows are validated
        dataframe['address_validation'] = dataframe.apply(lambda row: validate_address(gmaps_key, row, address_column, city_column), axis = 1)      #   applies the validate_address function to the data by row (can be slow for large datasets)
        dataframe['validated_address'] = [x['result']['address']['formattedAddress'] for x in dataframe['address_validation']]        #   extracts the formatted address and saves it to a new column 'validated_address'
        dataframe['latitude'] = [x['result']['geocode']['location']['latitude'] for x in dataframe['address_validation']]       #   extracts the latitude data and saves it to a new column 'latitude'
        dataframe['longitude'] = [x['result']['geocode']['location']['longitude'] for x in dataframe['address_validation']]     #   extracts the longitude data and saves it to a new column 'longitude'
        dataframe = dataframe.drop('address_validation', axis = 1)      #   drops the 'address_validation' column since it is a bit hard to read after all useful information has been extracted
    else:       #   if there is existing data given then only new rows (based on a primary key) are validated
        new_data = pd.merge(dataframe, existing_data[primary_key], how = 'left_anti', on = primary_key)     #   merges the dataframe with the existing data and only keeps those unique to the dataframe based on the primary key
        new_data['address_validation'] = new_data.apply(lambda row: validate_address(gmaps_key, row, address_column, city_column), axis = 1)        #   applies the validate_address function to the data by row (can be slow for large datasets, but should be faster than validating the entire dataset without removing the existing data)
        new_data['validateaddress'] = [x['result']['address']['formattedAddress'] for x in new_data['address_validation']]      #   extracts the formatted address and saves it to a new column 'validated_address'
        new_data['latitude'] = [x['result']['geocode']['location']['latitude'] for x in new_data['address_validation']]     #   extracts the latitude data and saves it to a new column 'latitude'
        new_data['longitude'] = [x['result']['geocode']['location']['longitude'] for x in new_data['address_validation']]       #   extracts the longitude data and saves it to a new column 'longitude'
        new_data = new_data.drop('address_validation', axis = 1)        #   drops the 'address_validation' column since it is a bit hard to read after all useful information has been extracted
        dataframe = pd.concat([existing_data, new_data], axis = 0)      #   adds the new data to the existing data
    return dataframe