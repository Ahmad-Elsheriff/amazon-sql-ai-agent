import sqlite3
import pandas as pd

def build_database_from_csv():
    # مسار ملف الأمازون على جهازك
    csv_path = r"C:\Users\ahmad\Downloads\archive\Amazon.csv"
    print("🔄 جاري قراءة ملف الـ CSV وبناء قاعدة بيانات الشركة...")
    
    try:
        df = pd.read_csv(csv_path)
        # توحيد تنسيق التاريخ ليمشي مع SQLite (YYYY-MM-DD)
        df['OrderDate'] = pd.to_datetime(df['OrderDate'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        
        # مسح الجداول القديمة للحصول على داتا نظيفة تماماً
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS products")
        cursor.execute("DROP TABLE IF EXISTS customers")
        
        # 1. إنشاء جدول المنتجات (بأعمدة الأمازون الحقيقية)
        products_df = df[['ProductID', 'ProductName', 'Category', 'Brand', 'UnitPrice']].drop_duplicates(subset=['ProductID'])
        products_df.to_sql('products', conn, if_exists='replace', index=False)
        
        # 2. إنشاء جدول العملاء (بأعمدة الأمازون الحقيقية)
        customers_df = df[['CustomerID', 'CustomerName', 'City', 'State', 'Country']].drop_duplicates(subset=['CustomerID'])
        customers_df.to_sql('customers', conn, if_exists='replace', index=False)
        
        # 3. إنشاء جدول الطلبات والمبيعات 
        orders_df = df[['OrderID', 'OrderDate', 'CustomerID', 'ProductID', 'Quantity', 'Discount', 'Tax', 'ShippingCost', 'TotalAmount', 'PaymentMethod', 'OrderStatus']]
        orders_df.to_sql('orders', conn, if_exists='replace', index=False)
        
        conn.commit()
        conn.close()
        print("✅ تم تحويل ملف Amazon.csv إلى قاعدة بيانات store.db بنجاح! 🎉")
        
    except Exception as e:
        print(f"❌ حدث خطأ أثناء بناء الداتا بيز: {e}")

if __name__ == "__main__":
    build_database_from_csv()