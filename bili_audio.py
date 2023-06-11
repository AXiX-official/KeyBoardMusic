from bilibili_api import video, Credential, HEADERS, sync
import subprocess
import httpx
import os

credential = None

# os.environ["PATH"] += os.pathsep + os.path.abspath(r"ffmpeg-4.4-full_build\\bin\\ffmpeg.exe")


async def download_url(url: str, out: str, info: str):
    # 下载函数
    async with httpx.AsyncClient(headers=HEADERS) as sess:
        resp = await sess.get(url)
        length = resp.headers.get('content-length')
        with open(out, 'wb') as f:
            process = 0
            for chunk in resp.iter_bytes():
                if not chunk:
                    break

                process += len(chunk)
                # print(f'下载 {info} {process} / {length}')
                f.write(chunk)


async def download_bili_audio(bvid: str):
    # 实例化 Video 类
    v = video.Video(bvid=bvid, credential=credential)
    # 获取视频下载链接
    download_url_data = await v.get_download_url(0)
    # 解析视频下载信息
    detecter = video.VideoDownloadURLDataDetecter(data=download_url_data)
    streams = detecter.detect_best_streams()
    # 有 MP4 流 / FLV 流两种可能
    if detecter.check_flv_stream():
        # FLV 流下载
        await download_url(streams[0].url, "flv_temp.flv", "FLV 音视频流")
        # 转换文件格式
        os.system(f'ffmpeg -i flv_temp.flv video.mp4')
        # 删除临时文件
        os.remove("flv_temp.flv")
    else:
        # MP4 流下载
        await download_url(streams[1].url, "audio_temp.m4s", "音频流")
        command = f"ffmpeg -y -i audio_temp.m4s -vn -acodec libmp3lame -ac 2 -ab 128k audio.mp3"
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # 删除临时文件
        os.remove("audio_temp.m4s")

    # print('已下载为：video.mp4')


def download_baudio(bvid: str):
    sync(download_bili_audio(bvid))
