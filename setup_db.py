import sqlite3

def init_db():
    # إنشاء أو الاتصال بقاعدة بيانات محلية باسم store.db
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()

    # 1. إنشاء جدول المنتجات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            category TEXT,
            price REAL,
            stock_quantity INTEGER
        )
    ''')

    # 2. إنشاء جدول العملاء
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            city TEXT,
            join_date DATE
        )
    ''')

    # 3. إنشاء جدول الطلبات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            order_date DATE,
            total_amount REAL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # تنظيف الجداول قبل إدخال داتا جديدة لتجنب التكرار
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM customers")
    cursor.execute("DELETE FROM orders")

    # إضافة داتا وهمية لتجربتها
    products_data = [
        ('iPhone 15', 'Electronics', 1200.0, 15),
        ('Samsung S24', 'Electronics', 1100.0, 20),
        ('MacBook Pro', 'Electronics', 2500.0, 8),
        ('Nike Sneakers', 'Clothing', 120.0, 50),
        ('Adidas Hoodie', 'Clothing', 85.0, 35),
        ('Coffee Maker', 'Home Appliances', 95.0, 12)
    ]
    cursor.executemany("INSERT INTO products (product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?)", products_data)

    customers_data = [
        ('Ahmad Elsherif', 'ahmad@email.com', 'Cairo', '2025-01-15'),
        ('Mohamed Ali', 'mohamed@email.com', 'Alexandria', '2025-03-22'),
        ('Sara Mansour', 'sara@email.com', 'Tanta', '2025-05-10'),
        ('Omar Hassan', 'omar@email.com', 'Cairo', '2025-06-01')
    ]
    cursor.executemany("INSERT INTO customers (name, email, city, join_date) VALUES (?, ?, ?, ?)", customers_data)

    orders_data = [
        (1, '2026-01-10', 1200.0), # أحمد اشترى آيفون
        (1, '2026-02-14', 85.0),   # أحمد اشترى هودي
        (2, '2026-03-25', 2500.0), # محمد اشترى ماك بوك
        (3, '2026-05-12', 120.0),  # سارة اشترت كوتشي
        (4, '2026-06-05', 95.0)    # عمر اشترى ماكينة قهوة
    ]
    cursor.executemany("INSERT INTO orders (customer_id, order_date, total_amount) VALUES (?, ?, ?)", orders_data)

    conn.commit()
    conn.close()
    print("قاعدة البيانات store.db وجداولها اتعملت واتملت داتا بنجاح! 🎉")

if __name__ == "__main__":
    init_db()
# المسار الثالث: استعلام داتا مباشر (SQL)
            else:
                with st.spinner("جاري كتابة استعلام SQL وتشغيله..."):
                    schema = get_schema()
                    sql_chain = sql_prompt | llm | StrOutputParser()
                    raw_sql = sql_chain.invoke({"schema": schema, "question": user_question})
                    sql_query = re.sub(r"```sql|```", "", raw_sql).strip()
                    
                    df, error = run_query_df(sql_query)
                    
                    if error:
                        st.error(f"حدث خطأ أثناء تنفيذ الـ SQL: {error}")
                        with st.expander("🛠️ عرض استعلام SQL الذي فشل"):
                            st.code(sql_query, language="sql")
                    else:
                        response_chain = response_prompt | llm | StrOutputParser()
                        final_response = response_chain.invoke({
                            "question": user_question,
                            "query": sql_query,
                            "result": df.head(10).to_string() # نمرر أول 10 سطور فقط لعدم تخطي حجم الـ Token
                        })
                        
                        st.write(final_response)
                        st.dataframe(df)
                        
                        with st.expander("🛠️ عرض استعلام SQL المنفذ"):
                            st.code(sql_query, language="sql")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": final_response,
                            "df": df
                        })    