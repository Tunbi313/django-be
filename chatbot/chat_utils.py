import os
from dotenv import load_dotenv
import psycopg2
import sqlite3
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.documents import Document


# ==================== ENV ====================
load_dotenv()
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv("OPENROUTER_MODEL")

if not openrouter_api_key or not openrouter_model:
    raise EnvironmentError("OpenRouter API Key hoặc Model chưa được cấu hình. Kiểm tra file .env.")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "db.sqlite3")
#db_host = os.getenv("DB_HOST")
#db_port = os.getenv("DB_PORT")
#db_name = os.getenv("DB_NAME")
#db_user = os.getenv("DB_USER")
#db_password = os.getenv("DB_PASSWORD")


# ==================== LLM ====================
llm = ChatOpenAI(
    model=openrouter_model,
    temperature=0.03,
    api_key=SecretStr(openrouter_api_key),
    base_url="https://openrouter.ai/api/v1",
)


# ==================== GLOBAL STATE ====================
knowledge_base = None
is_rag_ready = False
global_chat_history = []


# ==================== DATABASE LOADER ====================
def fetch_data_from_database(user_id=None):
    db_documents = []
    #if not all([db_host, db_name, db_user, db_password, db_port]):
    if not os.path.exists(SQLITE_DB_PATH):
        print(" Sai cấu hình Database trong .env")
        return db_documents

    conn = None
    try:
        #conn = psycopg2.connect(
        #    host=db_host,
        #    database=db_name,
        #    user=db_user,
        #    password=db_password,
        #    port=db_port
        #)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cur = conn.cursor()

        sql_query = """
        SELECT p.id, p.name, p.description, p.price, p.created_at, c.name as category,
               CASE 
                   WHEN sp.discount_percent IS NOT NULL 
                   AND sp.start_date <= NOW() 
                   AND sp.end_date >= NOW() 
                   THEN p.price * (100 - sp.discount_percent) / 100
                   ELSE p.price 
               END as current_price,
               COALESCE(sp.discount_percent, 0) as discount_percent
        FROM products_product p
        LEFT JOIN products_category c ON p.category_id = c.id
        LEFT JOIN saleproduct_saleproduct sp ON p.id = sp.product_id;
        """
        cur.execute(sql_query)
        rows = cur.fetchall()

        for row in rows:
            product_id, name, description, price, created_at, category, current_price, discount_percent = row
            content = (
                f"Tên: {name}.\n"
                f"Mô tả: {description}.\n"
                f"Giá hiện tại: {current_price}.\n"
                f"Giảm giá: {discount_percent}%.\n"
                f"Danh mục: {category}.\n"
            )
            metadata = {"source": "database", "table": "products", "name": name}
            db_documents.append(Document(page_content=content, metadata=metadata))

        cur.close()
        print(f" Đã tải {len(db_documents)} document từ database.")

    except Exception as e:
        print(f" Lỗi khi truy vấn database: {e}")
    finally:
        if conn:
            conn.close()

    return db_documents


# ==================== KNOWLEDGE BASE ====================
def prepare_knowledge_base_sync(data_dir="data"):
    global knowledge_base, is_rag_ready

    documents = []

    # Load file
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f" Đang quét thư mục dữ liệu: {data_dir}")
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if os.path.isfile(filepath):
                if filename.endswith(".pdf"):
                    print(f" Đang tải PDF: {filename}")
                    loader = PyPDFLoader(filepath)
                    documents.extend(loader.load())
                elif filename.endswith(".txt"):
                    print(f" Đang tải TXT: {filename}")
                    loader = TextLoader(filepath, encoding="utf-8")
                    documents.extend(loader.load())
    else:
        print(f" Thư mục '{data_dir}' không tồn tại. RAG bị tắt.")
        is_rag_ready = False
        return

    # Load database documents
    db_documents = fetch_data_from_database()
    documents.extend(db_documents)

    if not documents:
        print(" Không tìm thấy tài liệu nào.")
        is_rag_ready = False
        return

    print(f" Tổng số document: {len(documents)}")

    # Embeddings + Vector store
    print(" Đang tạo embeddings...")
    embeddings = SentenceTransformerEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    knowledge_base = FAISS.from_documents(documents, embeddings)
    print(" Vector Store đã sẵn sàng.")

    is_rag_ready = True
    print(" RAG đã khởi tạo thành công.")


# QUESTION REWRITE 
def rewrite_user_question(user_message: str, chat_history_parsed: list[BaseMessage], max_turns=3):
    total_messages = len(chat_history_parsed)
    ai_messages = [msg for msg in chat_history_parsed if isinstance(msg, AIMessage)]
    user_messages = [msg for msg in chat_history_parsed if isinstance(msg, HumanMessage)]
    print(f"DEBUG - Tổng tin nhắn: {total_messages}, AI: {len(ai_messages)}, User: {len(user_messages)}")

    filtered = []
    ai_count = 0
    user_count = 0
    for msg in reversed(chat_history_parsed):
        if isinstance(msg, (HumanMessage, AIMessage)):
            filtered.append(msg)
            if isinstance(msg, AIMessage):
                ai_count += 1
            elif isinstance(msg, HumanMessage):
                user_count += 1
            if ai_count >= max_turns and user_count >= max_turns:
                break
    filtered.reverse()

    history_lines = []
    for msg in filtered:
        role = "User" if isinstance(msg, HumanMessage) else "AI"
        history_lines.append(f"{role}: {msg.content}")
    history_text = "\n".join(history_lines)

    if ai_count == 0:
        prompt_text = (
            "Người dùng chỉ trả lời ngắn gọn. Dựa vào lịch sử hội thoại trước đó, hãy diễn giải lại câu hỏi của người dùng thành một câu hỏi rõ ràng, đầy đủ ngữ cảnh.\n"
            f"Lịch sử hội thoại:\n{history_text}\n"
            f"Câu hỏi của người dùng: {user_message}\n"
            "Câu hỏi đã diễn giải:"
        )
    else:
        prompt_text = (
            "Dựa vào đoạn hội thoại gần nhất giữa người dùng và AI dưới đây, hãy diễn giải lại câu hỏi của người dùng thành một câu hỏi rõ ràng, đầy đủ ngữ cảnh để AI có thể trả lời chính xác.\n"
            f"Đoạn hội thoại gần nhất:\n{history_text}\n"
            f"Câu hỏi của người dùng: {user_message}\n"
            "Câu hỏi đã diễn giải:"
        )

    try:
        response = llm.invoke([HumanMessage(content=prompt_text)])
        rewritten = (response.content or user_message).strip()
    except Exception as e:
        print(f" Rewrite lỗi: {e}")
        return user_message

    print("Đoạn hội thoại gần nhất")
    print(history_text)
    print("Câu hỏi đã rewrite:")
    print(rewritten)

    return rewritten


# ==================== CHATBOT RESPONSE ====================
def get_chatbot_response(user_message: str, chat_history_raw: list, user_id: int = None):
    user_input_lower = user_message.lower()

    # Business rules shortcut
    if any(keyword in user_input_lower for keyword in ["đổi hàng", "trả hàng", "hủy đơn", "đổi trả", "đổi sản phẩm", "bảo hành"]):
        return {
            "answer": (
                " Chính sách đổi/trả hàng và bảo hành cần xác nhận qua các hình thức sau.\n"
                " Hotline: 0909 123 456\n"
                " Zalo: https://zalo.me/yourshop\n"
                " Facebook: https://facebook.com/yourshop\n"
            )
        }

    global global_chat_history

    combined_history = global_chat_history.copy()
    combined_history.append({"role": "human", "content": user_message})

    # Parse history
    chat_history_parsed: list[BaseMessage] = []
    for msg in combined_history:
        if isinstance(msg, dict):
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "human":
                chat_history_parsed.append(HumanMessage(content=content))
            elif role == "ai":
                chat_history_parsed.append(AIMessage(content=content))
            elif role == "system":
                chat_history_parsed.append(SystemMessage(content=content))
        elif isinstance(msg, str):
            chat_history_parsed.append(HumanMessage(content=msg))
        elif isinstance(msg, BaseMessage):
            chat_history_parsed.append(msg)

    try:
        user_message_rewritten = rewrite_user_question(user_message, chat_history_parsed)

        # ================= RAG FLOW (MANUAL, SAFE) =================
        if is_rag_ready and knowledge_base:
            print("...Rag đang được sử dụng...")
            retriever = knowledge_base.as_retriever(search_kwargs={"k": 10})
            docs = retriever.invoke(user_message_rewritten)

            context_text = "\n\n".join(doc.page_content for doc in docs) if docs else "Không có dữ liệu liên quan."

            system_prompt = (
                "Bạn là trợ lý AI về sản phẩm, chỉ trả lời dựa trên dữ liệu được cung cấp, không được bịa thông tin. "
                "Nếu không có thông tin, hãy nói rõ. "
                "Nếu người dùng hỏi về sản phẩm, hãy trả lời tập trung vào tình trạng hàng, giá, mô tả, giảm giá (nếu có). "
                "Không trả lời thêm sản phẩm khác. Trả lời bằng tiếng Việt, đầy đủ và chính xác. "
                "Nếu không có thông tin sản phẩm, hãy gợi ý 1 sản phẩm cùng danh mục, chỉ cung cấp tên và giá. "
                "Nếu người dùng đồng ý xem thêm, hãy gợi ý 1–2 sản phẩm khác cùng danh mục, không lặp lại sản phẩm cũ."
            )

            messages = [
                SystemMessage(content=system_prompt),
                *chat_history_parsed,
                HumanMessage(
                    content=f"Dữ liệu:\n{context_text}\n\nCâu hỏi: {user_message_rewritten}\n\nChỉ trả lời dựa trên dữ liệu trên."
                )
            ]

            llm_response = llm.invoke(messages)
            ai_response = llm_response.content

        # ================= FALLBACK FLOW =================
        else:
            print("💬 Sử dụng LLM cơ bản (không RAG).")
            if not chat_history_parsed or chat_history_parsed[0].type != "system":
                chat_history_parsed.insert(
                    0, SystemMessage(content="Bạn là một trợ lý AI hữu ích và thân thiện. Bạn sẽ trả lời bằng tiếng Việt.")
                )
            chat_history_parsed.append(HumanMessage(content=user_message_rewritten))
            llm_response = llm.invoke(chat_history_parsed)
            ai_response = llm_response.content

        global_chat_history.append({"role": "ai", "content": ai_response})
        if len(global_chat_history) > 20:
            global_chat_history = global_chat_history[-20:]

        return {"answer": ai_response}

    except Exception as e:
        print(f"❌ Lỗi LangChain/LLM khi xử lý chat: {e}")
        return {"answer": "Xin lỗi, tôi đang gặp vấn đề nội bộ. Vui lòng thử lại sau."}
