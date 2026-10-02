Extract the invoice below into a single JSON object with exactly these keys:

- `invoice_number` (string)
- `supplier_name` (string)
- `customer_name` (string): the "Bill to" party
- `issue_date`, `due_date` (string): ISO format `YYYY-MM-DD`
- `currency` (string): ISO 4217 code, e.g. `GBP`
- `line_items` (array): each `{ "sku", "description", "quantity", "unit_price", "line_total" }`;
  numbers as JSON numbers without currency symbols
- `subtotal`, `vat`, `total` (number)

Return JSON only.

Invoice:
"""
{input}
"""
