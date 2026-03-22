name = input("File name: ").strip().lower()

media_types = {
    ".gif": "image/gif",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".zip": "application/zip",
}

for ext, media_type in media_types.items():
    if name.endswith(ext):
        print(media_type)
        break
else:
    print("application/octet-stream")
