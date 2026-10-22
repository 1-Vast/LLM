from primary import fulltext
import concurrent.futures
import json

PAPERS = {'cardiac_multidonor_ai': 'PMC13547733', 'cardiac_population': 'PMC6231908', 'cardiac_organelle': 'PMC12408628'}
if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fulltext, PAPERS.items()):
            print(json.dumps(result))
