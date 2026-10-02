Extract the order from the email below and return a single JSON object with exactly these keys:

- `customer_name` (string): the ordering business
- `contact_name` (string): the person who sent the email
- `po_number` (string or null): purchase order reference, null if none is given
- `delivery_method` (string): one of `standard`, `next_day`, `collection`
- `required_by` (string): date in ISO format `YYYY-MM-DD`
- `delivery_address` (object): `line1`, `city`, `postcode`
- `items` (array): each `{ "sku": string, "quantity": integer }`, in the order they appear

Return JSON only.

Email:
"""
{input}
"""
