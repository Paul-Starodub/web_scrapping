import csv
import logging
import sys
from dataclasses import dataclass, fields, astuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://webscraper.io/"
LAPTOP_URL = urljoin(BASE_URL, "test-sites/e-commerce/static/computers/laptops")

PRODUCTS_OUTPUT_CSV_PATH = "products.csv"


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)8s]:  %(message)s",
    handlers=[
        logging.FileHandler("parser.log"),
        logging.StreamHandler(sys.stdout),
    ],
)


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCTS_FIELDS = [field.name for field in fields(Product)]


def parse_single_product(product_soup: BeautifulSoup) -> Product:
    return Product(
        title=product_soup.select_one(".title")["title"],
        description=product_soup.select_one(".description").text,
        price=float(product_soup.select_one(".price").text.replace("$", "")),
        rating=int(product_soup.select_one("p[data-rating]")["data-rating"]),
        num_of_reviews=int(
            product_soup.select_one(".ratings > p.pull-right").text.split()[0]
        ),
    )


def get_num_pages(page_soup: BeautifulSoup) -> int:
    pagination = page_soup.select_one(".pagination")

    if pagination is None:
        return 1

    return int(pagination.select("li")[-2].text)


def get_single_page_products(page_soup: BeautifulSoup) -> [Product]:
    products = page_soup.select(".thumbnail")
    return [parse_single_product(product_soup) for product_soup in products]


def get_laptop_products() -> [Product]:
    logging.info("Start parsing laptops")
    page = requests.get(LAPTOP_URL).content
    first_page_soup = BeautifulSoup(page, "html.parser")

    # get num of pages
    num_pages = get_num_pages(first_page_soup)

    all_products = get_single_page_products(first_page_soup)

    # iterate on pages & get all products on single page
    for page_num in range(2, num_pages + 1):
        logging.info(f"Start parsing page #{page_num}")
        page = requests.get(LAPTOP_URL, {"page": page_num}).content
        soup = BeautifulSoup(page, "html.parser")
        all_products.extend(get_single_page_products(soup))

    return all_products


def write_products_to_csv(products: [Product]) -> None:
    with open(PRODUCTS_OUTPUT_CSV_PATH, "w") as file:
        writer = csv.writer(file)
        writer.writerow(PRODUCTS_FIELDS)
        writer.writerows([astuple(product) for product in products])


def main():
    products = get_laptop_products()
    write_products_to_csv(products)


if __name__ == "__main__":
    main()
