
import requests


BASE_URL = "https://api.energy-charts.info"


def fetch_dataset(endpoint, params):
    # send api request
    url = BASE_URL + endpoint

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    # check http status
    response.raise_for_status()

    # parse json response
    payload = response.json()

    # validate basic structure
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("data"), list)
        or not isinstance(payload.get("series"), list)
    ):
        raise ValueError("Unexpected API response structure")

    return payload, response.url
