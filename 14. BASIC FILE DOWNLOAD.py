import httpx
import asyncio
import os
import aiofiles

async def fetch_images(url, index, download_folder):
    file_extension = os.path.basename(url)
    if file_extension not in ['jpeg', 'png', 'svg', 'jpg']:
        file_extension = 'jpg'  # default to jpg if unknown

    filename = os.path.join(download_folder, f"product_image_{index+1}.{file_extension}")
    return filename

async def basic_file_download():
    """Basic file download for product images"""
    
    # Sample images to download
    image_urls = [
        "https://httpbin.org/image/jpeg",
        "https://httpbin.org/image/png", 
        "https://httpbin.org/image/svg"
    ]

    download_folder = "downloaded_images"
    os.makedirs(download_folder, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)) as client:

        # Extract and Prepare filenames for each image
        tasks = [fetch_images(url, i, download_folder) for i, url in enumerate(image_urls)]
        filenames = await asyncio.gather(*tasks, return_exceptions=True)
        print("Results Summary:", filenames)

        tasks = [download_single_file(client, url, filename) for url, filename in zip(image_urls, filenames) if isinstance(filename, str)]

        # Download all files concurrently
        print("🚀 Starting concurrent file downloads...")
        result = await asyncio.gather(*tasks, return_exceptions=True)
        print("Results Summary:", result)

async def download_single_file(client, url, filename):
    """Download a single file"""
    try:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()  # Raise an error for bad responses
        print(response)

        async with aiofiles.open(filename, 'wb') as f:
            await f.write(response.content)
        
        file_size = len(response.content)
        return {
            "success": True,
            "filename": filename,
            "size_bytes": file_size,
            "error": None
        }

    except Exception as e:
        return {
            "success": False, 
            "filename": filename,
            "size": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    asyncio.run(basic_file_download())

