

import os
from dotenv import load_dotenv
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

# Tải biến môi trường ngay khi module được import
load_dotenv()

openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv("OPENROUTER_MODEL")

# Kiểm tra biến môi trường và raise lỗi nếu không tìm thấy
if openrouter_api_key is None or openrouter_model is None:
    raise EnvironmentError("OpenRouter API Key hoặc Model chưa được cấu hình. Vui lòng kiểm tra file .env.")

# Khởi tạo LLM (biến toàn cục, được khởi tạo một lần)
llm = ChatOpenAI(
    model=openrouter_model,  # Sử dụng 'model' thay vì 'model_name'
    temperature=0.3, # Nên để temperature thấp hơn cho RAG để AI ít "sáng tạo" và bám sát dữ liệu hơn
    api_key=SecretStr(openrouter_api_key),  # Bọc api_key bằng SecretStr
    base_url="https://openrouter.ai/api/v1",
)

# Biến toàn cục để lưu trữ knowledge base và retrieval chain
knowledge_base = None
retrieval_chain = None
is_rag_ready = False # Cờ báo hiệu RAG đã sẵn sàng hay chưa

def prepare_knowledge_base_sync(data_dir="data"):
    """
    Tải tài liệu, chia nhỏ và tạo vector store (hàm đồng bộ).
    Sẽ được gọi một lần khi server khởi động.
    """
    global knowledge_base, retrieval_chain, is_rag_ready

    documents = []
    # Kiểm tra xem thư mục dữ liệu có tồn tại không
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f"Đang quét thư mục dữ liệu: {data_dir}")
        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if os.path.isfile(filepath): # Đảm bảo là file
                if filename.endswith(".pdf"):
                    print(f"Đang tải file PDF: {filename}")
                    loader = PyPDFLoader(filepath)
                    documents.extend(loader.load())
                elif filename.endswith(".txt"):
                    print(f"Đang tải file TXT: {filename}")
                    loader = TextLoader(filepath, encoding="utf-8")
                    documents.extend(loader.load())
                # elif filename.endswith(".docx"):
                #     from langchain_community.document_loaders import UnstructuredWordDocumentLoader
                #     print(f"Đang tải file DOCX: {filename}")
                #     loader = UnstructuredWordDocumentLoader(filepath)
                #     documents.extend(loader.load())
                # Thêm các loại loader khác nếu cần (ví dụ: UnstructuredMarkdownLoader, WebBaseLoader)
    else:
        print(f"Thư mục dữ liệu '{data_dir}' không tồn tại hoặc không phải là thư mục. RAG sẽ không được kích hoạt.")
        is_rag_ready = False
        return # Thoát hàm nếu không có thư mục dữ liệu

    if not documents:
        print("Không tìm thấy tài liệu nào trong thư mục. Chatbot sẽ hoạt động mà không có kiến thức RAG tùy chỉnh.")
        is_rag_ready = False
        return # Thoát hàm nếu không có tài liệu

    # Chia nhỏ tài liệu thành các đoạn nhỏ hơn (chunks)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, # Kích thước mỗi đoạn văn bản
        chunk_overlap=200 # Phần trùng lặp giữa các đoạn để giữ ngữ cảnh
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Đã chia tài liệu thành {len(chunks)} đoạn văn bản.")

    # Tạo embeddings
    print("Đang tạo embeddings...")
    # Sử dụng mô hình embedding cục bộ. Có thể thay bằng OpenAIEmbeddings qua OpenRouter nếu muốn
    # from langchain_openai import OpenAIEmbeddings
    # embeddings = OpenAIEmbeddings(openai_api_key=openrouter_api_key, base_url="https://openrouter.ai/api/v1")
    embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    # Tạo Vector Store
    # FAISS là một lựa chọn tốt để lưu trữ cục bộ trong bộ nhớ
    knowledge_base = FAISS.from_documents(chunks, embeddings)
    print("Đã tạo Vector Store thành công.")

    # --- Xây dựng Chain cho RAG ---
    retriever = knowledge_base.as_retriever()

    # Prompt cho LLM
    # MessagesPlaceholder(variable_name="history") cho phép LangChain tự động chèn lịch sử trò chuyện
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Bạn là một trợ lý AI hữu ích. Bạn sẽ trả lời các câu hỏi dựa trên ngữ cảnh được cung cấp. Nếu không tìm thấy thông tin trong ngữ cảnh, hãy nói rằng bạn không biết."),
            MessagesPlaceholder(variable_name="history"), # Để thêm lịch sử trò chuyện vào prompt
            ("human", "Ngữ cảnh: {context}\n\nCâu hỏi: {input}") # context sẽ chứa các đoạn thông tin truy xuất được
        ]
    )

    # Chain để kết hợp tài liệu và tạo phản hồi
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Chain hoàn chỉnh: Truy xuất -> Tăng cường -> Tạo sinh
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    is_rag_ready = True # Đánh dấu RAG đã sẵn sàng
    print("Đã khởi tạo Retrieval Chain.")

def get_chatbot_response(user_message: str, chat_history_raw: list):
    """
    Xử lý tin nhắn người dùng và trả về phản hồi từ chatbot.
    """
    # Chuyển đổi lịch sử từ Frontend (list of dict) sang định dạng của LangChain (list of Message objects)
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
            # Nếu là string, mặc định coi là tin nhắn của người dùng
            chat_history_parsed.append(HumanMessage(content=msg))

    try:
        if is_rag_ready and retrieval_chain: # Chỉ sử dụng RAG nếu nó đã được preload thành công
            print("Sử dụng RAG chain...")
            response = retrieval_chain.invoke({
                "input": user_message,
                "history": chat_history_parsed
            })
            ai_response = response["answer"]
        else:
            print("Sử dụng LLM cơ bản (không có RAG).")
            # Nếu không có RAG, hoặc RAG chưa sẵn sàng, dùng LLM cơ bản
            # Đảm bảo có SystemMessage ở đầu nếu chưa có trong lịch sử
            if not chat_history_parsed or chat_history_parsed[0].type != "system":
                chat_history_parsed.insert(0, SystemMessage(content="Bạn là một trợ lý AI hữu ích và thân thiện. Bạn sẽ trả lời bằng tiếng Việt."))

            # Thêm tin nhắn hiện tại của người dùng
            chat_history_parsed.append(HumanMessage(content=user_message))

            # Gọi LLM trực tiếp
            llm_response = llm.invoke(chat_history_parsed)
            ai_response = llm_response.content

        return ai_response
    except Exception as e:
        print(f"Lỗi LangChain/LLM khi xử lý chat: {e}")
        return "Xin lỗi, tôi đang gặp vấn đề nội bộ. Vui lòng thử lại sau."