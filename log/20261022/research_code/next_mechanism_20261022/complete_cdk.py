"""Use EuropePMC for the authenticated primary after NCBI rate limiting."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from read_selected import get, OUT


def main():
    with (OUT / 'CDK_ALTERNATIVE_PROTOCOL.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'before_request': True,
            'pmcid': 'PMC13584416', 'route': 'EuropePMC fullTextXML; NCBI BioC429 retained, no repeat NCBI request',
            'scope': 'public article text only; no count/data arrays',
            'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'fetch_implementation_sha256': hashlib.sha256(Path(__file__).with_name('read_selected.py').read_bytes()).hexdigest()}, handle, indent=2)
    result = get(('cdk_epmc', 'PMC13584416'))
    with (OUT / 'CDK_ALTERNATIVE_RECEIPT.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
