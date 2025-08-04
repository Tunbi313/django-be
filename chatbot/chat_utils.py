

import os
from dotenv import load_dotenv
import psycopg2
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader, TextLoader  # Thêm UnstructuredWordDocumentLoader nếu dùng .docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings # Để tạo embeddings cục bộ
from langchain_community.vectorstores import FAISS # Vector Store cục bộ
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage # Cần import đầy đủ các loại Message
from pydantic import SecretStr
from langchain.docstore.document import Document
from langchain.chains import create_retrieval_chain


# Tải biến môi trường ngay khi module được import
load_dotenv()
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv("OPENROUTER_MODEL")
print("OPENROUTER_MODEL:", openrouter_model)
print("OPENROUTER_API_KEY",openrouter_api_key)

# Kiểm tra biến môi trường và raise lỗi nếu không tìm thấy
if openrouter_api_key is None or openrouter_model is None:
    raise EnvironmentError("OpenRouter API Key hoặc Model chưa được cấu hình. Vui lòng kiểm tra file .env.")

#lấy các biến môi trường cho database
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

# Khởi tạo LLM (biến toàn cục, được khởi tạo một lần)
llm = ChatOpenAI(
    model=openrouter_model,  # Sử dụng 'model' thay vì 'model_name'
    temperature=0.3, 
    api_key=SecretStr(openrouter_api_key),  # Bọc api_key bằng SecretStr
    base_url="https://openrouter.ai/api/v1",
    
)

# Biến toàn cục để lưu trữ knowledge base và retrieval chain
knowledge_base = None
retrieval_chain = None
is_rag_ready = False # Cờ báo hiệu RAG đã sẵn sàng hay chưa

# Biến toàn cục để lưu trữ lịch sử chat (bao gồm cả AI và user)
global_chat_history = []

def fetch_data_from_database(user_id=None):
    """
    Kết nối database và trích xuất dữ liệu dưới dạng Document
    """
    db_documents = []
    if not all([db_host, db_name, db_user, db_password, db_port]):
        print("Cảnh báo :Sai cấu hình Database trong .env")
        return db_documents  # Thoát hàm nếu thiếu cấu hình

    conn = None
    try: 
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        cur = conn.cursor()  # Sửa ở đây

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
        print(f"Đã tải thành công {len(db_documents)} document từ database.")
        if db_documents:
            print("Dữ liệu đầu tiên:", db_documents[0].page_content)
        else:
            print("Không có dữ liệu nào được đọc từ database.")

    except Exception as e:
        print(f"Lỗi khi kết nối hoặc truy vấn database: {e}")
    finally:
        if conn:
            conn.close()
    return db_documents






def prepare_knowledge_base_sync(data_dir="data"):
    """
    Tải tài liệu, tạo vector store (không split nhỏ hơn từng sản phẩm).
    Sẽ được gọi một lần khi server khởi động.
    """
    global knowledge_base, retrieval_chain, is_rag_ready

    documents = []
    # Kiểm tra xem thư mục dữ liệu có tồn tại không
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f"Đang quét thư mục dữ liệu: {data_dir}")
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if os.path.isfile(filepath):
                if filename.endswith(".pdf"):
                    print(f"Đang tải file PDF: {filename}")
                    loader = PyPDFLoader(filepath)
                    documents.extend(loader.load())
                elif filename.endswith(".txt"):
                    print(f"Đang tải file TXT: {filename}")
                    loader = TextLoader(filepath, encoding="utf-8")
                    documents.extend(loader.load())
    else:
        print(f"Thư mục dữ liệu '{data_dir}' không tồn tại hoặc không phải là thư mục. RAG sẽ không được kích hoạt.")
        is_rag_ready = False
        return

    # Thêm: Load từ database (mỗi sản phẩm là 1 Document)
    db_documents = fetch_data_from_database()
    documents.extend(db_documents)


    if not documents:
        print("Không tìm thấy tài liệu nào trong thư mục hoặc database.")
        is_rag_ready = False
        return

    # Không split nhỏ hơn nữa, mỗi document là 1 sản phẩm
    chunks = documents
    print(f"Tổng số document/chunk: {len(chunks)}")

    # In ra các chunk đầu tiên (tối đa 10 chunk đầu, 500 ký tự đầu)
    
    print("Đang tạo embeddings...")
    embeddings = SentenceTransformerEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    knowledge_base = FAISS.from_documents(chunks, embeddings)
    print("Đã tạo Vector Store thành công.")

    # --- Xây dựng Chain cho RAG ---
    retriever = knowledge_base.as_retriever(search_kwargs={"k": 15})

    # Prompt tối ưu - dùng {context} đúng chuẩn RAG chain
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Bạn là trợ lý AI về sản phẩm, chỉ trả lời dựa trên dữ liệu được cung cấp,không được bịa thông tin. Nếu không có thông tin, hãy nói rõ."
             "Nếu người dùng hỏi về sản phẩm hãy trả lời tập trung vào thông tin sản phẩm ấy có còn hàng hay không, giá cả, mô tả, giảm giá (nếu có).Không trả lời thêm các sản phẩm khác. Trả lời bằng tiếng Việt, đầy đủ và chính xác."
             "Nếu người dùng hỏi mà không có thông tin sản phẩm thì hãy trả lời là không tìm thấy thông tin phù hợp và gợi ý cho người dùng 1 sản phẩm cùng category nhưng chỉ cung cấp tên và giá tiền chứ không miêu tả thêm gì cả."
             "Nếu người dùng đồng ý về việc xem sản phẩm khác thì không nhắc lại các sản phẩm đã nhắc ở trên nũa mà hãy gợi ý cho người dùng 1-2 sản phẩm khác cùng category với sản phẩm đã hỏi."
             "Nếu người dùng chỉ hỏi về một phẩn của sản phẩm thì tập trung vào việc trả lời cho phần đó có thể hỏi người dung có muốn xem chi tiết phần đó không "
             ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{context}\n\nCâu hỏi: {input}\n\nChỉ trả lời dựa trên dữ liệu trên.")
        ]
    )

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    is_rag_ready = True
    print("Đã khởi tạo Retrieval Chain.")


def rewrite_user_question(user_message, chat_history_parsed, max_turns=3):
    """
    Dùng LLM để rewrite lại câu hỏi user dựa trên N lượt hội thoại gần nhất (cả AI và user).
    In ra đoạn hội thoại gần nhất và câu hỏi đã rewrite.
    """
    #Debug : số tin nhắn và phân loại
    total_messages = len(chat_history_parsed)
    ai_messages = [msg for msg in chat_history_parsed if isinstance(msg, AIMessage)]
    user_messages = [msg for msg in chat_history_parsed if isinstance(msg, HumanMessage)]
    print(f"DEBUG - Tổng tin nhắn: {total_messages}, AI: {len(ai_messages)}, User: {len(user_messages)}")
    
    # Lấy max_turns lượt hội thoại gần nhất (mỗi lượt gồm user và AI)
    # Đảm bảo luôn có cả AI và user
    filtered = []
    ai_count = 0
    user_count = 0
    # Duyệt từ cuối lên để lấy tin nhắn gần nhất
    for msg in reversed(chat_history_parsed):
        if isinstance(msg, (HumanMessage, AIMessage)):
            filtered.append(msg)
            if isinstance(msg, AIMessage):
                ai_count += 1
            elif isinstance(msg, HumanMessage):
                user_count += 1
            # Dừng khi đủ số lượng hoặc khi có đủ cả AI và user
            if ai_count >= max_turns and user_count >= max_turns:
                break
    filtered.reverse()  # Đảo lại thứ tự để giữ đúng thứ tự thời gian
    
    print(f"DEBUG - Tin nhắn được lọc: {len(filtered)}, AI: {ai_count}, User: {user_count}")
    
    # Tạo history_text ngắn gọn
    history_lines = []
    for msg in filtered:
        role = "User" if isinstance(msg, HumanMessage) else "AI"
        history_lines.append(f"{role}: {msg.content}")
    history_text = "\n".join(history_lines)
    
    # Kiểm tra xem có tin nhắn AI không
    if ai_count == 0:
        print("WARNING: Không tìm thấy tin nhắn AI trong history!")
        # Nếu không có AI, thêm một prompt đặc biệt
        prompt = (
            "Người dùng chỉ trả lời ngắn gọn. Dựa vào lịch sử hội thoại trước đó, hãy diễn giải lại câu hỏi của người dùng thành một câu hỏi rõ ràng, đầy đủ ngữ cảnh.\n"
            f"Lịch sử hội thoại:\n{history_text}"
            f"Câu hỏi của người dùng: {user_message}\n"
            "Câu hỏi đã diễn giải:"
        )
    else:
        prompt = (
            "Dựa vào đoạn hội thoại gần nhất giữa người dùng và AI dưới đây, hãy diễn giải lại câu hỏi của người dùng thành một câu hỏi rõ ràng, đầy đủ ngữ cảnh để AI có thể trả lời chính xác.\n"
            f"Đoạn hội thoại gần nhất:\n{history_text}"
            f"Câu hỏi của người dùng: {user_message}\n"
            "Câu hỏi đã diễn giải:"
        )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        rewritten = (response.content or user_message).strip()
    except Exception as e:
        print(f"❌ Rewrite lỗi: {e}")
        return user_message

    # In debug
    print("---- Đoạn hội thoại gần nhất ----")
    print(history_text)
    print("---- Câu hỏi đã rewrite ----")
    print(rewritten)

    return rewritten

def context_to_str(context):
    if isinstance(context, list):
        return "\n\n".join([getattr(doc, 'page_content', str(doc)) for doc in context])
    return str(context)

def context_to_data(context):
    return context_to_str(context)


def get_chatbot_response(user_message: str, chat_history_raw: list, user_id: int = None):
    """
    Xử lý tin nhắn người dùng và trả về phản hồi từ chatbot.
    """
    user_input_lower = user_message.lower()

    if any(keyword in user_input_lower for keyword in ["đổi hàng", "trả hàng", "hủy đơn", "đổi trả", "đổi sản phẩm","bảo hành"]):
        return {
            "answer": (
                "🔄 Chính sách đổi/trả hàng và bảo hành cần xác nhận qua các hình thức sau.\n"
                "📞 Hotline: 0909 123 456    \n"
                "💬 Zalo: https://zalo.me/yourshop\n"
                "💬 Facebook: https://facebook.com/yourshop\n"
                
            )
        }


    
    global global_chat_history
    
    # Kết hợp lịch sử từ frontend với lịch sử toàn cục
    combined_history = global_chat_history.copy()
    
    # Thêm tin nhắn user mới vào lịch sử
    combined_history.append({"role": "human", "content": user_message})
    
    chat_history_parsed = []
    for msg in combined_history:
        if isinstance(msg, dict):
            if msg.get("role") == "human":
                chat_history_parsed.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "ai":
                chat_history_parsed.append(AIMessage(content=msg.get("content", "")))
            elif msg.get("role") == "system":
                chat_history_parsed.append(SystemMessage(content=msg.get("content", "")))
        elif isinstance(msg, str):
            chat_history_parsed.append(HumanMessage(content=msg))

    try:
        # Rewrite lại câu hỏi user dựa vào ngữ cảnh hội thoại (AI + user)
        user_message_rewritten = rewrite_user_question(user_message, chat_history_parsed)
        if is_rag_ready and retrieval_chain:
            print("Sử dụng RAG chain...")
            response = retrieval_chain.invoke({
                "input": user_message_rewritten,
                "history": chat_history_parsed
            })
            # Đảm bảo context là string
            context_str = context_to_str(response["context"]) if "context" in response else ""
            print("DEBUG - Context truyền vào prompt:")
            print(context_str)
            print(f"DEBUG - Input gửi đến LLM: {user_message_rewritten}")
            # Render prompt thực tế gửi đến LLM
            prompt_text = f"{context_str}\n\nCâu hỏi: {user_message_rewritten}\n\nChỉ trả lời dựa trên dữ liệu trên."
            print("DEBUG - Prompt thực tế gửi đến LLM:")
            print(prompt_text)
            ai_response = response["answer"]
            print(f"DEBUG - AI response từ RAG: '{ai_response}'")
        else:
            print("Sử dụng LLM cơ bản (không có RAG).")
            if not chat_history_parsed or chat_history_parsed[0].type != "system":
                chat_history_parsed.insert(0, SystemMessage(content="Bạn là một trợ lý AI hữu ích và thân thiện. Bạn sẽ trả lời bằng tiếng Việt."))
            chat_history_parsed.append(HumanMessage(content=user_message_rewritten))
            llm_response = llm.invoke(chat_history_parsed)
            ai_response = llm_response.content
        
        # Lưu tin nhắn AI vào lịch sử toàn cục
        global_chat_history.append({"role": "ai", "content": ai_response})
        
        # Giới hạn độ dài lịch sử để tránh quá tải (giữ tối đa 20 tin nhắn)
        if len(global_chat_history) > 20:
            global_chat_history = global_chat_history[-20:]
        
        return {"answer": ai_response}
    except Exception as e:
        print(f"Lỗi LangChain/LLM khi xử lý chat: {e}")
        return {"answer": "Xin lỗi, tôi đang gặp vấn đề nội bộ. Vui lòng thử lại sau."}