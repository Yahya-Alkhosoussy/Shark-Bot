import asyncio

from TikTokApi import TikTokApi


async def get_latest_videos():
    async with TikTokApi() as api:
        await api.create_sessions(num_sessions=1, sleep_after=3, headless=False)

        user = api.user("sharkocalypse")
        async for video in user.videos(count=10):
            print(f"Video ID: {video.id}")
            print(f"Description: {video.as_dict['desc']}")
            print(f"Link: https://www.tiktok.com/@sharkocalypse/video/{video.id}")
            print("-------------------------------------------------------------")


asyncio.run(get_latest_videos())
