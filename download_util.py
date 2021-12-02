"""
Pre-requisites:
- tqdm library: pip3 install tqdm
"""

import os
from tqdm import tqdm

def download_file_from_url_with_progressbar(url, filepath, filename):
    if os.path.exists(filepath):
        os.remove(filepath)
    with requests.get(url, stream=True) as res:
        res.raise_for_status()
        block_size = 1024 * 1024
        total_size_in_bytes= int(res.headers.get('content-length', 0))
        logger.info(f"File size: {total_size_in_bytes}Bytes")
        with tqdm.wrapattr(open(filepath, "wb"), "write",
                   miniters=1, desc=filename,
                   total=int(res.headers.get('content-length', 0))) as fout:
            for chunk in res.iter_content(chunk_size=block_size):
                fout.write(chunk)
    if not os.path.exists(filepath) or  os.path.getsize(filepath) != total_size_in_bytes:
        raise Exception("Error while downloading file. ")
