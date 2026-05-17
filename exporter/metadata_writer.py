"""元数据写入器 - 写入视频元信息"""
import json
import subprocess
from pathlib import Path
from config.settings import log, get_ffmpeg_path


def write_metadata(
    video_path: str,
    title: str = "",
    author: str = "",
    description: str = "",
    tags: list[str] = None,
    output_path: str = None,
) -> bool:
    """将元数据写入视频文件"""
    output = output_path or video_path

    metadata_file = Path(video_path).parent / f"{Path(video_path).stem}_meta.txt"
    meta_lines = [";FFMETADATA1"]

    if title:
        meta_lines.append(f"title={title}")
    if author:
        meta_lines.append(f"artist={author}")
    if description:
        meta_lines.append(f"description={description}")
    if tags:
        meta_lines.append(f"keywords={','.join(tags)}")

    metadata_file.write_text("\n".join(meta_lines) + "\n", encoding="utf-8")

    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", video_path,
        "-i", str(metadata_file),
        "-map_metadata", "1",
        "-c", "copy",
        output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        metadata_file.unlink(missing_ok=True)
        return True
    log.error(f"元数据写入失败: {result.stderr}")
    return False
