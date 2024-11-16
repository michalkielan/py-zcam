# SPDX-License-Identifier: MIT
""" Python wrapper for zcam API """

import os
from datetime import datetime
from enum import Enum
from typing import List
import requests


class Mode(Enum):
    TO_PB = "to_pb"
    TO_REC = "to_rec"
    TO_STANDBY = "to_standby"


class Status(Enum):
    CAP = "cap"
    CAP_BURST = "cap_burst"
    CAP_TL_IDLE = "cap_tl_idle"
    CAP_TL_ING = "cap_tl_ing"
    PB = "pb"
    PB_ING = "pb_ing"
    PB_PAUSED = "pb_paused"
    REC = "rec"
    REC_ING = "rec_ing"
    REC_PAUSED = "rec_paused"
    REC_TL = "rec_tl"
    REC_TL_IDLE = "rec_tl_idle"
    REC_TL_ING = "rec_tl_ing"
    STANDBY = "standby"
    UNKNOWN = "unknown"


class ZCamError(Exception):
    """ZCam request error exception.

    Raised when request failed:

    """


class ZCam:
    DEFAULT_DIRECT_IP = "10.98.32.1"
    DEFAULT_TIMEOUT = 5

    def __init__(self, ip: str = DEFAULT_DIRECT_IP):
        self.__ip = ip

    def __create_dir(self, dst: str):
        try:
            os.makedirs(dst)
        except FileExistsError:
            pass

    def __get_setting(self, key: str):
        response = self.__request(f"ctrl/get?k={key}").json()
        self.__handle_error(response["code"])
        return response

    def __handle_error(self, code: int):
        if code != 0:
            raise ZCamError(f"Request failed, status: {code}")

    def __pull_video(self, dst: str, video: str, response: requests.Response):
        with open(os.path.join(dst, video), mode="wb") as fd:
            fd.write(response.content)

    def __request(self, path: str, timeout=DEFAULT_TIMEOUT):
        url = f"http://{self.__ip}/{path}"
        try:
            response = requests.get(url, timeout=timeout)
            status_code = response.status_code
            if status_code != 200:
                raise ZCamError(f"The request failed: {status_code}")
            return response

        except requests.exceptions.HTTPError as exc:
            raise ZCamError(f"An error occurred: {exc}") from exc

        except requests.exceptions.RequestException as exc:
            raise ZCamError(f"An error occurred: {exc}") from exc

        except requests.exceptions.ConnectionError as exc:
            raise ZCamError(f"An error occurred: {exc}") from exc

        except requests.exceptions.Timeout as exc:
            raise ZCamError("The request timed out") from exc

    def get_dirs(self) -> List[str]:
        return self.__request("DCIM/").json()["files"]

    def get_files(self, path: str) -> List[str]:
        return self.__request(f"DCIM/{path}").json()["files"]

    def info(self):
        return self.__request("info").json()

    def mode(self, mode: Mode):
        self.__request(f"ctrl/mode?action={mode}")

    def network_router(self):
        self.__request("ctrl/network?action=set&mode=Router")

    def network_direct(self):
        self.__request("ctrl/network?action=set&mode=Direct")

    def network_type(self) -> str:
        self.__request("ctrl/network?action=query").json()["value"]

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

    def reboot(self):
        self.__request("ctrl/reboot")

    def recording_start(self):
        self.__request("ctrl/rec?action=start")

    def recording_remain(self):
        self.__request("ctrl/rec?action=remain")

    def recording_stop(self):
        self.__request("ctrl/rec?action=stop")

    def session_start(self):
        self.__request("ctrl/session")

    def session_quit(self):
        self.__request("ctrl/session?action=quit")

    def get_setting_value(self, key: str):
        return self.__get_setting(key)["value"]

    def get_setting_opts(self, key: str):
        return self.__get_setting(key)["opts"]

    def is_setting_read_only(self, key: str):
        return self.__get_setting(key)["ro"] == 1

    def set_setting_value(self, key: str, value: str):
        response = self.__request(f"ctrl/set?{key}={value}").json()
        self.__handle_error(response["code"])

    def shutdown(self):
        self.__request("ctrl/shutdown")

    def status(self) -> Status:
        response = self.__request("ctrl/mode?action=query").json()
        self.__handle_error(response["code"])

        try:
            return Status(response["msg"])
        except ValueError as exc:
            raise ZCamError(f"Status not found: {exc}") from exc

    def sync_date(self):
        now = datetime.now().strftime("%Y-%m-%dtime=%H:%M:S")
        self.__request(f"datetime?date{now}")
