from primary import fulltext
import concurrent.futures
import json

PAPERS = {'cell_state_wiring': 'PMC13014938', 'microfluidic_hfim': 'PMC13351019', 'alk_tolerance': 'PMC11531495'}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fulltext, PAPERS.items()):
            print(json.dumps(result))
