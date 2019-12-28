#!/usr/bin/env python3
import json

import requests
from colour import Color
from dataclasses import dataclass, asdict
from cliglue import CliBuilder, argument, arguments, flag, parameter, subcommand, dictionary


def main():
    CliBuilder('flatmap').has(
        subcommand('scrape', run=generate_flatmap),
        subcommand('points', run=generate_points),
        subcommand('markers', run=generate_markers),
        subcommand('csv', run=generate_csv),
    ).run()


@dataclass
class FlatData:
    offer_id: int
    name: str
    longitude: float
    latitude: float
    price_m2_min: float
    price_m2_max: float


def generate_flatmap():
    flats = fetch_flats()
    for flat in flats:
        print(flat)
    priced_flats = list(filter(lambda f: f.price_m2_min > 0, flats))
    print(f'priced flats: {len(priced_flats)}')
    save_flats(priced_flats)


def normalize(value, minv, maxv):
    return (value - minv) / (maxv - minv)


def generate_points():
    with open('flats.json') as json_file:
        flats = json.load(json_file)
    min_price = min(flats, key=lambda flat: flat['price_m2_min'])['price_m2_min']
    max_price = max(flats, key=lambda flat: flat['price_m2_min'])['price_m2_min']
    for flat in flats:
        weight = flat['price_m2_min']
        print(f"          {{location: new google.maps.LatLng({flat['latitude']}, {flat['longitude']}), weight: {weight}}},")


green = Color("green")
yellow = Color("yellow")
red = Color("red")
color_scale = list(green.range_to(yellow, 50)) + list(yellow.range_to(red, 50))

def interpolate_colour(value, minv, maxv):
    factor = (value - minv) / (maxv - minv)
    return color_scale[int(factor * 99)]


def generate_markers():
    with open('flats.json') as json_file:
        flats = json.load(json_file)
    prices = list(map(lambda flat: int(flat['price_m2_min']), flats))
    min_price = min(prices)
    max_price = max(prices)
    for flat in flats:
        price = f"{flat['price_m2_min']}"
        title = f"{flat['name']}, {price} zl/m2"
        label = price
        color = interpolate_colour(int(price), min_price, max_price)
        print(f"              new google.maps.Marker({{position: new google.maps.LatLng({flat['latitude']}, {flat['longitude']}), title: '{title}', label: '{label}', icon: {{path: google.maps.SymbolPath.CIRCLE, scale: 20, fillColor: \"{color}\", fillOpacity: 0.6, strokeWeight: 0.3}} }}),")


def generate_csv():
    with open('flats.json') as json_file:
        flats = json.load(json_file)
    for flat in flats:
        price = f"{flat['price_m2_min']}"
        print(f"{flat['latitude']},{flat['longitude']},{price},\"{flat['name']}\"")


def fetch_flats():
    offers = load_offers()
    print(f'all offers: {len(offers)}')
    offers = offers[:]
    flats = []
    for offer in offers:
        coordinates = offer['geo_point']['coordinates']
        details = fetch_offer_details(offer['id'])
        stats = details['offer']['stats']
        price_m2_min = stats['ranges_price_m2_min']
        price_m2_max = stats['ranges_price_m2_max']
        flat = FlatData(offer['id'], offer['name'], coordinates[0], coordinates[1], price_m2_min, price_m2_max)
        flats.append(flat)
    return flats


def fetch_offer_details(offer_id: int):
    url = f'https://rynekpierwotny.pl/api/offers/offer/{offer_id}/?i[]=is_condohotel&i[]=is_dedicated_for_rent&i[]=is_holiday_location&i[]=main_image.vertical&i[]=main_image.tiny&s=offer_detail'
    resp = requests.get(url)
    return resp.json()


def load_offers():
    with open('offers.json') as json_file:
        return json.load(json_file)


def save_flats(flats):
    with open('flats.json', 'w') as outfile:
        serializable = list(map(lambda f: asdict(f), flats))
        json.dump(serializable, outfile)


if __name__ == '__main__':
    main()
