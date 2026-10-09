  
import asyncio
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from uuid import UUID

from src.core.config import settings
from src.core.constants import ALLOWED_FILE_EXTENSIONS
from src.core.exceptions import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)


class FileStorage:
    """Secure, startup-scoped asynchronous file storage."""

    def __init__(
        self,
        base_path: str | Path,
        max_file_size_bytes: int,
        allowed_extensions: frozenset = ALLOWED_FILE_EXTENSIONS,
    ) -> None:
        if max_file_size_bytes <= 0:
            raise ValueError("Maximum file size must be positive.")

        self.base_path = Path(base_path).resolve()
        self.max_file_size_bytes = max_file_size_bytes
        self.allowed_extensions = frozenset(
            ext.lower() for ext in allowed_extensions
        )

    @staticmethod
    def _validate_uuid(value: str, field_name: str) -> str:
        """Accept valid UUIDs and return their canonical representation."""
        try:
            return str(UUID(str(value)))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"Invalid {field_name}.") from exc

    def _resolve_contained_path(self, relative_path: str) -> Path:
        """Resolve an untrusted relative reference inside the storage root."""
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("Storage reference must be a non-empty string.")

        # References always use POSIX separators, regardless of OS.
        if "\\" in relative_path:
            raise ValueError("Invalid storage reference separators.")

        reference = PurePosixPath(relative_path)

        if reference.is_absolute() or len(reference.parts) != 2:
            raise ValueError("Invalid storage reference.")

        if any(part in {"", ".", ".."} for part in reference.parts):
            raise ValueError("Invalid storage reference.")

        startup_id = self._validate_uuid(
            reference.parts[0], "startup ID"
        )
        filename = reference.parts[1]
        document_name = Path(filename).stem
        extension = Path(filename).suffix.lower()

        self._validate_uuid(document_name, "document ID")

        if extension not in self.allowed_extensions:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension: {extension or '(none)'}"
            )

        candidate = (
            self.base_path / startup_id / filename
        ).resolve()

        if not candidate.is_relative_to(self.base_path):
            raise ValueError("Storage reference escapes the storage directory.")

        return candidate

    def _store_sync(
        self,
        startup_id: str,
        document_id: str,
        original_filename: str,
        content: bytes,
    ) -> str:
        startup_id = self._validate_uuid(startup_id, "startup ID")
        document_id = self._validate_uuid(document_id, "document ID")

        if not isinstance(original_filename, str) or not original_filename:
            raise ValueError("Original filename must be non-empty.")

        # Reject both Windows and POSIX path separators in user filenames.
        if "/" in original_filename or "\\" in original_filename:
            raise ValueError("Pass a filename, not a filesystem path.")

        extension = Path(original_filename).suffix.lower()

        # Validation order: extension, size, path, then filesystem changes.
        if extension not in self.allowed_extensions:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension: {extension or '(none)'}"
            )

        if not isinstance(content, bytes):
            raise TypeError("File content must be bytes.")

        if len(content) > self.max_file_size_bytes:
            raise FileTooLargeError(
                f"File exceeds the {self.max_file_size_bytes}-byte limit."
            )

        relative_reference = PurePosixPath(
            startup_id, f"{document_id}{extension}"
        ).as_posix()

        destination = self._resolve_contained_path(relative_reference)

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = None

        try:
            # Temporary file in the destination directory enables atomic replace.
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".upload-",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, destination)
            temporary_path = None

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

        return relative_reference

    async def store(
        self,
        startup_id: str,
        document_id: str,
        original_filename: str,
        content: bytes,
    ) -> str:
        """Store bytes and return a relative storage reference."""
        return await asyncio.to_thread(
            self._store_sync,
            startup_id,
            document_id,
            original_filename,
            content,
        )

    def _retrieve_sync(self, storage_reference: str) -> bytes:
        path = self._resolve_contained_path(storage_reference)

        if not path.is_file():
            raise FileNotFoundError("Stored file does not exist.")

        return path.read_bytes()

    async def retrieve(self, storage_reference: str) -> bytes:
        """Retrieve a file using an untrusted relative reference."""
        return await asyncio.to_thread(
            self._retrieve_sync, storage_reference
        )

    def _delete_sync(self, storage_reference: str) -> None:
        path = self._resolve_contained_path(storage_reference)

        # Idempotent when the file has already been removed.
        path.unlink(missing_ok=True)

    async def delete(self, storage_reference: str) -> None:
        """Delete a stored file; missing files are ignored."""
        await asyncio.to_thread(self._delete_sync, storage_reference)

    def _delete_startup_sync(self, startup_id: str) -> None:
        startup_id = self._validate_uuid(startup_id, "startup ID")
        startup_directory = (
            self.base_path / startup_id
        ).resolve()

        if not startup_directory.is_relative_to(self.base_path):
            raise ValueError("Startup directory escapes the storage root.")

        if startup_directory == self.base_path:
            raise ValueError("Refusing to delete the storage root.")

        if startup_directory.exists():
            if startup_directory.is_symlink():
                raise ValueError("Refusing to delete a symlinked startup directory.")

            shutil.rmtree(startup_directory)

    async def delete_startup_files(self, startup_id: str) -> None:
        """Remove all stored files for one startup."""
        await asyncio.to_thread(
            self._delete_startup_sync, startup_id
        )


def create_file_storage() -> FileStorage:
    """Construct the storage service from Phase 6 settings."""
    return FileStorage(
        base_path=settings.file_storage_path,
        max_file_size_bytes=settings.max_file_size_bytes,
        allowed_extensions=ALLOWED_FILE_EXTENSIONS,
    )



if __name__ == "__main__":
    import asyncio
    import tempfile
    from pathlib import Path
    from uuid import uuid4

    async def test_file_storage():
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = FileStorage(
                base_path=Path(temp_dir),
                max_file_size_bytes=1024,
            )

            startup_id = str(uuid4())
            document_id = str(uuid4())
            content = b"FileStorage smoke test"

            # Test 1: Store
            reference = await storage.store(
                startup_id,
                document_id,
                "test.txt",
                content,
            )
            assert not Path(reference).is_absolute()
            print("PASS: Store returns a relative reference")

            # Test 2: Retrieve
            retrieved = await storage.retrieve(reference)
            assert retrieved == content
            print("PASS: Retrieve returns identical bytes")

            # Test 3: Unsupported extension
            try:
                await storage.store(
                    startup_id,
                    str(uuid4()),
                    "malicious.exe",
                    b"invalid",
                )
                raise AssertionError("Unsupported extension was accepted")
            except UnsupportedFileTypeError:
                print("PASS: Unsupported extension rejected")

            # Test 4: Oversized content
            try:
                await storage.store(
                    startup_id,
                    str(uuid4()),
                    "large.txt",
                    b"x" * 1025,
                )
                raise AssertionError("Oversized file was accepted")
            except FileTooLargeError:
                print("PASS: Oversized file rejected")

            # Test 5: Path traversal
            try:
                await storage.retrieve("../../secret.txt")
                raise AssertionError("Traversal reference was accepted")
            except ValueError:
                print("PASS: Path traversal rejected")

            # Test 6: Idempotent deletion
            await storage.delete(reference)
            await storage.delete(reference)
            assert not (Path(temp_dir) / startup_id / f"{document_id}.txt").exists()
            print("PASS: Repeated deletion is safe")

            # Test 7: Startup cleanup
            await storage.store(
                startup_id,
                str(uuid4()),
                "cleanup.txt",
                b"cleanup",
            )
            await storage.delete_startup_files(startup_id)
            assert not (Path(temp_dir) / startup_id).exists()
            print("PASS: Startup directory removed")

    asyncio.run(test_file_storage())
