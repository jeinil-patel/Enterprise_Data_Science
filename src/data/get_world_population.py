# %load ../src/data/get_world_population.py

import pandas as pd
import numpy as np
from datetime import datetime

def get_large_dataset():
    ''' Get COVID confirmed case for all countries

    '''
    # get large data frame
    df_full=pd.read_csv('../data/processed/COVID_final_set.csv',sep=';')  
    df_full.reset_index(drop=True)

    country_list = df_full.country.unique()
    
    # convert date to datetime format
    t_idx = [datetime.strptime(date,"%Y-%m-%d") for date in df_full.date] 
    t_str = [each.strftime('%Y-%m-%d') for each in t_idx] 
    df_full['date'] = t_idx
    
    # featch confirmed cases of all countries
    df = df_full.drop(['state'], axis=1).groupby(['country', 'date'])['confirmed'].sum()
    df_confirmed = pd.DataFrame()
    df_confirmed['date'] = df['Canada'].index
    for each in country_list:
        df_confirmed[each] = df[each].values
    
    return df_confirmed

import requests
from bs4 import BeautifulSoup

def world_population():
    
    # get large data frame
    df_full=pd.read_csv('../data/processed/COVID_final_set.csv',sep=';')  
    df_full.reset_index(drop=True)

    country_list = df_full.country.unique()
    
    page = requests.get("https://www.worldometers.info/coronavirus/")    # get webpage
    soup = BeautifulSoup(page.content, 'html.parser')                    # get page content 
    
    # scrap table data from page content into a list 
    html_table= soup.find('table')                 # find the table in the page content
    all_rows= html_table.find_all('tr')            # filn rows in table data

    final_data_list= []
    for pos,rows in enumerate(all_rows):
        col_list= [each_col.get_text(strip= True) for each_col in rows.find_all('td')]     # td for row element
        final_data_list.append(col_list)

    # convert list into DataFrame with proper labling
    pd_daily=pd.DataFrame(final_data_list)
    
    df_population = pd.DataFrame()
    df_population['population'] = pd_daily[14][9:223]    # get only population column 
    df_population['country'] = pd_daily[1][9:223]        # respective country names
    
    # convert number seperator
    df_population['population'] = df_population.apply(lambda x: x.str.replace(',',''))
    df_population = df_population.reset_index(drop=True)
    # convert string to number
    df_population['population']  = pd.to_numeric(df_population['population'], errors='coerce')
    
    # some country names are different in Jhon Hopkins dataset and Worldometer data, therefore we have to plausiblise it
    df_population['country'] = df_population['country'].replace('S. Korea', 'Korea, South')
    df_population['country'] = df_population['country'].replace('USA', 'US')
    df_population['country'] = df_population['country'].replace('Taiwan', 'Taiwan*')
    df_population['country'] = df_population['country'].replace('UAE', 'United Arab Emirates')
    df_population['country'] = df_population['country'].replace('UK', 'United Kingdom')
    
    # plausiblize data of unknown country
    pop = {}
    for each in country_list:
        try:
            pop[each] = np.floor(df_population['population'][np.where(df_population['country']==each)[0][0]])
        except:
            if each=='China':
                pop[each] = 14e7
            else:
                pop[each] = 5000000 # randowm number for the unkonwn country
                
    df_population = pd.DataFrame([pop]).T.rename(columns={0:'population'})
    
    df_population.to_csv('../data/processed/world_population.csv',sep=';')
    
    return df_population, country_list


if __name__ == '__main__':
    df_confirmed = get_large_dataset()
    df_population, country_list = world_population()