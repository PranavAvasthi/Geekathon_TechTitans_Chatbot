from typing import Dict, List, Optional, Any
from pathlib import Path
import os
from dotenv import load_dotenv # type: ignore
from langchain_huggingface import HuggingFaceEmbeddings # type: ignore
from langchain_community.vectorstores import Chroma # type: ignore  
from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain.chains import ConversationalRetrievalChain # type: ignore
from langchain.chains.conversational_retrieval.base import BaseConversationalRetrievalChain # type: ignore
from langchain.memory import ConversationBufferWindowMemory # type: ignore
from bs4 import BeautifulSoup # type: ignore
import markdown # type: ignore
import time
from tenacity import ( # type: ignore
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import requests.exceptions
import chromadb # type: ignore
import chromadb.config # type: ignore

# Load environment variables
load_dotenv()

class CodeAnalyzer:
    def __init__(self):
        """Initialize the code analyzer with necessary components."""
        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
            
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize LLM with GPT-4
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.2,
            request_timeout=90,  # Increased timeout for GPT-4
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize text splitter with larger chunks for GPT-4's context window
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,   # Increased chunk size for GPT-4
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        self.vector_store = None
        self.conversation_chain = None
        
        # Keep track of processed files and their contents
        self.file_map = {}
        self.file_contents = {}
        
        # Configure ChromaDB settings
        self.chroma_settings = chromadb.config.Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=False  # Use in-memory storage for temporary sessions
        )

    def _create_chain(self) -> BaseConversationalRetrievalChain:
        """Create a new conversation chain with proper configuration."""
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            output_key="answer",
            input_key="question",
            return_messages=True,
            k=10
        )
        
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 6}
            ),
            memory=memory,
            return_source_documents=True,
            verbose=True,
            chain_type="stuff",
            get_chat_history=lambda h: h,  # Simple chat history handler
            combine_docs_chain_kwargs={"output_key": "answer"}
        )

    def process_code_files(self, files: List[Path]) -> None:
        """Process code files and create a vector store."""
        if not files:
            print("No files found to analyze")
            return
        
        documents = []
        
        for file_path in files:
            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8')
                
                # Skip empty files
                if not content.strip():
                    continue
                
                # Store the original content
                self.file_contents[str(file_path)] = content
                
                # Add file metadata as context
                file_context = f"""
                File: {file_path.name}
                Path: {file_path}
                Type: {file_path.suffix[1:]} file
                """
                
                # Create chunks for the content
                chunks = self.text_splitter.split_text(content)
                
                # Store file path for each chunk
                for i, chunk in enumerate(chunks):
                    if not chunk.strip():  # Skip empty chunks
                        continue
                    doc_id = f"{file_path}_{i}"
                    self.file_map[doc_id] = str(file_path)
                    documents.append({
                        "text": chunk,
                        "metadata": {
                            "file": str(file_path),
                            "chunk_id": i,
                            "file_type": file_path.suffix[1:],
                            "file_name": file_path.name
                        }
                    })
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue

        if documents:
            try:
                # Create vector store with settings
                self.vector_store = Chroma.from_texts(
                    texts=[doc["text"] for doc in documents],
                    embedding=self.embeddings,
                    collection_name="code_chunks",
                    metadatas=[doc["metadata"] for doc in documents],
                    client_settings=self.chroma_settings
                )
                
                # Create conversation chain
                self.conversation_chain = self._create_chain()
                
            except Exception as e:
                print(f"Error creating vector store: {str(e)}")
                raise

    def get_code_explanation(self, query: str) -> Optional[str]:
        """Get explanation for code-related queries."""
        if not self.conversation_chain:
            return "❌ Please load a repository first."
        
        try:
            # Add timeout handling
            start_time = time.time()
            timeout = 90  # seconds
            
            # Check if query is about specific file
            show_code = any(keyword in query.lower() for keyword in ["show", "display", "what's in", "what is in", "content of"])
            
            # Find the requested file using improved path handling
            requested_file = self._find_file_path(query)
            
            if requested_file:
                # Get the file content directly from our storage
                file_content = self.file_contents.get(requested_file)
                
                if not file_content:
                    return f"❌ I found the file '{requested_file}' but couldn't retrieve its contents. Please try reloading the repository."
                
                # If user just wants to see the code, return it directly
                if show_code:
                    file_extension = Path(requested_file).suffix[1:]
                    return f"""📄 Contents of {Path(requested_file).name} (from {requested_file}):

```{file_extension}
{file_content}
```"""
                
                # Enhanced query with file content
                enhanced_query = f"""
                Question about file: {Path(requested_file).name}
                File path: {requested_file}
                
                File content:
                ```{Path(requested_file).suffix[1:]}
                {file_content}
                ```
                
                User question: {query}
                
                Please provide a detailed explanation of the code, including its purpose, structure, and key components.
                If the user is asking to see the code, include the code snippet in your response.
                """
            else:
                # If no specific file is mentioned, provide repository structure
                # Group files by directory for better organization
                files_by_dir = {}
                for file_path in sorted(set(self.file_map.values())):
                    dir_path = str(Path(file_path).parent)
                    if dir_path not in files_by_dir:
                        files_by_dir[dir_path] = []
                    files_by_dir[dir_path].append(Path(file_path).name)
                
                # Format the file structure
                file_structure = []
                for dir_path, files in sorted(files_by_dir.items()):
                    file_structure.append(f"\n📁 {dir_path}:")
                    for file in sorted(files):
                        file_structure.append(f"  - {file}")
                
                file_list = "\n".join(file_structure)
                enhanced_query = f"""
                Repository structure:
                {file_list}
                
                User question: {query}
                
                Note: The file might be in one of these directories. Please check the repository structure and inform the user about available files.
                """
            
            # Check for timeout
            if time.time() - start_time > timeout:
                return "⚠️ Request timed out. Please try again with a more specific query."
            
            # Make the query
            response = self.conversation_chain({"question": enhanced_query})
            
            # Extract answer and sources
            answer = response.get("answer", "")
            source_docs = response.get("source_documents", [])
            
            # Add source information to response if available
            if source_docs:
                sources = set(doc.metadata['file'] for doc in source_docs)
                source_info = "\n\n📁 Sources:\n" + "\n".join(f"- {src}" for src in sources)
                return answer + source_info
            
            return answer
            
        except Exception as e:
            print(f"Detailed error: {str(e)}")
            if "timeout" in str(e).lower():
                return "⚠️ The request timed out. Please try:\n1. A more specific query\n2. Asking about a smaller part of the code\n3. Breaking your question into smaller parts"
            return f"❌ Error generating explanation: {str(e)}"

    def _find_file_path(self, query: str) -> Optional[str]:
        """Find the full file path from a query, handling nested folders."""
        query_lower = query.lower()
        
        # First try exact matches
        for file_path in self.file_map.values():
            if file_path.lower() in query_lower:
                return file_path
        
        # Then try filename matches
        for file_path in self.file_map.values():
            file_name = Path(file_path).name
            if file_name.lower() in query_lower:
                return file_path
        
        # Try partial path matches (e.g., "components/Button.tsx")
        for file_path in self.file_map.values():
            path_parts = Path(file_path).parts
            for i in range(len(path_parts)):
                partial_path = str(Path(*path_parts[-(i+1):]))
                if partial_path.lower() in query_lower:
                    return file_path
        
        return None

    def reset(self):
        """Reset the analyzer state."""
        if self.vector_store:
            try:
                self.vector_store.delete_collection()
            except:
                pass
            self.vector_store = None
        if self.conversation_chain:
            self.conversation_chain = None
        self.memory.clear()
        self.file_map.clear()
        self.file_contents.clear()  # Clear stored file contents