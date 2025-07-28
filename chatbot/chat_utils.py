

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
    temperature=0.00001, # Nên để temperature thấp hơn cho RAG để AI ít "sáng tạo" và bám sát dữ liệu hơn
    api_key=SecretStr(openrouter_api_key),  # Bọc api_key bằng SecretStr
    base_url="https://openrouter.ai/api/v1",
)

# Biến toàn cục để lưu trữ knowledge base và retrieval chain
knowledge_base = None
retrieval_chain = None
is_rag_ready = False # Cờ báo hiệu RAG đã sẵn sàng hay chưa

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
                f"ID sản phẩm: {product_id}.\n"
                f"Tên: {name}.\n"
                f"Mô tả: {description}.\n"
                f"Giá gốc: {price}.\n"
                f"Giá hiện tại: {current_price}.\n"
                f"Giảm giá: {discount_percent}%.\n"
                f"Danh mục: {category}.\n"
                f"Thời gian: {created_at}"
            )
            metadata = {"source": "database", "table": "products", "product_id": product_id, "name": name}
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
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    knowledge_base = FAISS.from_documents(chunks, embeddings)
    print("Đã tạo Vector Store thành công.")

    # --- Xây dựng Chain cho RAG ---
    retriever = knowledge_base.as_retriever(search_kwargs={"k": 8})

    # Prompt tối ưu
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Bạn là trợ lý AI về sản phẩm. Khi trả lời về sản phẩm, hãy trích xuất và trình bày đầy đủ các trường: tên, ID, danh mục, giá, mô tả,... từ dữ liệu truy xuất được. Nếu không có trường nào, hãy nói rõ là không có. Tuyệt đối không bịa thông tin."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Ngữ cảnh: {context}\n\nCâu hỏi: {input}")
        ]
    )

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    is_rag_ready = True
    print("Đã khởi tạo Retrieval Chain.")


def get_chatbot_response(user_message: str, chat_history_raw: list, user_id: int = None):
    """
    Xử lý tin nhắn người dùng và trả về phản hồi từ chatbot.
    """
    chat_history_parsed = []
    for msg in chat_history_raw:
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
        if is_rag_ready and retrieval_chain:
            print("Sử dụng RAG chain...")
            response = retrieval_chain.invoke({
                "input": user_message,
                "history": chat_history_parsed
            })
            # In context thực tế để debug
            if "context" in response:
                print("Context truy xuất được:")
                print(response["context"])
            else:
                print("Không có context truy xuất được!")
            ai_response = response["answer"]
        else:
            print("Sử dụng LLM cơ bản (không có RAG).")
            if not chat_history_parsed or chat_history_parsed[0].type != "system":
                chat_history_parsed.insert(0, SystemMessage(content="Bạn là một trợ lý AI hữu ích và thân thiện. Bạn sẽ trả lời bằng tiếng Việt."))
            chat_history_parsed.append(HumanMessage(content=user_message))
            llm_response = llm.invoke(chat_history_parsed)
            ai_response = llm_response.content
        return ai_response
    except Exception as e:
        print(f"Lỗi LangChain/LLM khi xử lý chat: {e}")
        return "Xin lỗi, tôi đang gặp vấn đề nội bộ. Vui lòng thử lại sau."