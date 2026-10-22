from discover import fetch
import concurrent.futures
import json

QUERIES = {
    'cardiac_dataset': '(TITLE_ABS:"cardiomyocytes" AND (TITLE_ABS:"dataset" OR TITLE_ABS:"data" OR TITLE_ABS:"ToxCast") AND TITLE_ABS:"drugs") AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'cardiac_chemicals': '(TITLE_ABS:"cardiomyocytes" AND TITLE_ABS:"chemicals" AND (TITLE_ABS:"screening" OR TITLE_ABS:"functional")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'cardiac_cipa': '(TITLE_ABS:"CiPA" AND (TITLE_ABS:"dataset" OR TITLE_ABS:"raw" OR TITLE_ABS:"data")) AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, QUERIES.items()):
            print(json.dumps(result))
