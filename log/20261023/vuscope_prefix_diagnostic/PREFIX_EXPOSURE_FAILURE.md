# Prefix exposure before freeze

The initial inspect_schema.py attempted to detect numeric trajectory rows using the first field. The actual first field is a date/time string and elapsed time is the second. It therefore saved the first12lines per file (vessel/header plus10rows at0..27h) in SCHEMA.json. Root tool output displayed those early values (partly truncated), contrary to the intended headers-only inspection. Preserve that original record; no assertion that all values remain unseen.

No >27h row was saved/displayed by this operation. The planned72h cutoff and >72..120h forecast outcomes therefore remain unopened. This asset is exploratory, not a fresh external confirmation, and prefix inspection before specification must be disclosed. No outcome-driven parameter or endpoint choice is justified by this failure. Corrected schema inspection stops immediately on the Elapsed header, writes SCHEMA_METADATA_ONLY.json, and never reads the next trajectory row. Read-only source text projection remains in that metadata record.

Source inspection also revealed that the released author preprocessing keeps four globally indexed concentration levels, and that the fit file contains time-shift/cutoff conventions needing independent review. Do not blindly execute the author pipeline or claim bit-for-bit published replication.
