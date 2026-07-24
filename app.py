import streamlit as st
import sqlite3
import pandas as pd
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
import os

# استيراد مكتبات الـ RAG والـ VectorStore
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------------------------------------
# 1. إعداد واجهة الـ Streamlit ودعم الـ RTL وتنسيق الجداول
# ---------------------------------------------------------
st.set_page_config(page_title="Amazon SQL AI Agent", page_icon="📊", layout="wide")

# حقن كود CSS لضبط اتجاه الواجهة ومحاذاة الجداول والقوائم
# حقن كود CSS لضبط اتجاه الواجهة ومحاذاة القوائم والرسائل بدون تخريب الجداول
st.markdown("""
    <style>
    /* 1. ضبط اتجاه التطبيق بالكامل ليصبح من اليمين إلى اليسار */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    
    /* 2. محاذاة نصوص العناوين والفقرات ومربعات الرسائل */
    p, div, h1, h2, h3, h4, h5, h6, label {
        text-align: right !important;
    }

    /* 3. تعديل اتجاه مربع إدخال الدردشة (Chat Input) */
    .stChatInputContainer textarea {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 4. محاذاة فقاعات الرسائل (Chat Messages) */
    [data-testid="stChatMessage"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* 5. ضبط عرض الجدول ومنع ترحيل الأعمدة */
    [data-testid="stDataFrame"] {
        width: 100% !important;
    }

    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        text-align: center !important;
    }
    
    /* 6. محاذاة عناصر الأكورديون (Expander) */
    .st-emotion-cache-p5msec {
        text-align: right !important;
    }
    
    /* 7. تحسين تنسيق القوائم والنقاط */
    [data-testid="stChatMessage"] ul, [data-testid="stChatMessage"] ol {
        padding-right: 25px !important;
        padding-left: 0px !important;
        direction: rtl !important;
        text-align: right !important;
    }

    [data-testid="stChatMessage"] li {
        margin-bottom: 8px !important;
        text-align: right !important;
    }

    [data-testid="stChatMessage"] p {
        line-height: 1.7 !important;
        margin-bottom: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 نظام المساعد الذكي لبيانات الشركة (أمازون)")
st.caption("مرحباً بك! يمكنك الآن الاستفسار المباشر بـ SQL أو طلب استشارات وتحليلات ذكية للمخازن والمبيعات.")

# ---------------------------------------------------------
# 2. تهيئة الموديل مع تحديد حجم الـ Context
# ---------------------------------------------------------
llm = OllamaLLM(
    model="llama3",
    num_ctx=2048,
    temperature=0.1  # تقليل حجم الـ Context لمنع الـ CUDA OOM Error
)

# ---------------------------------------------------------
# 3. تهيئة الـ RAG Vectorstore لربطه مع فولدر knowledge
# ---------------------------------------------------------
@st.cache_resource
def init_rag_retriever():
    if os.path.exists("knowledge"):
        try:
            loader = DirectoryLoader( 
                "knowledge", 
                glob="*.md", 
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'}
            )
            docs = loader.load()
            
            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )               
            vectorstore = FAISS.from_documents(docs, embeddings)
            return vectorstore.as_retriever(search_kwargs={"k": 2})
        except Exception as e:
            st.warning(f"تحذير: لم يتم تحميل ملفات الـ Knowledge Base بنجاح: {e}")
            return None
    return None

retriever = init_rag_retriever()

# ---------------------------------------------------------
# 4. دالات التعامل مع قاعدة البيانات وفحص الأمان
# ---------------------------------------------------------
def is_safe_sql(query):
    """فحص الاستعلام للتأكد من أنه أمر قراءة فقط (SELECT) لمنع SQL Injection أو التعديل."""
    clean_query = query.strip().upper()
    forbidden_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE"]
    for keyword in forbidden_keywords:
        if keyword in clean_query:
            return False
    return clean_query.startswith("SELECT")

def get_schema():
    conn = sqlite3.connect("store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_details = ""
    for table in tables:
        table_name = table[0]
        schema_details += f"\nTable: {table_name}\nColumns:\n"
        cursor.execute(f"PRAGMA table_info({table_name});")
        for col in cursor.fetchall():
            schema_details += f"  - {col[1]} ({col[2]})\n"
    conn.close()
    return schema_details

def run_query_df(query):
    try:
        conn = sqlite3.connect("store.db")
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

# ---------------------------------------------------------
# 5. دالة الـ Router لتصنيف طلبات المستخدم
# ---------------------------------------------------------
def route_input(question, chat_history):
    router_prompt = ChatPromptTemplate.from_template(
        """You are an intent classification system for an Amazon Data Assistant app.
Analyze the user's message and classify its intent into EXACTLY ONE of the following tags:

- GENERAL: Casual talk, greetings, check-ins, or non-data sentences (e.g., "ازيك", "هلا", "صباح الخير", "يلا بينا", "شكرا", "hello").
- DATA_QUERY: Any request needing database access, SQL query execution, sales numbers, strategic analysis, or business advice based on data.

CRITICAL: Output ONLY the classification tag name (GENERAL or DATA_QUERY). Nothing else.

User Message: {question}
Intent:"""
    )
    
    router_chain = router_prompt | llm | StrOutputParser()
    result = router_chain.invoke({"question": question, "chat_history": chat_history}).strip().upper()
    
    return "GENERAL" if "GENERAL" in result else "DATA_QUERY"

# ---------------------------------------------------------
# 6. الـ Prompts المعدلة بالنظام الجديد
# ---------------------------------------------------------
sql_prompt = ChatPromptTemplate.from_template(
    """You are a strict and precise SQLite expert. Write a clean, valid, and executable SQL SELECT query to retrieve the exact data required to answer or analyze the user's request.

⚠️ CRITICAL RULES:
1. Return ONLY the raw SQL query starting directly with SELECT. Do NOT include markdown syntax, introductory text, or SQL comments.
2. ALWAYS use explicit column aliases (AS) for all aggregations and calculations (e.g., SELECT COUNT(*) AS OrdersCount, SUM(TotalAmount) AS TotalLoss).
3. Do NOT leave expressions without aliases (e.g., NEVER return `COUNT(o.OrderStatus)` directly as a column name).
4. ALWAYS use explicit ordering (e.g., ORDER BY ... DESC) whenever top categories, highest revenue, or rankings are needed.
5. Strictly adhere to the Database Schema and Business Knowledge rules below.

Database Schema:
{schema}

Retrieved Business Knowledge & Rules (RAG Context):
{context}

User Question: {question}
SQL Query:"""
)

sql_fix_prompt = ChatPromptTemplate.from_template(
    """The SQL query you generated failed with an error. Correct it and return ONLY a valid SQLite query starting with SELECT.

Database Schema:
{schema}

Failed SQL Query:
{failed_sql}

Error Message:
{error}

User Question:
{question}

Corrected SQL Query:"""
)

analysis_prompt = ChatPromptTemplate.from_template(
"""أنت مستشار أعمال ومحلل بيانات استراتيجي لشركة أمازون.

بناءً على نتائج استعلام قاعدة البيانات الحقيقية المرفقة أدناه، قدم تحليلاً وتوصيات استراتيجية إدارية تُجيب بدقة عن سؤال المستخدم.

⚠️ قواعد حازمة جداً للغة والتنسيق:
1. **اللغة والترجمة المباشرة:** 
   - اكتب الرد باللغة العربية الفصحى البسيطة والمباشرة فقط. 
   - يُمنع منعاً باتاً استخدام أي كلمات إنجليزية أو تكرار المصطلحات الأجنبية الواردة في السؤال (مثال: ترجم "processing pending orders" إلى "معالجة الطلبات المعلقة").
   - يُمنع استخدام أي كلمات من لغات أجنبية أخرى (مثل الكلمات السلافية/الألمانية/التركية/الإسبانية مثل mientras).

2. **الدقة المفهومية والرقمية:** 
   - اعتمد بنسبة 100% على الأرقام الواردة في جدول البيانات المرفق فقط. لا تحسب ولا تخترع نسباً مئوية أو أرقاماً غير موجودة بالجدول.
   - التزم بالدقة والمسميات: إذا كان العمود يمثل المجموع الحسابي (Total)، سمّه "إجمالي" ولا تطلق عليه لفظ "متوسط" أو "معدل" إطلاقاً.

3. **التنسيق:**
   - ابدأ بذكر الأرقام والنتائج المباشرة من الجدول أولاً بوضوح وتركيز.
   - اتبعها بـ (3 إلى 4) توصيات عملية محددة بأسلوب النقاط (Bullet points) بدون تكرار نفس المعنى في أكثر من نقطة.

سؤال المستخدم: {question}

البيانات الحقيقية المستخرجة:
{data_table}

التحليل والتوصيات الاستراتيجية:"""
)

# ---------------------------------------------------------
# 7. إدارة جلسة الـ Chat History
# ---------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "df" in message:
            st.dataframe(message["df"])

# ---------------------------------------------------------
# 8. استقبال وإرسال الرسائل
# ---------------------------------------------------------
if user_question := st.chat_input("اسألني أي شيء عن المبيعات أو المنتجات..."):
    with st.chat_message("user"):
        st.write(user_question)
    
    st.session_state.messages.append({"role": "user", "content": user_question})
    chat_history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-1]])
    
    with st.chat_message("assistant"):
        intent = route_input(user_question, chat_history_str)
        
        # 🟢 المسار الأول: الدردشة العامة
        if intent == "GENERAL":
            with st.spinner("جاري الرد..."):
                general_prompt = ChatPromptTemplate.from_template(
                    """أنت مساعد ذكي متخصص لبيانات شركة أمازون.

قواعد اللغة والصياغة:
- إذا كانت رسالة المستخدم مكتوبة بالحروف العربية، رد باللغة العربية بأسلوب مصري ودود.
- يُمنع استخدام الإنجليزية أو الفرانكو عند الرد على رسالة عربية.
- إذا كانت الرسالة إنجليزية فقط، رد باللغة الإنجليزية.

رسالة المستخدم الحالية: {question}
الرد:"""
                )
                general_chain = general_prompt | llm | StrOutputParser()
                response = general_chain.invoke({"question": user_question})
                
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
        # 🔵 المسار الثاني: استعلام وتحليل البيانات الديناميكي (DATA_QUERY)
        else:
            with st.spinner("جاري استعلام قاعدة البيانات وتحليل الأرقام..."):
                schema = get_schema()
                retrieved_docs = retriever.invoke(user_question) if retriever else []
                rag_context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                
                # 1. توليد استعلام SQL ديناميكي يخدم السؤال
                sql_chain = sql_prompt | llm | StrOutputParser()
                raw_sql = sql_chain.invoke({
                    "schema": schema,
                    "context": rag_context if rag_context else "No extra guidelines provided.",
                    "question": user_question
                })
                
                # تنظيف استعلام الـ SQL
                sql_query = re.sub(r"```sql|```", "", raw_sql).strip()
                if "SELECT" in sql_query:
                    sql_query = sql_query[sql_query.find("SELECT"):]
                if ";" in sql_query:
                    sql_query = sql_query.split(";")[0] + ";"

                # 🔒 فحص الأمان
                if not is_safe_sql(sql_query):
                    st.error("⚠️ خطأ أمان: يُسمح فقط باستعلامات القراءة (SELECT) لضمان سلامة البيانات.")
                else:
                    df, error = run_query_df(sql_query)
                    
                    # 🔄 حلقة التصحيح الذاتي في حالة الخطأ
                    if error:
                        with st.spinner("حدث خطأ أثناء التنفيذ.. جاري إعادة تصحيح استعلام الـ SQL..."):
                            fix_chain = sql_fix_prompt | llm | StrOutputParser()
                            fixed_raw_sql = fix_chain.invoke({
                                "schema": schema,
                                "failed_sql": sql_query,
                                "error": error,
                                "question": user_question
                            })
                            
                            sql_query = re.sub(r"```sql|```", "", fixed_raw_sql).strip()
                            if "SELECT" in sql_query:
                                sql_query = sql_query[sql_query.find("SELECT"):]
                            if ";" in sql_query:
                                sql_query = sql_query.split(";")[0] + ";"
                            
                            df, error = run_query_df(sql_query)

                    # إخراج النتيجة والتحليل
                    if error:
                        st.error(f"حدث خطأ أثناء تنفيذ الـ SQL: {error}")
                        with st.expander("🛠️ عرض استعلام SQL الذي فشل"):
                            st.code(sql_query, language="sql")
                    else:
                        # 2. تمرير نتائج الـ DataFrame المترتبة إلى الـ Analysis Prompt مباشرة
                        analysis_chain = analysis_prompt | llm | StrOutputParser()
                        analysis_response = analysis_chain.invoke({
                            "question": user_question,
                            "data_table": df.to_string(index=False)
                        })
                        
                        st.write(analysis_response)
                        st.dataframe(df)
                        
                        with st.expander("🛠️ عرض استعلام SQL ومصادر الـ RAG"):
                            st.code(sql_query, language="sql")
                            st.write("📖 **المعلومات المسترجعة من الـ Knowledge Base (RAG):**")
                            st.info(rag_context if rag_context else "لم يتم استرجاع قواعد خاصة بهذا السؤال.")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": analysis_response,
                            "df": df
                        })