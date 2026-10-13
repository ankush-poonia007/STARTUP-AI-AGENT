
import pytest
from uuid import uuid4

from src.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from src.infrastructure.storage.file_storage import FileStorage


@pytest.fixture
def storage(tmp_path):
    return FileStorage(
        base_path=tmp_path / "uploads",
        max_file_size_bytes=16,
        allowed_extensions=frozenset({".pdf", ".txt"}),
    )


@pytest.mark.asyncio
async def test_store_and_retrieve_preserves_bytes(storage):
    startup_id = str(uuid4())
    document_id = str(uuid4())
    content = b"document bytes"

    reference = await storage.store(
        startup_id, document_id, "report.pdf", content
    )

    assert await storage.retrieve(reference) == content


@pytest.mark.asyncio
async def test_rejects_unsupported_extension_before_writing(storage):
    with pytest.raises(UnsupportedFileTypeError):
        await storage.store(
            str(uuid4()), str(uuid4()), "report.exe", b"content"
        )

    assert not storage.base_path.exists()


@pytest.mark.asyncio
async def test_rejects_oversized_content_before_writing(storage):
    with pytest.raises(FileTooLargeError):
        await storage.store(
            str(uuid4()), str(uuid4()), "report.pdf", b"x" * 17
        )

    assert not storage.base_path.exists()


@pytest.mark.asyncio
async def test_delete_is_idempotent(storage):
    startup_id = str(uuid4())
    reference = await storage.store(
        startup_id, str(uuid4()), "report.txt", b"content"
    )

    await storage.delete(reference)
    await storage.delete(reference)


@pytest.mark.asyncio
async def test_delete_startup_only_removes_its_own_files(storage):
    startup_a = str(uuid4())
    startup_b = str(uuid4())

    reference_a = await storage.store(
        startup_a, str(uuid4()), "a.txt", b"startup A"
    )
    reference_b = await storage.store(
        startup_b, str(uuid4()), "b.txt", b"startup B"
    )

    await storage.delete_startup_files(startup_a)

    with pytest.raises(FileNotFoundError):
        await storage.retrieve(reference_a)

    assert await storage.retrieve(reference_b) == b"startup B"


def test_rejects_symlinked_startup_directory_for_deletion(storage, tmp_path):
    startup_id = str(uuid4())
    outside = tmp_path / "outside"
    outside.mkdir()

    (outside / "important.txt").write_bytes(b"keep me")
    storage.base_path.mkdir(parents=True)
    link = storage.base_path / startup_id

    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")

    with pytest.raises(ValueError, match="symlinked startup directory"):
        storage._delete_startup_sync(startup_id)

    assert (outside / "important.txt").read_bytes() == b"keep me"


def test_rejects_symlinked_startup_directory_for_storage(storage, tmp_path):
    startup_id = str(uuid4())
    outside = tmp_path / "outside"
    outside.mkdir()

    storage.base_path.mkdir(parents=True)
    link = storage.base_path / startup_id

    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")

    with pytest.raises(ValueError, match="symlinked startup directory"):
        storage._store_sync(
            startup_id, str(uuid4()), "report.txt", b"content"
        )

    assert list(outside.iterdir()) == []


@pytest.mark.asyncio
async def test_hostile_filename_cannot_escape_storage_directory(storage, tmp_path):
    startup_id = str(uuid4())
    document_id = str(uuid4())

    reference = await storage.store(
        startup_id,
        document_id,
        r"..\..\outside\malicious.pdf",
        b"safe content",
    )

    assert reference == f"{startup_id}/{document_id}.pdf"
    assert await storage.retrieve(reference) == b"safe content"
    assert not (tmp_path / "outside" / "malicious.pdf").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reference",
    [
        "../outside.txt",
        r"..\outside.txt",
        "/outside.txt",
        "not-a-uuid/document.txt",
        f"{uuid4()}/../outside.txt",
        f"{uuid4()}/{uuid4()}.exe",
    ],
)
async def test_tampered_storage_reference_is_rejected(storage, reference):
    with pytest.raises((ValueError, UnsupportedFileTypeError)):
        await storage.retrieve(reference)
        