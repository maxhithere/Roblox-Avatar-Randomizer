from typing import List, Dict, Any, Union
import requests
import time
import random
import logging
from itertools import cycle
import threading

def read_lines_from_file(filename: str) -> List[str]:
    with open(filename, "r") as f:
        return f.read().splitlines()

def get_csrf(session: requests.Session, cookie: str) -> str:
    response = session.post("https://auth.roblox.com/v2/logout", cookies={".ROBLOSECURITY": cookie})
    return response.headers["X-Csrf-Token"]

def set_avatar_type(session: requests.Session, cookie: str, csrf: str, avatar_type: str) -> None:
    response = session.post(
        "https://avatar.roblox.com/v1/avatar/set-player-avatar-type",
        cookies={".ROBLOSECURITY": cookie},
        headers={"X-Csrf-Token": csrf},
        json={"playerAvatarType": avatar_type}
    )
    if response.status_code == 200:
        logging.info(f"Successfully set avatar type: {avatar_type}")

def set_scales(session: requests.Session, cookie: str, csrf: str, height: float, width: float) -> None:
    response = session.post(
        "https://avatar.roblox.com/v1/avatar/set-scales",
        cookies={".ROBLOSECURITY": cookie},
        headers={"X-Csrf-Token": csrf},
        json={"height": height, "width": width, "proportion": 0, "head": 1, "bodyType": 0}
    )
    if response.status_code == 200:
        logging.info(f"Successfully set avatar scales: {height} | {width}")

def set_body_color(session: requests.Session, cookie: str, csrf: str, color: int) -> None:
    response = session.post(
        "https://avatar.roblox.com/v1/avatar/set-body-colors",
        cookies={".ROBLOSECURITY": cookie},
        headers={"X-Csrf-Token": csrf},
        json={"headColorId": color, "torsoColorId": color, "rightArmColorId": color,
              "leftArmColorId": color, "rightLegColorId": color, "leftLegColorId": color}
    )
    if response.status_code == 200:
        logging.info(f"Successfully set avatar body color: {color}")

def claim_free_items(session: requests.Session, cookie: str, csrf: str) -> None:
    asset_types: List[Dict[str, int]] = [{"c": 4, "s": 20}, {"c": 3, "s": 56}, {"c": 3, "s": 57}] # hair, shirts, pants
    assets: List[Dict[str, Union[int, str, bool]]] = []
    free_items: List[int] = []

    for asset_type in asset_types:
        url = f"https://catalog.roblox.com/v1/search/items/details?Category={asset_type['c']}&Subcategory={asset_type['s']}&MaxPrice=0"
        response = session.get(url).json()
        time.sleep(0.5)

        if "data" in response and len(response["data"]) > 0:
            item = random.choice(response["data"])
            asset_info = {"id": item['id'], "name": item['name'], "assetType": get_asset_type_info(item['assetType']),
                          "isCollectible": False, "isDynamicHead": False, "isLimited": False,
                          "isLimitedUnique": False, "isThirteenPlus": False, "itemRestrictions": [],
                          "itemType": "Asset", "link": f"https://www.roblox.com/catalog/{item['id']}/{item['name'].replace(' ', '-')}",
                          "selected": True, "thumbnailType": "Asset", "type": "Asset"}
            assets.append(asset_info)
            free_items.append(item["productId"])

    for item in free_items:
        logging.info(f'Claiming {str(item)}..')
        session.post(
            f"https://economy.roblox.com/v1/purchases/products/{item}",
            data={"expectedCurrency": 1, "expectedPrice": 0, "expectedSellerId": 1},
            cookies={".ROBLOSECURITY": cookie},
            headers={"X-Csrf-Token": csrf}
        )
        time.sleep(0.3)

    get_av_and_set_new(session, cookie, csrf, assets)

def get_asset_type_info(asset_type_id: int) -> Dict[str, Union[str, int]]:
    asset_type_info = {}
    if asset_type_id == 41:
        asset_type_info = {"name": "Hair Accessory", "id": 41}
    elif asset_type_id == 11:
        asset_type_info = {"name": "Hat", "id": 11}
    elif asset_type_id == 12:
        asset_type_info = {"name": "Pants", "id": 12}
    return asset_type_info

def get_av_and_set_new(session: requests.Session, cookie: str, csrf: str, assets: List[Dict[str, Any]]) -> None:
    asset_ids = [asset["id"] for asset in assets]
    data = {"assets": assets}

    set_wear = session.post(
        "https://avatar.roblox.com/v2/avatar/set-wearing-assets",
        cookies={".ROBLOSECURITY": cookie},
        headers={
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json;charset=UTF-8',
            'x-csrf-token': csrf,
        },
        json=data
    )
    if set_wear.status_code == 200:
        logging.info(f"Successfully set avatar wearing assets: {asset_ids}")
    else:
        logging.error(f"Failed to set avatar wearing assets: {set_wear.text}")

def main(cookie: str, proxy: str) -> None:
    session = requests.Session()
    session.proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    csrf = get_csrf(session, cookie)
    set_avatar_type(session, cookie, csrf, random.choice(avatar_types))
    set_scales(session, cookie, csrf, random.choice(heights), random.choice(weights))
    set_body_color(session, cookie, csrf, random.choice(body_colors))
    claim_free_items(session, cookie, csrf)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting..")
    cookie_pool = read_lines_from_file("input/cookies.txt")
    proxy_pool = read_lines_from_file("input/proxies.txt")
    avatar_types = ["R6", "R15"]
    body_colors = [125, 18, 192, 217, 5, 1001]
    heights = [0.9, 1, 1.05]
    weights = [0.7, 0.8, 0.9, 1]

    for i in range(len(cookie_pool)):
        cookie = next(cycle(cookie_pool))
        proxy = next(cycle(proxy_pool))
        threading.Thread(target=main, args=(cookie, proxy)).start()
