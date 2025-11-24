import httpx
import asyncio
import os
import hashlib
import aiofiles


async def enterprise_file_upload():
    """Enterprise-grade file upload with progress tracking and verification"""
   
    folder = r"/Users/joshua.echendu/Documents/pydoll/asyncio_httpx/downloaded_images"
   # Simulate multiple files to upload
    files_to_upload = [
        {"path": f"{os.path.join(folder, 'product_image_1.jpeg')}", "type": "image/jpeg"},
        {"path": f"{os.path.join(folder, 'product_image_2.png')}", "type": "image/png"},
        {"path": f"{os.path.join(folder, 'product_image_3.svg')}", "type": "image/svg+xml"}
    ]

    for file in files_to_upload:
        if not os.path.exists(file['path']):
            async with aiofiles.open(file['path'], 'wb') as f:
                f.write(f"This is sample content for {file_info['path']}\n" * 100)
                print(f"📝 Created sample file: {file_info['path']}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0), limits=httpx.Limits(max_connections=5, max_keepalive_connections=5)) as client:
        tasks = [upload_single_file(client, file_info) for file_info in files_to_upload]

        # Wait for all uploads to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print("Results Summary:", results)


async def upload_single_file(client, filepath):
    """Upload a single file with progress tracking and retry logic"""
    start_time = asyncio.get_event_loop().time()
    retry_count = 0

    for i in range(1, 4):  # Retry up to 3 times
        try:
            file_size = os.path.getsize(filepath['path'])
            file_name = os.path.basename(filepath['path'])

            print(f"   📤 Uploading {file_name} ({file_size} bytes)...")

            # Read file content
            async with aiofiles.open(filepath['path'], 'rb') as file:
                file_content = await file.read()
                print(f"   📦 Read {len(file_content)} bytes from {file_name}")

            # Generate file hash for verification
            file_hash = hashlib.md5(file_content).hexdigest()
            print(f"   🔒 File Hash (MD5): {file_hash}")

             # Prepare files for upload (multipart form data)
            files = {
                'file': (file_name, file_content, filepath['type']),
                'metadata': (None, f'{{"original_name":"{file_name}","hash":"{file_hash}"}}')
            }

            # Upload to httpbin (simulating real upload endpoint)
            response = await client.post(
                "https://httpbin.org/post",
                files=files,
                timeout=60.0,
                headers={
                    "X-File-Size": str(file_size),
                    "X-File-Hash": file_hash
                }
            )
            response.raise_for_status()  # Raise error for bad responses
            upload_time = asyncio.get_event_loop().time() - start_time

            # parse response
            response_data = response.json()
            return {
                "success": True,
                "filename": file_name,
                "file_size": file_size,
                "upload_time": upload_time,
                "retry_count": retry_count,
                "error": None
            }
            break  # Exit retry loop on success
        except Exception as e:
            retry_count = retry_count + 1
            # Exponential backoff: double wait time each retry
            await asyncio.sleep(2 ** retry_count)

            print(f"   ❌ Error uploading {file_name} (Attempt {retry_count}/3): {e}")
            if retry_count >= 3:
                return {
                    "success": False,
                    "filename": filepath,
                    "file_size": 0,
                    "upload_time": 0,
                    "error": str(e),
                    "retry_count": retry_count
                }

if __name__ == "__main__":
    asyncio.run(enterprise_file_upload())








