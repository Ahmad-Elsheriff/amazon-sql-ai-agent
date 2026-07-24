import sqlite3
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

# 1. الاتصال بموديل Llama 3 المتاح عندك على Ollama
llm = OllamaLLM(model="llama3", temperature=0)

# 2. دالة لجلب هيكل قاعدة البيانات (Schema) عشان الموديل يفهم الجداول
def get_schema():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
    schemas = [row[0] for row in cursor.fetchall()]
    conn.close()
    return "\n".join(schemas)

# 3. دالة لتنفيذ الـ SQL Query وجلب البيانات الحقيقية
def run_query(query):
    try:
        conn = sqlite3.connect("store.db")
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()
        return result, column_names
    except Exception as e:
        return str(e), []

# 4. بناء الـ Prompt اللي هيوجه الموديل لكتابة الـ SQL صح بدون رغي
sql_prompt = ChatPromptTemplate.from_template(
    """You are a SQLite expert. Given the database schema below, write a clean SQL query that answers the user's question.
    Return ONLY the raw SQL query inside code blocks, nothing else. Do not explain the query.

    Database Schema:
    {schema}

    User Question: {question}
    SQL Query:"""
)

# 5. بناء الـ Prompt اللي هياخد النتيجة الحقيقية ويصيغها للمستخدم كإجابة ذكية
response_prompt = ChatPromptTemplate.from_template(
    """أنتا مساعد ذكي خبير في تحليل البيانات. بناءً على السؤال المكتوب والبيانات المستخرجة من قاعدة البيانات، قم بكتابة إجابة واضحة ومختصرة باللغة العربية تشرح فيها النتيجة للمستخدم بشكل احترافي.

    سؤال المستخدم: {question}
    الـ SQL Query اللي اتنفذت: {query}
    البيانات المستخرجة الحقيقية: {result}

    الإجابة باللغة العربية:"""
)

# 6. الـ Flow الأساسي للـ Agent
def ask_agent(question):
    schema = get_schema()
    
    # الخطوة أ: توليد الـ SQL
    sql_chain = sql_prompt | llm | StrOutputParser()
    raw_sql = sql_chain.invoke({"schema": schema, "question": question})
    
    # تنظيف الـ SQL المستخرج من أي علامات كود زائدة (مثل ```sql)
    sql_query = re.sub(r"```sql|```", "", raw_sql).strip()
    print(f"\n[Generated SQL]: {sql_query}") # عشان نشوف الموديل فكر في إيه في الـ Terminal
    
    # الخطوة ب: تنفيذ الـ SQL في قاعدة البيانات
    db_result, columns = run_query(sql_query)
    
    if isinstance(db_result, str): # لو حصل خطأ في الـ SQL
        return f"عذراً، حدث خطأ أثناء تنفيذ الاستعلام: {db_result}"
    
    # الخطوة ج: صياغة الإجابة النهائية بالعربي
    response_chain = response_prompt | llm | StrOutputParser()
    final_response = response_chain.invoke({
        "question": question,
        "query": sql_query,
        "result": str(db_result)
    })
    
    return final_response

# لتجربة الـ Agent في الـ Terminal مباشرة
if __name__ == "__main__":
    print("الـ SQL Agent جاهز! اسأل أي سؤال عن البيانات (أو اكتب 'exit' للخروج):")
    while True:
        user_q = input("\nسؤالك: ")
        if user_q.lower() == 'exit':
            break
        answer = ask_agent(user_q)
        print(f"\nإجابة الـ AI:\n{answer}")