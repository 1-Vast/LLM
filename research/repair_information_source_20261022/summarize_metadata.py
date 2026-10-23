"""Record exact static paths and local source provenance; no data payload read."""
from pathlib import Path
import hashlib
import json
import re

root = Path('D:/MAESTRO')
out = root / 'log/20261022/repair_information_opportunity/source'
local = [root / 'research/dual_core_innovation_validation_20261021/SOURCE_MANIFEST.json',
         root / 'data/external/ptv1_proteintalks_20261021/repo/README.md',
         root / 'data/external/ptv1_proteintalks_20261021/repo/root_README.md']
client = (out / 'request_2_client.body').read_text(encoding='utf-8')
paths = sorted(set(re.findall(r'assets/(?:Download|PTV1|agreement|Agreement)-[^"\s,]+', client[:6000])))
result = dict(local_sources=[dict(path=str(path.relative_to(root)),
                                  sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in local],
              observed_static_application_paths=paths,
              explicit_metadata_or_schema_endpoint_identified=False,
              independent_new_background_or_condition_identified=False,
              request_2_incomplete=True,
              requests_used=2,
              requests_remaining=1,
              disposition='STOP_METADATA_SCOPE_WITH_INDEPENDENCE_UNKNOWN')
(out / 'PATH_RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
