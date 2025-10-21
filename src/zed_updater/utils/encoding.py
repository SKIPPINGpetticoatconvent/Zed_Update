#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Encoding utilities for handling UTF-8 and cross-platform text operations
"""

import os
import sys
import locale
import chardet
from pathlib import Path
from typing import Optional, Union, Tuple


class EncodingUtils:
    """Utilities for handling text encoding across platforms"""

    @staticmethod
    def setup_utf8_environment() -> None:
        """Setup UTF-8 environment for cross-platform compatibility"""
        # Set environment variables
        os.environ['PYTHONIOENCODING'] = 'utf-8'

        # Windows specific setup
        if sys.platform == 'win32':
            try:
                # Try to set console codepage to UTF-8
                os.system('chcp 65001 > nul 2>&1')
            except:
                pass

            # Set locale to Chinese if available
            try:
                locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                except locale.Error:
                    pass

        # Configure stdout/stderr for UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
                sys.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass

    @staticmethod
    def get_system_encoding() -> str:
        """Get the system's preferred encoding"""
        try:
            return locale.getpreferredencoding()
        except:
            return 'utf-8'

    @staticmethod
    def detect_file_encoding(file_path: Union[str, Path], sample_size: int = 8192) -> str:
        """
        Detect file encoding using chardet

        Args:
            file_path: Path to the file
            sample_size: Number of bytes to sample

        Returns:
            Detected encoding string
        """
        file_path = Path(file_path)

        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)

            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')

            # Handle common encoding aliases
            if encoding:
                encoding = encoding.lower()
                if encoding in ['utf-8-sig', 'utf-8']:
                    return 'utf-8-sig' if raw_data.startswith(b'\xef\xbb\xbf') else 'utf-8'
                elif encoding in ['gbk', 'gb2312', 'cp936']:
                    return 'gbk'

            return 'utf-8'  # Default fallback

        except Exception:
            return 'utf-8'

    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: Optional[str] = None) -> Optional[str]:
        """
        Safely read text file with encoding detection

        Args:
            file_path: Path to the file
            encoding: Optional encoding override

        Returns:
            File content as string, or None if failed
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        # Detect encoding if not provided
        if encoding is None:
            encoding = EncodingUtils.detect_file_encoding(file_path)

        # Try reading with detected encoding
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Final fallback to latin-1 (lossless)
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        return f.read()
                except Exception:
                    return None
        except Exception:
            return None

    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8-sig') -> bool:
        """
        Safely write text file with UTF-8 BOM

        Args:
            file_path: Path to the file
            content: Content to write
            encoding: Encoding to use

        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)

        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with backup
            if file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                try:
                    file_path.replace(backup_path)
                except Exception:
                    pass  # Continue without backup if it fails

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)

            return True

        except Exception:
            return False

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text for consistent handling

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        if not isinstance(text, str):
            return str(text)

        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Strip BOM if present
        if text.startswith('\ufeff'):
            text = text[1:]

        return text

    @staticmethod
    def safe_encode(text: str, target_encoding: str = 'utf-8') -> bytes:
        """
        Safely encode text to bytes

        Args:
            text: Text to encode
            target_encoding: Target encoding

        Returns:
            Encoded bytes
        """
        try:
            return text.encode(target_encoding)
        except UnicodeEncodeError:
            # Fallback to UTF-8
            return text.encode('utf-8')
        except Exception:
            return str(text).encode('utf-8')

    @staticmethod
    def safe_decode(data: bytes, source_encoding: Optional[str] = None) -> str:
        """
        Safely decode bytes to text

        Args:
            data: Bytes to decode
            source_encoding: Source encoding (auto-detect if None)

        Returns:
            Decoded text
        """
        if source_encoding:
            try:
                return data.decode(source_encoding)
            except UnicodeDecodeError:
                pass

        # Auto-detection fallback
        encodings_to_try = ['utf-8', 'utf-8-sig', 'gbk', 'latin-1']

        for encoding in encodings_to_try:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue

        # Final fallback - replace errors
        return data.decode('utf-8', errors='replace')

    @staticmethod
    def convert_file_encoding(
        source_path: Union[str, Path],
        target_path: Union[str, Path],
        target_encoding: str = 'utf-8-sig'
    ) -> bool:
        """
        Convert file encoding

        Args:
            source_path: Source file path
            target_path: Target file path
            target_encoding: Target encoding

        Returns:
            True if successful, False otherwise
        """
        source_path = Path(source_path)
        target_path = Path(target_path)

        # Read source file
        content = EncodingUtils.read_text_file(source_path)
        if content is None:
            return False

        # Write with new encoding
        return EncodingUtils.write_text_file(target_path, content, target_encoding)

    @staticmethod
    def is_utf8_compatible(text: str) -> bool:
        """
        Check if text is UTF-8 compatible

        Args:
            text: Text to check

        Returns:
            True if UTF-8 compatible
        """
        try:
            text.encode('utf-8')
            return True
        except UnicodeEncodeError:
            return False