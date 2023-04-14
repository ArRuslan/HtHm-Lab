from asyncio import gather, get_event_loop
from concurrent.futures import ThreadPoolExecutor
from hashlib import md5
from io import BytesIO

from aioboto3 import Session
from PIL import Image, ImageSequence

from .singleton import Singleton


async def resizeAnimImage(img: Image, size: tuple[int, int], form: str) -> bytes:
    def _resize() -> bytes:
        orig_size = (img.size[0], img.size[1])
        n_frames = getattr(img, 'n_frames', 1)

        def resize_frame(frame):
            if orig_size == size:
                return frame
            return frame.resize(size)

        if n_frames == 1:
            return resize_frame(img)
        frames = []
        for frame in ImageSequence.Iterator(img):
            frames.append(resize_frame(frame))
        b = BytesIO()
        frames[0].save(b, format=form, save_all=True, append_images=frames[1:], loop=0)
        return b.getvalue()
    with ThreadPoolExecutor() as pool:
        res = await gather(get_event_loop().run_in_executor(pool, lambda: _resize()))
    return res[0]

async def resizeImage(image: Image, size: tuple[int, int], form: str) -> bytes:
    def _resize():
        img = image.resize(size)
        b = BytesIO()
        img.save(b, format=form, save_all=True)
        return b.getvalue()
    with ThreadPoolExecutor() as pool:
        res = await gather(get_event_loop().run_in_executor(pool, _resize))
    return res[0]

def imageFrames(img) -> int:
    return getattr(img, "n_frames", 1)

class S3Storage(Singleton):
    def __init__(self, endpoint: str, key_id: str, access_key: str, bucket: str):
        self.bucket = bucket
        self._sess = Session()
        self._args = {
            "endpoint_url": endpoint,
            "aws_access_key_id": key_id,
            "aws_secret_access_key": access_key
        }

    async def setAvatar(self, user_id: int, image: BytesIO, size: int) -> str:
        async with self._sess.client("s3", **self._args) as s3:
            image_hash = md5()
            image_hash.update(image.getvalue())
            image_hash = image_hash.hexdigest()

            image = Image.open(image)
            anim = imageFrames(image) > 1
            form = "gif" if anim else "png"
            image_hash = f"a_{image_hash}" if anim else image_hash
            size = (size, size)
            coro = resizeImage if not anim else resizeAnimImage
            data = await coro(image, size, form)
            await s3.upload_fileobj(BytesIO(data), self.bucket, f"avatars/{user_id}/{image_hash}.{form}")
        return image_hash
