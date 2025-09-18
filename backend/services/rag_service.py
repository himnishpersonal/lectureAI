"""RAG (Retrieval-Augmented Generation) service using OpenRouter API."""

import json
import logging
from typing import List, Dict, Any, Optional
import requests

from ..utils.config import get_settings
from .embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class RAGService:
    """Service for RAG queries using OpenRouter API."""
    
    def __init__(self, embedding_service=None, vector_store=None):
        self.settings = get_settings()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or VectorStore()
        self.api_key = self.settings.OPENROUTER_API_KEY
        self.base_url = self.settings.OPENROUTER_BASE_URL
        self.model = self.settings.LLM_MODEL
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key and self.api_key != "your_openrouter_api_key_here")
    
    def retrieve_relevant_chunks(
        self, 
        query: str, 
        max_results: int = 5,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant document chunks for a query."""
        try:
            if not self.embedding_service.is_available():
                logger.error("Embedding service not available")
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)
            
            # Search vector store
            search_results = self.vector_store.search(
                query_vector=query_embedding,
                k=max_results,
                document_ids=document_ids
            )
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return []
    
    def generate_response(
        self, 
        query: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate response using OpenRouter API."""
        if not self.is_configured():
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "answer": "Please configure your OpenRouter API key to use the RAG functionality."
            }
        
        try:
            # Prepare context from chunks
            context_texts = []
            for chunk in context_chunks:
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')
                filename = metadata.get('filename', 'Unknown')
                
                context_texts.append(f"[From {filename}]: {text}")
            
            context = "\n\n".join(context_texts)
            
            # Create prompt
            system_prompt = """You are an AI assistant specialized in journalism and document analysis. 
You help journalists analyze and cross-reference information from multiple documents.
Use the provided context to answer questions accurately and cite your sources.
If the context doesn't contain enough information, say so clearly."""
            
            user_prompt = f"""Context from documents:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. 
Cite specific documents when referencing information."""
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.settings.TEMPERATURE,
                "max_tokens": 1000
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=75
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                return {
                    "success": True,
                    "answer": answer,
                    "usage": result.get('usage', {}),
                    "model": self.model
                }
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "answer": "Sorry, I encountered an error while generating the response."
                }
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "answer": "Sorry, I encountered an error while processing your request."
            }
    
    def query_document(self, user_input: str, document_id: int, max_results: int = 5) -> Dict[str, Any]:
        """Perform RAG query on a specific document."""
        try:
            logger.info(f"RAG query_document called with input: '{user_input}', doc_id: {document_id}")
            
            if not self.embedding_service.is_available():
                logger.error("Embedding service not available")
                return {
                    "answer": "Embedding service is not available. Please check the installation.",
                    "citations": [],
                    "success": False
                }
            
            # Generate query embedding
            logger.info("Generating query embedding...")
            query_embedding = self.embedding_service.encode_text(user_input)
            logger.info(f"Query embedding shape: {query_embedding.shape}")
            
            # Search for relevant chunks in the specific document
            logger.info(f"Searching for relevant chunks in document {document_id}...")
            relevant_chunks = self.vector_store.search_document(
                document_id=document_id,
                query_vector=query_embedding,
                k=max_results
            )
            
            logger.info(f"Found {len(relevant_chunks)} relevant chunks")
            for i, chunk in enumerate(relevant_chunks):
                metadata = chunk.get('metadata', {})
                logger.info(f"Chunk {i}: similarity={chunk.get('similarity', 'N/A'):.3f}, text_preview='{metadata.get('text', 'N/A')[:100]}...'")
            
            if not relevant_chunks:
                logger.warning("No relevant chunks found")
                return {
                    "answer": "I couldn't find any relevant information in this document for your input.",
                    "citations": [],
                    "success": True
                }
            
            # Generate response with flexible prompt
            logger.info("Generating response with LLM...")
            response_data = self._generate_flexible_response(user_input, relevant_chunks)
            logger.info(f"LLM response success: {response_data.get('success', False)}")
            logger.info(f"LLM response length: {len(response_data.get('answer', ''))}")
            
            # Prepare citations
            citations = []
            for chunk in relevant_chunks:
                metadata = chunk.get('metadata', {})
                citations.append({
                    "chunk_index": metadata.get('chunk_index', 0),
                    "text": metadata.get('text', '')[:300] + "..." if len(metadata.get('text', '')) > 300 else metadata.get('text', ''),
                    "similarity_score": chunk.get('similarity', 0.0),
                    "estimated_tokens": metadata.get('estimated_tokens', 0),
                    "sentence_count": metadata.get('sentence_count', 0)
                })
            
            final_response = {
                "answer": response_data.get("answer", "No answer generated"),
                "citations": citations,
                "success": response_data.get("success", False),
                "model_info": {
                    "model": self.model,
                    "usage": response_data.get("usage", {})
                }
            }
            
            logger.info(f"Final response success: {final_response.get('success', False)}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error in document RAG query: {str(e)}", exc_info=True)
            return {
                "answer": f"Sorry, I encountered an error while processing your input: {str(e)}",
                "citations": [],
                "success": False
            }
    
    def query_course(self, user_input: str, course_id: int, max_results: int = 5) -> Dict[str, Any]:
        """Perform RAG query across all documents in a specific course."""
        try:
            logger.info(f"RAG query_course called with input: '{user_input}', course_id: {course_id}")
            
            if not self.embedding_service.is_available():
                logger.error("Embedding service not available")
                return {
                    "answer": "Embedding service is not available. Please check the installation.",
                    "citations": [],
                    "success": False
                }
            
            # Generate query embedding
            logger.info("Generating query embedding...")
            query_embedding = self.embedding_service.encode_text(user_input)
            logger.info(f"Query embedding shape: {query_embedding.shape}")
            
            # Search for relevant chunks across all documents in the course
            logger.info(f"Searching for relevant chunks in course {course_id}...")
            relevant_chunks = self.vector_store.search_course(
                course_id=course_id,
                query_vector=query_embedding,
                k=max_results
            )
            
            logger.info(f"Found {len(relevant_chunks)} relevant chunks")
            for i, chunk in enumerate(relevant_chunks):
                metadata = chunk.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')
                logger.info(f"Chunk {i}: similarity={chunk.get('similarity', 'N/A'):.3f}, from='{filename}', text_preview='{metadata.get('text', 'N/A')[:100]}...'")
            
            if not relevant_chunks:
                logger.warning("No relevant chunks found")
                return {
                    "answer": "I couldn't find any relevant information in this course's documents for your input.",
                    "citations": [],
                    "success": True
                }
            
            # Generate response with flexible prompt for multi-document context
            logger.info("Generating response with LLM...")
            response_data = self._generate_course_response(user_input, relevant_chunks)
            logger.info(f"LLM response success: {response_data.get('success', False)}")
            logger.info(f"LLM response length: {len(response_data.get('answer', ''))}")
            
            # Prepare citations with document source information
            citations = []
            for chunk in relevant_chunks:
                metadata = chunk.get('metadata', {})
                citations.append({
                    "chunk_index": metadata.get('chunk_index', 0),
                    "document_id": metadata.get('document_id', 0),
                    "filename": metadata.get('filename', 'Unknown'),
                    "text": metadata.get('text', '')[:300] + "..." if len(metadata.get('text', '')) > 300 else metadata.get('text', ''),
                    "similarity_score": chunk.get('similarity', 0.0),
                    "estimated_tokens": metadata.get('estimated_tokens', 0),
                    "sentence_count": metadata.get('sentence_count', 0)
                })
            
            final_response = {
                "answer": response_data.get("answer", "No answer generated"),
                "citations": citations,
                "chunks": relevant_chunks,  # Include raw chunks for frontend processing
                "success": response_data.get("success", False),
                "model_info": {
                    "model": self.model,
                    "usage": response_data.get("usage", {})
                }
            }
            
            logger.info(f"Final response success: {final_response.get('success', False)}")
            return final_response
            
        except Exception as e:
            logger.error(f"Error in course RAG query: {str(e)}", exc_info=True)
            return {
                "answer": f"Sorry, I encountered an error while processing your input: {str(e)}",
                "citations": [],
                "success": False
            }
    
    def _generate_flexible_response(self, user_input: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response with flexible prompt for questions and statements."""
        logger.info("Starting _generate_flexible_response...")
        
        if not self.is_configured():
            logger.error("OpenRouter API key not configured")
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "answer": "Please configure your OpenRouter API key to use the RAG functionality."
            }
        
        try:
            # Prepare context from chunks
            context_texts = []
            for i, chunk in enumerate(context_chunks, 1):
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')
                chunk_idx = metadata.get('chunk_index', i)
                
                context_texts.append(f"[Chunk {chunk_idx}]: {text}")
            
            context = "\n\n".join(context_texts)
            
            # Professor/Expert system prompt
            system_prompt = """You are an expert academic professor and educational assistant specialized in analyzing course materials. 
Using ONLY the provided document excerpts, provide scholarly and educational responses to student inquiries.

- If the input is a question, provide a thorough, pedagogical explanation that helps the student understand the concepts
- If the input is a topic or statement, offer comprehensive academic analysis with educational insights
- Use an authoritative yet approachable tone suitable for higher education
- Always cite specific chunks (e.g., "According to Chunk 1..." or "As referenced in Chunk 3...") to support your explanations
- When appropriate, connect concepts to broader academic frameworks or theories
- If the excerpts lack sufficient information, explain what additional context would be needed for a complete understanding
- Focus on fostering deep learning and critical thinking rather than just providing answers"""
            
            # Determine if input is likely a question
            is_question = user_input.strip().endswith('?') or any(
                user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did']
            )
            
            if is_question:
                user_prompt = f"""Student Question: {user_input}

Course Material Excerpts:
{context}

As an expert professor, provide a comprehensive educational response that helps the student understand this concept. Use the course material excerpts above to support your explanation, citing specific chunks. Where appropriate, connect the material to broader academic concepts or provide additional context that enhances learning."""
            else:
                user_prompt = f"""Learning Topic: {user_input}

Course Material Excerpts:
{context}

As an expert professor, provide a thorough academic analysis of this topic using the course material excerpts above. Offer educational insights that help students understand key concepts, relationships, and implications. Cite specific chunks and consider how this topic connects to broader educational objectives."""
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.settings.TEMPERATURE,
                "max_tokens": 1000
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=75
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                return {
                    "success": True,
                    "answer": answer,
                    "usage": result.get('usage', {}),
                    "model": self.model
                }
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "answer": "Sorry, I encountered an error while generating the response."
                }
                
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "answer": "Sorry, I encountered an error while processing your request."
            }
    
    def _generate_course_response(self, user_input: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response with multi-document context for course queries."""
        logger.info("Starting _generate_course_response for multi-document context...")
        
        if not self.is_configured():
            logger.error("OpenRouter API key not configured")
            return {
                "success": False,
                "error": "OpenRouter API key not configured",
                "answer": "Please configure your OpenRouter API key to use the RAG functionality."
            }
        
        try:
            # Prepare context from chunks with document source information
            context_texts = []
            document_sources = set()
            
            for i, chunk in enumerate(context_chunks, 1):
                metadata = chunk.get('metadata', {})
                text = metadata.get('text', '')
                chunk_idx = metadata.get('chunk_index', i)
                filename = metadata.get('filename', 'Unknown')
                
                document_sources.add(filename)
                context_texts.append(f"[Document: {filename} - Chunk {chunk_idx}]: {text}")
            
            context = "\n\n".join(context_texts)
            
            # Enhanced professor system prompt for multi-document course analysis
            system_prompt = f"""You are an expert professor conducting a comprehensive lecture analysis using multiple course materials. 
You have access to excerpts from {len(document_sources)} course documents: {', '.join(document_sources)}.

As an academic educator, provide scholarly responses using ONLY the provided course material excerpts:

- For student questions, deliver thorough pedagogical explanations that synthesize knowledge across all relevant sources
- For learning topics, provide comprehensive academic analysis that integrates multiple perspectives
- When concepts appear across multiple documents, highlight the scholarly consensus or complementary viewpoints
- When documents present different theoretical approaches, explain the academic discourse and help students understand various schools of thought
- Always cite specific documents and chunks (e.g., "As discussed in lecture1.pdf, Chunk 2..." or "Building on the framework in textbook.docx, Chunk 1...")
- When sources present conflicting information, guide students through the academic debate and help them develop critical thinking skills
- If course materials lack sufficient depth, suggest what additional academic resources would enhance understanding
- Focus on fostering deep learning by connecting concepts across sources and relating them to broader educational objectives"""
            
            # Determine if input is likely a question
            is_question = user_input.strip().endswith('?') or any(
                user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did']
            )
            
            if is_question:
                user_prompt = f"""Student Question: {user_input}

Course Material Excerpts from Multiple Sources:
{context}

As an expert professor, provide a comprehensive educational response that synthesizes knowledge from the multiple course documents above. Help the student understand this concept by drawing connections between sources, citing specific documents and chunks. When sources complement each other, show how they build a complete picture. When they present different perspectives, guide the student through the academic discourse to develop critical thinking."""
            else:
                user_prompt = f"""Learning Topic for Analysis: {user_input}

Course Material Excerpts from Multiple Sources:
{context}

As an expert professor, provide a thorough academic analysis of this topic by integrating insights from the multiple course documents above. Offer comprehensive educational perspectives that help students understand key concepts, theoretical frameworks, and scholarly debates. Cite specific documents and chunks, and demonstrate how different sources contribute to a holistic understanding of the topic."""
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": self.settings.TEMPERATURE,
                "max_tokens": 1500  # Increased for multi-document responses
            }
            
            # Make API request
            logger.info(f"Making API request to {self.base_url}/chat/completions")
            logger.info(f"Using model: {self.model}")
            logger.info(f"Context includes {len(document_sources)} documents")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=75
            )
            
            logger.info(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                logger.info(f"API response received, answer length: {len(answer)}")
                
                return {
                    "success": True,
                    "answer": answer,
                    "usage": result.get('usage', {}),
                    "model": self.model
                }
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "answer": "Sorry, I encountered an error while generating the response."
                }
                
        except Exception as e:
            error_msg = f"Error generating course response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "answer": "Sorry, I encountered an error while processing your request."
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the status of all RAG service components."""
        return {
            "embedding_service": {
                "available": self.embedding_service.is_available(),
                "model_info": self.embedding_service.get_model_info()
            },
            "vector_store": {
                "available": self.vector_store.is_available(),
                "stats": self.vector_store.get_stats()
            },
            "llm_service": {
                "configured": self.is_configured(),
                "model": self.model,
                "base_url": self.base_url
            }
        }
    
    def generate_document_notes(self, document_chunks: List[Dict[str, Any]], document_filename: str) -> Dict[str, Any]:
        """Generate AI study notes for a document."""
        try:
            logger.info(f"Generating AI notes for document: {document_filename}")
            
            if not self.is_configured():
                logger.error("RAG service not configured")
                return {
                    "success": False,
                    "error": "AI service not configured. Please check OpenRouter API key."
                }
            
            if not document_chunks:
                logger.warning("No document chunks provided for notes generation")
                return {
                    "success": False,
                    "error": "No content available to generate notes from."
                }
            
            # Combine chunks into full document content
            full_content = "\n\n".join([chunk.get('content', '') for chunk in document_chunks])
            
            # Create a comprehensive prompt for notes generation
            notes_prompt = f"""You are an expert educational assistant. Generate comprehensive, well-structured study notes from the following document content.

Document: {document_filename}

Please create study notes that include:
1. **Main Topics & Key Concepts** - Identify and explain the primary subjects covered
2. **Important Definitions** - Define key terms and concepts
3. **Key Points & Facts** - Highlight crucial information and facts
4. **Summary** - Provide a concise overview of the main ideas
5. **Study Questions** - Suggest 3-5 review questions to test understanding

Format your response in clear markdown with appropriate headers, bullet points, and emphasis. Make the notes comprehensive but concise, suitable for studying and review.

Document Content:
{full_content[:8000]}

Generate comprehensive study notes:"""

            # Make API call to generate notes
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": self.settings.APP_URL,
                "X-Title": "LectureAI Notes Generator"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": notes_prompt
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent notes
                "max_tokens": 2000,
                "stream": False
            }
            
            logger.info(f"Making API call to generate notes...")
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    notes_content = response_data['choices'][0]['message']['content']
                    
                    logger.info(f"Successfully generated notes for {document_filename}")
                    return {
                        "success": True,
                        "notes": notes_content,
                        "model_used": self.model
                    }
                else:
                    logger.error("Invalid response format from API")
                    return {
                        "success": False,
                        "error": "Invalid response from AI service"
                    }
            else:
                error_msg = f"API request failed with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": f"AI service error: {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during notes generation: {str(e)}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error during notes generation: {str(e)}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }