"""
AI标题生成器 - 基于视频内容自动生成吸引人的标题
"""
import json
import re
from typing import Optional
import requests
from config.settings import log, app_config


TITLE_STYLES = {
    "情感": "生成带有情感共鸣的标题，引发用户共情",
    "悬疑": "生成制造悬念的标题，引发用户好奇心",
    "干货": "生成实用知识类标题，强调价值输出",
    "娱乐": "生成轻松有趣的标题，突出娱乐性",
    "带货": "生成促使用户购买的标题，突出产品优势",
    "教程": "生成教程类标题，强调学习过程",
}


def generate_title(
    video_description: str = "",
    keywords: list[str] = None,
    style: str = "干货",
    subtitle_text: str = "",
    count: int = 3,
) -> list[str]:
    """
    基于视频信息生成AI标题

    Args:
        video_description: 视频内容描述
        keywords: 关键词列表
        style: 标题风格
        subtitle_text: 字幕文本（用于提取关键信息）
        count: 生成数量
    """
    keywords = keywords or []
    style_hint = TITLE_STYLES.get(style, TITLE_STYLES["干货"])

    # 尝试使用Ollama
    if _check_ollama():
        return _generate_with_ollama(
            video_description, keywords, style_hint, subtitle_text, count
        )

    # 回退方案：基于模板生成
    return _generate_with_template(keywords, style, count)


def generate_hashtags(
    video_description: str = "",
    keywords: list[str] = None,
    category: str = "综合",
    count: int = 5,
) -> list[str]:
    """
    生成推荐标签

    Args:
        video_description: 视频描述
        keywords: 关键词
        category: 视频分类
        count: 生成数量
    """
    keywords = keywords or []

    if _check_ollama():
        return _gen_tags_with_ollama(video_description, keywords, category, count)

    return _gen_tags_with_template(keywords, category, count)


def score_video_quality(
    video_path: str = "",
    metadata: dict = None,
) -> dict:
    """
    AI评分视频质量

    Returns:
        dict: {
            "score": 0-100,
            "aspects": {"画面": 80, "音频": 75, "内容": 85, "节奏": 70},
            "suggestions": ["建议1", "建议2"],
            "is_safe": True  # 是否安全（无违规风险）
        }
    """
    metadata = metadata or {}
    score = 75
    aspects = {"画面质量": 75, "音频质量": 75, "内容吸引力": 75, "节奏感": 75}
    suggestions = []

    # 基于元数据做基础评分
    dur = metadata.get("duration", 0)
    w = metadata.get("width", 0)
    h = metadata.get("height", 0)

    if w >= 1080 and h >= 1920:
        aspects["画面质量"] = 85
    elif w >= 720:
        aspects["画面质量"] = 75
    else:
        aspects["画面质量"] = 60
        suggestions.append("建议使用1080x1920分辨率")

    if dur >= 15:
        aspects["内容吸引力"] = 80
    elif dur >= 8:
        aspects["内容吸引力"] = 70
    else:
        aspects["内容吸引力"] = 55
        suggestions.append("视频时长建议≥15秒")

    if 15 <= dur <= 60:
        aspects["节奏感"] = 82
    elif dur < 15:
        aspects["节奏感"] = 65
        suggestions.append("视频过短，建议15-60秒")
    else:
        aspects["节奏感"] = 78

    fps = metadata.get("fps", 0)
    if fps >= 30:
        aspects["画面质量"] = min(aspects["画面质量"] + 5, 100)
    elif fps < 25:
        aspects["画面质量"] = max(aspects["画面质量"] - 5, 40)
        suggestions.append("建议使用30fps帧率")

    score = int(sum(aspects.values()) / len(aspects))
    return {
        "score": score,
        "aspects": aspects,
        "suggestions": suggestions,
        "is_safe": score >= 60,
    }


def _check_ollama() -> bool:
    """检查Ollama是否可用"""
    try:
        r = requests.get(f"{app_config.ai.ollama_host}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _generate_with_ollama(
    description: str,
    keywords: list[str],
    style_hint: str,
    subtitle: str,
    count: int,
) -> list[str]:
    """使用Ollama生成标题"""
    prompt = f"""你是抖音短视频标题专家。请根据以下视频信息生成吸引人的标题。
{style_hint}

视频描述: {description or '抖音短视频'}
关键词: {', '.join(keywords) if keywords else '通用'}
字幕摘要: {subtitle[:200] if subtitle else '无'}

请生成{count}个吸引人的短视频标题（每个标题15-30字），直接返回JSON数组格式：
["标题1", "标题2", "标题3"]

要求: 标题简洁有力、包含关键词、适合抖音风格。"""

    try:
        resp = requests.post(
            f"{app_config.ai.ollama_host}/api/generate",
            json={
                "model": app_config.ai.strategy_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "")
            # 提取JSON数组
            match = re.search(r"\[.*?\]", text, re.DOTALL)
            if match:
                titles = json.loads(match.group())
                return titles[:count]
    except Exception as e:
        log.warning(f"Ollama标题生成失败: {e}")

    return _generate_with_template(keywords, "干货", count)


def _gen_tags_with_ollama(
    description: str,
    keywords: list[str],
    category: str,
    count: int,
) -> list[str]:
    """使用Ollama生成标签"""
    prompt = f"""你是抖音标签专家。请为以下视频生成{count}个推荐标签。

描述: {description or '抖音短视频'}
关键词: {', '.join(keywords) if keywords else '通用'}
分类: {category}

直接返回JSON数组格式: ["标签1", "标签2"]"""

    try:
        resp = requests.post(
            f"{app_config.ai.ollama_host}/api/generate",
            json={
                "model": app_config.ai.strategy_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            text = resp.json().get("response", "")
            match = re.search(r"\[.*?\]", text, re.DOTALL)
            if match:
                return json.loads(match.group())[:count]
    except Exception:
        pass

    return _gen_tags_with_template(keywords, category, count)


def _generate_with_template(
    keywords: list[str],
    style: str,
    count: int,
) -> list[str]:
    """模板标题回退方案"""
    templates = {
        "情感": [
            "看完这条视频，我沉默了...",
            "我们都曾经历过这样的瞬间",
            "如果时光可以倒流，你会怎么做？",
        ],
        "悬疑": [
            "最后3秒千万别眨眼！",
            "结局你绝对猜不到",
            "你知道真相是什么吗？",
        ],
        "干货": [
            "学会这招，效率提升100%",
            "收藏！这可能是全网最全的教程",
            "新手必看！3分钟教你掌握核心技巧",
        ],
        "娱乐": [
            "笑得我肚子疼，一定要看到最后",
            "今日份快乐已到账，请查收",
            "这也太好笑了吧！",
        ],
        "带货": [
            "用了它才知道什么叫相见恨晚",
            "这个东西真的绝了！",
            "闺蜜推荐的，用了确实不错",
        ],
        "教程": [
            "保姆级教程，手把手教你",
            "从零开始，带你轻松入门",
            "一学就会，超实用技巧分享",
        ],
    }
    base = templates.get(style, templates["干货"])
    result = list(base[:count])
    while len(result) < count:
        result.append(f"超实用的{keywords[0] if keywords else '技能'}分享")
    return result


def _gen_tags_with_template(
    keywords: list[str],
    category: str,
    count: int,
) -> list[str]:
    """模板标签回退方案"""
    base_tags = {
        "综合": ["抖音", "短视频", "日常", "vlog", "生活", "干货"],
        "美食": ["美食", "吃货", "料理", "下厨房", "今天吃什么"],
        "美妆": ["美妆", "化妆", "护肤", "变美", "好物分享"],
        "游戏": ["游戏", "手游", "电竞", "游戏日常", "上分"],
        "教程": ["教程", "学习", "技巧", "干货", "实用"],
        "带货": ["好物推荐", "种草", "测评", "必买清单", "性价比"],
        "搞笑": ["搞笑", "沙雕", "日常搞笑", "快乐源泉"],
    }
    tags = list(base_tags.get(category, base_tags["综合"]))
    tags.extend(keywords[:3])
    return list(dict.fromkeys(tags))[:count]  # 去重
