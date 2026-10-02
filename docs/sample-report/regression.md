**Regression check: passed** (24/24 checks passed)

| | Suite | Model | Metric | Baseline | Current | Limit |
|---|---|---|---|---|---|---|
| ✅ | order_extraction | precise-large | field_accuracy (floor) | - | 0.9583 | >= 0.500 |
| ✅ | order_extraction | precise-large | field_accuracy | 0.9583 | 0.9583 | drop <= 0.020 |
| ✅ | order_extraction | precise-large | json_valid_rate | 1 | 1 | drop <= 0.050 |
| ✅ | order_extraction | precise-large | cost_per_doc_usd | 0.002216 | 0.002216 | increase <= 25% |
| ✅ | order_extraction | balanced-medium | field_accuracy (floor) | - | 0.8125 | >= 0.500 |
| ✅ | order_extraction | balanced-medium | field_accuracy | 0.8125 | 0.8125 | drop <= 0.020 |
| ✅ | order_extraction | balanced-medium | json_valid_rate | 0.9167 | 0.9167 | drop <= 0.050 |
| ✅ | order_extraction | balanced-medium | cost_per_doc_usd | 0.0002687 | 0.0002687 | increase <= 25% |
| ✅ | order_extraction | fast-small | field_accuracy (floor) | - | 0.6181 | >= 0.500 |
| ✅ | order_extraction | fast-small | field_accuracy | 0.6181 | 0.6181 | drop <= 0.020 |
| ✅ | order_extraction | fast-small | json_valid_rate | 0.9167 | 0.9167 | drop <= 0.050 |
| ✅ | order_extraction | fast-small | cost_per_doc_usd | 6.218e-05 | 6.218e-05 | increase <= 25% |
| ✅ | invoice_extraction | precise-large | field_accuracy (floor) | - | 0.9848 | >= 0.500 |
| ✅ | invoice_extraction | precise-large | field_accuracy | 0.9848 | 0.9848 | drop <= 0.020 |
| ✅ | invoice_extraction | precise-large | json_valid_rate | 1 | 1 | drop <= 0.050 |
| ✅ | invoice_extraction | precise-large | cost_per_doc_usd | 0.003393 | 0.003393 | increase <= 25% |
| ✅ | invoice_extraction | balanced-medium | field_accuracy (floor) | - | 0.9087 | >= 0.500 |
| ✅ | invoice_extraction | balanced-medium | field_accuracy | 0.9087 | 0.9087 | drop <= 0.020 |
| ✅ | invoice_extraction | balanced-medium | json_valid_rate | 1 | 1 | drop <= 0.050 |
| ✅ | invoice_extraction | balanced-medium | cost_per_doc_usd | 0.0004031 | 0.0004031 | increase <= 25% |
| ✅ | invoice_extraction | fast-small | field_accuracy (floor) | - | 0.6388 | >= 0.500 |
| ✅ | invoice_extraction | fast-small | field_accuracy | 0.6388 | 0.6388 | drop <= 0.020 |
| ✅ | invoice_extraction | fast-small | json_valid_rate | 0.9167 | 0.9167 | drop <= 0.050 |
| ✅ | invoice_extraction | fast-small | cost_per_doc_usd | 8.744e-05 | 8.744e-05 | increase <= 25% |
