#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTF-8编码工具模块
提供跨平台的UTF-8编码支持和文本处理工具
"""

import os
import sys
import locale
import codecs
import logging
from pathlib import Path
from typing import Optional, Union, List, Tuple

logger = logging.getLogger(__name__)

class EncodingUtils:
    """编码工具类"""

    # 常用编码格式，按优先级排序
    COMMON_ENCODINGS = [
        'utf-8-sig',    # UTF-8 with BOM
        'utf-8',        # UTF-8
        'gbk',          # 简体中文
        'gb2312',       # 简体中文（旧）
        'big5',         # 繁体中文
        'cp936',        # Windows简体中文
        'cp950',        # Windows繁体中文
        'iso-8859-1',   # Latin-1
        'ascii'         # ASCII
    ]

    @staticmethod
    def setup_utf8_environment():
        """设置UTF-8环境"""
        try:
            # 设置环境变量
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            os.environ['LANG'] = 'en_US.UTF-8'

            # Windows特殊处理
            if sys.platform == 'win32':
                # 设置控制台代码页
                try:
                    os.system('chcp 65001 >nul 2>&1')
                except:
                    pass

                # 重新配置标准输出流
                if hasattr(sys.stdout, 'reconfigure'):
                    try:
                        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                    except:
                        pass

                # 设置locale
                try:
                    locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
                except:
                    try:
                        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                    except:
                        try:
                            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                        except:
                            pass

            logger.info("UTF-8环境设置完成")
            return True

        except Exception as e:
            logger.warning(f"UTF-8环境设置失败: {e}")
            return False

    @staticmethod
    def detect_file_encoding(file_path: Union[str, Path], sample_size: int = 8192) -> str:
        """检测文件编码格式

        Args:
            file_path: 文件路径
            sample_size: 采样大小

        Returns:
            检测到的编码格式
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return 'utf-8'

        try:
            # 读取文件开头的字节
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)

            if not raw_data:
                return 'utf-8'

            # 检查BOM标记
            if raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            elif raw_data.startswith(b'\xff\xfe'):
                return 'utf-16-le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16-be'

            # 尝试不同编码
            for encoding in EncodingUtils.COMMON_ENCODINGS:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    continue

            # 如果都失败，使用chardet库检测（如果可用）
            try:
                import chardet
                result = chardet.detect(raw_data)
                if result and result.get('confidence', 0) > 0.7:
                    return result['encoding']
            except ImportError:
                pass

            # 默认返回utf-8
            logger.warning(f"无法检测文件编码: {file_path}，使用默认UTF-8")
            return 'utf-8'

        except Exception as e:
            logger.error(f"检测文件编码时出错: {e}")
            return 'utf-8'

    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: Optional[str] = None) -> Optional[str]:
        """安全读取文本文件

        Args:
            file_path: 文件路径
            encoding: 指定编码，None表示自动检测

        Returns:
            文件内容，失败时返回None
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        if encoding:
            encodings_to_try = [encoding]
        else:
            # 先检测编码
            detected_encoding = EncodingUtils.detect_file_encoding(file_path)
            encodings_to_try = [detected_encoding] + [enc for enc in EncodingUtils.COMMON_ENCODINGS if enc != detected_encoding]

        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc, errors='strict') as f:
                    content = f.read()
                logger.debug(f"成功使用编码 {enc} 读取文件: {file_path}")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"读取文件时出错: {e}")
                break

        # 最后尝试用替换模式读取
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            logger.warning(f"使用替换模式读取文件: {file_path}")
            return content
        except Exception as e:
            logger.error(f"读取文件完全失败: {e}")
            return None

    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str, encoding: str = 'utf-8-sig',
                       backup: bool = True) -> bool:
        """安全写入文本文件

        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 编码格式
            backup: 是否备份原文件

        Returns:
            是否成功
        """
        file_path = Path(file_path)

        try:
            # 创建目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 备份原文件
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                try:
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    logger.debug(f"文件已备份: {backup_path}")
                except Exception as e:
                    logger.warning(f"备份文件失败: {e}")

            # 写入文件
            with open(file_path, 'w', encoding=encoding, errors='replace') as f:
                f.write(content)

            logger.debug(f"成功写入文件: {file_path} (编码: {encoding})")
            return True

        except Exception as e:
            logger.error(f"写入文件失败: {e}")
            return False

    @staticmethod
    def normalize_text(text: str) -> str:
        """规范化文本，处理编码问题

        Args:
            text: 输入文本

        Returns:
            规范化后的文本
        """
        if not isinstance(text, str):
            text = str(text)

        try:
            # 移除BOM标记
            if text.startswith('\ufeff'):
                text = text[1:]

            # 规范化换行符
            text = text.replace('\r\n', '\n').replace('\r', '\n')

            # 移除控制字符（保留换行符和制表符）
            import re
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

            return text

        except Exception as e:
            logger.error(f"文本规范化失败: {e}")
            return text

    @staticmethod
    def safe_encode(text: str, target_encoding: str = 'utf-8') -> bytes:
        """安全编码文本

        Args:
            text: 输入文本
            target_encoding: 目标编码

        Returns:
            编码后的字节串
        """
        try:
            if not isinstance(text, str):
                text = str(text)

            return text.encode(target_encoding, errors='replace')

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            # 返回安全的ASCII编码
            return text.encode('ascii', errors='replace')

    @staticmethod
    def safe_decode(data: bytes, source_encoding: Optional[str] = None) -> str:
        """安全解码字节串

        Args:
            data: 字节数据
            source_encoding: 源编码，None表示自动检测

        Returns:
            解码后的文本
        """
        if isinstance(data, str):
            return data

        if not data:
            return ''

        if source_encoding:
            encodings_to_try = [source_encoding]
        else:
            encodings_to_try = EncodingUtils.COMMON_ENCODINGS

        for encoding in encodings_to_try:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"使用编码 {encoding} 解码失败: {e}")
                continue

        # 最后尝试用替换模式
        try:
            return data.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"解码完全失败: {e}")
            return str(data, errors='replace')

    @staticmethod
    def get_system_encoding() -> str:
        """获取系统默认编码"""
        try:
            return locale.getpreferredencoding() or 'utf-8'
        except Exception:
            return 'utf-8'

    @staticmethod
    def is_utf8_compatible(text: str) -> bool:
        """检查文本是否UTF-8兼容

        Args:
            text: 输入文本

        Returns:
            是否UTF-8兼容
        """
        try:
            if not isinstance(text, str):
                text = str(text)

            # 尝试编码和解码
            encoded = text.encode('utf-8')
            decoded = encoded.decode('utf-8')

            return decoded == text

        except Exception:
            return False

    @staticmethod
    def convert_file_encoding(source_path: Union[str, Path], target_path: Union[str, Path],
                            source_encoding: Optional[str] = None, target_encoding: str = 'utf-8-sig') -> bool:
        """转换文件编码格式

        Args:
            source_path: 源文件路径
            target_path: 目标文件路径
            source_encoding: 源编码，None表示自动检测
            target_encoding: 目标编码

        Returns:
            是否成功
        """
        try:
            # 读取源文件
            content = EncodingUtils.read_text_file(source_path, source_encoding)
            if content is None:
                return False

            # 写入目标文件
            return EncodingUtils.write_text_file(target_path, content, target_encoding, backup=False)

        except Exception as e:
            logger.error(f"转换文件编码失败: {e}")
            return False

# 模块初始化时自动设置UTF-8环境
try:
    EncodingUtils.setup_utf8_environment()
except Exception as e:
    logger.warning(f"模块初始化时设置UTF-8环境失败: {e}")

# 导出常用函数
__all__ = [
    'EncodingUtils',
    'setup_utf8_environment',
    'detect_file_encoding',
    'read_text_file',
    'write_text_file',
    'normalize_text',
    'safe_encode',
    'safe_decode'
]

# 便捷函数别名
setup_utf8_environment = EncodingUtils.setup_utf8_environment
detect_file_encoding = EncodingUtils.detect_file_encoding
read_text_file = EncodingUtils.read_text_file
write_text_file = EncodingUtils.write_text_file
normalize_text = EncodingUtils.normalize_text
safe_encode = EncodingUtils.safe_encode
safe_decode = EncodingUtils.safe_decode
