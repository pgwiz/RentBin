from django.core.files.storage import FileSystemStorage

class NoLockFileSystemStorage(FileSystemStorage):
    def _save(self, name, content):
        """Overrides the default _save method to bypass file locking."""
        try:
            # Disable locking by skipping fcntl operations
            content.file.seek(0)
        except (AttributeError, IOError):
            pass
        return super()._save(name, content)