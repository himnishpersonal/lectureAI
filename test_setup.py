#!/usr/bin/env python3
"""
Test script to verify CrossCheck setup is working properly.
Run this to check if all components are functioning.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required packages can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import streamlit
        print("✅ Streamlit")
    except ImportError as e:
        print(f"❌ Streamlit: {e}")
        return False
    
    try:
        import fastapi
        print("✅ FastAPI")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    try:
        import faiss
        print("✅ FAISS")
    except ImportError as e:
        print(f"❌ FAISS: {e}")
        return False
    
    try:
        import sentence_transformers
        print("✅ SentenceTransformers")
    except ImportError as e:
        print(f"❌ SentenceTransformers: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2")
    except ImportError as e:
        print(f"❌ PyPDF2: {e}")
        return False
    
    try:
        from docx import Document
        print("✅ python-docx")
    except ImportError as e:
        print(f"❌ python-docx: {e}")
        return False
    
    return True

def test_backend_services():
    """Test that backend services can be initialized."""
    print("\n🔍 Testing backend services...")
    
    try:
        from backend.utils.config import get_settings
        settings = get_settings()
        print("✅ Configuration loaded")
    except Exception as e:
        print(f"❌ Configuration: {e}")
        return False
    
    try:
        from backend.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        print(f"✅ Embedding service ({'available' if embedding_service.is_available() else 'not available'})")
    except Exception as e:
        print(f"❌ Embedding service: {e}")
        return False
    
    try:
        from backend.services.vector_store import VectorStore
        vector_store = VectorStore()
        print(f"✅ Vector store ({'available' if vector_store.is_available() else 'not available'})")
    except Exception as e:
        print(f"❌ Vector store: {e}")
        return False
    
    try:
        from backend.services.document_processor import DocumentProcessor
        doc_processor = DocumentProcessor()
        print("✅ Document processor")
    except Exception as e:
        print(f"❌ Document processor: {e}")
        return False
    
    try:
        from backend.services.rag_service import RAGService
        rag_service = RAGService()
        print(f"✅ RAG service ({'configured' if rag_service.is_configured() else 'not configured - missing API key'})")
    except Exception as e:
        print(f"❌ RAG service: {e}")
        return False
    
    return True

def test_database():
    """Test database connection."""
    print("\n🔍 Testing database...")
    
    try:
        from sqlalchemy import create_engine
        from backend.utils.config import get_settings
        from backend.models import Base
        
        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database connection and table creation")
        return True
    except Exception as e:
        print(f"❌ Database: {e}")
        return False

def test_embedding_functionality():
    """Test basic embedding functionality."""
    print("\n🔍 Testing embedding functionality...")
    
    try:
        from backend.services.embedding_service import EmbeddingService
        
        embedding_service = EmbeddingService()
        if not embedding_service.is_available():
            print("⚠️ Embedding service not available - will download model on first use")
            return True
        
        # Test basic embedding
        test_text = "This is a test sentence for embedding."
        embedding = embedding_service.encode_text(test_text)
        print(f"✅ Generated embedding with dimension: {len(embedding)}")
        return True
    except Exception as e:
        print(f"❌ Embedding functionality: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 CrossCheck Setup Test\n" + "="*50)
    
    tests = [
        test_imports,
        test_backend_services,
        test_database,
        test_embedding_functionality
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! CrossCheck is ready to use.")
        print("\nNext steps:")
        print("1. Start the backend: uvicorn backend.api:app --reload")
        print("2. Start the frontend: streamlit run app.py")
        print("3. (Optional) Add your OpenRouter API key to .env for full RAG functionality")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
