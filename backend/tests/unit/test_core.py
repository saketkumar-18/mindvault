"""Unit tests for security, chunker, parsers, embeddings, vector store, LLM mock."""


import pytest
from mindvault.domain.chunker import ChunkSpec, TextChunker, chunk_document
from mindvault.embeddings.hash_embedding import HashEmbeddingProvider
from mindvault.errors import SecurityViolation, ValidationFailed
from mindvault.llm.base import LLMRequest
from mindvault.llm.mock import MockLLMProvider
from mindvault.parsers.base import Page, ParsedDocument
from mindvault.parsers.text import MarkdownParser, TextParser
from mindvault.security.files import resolve_under, sanitize_display_name, validate_upload
from mindvault.vectorstore.numpy_store import NumpyVectorStore


# -- Security tests ----------------------------------------------------------
class TestSecurity:
    def test_sanitize_display_name(self):
        assert sanitize_display_name("hello.txt") == "hello.txt"
        assert sanitize_display_name("../../etc/passwd.txt") == "passwd.txt"
        assert sanitize_display_name("CON.txt") == "_CON.txt"  # reserved word
        with pytest.raises(ValidationFailed):
            sanitize_display_name("")

    def test_validate_upload(self):
        display, ext = validate_upload("test.pdf", 1000, max_size=10000, allowed_extensions={"pdf"})
        assert ext == "pdf"
        from mindvault.errors import UnsupportedFileType

        with pytest.raises(UnsupportedFileType) as exc:
            validate_upload("test.pdf", 1000, max_size=10000, allowed_extensions={"txt"})
        assert "not supported" in str(exc.value).lower()

    def test_resolve_under(self, tmp_path):
        base = tmp_path / "data"
        base.mkdir()
        safe = base / "sub" / "file.txt"
        safe.parent.mkdir(parents=True)
        safe.write_text("ok")
        resolved = resolve_under(base, "sub", "file.txt")
        assert resolved == safe.resolve()
        with pytest.raises(SecurityViolation):
            resolve_under(base, "..", "secret.txt")


# -- Chunker tests -----------------------------------------------------------
SAMPLE_TEXT = """MindVault is a private AI knowledge assistant.

It runs entirely on your local machine.
All your data stays on your computer."""


class TestChunker:
    def test_split_text(self):
        chunker = TextChunker(ChunkSpec(size=50, overlap=10))
        pieces = chunker.split_text(SAMPLE_TEXT)
        assert len(pieces) > 0
        assert all(isinstance(p[0], int) for p in pieces)
        assert all(isinstance(p[1], str) for p in pieces)

    def test_chunk_document(self):
        doc = ParsedDocument(pages=[Page(number=1, text=SAMPLE_TEXT)])
        chunks = chunk_document(doc, ChunkSpec(size=100, overlap=20))
        assert len(chunks) > 0
        assert chunks[0].text
        assert chunks[0].ordinal == 0
        assert chunks[0].page_start == 1

    def test_heading_section(self, tmp_path):
        md_text = "# Introduction\nHello world.\n## Details\nMore text."
        f = tmp_path / "dummy.md"
        f.write_text(md_text, encoding="utf-8")
        parsed = MarkdownParser().parse(f)
        assert any(h.startswith("#") for page in parsed.pages for h in page.headings)
        # Manually construct parsed doc with headings
        doc = ParsedDocument(
            pages=[Page(number=1, text=md_text, headings=["# Introduction", "## Details"])]
        )
        chunks = chunk_document(doc, ChunkSpec(size=200, overlap=20))
        # The chunker should pick up the section from headings
        assert any(c.section and "Introduction" in c.section for c in chunks)


# -- Parser tests ------------------------------------------------------------
class TestParsers:
    def test_txt_parser(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello\nWorld", encoding="utf-8")
        doc = TextParser().parse(f)
        assert len(doc.pages) == 1
        assert "Hello" in doc.pages[0].text

    def test_md_parser(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Title\nBody text.", encoding="utf-8")
        doc = MarkdownParser().parse(f)
        assert len(doc.pages) == 1
        assert "Body" in doc.pages[0].text

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(ValidationFailed):
            TextParser().parse(f)


# -- Embedding tests ---------------------------------------------------------
class TestEmbeddings:
    def test_hash_embedding(self):
        provider = HashEmbeddingProvider(dim=384)
        vectors = provider.embed(["hello world", "test"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 384
        assert all(isinstance(v, float) for v in vectors[0])


# -- Vector store tests ------------------------------------------------------
class TestVectorStore:
    def test_numpy_store(self, tmp_path):
        store = NumpyVectorStore(tmp_path / "test.npz", dim=384)

        store.add(["id1", "id2"], [[1.0] * 384, [0.5] * 384])
        assert store.count() == 2
        hits = store.query([1.0] * 384, top_k=1)
        assert len(hits) == 1
        assert hits[0].id == "id1"

    def test_persistence(self, tmp_path):
        path = tmp_path / "persist.npz"
        store = NumpyVectorStore(path, dim=384)
        store.add(["id1"], [[1.0] * 384])
        store.save()
        store2 = NumpyVectorStore(path, dim=384)
        store2.load()
        assert store2.count() == 1
        assert store2.ids() == ["id1"]


# -- LLM mock tests ----------------------------------------------------------
class TestMockLLM:
    def test_mock_with_context(self):
        provider = MockLLMProvider()
        assert provider.available()
        prompt = (
            "Question: test\n\n<documents>\n[1] source=test.txt\nHello world\n</documents>"
        )
        req = LLMRequest(messages=[{"role": "user", "content": prompt}])
        text = "".join(provider.generate(req))
        assert "Based on the provided documents" in text
        assert "[1]" in text

    def test_mock_no_context(self):
        provider = MockLLMProvider()
        req = LLMRequest(messages=[{"role": "user", "content": "No documents here."}])
        text = "".join(provider.generate(req))
        assert "I couldn't find enough information" in text