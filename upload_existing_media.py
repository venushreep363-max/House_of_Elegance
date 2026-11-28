

import os
import django
from pathlib import Path

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "house_of_elegance.settings"
)

django.setup()

from django.conf import settings
import cloudinary.uploader

media_folder = Path(settings.BASE_DIR) / "media"

image_files = sorted(
    file for file in media_folder.rglob("*")
    if file.is_file()
)

uploaded = 0

print("Starting Cloudinary upload...")

for file in image_files:
    relative_path = file.relative_to(media_folder)
    public_id = relative_path.with_suffix("").as_posix()

    result = cloudinary.uploader.upload(
        str(file),
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )

    uploaded += 1
    print("Uploaded:", relative_path)

print("Successfully uploaded:", uploaded)
print("Upload process completed!")
