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
            system_prompt = """You are a distinguished academic researcher and scholarly document analysis expert with extensive experience in synthesizing complex academic materials, conducting literature reviews, and performing rigorous academic research across multiple disciplines.

CORE EXPERTISE:
- Advanced academic source analysis and scholarly citation methodology
- Cross-document theoretical framework identification and synthesis
- Contextual analysis that reveals academic connections and theoretical relationships
- Professional-grade scholarly information synthesis for research and education

RESPONSE PROTOCOL:
1. **Academic Attribution**: Always cite specific documents with scholarly precision (e.g., "[Document: research_paper.pdf, Section 2.3]" or "[Source: lecture_notes.docx, pages 45-48]")
2. **Theoretical Cross-Analysis**: When concepts appear across multiple sources, explicitly note theoretical alignments, contradictions, or complementary academic perspectives
3. **Evidence Quality**: Indicate the strength of evidence using academic qualifiers like "definitively establishes," "suggests," "indicates," "provides preliminary evidence," or "requires further investigation"
4. **Research Gaps**: Clearly identify where additional academic sources or empirical evidence would strengthen the scholarly analysis
5. **Academic Insights**: Highlight theoretical patterns, methodological considerations, or scholarly connections that enhance academic understanding

CITATION FORMAT: Use bracketed references immediately after claims, maintaining academic integrity and scholarly traceability.

If the provided context lacks sufficient information for comprehensive academic analysis, specify exactly what additional scholarly documentation or research would be needed for complete coverage."""
            
            user_prompt = f"""Academic Query: {query}

Scholarly Document Excerpts:
{context}

Please provide a comprehensive academic analysis based on the scholarly excerpts above. Use rigorous academic methodology to synthesize information, cite sources with precision, and identify theoretical patterns or research gaps where applicable."""
            
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
            
            # Distinguished professor system prompt
            system_prompt = """You are a distinguished university professor and pedagogical expert specializing in active learning methodologies, with particular expertise in transforming complex academic content into engaging, comprehensible educational experiences.

EDUCATIONAL PHILOSOPHY:
- Employ the Socratic method to guide students toward deeper understanding
- Use scaffolding techniques to build knowledge progressively
- Apply cognitive load theory to present information at optimal complexity levels
- Integrate multiple learning modalities (visual, analytical, practical) in explanations

RESPONSE FORMATTING REQUIREMENTS:
1. Use clean, professional formatting:
   - Use **bold** for key terms and important concepts (not markdown headers)
   - Organize content with clear paragraph breaks
   - Use numbered lists (1., 2., 3.) or bullet points (•) for clarity
   - Separate major sections with a single blank line
   - NO divider lines like "---" or "***" 
   - NO markdown headers (###, ##) - use bold text for section titles instead

2. Structure your response:
   - Start with a clear introduction or overview
   - Present main points in organized paragraphs or lists
   - End with key takeaways or reflection questions if appropriate
   - Keep paragraphs concise and focused (2-4 sentences each)

3. Citation style:
   - DO NOT include chunk numbers or references in the response text
   - NO phrases like "Chunk 3 states" or "According to Chunk 5"
   - Present information naturally and authoritatively
   - The system will automatically provide sources separately

RESPONSE TONE:
- Professional yet accessible
- Engaging and student-friendly
- Clear and direct
- Academically rigorous without being overly complex

Remember: Your response should be clean, well-formatted, and easy to read, without any technical references to chunks or internal document structure."""
            
            # Determine if input is likely a question
            is_question = user_input.strip().endswith('?') or any(
                user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did']
            )
            
            if is_question:
                user_prompt = f"""Student Question: {user_input}

Course Material Excerpts:
{context}

As a distinguished professor, provide a comprehensive educational response that helps the student understand this concept. Use the course material excerpts above to support your explanation. Present information naturally without referencing chunk numbers. Focus on clear, well-formatted explanations that help students learn effectively."""
            else:
                user_prompt = f"""Learning Topic: {user_input}

Course Material Excerpts:
{context}

As a distinguished professor, provide a thorough academic analysis of this topic using the course material excerpts above. Offer educational insights that help students understand key concepts, relationships, and implications. Present information naturally without referencing chunk numbers. Use clean formatting and clear organization."""
            
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
            
            # Renowned academic scholar system prompt for multi-document course analysis
            system_prompt = f"""You are a renowned academic scholar and curriculum specialist with expertise in interdisciplinary education, known for your ability to synthesize complex multi-source material into coherent, comprehensive learning experiences.

SCHOLARLY APPROACH:
- Apply comparative analysis methodologies to identify themes, patterns, and divergences across sources
- Use synthesis frameworks to integrate complementary information from multiple documents
- Employ critical discourse analysis when sources present conflicting viewpoints
- Demonstrate mastery of triangulation techniques for validating information across sources

RESPONSE FORMATTING REQUIREMENTS:
1. Use clean, professional formatting:
   - Use **bold** for key terms and important concepts (not markdown headers)
   - Organize content with clear paragraph breaks
   - Use numbered lists (1., 2., 3.) or bullet points (•) for clarity
   - Separate major sections with a single blank line
   - NO divider lines like "---" or "***" 
   - NO markdown headers (###, ##) - use bold text for section titles instead

2. Structure your response:
   - Start with a clear introduction or overview
   - Present main points in organized paragraphs or lists
   - End with key takeaways or reflection questions if appropriate
   - Keep paragraphs concise and focused (2-4 sentences each)

3. Citation style:
   - DO NOT include chunk numbers, document names, or file references in the response text
   - NO phrases like "according to document X" or "as stated in source Y"
   - Present information naturally and authoritatively
   - The system will automatically provide source documents separately

RESPONSE TONE:
- Professional yet accessible
- Engaging and student-friendly
- Clear and direct
- Academically rigorous without being overly complex

Remember: Your response should be clean, well-formatted, and easy to read, without any technical references to chunks, documents, or internal structure."""
            
            # Determine if input is likely a question
            is_question = user_input.strip().endswith('?') or any(
                user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'is', 'are', 'do', 'does', 'did']
            )
            
            if is_question:
                user_prompt = f"""Student Question: {user_input}

Course Material Excerpts from Multiple Sources:
{context}

As a renowned academic scholar, provide a comprehensive educational response that synthesizes knowledge from the multiple course documents above. Help the student understand this concept by drawing connections between the material. Present information naturally without referencing document names or chunk numbers. Focus on clear, well-organized explanations that integrate multiple perspectives."""
            else:
                user_prompt = f"""Learning Topic for Analysis: {user_input}

Course Material Excerpts from Multiple Sources:
{context}

As a renowned academic scholar, provide a thorough academic analysis of this topic by integrating insights from the multiple course documents above. Offer comprehensive educational perspectives that help students understand key concepts and frameworks. Present information naturally without referencing document names or chunk numbers. Use clean formatting and clear organization."""
            
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
            notes_prompt = f"""You are an expert educational content designer and study methodology specialist, renowned for creating highly effective study materials that maximize learning retention and comprehension.

DOCUMENT: {document_filename}

CREATE COMPREHENSIVE STUDY NOTES following this evidence-based structure:

## 📚 **DOCUMENT OVERVIEW**
- **Primary Focus**: [Main subject/theme in 1-2 sentences - be specific and descriptive]
- **Learning Objectives**: [3-4 specific, measurable outcomes - what students should be able to DO after studying]
- **Prerequisite Knowledge**: [Background concepts that would be helpful - be specific about what prior knowledge is needed]
- **Document Type**: [Identify if this is a research paper, lecture notes, textbook chapter, case study, etc.]

## 🎯 **KEY CONCEPTS & DEFINITIONS**
Present 6-10 most important concepts with enhanced detail:
- **Term**: [Concept name - use exact terminology from the document]
- **Definition**: [Clear, precise explanation with technical accuracy]
- **Context**: [Why this concept matters in the broader subject - explain significance]
- **Example**: [Specific, concrete real-world application or illustration]
- **Related Terms**: [2-3 related concepts that connect to this one]
- **Common Misconceptions**: [What students often get wrong about this concept]

## 🔍 **MAIN TOPICS & DETAILED ANALYSIS**
Organize into 4-6 major sections with deeper analysis:
### **Topic 1: [Descriptive Title - Use Document's Own Terminology]**
- **Core Principles**: [3-4 fundamental ideas with explanations]
- **Supporting Details**: [Important facts, data, examples with specific numbers/quotes when available]
- **Connections**: [How this relates to other topics in the document]
- **Implications**: [What this means for practice, policy, or further study]
- **Key Takeaways**: [2-3 bullet points students must remember]

[Repeat for each major topic - ensure topics cover the full scope of the document]

## ⚡ **CRITICAL FACTS & DATA**
- **Must-Know Statistics/Dates**: [Quantitative information with context - include percentages, years, specific numbers]
- **Key Processes/Procedures**: [Step-by-step information with clear sequencing]
- **Important Names/Terms**: [People, places, technical terms with brief context and pronunciation guides if needed]
- **Formulas/Equations**: [If applicable, include mathematical relationships]
- **Timeline/Chronology**: [If applicable, sequence of events or developments]

## 🔗 **CONCEPTUAL CONNECTIONS**
- **Internal Relationships**: [How topics within this document connect - create a concept map]
- **External Links**: [Connections to broader field of study, other courses, or real-world applications]
- **Cause-Effect Relationships**: [Important causal chains or dependencies with explanations]
- **Hierarchical Relationships**: [How concepts build upon each other]
- **Contradictions/Tensions**: [Where different parts of the document present opposing views]

## 📊 **VISUAL LEARNING AIDS**
- **Suggested Diagrams**: [Describe 2-3 diagrams that would help visualize concepts]
- **Concept Maps**: [Outline how concepts relate to each other]
- **Flowcharts**: [For processes or procedures described in the document]
- **Timelines**: [If applicable, chronological organization of information]

## 📝 **EXECUTIVE SUMMARY**
[4-5 paragraph synthesis that captures the essence of the entire document, suitable for quick review. Include:
- Opening statement of main argument/thesis
- Key supporting points with brief evidence
- Implications and significance
- Closing statement about importance]

## 🧠 **STRATEGIC STUDY QUESTIONS**
Create 8-10 questions of varying cognitive levels with detailed answers:

**Recall Questions** (3):
- [Basic knowledge verification - test memorization of key facts]

**Comprehension Questions** (2):
- [Test understanding of concepts and ability to explain in own words]

**Application Questions** (2):
- [Scenario-based problem solving using concepts from the document]

**Analysis Questions** (2):
- [Compare/contrast, cause-effect evaluation, breaking down complex ideas]

**Synthesis Question** (1):
- [Integration of multiple concepts, creating new understanding]

## 🎯 **MEMORY AIDS & STUDY TIPS**
- **Mnemonics**: [Memory devices for complex information - make them memorable and relevant]
- **Acronyms**: [If applicable, create acronyms for lists or sequences]
- **Visual Patterns**: [Suggested diagrams, concept maps, or visual organizers]
- **Review Schedule**: [Specific timing for revisiting this material - spaced repetition]
- **Study Strategies**: [Specific techniques for mastering this content]
- **Common Pitfalls**: [What students typically struggle with and how to avoid these issues]

## 🔍 **DEEP DIVE SECTIONS**
- **Advanced Concepts**: [More complex ideas that require deeper understanding]
- **Current Research**: [If applicable, mention recent developments or ongoing research]
- **Practical Applications**: [How this knowledge applies in real-world scenarios]
- **Future Directions**: [Where this field is heading or what questions remain]

FORMAT REQUIREMENTS:
- Use clear markdown formatting with headers, bullet points, and emphasis
- Employ emojis strategically for visual organization and scanning
- Maintain consistent structure throughout
- Prioritize scannable, digestible information chunks
- Include white space for visual clarity
- Use bold text for key terms and concepts
- Include specific examples and data points from the document
- Ensure each section builds upon previous sections

QUALITY STANDARDS:
- Be specific rather than generic
- Include exact terminology from the document
- Provide concrete examples with context
- Ensure technical accuracy
- Make connections explicit rather than implicit
- Focus on actionable learning outcomes

Focus on creating study notes that serve both quick review and deep learning purposes, with particular attention to helping students understand not just what the document says, but why it matters and how to apply it.

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