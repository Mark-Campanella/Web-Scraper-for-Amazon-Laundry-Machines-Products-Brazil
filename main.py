import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
import pandas as pd
# -------------------------------------------------------------------------------------------------------------------#
# -----------------------------------------Customization Variables---------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#

#Where
url = "https://www.amazon.com.br"

#What
keywords = "Lavadora e Secadoraa de Roupas"

# -------------------------------------------------------------------------------------------------------------------#
#JUST TO CHANGE IF THERE IS A CHANGE IN THE AMAZON WEBSITE  
# -------------------------------------------------------------------------------------------------------------------#
# Navigation classes
class_search_bar = 'nav-input.nav-progressive-attribute'
class_submit_btn = 'nav-search-submit-button'
class_next_btn = 's-pagination-item.s-pagination-next.s-pagination-button.s-pagination-separator'

# For each item
class_itens = 's-result-item.s-asin'

# URLs of each item
class_link = 'a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal'

# Item classes DEPRECATED OR TO BE USED LATER   
att_img = 'data-image-source-density'
class_image_li = 'a-spacing-small item imageThumbnail a-declarative'
class_local_currency = "a-price-symbol"

# What to get from each object
class_name = 'a-size-large.product-title-word-break'
class_price = "a-price-whole"
class_marketing_claims_div = "productDescription"
xpath_prod_description = '//*[@id="productDescription"]/p/span/text()'
xpath_img_1 = ''
class_th = "a-color-secondary.a-size-base.prodDetSectionEntry"
class_td = 'a-size-base.prodDetAttrValue'
class_5_Star = 'reviewCountTextLinkedHistogram.noUnderline'
# -------------------------------------------------------------------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------#
#If you change the place/language, please take a look at this! And change what is required!
txt_th_5star = "Avaliações de clientes"
txt_th_ignore = "Ranking dos mais vendidos"
# -------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------#
# Global Variables
next_page = None
product_link = []
products_data = []
# -------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------#
# Driver Configuration - prioratazing safety and discretion (trying at least)
# -------------------------------------------------------------------------------------------------------------------#
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-geolocation")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-extensions")
languages = ["pt-BR", "pt"] #In case of going for the USA/UK or anywhere, CHANGE THIS
driver = webdriver.Chrome(options=chrome_options)
# -------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------#
# configure Selenium Stealth
# -------------------------------------------------------------------------------------------------------------------#
stealth(driver,
        languages=languages,
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True)
# -------------------------------------------------------------------------------------------------------------------#

# -------------------------------------------------------------------------------------------------------------------#
#----------------------------------------------------FUNCTIONS-------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#

def scrape_page(driver:webdriver):
    '''
    This function gets the link of each object of each page in the 'keywords' pages.
    It will change variables such as 'product_link' and 'next_page',
    putting all the links inside product_link and going to the next page if there is one 
    
    Parameters:
        -driver: webdriver
    '''
    global product_link
    global next_page

    # wait until elements are found
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, class_itens)))

    # get elements links
    elements = driver.find_elements(By.CLASS_NAME, class_itens)
    for element in elements:
        item = element.find_element(By.CLASS_NAME, class_link)
        product_link.append(item.get_attribute('href'))

    # Uncomment after testing:
    # try:
    #     next_page = driver.find_element(By.CLASS_NAME, class_next_btn).get_attribute("href")
    # except:
    #     next_page = None

def process_product(driver:webdriver, link:str):
    '''
    For each object whose link was copied in the product_link:
    →it will fetch some informations
    →process a dictionary if this informations
    →append in the list of the dictionaries that contains all machines
    
    For all of them, we are trying to get, if not found, leave it blank, because there are lots of differences between each object
    
    Parameters:
        -driver: webdriver
        -link: str
    '''
    global products_data
    driver.get(link) #Go to the object's page
    driver.implicitly_wait(20) #Wait the page to load

    product_info = {'product_link': link} #append it's link in the dictionary

    try:
        name = driver.find_element(By.CLASS_NAME, class_name).text 
        product_info['product_name'] = name #append it's name in the dictionary      
    except: product_info['product_name'] = ""

    try:
        price = driver.find_element(By.CLASS_NAME, class_price).text
        product_info['product_price'] = price #append it's price in the dictionary (integer only)    
    except: product_info['product_price'] = ""
        
    #For this one, there is a table, so I am gathering all elements, the Table Headers (th) and the Table Data (td)
    #I'm storing them in two lists
    #There are two exceptions in the tables, the 5-Star Review Avg., that we want and the Website's Selling Rank, which is not interesting
    try:
        th_elements = driver.find_elements(By.CLASS_NAME, class_th)
        td_elements = driver.find_elements(By.CLASS_NAME, class_td)
        th_texts = [elem.text for elem in th_elements]
        td_texts = [elem.text for elem in td_elements]
        
        #The review avg.
        try: five_stars = driver.find_element(By.CLASS_NAME, class_5_Star).get_attribute('title') 
        except: five_stars = None
            
        for th_text, td_text in zip(th_texts, td_texts): #Now we want to envelop that in a structure like: "th_text":"td_text", treating the exceptions
            if th_text == txt_th_5star: product_info[th_text] = five_stars
            elif th_text == txt_th_ignore: product_info[th_text] = ""
            else: product_info[th_text] = td_text
                
    except Exception as e: print("Error: ", e)
        
   #this one is not working properly, should get the description     
    try: description = driver.find_elements(By.CLASS_NAME,xpath_prod_description).text
        
    except: description = None
        
    finally: product_info["Description"] = description
    
    products_data.append(product_info)#Add item in the list of items

def process_products(driver:webdriver):
    '''
        Iterates for each link, in the end let go of the list of links
    '''
    global product_link
    for link in product_link: process_product(driver, link)

    product_link.clear()
    
# -------------------------------------------------------------------------------------------------------------------#
# ------------------------------------------------------Start!-------------------------------------------------------#
# -------------------------------------------------------------------------------------------------------------------#

try:
    driver.get(url) #Go to the website
    driver.implicitly_wait(20)#Wait for it to load
    
    search = driver.find_element(By.CLASS_NAME, class_search_bar)#go to the search bar
    search.send_keys(keywords)#type the keywords
    time.sleep(1)#take a breath
    search_btn = driver.find_element(By.ID, class_submit_btn)#go to the button
    search_btn.click()#click in the search button
    driver.implicitly_wait(5)#wait for the page to load
    
    while True:
        '''
        For each page, scrape the links until you find no more pages
        '''
        scrape_page(driver)
        if next_page: driver.get(next_page)
            
        else: break
            
    #Now for each link gotten, find the infos we need        
    process_products(driver)
    
except Exception as e:
    print("Failed to run the code, exited with error: ", e)
    
finally:
    #Close google
    driver.quit()

    # Convert the list of dictionaries into a csv, printing top 5 items for checking
    df = pd.DataFrame(products_data)
    print(df.head())
    df.to_csv('product_data.csv', index=False)
