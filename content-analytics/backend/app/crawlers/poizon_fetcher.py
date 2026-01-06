import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Any
import asyncio
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)


@asynccontextmanager
async def _playwright_context():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            yield browser
        finally:
            await browser.close()


def _normalize_image_url(url: Optional[str], remove_resize: bool = True) -> Optional[str]:
    """规范化图片URL，可选去除裁剪参数获取完整图片"""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if url.startswith("//"):
        url = f"https:{url}"
    
    # 去除得物CDN的裁剪参数，获取完整图片
    if remove_resize and "x-oss-process" in url:
        # 移除 ?x-oss-process=... 或 &x-oss-process=... 参数
        if "?" in url:
            base_url = url.split("?")[0]
            return base_url
    
    return url


def _collect_images_from_html(html: Optional[str]) -> List[str]:
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls: List[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        src = _normalize_image_url(src)
        if not src:
            continue
        if "poizon.com" in src or "image-cdn.poizon.com" in src:
            if src not in urls:
                urls.append(src)
    return urls


def _looks_like_image_url(value: str) -> bool:
    if not value:
        return False
    lower = value.lower()
    if "image-cdn.poizon.com" in lower:
        return True
    if "poizon.com" in lower and any(ext in lower for ext in (".jpg", ".jpeg", ".png", ".webp")):
        return True
    return False


def _extract_images_from_payload(payload: Any) -> List[str]:
    images: List[str] = []

    def add(url: str):
        normalized = _normalize_image_url(url)
        if normalized and normalized not in images:
            images.append(normalized)

    def walk(obj: Any):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    if _looks_like_image_url(value):
                        add(value)
                    continue
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and _looks_like_image_url(item):
                            add(item)
                        elif isinstance(item, dict):
                            for k in ("url", "imageUrl", "originUrl", "imgUrl", "picUrl"):
                                val = item.get(k)
                                if isinstance(val, str) and _looks_like_image_url(val):
                                    add(val)
                        else:
                            walk(item)
                    continue
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)
    return images


def _extract_content_from_payload(payload: Any) -> Dict[str, Optional[str]]:
    """从得物API响应中提取真实的标题和描述"""
    result = {"title": None, "description": None}
    
    def walk(obj: Any):
        if isinstance(obj, dict):
            # 查找 content 或 detail 字段中的标题和描述
            # 得物API通常在 data.detail.content 或类似路径
            if "content" in obj and isinstance(obj["content"], str):
                text = obj["content"].strip()
                if text and not result["title"]:
                    # 分割标题和正文：第一行或emoji前的部分作为标题
                    lines = text.split('\n')
                    if lines:
                        first_line = lines[0].strip()
                        # 如果第一行不是纯标签，作为标题
                        if first_line and not first_line.startswith('#'):
                            result["title"] = first_line
                            # 剩余部分作为描述
                            rest = '\n'.join(lines[1:]).strip()
                            if rest:
                                result["description"] = rest
                        else:
                            # 整个内容作为描述
                            result["description"] = text
            
            # 也检查 title 字段
            if "title" in obj and isinstance(obj["title"], str):
                title_val = obj["title"].strip()
                if title_val and not result["title"]:
                    result["title"] = title_val
            
            # 检查 desc/description 字段
            for key in ("desc", "description", "text"):
                if key in obj and isinstance(obj[key], str):
                    desc_val = obj[key].strip()
                    if desc_val and not result["description"]:
                        result["description"] = desc_val
            
            # 递归遍历
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
    
    walk(payload)
    return result


async def fetch_poizon_meta(url: str, timeout: int = 10, use_playwright_fallback: bool = True) -> Dict[str, Optional[object]]:
    """
    抓取得物分享页的 og 信息（标题/描述/封面）
    先尝试 httpx 静态提取，若失败可选用 Playwright 渲染获取 meta。
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": "https://m.poizon.com/",
    }
    html = None
    try:
        async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
    except Exception:
        html = None

    title = desc = img = None
    images: List[str] = []
    if html:
        soup = BeautifulSoup(html, "html.parser")

        def get_meta(prop):
            tag = soup.find("meta", property=prop)
            return tag.get("content") if tag else None

        title = get_meta("og:title")
        desc = get_meta("og:description")
        img = _normalize_image_url(get_meta("og:image"))
        images = _collect_images_from_html(html)
        if img and img not in images:
            images.insert(0, img)

    # 得物链接总是使用 Playwright 获取API响应中的真实标题（og:title通常是账号名，不准确）
    if use_playwright_fallback:
        try:
            async with _playwright_context() as browser:
                page = await browser.new_page()
                detail_payloads: List[Any] = []

                async def handle_response(response):
                    if "sns-cnt-center/v1/common/h5/content-detail" in response.url:
                        try:
                            detail_payloads.append(await response.json())
                        except Exception:
                            pass

                page.on("response", handle_response)
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
                await page.wait_for_timeout(3000)
                title = await page.title()
                og_title = await page.locator('meta[property="og:title"]').get_attribute('content')
                og_desc = await page.locator('meta[property="og:description"]').get_attribute('content')
                og_img = await page.locator('meta[property="og:image"]').get_attribute('content')
                title = og_title or title
                desc = og_desc or desc
                img = _normalize_image_url(og_img or img)

                try:
                    await page.wait_for_selector("img", timeout=3000)
                except Exception:
                    pass
                img_list = await page.eval_on_selector_all(
                    "img",
                    "els => els.map(e => e.src || e.getAttribute('data-src') || e.getAttribute('data-original'))"
                )
                for item in img_list or []:
                    normalized = _normalize_image_url(item)
                    if normalized and _looks_like_image_url(normalized):
                        if normalized not in images:
                            images.append(normalized)
                for payload in detail_payloads:
                    for found in _extract_images_from_payload(payload):
                        if found not in images:
                            images.append(found)
                    # 从API响应提取真实标题和描述（优先级高于og:title）
                    content_info = _extract_content_from_payload(payload)
                    if content_info.get("title"):
                        title = content_info["title"]
                    if content_info.get("description"):
                        desc = content_info["description"]
                if img and img not in images:
                    images.insert(0, img)
        except Exception:
            pass

    # 优先使用image_urls中的第一张完整图片作为封面（而不是og:image裁剪版）
    final_cover = images[0] if images else img
    
    return {
        "title": title,
        "description": desc,
        "image": final_cover,
        "image_urls": images or None
    }


def fetch_poizon_meta_sync(url: str, timeout: int = 10, use_playwright_fallback: bool = True) -> Dict[str, Optional[str]]:
    return asyncio.run(fetch_poizon_meta(url, timeout=timeout, use_playwright_fallback=use_playwright_fallback))
