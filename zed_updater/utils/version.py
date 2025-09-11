#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本工具模块
提供版本号解析、比较和处理相关功能
"""

import re
import logging
from typing import Tuple, Union, List, Optional

logger = logging.getLogger(__name__)

def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    解析版本号字符串为元组，用于比较

    支持的格式:
    - 标准版本号: 1.2.3, 1.2, 1
    - 包含字母的版本号: 1.2.3a, 1.2beta
    - 包含前缀的版本号: v1.2.3, Version 1.2.3

    Args:
        version_str: 版本号字符串

    Returns:
        包含版本各部分的元组 (主版本号, 次版本号, 修订号, ...)
    """
    if not version_str:
        return (0, 0, 0)

    # 移除版本号前缀
    version_str = re.sub(r'^[vV]', '', version_str)
    version_str = re.sub(r'^[a-zA-Z\s]+', '', version_str)

    # 提取数字部分
    version_parts = []
    for part in re.split(r'[.-]', version_str):
        # 处理带字母的部分，如1.2.3a, 1.2beta
        match = re.match(r'(\d+)([a-zA-Z].*)?', part)
        if match:
            num_part, alpha_part = match.groups()
            version_parts.append(int(num_part))
            if alpha_part:
                # 把字母部分添加为额外的版本号部分
                # 字母部分按照字母序比较
                version_parts.append(alpha_part)
        else:
            # 如果部分不包含数字，可能是纯字母
            version_parts.append(part)

    # 确保至少有三个数字部分
    while len(version_parts) < 3:
        version_parts.append(0)

    return tuple(version_parts)

def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号

    Args:
        version1: 第一个版本号
        version2: 第二个版本号

    Returns:
        如果version1 < version2，返回-1
        如果version1 > version2，返回1
        如果version1 == version2，返回0
    """
    # 解析版本号为元组
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)

    # 逐部分比较
    for i in range(max(len(v1_parts), len(v2_parts))):
        # 获取对应部分，不存在则视为0或''
        v1_part = v1_parts[i] if i < len(v1_parts) else 0 if isinstance(v1_parts[0], int) else ''
        v2_part = v2_parts[i] if i < len(v2_parts) else 0 if isinstance(v2_parts[0], int) else ''

        # 类型不同时的处理
        if isinstance(v1_part, int) and isinstance(v2_part, str):
            return -1  # 数字版本比字母版本早
        elif isinstance(v1_part, str) and isinstance(v2_part, int):
            return 1  # 字母版本比数字版本晚

        # 相同类型的比较
        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1

    # 所有部分都相同
    return 0

def format_version(version_parts: Union[Tuple[int, ...], List[int]], include_prefix: bool = False) -> str:
    """
    将版本号元组格式化为字符串

    Args:
        version_parts: 版本号各部分组成的元组或列表
        include_prefix: 是否包含'v'前缀

    Returns:
        格式化的版本号字符串
    """
    # 过滤掉非整数部分
    int_parts = [p for p in version_parts if isinstance(p, int)]

    # 生成版本号字符串
    version_str = '.'.join(str(p) for p in int_parts)

    # 添加前缀
    if include_prefix and version_str:
        version_str = f"v{version_str}"

    return version_str

def extract_version_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取版本号

    Args:
        filename: 文件名

    Returns:
        提取到的版本号字符串，未找到则返回None
    """
    # 匹配常见的版本号模式
    patterns = [
        r'[vV]?(\d+\.\d+\.\d+)',  # v1.2.3 or 1.2.3
        r'[vV]?(\d+\.\d+)',       # v1.2 or 1.2
        r'[vV]?(\d+_\d+_\d+)',    # v1_2_3 or 1_2_3
        r'[vV]?(\d+[-_]\d+)',     # v1-2 or 1_2
        r'[-_]([0-9.]+)[.-]'      # -1.2.3- or _1.2.3.
    ]

    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1).replace('_', '.')

    return None

def get_version_info(version_str: str) -> dict:
    """
    获取版本详细信息

    Args:
        version_str: 版本号字符串

    Returns:
        包含版本信息的字典
    """
    parts = parse_version(version_str)

    # 从元组中提取版本信息
    version_info = {
        'full': version_str,
        'normalized': format_version(parts, include_prefix=True),
        'major': parts[0] if len(parts) > 0 and isinstance(parts[0], int) else 0,
        'minor': parts[1] if len(parts) > 1 and isinstance(parts[1], int) else 0,
        'patch': parts[2] if len(parts) > 2 and isinstance(parts[2], int) else 0,
        'is_prerelease': any(isinstance(p, str) for p in parts),
        'parts': parts
    }

    return version_info
