from locale import setlocale, LC_NUMERIC, atof
import os
import time
import pandas as pd
import requests

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from postgres import save_df
import configs
import utils 


def init_driver():
    web_driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
    )
    return web_driver


setlocale(LC_NUMERIC, '')

column_names = ['id', 'name', 'price', 'price_quantity', 'price_unit',
                'size', 'container', 'size_units', 'category', 'subcategory',
                'section', 'image_url']

driver = init_driver()
mercadona_params = configs.init_config_mercadona()

POSTAL_CODE_XPATH = '//*[@id="root"]/div[4]/div/div[2]/div/form/div/input'

IMAGE_REQUEST_URL = 'https://prod-mercadona.imgix.net/images/{identifier}.jpg?fit=crop&h=600&w=600'


def set_postal_code():
    WebDriverWait(driver, 10).until(
        ec.visibility_of_element_located((By.ID, "root"))
    )
    postal_code = driver.find_element(by=By.NAME, value='postalCode')
    postal_code.send_keys(mercadona_params['postal_code'])
    driver.find_element(
        by=By.XPATH,
        value='//*[@data-test="postal-code-checker-button"]'
    ).click()


def download_image(data, identifier):
    try:
        image_dir = f'images\\{data["category"]}\\{data["subcategory"]}\\' \
                    f'{data["section"]}'
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        image_path = image_dir + f'\\{identifier}.jpg'
        if not os.path.exists(image_path):
            with open(image_path, 'wb') as handler:
                img_data = requests.get(IMAGE_REQUEST_URL.format(identifier=identifier)).content
                handler.write(img_data)

        return image_path

    except Exception:
        if not utils.check_id_already_failed(identifier):
            utils.store_failed_id(identifier)
        print(f"Error trying to fetch image with id {identifier}")

    return None


def get_image(product):
    image = product.find_element(
        by=By.TAG_NAME, value='img'
    ).get_attribute('src')
    return image


def get_name(product):
    name = product.find_element(
        by=By.CLASS_NAME,
        value='product-cell__description-name'
    ).text

    return name


def get_price(product):
    full_price = product.find_element(
        by=By.CLASS_NAME,
        value='product-price__unit-price'
    ).text.split()
    price = full_price[0]
    price_unit = full_price[1]
    price_quantity = product.find_element(
        by=By.CLASS_NAME,
        value='product-price__extra-price'
    ).text

    return price, price_unit, price_quantity


def get_size(product):
    size_divs = product.find_elements(by=By.CLASS_NAME, value='footnote1-r')
    if len(size_divs) > 1 and size_divs[1].text != '':
        full_size = size_divs[1].text.split()
        size = full_size[0]
        size_units = full_size[1]
        container = size_divs[0].text
    else:
        full_size = size_divs[0].text.split()
        size = full_size[0]
        size_units = full_size[1]
        container = None

    return size, size_units, container


def get_id(image_url):
    _id = image_url.split('/')[4].split('.')[0]
    return _id


def get_product_data(product, category, subcategory, section):
    data = {
        'category': category.replace(' ', '_'),
        'subcategory': subcategory.replace(' ', '_'),
        'section': section.replace(' ', '_'),
    }

    image = get_image(product)
    data['image_url'] = image

    _id = get_id(image)
    data['id'] = f'{_id}'

    if utils.check_id_already_saved(_id):
        return None

    name = get_name(product)
    data['name'] = name

    price, price_unit, price_quantity = get_price(product)
    data['price'] = atof(price)
    data['price_unit'] = price_unit
    data['price_quantity'] = price_quantity

    size, size_units, container = get_size(product)
    data['size'] = atof(size)
    data['size_units'] = size_units
    data['container'] = container

    image = download_image(data, _id)
    data['image_url'] = image

    return data


def process_products(category, subcategory):
    sections = driver.find_elements(
        by=By.XPATH,
        value='//section'
    )
    for index, section in enumerate(sections):
        data_products = pd.DataFrame(
            columns=column_names)
        try:
            section_name = section.find_element(
                by=By.CLASS_NAME,
                value='section__header',
            ).text
        except NoSuchElementException:
            print(f'Could not find section {section}')
            continue

        products = (
            section.find_elements(
                by=By.XPATH,
                value=f'//section[{index + 1}]/div/div',
            )
        )
        for product in products:
            data_product = get_product_data(
                product=product,
                category=category,
                subcategory=subcategory,
                section=section_name
            )
            if data_product is None:
                continue

            data_products = pd.concat([data_products, pd.DataFrame([data_product])])

        if not data_products.empty:
            data_products.replace("€", "EUR", inplace=True)
            save_df(data_products)


def navigate():
    menu = driver.find_element(by=By.CLASS_NAME, value='category-menu')

    categories = menu.find_elements(
        by=By.XPATH,
        value='//*[@id="root"]/div[3]/div[1]/ul/li'
    )
    for category in categories:
        time.sleep(1)
        category.click()
        category_name = category.find_element(
            by=By.CLASS_NAME,
            value='subhead1-r',
        ).text

        subcategories = category.find_elements(by=By.TAG_NAME, value='li')
        for subcategory in subcategories:
            time.sleep(1)
            subcategory.click()
            subcategory_name = subcategory.find_element(
                by=By.CLASS_NAME,
                value='category-item__link',
            ).text
            process_products(
                category=category_name,
                subcategory=subcategory_name,
            )


def main():
    try:
        driver.get("https://tienda.mercadona.es/categories")
        set_postal_code()
        navigate()

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
