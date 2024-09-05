import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
url_main = 'https://www.lego.com'


def get_themes(soup):
    themes_list= []
    section= soup.find('section')
    if section:
        ul = section.find('ul')
        if ul:
            themes = ul.find_all('li')
            for theme in themes:
                themes_dict ={
                    'name':theme.h2.span.text if theme.h2 else 'Unknown',
                    'url':f"{url_main}{theme.a.get('href')}" if theme.a else '#'
                }
                themes_list.append(themes_dict)
        else:
            print('Ul not found')
    else:
        print('Section not found')

    if themes_list:
        df = pd.DataFrame(themes_list)
        df.to_excel('themes.xlsx', index=False)
    else:
        print("No themes found.")

    return themes_list 

def get_soup(url, page=1):
    if page == 1:
        r = requests.get(url=url)
    else:
        url = f'{url}?page={page}&offset=0'   
        r = requests.get(url) 
    return BeautifulSoup(r.text, 'lxml')

def get_toys_info(toy_data):
    t_data = {
        'age':None,
        'pieces':None,
        'rating':None 
    }
    for item in toy_data:
        if '+' in item:
            t_data['age']=item 
        elif '.' in item:
            t_data['rating']=item
        else:
            t_data['pieces']=item

    return t_data

def get_toys_pages(soup):
    n_toys = int(soup.select('span[data-value]')[0].get('data-value'))
    n_pages = n_toys//18+1
    return n_toys, n_pages


def get_price(toy):
    try:
        price_div = toy.find('div', {'data-test': 'product-leaf-price-row'}).text
        price = toy.find('span', {'data-test': 'product-leaf-price'}).text

        if '%' in price_div:
            discount = toy.find('span', {'data-test': 'product-leaf-discounted-price'}).text
            return price, discount
        else:
            return price, 0
    except AttributeError:
        return "N/A", "N/A"


def get_toys_values(soup, collection='Marvel'):
    toys = soup.find_all('li', {'data-test': 'product-item'})
    toys_data = []
    for toy in toys:  
        toy_name_el = toy.find('h3')
        if toy_name_el:
            toy_name = toy_name_el.text.strip()
        else:
            toy_name= 'Name not found'
            continue
        toy_price, toy_discount  = get_price(toy)
        attributes_row = toy.find('div', {'data-test': 'product-leaf-attributes-row'})
        if attributes_row:
            toy_data = [x.text.strip() for x in attributes_row.find_all('span')]
            toy_data = get_toys_info(toy_data)
        else:
            print('No attributes found for this product')
        toy_info= {
            'name':toy_name, 
            'collection':collection,
            'age':toy_data['age'],
            'pieces':toy_data['pieces'],
            'rating':toy_data['rating'],
            'price':toy_price,
            'discount':toy_discount,
        }
        toys_data.append(toy_info)

    return toys_data

def main():
    logging.info("Starting the scraping process")
    themes_url = 'https://www.lego.com/uk-ua/themes'
    soup = get_soup(themes_url)
    themes = get_themes(soup)

    all_toys_data = []

    for theme in themes:
        logging.info(f"Scraping collection: {theme['name']}")
        theme_url = theme['url']
        soup = get_soup(theme_url)
        
        if not soup:
            logging.warning(f"Skipping collection {theme['name']} due to failed request")
            continue
        
        n_toys, n_pages = get_toys_pages(soup)
        logging.info(f"Total toys: {n_toys}, Pages: {n_pages}")
    
        for page in range(1, n_pages + 1):
            logging.info(f"Scraping page {page} of {n_pages} for collection {theme['name']}")
            soup = get_soup(theme_url, page)
            if not soup:
                logging.warning(f"Skipping page {page} of collection {theme['name']} due to failed request")
                continue
            toys_data = get_toys_values(soup, theme['name'])
            all_toys_data.extend(toys_data)
    
    # Saving all the data at once
    if all_toys_data:
        df = pd.DataFrame(all_toys_data)
        df.to_excel('final_result.xlsx', index=False)
        logging.info("Data saved successfully to final_result.xlsx")
    else:
        logging.warning("No toy data found to write.")

if __name__=='__main__':
    main()

