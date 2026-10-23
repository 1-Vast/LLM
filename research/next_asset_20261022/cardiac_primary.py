from primary import fulltext
import concurrent.futures
import json

PAPERS = {'cardiac_hazard': 'PMC6294263', 'calcium_perturbation': 'PMC4361473', 'cardiac_multiplex': 'PMC4652224'}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fulltext, PAPERS.items()):
            print(json.dumps(result))
