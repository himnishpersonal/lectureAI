"""
LectureAI - Intelligent Course Assistant
AI-Powered Educational RAG System for Academic Learning
"""

import streamlit as st
import requests
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any

try:
    from streamlit_chat import message
except ImportError:
    message = None

# Page configuration
st.set_page_config(
    page_title="LectureAI - Intelligent Course Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000"
ALLOWED_FILE_TYPES = ["pdf", "docx", "txt", "mp3", "wav", "m4a", "mp4"]

def init_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'courses' not in st.session_state:
        st.session_state.courses = []
    if 'selected_course' not in st.session_state:
        st.session_state.selected_course = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Course Dashboard"

def check_api_health() -> bool:
    """Check if the API server is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=15)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# Course Management Functions
def get_courses() -> List[Dict[str, Any]]:
    """Get list of courses from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/courses", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch courses: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching courses: {str(e)}")
        return []

def create_course(name: str, description: str = "") -> Dict[str, Any]:
    """Create a new course."""
    try:
        payload = {
            "name": name,
            "description": description
        }
        response = requests.post(f"{API_BASE_URL}/courses", json=payload, timeout=10)
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Failed to create course: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_course_documents(course_id: int) -> List[Dict[str, Any]]:
    """Get documents for a specific course."""
    try:
        response = requests.get(f"{API_BASE_URL}/courses/{course_id}/documents", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch course documents: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching course documents: {str(e)}")
        return []

def upload_document_to_course(course_id: int, uploaded_file) -> Dict[str, Any]:
    """Upload a document to a specific course."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{API_BASE_URL}/courses/{course_id}/documents", files=files, timeout=30)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Upload failed: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def query_course(course_id: int, question: str) -> Dict[str, Any]:
    """Query a course using RAG."""
    try:
        payload = {
            "question": question,
            "max_results": 5
        }
        
        response = requests.post(
            f"{API_BASE_URL}/courses/{course_id}/query", 
            json=payload, 
            timeout=75
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def generate_ai_notes(document_id: int) -> Dict[str, Any]:
    """Generate AI notes for a document."""
    try:
        response = requests.post(f"{API_BASE_URL}/documents/{document_id}/generate-notes", timeout=60)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_ai_notes(document_id: int) -> Dict[str, Any]:
    """Get AI notes for a document."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}/notes", timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_document_chunks(document_id: int) -> Dict[str, Any]:
    """Get document chunks for viewing original content."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}/chunks", timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_transcription_status(document_id: int) -> Dict[str, Any]:
    """Get transcription status for an audio document."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}/transcription-status", timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def get_transcript(document_id: int) -> Dict[str, Any]:
    """Get transcript for an audio document."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents/{document_id}/transcript", timeout=10)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def delete_document(document_id: int) -> Dict[str, Any]:
    """Delete a document and all associated data."""
    try:
        response = requests.delete(f"{API_BASE_URL}/documents/{document_id}", timeout=30)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

def render_document_card(doc: Dict[str, Any], course_id: int):
    """Render an individual document card with AI notes functionality."""
    # Create a unique key for this document's expander
    doc_key = f"doc_{doc['id']}"
    
    # Determine if this is an audio file
    is_audio = doc.get('is_audio') == "true" or doc.get('file_type', '').lower() in ['.mp3', '.wav', '.m4a', '.mp4']
    
    # Status icon based on file type and processing status
    if is_audio:
        # Audio file status
        transcription_status = doc.get('transcription_status', 'pending')
        if transcription_status == "completed":
            status_icon = "🎵"
            status_text = "Transcribed"
        elif transcription_status == "processing":
            status_icon = "⏳"
            status_text = "Transcribing"
        elif transcription_status == "failed":
            status_icon = "❌"
            status_text = "Failed"
        else:
            status_icon = "🎤"
            status_text = "Pending"
    else:
        # Document file status
        if doc['processed'] == "completed":
            status_icon = "✅"
            status_text = "Ready"
        elif doc['processed'] == "processing":
            status_icon = "⏳"
            status_text = "Processing"
        else:
            status_icon = "❌"
            status_text = "Error"
    
    # Document card container
    with st.container():
        # Header with document info
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{status_icon} {doc['filename']}**")
        
        with col2:
            st.write(f"{doc['file_size'] / 1024:.1f} KB")
        
        with col3:
            if doc['processed'] == "completed":
                st.write(f"{doc['num_chunks']} chunks")
            else:
                st.write(status_text)
        
        with col4:
            # Create sub-columns for view and delete buttons
            view_col, delete_col = st.columns([1, 1])
            
            with view_col:
                # Expand/collapse button
                if st.button("👁️ View", key=f"view_{doc['id']}", help="View document details and AI notes"):
                    # Toggle the document viewer state
                    viewer_key = f"show_viewer_{doc['id']}"
                    if viewer_key not in st.session_state:
                        st.session_state[viewer_key] = True
                    else:
                        st.session_state[viewer_key] = not st.session_state[viewer_key]
            
            with delete_col:
                # Delete button with confirmation
                if st.button("🗑️", key=f"delete_{doc['id']}", help="Delete this document", type="secondary"):
                    # Set confirmation state
                    st.session_state[f"confirm_delete_{doc['id']}"] = True
        
        # Expandable document viewer
        if st.session_state.get(f"show_viewer_{doc['id']}", False):
            with st.expander("📄 Document Details", expanded=True):
                # Document info
                st.write(f"**File Type:** {doc.get('file_type', 'Unknown')}")
                st.write(f"**Upload Date:** {doc.get('upload_date', 'Unknown')[:10]}")
                if is_audio:
                    st.write(f"**Transcription Status:** {status_text}")
                    if doc.get('audio_duration'):
                        duration_mins = int(doc['audio_duration'] // 60)
                        duration_secs = int(doc['audio_duration'] % 60)
                        st.write(f"**Duration:** {duration_mins}:{duration_secs:02d}")
                else:
                    st.write(f"**Processing Status:** {status_text}")
                
                # Show content options based on file type and status
                if is_audio and transcription_status == "completed":
                    # Toggle between transcript and AI notes
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        view_mode = st.radio(
                            "View Mode:",
                            ["📝 Transcript", "🤖 AI Notes"],
                            key=f"view_mode_{doc['id']}",
                            horizontal=True
                        )
                    
                    with col2:
                        # AI Notes generation button
                        if st.button(f"🧠 Generate AI Notes", key=f"generate_notes_{doc['id']}"):
                            with st.spinner("🤖 Generating AI study notes..."):
                                result = generate_ai_notes(doc['id'])
                            
                            if result["success"]:
                                st.success("✅ AI notes generated successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to generate notes: {result.get('error', 'Unknown error')}")
                    
                    # Content display based on selected mode
                    if view_mode == "📝 Transcript":
                        st.subheader("📝 Lecture Transcript")
                        st.info("AI-generated transcript from your lecture audio")
                        
                        # Get and display transcript
                        transcript_result = get_transcript(doc['id'])
                        
                        if transcript_result["success"]:
                            transcript_data = transcript_result["data"]
                            transcript_text = transcript_data.get("transcript", "")
                            
                            if transcript_text:
                                # Display transcript in a nice format
                                st.markdown("### Full Transcript")
                                st.markdown(transcript_text)
                                
                                # Show transcript metadata
                                metadata = transcript_data.get("transcription_metadata", {})
                                if metadata:
                                    with st.expander("📊 Transcription Details"):
                                        st.write(f"**Language:** {metadata.get('language', 'N/A')}")
                                        st.write(f"**Duration:** {metadata.get('duration', 'N/A')} seconds")
                                        st.write(f"**Segments:** {metadata.get('segments_count', 'N/A')}")
                                        st.write(f"**Model:** {metadata.get('model_size', 'N/A')}")
                            else:
                                st.warning("No transcript available")
                        else:
                            st.error(f"Failed to load transcript: {transcript_result.get('error', 'Unknown error')}")
                    
                    elif view_mode == "📄 Original Content":
                        st.subheader("📄 Document Chunks")
                        st.info("Showing the original document content broken into searchable chunks")
                        
                        # Get and display document chunks
                        chunks_result = get_document_chunks(doc['id'])
                        
                        if chunks_result["success"]:
                            chunks_data = chunks_result["data"]
                            chunks = chunks_data.get("chunks", [])
                            
                            if chunks:
                                st.write(f"**Total chunks:** {len(chunks)}")
                                
                                # Display each chunk
                                for i, chunk in enumerate(chunks):
                                    with st.expander(f"Chunk {chunk['chunk_index'] + 1}", expanded=False):
                                        st.markdown(chunk['content'])
                                        
                                        # Show chunk metadata if available
                                        metadata = chunk.get('metadata', {})
                                        if metadata:
                                            st.caption(f"📊 Metadata: {metadata.get('estimated_tokens', 'N/A')} tokens, {metadata.get('sentence_count', 'N/A')} sentences")
                            else:
                                st.warning("No chunks available for this document")
                        else:
                            st.error(f"Failed to load document content: {chunks_result.get('error', 'Unknown error')}")
                    
                    else:  # AI Notes mode
                        st.subheader("🤖 AI-Generated Study Notes")
                        
                        # Try to get existing AI notes
                        notes_result = get_ai_notes(doc['id'])
                        
                        if notes_result["success"] and notes_result["data"]:
                            notes_data = notes_result["data"]
                            
                            # Display AI notes
                            if notes_data.get('notes'):
                                st.markdown(notes_data['notes'])
                                
                                # Show generation info
                                if notes_data.get('generated_at'):
                                    st.caption(f"Generated on: {notes_data['generated_at'][:16]}")
                            else:
                                st.info("📝 No AI notes available. Click 'Generate AI Notes' to create them!")
                        else:
                            st.info("📝 No AI notes generated yet. Click 'Generate AI Notes' above to create study notes!")
                
                elif not is_audio and doc['processed'] == "completed":
                    # Regular document processing
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        view_mode = st.radio(
                            "View Mode:",
                            ["📄 Original Content", "🤖 AI Notes"],
                            key=f"view_mode_{doc['id']}",
                            horizontal=True
                        )
                    
                    with col2:
                        # AI Notes generation button
                        if st.button(f"🧠 Generate AI Notes", key=f"generate_notes_{doc['id']}"):
                            with st.spinner("🤖 Generating AI study notes..."):
                                result = generate_ai_notes(doc['id'])
                            
                            if result["success"]:
                                st.success("✅ AI notes generated successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to generate notes: {result.get('error', 'Unknown error')}")
                    
                    # Content display for regular documents
                    if view_mode == "📄 Original Content":
                        st.subheader("📄 Document Chunks")
                        st.info("Showing the original document content broken into searchable chunks")
                        
                        # Get and display document chunks
                        chunks_result = get_document_chunks(doc['id'])
                        
                        if chunks_result["success"]:
                            chunks_data = chunks_result["data"]
                            chunks = chunks_data.get("chunks", [])
                            
                            if chunks:
                                st.write(f"**Total chunks:** {len(chunks)}")
                                
                                # Display each chunk
                                for i, chunk in enumerate(chunks):
                                    with st.expander(f"Chunk {chunk['chunk_index'] + 1}", expanded=False):
                                        st.markdown(chunk['content'])
                                        
                                        # Show chunk metadata if available
                                        metadata = chunk.get('metadata', {})
                                        if metadata:
                                            st.caption(f"📊 Metadata: {metadata.get('estimated_tokens', 'N/A')} tokens, {metadata.get('sentence_count', 'N/A')} sentences")
                            else:
                                st.warning("No chunks available for this document")
                        else:
                            st.error(f"Failed to load document content: {chunks_result.get('error', 'Unknown error')}")
                    
                    else:  # AI Notes mode for documents
                        st.subheader("🤖 AI-Generated Study Notes")
                        
                        # Try to get existing AI notes
                        notes_result = get_ai_notes(doc['id'])
                        
                        if notes_result["success"] and notes_result["data"]:
                            notes_data = notes_result["data"]
                            
                            # Display AI notes
                            if notes_data.get('notes'):
                                st.markdown(notes_data['notes'])
                                
                                # Show generation info
                                if notes_data.get('generated_at'):
                                    st.caption(f"Generated on: {notes_data['generated_at'][:16]}")
                            else:
                                st.info("📝 No AI notes available. Click 'Generate AI Notes' to create them!")
                        else:
                            st.info("📝 No AI notes generated yet. Click 'Generate AI Notes' above to create study notes!")
                
                elif is_audio and transcription_status == "processing":
                    st.info("🎤 Audio is being transcribed... This may take a few minutes depending on the length.")
                    st.write("Once transcription is complete, AI notes will be automatically generated!")
                    
                    # Auto-refresh button for processing audio files
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button(f"🔄 Check Progress", key=f"refresh_processing_{doc['id']}"):
                            st.rerun()
                    with col2:
                        st.write("*Page will auto-refresh in background*")
                    
                    # Use JavaScript for auto-refresh (non-blocking)
                    st.markdown("""
                    <script>
                    setTimeout(function(){
                        window.location.reload();
                    }, 30000);
                    </script>
                    """, unsafe_allow_html=True)
                
                elif is_audio and transcription_status == "failed":
                    st.error("❌ Transcription failed. Please try uploading the audio file again.")
                
                elif is_audio and transcription_status == "pending":
                    st.info("⏳ Audio transcription is queued. Processing will begin shortly.")
                    
                    # Auto-refresh button for pending audio files
                    if st.button(f"🔄 Refresh Status", key=f"refresh_pending_{doc['id']}"):
                        st.rerun()
                    
                    # Use JavaScript for auto-refresh (non-blocking)
                    st.markdown("""
                    <script>
                    setTimeout(function(){
                        window.location.reload();
                    }, 10000);
                    </script>
                    """, unsafe_allow_html=True)
                
                else:
                    st.warning("⚠️ Document is still processing. Content will be available once processing is complete.")
        
        # Handle delete confirmation dialog
        if st.session_state.get(f"confirm_delete_{doc['id']}", False):
            st.error("⚠️ **Delete Document?**")
            st.write(f"Are you sure you want to delete **{doc['filename']}**?")
            
            if is_audio:
                st.write("This will delete:")
                st.write("• The audio file and transcript")
                st.write("• All generated chunks and embeddings") 
                st.write("• Any AI-generated notes")
            else:
                st.write("This will delete:")
                st.write("• The document file")
                st.write("• All generated chunks and embeddings")
                st.write("• Any AI-generated notes")
            
            st.warning("**This action cannot be undone!**")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("✅ Yes, Delete", key=f"confirm_yes_{doc['id']}", type="primary"):
                    # Perform deletion
                    with st.spinner("Deleting document..."):
                        result = delete_document(doc['id'])
                    
                    if result["success"]:
                        st.success(f"✅ Successfully deleted {doc['filename']}")
                        st.balloons()
                        # Clear confirmation state
                        del st.session_state[f"confirm_delete_{doc['id']}"]
                        # Force refresh by clearing cache and rerunning
                        st.cache_data.clear()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete document: {result.get('error', 'Unknown error')}")
                        # Clear confirmation state even on error
                        del st.session_state[f"confirm_delete_{doc['id']}"]
            
            with col2:
                if st.button("❌ Cancel", key=f"confirm_no_{doc['id']}", type="secondary"):
                    # Clear confirmation state
                    del st.session_state[f"confirm_delete_{doc['id']}"]
                    st.rerun()
        
        # Add some spacing between cards
        st.markdown("<br>", unsafe_allow_html=True)

def render_course_dashboard():
    """Render the course dashboard page."""
    st.title("📚 Course Dashboard")
    st.caption("Organize your learning materials and create intelligent course workspaces")
    
    # Load courses
    courses = get_courses()
    st.session_state.courses = courses
    
    # Move course selection to the top with better layout
    st.subheader("🎯 Select Course")
    
    # Course selection and creation in a more prominent position
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if courses:
            course_options = {f"{course['name']} ({course['document_count']} docs)": course for course in courses}
            selected_course_name = st.selectbox(
                "Choose your course to manage materials and generate AI notes",
                options=list(course_options.keys()),
                key="course_selector",
                help="Select a course to view documents and generate AI-powered study notes"
            )
            selected_course = course_options[selected_course_name] if selected_course_name else None
        else:
            st.info("🎓 No courses yet. Create your first course to start organizing your learning materials!")
            selected_course = None
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        if st.button("➕ New Course", use_container_width=True):
            st.session_state.show_course_form = True
    
    # Course creation form
    if st.session_state.get('show_course_form', False):
        with st.form("create_course_form"):
            st.subheader("Create New Course")
            course_name = st.text_input("Course Name", placeholder="e.g., Introduction to Machine Learning")
            course_description = st.text_area("Description (optional)", placeholder="Brief description of the course content and learning objectives...")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Create Course"):
                    if course_name.strip():
                        with st.spinner("Creating course..."):
                            result = create_course(course_name.strip(), course_description.strip())
                        
                        if result["success"]:
                            st.success(f"Course '{course_name}' created successfully!")
                            st.session_state.show_course_form = False
                            st.rerun()
                        else:
                            st.error(f"Failed to create course: {result.get('error', 'Unknown error')}")
                    else:
                        st.error("Course name is required!")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_course_form = False
                    st.rerun()
    
    # Document management for selected course
    if selected_course:
        st.session_state.selected_course = selected_course
        
        # Separator
        st.markdown("---")
        
        # Upload section with tabs
        st.subheader(f"📤 Upload Materials to '{selected_course['name']}'")
        
        upload_tab1, upload_tab2 = st.tabs(["📄 Documents", "🎤 Audio Lectures"])
        
        with upload_tab1:
            st.write("**Upload text-based materials**")
            uploaded_files = st.file_uploader(
                "Upload lecture notes, readings, textbooks, or other course materials",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="course_file_uploader",
                help="Supported formats: PDF, DOCX, TXT"
            )
        
        with upload_tab2:
            st.write("**Upload lecture audio for automatic transcription**")
            uploaded_audio = st.file_uploader(
                "Upload lecture recordings for AI transcription and note generation",
                type=["mp3", "wav", "m4a", "mp4"],
                accept_multiple_files=True,
                key="course_audio_uploader",
                help="Supported formats: MP3, WAV, M4A, MP4"
            )
        
        if uploaded_files:
            if st.button("Upload All Documents", type="primary"):
                progress_bar = st.progress(0)
                success_count = 0
                
                for i, file in enumerate(uploaded_files):
                    with st.spinner(f"Uploading {file.name}..."):
                        result = upload_document_to_course(selected_course['id'], file)
                    
                    if result["success"]:
                        success_count += 1
                        st.success(f"✅ {file.name} uploaded successfully!")
                    else:
                        st.error(f"❌ Failed to upload {file.name}: {result.get('error', 'Unknown error')}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success(f"Upload complete! {success_count}/{len(uploaded_files)} files uploaded successfully.")
                time.sleep(1)
                st.rerun()
        
        if uploaded_audio:
            if st.button("Upload All Audio Files", type="primary", key="upload_audio_btn"):
                progress_bar = st.progress(0)
                success_count = 0
                
                for i, file in enumerate(uploaded_audio):
                    with st.spinner(f"Uploading {file.name}..."):
                        result = upload_document_to_course(selected_course['id'], file)
                    
                    if result["success"]:
                        success_count += 1
                        st.success(f"🎤 {file.name} uploaded successfully! Transcription will start automatically.")
                    else:
                        st.error(f"❌ Failed to upload {file.name}: {result.get('error', 'Unknown error')}")
                    
                    progress_bar.progress((i + 1) / len(uploaded_audio))
                
                st.success(f"Audio upload complete! {success_count}/{len(uploaded_audio)} files uploaded successfully.")
                st.info("🤖 Transcription and AI notes generation will happen automatically. Check back in a few minutes!")
                time.sleep(1)
                st.rerun()
        
        # Document viewer section
        st.subheader(f"📋 Course Materials ({selected_course['document_count']} documents)")
        
        # Get documents
        documents = get_course_documents(selected_course['id'])
        
        if documents:
            # Document viewer with expandable cards
            for doc in documents:
                render_document_card(doc, selected_course['id'])
        else:
            st.info("📚 No course materials uploaded yet. Add lecture notes, readings, or textbooks above!")
    
    else:
        st.info("👆 Select a course to manage its materials, or create a new course to get started.")

def render_sidebar():
    """Render the sidebar with navigation."""
    st.sidebar.header("🎓 LectureAI")
    st.sidebar.caption("Intelligent Course Assistant")
    
    # Navigation
    st.sidebar.subheader("📚 Learning Hub")
    page = st.sidebar.radio(
        "Navigate to:",
        ["Course Dashboard", "AI Learning Assistant"],
        key="navigation",
        help="Organize your courses or chat with AI tutor"
    )
    
    st.session_state.current_page = page
    
    # Course info if selected
    if st.session_state.selected_course:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Selected Course")
        course = st.session_state.selected_course
        st.sidebar.write(f"**{course['name']}**")
        st.sidebar.write(f"📄 {course['document_count']} documents")
        if course.get('description'):
            st.sidebar.write(f"*{course['description']}*")
    

def render_course_chat():
    """Render the course-aware chat interface."""
    st.title("🤖 AI Learning Assistant")
    st.caption("Get expert explanations and insights from your course materials")
    
    # Course selection
    courses = get_courses()
    if not courses:
        st.warning("📚 No courses available. Please create a course first!")
        st.info("👈 Go to 'Course Dashboard' to create your first course and upload learning materials.")
        return
    
    # Course selection
    course_options = {f"{course['name']} ({course['document_count']} docs)": course for course in courses}
    selected_course_name = st.selectbox(
        "Select Course for AI Tutoring",
        options=list(course_options.keys()),
        key="chat_course_selector",
        help="Choose the course you'd like to study with AI assistance"
    )
    
    if not selected_course_name:
        st.info("🎯 Please select a course to start your AI-powered learning session.")
        return
    
    selected_course = course_options[selected_course_name]
    st.session_state.selected_course = selected_course
    
    # Check if course has documents
    if selected_course['document_count'] == 0:
        st.warning(f"📚 Course '{selected_course['name']}' has no learning materials yet.")
        st.info("👈 Go to 'Course Dashboard' to upload lecture notes, readings, or textbooks to this course.")
        return
    
    # Show course info
    st.success(f"🎓 Learning from **{selected_course['name']}** ({selected_course['document_count']} materials)")
    st.info("💡 Ask questions about concepts, request explanations, or explore topics from your course materials!")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for i, msg in enumerate(st.session_state.messages):
            if message:  # If streamlit-chat is available
                message(
                    msg["content"],
                    is_user=msg["is_user"],
                    key=f"message_{i}"
                )
            else:
                # Fallback without streamlit-chat
                if msg["is_user"]:
                    st.write(f"**You:** {msg['content']}")
                else:
                    st.write(f"**Assistant:** {msg['content']}")
                    
                    # Show citations if available
                    if "citations" in msg and msg["citations"]:
                        with st.expander("📚 Sources"):
                            for citation in msg["citations"]:
                                filename = citation.get('filename', 'Unknown')
                                similarity = citation.get('similarity_score', 0)
                                text_preview = citation.get('text', '')[:200] + "..."
                                st.write(f"**{filename}** (Similarity: {similarity:.2f})")
                                st.write(f"*{text_preview}*")
                                st.write("---")
    
    # Chat input
    user_input = st.chat_input("Ask a question or explore a topic from your course materials...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "content": user_input,
            "is_user": True,
            "timestamp": datetime.now()
        })
        
        # Query the course
        with st.spinner("🧠 Analyzing course materials and preparing expert explanation..."):
            result = query_course(selected_course['id'], user_input)
        
        if result.get("success", False):
            answer = result.get("answer", "No answer generated")
            citations = result.get("citations", [])
            
            # Check if input is not a question and show tip
            if not user_input.strip().endswith('?') and not any(
                user_input.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which']
            ):
                answer = "💡 **Learning Tip**: Asking specific questions helps me provide more targeted educational explanations!\n\n" + answer
            
            # Add assistant response
            st.session_state.messages.append({
                "content": answer,
                "is_user": False,
                "timestamp": datetime.now(),
                "citations": citations
            })
            
        else:
            # Add error message
            error_msg = result.get("answer", f"Error: {result.get('error', 'Unknown error')}")
            st.session_state.messages.append({
                "content": f"❌ {error_msg}",
                "is_user": False,
                "timestamp": datetime.now()
            })
        
        st.rerun()



def main():
    """Main application function."""
    init_session_state()
    
    # Render sidebar first to get navigation
    render_sidebar()
    
    # Header
    st.title("🎓 LectureAI")
    st.subheader("Your Intelligent Course Assistant")
    st.caption("AI-powered learning with expert explanations from your course materials")
    st.markdown("---")
    
    # Check API status
    if not check_api_health():
        st.error("⚠️ API server is not running. Please start it with: `uvicorn backend.api:app --reload`")
        st.stop()
    
    # Route to appropriate page based on navigation
    current_page = st.session_state.get('current_page', 'Course Dashboard')
    
    if current_page == "Course Dashboard":
        render_course_dashboard()
    elif current_page == "AI Learning Assistant":
        render_course_chat()
    else:
        # Fallback to course dashboard
        render_course_dashboard()

if __name__ == "__main__":
    main()
