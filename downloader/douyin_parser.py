"""
抖音直播回放解析下载器 - 基于yt-dlp
"""
import os
import json
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable


class DouyinDownloader:
    """抖音视频/回放下載器"""
    
    def __init__(self):
        self.cancelled = False
        self._progress_cb: Optional[Callable] = None
    
    def cancel(self):
        self.cancelled = True
    
    def extract_info(self, url: str) -> Optional[dict]:
        """提取视频信息（不下载）"""
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-playlist", url],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return None
    
    def download(
        self,
        url: str,
        output_dir: str,
        progress_cb: Optional[Callable] = None,
    ) -> tuple[bool, str]:
        """
        下载视频
        返回: (成功标志, 输出文件路径或错误信息)
        """
        self.cancelled = False
        self._progress_cb = progress_cb
        
        # 构建yt-dlp参数
        output_template = os.path.join(output_dir, "%(title)s_%(id)s.%(ext)s")
        
        args = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", output_template,
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--newline",
            url,
        ]
        
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            
            output_path = ""
            for line in process.stdout:
                if self.cancelled:
                    process.terminate()
                    return False, "用户取消"
                
                # 解析进度
                if "[download]" in line and "%" in line:
                    try:
                        pct_str = line.split("%")[0].split()[-1]
                        pct = float(pct_str)
                        if progress_cb:
                            progress_cb(pct, "下载中...")
                    except ValueError:
                        pass
                
                # 解析输出路径
                if "Destination:" in line:
                    output_path = line.split("Destination:")[1].strip()
                elif "[Merger]" in line and "Deleting" not in line:
                    pass
                elif "has already been downloaded" in line:
                    return True, output_path
            
            process.wait()
            
            if process.returncode == 0:
                return True, output_path
            else:
                return False, f"下载失败 (code={process.returncode})"
                
        except FileNotFoundError:
            return False, "yt-dlp未安装，请运行: pip install yt-dlp"
        except Exception as e:
            return False, str(e)
    
    def download_batch(
        self,
        urls: list[str],
        output_dir: str,
        progress_cb: Optional[Callable] = None,
    ) -> list[tuple[bool, str]]:
        """批量下载"""
        results = []
        for i, url in enumerate(urls):
            if self.cancelled:
                break
            if progress_cb:
                progress_cb(0, f"下载 {i+1}/{len(urls)}")
            result = self.download(url, output_dir)
            results.append(result)
        return results
    
    def parse_share_link(self, share_text: str) -> list[str]:
        """从分享文本中提取视频链接"""
        import re
        urls = re.findall(r'https?://[^\s]+', share_text)
        # 过滤出抖音相关链接
        douyin_urls = [u for u in urls if any(
            d in u for d in ["douyin.com", "iesdouyin.com", "tiktok.com"]
        )]
        return douyin_urls if douyin_urls else urls


# 全局单例
downloader = DouyinDownloader()
