from primary import fulltext
import concurrent.futures
import json

PAPERS = {'cipa_multisite_primary': 'PMC6226030', 'cardiac_multiscale': 'PMC11390749'}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(fulltext, PAPERS.items()):
            print(json.dumps(result))
