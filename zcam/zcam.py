#
# file zcam.py
#
# SPDX-FileCopyrightText: (c) 2023 Michal Kielan
#
# SPDX-License-Identifier: MIT
#
""" Python wrapper for zcam API """

import os
from typing import List
from enum import Enum
import requests


class Mode(Enum):
    RECORD = "to_rec"
    PLAYBACK = "to_pb"
    STANDBY = "to_standby"


class ZCamError(Exception):
    """ZCam request error exception.

    Raised when request failed:

    """


class ZCam:
    def __init__(self, ip: str):
        self.ip = ip

    def __create_dir(self, dst: str):
        try:
            os.makedirs(dst)
        except FileExistsError:
            pass

    def __pull_video(self, dst: str, video: str, response: requests.Response):
        with open(os.path.join(dst, video), mode="wb") as fd:
            fd.write(response.content)

    def __request(self, path: str, timeout=None):
        url = f"http://{self.ip}/{path}"
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 404:
                raise ZCamError("Error 404 not found")

            return response
        except requests.exceptions.Timeout as exc:
            raise ZCamError("The request timed out") from exc

        except requests.exceptions.RequestException as exc:
            raise ZCamError(f"An error occurred: {exc}") from exc

    def get_dirs(self) -> List[str]:
        return self.__request("DCIM/").json()["files"]

    def get_files(self, path: str) -> List[str]:
        return self.__request(f"DCIM/{path}").json()["files"]

    def info(self):
        return self.__request("info").json()

    def mode(self, mode: Mode):
        self.__request(f"ctrl/mode?action={mode}")

    def pull(self, dst=".", **kwargs):
        self.__create_dir(dst)
        proxy = "proxy" if kwargs.get("proxy", False) else ""
        timeout = kwargs.get("timeout", None)
        for path in self.get_dirs():
            for video in self.get_files(path):
                url = f"DCIM/{os.path.join(path, proxy, video)}"
                response = self.__request(url, timeout)
                self.__pull_video(dst, video, response)

    def pull_video(self, to_download: str, dst=".", **kwargs):
        proxy = "proxy" if kwargs.get("proxy", False) else ""
        timeout = kwargs.get("timeout", None)
        for path in self.get_dirs():
            for video in self.get_files(path):
                if to_download == video:
                    self.__create_dir(dst)
                    url = f"DCIM/{os.path.join(path, proxy, video)}"
                    response = self.__request(url, timeout)
                    self.__pull_video(dst, video, response)
                    return
        raise ZCamError("File not found")

    def start(self):
        self.__request("ctrl/rec?action=start")

    def stop(self):
        self.__request("ctrl/rec?action=stop")
