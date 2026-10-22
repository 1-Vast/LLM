# Source-derived manifest route

The retained v1 landing references /datasets/bundle.js?8533f74fd5ffa7f3d44f. The fetched client has SHA256 6dc1ed58657b306832db9f82de114a9f40f7db88f5ce494c10b3a558ad725658. It was inspected as text, never executed. CLIENT_ROUTE_PROJECTION.json retains route contexts.

At byte/character vicinity203438 config sets publicApiBaseUrl=/public-api. Around559173, fetchFiles constructs https://${hostname}${publicApiBaseUrl}/datasets/${datasetId}/files?folder_id=${folderId}&version=${version}&$start=${start}&$limit=1000, with Accept application/vnd.mendeley-public-dataset.1+json, start0. Around563100, setFolderPath calls fetchFiles with folderId=root and the active snapshot id/version. The known snapshot supplies datasetId3pnv5wh5jm/version1. Therefore the exact source-derived request is https://data.mendeley.com/public-api/datasets/3pnv5wh5jm/files?folder_id=root&version=1&$start=0&$limit=1000. The helper sends its existing User-Agent; the default Accept is not the vendor-specific header. Any resulting failure is retained rather than probing alternate paths.

The landing's API documentation link returned301 Location /api/docs/; one explicit same-host HTTPS redirect request returned200. This is a recorded redirect, not an unlogged retry. No raw numerical source has been opened.
