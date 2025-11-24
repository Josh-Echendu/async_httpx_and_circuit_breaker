import httpx
import asyncio
import os
import aiofiles


async def download_large_file(file_info, download_folder):
    file_path = os.path.join(download_folder, file_info['name'])
    return file_path

async def streaming_large_downloads():
    """Stream large files to avoid memory issues"""
    
    # Simulate large file downloads (using httpbin streams)
    large_files = [
        {"url": "https://httpbin.org/bytes/1048576", "name": "1MB_file.bin"},  # 1MB
        {"url": "https://httpbin.org/bytes/5242880", "name": "5MB_file.bin"},  # 5MB
        {"url": "https://httpbin.org/bytes/10485760", "name": "10MB_file.bin"}, # 10MB
    ]

    download_folder = "large_downloads"
    os.makedirs(download_folder, exist_ok=True)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)) as client:

        # Extract and Prepare filenames for each large file
        tasks = [download_large_file(file_info, download_folder) for file_info in large_files]
        file_paths = await asyncio.gather(*tasks)
        print("✅ Downloaded files:", file_paths)

        # Extract the URLs from large_files
        urls = [file_info['url'] for file_info in large_files]
        print("✅ File URLs:", urls)

        tasks = [stream_download_file(client, file_path, url) for file_path, url in zip(file_paths, urls)]

        results = await asyncio.gather(*tasks)
        print("Results Summary:", results)

        # Display results
        total_downloaded = 0
        for result in results:
            status = "✅ Success" if result['success'] else "❌ Failed"
            size_mb = result['size_bytes'] / (1024 * 1024) # Convert bytes to MB
            total_downloaded = total_downloaded + result['size_bytes']

            if result['success']:
                print(f"{status}: {result['filename']} | Size: {size_mb:.2f} MB | Chunks: {result['chunks']}")
            else:
                print(f"{status}: {result['filename']} | Error: {result['error']}")

            total_mb = total_downloaded / (1024 * 1024)
            print(f"Total Downloaded: {total_mb:.2f} MB")


async def stream_download_file(client, file_path, url):
    """Stream download to handle large files without memory issues"""

    try:
        chunk_count = 0
        total_size = 0

        async with client.stream("GET", url, timeout=60.0) as response:
            response.raise_for_status() 

            async with aiofiles.open(file_path, 'wb') as file:

                # aiter_bytes() : is not a normal list or tuple. It’s an asynchronous iterator — a stream of data coming over time from the network.
                async for chunk in response.aiter_bytes():  # So instead of “looping through things we already have,” we’re “looping through things as they arrive.”
                    await file.write(chunk)
                    print(f"Chunk received {file_path}: {chunk[:20]}")
                    chunk_count = chunk_count + 1
                    total_size = total_size + len(chunk)

                    # Progress indicator for very large files
                    if chunk_count % 20 == 0:

                        # 1 KB = 1024 bytes, 1 MB = 1024 × 1024 bytes
                        mb_downloaded = total_size / (1024 * 1024)
                        print(f"   📥 {os.path.basename(file_path)}: {mb_downloaded:.2f} MB... ✅")

        return {
            "success": True,
            "filename": file_path,
            "size_bytes": total_size,
            "chunks": chunk_count,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "filename": file_path,
            "size_bytes": 0,
            "chunks": 0,
            "error": str(e)
        }



if __name__ == "__main__":
    asyncio.run(streaming_large_downloads())



# async with client.stream("GET", "https://httpbin.org/stream/5") as response:
#     print("BYTES MODE:")
#     async for chunk in response.aiter_bytes():
#         print(repr(chunk))  # raw data
    
#     print("TEXT MODE:")
#     async for chunk in response.aiter_text():
#         print(chunk)  # decoded text pieces

#     print("LINES MODE:")
#     async for line in response.aiter_lines():
#         print(line)  # each line individually

