from discover import fetch
import concurrent.futures
import json

QUERIES = {
    'erk_reporter': '(TITLE_ABS:"ERK" AND TITLE_ABS:"drug" AND (TITLE_ABS:"single-cell" OR TITLE_ABS:"live-cell")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'drug_live_screen': '((TITLE_ABS:"drug" AND TITLE_ABS:"time-lapse") OR TITLE:"live-cell screening" OR TITLE:"dynamic drug") AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'microfluidic_drug': '(TITLE_ABS:"microfluidic" AND TITLE_ABS:"drug" AND (TITLE_ABS:"pulses" OR TITLE_ABS:"washout" OR TITLE_ABS:"dynamic")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, QUERIES.items()):
            print(json.dumps(result))
