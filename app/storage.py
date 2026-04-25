from __future__ import annotations

import shutil
from pathlib import Path
from urllib.parse import urlparse


class StorageAdapter:
    def download(self, uri: str, destination: Path) -> Path:
        raise NotImplementedError

    def upload(self, source: Path, uri: str) -> str:
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):
    def download(self, uri: str, destination: Path) -> Path:
        source = _local_path(uri)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    def upload(self, source: Path, uri: str) -> str:
        destination = _local_path(uri)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return str(destination)


class S3StorageAdapter(StorageAdapter):
    def __init__(self, region: str = "us-east-1") -> None:
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 storage") from exc

        self.client = boto3.client("s3", region_name=region)

    def download(self, uri: str, destination: Path) -> Path:
        parsed = urlparse(uri)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(parsed.netloc, parsed.path.lstrip("/"), str(destination))
        return destination

    def upload(self, source: Path, uri: str) -> str:
        parsed = urlparse(uri)
        self.client.upload_file(str(source), parsed.netloc, parsed.path.lstrip("/"))
        return uri


def adapter_for_uri(uri: str, *, region: str = "us-east-1") -> StorageAdapter:
    if uri.startswith("s3://"):
        return S3StorageAdapter(region=region)
    return LocalStorageAdapter()


def _local_path(uri: str) -> Path:
    if uri.startswith("file://"):
        return Path(urlparse(uri).path)
    return Path(uri)
