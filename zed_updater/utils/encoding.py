#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编码工具模块
负责处理文本编码相关的功能，确保跨平台兼容性
"""

import sys
import os
import locale
import codecs
import logging

logger = logging.getLogger(__name__)

def setup_encoding():
    """
    设置程序的默认编码环境为UTF-8
    确保所有文本处理和I/O操作都使用UTF-8编码
    """
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    if sys.platform == 'win32':
        # Windows系统UTF-8兼容性设置
        try:
            # 尝试设置控制台代码页为UTF-8
            os.system('chcp 65001 > nul')
        except Exception as e:
            logger.warning(f"无法设置Windows控制台代码页: {e}")

        try:
            # 尝试设置区域编码
            locale.setlocale(locale.LC_ALL, 'Chinese_China.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except Exception as e:
                logger.warning(f"无法设置系统区域编码: {e}")

    # 配置标准输出流
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            logger.debug("已重新配置标准输出流为UTF-8")
        except Exception as e:
            logger.warning(f"无法重新配置标准输出流: {e}")

def ensure_utf8(text, fallback_encodings=None):
    """
    确保文本是UTF-8编码，尝试从其他编码转换

    Args:
        text: 要转换的文本字符串或字节对象
        fallback_encodings: 当UTF-8解码失败时尝试的其他编码列表

    Returns:
        UTF-8编码的字符串
    """
    if fallback_encodings is None:
        fallback_encodings = ['gbk', 'gb2312', 'latin1', locale.getpreferredencoding()]

    # 如果已经是字符串，直接返回
    if isinstance(text, str):
        return text

    # 如果是字节，尝试用UTF-8解码
    if isinstance(text, bytes):
        try:
            return text.decode('utf-8')
        except UnicodeDecodeError:
            # 尝试备用编码
            for encoding in fallback_encodings:
                try:
                    return text.decode(encoding)
                except UnicodeDecodeError:
                    continue

            # 如果都失败了，使用latin1作为最后的备选（保证不会抛出异常）
            logger.warning("无法确定文本编码，使用latin1作为备选")
            return text.decode('latin1', errors='replace')

    # 如果不是字符串也不是字节，转为字符串
    return str(text)

def detect_file_encoding(file_path, default='utf-8'):
    """
    尝试检测文件的编码

    Args:
        file_path: 要检测的文件路径
        default: 默认使用的编码

    Returns:
        检测到的编码或默认编码
    """
    # 尝试使用chardet库检测编码
    try:
        import chardet

        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)  # 读取前4096字节进行检测
            if not raw_data:
                return default

            result = chardet.detect(raw_data)
            if result['confidence'] > 0.7:  # 只有当置信度高时才返回检测结果
                return result['encoding']
    except ImportError:
        logger.debug("未安装chardet库，无法精确检测文件编码")
    except Exception as e:
        logger.warning(f"检测文件编码时出错: {e}")

    # 尝试一些常见的编码
    encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(100)  # 尝试读取一小部分
                return enc
        except UnicodeDecodeError:
            continue

    # 返回默认编码
    return default

def read_file_with_encoding(file_path, encoding=None):
    """
    以适当的编码读取文件内容

    Args:
        file_path: 文件路径
        encoding: 指定编码，如果为None则自动检测

    Returns:
        文件内容字符串
    """
    if encoding is None:
        encoding = detect_file_encoding(file_path)

    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except UnicodeDecodeError:
        # 如果指定编码失败，尝试自动检测
        encoding = detect_file_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()

def write_file_with_encoding(file_path, content, encoding='utf-8'):
    """
    以指定编码写入文件内容

    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 使用的编码，默认UTF-8

    Returns:
        成功写入返回True，否则返回False
    """
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {e}")
        return False
