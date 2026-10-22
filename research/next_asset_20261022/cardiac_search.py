from discover import fetch
import concurrent.futures
import json

QUERIES = {
    'cardiac_screen': '(TITLE_ABS:"cardiomyocyte" AND (TITLE_ABS:"screening" OR TITLE_ABS:"high-throughput") AND (TITLE_ABS:"calcium" OR TITLE_ABS:"contractility") AND TITLE_ABS:"compounds") AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'kinase_live_screen': '(TITLE_ABS:"kinase" AND TITLE_ABS:"screen" AND TITLE_ABS:"live-cell" AND TITLE_ABS:"dynamics") AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
    'phenotypic_live': '(TITLE_ABS:"drug" AND TITLE_ABS:"single-cell" AND TITLE_ABS:"trajectories" AND TITLE_ABS:"screen") AND OPEN_ACCESS:Y NOT PUB_TYPE:Review',
}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, QUERIES.items()):
            print(json.dumps(result))
