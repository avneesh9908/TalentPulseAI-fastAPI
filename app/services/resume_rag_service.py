import base64
import io
import importlib
import re
from typing import Any, Dict, List, Tuple

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.resume import ResumeChunk, ResumeDocument
from app.schemas.resume_rag_schema import ContextRetrieveRequest, ResumeIndexRequest


def _resolve_pgvector_class():
    """
    Resolve PGVector from whichever LangChain package is installed.
    Avoids hard import errors in environments where only one package exists.
    """
    try:
        module = importlib.import_module("langchain_postgres")
        return module.PGVector
    except ModuleNotFoundError:
        pass

    try:
        module = importlib.import_module("langchain_community.vectorstores")
        return module.PGVector
    except ModuleNotFoundError as err:
        raise ModuleNotFoundError(
            "PGVector backend is missing. Install one of: "
            "'langchain-postgres' (preferred) or 'langchain-community'."
        ) from err


PGVector = _resolve_pgvector_class()


class ResumeRAGService:
    def __init__(self) -> None:
        self.collection_name = settings.RAG_COLLECTION
        self.cursor_api_key = settings.CURSOR_API_KEY
        self.cursor_api_base = settings.CURSOR_API_BASE_URL
        self.embedding_model = settings.CURSOR_EMBEDDING_MODEL
        self.vector_db_url = settings.VECTOR_DATABASE_URL or settings.DATABASE_URL

        if not self.cursor_api_key:
            raise ValueError("CURSOR_API_KEY is required")

    def _extract_text_from_pdf_b64(self, base64_pdf: str) -> str:
        pdf_bytes = base64.b64decode(base64_pdf)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages: List[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()

    def _normalize_resume_text(self, payload: ResumeIndexRequest) -> str:
        if payload.resume.text and payload.resume.text.strip():
            return payload.resume.text.strip()
        if payload.resume.base64_pdf:
            extracted = self._extract_text_from_pdf_b64(payload.resume.base64_pdf)
            if extracted:
                return extracted
        raise ValueError("Resume text is empty. Provide resume.text or resume.base64_pdf")

    def _parse_sections(self, text: str) -> Dict[str, str]:
        headings = {
            "summary",
            "experience",
            "work experience",
            "projects",
            "skills",
            "education",
            "certifications",
            "achievements",
        }
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        current = "general"
        bucket: Dict[str, List[str]] = {current: []}

        for line in lines:
            key = line.lower().strip(":")
            if key in headings:
                current = key.replace(" ", "_")
                bucket.setdefault(current, [])
                continue
            bucket.setdefault(current, []).append(line)

        return {section: "\n".join(parts).strip() for section, parts in bucket.items() if parts}

    def _extract_summary(self, text: str, skills: List[str]) -> Dict:
        years_match = re.search(r"(\d+)\+?\s+years?", text.lower())
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        phone_match = re.search(r"(\+?\d[\d\-\s]{8,}\d)", text)

        return {
            "detected_years": years_match.group(1) if years_match else None,
            "detected_email": email_match.group(0) if email_match else None,
            "detected_phone": phone_match.group(0) if phone_match else None,
            "skills_from_setup": skills,
        }

    def _build_embeddings(self, model_name: str):
        return OpenAIEmbeddings(
            model=model_name,
            openai_api_key=self.cursor_api_key,
            openai_api_base=self.cursor_api_base,
        )

    def _build_vector_store(self, embeddings: OpenAIEmbeddings) -> Any:
        return PGVector(
            embeddings=embeddings,
            collection_name=self.collection_name,
            connection=self.vector_db_url,
            use_jsonb=True,
        )

    def index_resume(
        self,
        db: Session,
        user_id: int,
        payload: ResumeIndexRequest,
    ) -> Tuple[ResumeDocument, int]:
        raw_text = self._normalize_resume_text(payload)
        sections = self._parse_sections(raw_text)
        parsed_summary = self._extract_summary(raw_text, payload.skills)

        resume_doc = ResumeDocument(
            user_id=user_id,
            interview_id=payload.interview_id,
            setup_id=payload.setup_id,
            role=payload.role,
            experience=payload.experience,
            difficulty=payload.difficulty,
            skills=payload.skills,
            profile_option=payload.profile_option,
            source=payload.resume.source,
            file_name=payload.resume.file_name,
            mime_type=payload.resume.mime_type,
            raw_text=raw_text,
            parsed_sections=sections,
            parsed_summary=parsed_summary,
        )
        db.add(resume_doc)
        db.flush()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=payload.chunking.chunk_size,
            chunk_overlap=payload.chunking.chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

        docs: List[Document] = []
        rows: List[ResumeChunk] = []
        chunk_index = 0

        for section_name, section_text in sections.items():
            split_texts = splitter.split_text(section_text)
            for piece in split_texts:
                metadata = {
                    "resume_document_id": resume_doc.id,
                    "user_id": user_id,
                    "interview_id": payload.interview_id,
                    "setup_id": payload.setup_id,
                    "role": payload.role,
                    "experience": payload.experience,
                    "difficulty": payload.difficulty,
                    "skills": payload.skills,
                    "profile_option": payload.profile_option,
                    "section": section_name,
                    "chunk_index": chunk_index,
                }
                docs.append(Document(page_content=piece, metadata=metadata))
                rows.append(
                    ResumeChunk(
                        resume_document_id=resume_doc.id,
                        chunk_index=chunk_index,
                        section=section_name,
                        chunk_text=piece,
                        metadata_json=metadata,
                    )
                )
                chunk_index += 1

        db.add_all(rows)

        embed_model = payload.embedding.model or self.embedding_model
        embeddings = self._build_embeddings(embed_model)
        vector_store = self._build_vector_store(embeddings)
        vector_store.add_documents(docs)

        db.commit()
        db.refresh(resume_doc)

        return resume_doc, len(docs)

    def retrieve_context(
        self,
        db: Session,
        user_id: int,
        payload: ContextRetrieveRequest,
    ) -> List[Dict]:
        enriched_query = (
            f"Role={payload.role}; Experience={payload.experience}; Difficulty={payload.difficulty}; "
            f"Skills={', '.join(payload.skills)}; ProfileOption={payload.profile_option}; "
            f"Question={payload.query}"
        )

        embeddings = self._build_embeddings(self.embedding_model)
        vector_store = self._build_vector_store(embeddings)

        matches = vector_store.similarity_search_with_score(
            enriched_query,
            k=payload.top_k,
            filter={
                "user_id": user_id,
                "interview_id": payload.interview_id,
                "setup_id": payload.setup_id,
            },
        )

        context_pack: List[Dict] = []
        for doc, score in matches:
            if payload.min_score is not None and score > payload.min_score:
                continue

            resume_doc_id = doc.metadata.get("resume_document_id")
            chunk_index = doc.metadata.get("chunk_index")

            chunk_row = (
                db.query(ResumeChunk)
                .filter(
                    ResumeChunk.resume_document_id == resume_doc_id,
                    ResumeChunk.chunk_index == chunk_index,
                )
                .first()
            )

            context_pack.append(
                {
                    "chunk_id": chunk_row.id if chunk_row else -1,
                    "section": doc.metadata.get("section"),
                    "score": float(score),
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                }
            )

        return context_pack
