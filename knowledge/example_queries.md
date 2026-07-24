# Few-Shot SQL Examples

Question: هاتلي أحدث 5 طلبات تم شحنها، واعرضلي اسم العميل، واسم المنتج ، وإجمالي المبلغ، وتاريخ الطلب
SQL:
SELECT c.CustomerName, p.ProductName, o.TotalAmount, o.OrderDate
FROM orders o
JOIN customers c ON o.CustomerID = c.CustomerID
JOIN products p ON o.ProductID = p.ProductID
WHERE o.OrderStatus = 'Shipped'
ORDER BY o.OrderDate DESC
LIMIT 5;

Question: إيه أكتر فئة مبيعاً من حيث الكمية؟
SQL:
SELECT p.Category, SUM(o.Quantity) AS TotalQuantity
FROM orders o
JOIN products p ON o.ProductID = p.ProductID
GROUP BY p.Category
ORDER BY TotalQuantity DESC
LIMIT 1;