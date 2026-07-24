# Schema Guidelines
- TotalAmount in orders table is already calculated. Use `o.TotalAmount` directly for any total sales or revenue query. Do NOT use SUM(Quantity * UnitPrice).
- UnitPrice column belongs ONLY to the `products` table. NEVER use `o.UnitPrice`.
- Quantity column belongs ONLY to the `orders` table (`o.Quantity`).