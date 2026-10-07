# Eval report: simulator

Run `20261002T180213Z-simulator` · started 2026-10-02 18:02:13 UTC · 3 models · 2 suites

## Overall

| Model | Field accuracy | Exact match | Valid JSON | Latency p50 | Total cost |
|---|---|---|---|---|---|
| precise-large | 97.5% | 58.3% | 100.0% | 2.31s | $0.0673 |
| balanced-medium | 87.5% | 20.8% | 95.8% | 1.12s | $0.00806 |
| fast-small | 63.1% | 0.0% | 91.7% | 0.38s | $0.00180 |

## Suite: order_extraction

**Most accurate:** precise-large · **Cheapest:** fast-small · **Fastest (p50):** fast-small · **Best value (within 5 pts):** precise-large

| Model | Field acc. | Exact match | Valid JSON | p50 | p95 | Cost/doc | Errors |
|---|---|---|---|---|---|---|---|
| precise-large | 95.8% | 50.0% | 100.0% | 2.25s | 2.89s | $0.00222 | 0 |
| balanced-medium | 81.2% | 16.7% | 91.7% | 1.08s | 1.32s | $0.00027 | 0 |
| fast-small | 61.8% | 0.0% | 91.7% | 0.39s | 0.47s | $0.00006 | 0 |

### Weakest fields

- **precise-large**: `delivery_method` 75.0%, `contact_name` 91.7%, `delivery_address.postcode` 91.7%, `items[].quantity` 95.8%
- **balanced-medium**: `delivery_address.city` 58.3%, `customer_name` 75.0%, `delivery_method` 75.0%, `contact_name` 83.3%, `required_by` 83.3%
- **fast-small**: `customer_name` 50.0%, `po_number` 50.0%, `items[].quantity` 54.2%, `delivery_method` 58.3%, `required_by` 58.3%

### Lowest-scoring cases

| Model | Case | Accuracy | Valid JSON | Error |
|---|---|---|---|---|
| fast-small | `order-002` | 0.0% | no |  |
| balanced-medium | `order-001` | 0.0% | no |  |
| fast-small | `order-008` | 40.0% | yes |  |
| fast-small | `order-012` | 50.0% | yes |  |
| fast-small | `order-009` | 50.0% | yes |  |
| fast-small | `order-005` | 50.0% | yes |  |
| fast-small | `order-010` | 68.8% | yes |  |
| fast-small | `order-006` | 70.0% | yes |  |
| fast-small | `order-004` | 71.4% | yes |  |
| fast-small | `order-003` | 75.0% | yes |  |

## Suite: invoice_extraction

**Most accurate:** precise-large · **Cheapest:** fast-small · **Fastest (p50):** fast-small · **Best value (within 5 pts):** precise-large

| Model | Field acc. | Exact match | Valid JSON | p50 | p95 | Cost/doc | Errors |
|---|---|---|---|---|---|---|---|
| precise-large | 98.5% | 66.7% | 100.0% | 2.41s | 2.85s | $0.00339 | 0 |
| balanced-medium | 90.9% | 25.0% | 100.0% | 1.15s | 1.36s | $0.00040 | 0 |
| fast-small | 63.9% | 0.0% | 91.7% | 0.38s | 0.47s | $0.00009 | 0 |

### Weakest fields

- **precise-large**: `invoice_number` 91.7%, `customer_name` 91.7%, `line_items[].unit_price` 93.5%
- **balanced-medium**: `total` 83.3%, `line_items[].line_total` 83.9%, `line_items[].sku` 87.1%, `line_items[].quantity` 87.1%, `line_items[].unit_price` 87.1%
- **fast-small**: `vat` 41.7%, `currency` 50.0%, `line_items[].unit_price` 54.8%, `invoice_number` 58.3%, `due_date` 58.3%

### Lowest-scoring cases

| Model | Case | Accuracy | Valid JSON | Error |
|---|---|---|---|---|
| fast-small | `invoice-007` | 0.0% | no |  |
| fast-small | `invoice-012` | 57.9% | yes |  |
| fast-small | `invoice-003` | 58.3% | yes |  |
| fast-small | `invoice-002` | 70.6% | yes |  |
| fast-small | `invoice-008` | 71.4% | yes |  |
| fast-small | `invoice-006` | 71.4% | yes |  |
| balanced-medium | `invoice-012` | 73.7% | yes |  |
| fast-small | `invoice-011` | 76.5% | yes |  |
| fast-small | `invoice-009` | 78.6% | yes |  |
| fast-small | `invoice-004` | 78.6% | yes |  |
