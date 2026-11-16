"""
Wi-Fi Sense V0.9.1
================
基于 Streamlit 的 Wi-Fi 感知智能监测与家庭监护平台（应用层）。

DEMO 版本：全部数据为模拟数据，未连接真实 ESP32、Wi-Fi 感知算法与温度传感器。
运行方式：streamlit run app.py
演示账号：admin / admin123（管理员）、family / family123（家属 P001）、family2 / family123（家属 P002）
"""

import base64
import hashlib
import hmac
import json
import math
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import contextmanager

import streamlit.components.v1 as components

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

APP_VERSION = "0.9.2"

st.set_page_config(
    page_title="Wi-Fi Sense | 智能监护平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="auto",
)

# ============================================================
# 常量与主题
# ============================================================

LEVEL_MAP = {0: "静止", 1: "活动", 2: "移动"}

THEMES = {
    "dark": {
        "bg": "#0C1117",
        "sidebar": "#11171F",
        "surface": "#151C25",
        "surface2": "#1B242E",
        "border": "#27313C",
        "text": "#E5EAF1",
        "muted": "#8A94A3",
        "accent": "#5B9ED1",
        "accent_hover": "#4A8CBE",
        "solid": "#356F9B",
        "solid_hover": "#2C5F86",
        "accent_bg": "rgba(91,158,209,0.10)",
        "accent_border": "rgba(91,158,209,0.22)",
        "ok": "#3FAE82",
        "ok_bg": "rgba(63,174,130,0.10)",
        "ok_border": "rgba(63,174,130,0.24)",
        "warn": "#D9994E",
        "warn_bg": "rgba(217,153,78,0.10)",
        "warn_border": "rgba(217,153,78,0.24)",
        "danger": "#D25C68",
        "danger_bg": "rgba(210,92,104,0.10)",
        "danger_border": "rgba(210,92,104,0.24)",
        "muted_bg": "rgba(138,148,163,0.08)",
        "muted_border": "rgba(138,148,163,0.18)",
        "header_bg": "rgba(12,17,23,0.92)",
        "hover_bg": "#1A2430",
        "nav_active_bg": "rgba(91,158,209,0.10)",
        "nav_active_border": "rgba(91,158,209,0.24)",
        "nav_active_text": "#CFE2F2",
        "btn": "#1A232D",
        "btn_hover": "#212C38",
        "btn_border": "#2C3742",
        "btn_text": "#DCE3EB",
        "input": "#161E27",
        "grid": "rgba(140,158,178,0.09)",
        "table_head": "#1A232E",
        "row_alt": "transparent",
        "shadow": "none",
        "container_bg": "#151C25",
        "template": "plotly_dark",
        "mode": "dark",
    },
    "light": {
        "bg": "#F4F5F7",
        "sidebar": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface2": "#F2F4F7",
        "border": "#E1E5EB",
        "text": "#171C24",
        "muted": "#6C7583",
        "accent": "#2E77AB",
        "accent_hover": "#26628F",
        "solid": "#24618F",
        "solid_hover": "#1E5279",
        "accent_bg": "rgba(46,119,171,0.06)",
        "accent_border": "rgba(46,119,171,0.18)",
        "ok": "#17795A",
        "ok_bg": "rgba(23,121,90,0.07)",
        "ok_border": "rgba(23,121,90,0.18)",
        "warn": "#A26A1F",
        "warn_bg": "rgba(162,106,31,0.07)",
        "warn_border": "rgba(162,106,31,0.18)",
        "danger": "#B24A56",
        "danger_bg": "rgba(178,74,86,0.06)",
        "danger_border": "rgba(178,74,86,0.18)",
        "muted_bg": "rgba(108,117,131,0.06)",
        "muted_border": "rgba(108,117,131,0.16)",
        "header_bg": "rgba(244,245,247,0.92)",
        "hover_bg": "#F0F3F7",
        "nav_active_bg": "rgba(46,119,171,0.08)",
        "nav_active_border": "rgba(46,119,171,0.20)",
        "nav_active_text": "#15486B",
        "btn": "#FFFFFF",
        "btn_hover": "#F5F8FB",
        "btn_border": "#DCE1E7",
        "btn_text": "#20262E",
        "input": "#FFFFFF",
        "grid": "rgba(40,60,85,0.08)",
        "table_head": "#F1F4F8",
        "row_alt": "transparent",
        "shadow": "none",
        "container_bg": "#FFFFFF",
        "template": "plotly_white",
        "mode": "light",
    },
}

THEMES["glass"] = {
    "bg": "#0A0C10",
    "sidebar": "rgba(10,12,16,0.52)",
    "surface": "rgba(255,255,255,0.055)",
    "surface2": "rgba(255,255,255,0.09)",
    "border": "rgba(255,255,255,0.13)",
    "text": "#F2F5F9",
    "muted": "rgba(226,232,240,0.64)",
    "accent": "#F08A4B",
    "accent_hover": "#E57936",
    "solid": "#C4602B",
    "solid_hover": "#AC5224",
    "accent_bg": "rgba(240,138,75,0.12)",
    "accent_border": "rgba(240,138,75,0.26)",
    "ok": "#54C79A",
    "ok_bg": "rgba(84,199,154,0.12)",
    "ok_border": "rgba(84,199,154,0.26)",
    "warn": "#E5B165",
    "warn_bg": "rgba(229,177,101,0.12)",
    "warn_border": "rgba(229,177,101,0.26)",
    "danger": "#E77B85",
    "danger_bg": "rgba(231,123,133,0.12)",
    "danger_border": "rgba(231,123,133,0.26)",
    "muted_bg": "rgba(255,255,255,0.05)",
    "muted_border": "rgba(255,255,255,0.12)",
    "header_bg": "rgba(10,12,16,0.30)",
    "hover_bg": "rgba(255,255,255,0.10)",
    "nav_active_bg": "rgba(240,138,75,0.14)",
    "nav_active_border": "rgba(240,138,75,0.30)",
    "nav_active_text": "#FFD9BE",
    "btn": "rgba(255,255,255,0.07)",
    "btn_hover": "rgba(255,255,255,0.11)",
    "btn_border": "rgba(255,255,255,0.16)",
    "btn_text": "#EDF1F6",
    "input": "rgba(255,255,255,0.06)",
    "grid": "rgba(255,255,255,0.08)",
    "table_head": "rgba(255,255,255,0.06)",
    "row_alt": "transparent",
    "shadow": "none",
    "container_bg": "rgba(255,255,255,0.05)",
    "template": "plotly_dark",
    "mode": "glass",
}

THEMES["glass_light"] = {
    "bg": "#EDE8E0",
    "sidebar": "rgba(255,255,255,0.55)",
    "surface": "rgba(255,255,255,0.62)",
    "surface2": "rgba(255,255,255,0.80)",
    "border": "rgba(22,30,40,0.12)",
    "text": "#1B2027",
    "muted": "rgba(28,36,46,0.62)",
    "accent": "#C4622A",
    "accent_hover": "#A94F1F",
    "solid": "#B8561F",
    "solid_hover": "#9C4718",
    "accent_bg": "rgba(196,98,42,0.10)",
    "accent_border": "rgba(196,98,42,0.22)",
    "ok": "#1E8E63",
    "ok_bg": "rgba(30,142,99,0.10)",
    "ok_border": "rgba(30,142,99,0.24)",
    "warn": "#A06615",
    "warn_bg": "rgba(160,102,21,0.10)",
    "warn_border": "rgba(160,102,21,0.24)",
    "danger": "#B04250",
    "danger_bg": "rgba(176,66,80,0.10)",
    "danger_border": "rgba(176,66,80,0.24)",
    "muted_bg": "rgba(22,30,40,0.05)",
    "muted_border": "rgba(22,30,40,0.12)",
    "header_bg": "rgba(255,255,255,0.42)",
    "hover_bg": "rgba(22,30,40,0.06)",
    "nav_active_bg": "rgba(196,98,42,0.12)",
    "nav_active_border": "rgba(196,98,42,0.26)",
    "nav_active_text": "#8A4318",
    "btn": "rgba(255,255,255,0.55)",
    "btn_hover": "rgba(255,255,255,0.80)",
    "btn_border": "rgba(22,30,40,0.14)",
    "btn_text": "#1B2027",
    "input": "rgba(255,255,255,0.68)",
    "grid": "rgba(22,30,40,0.10)",
    "table_head": "rgba(255,255,255,0.55)",
    "row_alt": "transparent",
    "shadow": "none",
    "container_bg": "rgba(255,255,255,0.46)",
    "template": "plotly_white",
    "mode": "glass_light",
}


NAV_ICONS = {
    "管理工作台": "dashboard",
    "人员档案管理": "groups",
    "设备管理": "router",
    "实时监测": "monitor_heart",
    "留意": "visibility",
    "告警中心": "warning",
    "历史数据": "history",
    "监测任务": "task_alt",
    "我的家庭": "home",
    "家庭成员": "face",
    "家里的设备": "router",
    "实时状态": "monitor_heart",
    "告警提醒": "notifications",
    "历史记录": "history",
    "设置": "settings",
    "系统配置": "tune",
    "家庭监护首页": "home",
    "实时监护画面": "monitor_heart",
    "我的告警": "warning",
    "历史告警记录": "history",
    "个人信息": "face",
}

NAV_ADMIN = [
    ("总览", ["管理工作台"]),
    ("资产", ["人员档案管理", "设备管理"]),
    ("监测", ["实时监测", "留意", "告警中心", "历史数据", "监测任务"]),
    ("系统", ["设置", "系统配置"]),
]

NAV_FAMILY = [
    ("总览", ["家庭监护首页", "实时监护画面", "留意"]),
    ("告警", ["我的告警", "历史告警记录"]),
    ("账户", ["个人信息", "设置"]),
]

DEVICE_STATUS_TONE = {"在线": "ok", "等待接入": "warn", "离线": "muted"}
TASK_STATUS_TONE = {"待启动": "accent", "运行中": "ok", "已暂停": "warn", "已结束": "muted"}


def _env_flag(name, default="1"):
    """环境变量开关，接入后端时只改 Deployment 的 env，无需重新打镜像。"""
    return os.environ.get(name, default).strip().lower() not in ("0", "false", "no", "off")


# WIFI_SENSE_DEMO_MODE=0 时数据全部走后端；WIFI_SENSE_SEED_DEMO=0 时不预置演示档案
DEMO_MODE = _env_flag("WIFI_SENSE_DEMO_MODE", "1")
SEED_DEMO = _env_flag("WIFI_SENSE_SEED_DEMO", "1")

# ============================================================
# 会话状态
# ============================================================

# 视觉风格单独存进地址栏参数：浏览器刷新（新会话）后据此恢复
THEME_PARAM = "ws_t"


def apply_theme(key, persist=True):
    """统一的主题写入口：改 session_state，同时把选择写进地址栏。"""
    if key not in THEMES:
        return
    st.session_state.theme = key
    if not persist:
        return
    try:
        if st.query_params.get(THEME_PARAM) != key:
            st.query_params[THEME_PARAM] = key
    except Exception:
        pass


def init_state():
    defaults = {
        "logged_in": False,
        "role": None,
        "username": None,
        "person_id": None,
        "page": "管理工作台",
        "theme": "glass",
        "density": "标准",
        "reduce_motion": False,
        "show_confidence": True,
        "show_device_detail": True,
        "auto_brief": True,
        "alerts": [],
        # 演示档案仅在 SEED_DEMO=1 时预置；接入后端后置 0，列表交给 GET /persons
        "persons": [
            {
                "id": "P001",
                "name": "张先生",
                "age": 72,
                "contact": "李女士",
                "phone": "13800000001",
                "room": "示范房间 A-01",
                "relation": "父亲",
            },
            {
                "id": "P002",
                "name": "王女士",
                "age": 68,
                "contact": "王先生",
                "phone": "13800000002",
                "room": "示范房间 A-02",
                "relation": "母亲",
            },
        ]
        if SEED_DEMO
        else [],
        # 演示设备同理由 SEED_DEMO 控制
        "devices": [
            {
                "id": "ESP32-WIFI-01",
                "name": "Wi-Fi 感知设备",
                "type": "ESP32",
                "room": "示范房间 A-01",
                "status": "在线",
                "enabled": True,
                "last_seen": datetime.now(),
            },
            {
                "id": "ESP32-TEMP-01",
                "name": "温度采集设备",
                "type": "ESP32",
                "room": "示范房间 A-01",
                "status": "等待接入",
                "enabled": True,
                "last_seen": None,
            },
            {
                "id": "ESP32-WIFI-02",
                "name": "Wi-Fi 感知设备",
                "type": "ESP32",
                "room": "示范房间 A-02",
                "status": "在线",
                "enabled": True,
                "last_seen": datetime.now(),
            },
        ]
        if SEED_DEMO
        else [],
        "params": {
            "activity_threshold": 0.65,
            "ambient_limit": 28.0,
            "surface_limit": 35.0,
            "abnormal_duration": 30,
        },
        "areas": ["示范房间 A-01", "示范房间 A-02"],
        "demo_df": None,
        "last_refresh": datetime.now(),
        "tasks": [],
        "api_error": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 新会话（含浏览器刷新）先从地址栏取回上次选定的风格
    if not st.session_state.get("_theme_restored"):
        saved = st.query_params.get(THEME_PARAM)
        if saved in THEMES:
            st.session_state.theme = saved
        st.session_state["_theme_restored"] = True


init_state()


# ============================================================
# 数据访问层（对接后端时唯一需要改动的部分）
# ============================================================
# 约定：页面只通过 source() 取数据与写数据，不直接读写 session_state。
# 后端就绪后：把 WIFI_SENSE_DEMO_MODE 置 0（环境变量，见 Deployment），
# 并在 HttpDataSource 里按 API_CONTRACT 实现具体调用，页面代码不用改。

API_CONTRACT = """
【认证】
  POST /api/v1/auth/login   {username, password} -> {token, role, person_id}
  POST /api/v1/auth/logout

【人员档案】
  GET    /api/v1/persons                    -> [{id,name,age,relation,room,contact,phone}]
  POST   /api/v1/persons                    {name,age,relation,room,contact,phone}
  PATCH  /api/v1/persons/{id}               {name?,age?,relation?,room?,contact?,phone?}
  DELETE /api/v1/persons/{id}

【设备】
  GET    /api/v1/devices
         -> [{id,name,type,room,status,enabled,last_seen,sensor_model,fw,rssi}]
  POST   /api/v1/devices                    {id,name,type,room,sensor_model}
  PATCH  /api/v1/devices/{id}               {name?,type?,room?,enabled?}
  DELETE /api/v1/devices/{id}
  POST   /api/v1/devices/{id}/reconnect     （模拟操作，后端返回 status=在线 时前端才置为在线）

【传感器与遥测上报】
  # 硬件：AHT20（I²C 0x38，温度 −40~+85℃ ±0.3℃，湿度 0~100%RH ±2%RH）
  #       BMP280（I²C 0x76/0x77，气压 300~1100hPa ±1hPa，需自动探测地址）
  # 采样 1Hz，上报周期 5 分钟（对齐前端 5 分钟粒度）；断网本地缓存 30 条，恢复后按 device_id+ts 幂等补传。
  # 时间戳统一 UTC 毫秒，不传本地时间字符串；显示层按 Asia/Shanghai 渲染。
  # 展示小数位：温度 1 位、湿度 1 位、气压 1 位（分辨率 ≠ 精度，不要显示 2 位小数）。
  POST /api/v1/telemetry
       {device_id, room, ts, seq, sensor:{model,fw}, env_temp_c, humidity_pct,
        pressure_hpa, surface_temp_c, rssi, battery}
       -> {accepted, device_id, ts}
  # 字段来源约束：
  #   env_temp_c      <- AHT20，映射页面「环境温度」
  #   humidity_pct    <- AHT20，暂只入库，页面暂无展示
  #   pressure_hpa    <- BMP280，暂只入库，页面暂无展示
  #   surface_temp_c  -> 当前无传感器来源，一律上报 null；页面显示「暂无传感器来源」，
  #                      禁止用 AHT20 温度顶替表面温度（不得伪造设备能力）
  # MQTT 可选：wisense/{room}/{device_id}/telemetry，payload 同上

【监测数据】
  GET    /api/v1/metrics?room=&from=&to=&limit=
         -> [{ts, room, ambient, surface, humidity, pressure, activity}]
            ambient=环境温度℃, surface=表面温度℃(可为 null), humidity=%RH(可为 null),
            pressure=hPa(可为 null), activity：0 静止 / 1 活动 / 2 移动

【告警】
  GET    /api/v1/alerts?status=&room=&limit=
         -> [{id,ts,level,category,message,room,status,handler,handled_at}]
  POST   /api/v1/alerts                     {level,category,message,room}
  POST   /api/v1/alerts/{id}/ack            {handler}

【监测任务】
  GET    /api/v1/tasks                      -> [{id,name,room,mode,duration,created_at,status}]
  POST   /api/v1/tasks                      {name,room,mode,duration}
  POST   /api/v1/tasks/{id}/start|pause|resume|end

【识别参数与区域】
  GET    /api/v1/settings  -> {activity_threshold,ambient_limit,surface_limit,abnormal_duration,areas}
  PUT    /api/v1/settings  {同结构}

【健康检查】
  GET    /api/v1/health    -> {version, mode, server_time, devices:[{id,last_seen,online}]}
  # 离线判定：last_seen 超过 3 个上报周期（15 分钟）判为离线，前端显示「离线/数据陈旧」
"""


class DataSourceError(Exception):
    """后端不可用 / 超时 / 返回错误时的统一异常，由 UI 层转成错误提示，不当作成功。"""


class BaseDataSource:
    """数据访问层接口。页面只依赖这里的语义，不依赖具体实现。"""

    def authenticate(self, username, password):
        raise NotImplementedError

    def series(self):
        """监测序列 DataFrame：时间 / 环境温度 / 表面温度 / 活动等级 / 活动状态 / 监测区域"""
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def alerts(self, person=None):
        raise NotImplementedError

    def pending_alerts(self, person=None):
        raise NotImplementedError

    def create_alert(self, level, category, message, room=None):
        raise NotImplementedError

    def acknowledge_alert(self, alert_id, handler=None):
        raise NotImplementedError

    def person_by_id(self, pid):
        raise NotImplementedError

    # ---- 写操作：页面必须经由这里，禁止直接改 session_state ----
    def create_person(self, person):
        raise NotImplementedError

    def update_person(self, pid, patch):
        raise NotImplementedError

    def delete_person(self, pid):
        raise NotImplementedError

    def create_device(self, device):
        raise NotImplementedError

    def update_device(self, dev_id, patch):
        raise NotImplementedError

    def delete_device(self, dev_id):
        raise NotImplementedError

    def set_device_enabled(self, dev_id, enabled):
        raise NotImplementedError

    def reconnect_device(self, dev_id):
        raise NotImplementedError

    def save_settings(self, params, areas=None):
        raise NotImplementedError

    def add_area(self, name):
        raise NotImplementedError

    def delete_area(self, name):
        raise NotImplementedError

    def create_task(self, task):
        raise NotImplementedError

    def task_action(self, task_id, action):
        raise NotImplementedError

    def hydrate(self):
        """HTTP 模式：把接口数据灌进会话缓存。演示模式无需实现。"""
        return None


class DemoDataSource(BaseDataSource):
    """演示实现：数据落在 session_state，行为与原版本完全一致。"""

    def authenticate(self, username, password):
        user = DEMO_USERS.get(username)
        if not user or user["password"] != password:
            return None
        return user

    def series(self):
        now = datetime.now()
        rng = random.Random(int(time_seed()))
        records = []
        activity = 0

        for i in range(36):
            if rng.random() < 0.30:
                activity = rng.choice([0, 1, 2])

            records.append(
                {
                    "时间": now - timedelta(minutes=5 * (35 - i)),
                    "环境温度": round(24.5 + rng.uniform(-0.5, 0.5), 1),
                    "表面温度": round(32.2 + rng.uniform(-0.7, 0.7), 1),
                    "活动等级": activity,
                    "活动状态": LEVEL_MAP[activity],
                    "监测区域": random.choice(st.session_state.areas),
                }
            )

        return pd.DataFrame(records)

    def refresh(self):
        old = st.session_state.demo_df
        new = self.series()

        if old is not None and not old.empty:
            merged = pd.concat([old, new.iloc[[-1]]], ignore_index=True)
            merged = merged.drop_duplicates(subset=["时间"], keep="last")
            st.session_state.demo_df = merged.tail(500).reset_index(drop=True)
        else:
            st.session_state.demo_df = new

        st.session_state.last_refresh = datetime.now()
        return st.session_state.demo_df

    def alerts(self, person=None):
        items = st.session_state.alerts
        if person:
            items = [a for a in items if a["room"] == person["room"]]
        return items

    def pending_alerts(self, person=None):
        return [a for a in self.alerts(person) if a["status"] == "待处理"]

    def create_alert(self, level, category, message, room=None):
        alert = {
            "id": "AL-" + uuid.uuid4().hex[:8].upper(),
            "time": datetime.now(),
            "level": level,
            "category": category,
            "message": message,
            "room": room or st.session_state.get("selected_area", st.session_state.areas[0]),
            "status": "待处理",
        }
        st.session_state.alerts.insert(0, alert)
        return alert

    def acknowledge_alert(self, alert_id, handler=None):
        for alert in st.session_state.alerts:
            if alert["id"] == alert_id:
                alert["status"] = "已确认"
                alert["handler"] = handler or st.session_state.username
                alert["handled_at"] = datetime.now()
                return alert
        return None

    def person_by_id(self, pid):
        for person in st.session_state.persons:
            if person["id"] == pid:
                return person
        return None

    # ---- 写操作：与原页面逻辑等价，这里只是搬迁 ----
    def create_person(self, person):
        st.session_state.persons.append(person)
        return person

    def update_person(self, pid, patch):
        person = self.person_by_id(pid)
        if person is not None:
            person.update(patch)
        return person

    def delete_person(self, pid):
        before = len(st.session_state.persons)
        st.session_state.persons = [
            p for p in st.session_state.persons if p["id"] != pid
        ]
        return before != len(st.session_state.persons)

    def create_device(self, device):
        st.session_state.devices.append(device)
        return device

    def update_device(self, dev_id, patch):
        device = next(
            (d for d in st.session_state.devices if d["id"] == dev_id), None
        )
        if device is not None:
            device.update(patch)
        return device

    def delete_device(self, dev_id):
        before = len(st.session_state.devices)
        st.session_state.devices = [
            d for d in st.session_state.devices if d["id"] != dev_id
        ]
        return before != len(st.session_state.devices)

    def set_device_enabled(self, dev_id, enabled):
        device = next(
            (d for d in st.session_state.devices if d["id"] == dev_id), None
        )
        if device is not None:
            device["enabled"] = bool(enabled)
        return device

    def reconnect_device(self, dev_id):
        device = next(
            (d for d in st.session_state.devices if d["id"] == dev_id), None
        )
        if device is not None:
            device["status"] = "在线"
            device["last_seen"] = datetime.now()
        return device

    def save_settings(self, params, areas=None):
        payload = dict(params or {})
        layout = payload.pop("zone_layout", None)
        st.session_state.params.update(payload)
        if layout is not None:
            st.session_state.zone_layout = dict(layout)
        if areas is not None:
            st.session_state.areas = list(areas)
        return dict(st.session_state.params)

    def add_area(self, name):
        if name in st.session_state.areas:
            return False
        st.session_state.areas.append(name)
        return True

    def delete_area(self, name):
        if name not in st.session_state.areas:
            return False
        st.session_state.areas.remove(name)
        return True

    def create_task(self, task):
        st.session_state.tasks.insert(0, task)
        return task

    def task_action(self, task_id, action):
        task = next((t for t in st.session_state.tasks if t["id"] == task_id), None)
        if task is None:
            return None
        if action == "start":
            task["status"] = "运行中"
            task["started_at"] = task["started_at"] or datetime.now()
        elif action == "pause":
            task["status"] = "已暂停"
        elif action == "resume":
            task["status"] = "运行中"
        elif action == "end":
            task["status"] = "已结束"
        else:
            raise DataSourceError(f"未知任务操作：{action}")
        return task


_API_CACHE = {}
_API_CACHE_TTL = float(os.environ.get("WIFI_SENSE_API_TTL", "8"))
_TZ = ZoneInfo("Asia/Shanghai")


def _cache_get(key):
    item = _API_CACHE.get(key)
    if not item:
        return None
    stamp, payload = item
    if time.time() - stamp > _API_CACHE_TTL:
        _API_CACHE.pop(key, None)
        return None
    return payload


def _cache_put(key, payload):
    _API_CACHE[key] = (time.time(), payload)


def _cache_clear():
    _API_CACHE.clear()


class HttpDataSource(BaseDataSource):
    """真实后端实现。所有请求走 WIFI_SENSE_API_BASE，失败一律抛 DataSourceError，不静默成功。"""

    def __init__(self, base_url=""):
        self.base_url = (base_url or "").rstrip("/")
        self.timeout = float(os.environ.get("WIFI_SENSE_API_TIMEOUT", "10"))

    # ---- 基础请求 ----
    def _token(self):
        return st.session_state.get("api_token") or ""

    def _request(self, method, path, payload=None, query=None, cache=False):
        if not self.base_url:
            raise DataSourceError(
                "未配置 WIFI_SENSE_API_BASE，无法访问后端（检查 Deployment 环境变量）"
            )

        url = self.base_url + path
        if query:
            qs = urllib.parse.urlencode(
                {k: v for k, v in query.items() if v not in (None, "")}
            )
            if qs:
                url = url + "?" + qs

        cache_key = (method, url, self._token())
        if cache:
            hit = _cache_get(cache_key)
            if hit is not None:
                return hit

        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Accept", "application/json")
        if body is not None:
            req.add_header("Content-Type", "application/json; charset=utf-8")
        token = self._token()
        if token:
            req.add_header("Authorization", "Bearer " + token)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:200]
            except Exception:  # noqa: BLE001 - 读响应体失败不影响主错误
                detail = ""
            if exc.code in (401, 403):
                st.session_state.api_token = None
                st.session_state.auth_expired = True
                st.session_state.logged_in = False
            raise DataSourceError(
                f"{method} {path} 返回 {exc.code}"
                + (f"：{detail}" if detail else "")
            )
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise DataSourceError(f"后端不可达：{method} {path}（{exc}）")

        parsed = None
        if raw.strip():
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = None

        if cache:
            _cache_put(cache_key, parsed)
        return parsed

    # ---- 时间换算 ----
    @staticmethod
    def _ms_to_dt(value):
        if value in (None, ""):
            return None
        try:
            return datetime.fromtimestamp(
                float(value) / 1000, tz=_TZ
            ).replace(tzinfo=None)
        except (TypeError, ValueError, OSError):
            return None

    @staticmethod
    def _dt_to_ms(value):
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return int(value)
        try:
            if value.tzinfo is None:
                value = value.replace(tzinfo=_TZ)
            return int(value.timestamp() * 1000)
        except (AttributeError, ValueError, OSError):
            return None

    # ---- 读 ----
    def authenticate(self, username, password):
        res = self._request(
            "POST", "/api/v1/auth/login",
            {"username": username, "password": password},
        ) or {}
        token = res.get("token")
        if token:
            st.session_state.api_token = token
        if not res:
            return None
        return {
            "role": res.get("role") or ("家属" if res.get("person_id") else "管理员"),
            "person_id": res.get("person_id"),
        }

    def series(self):
        rows = self._request(
            "GET", "/api/v1/metrics", query={"limit": 36}, cache=True
        ) or []
        records = []
        for row in rows:
            stamp = self._ms_to_dt(row.get("ts"))
            if stamp is None:
                continue
            level = int(row.get("activity") or 0)
            records.append(
                {
                    "时间": stamp,
                    "环境温度": row.get("ambient"),
                    "表面温度": row.get("surface"),
                    "活动等级": level,
                    "活动状态": LEVEL_MAP.get(level, "静止"),
                    "监测区域": row.get("room") or "",
                }
            )

        columns = ["时间", "环境温度", "表面温度", "活动等级", "活动状态", "监测区域"]
        if not records:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame(records).sort_values("时间").reset_index(drop=True)

    def refresh(self):
        df = self.series()
        st.session_state.demo_df = df
        st.session_state.last_refresh = datetime.now()
        return df

    def _map_alert(self, row):
        return {
            "id": row.get("id"),
            "time": self._ms_to_dt(row.get("ts")) or datetime.now(),
            "level": row.get("level") or "提示",
            "category": row.get("category") or "",
            "message": row.get("message") or "",
            "room": row.get("room") or "",
            "status": row.get("status") or "待处理",
            "handler": row.get("handler"),
            "handled_at": self._ms_to_dt(row.get("handled_at")),
        }

    def alerts(self, person=None):
        rows = self._request(
            "GET", "/api/v1/alerts",
            query={"room": person["room"] if person else None, "limit": 50},
            cache=True,
        ) or []
        return [self._map_alert(row) for row in rows]

    def pending_alerts(self, person=None):
        rows = self._request(
            "GET", "/api/v1/alerts",
            query={"status": "待处理", "room": person["room"] if person else None},
            cache=True,
        ) or []
        return [self._map_alert(row) for row in rows]

    def person_by_id(self, pid):
        if not pid:
            return None
        res = self._request(
            "GET", f"/api/v1/persons/{urllib.parse.quote(pid)}", cache=True
        ) or {}
        if not res.get("id"):
            return None
        return {
            "id": res.get("id"),
            "name": res.get("name") or "",
            "age": int(res.get("age") or 0),
            "contact": res.get("contact") or "",
            "phone": res.get("phone") or "",
            "room": res.get("room") or "",
            "relation": res.get("relation") or "家属",
        }

    # ---- 写：人员 ----
    def create_person(self, person):
        payload = {
            "name": person.get("name"),
            "age": int(person.get("age") or 0),
            "relation": person.get("relation"),
            "room": person.get("room"),
            "contact": person.get("contact"),
            "phone": person.get("phone"),
        }
        res = self._request("POST", "/api/v1/persons", payload) or {}
        _cache_clear()
        merged = dict(person)
        for key in ("id", "name", "age", "relation", "room", "contact", "phone"):
            if res.get(key) not in (None, ""):
                merged[key] = res[key]
        if merged.get("age") is not None:
            merged["age"] = int(merged["age"])
        st.session_state.persons.append(merged)
        return merged

    def update_person(self, pid, patch):
        res = self._request(
            "PATCH", f"/api/v1/persons/{urllib.parse.quote(pid)}", patch
        ) or {}
        _cache_clear()
        merged = {"id": pid}
        merged.update(patch or {})
        for key, value in (res or {}).items():
            if key in ("name", "age", "relation", "room", "contact", "phone"):
                merged[key] = value
        for item in st.session_state.persons:
            if item.get("id") == pid:
                item.update({k: v for k, v in merged.items() if k != "id"})
                break
        return merged

    def delete_person(self, pid):
        self._request("DELETE", f"/api/v1/persons/{urllib.parse.quote(pid)}")
        _cache_clear()
        st.session_state.persons = [
            p for p in st.session_state.persons if p.get("id") != pid
        ]
        return True

    # ---- 写：设备 ----
    def _map_device(self, row):
        return {
            "id": row.get("id"),
            "name": row.get("name") or "",
            "type": row.get("type") or "ESP32",
            "room": row.get("room") or "",
            "status": row.get("status") or "等待接入",
            "enabled": bool(row.get("enabled", True)),
            "last_seen": self._ms_to_dt(row.get("last_seen")),
            "sensor_model": row.get("sensor_model"),
            "fw": row.get("fw"),
            "rssi": row.get("rssi"),
        }

    def create_device(self, device):
        payload = {
            "id": device.get("id"),
            "name": device.get("name"),
            "type": device.get("type"),
            "room": device.get("room"),
            "sensor_model": device.get("sensor_model"),
        }
        res = self._request("POST", "/api/v1/devices", payload) or {}
        _cache_clear()
        merged = dict(device)
        merged.update(self._map_device({**device, **res}))
        st.session_state.devices.append(merged)
        return merged

    def update_device(self, dev_id, patch):
        res = self._request(
            "PATCH", f"/api/v1/devices/{urllib.parse.quote(dev_id)}", patch
        ) or {}
        _cache_clear()
        merged = {"id": dev_id}
        merged.update(patch or {})
        if res:
            mapped = self._map_device({**merged, **res})
            for key in ("name", "type", "room"):
                if mapped.get(key):
                    merged[key] = mapped[key]
        for item in st.session_state.devices:
            if item.get("id") == dev_id:
                item.update({k: v for k, v in merged.items() if k != "id"})
                break
        return merged

    def delete_device(self, dev_id):
        self._request("DELETE", f"/api/v1/devices/{urllib.parse.quote(dev_id)}")
        _cache_clear()
        st.session_state.devices = [
            d for d in st.session_state.devices if d.get("id") != dev_id
        ]
        return True

    def set_device_enabled(self, dev_id, enabled):
        return self.update_device(dev_id, {"enabled": bool(enabled)})

    def reconnect_device(self, dev_id):
        res = self._request(
            "POST", f"/api/v1/devices/{urllib.parse.quote(dev_id)}/reconnect"
        ) or {}
        _cache_clear()
        result = {
            "id": dev_id,
            "status": res.get("status") or "等待接入",
            "last_seen": self._ms_to_dt(res.get("last_seen")),
        }
        for item in st.session_state.devices:
            if item.get("id") == dev_id:
                item["status"] = result["status"]
                if result["last_seen"]:
                    item["last_seen"] = result["last_seen"]
                break
        return result

    # ---- 写：告警 ----
    def create_alert(self, level, category, message, room=None):
        payload = {
            "level": level,
            "category": category,
            "message": message,
            "room": room or st.session_state.get("selected_area"),
        }
        res = self._request("POST", "/api/v1/alerts", payload) or {}
        _cache_clear()
        if res.get("id"):
            alert = self._map_alert(res)
            st.session_state.alerts.insert(0, alert)
            return alert
        raise DataSourceError("后端未返回告警编号，无法更新页面状态")

    def acknowledge_alert(self, alert_id, handler=None):
        res = self._request(
            "POST",
            f"/api/v1/alerts/{urllib.parse.quote(str(alert_id))}/ack",
            {"handler": handler or st.session_state.get("username")},
        ) or {}
        _cache_clear()
        result = {
            "id": alert_id,
            "status": res.get("status") or "已确认",
            "handler": res.get("handler") or handler,
            "handled_at": self._ms_to_dt(res.get("handled_at")) or datetime.now(),
        }
        for item in st.session_state.alerts:
            if str(item.get("id")) == str(alert_id):
                item.update({k: v for k, v in result.items() if v is not None})
                break
        return result

    # ---- 写：参数与区域 ----
    def _settings_payload(self):
        current = dict(st.session_state.params or {})
        return {
            "activity_threshold": float(current.get("activity_threshold", 0.65)),
            "ambient_limit": float(current.get("ambient_limit", 28.0)),
            "surface_limit": float(current.get("surface_limit", 35.0)),
            "abnormal_duration": int(current.get("abnormal_duration", 30)),
            "areas": list(st.session_state.areas or []),
        }

    def _zone_layout_payload(self):
        layout = st.session_state.get("zone_layout") or {}
        return {
            str(name): {
                "x": float(rect.get("x", 0.0)),
                "y": float(rect.get("y", 0.0)),
                "w": float(rect.get("w", 0.0)),
                "h": float(rect.get("h", 0.0)),
                "height": float(rect.get("height", 0.08)),
            }
            for name, rect in layout.items()
            if isinstance(rect, dict)
        }

    def save_settings(self, params, areas=None):
        payload = self._settings_payload()
        payload.update(params or {})
        if areas is not None:
            payload["areas"] = list(areas)
        layout = self._zone_layout_payload()
        if layout:
            payload["zone_layout"] = layout
        try:
            res = self._request("PUT", "/api/v1/settings", payload) or {}
        except DataSourceError:
            if "zone_layout" not in payload:
                raise
            payload.pop("zone_layout", None)
            st.session_state["zone_layout_unsupported"] = True
            res = self._request("PUT", "/api/v1/settings", payload) or {}
        _cache_clear()
        st.session_state.params.update(
            {
                key: payload[key]
                for key in (
                    "activity_threshold",
                    "ambient_limit",
                    "surface_limit",
                    "abnormal_duration",
                )
            }
        )
        if payload["areas"]:
            st.session_state.areas = list(payload["areas"])
        return {
            **{k: payload[k] for k in payload if k != "areas"},
            "areas": list(payload["areas"]),
        }

    def add_area(self, name):
        if name in (st.session_state.areas or []):
            return False
        areas = list(st.session_state.areas or []) + [name]
        self.save_settings({}, areas=areas)
        return True

    def delete_area(self, name):
        if name not in (st.session_state.areas or []):
            return False
        areas = [a for a in st.session_state.areas if a != name]
        self.save_settings({}, areas=areas)
        return True

    # ---- 写：任务 ----
    def create_task(self, task):
        payload = {
            "name": task.get("name"),
            "room": task.get("room"),
            "mode": task.get("mode"),
            "duration": int(task.get("duration") or 0),
        }
        res = self._request("POST", "/api/v1/tasks", payload) or {}
        _cache_clear()
        merged = dict(task)
        if res.get("id"):
            merged["id"] = res["id"]
        if res.get("status"):
            merged["status"] = res["status"]
        if res.get("created_at"):
            merged["created_at"] = self._ms_to_dt(res["created_at"]) or task.get(
                "created_at"
            )
        st.session_state.tasks.insert(0, merged)
        return merged

    def task_action(self, task_id, action):
        if action not in ("start", "pause", "resume", "end"):
            raise DataSourceError(f"未知任务操作：{action}")
        res = self._request(
            "POST",
            f"/api/v1/tasks/{urllib.parse.quote(str(task_id))}/{action}",
        ) or {}
        _cache_clear()
        result = {
            "id": task_id,
            "status": res.get("status")
            or {"start": "运行中", "pause": "已暂停", "resume": "运行中", "end": "已结束"}[action],
            "started_at": self._ms_to_dt(res.get("started_at")),
        }
        for item in st.session_state.tasks:
            if str(item.get("id")) == str(task_id):
                item["status"] = result["status"]
                if result["started_at"]:
                    item["started_at"] = result["started_at"]
                break
        return result

    def _space_state(self):
        """可选端点 /api/v1/space/state：后端提供时接入 AI 语义与全局摘要。

        后端未实现（404）或不可达时只在本会话关闭该探测，不影响主流程；
        成功时写入 space_ai / space_summary / space_baseline_ready，供空间视图消费。
        """
        if st.session_state.get("space_state_off"):
            return
        try:
            doc = self._request("GET", "/api/v1/space/state", cache=False)
        except DataSourceError:
            st.session_state.space_state_off = True
            return
        if not isinstance(doc, dict):
            st.session_state.space_state_off = True
            return

        ai_map = {}
        for row in doc.get("rooms") or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            ai = row.get("ai")
            if not isinstance(ai, dict):
                continue
            level = ai.get("level") if ai.get("level") in _SPACE_AI_LEVELS else "info"
            confidence = ai.get("confidence")
            if not isinstance(confidence, (int, float)):
                confidence = row.get("confidence")
            if not isinstance(confidence, (int, float)):
                confidence = 0.0
            ai_map[str(row["id"])] = {
                "label": str(ai.get("label") or ""),
                "plain": str(ai.get("plain") or ""),
                "level": level,
                "action": str(ai.get("action") or ""),
                "facts": [
                    {"k": str(f.get("k") or ""), "v": str(f.get("v") or "")}
                    for f in (ai.get("facts") or [])
                    if isinstance(f, dict)
                ],
                "confidence": float(confidence),
                "source": "backend",
            }

        st.session_state.space_ai = ai_map
        st.session_state.space_summary = str((doc.get("global") or {}).get("summary") or "")
        if doc.get("baseline_ready") is not None:
            st.session_state.space_baseline_ready = bool(doc.get("baseline_ready"))

    # ---- 全量同步：接口 → 会话缓存 ----
    def hydrate(self):
        people = self._request("GET", "/api/v1/persons", cache=False) or []
        st.session_state.persons = [
            {
                "id": row.get("id"),
                "name": row.get("name") or "",
                "age": int(row.get("age") or 0),
                "contact": row.get("contact") or "",
                "phone": row.get("phone") or "",
                "room": row.get("room") or "",
                "relation": row.get("relation") or "家属",
            }
            for row in people
            if row.get("id")
        ]

        devices = self._request("GET", "/api/v1/devices", cache=False) or []
        st.session_state.devices = [
            self._map_device(row) for row in devices if row.get("id")
        ]

        settings = self._request("GET", "/api/v1/settings", cache=False) or {}
        for key in (
            "activity_threshold",
            "ambient_limit",
            "surface_limit",
            "abnormal_duration",
        ):
            if settings.get(key) is not None:
                st.session_state.params[key] = settings[key]
        areas = settings.get("areas") or []
        if areas:
            st.session_state.areas = list(areas)

        layout = settings.get("zone_layout")
        if isinstance(layout, dict) and layout:
            parsed_layout = {}
            for name, rect in layout.items():
                if not isinstance(rect, dict):
                    continue
                coords = {}
                for key in ("x", "y", "w", "h", "height"):
                    value = rect.get(key)
                    if isinstance(value, (int, float)):
                        coords[key] = float(value)
                if {"x", "y", "w", "h"} <= set(coords):
                    parsed_layout[str(name)] = coords
            if parsed_layout:
                st.session_state.zone_layout = parsed_layout

        tasks = self._request("GET", "/api/v1/tasks", cache=False) or []
        st.session_state.tasks = [
            {
                "id": row.get("id"),
                "name": row.get("name") or "",
                "room": row.get("room") or "",
                "mode": row.get("mode") or "持续监测",
                "duration": int(row.get("duration") or 0),
                "status": row.get("status") or "待启动",
                "created_at": self._ms_to_dt(row.get("created_at")) or datetime.now(),
                "started_at": self._ms_to_dt(row.get("started_at")),
            }
            for row in tasks
            if row.get("id")
        ]

        st.session_state.alerts = self.alerts()
        st.session_state.demo_df = self.series()
        self._space_state()
        return True



_DEMO_SOURCE = DemoDataSource()
_HTTP_SOURCE = HttpDataSource(os.environ.get("WIFI_SENSE_API_BASE", ""))


def source():
    return _DEMO_SOURCE if DEMO_MODE else _HTTP_SOURCE


# ============================================================
# 通用工具
# ============================================================


def esc(value):
    """转义动态文本，避免破坏 HTML 结构。"""
    import html as html_lib

    return html_lib.escape(str(value))


def get_palette():
    return THEMES.get(st.session_state.get("theme", "glass"), THEMES["glass"])


CSS_TEMPLATE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

:root {
    --bg: @bg;
    --sidebar: @sidebar;
    --surface: @surface;
    --surface2: @surface2;
    --border: @border;
    --text: @text;
    --muted: @muted;
    --accent: @accent;
    --ok: @ok;
    --warn: @warn;
    --danger: @danger;
    --shadow: @shadow;
    --r: 6px;
    --r-sm: 4px;
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
}

.stApp {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1640px;
    padding: 1.5rem 2.2rem 3rem !important;
}

/* 顶部工具栏（Streamlit 自带）做成透明，避免滚动/静止时压住面包屑与页面标题 */
header[data-testid="stHeader"],
[data-testid="stAppHeader"],
[data-testid="stToolbar"] {
    background: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
    backdrop-filter: none !important;
}

#MainMenu, footer {
    visibility: hidden;
}

/* ---------- 侧边栏 ---------- */

section[data-testid="stSidebar"] {
    background: var(--sidebar);
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.1rem;
}

/* 侧栏品牌与页标题齐平：抵消 Streamlit 侧栏头部（收起箭头那块）的占位高度 */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    margin-bottom: -22px !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 17px;
    font-weight: 650;
    letter-spacing: -0.3px;
    color: var(--text);
}

.brand-mark {
    width: 26px;
    height: 26px;
    border-radius: 6px;
    background: @accent_bg;
    border: 1px solid @accent_border;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: var(--accent);
    flex: 0 0 26px;
}

.brand-mark svg {
    width: 17px;
    height: 17px;
}

.brand-sub {
    margin-top: 6px;
    padding-left: 35px;
    font-size: 11.5px;
    letter-spacing: 0;
    color: var(--muted);
    text-transform: none;
}

.user-chip {
    margin-top: 15px;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
}

.user-name {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text);
}

.user-meta {
    margin-top: 5px;
    font-size: 11px;
    color: var(--muted);
    display: flex;
    align-items: center;
    gap: 6px;
}

.nav-label {
    margin: 16px 0 4px 2px;
    font-size: 11.5px;
    letter-spacing: 0;
    color: var(--muted);
    text-transform: none;
    opacity: 0.9;
}

.side-sep {
    margin: 14px 0 6px;
    border-top: 1px solid var(--border);
}

.side-foot {
    font-size: 10.5px;
    color: var(--muted);
    line-height: 1.8;
    letter-spacing: 0;
}

/* ---------- 侧边栏导航按钮 ---------- */

section[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start;
    text-align: left;
    background: transparent !important;
    border: 1px solid transparent !important;
    color: var(--muted) !important;
    font-size: 12.5px;
    font-weight: 500;
    min-height: 32px;
    padding: 5px 10px;
    border-radius: var(--r-sm);
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: @hover_bg !important;
    color: var(--text) !important;
    border-color: transparent !important;
}

section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    background: @nav_active_bg !important;
    border-color: @nav_active_border !important;
    color: @nav_active_text !important;
    font-weight: 600;
}

/* ---------- 页面头部 ---------- */

.ph-breadcrumb {
    font-size: 11.5px;
    letter-spacing: 0;
    color: var(--muted);
    text-transform: none;
    margin-bottom: 6px;
}

.ph-title {
    font-size: 19px;
    font-weight: 650;
    letter-spacing: -0.2px;
    line-height: 1.3;
    color: var(--text);
}

.ph-sub {
    margin-top: 5px;
    font-size: 12.5px;
    color: var(--muted);
    line-height: 1.6;
}

.demo-line {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 12px 0 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    font-size: 11.5px;
    color: var(--muted);
}

.demo-line .tag-muted {
    display: inline-block;
    padding: 1px 7px;
    border-radius: var(--r-sm);
    background: @muted_bg;
    color: var(--muted);
    font-size: 10.5px;
    letter-spacing: 0.4px;
}

.ph-meta {
    text-align: right;
    font-size: 11.5px;
    color: var(--muted);
    margin-bottom: 6px;
}

/* ---------- 指标卡片 ---------- */

.mcard {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 13px 15px 14px;
    box-sizing: border-box;
    min-height: 98px;
    display: flex;
    flex-direction: column;
}

.mcard-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--muted);
}

.mcard-value {
    margin-top: 6px;
    font-size: 22px;
    font-weight: 650;
    letter-spacing: -0.3px;
    line-height: 1.2;
    color: var(--text);
    font-variant-numeric: tabular-nums;
}

.mcard-hint {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--muted);
    line-height: 1.5;
    margin-bottom: 0;
    flex: 1;
    display: flex;
    align-items: flex-end;
}

.mcard.tone-danger .mcard-value { color: var(--danger); }
.mcard.tone-warn .mcard-value { color: var(--warn); }

/* ---------- 分区标题 ---------- */

.section {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    margin: 22px 0 10px;
}

.section-title {
    font-size: 13.5px;
    font-weight: 600;
    letter-spacing: 0;
    color: var(--text);
}

.section-note {
    font-size: 11.5px;
    color: var(--muted);
}

/* ---------- 状态标签 ---------- */

.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 7px;
    border-radius: var(--r-sm);
    font-size: 11px;
    font-weight: 500;
    line-height: 1.5;
    white-space: nowrap;
}

.badge-accent { color: @accent; background: @accent_bg; border-color: @accent_border; }
.badge-ok { color: @ok; background: @ok_bg; border-color: @ok_border; }
.badge-warn { color: @warn; background: @warn_bg; border-color: @warn_border; }
.badge-danger { color: @danger; background: @danger_bg; border-color: @danger_border; }
.badge-muted { color: var(--muted); background: @muted_bg; border-color: @muted_border; }

/* ---------- 空状态 ---------- */

.empty {
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
    padding: 32px 18px;
    text-align: center;
}

.empty-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
}

.empty-hint {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--muted);
    line-height: 1.7;
}

/* ---------- 列表行 ---------- */

.mlist {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 2px 14px;
}

.mrow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border);
}

.mrow:last-child {
    border-bottom: none;
}

.mrow-title {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text);
}

.mrow-meta {
    margin-top: 3px;
    font-size: 11px;
    color: var(--muted);
}

/* ---------- 告警 / 设备卡片内文 ---------- */

.acard-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 7px;
    flex-wrap: wrap;
}

.acard-cat {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text);
}

.acard-sub {
    font-size: 12px;
    color: var(--muted);
}

.acard-msg {
    font-size: 11.5px;
    color: var(--muted);
    line-height: 1.75;
}

.acard-meta {
    margin-top: 8px;
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.2px;
}

.dcard-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
    margin-top: 2px;
}

.dcard-meta {
    margin-top: 5px;
    font-size: 10.5px;
    color: var(--muted);
    line-height: 1.7;
}

.dcard-side {
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ---------- 状态横幅 ---------- */

.banner {
    display: flex;
    gap: 10px;
    align-items: flex-start;
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 13px 16px;
    background: var(--surface);
}

.banner-ok { border-color: @ok_border; background: @ok_bg; }
.banner-warn { border-color: @warn_border; background: @warn_bg; }
.banner-danger { border-color: @danger_border; background: @danger_bg; }

.banner-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-top: 8px;
    flex: 0 0 6px;
}

.banner-ok .banner-dot { background: @ok; }
.banner-warn .banner-dot { background: @warn; }
.banner-danger .banner-dot { background: @danger; }

.banner-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
}

.banner-text {
    margin-top: 6px;
    font-size: 11.5px;
    color: var(--muted);
    line-height: 1.75;
}

/* ---------- 键值区块 ---------- */

.kvb {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 14px 16px;
}

.kvb-title {
    font-size: 12px;
    letter-spacing: 0;
    text-transform: none;
    color: var(--muted);
    margin-bottom: 8px;
}

.kv {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 16px;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    font-size: 12.5px;
    color: var(--muted);
}

.kv:last-child {
    border-bottom: none;
}

.kv b {
    font-weight: 600;
    color: var(--text);
    text-align: right;
}

/* ---------- 时间线条目 ---------- */

.titem {
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
    padding: 12px 14px;
    margin-bottom: 8px;
}

.titem.danger {
    border-color: @danger_border;
    background: @danger_bg;
}

/* ---------- 区域标签 ---------- */

.chip {
    display: inline-flex;
    align-items: center;
    padding: 5px 10px;
    margin: 0 6px 6px 0;
    border: 1px solid var(--border);
    border-radius: var(--r-sm);
    background: var(--surface2);
    font-size: 11.5px;
    color: var(--text);
}

/* ---------- 数据表格 ---------- */

.twrap {
    max-height: 420px;
    overflow: auto;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
}

table.dfmt {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}

/* Streamlit 会给 markdown 里的表格加四边描边（用它的主题色，浅色主题下近黑），
   这里清掉，只保留主题里的横向细分隔线 */
table.dfmt,
table.dfmt th,
table.dfmt td {
    border-top: 0 !important;
    border-left: 0 !important;
    border-right: 0 !important;
}

table.dfmt thead th {
    position: sticky;
    top: 0;
    z-index: 2;
    background: @table_head;
    color: var(--muted);
    text-align: left;
    font-weight: 500;
    font-size: 11.5px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}

table.dfmt tbody td {
    padding: 10px 12px;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
    font-variant-numeric: tabular-nums;
    word-break: break-word;
}

table.dfmt tbody tr:nth-child(even) {
    background: @row_alt;
}

table.dfmt tbody tr:last-child td {
    border-bottom: none;
}

/* ---------- 按钮 ---------- */

.stButton > button,
.stDownloadButton > button {
    min-height: 32px;
    border-radius: var(--r-sm);
    border: 1px solid @btn_border !important;
    background-color: @btn !important;
    background-image: linear-gradient(@btn, @btn) !important;
    color: @btn_text !important;
    font-size: 12.5px;
    font-weight: 500;
    transition: background-color 0.16s ease, border-color 0.16s ease;
    box-shadow: none;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: @btn_hover !important;
    background-image: linear-gradient(@btn_hover, @btn_hover) !important;
    border-color: @btn_border !important;
    color: @btn_text !important;
}

[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
button[kind="primary"],
button[kind="primaryFormSubmit"] {
    background: @solid !important;
    border-color: @solid !important;
    color: #FFFFFF !important;
}

[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover {
    background: @solid_hover !important;
    border-color: @solid_hover !important;
    color: #FFFFFF !important;
}

/* ---------- 容器 / 表单 ---------- */

/* Streamlit 默认给 markdown 容器加 -16px 下边距。指标卡、表格卡这类自定义卡片会撑满
   整个容器，于是这块负边距正好抵掉上下相邻区块的 16px 间距，卡片会和下面一块贴死。
   只对「装着我们卡片」的容器归零，正文 markdown 不受影响。 */
[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.mcard),
[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(> .banner),
[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(> .ph-meta),
[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(> .twrap) {
    margin-bottom: 0 !important;
}

/* st.container(border=True) 的卡片：新版本 Streamlit 不再有 stVerticalBlockBorderWrapper，
   边框由 stVerticalBlock 自带（用的是 Streamlit 自己的主题色，浅色主题下会显成黑描边） */
[data-testid="stVerticalBlockBorderWrapper"],
.stVerticalBlock.st-emotion-cache-1n187a7 {
    background: @container_bg;
    border: 1px solid var(--border) !important;
    border-radius: var(--r);
    box-shadow: none;
}

/* 兜底：后面 Streamlit 版本换 class 名时，带边框的容器至少还沿用主题描边色 */
[data-testid="stMain"] [data-testid="stVerticalBlock"] {
    border-color: var(--border) !important;
}

[data-testid="stExpander"] details {
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface);
    box-shadow: none;
}

[data-testid="stExpander"] summary {
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
}

/* ---------- 输入控件 ---------- */

[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div {
    background: @input !important;
    border-color: var(--border) !important;
    border-radius: var(--r-sm) !important;
}

/* Streamlit 1.45+ 的输入控件结构 */
[data-testid="stTextInputRootElement"],
[data-testid="stNumberInputRootElement"],
[data-testid="stTextAreaRootElement"],
[data-testid="stSelectboxRootElement"],
[data-testid="stBaseSelectRootElement"],
[data-testid="stDateInputRootElement"] {
    background: @input !important;
    border-color: var(--border) !important;
    border-radius: var(--r-sm) !important;
    color: var(--text) !important;
}

input,
textarea,
[data-testid="stTextInputField"],
[data-testid="stNumberInputField"] {
    color: var(--text) !important;
    background: transparent !important;
}

/* 数字输入与下拉框（1.45+ 的 react-aria 结构） */
[data-testid="stNumberInputContainer"],
[data-testid="stSelectbox"] [role="group"] {
    background: @input !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
}

[data-testid="stSelectbox"] input[role="combobox"] {
    color: var(--text) !important;
    background: transparent !important;
}

[data-testid="stNumberInputStepUp"],
[data-testid="stNumberInputStepDown"],
[data-testid="stSelectbox"] button {
    color: var(--muted) !important;
}

input::placeholder,
textarea::placeholder {
    color: @muted !important;
    opacity: 0.85 !important;
}

/* 隐藏右上角 Deploy 按钮 */
[data-testid="stAppDeployButton"] {
    display: none !important;
}

[data-baseweb="popover"] [role="listbox"],
ul[role="listbox"] {
    background: var(--surface) !important;
    color: var(--text) !important;
}

label,
[data-testid="stWidgetLabel"] p {
    color: var(--muted) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
}

[data-testid="stForm"] {
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 14px 16px 6px;
    background: var(--surface);
}

/* ---------- 文本与提示 ---------- */

div[data-testid="stAlert"] {
    border-radius: 10px;
    font-size: 12px;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
}

hr {
    border-color: var(--border);
    margin: 1.1rem 0;
}

/* ---------- 登录页 ---------- */

.login-hero {
    min-height: 470px;
    padding: 34px 32px;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: @hero_bg;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}

.login-brand {
    font-size: 24px;
    font-weight: 650;
    color: var(--text);
    letter-spacing: -0.4px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.login-heading {
    margin-top: 34px;
    font-family: "Songti SC", "Source Han Serif SC", "Noto Serif SC", serif;
    font-size: clamp(26px, 2.9vw, 38px);
    line-height: 1.46;
    font-weight: 500;
    letter-spacing: 1.5px;
    color: var(--text);
}

.login-desc {
    margin-top: 14px;
    max-width: 24em;
    font-size: 13px;
    line-height: 1.8;
    color: var(--muted);
}

.login-foot {
    margin-top: auto;
    padding-top: 14px;
    border-top: 1px solid var(--border);
    font-size: 11px;
    letter-spacing: 0;
    color: var(--muted);
}

/* 登录页：一张安静的信道仪表 */
.login-hero {
    position: relative;
    overflow: hidden;
}

.hero-fx {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(76% 62% at 92% 2%, @accent_bg, transparent 62%),
        radial-gradient(62% 54% at 2% 100%, @accent_bg, transparent 68%);
}

.hero-grid {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image: radial-gradient(var(--border) 1px, transparent 1px);
    background-size: 22px 22px;
    opacity: 0.5;
    -webkit-mask-image: radial-gradient(74% 70% at 44% 36%, #000 20%, transparent 78%);
    mask-image: radial-gradient(74% 70% at 44% 36%, #000 20%, transparent 78%);
    animation: heroGrid 30s linear infinite;
}

@keyframes heroGrid {
    from { background-position: 0 0; }
    to { background-position: 22px 22px; }
}

.hero-body {
    position: relative;
    z-index: 1;
}

.hero-meter {
    position: relative;
    z-index: 1;
    margin-top: 30px;
    padding-top: 13px;
    border-top: 1px solid var(--border);
}

.meter-head {
    display: flex;
    justify-content: space-between;
    font-size: 10.5px;
    letter-spacing: 0.2px;
    color: var(--muted);
}

.meter-rows {
    display: flex;
    flex-direction: column;
    gap: 15px;
    margin-top: 14px;
}

.meter-row {
    display: flex;
    align-items: flex-end;
    gap: 10px;
}

.meter-tag {
    flex: 0 0 46px;
    font-size: 10px;
    letter-spacing: 0.2px;
    color: var(--muted);
    padding-bottom: 3px;
}

.meter-val {
    flex: 0 0 50px;
    text-align: right;
    font-size: 10px;
    letter-spacing: 0.2px;
    color: var(--muted);
    padding-bottom: 3px;
}

.meter-track {
    flex: 1 1 auto;
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 42px;
}

/* 一个信道一组柱：鼠标走到哪一段，哪一段亮起来，其余压暗 */
.band {
    position: relative;
    flex: 1 1 0;
    height: 100%;
    display: flex;
    align-items: flex-end;
    gap: 1px;
}

.band b {
    flex: 1 1 0;
    min-width: 1px;
    height: calc(var(--h1) * 1%);
    border-radius: 1px;
    background: var(--muted);
    opacity: 0.62;
    animation: meterWave var(--t) ease-in-out infinite;
    animation-delay: var(--d);
    transition: opacity 0.14s ease, background-color 0.14s ease;
}

.band.busy b {
    background: @accent;
    opacity: 0.9;
    box-shadow: 0 0 6px @accent_bg;
}

.band:hover b {
    background: var(--text);
    opacity: 0.95;
}

.band.busy:hover b {
    background: @accent;
    opacity: 1;
}

.meter-track:has(.band:hover) .band:not(:hover) b {
    opacity: 0.2;
}

.band-ch {
    position: absolute;
    left: 50%;
    top: calc(100% + 3px);
    transform: translateX(-50%);
    font-size: 9.5px;
    line-height: 1;
    color: var(--text);
    opacity: 0;
    transition: opacity 0.14s ease;
    pointer-events: none;
    white-space: nowrap;
}

.band:hover .band-ch {
    opacity: 0.9;
}

@keyframes meterWave {
    0%   { height: calc(var(--h1) * 1%); }
    17%  { height: calc(var(--h2) * 1%); }
    34%  { height: calc(var(--h3) * 1%); }
    51%  { height: calc(var(--h4) * 1%); }
    69%  { height: calc(var(--h5) * 1%); }
    86%  { height: calc(var(--h6) * 1%); }
    100% { height: calc(var(--h1) * 1%); }
}

/* 尊重系统的“减弱动效”设置 */
@media (prefers-reduced-motion: reduce) {
    .band b,
    .hero-grid {
        animation: none !important;
    }
}

.hero-feats {
    position: relative;
    z-index: 1;
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    gap: 11px;
}

.hf {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 12px;
    color: var(--muted);
    line-height: 1.6;
}

.hf-dot {
    flex: 0 0 auto;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: @accent;
    box-shadow: 0 0 0 3px @accent_bg;
}

/* 进入平台的粒子过渡（登录成功后 1.5 秒） */
.boot {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background: var(--bg);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 15px;
}

.boot-stage {
    position: relative;
    width: 220px;
    height: 220px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.boot-field {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 0;
    height: 0;
}

.boot-field i {
    position: absolute;
    left: 0;
    top: 0;
    width: var(--s);
    height: var(--s);
    margin-left: calc(var(--s) / -2);
    margin-top: calc(var(--s) / -2);
    border-radius: 50%;
    background: @accent;
    animation-name: bootMerge;
    animation-timing-function: cubic-bezier(0.22, 0.68, 0.24, 1);
    animation-fill-mode: forwards;
}

@keyframes bootMerge {
    0% { transform: translate(var(--x), var(--y)) scale(0.4); opacity: 0; }
    22% { opacity: 0.7; }
    62% { transform: translate(0, 0) scale(1); opacity: 0.95; }
    100% { transform: translate(0, 0) scale(0.2); opacity: 0; }
}

.boot-halo {
    position: absolute;
    width: 76px;
    height: 76px;
    border-radius: 50%;
    border: 1px solid @accent_border;
    box-shadow: 0 0 34px @accent_bg;
    animation: bootHalo 1.6s ease-out infinite;
}

.boot-core {
    position: absolute;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: @accent;
    box-shadow: 0 0 14px @accent, 0 0 30px @accent_bg;
    animation: bootCore 1.1s ease-in-out infinite alternate;
}

@keyframes bootCore {
    from { transform: scale(0.85); opacity: 0.55; }
    to { transform: scale(1.25); opacity: 1; }
}

@keyframes bootHalo {
    from { transform: scale(0.7); opacity: 0; }
    45% { opacity: 1; }
    to { transform: scale(1.4); opacity: 0; }
}

.boot-brand {
    position: relative;
    font-size: 15px;
    font-weight: 650;
    letter-spacing: 0.3px;
    color: var(--text);
}

.boot-tip {
    font-size: 11.5px;
    letter-spacing: 0.5px;
    color: var(--muted);
}

.boot-bar {
    width: 168px;
    height: 2px;
    border-radius: 2px;
    background: var(--border);
    overflow: hidden;
}

.boot-bar span {
    display: block;
    height: 100%;
    width: 34%;
    background: @accent;
    animation: bootBar 1.4s ease-in-out forwards;
}

@keyframes bootBar {
    from { transform: translateX(-110%); }
    to { transform: translateX(300%); }
}

.login-title {
    font-size: 19px;
    font-weight: 650;
    color: var(--text);
    letter-spacing: -0.2px;
}

.login-sub {
    margin-top: 5px;
    margin-bottom: 16px;
    font-size: 12px;
    color: var(--muted);
}

.login-note {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 10px 0 14px;
    font-size: 11px;
    color: var(--muted);
}

.role-card {
    padding: 12px 13px;
    border: 1px solid var(--border);
    border-radius: var(--r);
    background: var(--surface2);
    box-sizing: border-box;
}

.role-name {
    font-size: 12.5px;
    font-weight: 600;
    color: var(--text);
    margin-top: 5px;
}

.role-desc {
    font-size: 11px;
    color: var(--muted);
    margin-top: 3px;
}

.role-icon {
    color: var(--muted);
    line-height: 0;
}

.role-icon svg {
    width: 15px;
    height: 15px;
}

/* ---------- 小屏适配 ---------- */

@media (max-width: 900px) {
    .block-container {
        padding: 1rem 1rem 2rem !important;
    }

    .ph-title {
        font-size: 17px;
    }

    .mcard-value {
        font-size: 21px;
    }

    .login-hero {
        min-height: 320px;
        padding: 24px;
    }

    .login-heading {
        font-size: 25px;
        margin-top: 22px;
    }

    table.dfmt {
        font-size: 11px;
    }
}

/* ---------- 精修：交互反馈与控件一致性 ---------- */

.stButton > button:disabled,
.stDownloadButton > button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    border-color: var(--border) !important;
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible {
    outline: 2px solid @accent_border;
    outline-offset: 1px;
}

.stButton > button:active,
.stDownloadButton > button:active {
    background-color: @btn_border !important;
    background-image: linear-gradient(@btn_border, @btn_border) !important;
}

/* 破坏性操作只改外观，不改行为 */
[class*="st-key-delete"] button,
[class*="st-key-end_"] button,
[class*="st-key-endp_"] button {
    color: var(--danger) !important;
}

[class*="st-key-delete"] button:hover,
[class*="st-key-end_"] button:hover,
[class*="st-key-endp_"] button:hover {
    border-color: @danger_border !important;
    color: var(--danger) !important;
}

/* 表单：标签、控件与留白 */
[data-testid="stForm"] {
    padding: 15px 16px 10px;
}

[data-testid="stForm"] [data-testid="stVerticalBlock"] {
    gap: 0.55rem;
}

[data-testid="stWidgetLabel"] {
    margin-bottom: 2px;
}

[data-testid="stWidgetLabel"] p {
    font-size: 11.5px !important;
    font-weight: 500 !important;
    letter-spacing: 0;
}

[data-testid="stWidgetHelpText"] p,
[data-testid="stWidgetHelpText"] {
    font-size: 11px !important;
    color: var(--muted) !important;
}

/* 输入控件：统一高度与聚焦态 */
[data-testid="stNumberInputContainer"],
[data-testid="stSelectbox"] [role="group"],
[data-testid="stTextInputRootElement"],
[data-testid="stTextAreaRootElement"] {
    min-height: 36px;
}

[data-testid="stNumberInputContainer"]:focus-within,
[data-testid="stSelectbox"] [role="group"]:focus-within,
[data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stTextAreaRootElement"]:focus-within {
    border-color: @accent !important;
}

/* 侧边栏：导航密度 */
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
    gap: 0.35rem;
}

section[data-testid="stSidebar"] .nav-label {
    margin: 13px 0 6px 2px;
}

/* Streamlit 给 markdown 容器加了 -16px 下边距，会把下一项上提、导致 hover 底色压住分组标签 */
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.nav-label),
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.user-chip),
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.side-sep),
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]:has(.side-foot) {
    margin-bottom: 0 !important;
}

section[data-testid="stSidebar"] .stButton > button {
    padding: 6px 10px;
}

section[data-testid="stSidebar"] .user-chip {
    margin-top: 12px;
}

section[data-testid="stSidebar"] .side-sep {
    margin: 12px 0 6px;
}

/* 状态横幅：去掉圆点，改用左侧细条 */
.banner {
    padding: 12px 15px;
    border-left-width: 3px;
}

.banner-dot {
    display: none;
}

.banner-ok { border-left-color: @ok; }
.banner-warn { border-left-color: @warn; }
.banner-danger { border-left-color: @danger; }

.banner-title {
    font-size: 12.5px;
}

.banner-text {
    margin-top: 5px;
}

/* 展开面板 */
[data-testid="stExpander"] summary {
    padding: 10px 14px;
    background: @surface !important;
    color: var(--text);
}

[data-testid="stExpander"] summary:hover {
    background: @surface2 !important;
}

[data-testid="stExpander"] summary p {
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
}

/* 展开面板里的表单不再叠一层边框 */
[data-testid="stExpander"] [data-testid="stForm"] {
    border: none;
    background: transparent;
    padding: 2px 0 0;
}

.side-foot {
    margin-top: 2px;
}

[class*="st-key-logout"] {
    margin-top: 4px;
}

/* 开关开启态改用品牌色，避免与告警红撞色 */
[data-testid="stCheckbox"]:has(input:checked) label > div:not([data-testid]) {
    background: @solid !important;
}

/* 滑块：Streamlit 默认主色为红，转成品牌蓝（灰阶不受影响） */
[data-testid="stSlider"] {
    filter: hue-rotate(-150deg);
}

/* 单选仍走色相旋转 */
[data-testid="stRadio"] {
    filter: hue-rotate(-150deg);
}

/* 分段控件：默认未选中项是写死的白底，深色下会突然亮起一块，改成跟随主题 */
[data-testid="stButtonGroup"] button[data-variant="segmented_control"] {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
}

[data-testid="stButtonGroup"] button[data-variant="segmented_control"][aria-checked="true"] {
    background: @accent_bg !important;
    color: @accent !important;
    border-color: @accent_border !important;
    font-weight: 600;
}

/* ---------- 浮层与层叠修复 ---------- */

/* 下拉选项弹层：跟随主题，避免深色下白底深字 */
[data-testid="stSelectboxVirtualDropdown"] {
    background: @surface !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.16);
}

[data-testid="stSelectboxVirtualDropdown"] [role="option"] {
    color: var(--text) !important;
    font-size: 12.5px !important;
}

[data-testid="stSelectboxVirtualDropdown"] [role="option"]:hover,
[data-testid="stSelectboxVirtualDropdown"] [aria-selected="true"] {
    background: @surface2 !important;
    color: var(--text) !important;
}

/* 选中导航项在 hover 时保持高亮，不被通用 hover 覆盖 */
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover {
    background: @nav_active_bg !important;
    border-color: @nav_active_border !important;
    color: @nav_active_text !important;
}

/* 图表悬浮提示不被图表容器裁切 */
[data-testid="stPlotlyChart"] .js-plotly-plot {
    overflow: visible !important;
}

[data-testid="stElementContainer"]:has([data-testid="stPlotlyChart"]) {
    overflow: visible !important;
}

/* 表格行 hover 反馈（不改变行高） */
table.dfmt tbody tr:hover {
    background: @hover_bg !important;
}

/* 窄屏下换行的 columns 收紧行距 */
[data-testid="stHorizontalBlock"] {
    row-gap: 0.9rem;
}

/* 提示框 */
div[data-testid="stAlert"] {
    border-radius: var(--r);
    background: @surface2 !important;
    border: 1px solid var(--border) !important;
    border-left: 3px solid @accent !important;
    padding: 12px 14px !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) {
    border-left-color: @warn !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) {
    border-left-color: @danger !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) {
    border-left-color: @ok !important;
}

div[data-testid="stAlert"] [data-testid="stAlertContainer"],
div[data-testid="stAlert"] [data-testid="stAlertContentInfo"],
div[data-testid="stAlert"] [data-testid="stAlertContentWarning"],
div[data-testid="stAlert"] [data-testid="stAlertContentError"],
div[data-testid="stAlert"] [data-testid="stAlertContentSuccess"] {
    background: transparent !important;
    color: var(--text) !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] p * {
    font-size: 12px;
    line-height: 1.7;
    color: var(--text) !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentError"]) p {
    color: var(--danger) !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentWarning"]) p {
    color: var(--warn) !important;
}

div[data-testid="stAlert"]:has([data-testid="stAlertContentSuccess"]) p {
    color: var(--ok) !important;
}

/* 小屏再收一档 */
@media (max-width: 900px) {
    .section {
        margin: 18px 0 8px;
    }

    .mcard {
        min-height: 0;
    }

    .demo-line {
        margin: 10px 0 14px;
        padding-bottom: 10px;
    }

    /* 侧栏收起时展开按钮浮在左上角，给正文让出左侧空间，避免压住面包屑与标题 */
    [data-testid="stMainBlockContainer"] {
        padding-left: 2.6rem !important;
        padding-right: 1rem !important;
    }
}

/* ---------- 窄屏（≤900px，含手机与竖屏平板）：单列、可点、可滚 ---------- */

@media (max-width: 900px) {
    /* 正文边距收紧，把宽度让给内容 */
    /* 左侧留出侧栏展开按钮的位置，避免压住面包屑 */
    [data-testid="stMainBlockContainer"] {
        padding-left: 2.5rem !important;
        padding-right: 0.9rem !important;
        padding-top: 0.6rem !important;
    }

    /* 多列一律堆成单列：指标卡、房间卡、设置项不再并排挤成窄柱 */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 0.6rem !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 100% !important;
        width: 100% !important;
        min-width: 100% !important;
    }

    /* 徽章在窄屏不再被挤成竖排两字 */
    .badge,
    .demo-line .tag-muted {
        flex: 0 0 auto;
    }

    .demo-line {
        flex-wrap: wrap;
    }

    .mcard {
        min-height: 0;
        padding: 11px 12px 12px;
    }

    .mcard-value {
        font-size: 19px;
    }

    .section {
        margin: 16px 0 8px;
    }

    /* 表格：保底宽度 + 横向滚动，宁可滚动也不挤成竖排字 */
    .twrap {
        max-height: none;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }

    table.dfmt {
        min-width: 560px;
        font-size: 11.5px;
    }

    table.dfmt thead th,
    table.dfmt tbody td {
        padding: 8px 10px;
        white-space: nowrap;
    }

    /* 触摸目标不小于 44px */
    [data-testid="stButtonGroup"] button,
    .stButton > button,
    .stDownloadButton > button {
        min-height: 44px;
    }

    [data-testid="stCheckbox"] label,
    [data-testid="stToggle"] label {
        min-height: 44px;
        align-items: center;
    }

    /* 右上角「更新于」在窄屏左对齐，避免与刷新按钮互相挤压 */
    .ph-meta {
        text-align: left;
        margin-bottom: 2px;
    }

    /* 图表跟随容器宽度 */
    .js-plotly-plot {
        width: 100% !important;
    }
}
"""



def _glass_css():
    """玻璃态：照片底 + 磨砂卡片。底图内联成 data URI，避免额外静态路由。"""
    import base64 as _b
    mode = get_palette().get("mode")
    fname = "bg_light.jpg" if mode == "glass_light" else "bg.jpg"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", fname)
    try:
        uri = "data:image/jpeg;base64," + _b.b64encode(open(path, "rb").read()).decode()
    except Exception:
        uri = ""
    body = _GLASS_CSS_BODY
    if mode == "glass_light":
        body = body + _GLASS_LIGHT_SKIN
    body = body + _GLASS_MOTION
    return body.replace("@@BG@@", uri)


_GLASS_MOTION = """
/* ====== 动效层：Apple 风格（仅玻璃态注入，受「减少动效」统一关闭）====== */

@keyframes gx-rise {
    from { opacity: 0; transform: translate3d(0, 9px, 0) scale(0.995); }
    to   { opacity: 1; transform: none; }
}
@keyframes gx-drop {
    from { opacity: 0; transform: translate3d(0, -12px, 0); }
    to   { opacity: 1; transform: none; }
}
@keyframes gx-in {
    from { opacity: 0; }
    to   { opacity: 1; }
}

/* 卡片：入场轻微上浮，悬停像被手指按住再松开 */
.mcard, .dcard, .acard, .twrap, [data-testid="stMetric"],
[data-testid="stVerticalBlockBorderWrapper"] {
    animation: gx-rise .4s cubic-bezier(.32,.72,0,1) backwards;
    transition: transform .42s cubic-bezier(.32,.72,0,1),
                box-shadow .42s cubic-bezier(.32,.72,0,1),
                border-color .3s ease,
                background-color .3s ease;
    will-change: transform;
}
.mcard:hover, .dcard:hover, .acard:hover, [data-testid="stMetric"]:hover {
    transform: translate3d(0, -3px, 0) scale(1.004);
}
.mcard:active, .dcard:active, .acard:active {
    transform: scale(0.997);
    transition-duration: .16s;
}

/* 顶部胶囊：从上方落定 */
.st-key-topbar_shell {
    animation: gx-drop .48s cubic-bezier(.32,.72,0,1) both;
}

/* 按钮：按下回弹 */
[data-testid="stMain"] .stButton > button[kind],
[data-testid="stMain"] [data-testid="stBaseButton-secondary"],
[data-testid="stMain"] [data-testid="stBaseButton-primary"],
[data-testid="stMain"] [data-testid="stBaseButton-secondaryFormSubmit"],
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] .stButton > button[kind] {
    transition: transform .24s cubic-bezier(.32,.72,0,1),
                background-color .22s ease,
                border-color .22s ease,
                box-shadow .3s ease,
                color .2s ease !important;
}
[data-testid="stMain"] .stButton > button[kind]:hover,
[data-testid="stMain"] [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stMain"] [data-testid="stBaseButton-primary"]:hover,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[kind]:hover {
    transform: translate3d(0, -1px, 0) scale(1.014) !important;
}
[data-testid="stMain"] .stButton > button[kind]:active,
[data-testid="stMain"] [data-testid="stBaseButton-secondary"]:active,
[data-testid="stMain"] [data-testid="stBaseButton-primary"]:active,
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[kind]:active {
    transform: scale(0.963) !important;
    transition-duration: .09s !important;
}

/* 左侧 rail：图标按钮没有 .stButton 包装，按 testid 命中 */
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[data-testid^="stBaseButton"] {
    transition: transform .32s cubic-bezier(.34,1.32,.44,1),
                background-color .24s ease,
                box-shadow .3s ease,
                color .24s ease !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[data-testid="stBaseButton-secondary"]:hover {
    transform: scale(1.07) !important;
    transition-duration: .22s !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[data-testid="stBaseButton-primary"]:hover {
    transform: scale(1.05) !important;
    transition-duration: .28s !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] button[data-testid^="stBaseButton"]:active {
    transform: scale(0.93) !important;
    transition-duration: .1s !important;
}

/* 图表与表格：淡入，避免 rerun 时整块闪一下 */
[data-testid="stMain"] .js-plotly-plot,
[data-testid="stMain"] [data-testid="stDataFrame"],
[data-testid="stMain"] table.dfmt {
    animation: gx-in .5s ease both;
}

/* 输入类控件：聚焦时外发光代替硬描边 */
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stTextArea"] div[data-baseweb="textarea"] {
    transition: box-shadow .3s cubic-bezier(.32,.72,0,1), border-color .22s ease;
}
[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
    box-shadow: 0 0 0 3px rgba(240,138,75,0.18), 0 8px 22px rgba(0,0,0,0.2);
}

/* 分段控件与开关：状态切换走同一套缓动 */
[data-testid="stButtonGroup"] button,
[data-testid="stCheckbox"] > label,
[data-testid="stToggle"] > label {
    transition: background-color .26s cubic-bezier(.32,.72,0,1),
                color .2s ease,
                border-color .2s ease,
                transform .26s cubic-bezier(.32,.72,0,1);
}
[data-testid="stButtonGroup"] button:active {
    transform: scale(0.97);
}

/* 系统级“减弱动效”优先 */
@media (prefers-reduced-motion: reduce) {
    .mcard, .dcard, .acard, .twrap, [data-testid="stMetric"],
    [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-topbar_shell,
    [data-testid="stMain"] .js-plotly-plot,
    [data-testid="stMain"] [data-testid="stDataFrame"] {
        animation: none !important;
    }
}
"""

_GLASS_CSS_BODY = """
/* ====== 玻璃态覆盖层（palette mode=glass 时注入）====== */
html, body { background: #080A0E; }
[data-testid="stAppViewContainer"] {
    background-color: #080A0E;
    background-image:
        linear-gradient(180deg, rgba(8,10,14,0.55) 0%, rgba(8,10,14,0.78) 55%, rgba(8,10,14,0.92) 100%),
        radial-gradient(80% 50% at 14% 0%, rgba(255,150,80,0.13), transparent 64%),
        url("@@BG@@");
    background-size: cover, cover, cover;
    background-position: center, center, center;
    background-attachment: fixed, fixed, fixed;
    background-repeat: no-repeat;
}
[data-testid="stSidebar"] {
    background: rgba(10,12,16,0.62) !important;
    backdrop-filter: blur(26px) saturate(150%);
    -webkit-backdrop-filter: blur(22px) saturate(150%);
    border-right: 1px solid rgba(255,255,255,0.07);
}
[data-testid="stHeader"] {
    background: rgba(10,12,16,0.28) !important;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
}
.mcard, .dcard, .acard, .twrap, .login-card,
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"] details,
[data-testid="stMetric"] {
    background: linear-gradient(155deg, rgba(255,255,255,0.105), rgba(255,255,255,0.028)) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(18px) saturate(155%);
    -webkit-backdrop-filter: blur(18px) saturate(155%);
    box-shadow: 0 16px 38px rgba(0,0,0,0.26), inset 0 1px 0 rgba(255,255,255,0.10) !important;
    transition: transform .28s cubic-bezier(.2,.7,.3,1), box-shadow .28s ease, border-color .28s ease;
}
.mcard:hover, .dcard:hover, .acard:hover, [data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(255,255,255,0.24) !important;
    box-shadow: 0 24px 52px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.16) !important;
}

[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"],
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    color: #EDF1F6 !important;
    backdrop-filter: blur(12px) saturate(140%);
    -webkit-backdrop-filter: blur(12px) saturate(140%);
    border-radius: 12px !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.10);
    transition: background .22s ease, border-color .22s ease, transform .22s ease;
}
[data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-secondaryFormSubmit"]:hover,
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.26) !important;
    transform: translateY(-1px);
}
[data-testid="stBaseButton-primary"], .stButton > button[kind="primary"] {
    background: #F08A4B !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    color: #1A0F08 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 26px rgba(240,138,75,0.28), inset 0 1px 0 rgba(255,255,255,0.28);
}
[data-testid="stBaseButton-primary"]:hover, .stButton > button[kind="primary"]:hover {
    background: #E57936 !important;
    transform: translateY(-1px);
}

section[data-testid="stSidebar"] .stButton > button {
    border-radius: 12px !important;
}

/* ====== 窄图标栏（参考图的左侧 rail）====== */
section[data-testid="stSidebar"] {
    width: 68px !important;
    min-width: 68px !important;
    display: flex !important;
    align-items: center !important;
    background: transparent !important;
    border-right: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}
[data-testid="stSidebarResizeHandle"] {
    display: none !important;
    width: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding: 0 !important;
    gap: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: linear-gradient(168deg, rgba(255,255,255,0.15), rgba(255,255,255,0.055)) !important;
    border: none;
    border-radius: 999px;
    margin: 0 0 0 16px;
    padding: 16px 0 14px;
    height: fit-content !important;
    max-height: calc(100vh - 20px);
    backdrop-filter: blur(24px) saturate(155%);
    -webkit-backdrop-filter: blur(24px) saturate(155%);
    box-shadow: 0 18px 42px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.14);
    overflow: visible;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    display: none !important;
    padding: 0 !important;
    height: auto !important;
    min-height: 0 !important;
    justify-content: center !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button {
    width: 34px !important;
    height: 34px !important;
    min-height: 34px !important;
    border-radius: 999px !important;
    opacity: .55;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button:hover { opacity: 1; }

/* 品牌与头像 */
.rail-brand {
    display: flex;
    justify-content: center;
    padding: 2px 0 6px;
}
.rail-brand .brand-mark {
    width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.18);
    color: #F08A4B;
}
.rail-avatar {
    width: 34px; height: 34px;
    margin: 0 auto 10px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700;
    color: #14181D;
    background: linear-gradient(160deg, #F7D2B4, #E9A574);
    box-shadow: 0 6px 16px rgba(0,0,0,0.32);
}
.rail-sep {
    width: 22px; height: 1px;
    margin: 6px auto 7px;
    background: rgba(255,255,255,0.16);
}
.rail-sep-bottom { margin: 10px auto 4px; }
.rail-chip {
    display: none;
}

/* 图标按钮：42px 圆，文字隐藏，靠 tooltip 说明 */
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    width: 42px !important;
    height: 42px !important;
    min-height: 42px !important;
    max-width: 42px !important;
    padding: 0 !important;
    margin: 3px auto !important;
    border-radius: 999px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    box-shadow: none !important;
    color: rgba(242,245,249,0.72) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.10) !important;
    border-color: rgba(255,255,255,0.14) !important;
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] {
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    padding: 0 !important;
    margin: -1px !important;
    overflow: hidden !important;
    clip: rect(0 0 0 0) !important;
    white-space: nowrap !important;
    border: 0 !important;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] [data-testid="stIconMaterial"] {
    font-size: 21px !important;
    margin: 0 !important;
    line-height: 1 !important;
}
section[data-testid="stSidebar"] span[data-testid="stTooltipHoverTarget"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
}
/* 当前页：白色实心圆 + 深色图标 */
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"],
section[data-testid="stSidebar"] button[kind="primary"] {
    background: #F6F2EC !important;
    border: 1px solid rgba(255,255,255,0.9) !important;
    color: #14181D !important;
    box-shadow: 0 10px 26px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.9) !important;
}
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover,
section[data-testid="stSidebar"] button[kind="primary"]:hover {
    background: #FFFFFF !important;
    color: #0F1216 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.10) !important;
}

/* 原生控件：下拉、输入框、滑块都改成玻璃片 */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stNumberInput"] div[data-baseweb="input"],
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] div[data-baseweb="input"] {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    border-radius: 12px !important;
    backdrop-filter: blur(12px) saturate(140%);
    -webkit-backdrop-filter: blur(12px) saturate(140%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
[data-testid="stTextInput"] div[data-baseweb="input"]:hover {
    border-color: rgba(255,255,255,0.26) !important;
}
/* 自定义组件（空间视图 iframe）切成卡片圆角 */
[data-testid="stIFrame"], [data-testid="stCustomComponentV1"] iframe {
    border-radius: 18px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    overflow: hidden !important;
    box-shadow: 0 16px 38px rgba(0,0,0,0.26);
}


/* ====== 顶部细条（头像 + 信息胶囊 + 刷新圆钮）====== */
.st-key-topbar_shell {
    border-radius: 999px !important;
    background: linear-gradient(160deg, rgba(255,255,255,0.10), rgba(255,255,255,0.03)) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
    box-shadow: 0 10px 28px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    padding: 5px 7px !important;
    margin-bottom: 2px;
}
.topbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-left: 6px;
}
.tb-avatar {
    width: 28px; height: 28px;
    flex: 0 0 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; font-weight: 700;
    color: #14181D;
    background: linear-gradient(160deg, #F7D2B4, #E9A574);
}
.tb-user { display: flex; flex-direction: column; line-height: 1.25; }
.tb-name { font-size: 12.5px; font-weight: 600; color: var(--text); }
.tb-role { font-size: 10.5px; color: var(--muted); }
.tb-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    border-radius: 999px;
    background: rgba(255,255,255,0.055);
    border: 1px solid rgba(255,255,255,0.10);
    color: rgba(242,245,249,0.68);
    font-size: 12px;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"] {
    border-radius: 999px !important;
    min-height: 34px !important;
    height: 34px !important;
    font-size: 12px;
}

/* 顶栏内部元素归零、垂直居中 */
.st-key-topbar_shell [data-testid="stVerticalBlock"],
.st-key-topbar_shell [data-testid="stColumn"],
.st-key-topbar_shell [data-testid="stElementContainer"],
.st-key-topbar_shell [data-testid="stMarkdown"],
.st-key-topbar_shell [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
    gap: 0 !important;
    min-height: 0 !important;
}
.st-key-topbar_shell [data-testid="stHorizontalBlock"] {
    align-items: center !important;
    min-height: 0 !important;
}
.st-key-topbar_shell [data-testid="stColumn"] {
    display: flex !important;
    align-items: center !important;
}
.st-key-topbar_shell button {
    height: 32px !important;
    min-height: 32px !important;
    margin: 0 !important;
}
.ph-title { margin-top: 18px; }

[data-testid="stPlotlyChart"] {
    background: rgba(255,255,255,0.075) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(18px) saturate(155%);
    -webkit-backdrop-filter: blur(18px) saturate(155%);
    box-shadow: 0 14px 34px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    overflow: hidden;
}
"""


_GLASS_LIGHT_SKIN = """
/* ====== 浅色玻璃：在深色结构之上覆写配色 ====== */
html, body { background: #EDE8E0; }
[data-testid="stAppViewContainer"] {
    background-color: #EDE8E0;
    background-image:
        linear-gradient(180deg, rgba(250,247,242,0.44) 0%, rgba(246,242,236,0.62) 55%, rgba(242,238,232,0.78) 100%),
        radial-gradient(70% 46% at 16% 0%, rgba(255,214,178,0.22), transparent 62%),
        url("@@BG@@");
}
[data-testid="stHeader"] {
    background: rgba(252,250,246,0.55) !important;
}
[data-testid="stSidebar"] {
    background: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: linear-gradient(168deg, rgba(255,255,255,0.66), rgba(255,255,255,0.34)) !important;
    box-shadow: 0 14px 34px rgba(28,36,46,0.14), inset 0 1px 0 rgba(255,255,255,0.85) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.72) !important;
    border-color: rgba(22,30,40,0.16) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    background: #C4622A !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 16px rgba(176,80,32,0.30) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"] {
    color: #FFFFFF !important;
}
.st-key-topbar_shell {
    background: linear-gradient(160deg, rgba(255,255,255,0.70), rgba(255,255,255,0.36)) !important;
    border: 1px solid rgba(255,255,255,0.70) !important;
    box-shadow: 0 10px 26px rgba(28,36,46,0.12), inset 0 1px 0 rgba(255,255,255,0.9) !important;
}
.tb-pill {
    background: rgba(255,255,255,0.58);
    border: 1px solid rgba(22,30,40,0.10);
    color: rgba(28,36,46,0.66);
}
.tb-avatar {
    background: linear-gradient(160deg, #E7A97C, #C4622A);
    color: #FFF7F0;
}
[data-testid="stMain"] button[data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,0.60) !important;
    border: 1px solid rgba(22,30,40,0.14) !important;
    color: #1B2027 !important;
}
.mcard, .dcard, .acard, .twrap, .login-card,
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stExpander"] details,
[data-testid="stMetric"] {
    background: linear-gradient(155deg, rgba(255,255,255,0.72), rgba(255,255,255,0.42)) !important;
    border: 1px solid rgba(255,255,255,0.80) !important;
    box-shadow: 0 0 0 1px rgba(22,30,40,0.06), 0 12px 28px rgba(28,36,46,0.10), inset 0 1px 0 rgba(255,255,255,0.95) !important;
}
.mcard:hover, .dcard:hover, .acard:hover, [data-testid="stMetric"]:hover {
    box-shadow: 0 16px 32px rgba(28,36,46,0.16), inset 0 1px 0 rgba(255,255,255,1) !important;
}
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"],
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.58) !important;
    border: 1px solid rgba(22,30,40,0.14) !important;
    color: #1B2027 !important;
    box-shadow: 0 6px 16px rgba(28,36,46,0.08) !important;
}
[data-testid="stCompare"] { }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
[data-testid="stTextInput"] div[data-baseweb="input"],
[data-testid="stNumberInput"] div[data-baseweb="input"],
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] div[data-baseweb="input"] {
    background: rgba(255,255,255,0.68) !important;
    border: 1px solid rgba(22,30,40,0.14) !important;
    color: #1B2027 !important;
}
[data-testid="stPlotlyChart"] {
    background: linear-gradient(160deg, rgba(255,255,255,0.70), rgba(255,255,255,0.40)) !important;
    border: 1px solid rgba(255,255,255,0.80) !important;
    box-shadow: 0 12px 28px rgba(28,36,46,0.10), inset 0 1px 0 rgba(255,255,255,0.95) !important;
}
[data-testid="stIFrame"], [data-testid="stCustomComponentV1"] iframe {
    background: rgba(255,255,255,0.70) !important;
    box-shadow: 0 12px 28px rgba(28,36,46,0.12) !important;
}

/* rail：浅色底板上的图标与选中态（放在皮肤最末尾，压过结构层的硬编码白色） */
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] {
    color: #2A3239 !important;
    -webkit-text-fill-color: #2A3239 !important;
}
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] [data-testid="stIconMaterial"] {
    color: #2A3239 !important;
    -webkit-text-fill-color: #2A3239 !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: #C4622A !important;
    border: 1px solid rgba(255,255,255,0.55) !important;
    box-shadow: 0 10px 24px rgba(148,68,28,0.34) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] [data-testid="stIconMaterial"] {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover,
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
    background: #B4551F !important;
    border-color: rgba(255,255,255,0.55) !important;
    box-shadow: 0 10px 24px rgba(148,68,28,0.38) !important;
}
section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover [data-testid="stIconMaterial"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover [data-testid="stIconMaterial"] {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
/* 勾选框：白底上要有可见的轨道与滑块 */
[data-testid="stCheckbox"] > label > div:not([data-testid]) {
    background: rgba(27, 32, 39, 0.12) !important;
    border-radius: 999px !important;
}
[data-testid="stCheckbox"] > label > div:not([data-testid]) > div {
    background: #FFFFFF !important;
    box-shadow: 0 1px 3px rgba(20, 26, 34, 0.22) !important;
}

.stButton button:disabled,
.stButton button[disabled] {
    background: rgba(255,255,255,0.46) !important;
    border: 1px dashed rgba(22,30,40,0.16) !important;
    color: rgba(28,36,46,0.52) !important;
    box-shadow: none !important;
}
.st-key-theme_quick button,
.st-key-theme_quick button [data-testid="stIconMaterial"],
.st-key-logout_btn button,
.st-key-logout_btn button [data-testid="stIconMaterial"] {
    color: #2A3239 !important;
    -webkit-text-fill-color: #2A3239 !important;
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}
"""

def inject_css():
    palette = get_palette()
    if palette["mode"] == "glass":
        palette["hero_bg"] = "linear-gradient(160deg, rgba(255,255,255,0.10), rgba(255,255,255,0.02))"
    elif palette["mode"] == "glass_light":
        palette["hero_bg"] = "linear-gradient(160deg, rgba(255,255,255,0.62), rgba(255,255,255,0.28))"
    elif palette["mode"] == "dark":
        palette["hero_bg"] = "linear-gradient(165deg, #141C26, #0B1016)"
    else:
        palette["hero_bg"] = "linear-gradient(165deg, #FFFFFF, #EDF1F5)"

    css = CSS_TEMPLATE
    for key in sorted(palette.keys(), key=len, reverse=True):
        css = css.replace("@" + key, palette[key])

    if st.session_state.get("density") == "紧凑":
        css += """
.mcard { padding: 10px 12px 11px; }
.section { margin: 14px 0 7px; }
.acard-msg { line-height: 1.62; }
"""
    if st.session_state.get("reduce_motion"):
        css += """
*, *::before, *::after { transition: none !important; animation: none !important; }
"""

    if palette.get("mode") in ("glass", "glass_light"):
        css += _glass_css()

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# ============================================================
# 图表主题
# ============================================================


def apply_chart_theme(fig, height=300):
    palette = get_palette()

    fig.update_layout(
        template=palette["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, Noto Sans SC, sans-serif",
            color=palette["muted"],
            size=11,
        ),
        height=height,
        margin=dict(l=10, r=10, t=24, b=8),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10.5, color=palette["muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=palette["surface2"],
            bordercolor=palette["border"],
            font=dict(color=palette["text"], size=11),
        ),
        colorway=[palette["accent"], palette["warn"], palette["ok"], palette["danger"]],
    )

    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linecolor=palette["border"],
        linewidth=1,
        ticks="",
        zeroline=False,
        tickfont=dict(color=palette["muted"], size=10),
        title_font=dict(color=palette["muted"], size=10),
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor=palette["grid"],
        griddash="dot",
        zeroline=False,
        showline=False,
        ticks="",
        tickfont=dict(color=palette["muted"], size=10),
        title_font=dict(color=palette["muted"], size=10),
    )

    return fig


def plot_chart(fig):
    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False, "responsive": True},
    )


def activity_figure(df, height=300, markers=False):
    palette = get_palette()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["时间"],
            y=df["活动等级"],
            mode="lines+markers" if markers else "lines",
            name="活动等级",
            line=dict(color=palette["accent"], width=2.2, shape="hv"),
            marker=dict(size=4.5, color=palette["accent"]),
            fill="tozeroy",
            fillcolor=palette["accent_bg"],
            hovertemplate="%{x|%H:%M} · %{y}<extra></extra>",
        )
    )

    fig.update_yaxes(
        tickvals=[0, 1, 2],
        ticktext=["静止", "活动", "移动"],
        range=[-0.25, 2.35],
    )
    fig.update_xaxes(tickformat="%H:%M")

    return apply_chart_theme(fig, height)


def temperature_figure(df, height=300):
    palette = get_palette()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["时间"],
            y=df["环境温度"],
            mode="lines",
            name="环境温度",
            line=dict(color=palette["accent"], width=1.8),
            hovertemplate="%{x|%H:%M} · %{y:.1f} °C<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["时间"],
            y=df["表面温度"],
            mode="lines",
            name="表面温度",
            line=dict(color=palette["warn"], width=1.8),
            hovertemplate="%{x|%H:%M} · %{y:.1f} °C<extra></extra>",
        )
    )
    fig.update_xaxes(tickformat="%H:%M")

    return apply_chart_theme(fig, height)


# ============================================================
# DEMO 数据
# ============================================================


def generate_data():
    """兼容旧调用：数据来源统一走数据访问层。"""
    try:
        return source().series()
    except DataSourceError as exc:
        data_error(exc, "监测数据加载失败，先展示上一次拿到的数据。")
        return st.session_state.demo_df


def time_seed():
    import time

    return time.time() // 20


if st.session_state.demo_df is None:
    try:
        st.session_state.demo_df = generate_data()
    except DataSourceError as exc:
        # 后端不可用时不留空白追踪栈：给出空数据 + 记录错误，页面走空态与错误提示
        st.session_state.demo_df = pd.DataFrame(
            columns=["时间", "环境温度", "表面温度", "活动等级", "活动状态", "监测区域"]
        )
        st.session_state.api_error = str(exc)


def refresh_data():
    """刷新入口：带加载态与失败兜底，失败时保留上一次成功的数据，不假装成功。"""
    try:
        with loading_state("正在刷新监测数据…"):
            series = source().refresh()
            source().hydrate()
            return series
    except DataSourceError as exc:
        data_error(exc, "刷新失败，页面继续展示上一次成功获取的数据。")
        return st.session_state.demo_df


# ============================================================
# 告警系统
# ============================================================


def create_alert(level, category, message, room=None):
    return source().create_alert(level, category, message, room=room)


def acknowledge_alert(alert_id):
    return source().acknowledge_alert(alert_id)


def get_pending_alerts(person=None):
    try:
        return source().pending_alerts(person)
    except DataSourceError as exc:
        data_error(exc, "待处理告警数量获取失败，先按本地记录统计。")
        return [a for a in st.session_state.alerts if a.get("status") == "待处理"]


# ============================================================
# 认证
# ============================================================

# 演示账号：正式部署需替换为数据库认证与安全密码存储
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "管理员", "person_id": None},
    "family": {"password": "family123", "role": "家属", "person_id": "P001"},
    "family2": {"password": "family123", "role": "家属", "person_id": "P002"},
}


# ---------- 会话持久化：浏览器刷新后保持登录 ----------
# Streamlit 的 session_state 与 WebSocket 绑定，按 F5 会新建会话、状态全丢，
# 表现为“刷新就退回登录页”。这里把一份签名后的凭证写进 URL query，
# 刷新时读回来重建登录态，并顺带重新拉一次数据，效果与普通后台网页一致。
# 注意：凭证出现在地址栏，仅适用于本地/DEMO 阶段；接正式后端后应改为
# /auth/login 下发 token + /auth/me 校验，并把 PERSIST_LOGIN 关掉或换实现。
PERSIST_LOGIN = True
# 生产部署请用环境变量注入独立密钥，避免沿用内置默认值
SESSION_SECRET = os.environ.get("WS_SESSION_SECRET", "wifi-sense-local-session-v1")
SESSION_TTL = 2 * 3600      # 2 小时：凭证在地址栏可见，有效期越短泄露窗口越小
SESSION_TTL_REMEMBER = 30 * 24 * 3600   # 勾选「记住我」：30 天
SESSION_PARAM = "ws_s"


def _session_sign(raw):
    return hmac.new(
        SESSION_SECRET.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256
    ).hexdigest()[:32]


def issue_session(username, role, person_id, remember=False):
    body = {
        "u": username,
        "r": role,
        "p": person_id,
        "ts": int(time.time()),
        "rm": 1 if remember else 0,
    }
    raw = base64.urlsafe_b64encode(
        json.dumps(body, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return f"{raw}.{_session_sign(raw)}"


def parse_session(token):
    if not token or "." not in token:
        return None
    raw, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _session_sign(raw)):
        return None
    try:
        body = json.loads(base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
    except Exception:
        return None
    ttl = SESSION_TTL_REMEMBER if body.get("rm") else SESSION_TTL
    if int(body.get("ts") or 0) + ttl < int(time.time()):
        return None
    if not body.get("u"):
        return None
    return body


def persist_session():
    if not PERSIST_LOGIN:
        return
    token = issue_session(
        st.session_state.get("username"),
        st.session_state.get("role"),
        st.session_state.get("person_id"),
        bool(st.session_state.get("remember_login")),
    )
    try:
        if st.query_params.get(SESSION_PARAM) != token:
            st.query_params[SESSION_PARAM] = token
    except Exception:
        pass


def clear_session_param():
    try:
        if SESSION_PARAM in st.query_params:
            del st.query_params[SESSION_PARAM]
    except Exception:
        pass


def restore_session():
    """刷新后没有任何 session_state，凭 URL 里的凭证重建登录态。"""
    if not PERSIST_LOGIN or st.session_state.get("logged_in"):
        return False

    body = parse_session(st.query_params.get(SESSION_PARAM))
    if not body:
        clear_session_param()
        return False

    st.session_state.logged_in = True
    st.session_state.username = body["u"]
    st.session_state.role = body.get("r") or "管理员"
    st.session_state.person_id = body.get("p")
    st.session_state.page = (
        "管理工作台" if st.session_state.role == "管理员" else "家庭监护首页"
    )
    return True


def login(username, password, remember=False):
    try:
        user = source().authenticate(username, password)
    except DataSourceError as exc:
        st.session_state.api_error = str(exc)
        return False

    if not user:
        return False

    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.role = user["role"]
    st.session_state.person_id = user["person_id"]
    st.session_state.page = "管理工作台" if user["role"] == "管理员" else "家庭监护首页"
    st.session_state.remember_login = bool(remember)
    st.session_state.boot_anim = True
    persist_session()

    # 真实模式下登录成功即拉一次全量数据，避免首页空列表
    if not DEMO_MODE:
        try:
            with loading_state("正在加载数据…"):
                source().hydrate()
        except DataSourceError as exc:
            data_error(exc, "登录成功，但数据加载失败，请点击页面右上角刷新重试。")

    return True


def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.person_id = None
    st.session_state.page = "管理工作台"
    st.session_state.api_token = None
    st.session_state.auth_expired = False
    clear_session_param()
    _cache_clear()
    st.rerun()


def get_current_person():
    pid = st.session_state.person_id

    for person in st.session_state.persons:
        if person["id"] == pid:
            return person

    return None


# ============================================================
# UI 组件
# ============================================================

ICON_WIFI = (
    '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M140,204a12,12,0,1,1-12-12A12,12,0,0,1,140,204ZM237.08,87A172,172,0,0,0,18.92,87,8,8,0,0,0,29.08,12.37a156,156,0,0,1,197.84,0A8,8,0,0,0,237.08,87ZM205,122.77a124,124,0,0,0-153.94,0A8,8,0,0,0,61,135.31a108,108,0,0,1,134.06,0,8,8,0,0,0,11.24-1.3A8,8,0,0,0,205,122.77Zm-32.26,35.76a76.05,76.05,0,0,0-89.42,0,8,8,0,0,0,9.42,12.94,60,60,0,0,1,70.58,0,8,8,0,1,0,9.42-12.94Z"/></svg>'
)

ICON_SHIELD = (
    '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M208,40H48A16,16,0,0,0,32,56v56c0,52.72,25.52,84.67,46.93,102.19,23.06,18.86,46,25.27,47,25.53a8,8,0,0,0,4.2,0c1-.26,23.91-6.67,47-25.53C198.48,196.67,224,164.72,224,112V56A16,16,0,0,0,208,40Zm0,72c0,37.07-13.66,67.16-40.6,89.42A129.3,129.3,0,0,1,128,223.62a128.25,128.25,0,0,1-38.92-21.81C61.82,179.51,48,149.3,48,112l0-56,160,0Z"/></svg>'
)

ICON_HOUSE = (
    '<svg viewBox="0 0 256 256" fill="currentColor" aria-hidden="true"><path d="M219.31,108.68l-80-80a16,16,0,0,0-22.62,0l-80,80A15.87,15.87,0,0,0,32,120v96a8,8,0,0,0,8,8h64a8,8,0,0,0,8-8V160h32v56a8,8,0,0,0,8,8h64a8,8,0,0,0,8-8V120A15.87,15.87,0,0,0,219.31,108.68ZM208,208H160V152a8,8,0,0,0-8-8H104a8,8,0,0,0-8,8v56H48V120l80-80,80,80Z"/></svg>'
)


def badge(text, tone="accent"):
    return f'<span class="badge badge-{tone}">{esc(text)}</span>'


DATA_MODE_TEXT = "DEMO 模拟" if DEMO_MODE else "实时"
DATA_MODE_CAPTION = "DEMO 模拟数据" if DEMO_MODE else "实时数据"


def data_mode_badge():
    """数据来源徽标：演示期显示 DEMO，接入后端后显示实时，不说假话。"""
    return badge("DEMO", "muted") if DEMO_MODE else badge("实时", "ok")


def fmt_temp(value):
    """温度格：后端可能上报 null（当前无表面温度传感器），如实说明，不用环境温度伪造。"""
    try:
        if value is None or pd.isna(value):
            return "暂无传感器来源"
        return f"{float(value):.1f} °C"
    except (TypeError, ValueError):
        return "暂无传感器来源"


def temp_limit_text(key, fallback):
    try:
        return f"阈值 {float(st.session_state.params.get(key, fallback)):.1f} °C"
    except (TypeError, ValueError):
        return f"阈值 {fallback:.1f} °C"


def metric_card(label, value, hint="", tone="accent"):
    st.markdown(
        f"""
        <div class="mcard tone-{tone}">
            <div class="mcard-label">{esc(label)}</div>
            <div class="mcard-value">{esc(value)}</div>
            <div class="mcard-hint">{esc(hint)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(title, note=""):
    st.markdown(
        f'<div class="section"><div class="section-title">{esc(title)}</div>'
        f'<div class="section-note">{esc(note)}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(title, hint):
    st.markdown(
        f'<div class="empty"><div class="empty-title">{esc(title)}</div>'
        f'<div class="empty-hint">{esc(hint)}</div></div>',
        unsafe_allow_html=True,
    )


def banner(kind, title, text):
    st.markdown(
        f'<div class="banner banner-{kind}"><div class="banner-dot"></div>'
        f'<div><div class="banner-title">{esc(title)}</div>'
        f'<div class="banner-text">{esc(text)}</div></div></div>',
        unsafe_allow_html=True,
    )


@contextmanager
def loading_state(text="正在读取数据…"):
    """统一加载态：后端接口慢时页面不会看起来像卡死。"""
    with st.spinner(text):
        yield


def data_error(exc, hint="接口未接入或不可用，当前数据仅供参考，请勿据此判断真实设备状态。"):
    """统一错误态：后端失败时不静默，也不冒充成功。"""
    st.session_state.api_error = str(exc)
    banner("danger", "数据读取失败", f"{str(exc)}。{hint}")


def freshness_text(ts=None):
    """数据新鲜度：正常只显示更新时间，超过 10 分钟才补一句提示。"""
    ts = ts or st.session_state.get("last_refresh") or datetime.now()
    label = "更新于 " + ts.strftime("%H:%M")
    minutes = int((datetime.now() - ts).total_seconds() // 60)

    if minutes >= 10:
        return f"{label} · 已 {minutes} 分钟未刷新"
    return label


def mini_rows(items):
    rows = ""
    for title, meta, right in items:
        rows += (
            f'<div class="mrow"><div><div class="mrow-title">{esc(title)}</div>'
            f'<div class="mrow-meta">{esc(meta)}</div></div>'
            f"<div>{right}</div></div>"
        )
    return f'<div class="mlist">{rows}</div>'


def kv_block(title, items):
    rows = "".join(
        f'<div class="kv"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k, v in items
    )
    st.markdown(
        f'<div class="kvb"><div class="kvb-title">{esc(title)}</div>{rows}</div>',
        unsafe_allow_html=True,
    )


def fmt_cell(value):
    if value is None:
        return "-"
    try:
        if pd.isna(value):
            return "-"
    except (TypeError, ValueError):
        pass

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, float):
        return f"{value:.1f}"

    return str(value)


def data_table(df, max_rows=150):
    view = df.head(max_rows).copy()

    header = "".join(f"<th>{esc(col)}</th>" for col in view.columns)
    body = []

    for _, row in view.iterrows():
        cells = "".join(f"<td>{esc(fmt_cell(v))}</td>" for v in row.tolist())
        body.append(f"<tr>{cells}</tr>")

    st.markdown(
        f'<div class="twrap"><table class="dfmt"><thead><tr>{header}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 空间视图（自绘 Canvas 等距三维，无外部依赖、离线可用）
# ============================================================

_SPACE_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;background:#0A0E14;overflow:hidden}
canvas{display:block;width:100%;height:100%}
.hud{transition:opacity .2s;}
html.compact .hud{display:none;}
.hud{position:absolute;inset:0;pointer-events:none;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#CBD5E1}
.panel{position:absolute;background:rgba(12,18,26,0.82);border:1px solid rgba(71,102,133,0.35);border-radius:8px;padding:8px 10px;backdrop-filter:blur(6px)}
.left{left:10px;top:10px;min-width:132px}
.right{right:10px;top:10px;min-width:150px}
.ttl{font-size:11px;font-weight:600;color:#E2E8F0;letter-spacing:.02em;margin-bottom:6px}
.badge{font-size:9px;font-weight:600;color:#7DD3FC;border:1px solid rgba(125,211,252,.4);border-radius:4px;padding:0 4px;margin-left:4px}
.stats{font-size:11px;line-height:1.7;color:#94A3B8}
.stats b{color:#E2E8F0;font-weight:600;margin-left:4px}
.row{display:flex;align-items:center;gap:6px;font-size:11px;line-height:1.9;color:#94A3B8;cursor:default}
.row .dot{width:6px;height:6px;border-radius:50%;flex:0 0 6px}
.row .nm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:86px}
.row.on .nm{color:#E2E8F0;font-weight:600}
.tip{position:absolute;left:12px;bottom:8px;font-size:10px;color:#64748B}
.aicard{left:10px;bottom:26px;max-width:min(330px,58%);display:none;line-height:1.55}
.aicard.show{display:block}
.aicard .lbl{font-size:11px;font-weight:600;color:#E2E8F0;margin-bottom:3px}
.aicard .lvl{font-size:9px;font-weight:600;border-radius:4px;padding:0 4px;margin-left:5px;border:1px solid}
.aicard .txt{font-size:10px;color:#94A3B8}
.aicard .act{font-size:10px;color:#7DD3FC;margin-top:4px}
.aicard .src{font-size:9px;color:#64748B;margin-top:4px}
.meta{position:absolute;right:12px;bottom:8px;font-size:10px;color:#64748B}
</style></head><body>
<canvas id="cv"></canvas>
<div class="hud">
  <div class="panel left"><div class="ttl">空间状态<span class="badge" id="mode">DEMO</span></div><div class="stats" id="stats"></div></div>
  <div class="panel right"><div class="ttl">房间</div><div id="list"></div></div>
  <div class="panel aicard" id="aicard"></div>
  <div class="tip">拖动旋转 · 滚轮缩放 · 点击房间</div>
  <div class="meta" id="meta"></div>
</div>
<script>const DATA = __DATASET__;</script>
<script>__JS__</script>
</body></html>"""

_SPACE_JS = r"""
(function(){
  var rooms = (DATA.rooms || []);
  var cv = document.getElementById('cv');
  var ctx = cv.getContext('2d');
  var yaw = -0.62, pitch = 0.70, zoom = 1.0, sel = null, W = 640, H = 340;

  function resize(){
    var box = cv.getBoundingClientRect();
    W = box.width || 640; H = box.height || 340;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resize);
  resize();

  function project(x, y, z){
    var cy = Math.cos(yaw), sy = Math.sin(yaw);
    var cp = Math.cos(pitch), sp = Math.sin(pitch);
    var xr = x * cy - z * sy;
    var zr = x * sy + z * cy;
    var s = Math.min(W * 0.32, (H * 0.78) / (2 * Math.max(0.34, sp))) * zoom;
    return { x: W * 0.50 + xr * s, y: H * 0.52 - (y * cp - zr * sp) * s, d: zr };
  }

  function colorFor(r){
    if (r.alerts > 0) return '239,68,68';
    if (r.activity === '移动') return '163,230,53';
    if (r.activity === '活动') return '52,211,153';
    if (r.activity === '静止') return '56,189,248';
    return '148,163,184';
  }
  function esc(v){
    return String(v == null ? '' : v).replace(/[&<>"']/g, function(c){
      return ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'})[c];
    });
  }
  function aiLevelColor(lv){
    if (lv === 'alert') return '#EF4444';
    if (lv === 'watch') return '#FBBF24';
    return '#7DD3FC';
  }
  function renderAiCard(){
    var el = document.getElementById('aicard');
    if (!el) return;
    var room = null;
    for (var i = 0; i < rooms.length; i++){ if (rooms[i].name === sel){ room = rooms[i]; break; } }
    if (!room || !room.ai){ el.classList.remove('show'); el.innerHTML = ''; return; }
    var ai = room.ai, lv = ai.level || 'info';
    var facts = '';
    if (ai.facts && ai.facts.length){
      var fs = [];
      for (var k = 0; k < ai.facts.length; k++){
        fs.push(esc(ai.facts[k].k || '') + ' ' + esc(ai.facts[k].v || ''));
      }
      facts = '<div class="txt" style="margin-top:3px">' + fs.join(' · ') + '</div>';
    }
    el.innerHTML = '<div class="lbl">' + esc(room.name) + ' · ' + esc(ai.label || '状态')
      + '<span class="lvl" style="color:' + aiLevelColor(lv) + ';border-color:' + aiLevelColor(lv) + '">' + esc(lv) + '</span></div>'
      + '<div class="txt">' + esc(ai.plain || '') + '</div>' + facts
      + (ai.action ? '<div class="act">' + esc(ai.action) + '</div>' : '')
      + '<div class="src">' + (ai.source === 'backend' ? 'AI 解释' : '本地模板')
      + (ai.confidence ? ' · 置信 ' + Math.round(ai.confidence * 100) + '%' : '') + '</div>';
    el.classList.add('show');
  }
  function alphaFor(r){
    if (r.alerts > 0) return 0.85;
    if (r.activity === '移动') return 0.72;
    if (r.activity === '活动') return 0.52;
    if (r.activity === '静止') return 0.30;
    return 0.16;
  }
  function pulseFor(){
    return 0.55 + 0.45 * Math.sin(Date.now() / 620);
  }

  function drawFloor(){
    var n = 6, i, p, a, b, c, d;
    ctx.strokeStyle = 'rgba(74,150,190,0.22)';
    ctx.lineWidth = 1;
    for (i = -n; i <= n; i++){
      p = i / n;
      a = project(p, 0, -1); b = project(p, 0, 1);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      c = project(-1, 0, p); d = project(1, 0, p);
      ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }
    for (i = -n; i <= n; i++){
      for (var j = -n; j <= n; j++){
        if ((i + j) % 2 !== 0) continue;
        var q = project(i / n, 0, j / n);
        var fade = 1 - Math.min(1, Math.sqrt(i * i + j * j) / (n * 1.35));
        ctx.fillStyle = 'rgba(74,222,128,' + (0.05 + 0.16 * fade) + ')';
        ctx.fillRect(q.x - 1.5, q.y - 1.5, 3, 3);
      }
    }
    var o = project(0, 0, 0);
    var g = ctx.createRadialGradient(o.x, o.y, 0, o.x, o.y, Math.min(W, H) * 0.8);
    g.addColorStop(0, 'rgba(28,84,116,0.16)');
    g.addColorStop(1, 'rgba(8,12,18,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }

  function roomFaces(r){
    var wx = (r.x + r.w / 2 - 0.5) * 2;
    var wz = (r.y + r.h / 2 - 0.5) * 2;
    var hh = (r.height || 0.1) * 2.2;
    var x0 = wx - r.w, x1 = wx + r.w, z0 = wz - r.h, z1 = wz + r.h;
    var T0 = project(x0, hh, z0), T1 = project(x1, hh, z0);
    var T2 = project(x1, hh, z1), T3 = project(x0, hh, z1);
    var B0 = project(x0, 0, z0), B1 = project(x1, 0, z0);
    var B2 = project(x1, 0, z1), B3 = project(x0, 0, z1);
    return {
      top: [T0, T1, T2, T3],
      sides: [
        { q: [T0, T1, B1, B0], d: (T0.d + T1.d) / 2 },
        { q: [T1, T2, B2, B1], d: (T1.d + T2.d) / 2 },
        { q: [T2, T3, B3, B2], d: (T2.d + T3.d) / 2 },
        { q: [T3, T0, B0, B3], d: (T3.d + T0.d) / 2 }
      ],
      center: project(wx, hh, wz)
    };
  }

  function poly(pts, fill, stroke){
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (var i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.closePath();
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1; ctx.stroke(); }
  }

  function inside(pt, pts){
    var c = false;
    for (var i = 0, j = pts.length - 1; i < pts.length; j = i++){
      if (((pts[i].y > pt.y) !== (pts[j].y > pt.y)) &&
          (pt.x < (pts[j].x - pts[i].x) * (pt.y - pts[i].y) / (pts[j].y - pts[i].y) + pts[i].x)) c = !c;
    }
    return c;
  }

  function draw(){
    var cssW = cv.clientWidth || (W / (window.devicePixelRatio || 1));
    document.documentElement.classList.toggle('compact', cssW < 620);
    ctx.clearRect(0, 0, W, H);
    var bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, '#0B1016'); bg.addColorStop(0.6, '#0A0E14'); bg.addColorStop(1, '#070A0F');
    ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);
    drawFloor();

    var items = [], i;
    for (i = 0; i < rooms.length; i++){
      var f = roomFaces(rooms[i]);
      items.push({ r: rooms[i], f: f, d: (f.top[0].d + f.top[2].d) / 2 });
    }
    items.sort(function(a, b){ return a.d - b.d; });

    var pulse = pulseFor();

    for (i = 0; i < items.length; i++){
      var it = items[i], r = it.r, fc = it.f;
      var rgb = colorFor(r), al = alphaFor(r);
      var conf = (r.ai && r.ai.confidence) ? Math.max(0.35, Math.min(1, r.ai.confidence)) : 1;
      al = Math.min(0.92, al * (0.62 + 0.38 * conf));
      fc.sides.sort(function(a, b){ return a.d - b.d; });
      for (var k = 0; k < fc.sides.length; k++){
        poly(fc.sides[k].q, 'rgba(16,24,34,0.94)', 'rgba(58,88,118,0.32)');
      }
      poly(fc.top, 'rgba(14,22,32,0.96)', 'rgba(' + rgb + ',0.5)');
      var c0 = fc.center;
      var rr = Math.max(22, W * 0.10);
      poly(fc.top, 'rgba(' + rgb + ',' + (al * 0.20) + ')', null);
      var g = ctx.createRadialGradient(0, 0, 1, 0, 0, rr);
      g.addColorStop(0, 'rgba(' + rgb + ',' + al + ')');
      g.addColorStop(0.5, 'rgba(' + rgb + ',' + (al * 0.34) + ')');
      g.addColorStop(1, 'rgba(' + rgb + ',0)');
      ctx.save();
      ctx.globalCompositeOperation = 'lighter';
      ctx.translate(c0.x, c0.y - Math.max(4, W * 0.014));
      ctx.scale(1, 0.42);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(0, 0, rr, 0, Math.PI * 2); ctx.fill();
      ctx.restore();

      if (r.alerts > 0 || (r.ai && r.ai.level === 'alert')){
        ctx.beginPath();
        ctx.ellipse(c0.x, c0.y - 6, 16 + 8 * pulse, 7 + 4 * pulse, 0, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(239,68,68,' + (0.45 + 0.4 * pulse) + ')';
        ctx.lineWidth = 1.6; ctx.stroke();
      }

      var devs = r.devices || [];
      for (var j = 0; j < devs.length; j++){
        var off = (j - (devs.length - 1) / 2) * 0.16;
        var bx = (r.x + r.w / 2 - 0.5) * 2 + off;
        var bz = (r.y + r.h / 2 - 0.5) * 2 + r.h * 0.5;
        var tp = project(bx, (r.height || 0.1) * 2.2 + 0.12, bz);
        var bp = project(bx, 0, bz);
        ctx.strokeStyle = devs[j].online ? 'rgba(45,212,191,0.85)' : 'rgba(148,163,184,0.55)';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(bp.x, bp.y); ctx.lineTo(tp.x, tp.y); ctx.stroke();
        ctx.fillStyle = devs[j].online ? 'rgba(45,212,191,1)' : 'rgba(148,163,184,0.9)';
        ctx.beginPath(); ctx.arc(tp.x, tp.y, 3, 0, Math.PI * 2); ctx.fill();
        var pg = ctx.createRadialGradient(tp.x, tp.y, 0, tp.x, tp.y, 14);
        pg.addColorStop(0, devs[j].online ? 'rgba(45,212,191,0.45)' : 'rgba(148,163,184,0.20)');
        pg.addColorStop(1, 'rgba(45,212,191,0)');
        ctx.save(); ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(tp.x, tp.y, 14, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      }

      ctx.font = '11px -apple-system,"PingFang SC","Microsoft YaHei",sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = sel === r.name ? '#FFFFFF' : 'rgba(203,213,225,0.9)';
      ctx.fillText(r.name, c0.x, c0.y - Math.max(18, W * 0.055));
      if (sel === r.name) poly(fc.top, null, 'rgba(226,232,240,0.85)');
      if (r.focus && sel !== r.name){ ctx.setLineDash([4, 4]); poly(fc.top, null, 'rgba(125,211,252,0.75)'); ctx.setLineDash([]); }
    }
  }

  function syncState(){
    cv.setAttribute('data-yaw', yaw.toFixed(3));
    cv.setAttribute('data-pitch', pitch.toFixed(3));
    cv.setAttribute('data-zoom', zoom.toFixed(3));
    cv.setAttribute('data-sel', sel || '');
  }

  function loop(){ draw(); syncState(); requestAnimationFrame(loop); }
  requestAnimationFrame(loop);

  var dragging = false, lx = 0, ly = 0;
  cv.addEventListener('pointerdown', function(e){
    dragging = true; lx = e.clientX; ly = e.clientY;
    if (cv.setPointerCapture) cv.setPointerCapture(e.pointerId);
  });
  cv.addEventListener('pointermove', function(e){
    if (!dragging) return;
    yaw += (e.clientX - lx) * 0.006;
    pitch = Math.max(0.28, Math.min(1.30, pitch + (e.clientY - ly) * 0.005));
    lx = e.clientX; ly = e.clientY;
  });
  cv.addEventListener('pointerup', function(){ dragging = false; });
  cv.addEventListener('pointercancel', function(){ dragging = false; });
  cv.addEventListener('wheel', function(e){
    e.preventDefault();
    zoom = Math.max(0.65, Math.min(2.4, zoom * (e.deltaY > 0 ? 0.92 : 1.08)));
  }, { passive: false });
  cv.addEventListener('click', function(e){
    var box = cv.getBoundingClientRect();
    var pt = { x: e.clientX - box.left, y: e.clientY - box.top };
    var items = [];
    for (var i = 0; i < rooms.length; i++){
      var f = roomFaces(rooms[i]);
      items.push({ r: rooms[i], f: f, d: (f.top[0].d + f.top[2].d) / 2 });
    }
    items.sort(function(a, b){ return b.d - a.d; });
    var hit = false;
    for (var k = 0; k < items.length; k++){
      if (inside(pt, items[k].f.top)){ sel = items[k].r.name; hit = true; break; }
    }
    if (!hit) sel = null;
    renderList();
    renderAiCard();
  });

  function renderList(){
    var el = document.getElementById('list');
    var html = '';
    for (var i = 0; i < rooms.length; i++){
      var r = rooms[i];
      var dot = r.alerts > 0 ? '#EF4444' : (r.activity === '移动' ? '#A3E635' : (r.activity === '活动' ? '#34D399' : (r.activity === '静止' ? '#38BDF8' : '#94A3B8')));
      var tail = r.temp === null ? '无数据' : (r.temp + '°C');
      html += '<div class="row' + (sel === r.name ? ' on' : '') + '"><span class="dot" style="background:' + dot + '"></span>'
            + '<span class="nm">' + r.name + '</span><span>' + tail + '</span></div>';
    }
    el.innerHTML = html;
  }

  (function(){
    var online = 0, total = 0, alerts = 0, actives = 0;
    for (var i = 0; i < rooms.length; i++){
      alerts += rooms[i].alerts || 0;
      if (rooms[i].activity === '活动' || rooms[i].activity === '移动') actives++;
      var ds = rooms[i].devices || [];
      total += ds.length;
      for (var j = 0; j < ds.length; j++) if (ds[j].online) online++;
    }
    document.getElementById('stats').innerHTML =
      '房间<b>' + rooms.length + '</b><br>设备在线<b>' + online + '/' + total + '</b><br>待处理告警<b>' + alerts + '</b><br>房间有活动<b>' + actives + '</b>';
    if (DATA.summary){
      document.getElementById('stats').innerHTML += '<div style="margin-top:5px;color:#94A3B8">' + esc(DATA.summary) + '</div>';
    }
    document.getElementById('mode').textContent = DATA.mode || 'DEMO';
    document.getElementById('meta').textContent = '数据更新 ' + (DATA.updated || '') + ' · ' + (DATA.mode || 'DEMO');
    renderList();
  })();
})();
"""


def _zone_grid(areas, cols, gap=0.10):
    """按指定列数把区域排成归一化网格（0–1 坐标系）。"""
    names = list(areas or [])
    if not names:
        return {}
    n = len(names)
    rows = (n + cols - 1) // cols
    cell_w = (1.0 - gap * (cols + 1)) / cols
    cell_h = (1.0 - gap * (rows + 1)) / rows
    out = {}
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        out[name] = {
            "x": round(gap + c * (cell_w + gap), 4),
            "y": round(gap + r * (cell_h + gap), 4),
            "w": round(cell_w, 4),
            "h": round(cell_h, 4),
            "height": round(0.07 + 0.012 * (i % 3), 4),
        }
    return out


def _zone_layout(areas, override=None):
    """区域坐标：默认自动网格，override 里给了哪个区域就用那个区域的手动值。"""
    names = list(areas or [])
    if not names:
        return {}
    n = len(names)
    cols = 1 if n == 1 else (2 if n <= 4 else 3)
    out = _zone_grid(names, cols)
    for key, rect in (override or {}).items():
        if key not in out or not isinstance(rect, dict):
            continue
        base = out[key]
        out[key] = {
            "x": round(float(rect.get("x", base["x"])) * 1.0, 4),
            "y": round(float(rect.get("y", base["y"])) * 1.0, 4),
            "w": round(float(rect.get("w", base["w"])) * 1.0, 4),
            "h": round(float(rect.get("h", base["h"])) * 1.0, 4),
            "height": round(float(rect.get("height", base["height"])), 4),
        }
    return out


def _room_num(value, digits=1):
    """读数可能为 null（后端异常或缺传感器），这里统一降级为 None，不抛错。"""
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


_SPACE_AI_LEVELS = ("info", "watch", "alert")


def _space_ai_template(room, activity, temp, alerts, devices):
    """本地模板兜底：只解释已有读数，不下诊断结论；source 标记 template。"""
    online = sum(1 for d in devices if d.get("online"))
    total = len(devices)
    facts = [{"k": "设备", "v": f"{online}/{total} 在线"}]
    if temp is not None:
        facts.append({"k": "环境", "v": f"{temp} ℃"})
    if activity is None:
        return {
            "label": "暂无数据",
            "plain": f"{room} 还没有可用的实时读数。",
            "level": "watch",
            "action": "检查设备连接与采集链路。",
            "facts": facts,
            "confidence": 0.2,
            "source": "template",
        }
    if alerts:
        return {
            "label": "待确认的异常",
            "plain": f"{room} 有 {alerts} 条待处理告警，当前活动状态为「{activity}」。",
            "level": "alert",
            "action": "查看告警详情，必要时电话确认。",
            "facts": facts + [{"k": "待处理", "v": f"{alerts} 条"}],
            "confidence": 0.5,
            "source": "template",
        }
    label, action = {
        "移动": ("有人在移动", "无需处理，保持观察。"),
        "活动": ("有人在活动", "无需处理。"),
        "静止": ("可能静止或休息", "无需处理；夜间长时间无变化时留意。"),
    }.get(activity, ("状态未知", "确认读数是否持续上报。"))
    return {
        "label": label,
        "plain": f"{room} 最近读数显示{label}" + (f"，环境 {temp} ℃。" if temp is not None else "。"),
        "level": "info",
        "action": action,
        "facts": facts,
        "confidence": 0.45,
        "source": "template",
    }


def _space_room_ai(name, activity, temp, alerts, devices):
    """后端给了 ai 就用后端的，没给则本地模板兜底；字段缺失一律降级，不抛错。"""
    ai_map = st.session_state.get("space_ai") or {}
    ai = ai_map.get(name) if isinstance(ai_map, dict) else None
    if isinstance(ai, dict) and (ai.get("label") or ai.get("plain")):
        out = dict(ai)
        out["source"] = "backend"
        out.setdefault("level", "info")
        out.setdefault("facts", [])
        return out
    return _space_ai_template(name, activity, temp, alerts, devices)


def space_rooms(df, focus=None, layout=None):
    """把区域、实时读数、设备、告警装配成空间视图的数据（layout 可覆盖自动排布）。"""
    areas = list(st.session_state.areas or [])
    override = layout if layout is not None else st.session_state.get("zone_layout")
    layout = _zone_layout(areas, override)
    alerts = st.session_state.get("alerts") or []
    devices = st.session_state.get("devices") or []

    rooms = []
    for name in areas:
        rect = layout[name]
        sub = df[df["监测区域"] == name] if df is not None else None
        latest = None if sub is None or sub.empty else sub.iloc[-1]
        room_alerts = [
            a for a in alerts if a.get("room") == name and a.get("status") == "待处理"
        ]
        room_devices = [d for d in devices if d.get("room") == name]

        activity = None if latest is None else str(latest["活动状态"])
        temp = None if latest is None else _room_num(latest["环境温度"])
        rooms.append(
            {
                **rect,
                "name": name,
                "activity": activity,
                "temp": temp,
                "surface": None if latest is None else _room_num(latest["表面温度"]),
                "alerts": len(room_alerts),
                "devices": [
                    {
                        "name": d.get("type") or "设备",
                        "online": d.get("status") == "在线",
                    }
                    for d in room_devices
                ],
                "ai": _space_room_ai(name, activity, temp, len(room_alerts), room_devices),
                "focus": bool(focus and name == focus),
            }
        )
    return rooms


def space_view(rooms, updated_at, height=340):
    """渲染空间视图：深色场景 + 房间体 + 设备柱 + 活动光斑，数据源与时间写在角标上。"""
    ai_map = st.session_state.get("space_ai") or {}
    payload = json.dumps(
        {
            "version": "1.1",
            "rooms": rooms,
            "updated": updated_at.strftime("%H:%M:%S") if updated_at else "",
            "mode": "DEMO 模拟" if DEMO_MODE else "实时",
            "summary": str(st.session_state.get("space_summary") or ""),
            "baseline_ready": st.session_state.get("space_baseline_ready"),
            "ai_source": "backend" if ai_map else "template",
        },
        ensure_ascii=False,
    )
    html = _SPACE_HTML.replace("__DATASET__", payload).replace("__JS__", _SPACE_JS)
    st.iframe(html, height=height)



def _rail_style():
    """只有玻璃态两套用图标 rail + 顶部胶囊；经典主题走原版布局。"""
    return get_palette().get("mode") in ("glass", "glass_light")


def _page_header_classic(title, subtitle, crumb, refresh_key="refresh_top"):
    left, right = st.columns([4.6, 1], gap="medium", vertical_alignment="bottom")

    with left:
        st.markdown(
            f'<div class="ph-breadcrumb">{esc(crumb)}</div>'
            f'<div class="ph-title">{esc(title)}</div>'
            f'<div class="ph-sub">{esc(subtitle)}</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            '<div class="ph-meta">' + freshness_text() + "</div>",
            unsafe_allow_html=True,
        )
        clicked = st.button("刷新数据", key=refresh_key, width="stretch")

    st.markdown(
        '<div class="demo-line"><span class="tag-muted">模拟数据</span>'
        "演示环境，未连接真实 ESP32 设备；页面中的状态与告警仅用于功能演示。</div>",
        unsafe_allow_html=True,
    )

    return clicked


def page_header(title, subtitle, crumb, refresh_key="refresh_top"):
    if not _rail_style():
        return _page_header_classic(title, subtitle, crumb, refresh_key)

    who = esc(st.session_state.get("username") or "访客")
    role = esc(st.session_state.get("role") or "访客")
    initial = (who or "?")[:1].upper()

    with st.container(border=True, key="topbar_shell"):
        bar_left, bar_mid, bar_right = st.columns([2.5, 4.2, 1.25], gap="small", vertical_alignment="center")

        with bar_left:
            st.markdown(
                '<div class="topbar">'
                f'<div class="tb-avatar">{initial}</div>'
                f'<div class="tb-user"><span class="tb-name">Welcome, {who}</span>'
                f'<span class="tb-role">{role} · DEMO</span></div>'
                "</div>",
                unsafe_allow_html=True,
            )

        with bar_mid:
            st.markdown(f'<div class="tb-pill">{esc(crumb)}</div>', unsafe_allow_html=True)

        with bar_right:
            clicked = st.button(
                "刷新数据",
                key=refresh_key,
                icon=":material/refresh:",
                width="stretch",
            )

    st.markdown(
        f'<div class="ph-title">{esc(title)}</div>'
        f'<div class="ph-sub">{esc(subtitle)}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="demo-line"><span class="tag-muted">模拟数据</span>'
        "演示环境，未连接真实 ESP32 设备；页面中的状态与告警仅用于功能演示。</div>",
        unsafe_allow_html=True,
    )

    return clicked


def state_badge(level):
    if level == "严重":
        return badge("严重告警", "danger")
    return badge("关注提醒", "warn")


def alert_badge(status):
    return badge(status, "warn" if status == "待处理" else "ok")


def mask_phone(phone):
    text = str(phone)
    if len(text) < 7:
        return text
    return text[:3] + "****" + text[-4:]


def person_by_id(pid):
    local = next((p for p in st.session_state.persons if p.get("id") == pid), None)
    if local is not None:
        return local
    try:
        return source().person_by_id(pid)
    except DataSourceError as exc:
        data_error(exc, "人员档案加载失败。")
        return None


def device_by_id(dev_id):
    return next((d for d in st.session_state.devices if d["id"] == dev_id), None)


# ============================================================
# 登录页
# ============================================================


def boot_overlay():
    """登录成功后的粒子过渡：约 1.5 秒后自动进入工作台。"""
    rnd = random.Random(20261115)
    dots = []
    for _ in range(68):
        ang = rnd.uniform(0, math.tau)
        dist = rnd.uniform(96, 302)
        size = rnd.uniform(2.0, 4.4)
        delay = rnd.uniform(0, 0.45)
        dur = rnd.uniform(1.25, 1.75)
        dots.append(
            f'<i style="--x:{math.cos(ang) * dist:.0f}px;--y:{math.sin(ang) * dist:.0f}px;'
            f'--s:{size:.1f}px;animation-delay:{delay:.2f}s;animation-duration:{dur:.2f}s"></i>'
        )
    st.markdown(
        '<style>[data-testid="stStatusWidget"]{display:none!important}</style>'
        '<div class="boot">'
        '<div class="boot-stage"><div class="boot-halo"></div><div class="boot-core"></div>'
        f'<div class="boot-field">{"".join(dots)}</div></div>'
        '<div class="boot-brand">Wi-Fi Sense</div>'
        '<div class="boot-tip">正在进入工作台</div>'
        '<div class="boot-bar"><span></span></div>'
        '</div>',
        unsafe_allow_html=True,
    )


CH_24 = list(range(1, 14))
CH_5 = [36, 44, 52, 60, 100, 116, 132, 149, 165]


def login_channel_scan() -> dict:
    """登录页频谱的唯一数据入口。两段：2.4 GHz（1–13）与 5 GHz（常用非重叠信道）。

    当前为本地模拟：以 10 分钟为一个时间片取种子 —— 同一时间片内刷新读数稳定
    （不会跳数），换到下一个时间片才换一张频谱，像同一台设备过一阵子重扫了一次。

    真实数据接入：把每段 series 里的 v 换成后端返回的占用度（0–1）即可；
    peak_ch 与 include 的 busy 标记都由 v 推导，渲染层无需改动。
    """
    slot = int(time.time() // 600)
    rnd = random.Random(slot)

    def band(channels, sigma, peak_idx, floor, amp):
        series = []
        for i, ch in enumerate(channels):
            hump = math.exp(-((i - peak_idx) ** 2) / (2 * sigma ** 2))
            v = min(0.96, rnd.uniform(*floor) + hump * rnd.uniform(*amp))
            series.append({"ch": ch, "v": round(v, 3)})
        return {"series": series, "peak_ch": channels[peak_idx]}

    b24 = band(CH_24, sigma=1.35, peak_idx=5 + rnd.randint(-2, 2), floor=(0.05, 0.24), amp=(0.55, 0.95))
    b24["label"] = "2.4 GHz"

    b5 = band(CH_5, sigma=1.05, peak_idx=rnd.choice([3, 4, 5]), floor=(0.03, 0.16), amp=(0.45, 0.88))
    b5["label"] = "5 GHz"

    return {"bands": [b24, b5], "source": "simulated"}


def login_spectrum_bars(band: dict, seed: int, per_ch: int = 3) -> str:
    """把一段信道占用渲染成「每信道一组柱」：静态高度来自数据，起伏幅度也由数据决定。"""
    rnd = random.Random(seed)
    groups = []
    for item in band["series"]:
        v, ch = item["v"], item["ch"]
        base = 14 + (v ** 0.85) * 78
        spread = 4 + v * 14
        bars = []
        for _ in range(per_ch):
            off = rnd.uniform(-6, 4)   # 同一信道内的每根柱也不同高，避免连成一片方块
            pts = [max(16, min(100, round(base + off + rnd.uniform(-spread, spread * 0.6)))) for _ in range(6)]
            dur = round(rnd.uniform(2.6, 4.4), 2)
            delay = round(rnd.uniform(-4.0, 0.0), 2)
            style = "".join(f"--h{k + 1}:{h};" for k, h in enumerate(pts))
            style += f"--t:{dur}s;--d:{delay}s"
            bars.append(f'<b style="{style}"></b>')
        busy = " busy" if v >= 0.48 else ""
        groups.append(
            f'<div class="band{busy}" title="信道 {ch}">{ "".join(bars) }'
            f'<span class="band-ch">{ch}</span></div>'
        )
    return "".join(groups)


def render_login():
    if st.session_state.get("auth_expired"):
        st.warning("登录状态已失效，请重新登录")
        st.session_state.auth_expired = False

    left, right = st.columns([1.05, 0.95], gap="large", vertical_alignment="center")

    with left:
        scan = login_channel_scan()
        slot = int(time.time() // 600)
        rows = []
        for k, band in enumerate(scan["bands"]):
            rows.append(
                f'<div class="meter-row">'
                f'<span class="meter-tag">{band["label"]}</span>'
                f'<div class="meter-track">{login_spectrum_bars(band, slot * 97 + k * 13 + 7)}</div>'
                f'<span class="meter-val">信道 {band["peak_ch"]}</span>'
                f'</div>'
            )
        spectrum = "".join(rows)
        st.markdown(
            f"""
            <style>
            [data-testid="stMainBlockContainer"] {{
                min-height: 94vh;
                display: flex;
                flex-direction: column;
                padding-top: 1.4rem !important;
                padding-bottom: 1.4rem !important;
            }}
            /* 内容不足一屏时上下自动留白居中；内容超长时自动退回顶部，不会把标题顶出可视区 */
            [data-testid="stMainBlockContainer"] > div {{
                width: 100%;
                flex: 0 0 auto;
                margin-top: auto;
                margin-bottom: auto;
            }}
            @media (max-width: 720px) {{
                .login-heading {{
                    font-size: 21px;
                    line-height: 1.5;
                    letter-spacing: 0.6px;
                }}
                .meter-track {{ height: 34px; }}
                .meter-tag {{ flex: 0 0 40px; }}
                .meter-val {{ flex: 0 0 46px; }}
                .band-ch {{ display: none; }}
                .login-hero {{ padding: 28px 24px; }}
            }}
            </style>
            <div class="login-hero">
                <div class="hero-fx"></div>
                <div class="hero-grid"></div>
                <div class="hero-body">
                    <div class="login-brand"><span class="brand-mark">{ICON_WIFI}</span>Wi-Fi Sense</div>
                    <div class="hero-meter">
                        <div class="meter-head"><span>信道活动</span><span>近 60 秒</span></div>
                        <div class="meter-rows">{spectrum}</div>
                    </div>
                    <div class="login-heading">感知每一刻<br>守护每一份安心</div>
                    <div class="login-desc">管理端看全部房间，家属端只看自己家这一户。</div>
                </div>
                <div class="login-foot">V{APP_VERSION}　　演示环境，数据为本地模拟</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        with st.container(border=True):
            st.markdown(
                '<div class="login-title">登录</div>'
                '<div class="login-sub">账号由管理员分配</div>',
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                username = st.text_input("账号", placeholder="请输入账号")
                password = st.text_input("密码", type="password", placeholder="请输入登录密码")
                remember = st.checkbox(
                    "记住我（30 天免登录）",
                    value=False,
                    key="remember_checkbox",
                    help="勾选后本机 30 天内打开同一链接仍保持登录；不勾选凭证只有 2 小时有效期",
                )
                submitted = st.form_submit_button("登录平台", type="primary", width="stretch")

                if submitted:
                    if login(username.strip(), password, remember):
                        st.rerun()
                    elif st.session_state.get("api_error"):
                        st.error(f"登录接口不可用：{st.session_state.api_error}")
                    else:
                        st.error("账号或密码不正确，请重新输入")

            st.markdown(
                '<div class="login-note"><span class="hf-dot"></span>'
                '默认 2 小时、刷新不掉线；勾选「记住我」后 30 天内免登录</div>',
                unsafe_allow_html=True,
            )

            role_left, role_right = st.columns(2)

            with role_left:
                st.markdown(
                    f'<div class="role-card"><div class="role-icon">{ICON_SHIELD}</div>'
                    '<div class="role-name">管理员</div>'
                    '<div class="role-desc">设备、人员与系统管理</div></div>',
                    unsafe_allow_html=True,
                )

            with role_right:
                st.markdown(
                    f'<div class="role-card"><div class="role-icon">{ICON_HOUSE}</div>'
                    '<div class="role-name">家属</div>'
                    '<div class="role-desc">家庭监护与告警查看</div></div>',
                    unsafe_allow_html=True,
                )


# ============================================================
# 侧边栏
# ============================================================


def resolve_page(is_admin):
    groups = NAV_ADMIN if is_admin else NAV_FAMILY
    valid = [item for _, items in groups for item in items]

    if st.session_state.page not in valid:
        st.session_state.page = valid[0]

    return st.session_state.page


def _render_sidebar_classic(is_admin):
    role_text = "管理员" if is_admin else "家属"

    with st.sidebar:
        st.markdown(
            f'<div class="brand"><span class="brand-mark">{ICON_WIFI}</span>Wi-Fi Sense</div>'
            '<div class="brand-sub">智能监测与家庭监护</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="user-chip"><div class="user-name">{esc(st.session_state.username)}</div>'
            f'<div class="user-meta">{badge(role_text, "accent")}'
            f'{data_mode_badge()}</div></div>',
            unsafe_allow_html=True,
        )

        groups = NAV_ADMIN if is_admin else NAV_FAMILY
        current = st.session_state.page

        for group_name, items in groups:
            st.markdown(f'<div class="nav-label">{esc(group_name)}</div>', unsafe_allow_html=True)
            for label in items:
                active = label == current
                clicked = st.button(
                    label,
                    key="nav_" + label,
                    type="primary" if active else "secondary",
                    width="stretch",
                )
                if clicked and not active:
                    st.session_state.page = label
                    st.rerun()

        st.markdown('<div class="side-sep"></div>', unsafe_allow_html=True)

        light = st.session_state.get("theme") in ("light", "glass_light")
        if st.button(
            "☾  切换到深色" if light else "☀  切换到浅色",
            key="theme_quick",
            width="stretch",
        ):
            apply_theme("light" if not light else "dark")
            st.rerun()

        st.markdown(
            f'<div class="side-foot">V{APP_VERSION} · 应用层<br>数据模式：{DATA_MODE_TEXT}</div>',
            unsafe_allow_html=True,
        )

        if st.button("退出登录", key="logout_btn", width="stretch"):
            logout()


def render_sidebar(is_admin):
    if not _rail_style():
        return _render_sidebar_classic(is_admin)

    role_text = "管理员" if is_admin else "家属"
    who = esc(st.session_state.username)
    initial = (who or "?")[:1].upper()

    with st.sidebar:
        groups = NAV_ADMIN if is_admin else NAV_FAMILY
        current = st.session_state.page

        for gi, (group_name, items) in enumerate(groups):
            for label in items:
                active = label == current
                clicked = st.button(
                    label,
                    key="nav_" + label,
                    type="primary" if active else "secondary",
                    icon=":material/%s:" % NAV_ICONS.get(label, "circle"),
                    help=label,
                    width="stretch",
                )
                if clicked and not active:
                    st.session_state.page = label
                    st.rerun()

        st.markdown(
            f'<div class="rail-chip">{esc(current)}</div>',
            unsafe_allow_html=True,
        )

        light = st.session_state.get("theme") in ("light", "glass_light")
        if st.button(
            "切换主题",
            key="theme_quick",
            icon=":material/light_mode:" if light else ":material/dark_mode:",
            help="在深色玻璃与浅色玻璃之间切换",
            width="stretch",
        ):
            cur = st.session_state.get("theme", "glass")
            if cur in ("glass", "glass_light"):
                apply_theme("glass" if light else "glass_light")
            else:
                apply_theme("dark" if light else "light")
            st.rerun()

        if st.button(
            "退出登录",
            key="logout_btn",
            icon=":material/logout:",
            help="退出登录",
            width="stretch",
        ):
            logout()


# ============================================================
# 管理员 · 管理工作台
# ============================================================


def page_dashboard():
    if page_header(
        "管理工作台",
        "系统运行概览、趋势分析与关键指标",
        "总览 / 工作台",
        "refresh_dashboard",
    ):
        refresh_data()
        st.rerun()

    persons = st.session_state.persons
    devices = st.session_state.devices
    alerts = st.session_state.alerts
    online = sum(1 for d in devices if d["status"] == "在线")
    pending = len(get_pending_alerts())

    cols = st.columns(4, gap="medium")

    with cols[0]:
        metric_card("人员总数", len(persons), f"覆盖 {len(st.session_state.areas)} 个监测区域")
    with cols[1]:
        metric_card("设备总数", len(devices), "Wi-Fi 感知 / 温度采集")
    with cols[2]:
        metric_card(
            "在线设备",
            online,
            f"未在线 {len(devices) - online} 台" if devices else "暂无设备",
            tone="ok" if online else "warn",
        )
    with cols[3]:
        metric_card(
            "待处理告警",
            pending,
            "全部为 DEMO 模拟告警" if DEMO_MODE else "需逐条确认",
            tone="danger" if pending else "ok",
        )

    df = st.session_state.demo_df

    if df is None or df.empty:
        section_title("监测趋势")
        empty_state("暂无监测数据", "点击右上角「刷新数据」生成一组新的 DEMO 数据。")
        return

    chart_left, chart_right = st.columns(2, gap="large")

    with chart_left:
        section_title("活动状态趋势", "近 3 小时 · 5 分钟粒度")
        plot_chart(activity_figure(df, height=300))

    with chart_right:
        section_title("温度变化", "近 3 小时 · 5 分钟粒度")
        plot_chart(temperature_figure(df, height=300))

    lower_left, lower_right = st.columns([1.35, 1], gap="large")

    with lower_left:
        section_title("最新告警", f"共 {len(alerts)} 条记录")

        if alerts:
            items = []
            for alert in alerts[:4]:
                items.append(
                    (
                        alert["category"],
                        f'{alert["time"].strftime("%Y-%m-%d %H:%M")} · {alert["room"]} · {alert["status"]}',
                        state_badge(alert["level"]),
                    )
                )
            st.markdown(mini_rows(items), unsafe_allow_html=True)
        else:
            empty_state(
                "目前没有告警记录",
                "可在「告警中心」生成 DEMO 模拟告警。" if DEMO_MODE else "设备上报异常后会自动出现在这里。",
            )

    with lower_right:
        section_title("设备运行状态", f"在线 {online} / {len(devices)}")

        if devices:
            items = []
            for device in devices:
                heartbeat = (
                    device["last_seen"].strftime("%H:%M:%S") if device["last_seen"] else "暂无数据"
                )
                items.append(
                    (
                        device["name"],
                        f'{device["id"]} · {device["room"]} · 心跳 {heartbeat}',
                        badge(device["status"], DEVICE_STATUS_TONE.get(device["status"], "muted")),
                    )
                )
            st.markdown(mini_rows(items), unsafe_allow_html=True)
        else:
            empty_state("尚未添加设备", "前往「设备管理」添加 DEMO 设备。")


# ============================================================
# 管理员 · 人员档案管理
# ============================================================


def page_persons():
    if page_header(
        "人员档案管理",
        "维护被监护人员基础信息与紧急联系人",
        "资产 / 人员档案",
        "refresh_persons",
    ):
        refresh_data()
        st.rerun()

    persons = st.session_state.persons

    section_title("人员列表", f"共 {len(persons)} 份档案")

    if persons:
        rows = pd.DataFrame(
            [
                {
                    "档案编号": p["id"],
                    "姓名": p["name"],
                    "年龄": p["age"],
                    "与家属关系": p["relation"],
                    "监测房间": p["room"],
                    "紧急联系人": p["contact"],
                    "联系电话": mask_phone(p["phone"]),
                }
                for p in persons
            ]
        )
        data_table(rows, max_rows=50)
    else:
        empty_state("暂无人员档案", "使用下方表单新增第一位被监护人。")

    with st.expander("＋ 新增监护人员", expanded=False):
        with st.form("person_form"):
            col_a, col_b = st.columns(2)

            with col_a:
                name = st.text_input("姓名", key="np_name")
                age = st.number_input("年龄", min_value=1, max_value=120, value=70, key="np_age")
                relation = st.text_input("与家属关系", value="父亲", key="np_relation")

            with col_b:
                contact = st.text_input("紧急联系人姓名", key="np_contact")
                phone = st.text_input("紧急联系人电话", key="np_phone")
                room = st.selectbox("监测房间", st.session_state.areas, key="np_room")

            if st.form_submit_button("保存人员档案", type="primary"):
                if not name.strip() or not contact.strip() or not phone.strip():
                    st.error("姓名、紧急联系人和联系电话不能为空")
                elif not phone.strip().isdigit() or len(phone.strip()) != 11:
                    st.error("请输入有效的 11 位联系电话")
                else:
                    try:
                        source().create_person(
                            {
                                "id": "P" + uuid.uuid4().hex[:6].upper(),
                                "name": name.strip(),
                                "age": int(age),
                                "contact": contact.strip(),
                                "phone": phone.strip(),
                                "room": room,
                                "relation": relation.strip() or "家属",
                            }
                        )
                    except DataSourceError as exc:
                        st.error(f"保存失败：{exc}")
                    else:
                        st.success("人员档案添加成功")
                        st.rerun()

    if persons:
        with st.expander("－ 删除监护人员", expanded=False):
            st.caption("删除后该档案从当前会话移除，不可撤销；相关历史告警与监测记录不受影响。")
            del_labels = {f'{p["name"]}（{p["id"]}）': p["id"] for p in persons}
            del_choice = st.selectbox(
                "选择要删除的人员", list(del_labels.keys()), key="del_pid"
            )
            del_pid = del_labels[del_choice]
            del_person = person_by_id(del_pid)
            del_name = del_person["name"] if del_person else del_choice
            del_room = del_person["room"] if del_person else ""
            st.caption(f"将删除：{del_name}（{del_pid}） · 监测房间 {del_room}")
            del_ok = st.checkbox(
                f"我确认删除 {del_name} 的档案", key="confirm_del_" + del_pid
            )
            if st.button(
                "删除该人员档案",
                key="delete_person_inline",
                disabled=not del_ok,
                width="stretch",
            ):
                try:
                    source().delete_person(del_pid)
                except DataSourceError as exc:
                    st.error(f"删除失败：{exc}")
                else:
                    st.success(f"{del_name} 的档案已删除")
                    st.rerun()

    if not persons:
        return

    section_title("编辑档案", "修改后立即生效，仅作用于当前会话")

    labels = {f'{p["name"]}（{p["id"]}）': p["id"] for p in persons}
    options = list(labels.keys())

    # 姓名被修改后，原选项标签会失效，这里按档案编号重新对齐，避免选择跳回第一项
    stored = st.session_state.get("edit_pid")
    if stored not in options:
        prev_id = stored.split("（")[-1].rstrip("）") if isinstance(stored, str) else None
        matched = [o for o in options if o.endswith(f"（{prev_id}）")]
        st.session_state["edit_pid"] = matched[0] if matched else options[0]

    chosen = st.selectbox("选择人员", options, key="edit_pid")
    pid = labels[chosen]

    selected = person_by_id(pid)

    if selected is None:
        return

    # 表单控件按档案编号分键，切换人员时加载对应档案的当前值
    with st.form("edit_person_form_" + pid):
        col_a, col_b = st.columns(2)

        with col_a:
            edit_name = st.text_input(
                "姓名", value=selected["name"], key="ep_name_" + pid
            )
            edit_age = st.number_input(
                "年龄",
                min_value=1,
                max_value=120,
                value=int(selected["age"]),
                key="ep_age_" + pid,
            )
            edit_relation = st.text_input(
                "与家属关系",
                value=selected["relation"],
                key="ep_relation_" + pid,
            )

        with col_b:
            edit_contact = st.text_input(
                "紧急联系人", value=selected["contact"], key="ep_contact_" + pid
            )
            edit_phone = st.text_input(
                "联系电话", value=selected["phone"], key="ep_phone_" + pid
            )
            edit_room = st.selectbox(
                "监测房间",
                st.session_state.areas,
                index=(
                    st.session_state.areas.index(selected["room"])
                    if selected["room"] in st.session_state.areas
                    else 0
                ),
                key="ep_room_" + pid,
            )

        if st.form_submit_button("保存修改", type="primary"):
            if not edit_name.strip() or not edit_contact.strip():
                st.error("姓名和紧急联系人不能为空")
            elif not edit_phone.strip().isdigit() or len(edit_phone.strip()) != 11:
                st.error("请输入有效的 11 位联系电话")
            else:
                try:
                    source().update_person(
                        pid,
                        {
                            "name": edit_name.strip(),
                            "age": int(edit_age),
                            "relation": edit_relation.strip() or selected["relation"],
                            "contact": edit_contact.strip(),
                            "phone": edit_phone.strip(),
                            "room": edit_room,
                        },
                    )
                except DataSourceError as exc:
                    st.error(f"保存失败：{exc}")
                else:
                    st.success("档案已更新")
                    st.rerun()

    with st.expander("危险操作 · 删除人员档案"):
        st.caption("删除后该档案将从当前会话中移除，操作不可撤销。")
        confirmed = st.checkbox(
            f"我确认删除 {selected['name']} 的档案",
            key="confirm_delete_person_" + pid,
        )

        if st.button(
            "删除该人员档案",
            key="delete_person_btn",
            disabled=not confirmed,
            width="stretch",
        ):
            try:
                source().delete_person(pid)
            except DataSourceError as exc:
                st.error(f"删除失败：{exc}")
            else:
                st.success("人员档案已删除")
                st.rerun()


# ============================================================
# 管理员 · 设备管理
# ============================================================


def page_devices():
    if page_header(
        "设备管理",
        "ESP32 感知设备台账、在线状态与模拟重连",
        "资产 / 设备管理",
        "refresh_devices",
    ):
        refresh_data()
        st.rerun()

    devices = st.session_state.devices
    online = sum(1 for d in devices if d["status"] == "在线")

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card("设备数量", len(devices), "全部为 DEMO 登记设备")
    with cols[1]:
        metric_card("在线设备", online, "状态为模拟值", tone="ok")
    with cols[2]:
        metric_card(
            "未连接设备",
            len(devices) - online,
            "等待接入或离线",
            tone="warn" if len(devices) - online else "ok",
        )

    section_title("设备清单", f"共 {len(devices)} 台")

    if not devices:
        empty_state("暂无设备", "使用下方表单添加一台 DEMO 设备。")

    for device in devices:
        with st.container(border=True):
            col_a, col_b = st.columns([4, 1.5], gap="large", vertical_alignment="center")

            with col_a:
                heartbeat = (
                    device["last_seen"].strftime("%Y-%m-%d %H:%M:%S")
                    if device["last_seen"]
                    else "暂无数据"
                )
                st.markdown(
                    f'<div class="acard-head">'
                    f'{badge(device["status"], DEVICE_STATUS_TONE.get(device["status"], "muted"))}'
                    f'{badge("已启用" if device["enabled"] else "已停用", "accent" if device["enabled"] else "muted")}'
                    f'{data_mode_badge()}</div>'
                    f'<div class="dcard-title">{esc(device["name"])}</div>'
                    f'<div class="dcard-meta">编号 {device["id"]} · 类型 {esc(device["type"])} · 房间 {esc(device["room"])}</div>'
                    f'<div class="dcard-meta">最近心跳：{esc(heartbeat)}</div>',
                    unsafe_allow_html=True,
                )

            with col_b:
                enabled = st.toggle(
                    "启用设备",
                    value=device["enabled"],
                    key="toggle_" + device["id"],
                )
                if enabled != device["enabled"]:
                    try:
                        source().set_device_enabled(device["id"], enabled)
                    except DataSourceError as exc:
                        st.error(f"启用状态保存失败：{exc}")
                    else:
                        device["enabled"] = enabled
                        st.rerun()

                if st.button(
                    "模拟重连（演示）",
                    key="reconnect_" + device["id"],
                    width="stretch",
                ):
                    try:
                        result = source().reconnect_device(device["id"]) or {}
                    except DataSourceError as exc:
                        st.error(f"重连失败：{exc}")
                    else:
                        device["status"] = result.get("status") or device["status"]
                        device["last_seen"] = (
                            result.get("last_seen") or datetime.now()
                        )
                        if device["status"] != "在线":
                            st.warning("后端未返回在线状态，设备仍显示为未连接。")
                        st.rerun()

    st.caption("「模拟重连」仅演示界面状态变化，不包含任何真实设备通信能力。")

    if devices:
        section_title("编辑设备", "编号创建后不可修改，其余字段改完立即生效")

        dev_labels = {f'{d["name"]}（{d["id"]}）': d["id"] for d in devices}
        dev_options = list(dev_labels.keys())

        # 名称被改后原标签会失效，按设备编号重新对齐，避免选择跳回第一台
        stored_dev = st.session_state.get("edit_did")
        if stored_dev not in dev_options:
            prev_dev = (
                stored_dev.split("（")[-1].rstrip("）")
                if isinstance(stored_dev, str)
                else None
            )
            matched_dev = [o for o in dev_options if o.endswith(f"（{prev_dev}）")]
            st.session_state["edit_did"] = (
                matched_dev[0] if matched_dev else dev_options[0]
            )

        chosen_dev = st.selectbox("选择设备", dev_options, key="edit_did")
        did = dev_labels[chosen_dev]
        dev = device_by_id(did)

        if dev is not None:
            type_options = ["ESP32-WIFI", "ESP32-TEMP"]
            if dev["type"] not in type_options:
                type_options = [dev["type"]] + type_options

            room_options = list(st.session_state.areas)
            if dev["room"] not in room_options:
                room_options = room_options + [dev["room"]]

            with st.form("edit_device_form_" + did):
                col_a, col_b = st.columns(2)

                with col_a:
                    dev_name = st.text_input(
                        "设备名称", value=dev["name"], key="ed_name_" + did
                    )
                    dev_type = st.selectbox(
                        "设备类型",
                        type_options,
                        index=type_options.index(dev["type"]),
                        key="ed_type_" + did,
                    )

                with col_b:
                    dev_room = st.selectbox(
                        "所属房间",
                        room_options,
                        index=room_options.index(dev["room"]),
                        key="ed_room_" + did,
                    )
                    st.caption(f"设备编号 {did} 创建后不可修改")

                if st.form_submit_button("保存设备信息", type="primary"):
                    if not dev_name.strip():
                        st.error("设备名称不能为空")
                    else:
                        try:
                            source().update_device(
                                did,
                                {
                                    "name": dev_name.strip(),
                                    "type": dev_type,
                                    "room": dev_room,
                                },
                            )
                        except DataSourceError as exc:
                            st.error(f"保存失败：{exc}")
                        else:
                            dev.update(
                                {
                                    "name": dev_name.strip(),
                                    "type": dev_type,
                                    "room": dev_room,
                                }
                            )
                            st.success("设备信息已更新")
                            st.rerun()

        with st.expander("－ 删除设备", expanded=False):
            st.caption("删除后该设备从当前会话移除，不可撤销；相关历史监测记录不受影响。")

            del_dev_labels = {f'{d["name"]}（{d["id"]}）': d["id"] for d in devices}
            del_dev_choice = st.selectbox(
                "选择要删除的设备", list(del_dev_labels.keys()), key="del_device_sel"
            )
            del_did = del_dev_labels[del_dev_choice]
            del_dev = device_by_id(del_did)

            if del_dev is None:
                st.caption("该设备已不存在，请重新选择。")
            else:
                st.caption(
                    f"将删除：{del_dev['name']}（{del_dev['id']}） · "
                    f"类型 {del_dev['type']} · 房间 {del_dev['room']}"
                )
                del_dev_ok = st.checkbox(
                    f"我确认删除设备 {del_dev['name']}",
                    key="confirm_del_dev_" + del_did,
                )
                if st.button(
                    "删除该设备",
                    key="delete_device_btn",
                    disabled=not del_dev_ok,
                    width="stretch",
                ):
                    try:
                        source().delete_device(del_did)
                    except DataSourceError as exc:
                        st.error(f"删除失败：{exc}")
                    else:
                        st.success(f"{del_dev['name']} 已删除")
                        st.rerun()

    section_title("添加设备", "设备编号需唯一")

    with st.form("device_form"):
        col_a, col_b = st.columns(2)

        with col_a:
            device_name = st.text_input("设备名称", key="nd_name")
            device_type = st.selectbox(
                "设备类型", ["ESP32-WIFI", "ESP32-TEMP"], key="nd_type"
            )

        with col_b:
            device_id = st.text_input("设备编号", key="nd_id")
            device_room = st.selectbox("所属房间", st.session_state.areas, key="nd_room")

        if st.form_submit_button("添加设备", type="primary"):
            if not device_name.strip() or not device_id.strip():
                st.error("请填写设备名称和编号")
            elif any(d["id"] == device_id.strip() for d in devices):
                st.error("设备编号已存在")
            else:
                try:
                    source().create_device(
                        {
                            "id": device_id.strip(),
                            "name": device_name.strip(),
                            "type": device_type,
                            "room": device_room,
                            "status": "等待接入",
                            "enabled": True,
                            "last_seen": None,
                        }
                    )
                except DataSourceError as exc:
                    st.error(f"添加失败：{exc}")
                else:
                    st.success("设备添加成功")
                    st.rerun()

    st.info(
        "当前设备管理为应用层演示。真实在线状态、心跳上报与参数下发，"
        "需要后续对接 ESP32 系统层接口。"
    )


# ============================================================
# 管理员 · 实时监测
# ============================================================


def page_live():
    if page_header(
        "实时监测",
        "按监测区域查看当前状态、变化趋势与原始数据",
        "监测 / 实时监测",
        "refresh_live",
    ):
        refresh_data()
        st.rerun()

    df = st.session_state.demo_df

    if df is None or df.empty:
        empty_state("暂无监测数据", "点击右上角「刷新数据」生成 DEMO 数据。")
        return

    room = st.selectbox("监测区域", st.session_state.areas, key="live_room")
    current = df[df["监测区域"] == room]

    if current.empty:
        empty_state("该区域暂无数据", "当前 DEMO 数据批次未覆盖此监测区域，请刷新或切换区域。")
        return

    latest = current.iloc[-1]

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card(
            "当前活动状态",
            latest["活动状态"],
            "DEMO 识别结果" if DEMO_MODE else "算法识别结果",
            tone="accent",
        )
    with cols[1]:
        metric_card("环境温度", fmt_temp(latest["环境温度"]), temp_limit_text("ambient_limit", 28.0))
    with cols[2]:
        metric_card("表面温度", fmt_temp(latest["表面温度"]), temp_limit_text("surface_limit", 35.0))

    st.caption(
        f"监测区域：{room} · 数据更新于 "
        f'{st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S")} · {DATA_MODE_CAPTION}'
    )

    section_title("空间状态", "按房间查看当前活动强度、设备连接与待处理告警")
    space_view(space_rooms(df, focus=room), st.session_state.last_refresh)

    section_title("活动变化趋势", "线条取值为活动等级：静止 / 活动 / 移动")
    plot_chart(activity_figure(current, height=300, markers=True))

    section_title("温度变化趋势", "环境温度与表面温度")
    plot_chart(temperature_figure(current, height=280))

    section_title("原始监测数据", f"{len(current)} 条记录，按时间倒序")

    ordered = current.sort_values("时间", ascending=False)[
        ["时间", "监测区域", "活动状态", "环境温度", "表面温度"]
    ]
    data_table(ordered, max_rows=80)


# ============================================================
# 管理员 · 告警中心
# ============================================================


def page_alerts():
    if page_header(
        "告警中心",
        "查看、确认与导出监测告警记录",
        "监测 / 告警中心",
        "refresh_alerts",
    ):
        refresh_data()
        st.rerun()

    alerts = st.session_state.alerts
    pending = len(get_pending_alerts())
    confirmed = sum(1 for a in alerts if a["status"] == "已确认")

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card("全部告警", len(alerts), "含已确认记录")
    with cols[1]:
        metric_card("待处理", pending, "需管理员确认", tone="warn" if pending else "ok")
    with cols[2]:
        metric_card("已确认", confirmed, "已完成处理", tone="ok")

    if DEMO_MODE:
        with st.container(border=True):
            st.markdown(
                '<div class="acard-head">' + badge("DEMO 模拟", "muted")
                + '<span class="acard-cat">演示告警生成</span></div>'
                '<div class="acard-msg">以下按钮仅生成演示用的模拟告警，'
                "不代表真实设备或算法输出。</div>",
                unsafe_allow_html=True,
            )

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("生成严重告警（模拟）", key="gen_severe", width="stretch"):
                    try:
                        create_alert(
                            "严重",
                            "异常活动",
                            "监测系统检测到疑似异常活动，请及时查看现场情况。",
                            random.choice(st.session_state.areas),
                        )
                    except DataSourceError as exc:
                        st.error(f"生成告警失败：{exc}")
                    else:
                        st.rerun()

            with col_b:
                if st.button("生成温度告警（模拟）", key="gen_temp", width="stretch"):
                    try:
                        create_alert(
                            "关注",
                            "温度异常",
                            "监测区域温度超过预设关注阈值，请检查环境。",
                            random.choice(st.session_state.areas),
                        )
                    except DataSourceError as exc:
                        st.error(f"生成告警失败：{exc}")
                    else:
                        st.rerun()


    section_title("告警列表", f"共 {len(alerts)} 条，按时间倒序")

    if not alerts:
        empty_state(
            "暂无告警记录",
            "点击上方按钮生成一条 DEMO 模拟告警。"
            if DEMO_MODE
            else "设备上报异常后会自动出现在这里。",
        )
        return

    for alert in alerts:
        with st.container(border=True):
            col_a, col_b = st.columns([4, 1.2], gap="large", vertical_alignment="center")

            with col_a:
                st.markdown(
                    f'<div class="acard-head">{state_badge(alert["level"])}'
                    f'<span class="acard-cat">{esc(alert["category"])}</span>'
                    f'{data_mode_badge()}</div>'
                    f'<div class="acard-msg">{esc(alert["message"])}</div>'
                    f'<div class="acard-meta">{alert["time"].strftime("%Y-%m-%d %H:%M:%S")} · {esc(alert["room"])} · {alert["id"]}</div>',
                    unsafe_allow_html=True,
                )

            with col_b:
                st.markdown(
                    f'<div style="text-align:center;margin-bottom:8px">{alert_badge(alert["status"])}</div>',
                    unsafe_allow_html=True,
                )
                if alert["status"] == "待处理":
                    if st.button(
                        "确认告警",
                        key="ack_" + alert["id"],
                        width="stretch",
                    ):
                        try:
                            acknowledge_alert(alert["id"])
                        except DataSourceError as exc:
                            st.error(f"确认失败：{exc}")
                        else:
                            st.rerun()

    st.download_button(
        "导出告警记录（CSV）",
        pd.DataFrame(alerts).to_csv(index=False).encode("utf-8-sig"),
        "wifi_sense_alerts.csv",
        "text/csv",
        width="stretch",
    )


# ============================================================
# 管理员 · 历史数据
# ============================================================


def page_history():
    if page_header(
        "历史数据",
        "筛选、查看与导出历史监测记录",
        "监测 / 历史数据",
        "refresh_history",
    ):
        refresh_data()
        st.rerun()

    df = st.session_state.demo_df

    if df is None or df.empty:
        empty_state("暂无历史数据", "点击右上角「刷新数据」生成 DEMO 数据。")
        return

    filter_col, _spacer = st.columns([1.2, 3.8])

    with filter_col:
        room = st.selectbox(
            "监测区域", ["全部"] + st.session_state.areas, key="history_room"
        )

    view = df.copy()

    if room != "全部":
        view = view[view["监测区域"] == room]

    view = view.sort_values("时间", ascending=False)

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card("数据记录", len(view), f"筛选：{room}")

    if not view.empty:
        with cols[1]:
            metric_card("平均环境温度", f'{view["环境温度"].mean():.1f} °C', "当前筛选区间")
        with cols[2]:
            metric_card("活动记录", int((view["活动等级"] > 0).sum()), "活动或移动状态记录数")

    section_title("历史监测记录", f"显示前 {min(len(view), 150)} 条")

    if view.empty:
        empty_state("筛选结果为空", "请切换监测区域后重新查看。")
        return

    data_table(
        view[["时间", "监测区域", "活动状态", "环境温度", "表面温度"]],
        max_rows=150,
    )

    st.download_button(
        "导出历史数据（CSV）",
        view.to_csv(index=False).encode("utf-8-sig"),
        "wifi_sense_history.csv",
        "text/csv",
        width="stretch",
    )


# ============================================================
# 管理员 · 监测任务
# ============================================================


def page_tasks():
    if page_header(
        "监测任务",
        "创建与调度 DEMO 监测任务（非真实设备调度）",
        "监测 / 监测任务",
        "refresh_tasks",
    ):
        refresh_data()
        st.rerun()

    tasks = st.session_state.tasks

    running = sum(1 for t in tasks if t["status"] == "运行中")
    paused = sum(1 for t in tasks if t["status"] == "已暂停")
    finished = sum(1 for t in tasks if t["status"] == "已结束")

    cols = st.columns(4, gap="medium")

    with cols[0]:
        metric_card("全部任务", len(tasks), "当前会话内创建")
    with cols[1]:
        metric_card("运行中", running, "互斥：同时仅一个", tone="ok" if running else "muted")
    with cols[2]:
        metric_card("已暂停", paused, "可恢复运行", tone="warn" if paused else "muted")
    with cols[3]:
        metric_card("已结束", finished, "不可恢复", tone="muted")

    with st.expander("＋ 新建监测任务", expanded=not tasks):
        with st.form("task_form"):
            col_a, col_b = st.columns(2)

            with col_a:
                name = st.text_input("任务名称", key="nt_name")
                room = st.selectbox("监测区域", st.session_state.areas, key="nt_room")

            with col_b:
                mode = st.selectbox(
                    "监测模式", ["持续监测", "定时监测", "手动监测"], key="nt_mode"
                )
                duration = st.number_input(
                    "计划时长（分钟）", min_value=1, max_value=1440, value=60, key="nt_duration"
                )

            if st.form_submit_button("创建任务", type="primary"):
                if not name.strip():
                    st.error("请输入任务名称")
                else:
                    try:
                        source().create_task(
                            {
                                "id": "TASK-" + uuid.uuid4().hex[:8].upper(),
                                "name": name.strip(),
                                "room": room,
                                "mode": mode,
                                "duration": int(duration),
                                "status": "待启动",
                                "created_at": datetime.now(),
                                "started_at": None,
                            }
                        )
                    except DataSourceError as exc:
                        st.error(f"创建失败：{exc}")
                    else:
                        st.success("任务创建成功")
                        st.rerun()

    section_title("任务列表", f"共 {len(tasks)} 个任务")

    if not tasks:
        empty_state("暂无监测任务", "使用上方表单创建第一个 DEMO 任务。")
        return

    for task in tasks:
        tone = TASK_STATUS_TONE.get(task["status"], "muted")

        with st.container(border=True):
            col_a, col_b = st.columns([3.6, 2.2], gap="large", vertical_alignment="center")

            with col_a:
                started = (
                    task["started_at"].strftime("%Y-%m-%d %H:%M")
                    if task["started_at"]
                    else "未启动"
                )
                st.markdown(
                    f'<div class="acard-head">{badge(task["status"], tone)}'
                    f'{data_mode_badge()}'
                    f'<span class="acard-cat">{esc(task["name"])}</span></div>'
                    f'<div class="acard-meta">编号 {task["id"]} · 区域 {esc(task["room"])} · 模式 {esc(task["mode"])}</div>'
                    f'<div class="acard-meta">计划时长 {task["duration"]} 分钟 · 创建于 {task["created_at"].strftime("%Y-%m-%d %H:%M")} · 启动于 {esc(started)}</div>',
                    unsafe_allow_html=True,
                )

            with col_b:
                if task["status"] == "待启动":
                    action_cols = st.columns(1)
                    with action_cols[0]:
                        if st.button(
                            "启动任务",
                            key="start_" + task["id"],
                            type="primary",
                            width="stretch",
                        ):
                            if any(
                                t["status"] == "运行中" for t in st.session_state.tasks
                            ):
                                st.error("已有任务正在运行，请先暂停或结束。")
                            else:
                                try:
                                    result = (
                                        source().task_action(task["id"], "start") or {}
                                    )
                                except DataSourceError as exc:
                                    st.error(f"启动失败：{exc}")
                                else:
                                    task["status"] = result.get("status") or "运行中"
                                    task["started_at"] = (
                                        result.get("started_at")
                                        or task["started_at"]
                                        or datetime.now()
                                    )
                                    st.rerun()

                elif task["status"] == "运行中":
                    action_cols = st.columns(2)
                    with action_cols[0]:
                        if st.button("暂停", key="pause_" + task["id"], width="stretch"):
                            try:
                                source().task_action(task["id"], "pause")
                            except DataSourceError as exc:
                                st.error(f"暂停失败：{exc}")
                            else:
                                task["status"] = "已暂停"
                                st.rerun()
                    with action_cols[1]:
                        if st.button("结束", key="end_" + task["id"], width="stretch"):
                            try:
                                source().task_action(task["id"], "end")
                            except DataSourceError as exc:
                                st.error(f"结束失败：{exc}")
                            else:
                                task["status"] = "已结束"
                                st.rerun()

                elif task["status"] == "已暂停":
                    action_cols = st.columns(2)
                    with action_cols[0]:
                        if st.button(
                            "恢复运行",
                            key="resume_" + task["id"],
                            type="primary",
                            width="stretch",
                        ):
                            if any(
                                t["status"] == "运行中" for t in st.session_state.tasks
                            ):
                                st.error("已有任务正在运行，请先暂停或结束。")
                            else:
                                try:
                                    result = (
                                        source().task_action(task["id"], "resume") or {}
                                    )
                                except DataSourceError as exc:
                                    st.error(f"恢复失败：{exc}")
                                else:
                                    task["status"] = result.get("status") or "运行中"
                                    st.rerun()
                    with action_cols[1]:
                        if st.button("结束", key="endp_" + task["id"], width="stretch"):
                            try:
                                source().task_action(task["id"], "end")
                            except DataSourceError as exc:
                                st.error(f"结束失败：{exc}")
                            else:
                                task["status"] = "已结束"
                                st.rerun()

                else:
                    st.caption("任务已结束，不可再操作。")

    st.caption("任务状态为应用层演示，不涉及真实设备调度或数据采集启停。")


# ============================================================
# 管理员 · 系统配置
# ============================================================


def page_settings():
    if page_header(
        "系统配置",
        "识别参数与监测区域管理（仅保存在当前会话）",
        "系统 / 配置",
        "refresh_settings",
    ):
        refresh_data()
        st.rerun()

    params = st.session_state.params

    col_left, col_right = st.columns([1.15, 1], gap="large")

    with col_left:
        section_title("识别参数配置", "应用层演示参数")

        with st.container(border=True):
            threshold = st.slider(
                "活动识别阈值",
                min_value=0.0,
                max_value=1.0,
                value=float(params["activity_threshold"]),
                step=0.01,
                key="cfg_threshold",
            )
            ambient = st.number_input(
                "环境温度预警阈值（°C）",
                value=float(params["ambient_limit"]),
                step=0.1,
                key="cfg_ambient",
            )
            surface = st.number_input(
                "表面温度预警阈值（°C）",
                value=float(params["surface_limit"]),
                step=0.1,
                key="cfg_surface",
            )
            duration = st.number_input(
                "异常持续时间（秒）",
                min_value=1,
                max_value=3600,
                value=int(params["abnormal_duration"]),
                key="cfg_duration",
            )

            if st.button(
                "保存识别参数",
                key="save_params",
                type="primary",
                width="stretch",
            ):
                try:
                    source().save_settings(
                        {
                            "activity_threshold": float(threshold),
                            "ambient_limit": float(ambient),
                            "surface_limit": float(surface),
                            "abnormal_duration": int(duration),
                        }
                    )
                except DataSourceError as exc:
                    st.error(f"保存失败：{exc}")
                else:
                    params.update(
                        {
                            "activity_threshold": float(threshold),
                            "ambient_limit": float(ambient),
                            "surface_limit": float(surface),
                            "abnormal_duration": int(duration),
                        }
                    )
                    st.success("应用层参数已保存")

            st.caption("参数仅保存在当前应用会话中，未下发至 ESP32 设备。")

    with col_right:
        section_title("监测区域管理", f"当前 {len(st.session_state.areas)} 个区域")

        with st.container(border=True):
            new_area = st.text_input("新增监测区域", key="new_area_name")

            if st.button("添加监测区域", key="add_area", width="stretch"):
                name = new_area.strip()

                if not name:
                    st.warning("区域名称不能为空")
                elif name in st.session_state.areas:
                    st.warning("该区域已存在")
                else:
                    try:
                        source().add_area(name)
                    except DataSourceError as exc:
                        st.error(f"添加失败：{exc}")
                    else:
                        st.success("区域添加成功")
                        st.rerun()

            chips = "".join(
                f'<span class="chip">{esc(area)}</span>' for area in st.session_state.areas
            )
            st.markdown(f'<div style="margin-top:12px">{chips}</div>', unsafe_allow_html=True)

        with st.expander("－ 删除监测区域", expanded=False):
            st.caption("被人员档案、设备或任务引用的区域不允许删除，需先解除引用。")

            if len(st.session_state.areas) <= 1:
                st.caption("至少需要保留一个监测区域。")
            else:
                area_choice = st.selectbox(
                    "选择要删除的区域", st.session_state.areas, key="del_area_sel"
                )

                refs = []
                for item in st.session_state.persons:
                    if item["room"] == area_choice:
                        refs.append(f"人员 {item['name']}")
                for item in st.session_state.devices:
                    if item["room"] == area_choice:
                        refs.append(f"设备 {item['name']}")
                for item in st.session_state.tasks:
                    if item["room"] == area_choice:
                        refs.append(f"任务 {item['name']}")

                if refs:
                    preview = "、".join(refs[:5]) + ("…" if len(refs) > 5 else "")
                    st.warning(f"该区域仍被 {len(refs)} 条记录占用：{preview}")
                else:
                    st.caption(f"将删除：{area_choice}")

                area_ok = st.checkbox(
                    f"我确认删除区域 {area_choice}",
                    key="confirm_del_area_" + area_choice,
                )

                if st.button(
                    "删除该监测区域",
                    key="delete_area_btn",
                    disabled=bool(refs) or not area_ok,
                    width="stretch",
                ):
                    try:
                        source().delete_area(area_choice)
                    except DataSourceError as exc:
                        st.error(f"删除失败：{exc}")
                    else:
                        st.success(f"区域「{area_choice}」已删除")
                        st.rerun()

        st.caption("区域列表用于演示数据与设备归属，不会同步到真实系统。")

        section_title("空间布局精调", "位置与大小用百分比表示；不调则沿用自动排布")

        with st.container(border=True):
            areas_now = list(st.session_state.areas)
            auto_layout = _zone_layout(areas_now)
            saved_layout = dict(st.session_state.get("zone_layout") or {})

            tpl = st.selectbox(
                "布局模板",
                ["自动排布", "单列排布", "双列排布", "三列排布"],
                key="space_tpl",
            )

            if st.button("按模板重置", key="space_tpl_apply"):
                cols = {"单列排布": 1, "双列排布": 2, "三列排布": 3}.get(tpl)
                st.session_state.zone_layout = _zone_grid(areas_now, cols) if cols else {}
                st.rerun()

            with st.expander("－ 逐个区域微调（位置 / 大小）", expanded=False):
                for name in areas_now:
                    base = saved_layout.get(name) or auto_layout[name]
                    st.markdown(f"**{esc(name)}**")
                    c1, c2, c3, c4 = st.columns(4)
                    x = c1.number_input(
                        "左 X %", 0.0, 90.0, round(float(base["x"]) * 100, 1), 1.0,
                        key=f"zl_x_{name}",
                    )
                    y = c2.number_input(
                        "上 Y %", 0.0, 90.0, round(float(base["y"]) * 100, 1), 1.0,
                        key=f"zl_y_{name}",
                    )
                    w = c3.number_input(
                        "宽 %", 10.0, 100.0, round(float(base["w"]) * 100, 1), 1.0,
                        key=f"zl_w_{name}",
                    )
                    h = c4.number_input(
                        "深 %", 10.0, 100.0, round(float(base["h"]) * 100, 1), 1.0,
                        key=f"zl_h_{name}",
                    )
                    saved_layout[name] = {
                        "x": x / 100.0,
                        "y": y / 100.0,
                        "w": w / 100.0,
                        "h": h / 100.0,
                        "height": float(base.get("height", 0.08)),
                    }
                st.caption("改动即时生效并保存在当前会话；尚未下发到后端。")

            st.session_state.zone_layout = saved_layout

            if DEMO_MODE:
                st.caption("演示模式：布局保存在当前会话，接入后端后随参数一起下发。")
            elif st.button("提交布局到后端", key="space_layout_push"):
                try:
                    source().save_settings(dict(st.session_state.params), list(areas_now))
                except DataSourceError as exc:
                    st.error(f"提交失败：{exc}")
                else:
                    if st.session_state.get("zone_layout_unsupported"):
                        st.warning("后端暂不支持 zone_layout，已保留在本地会话。")
                    else:
                        st.success("布局已提交到后端")

            df_now = st.session_state.get("demo_df")
            if df_now is None or df_now.empty:
                st.caption("生成 DEMO 数据后可在此预览布局。")
            else:
                space_view(
                    space_rooms(df_now, layout=_zone_layout(areas_now, saved_layout)),
                    st.session_state.last_refresh,
                    height=300,
                )


# ============================================================
# 家属 · 家庭监护首页
# ============================================================


def page_family_home():
    if page_header(
        "家庭监护首页",
        "家人的房间状态与需要关注的提醒",
        "总览 / 家庭监护",
        "refresh_family_home",
    ):
        refresh_data()
        st.rerun()

    person = get_current_person()

    if person is None:
        empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
        return

    df = st.session_state.demo_df

    if df is None or df.empty:
        empty_state("暂无监测数据", "点击右上角「刷新数据」生成 DEMO 数据。")
        return

    current = df[df["监测区域"] == person["room"]]

    if current.empty:
        empty_state("暂时没有收到该房间的数据", "请稍后刷新，或联系管理员确认监测区域配置。")
        return

    latest = current.iloc[-1]
    pending = get_pending_alerts(person)

    if pending and any(a["level"] == "严重" for a in pending):
        banner(
            "danger",
            f"需要您关注：{person['name']} 的房间出现严重提醒",
            "系统检测到需要尽快核实的情况，请先联系现场人员确认，必要时联系紧急联系人。",
        )
    elif pending:
        banner(
            "warn",
            f"温馨提醒：{person['name']} 的房间存在待处理提醒",
            "监测区域出现需要关注的情况，建议查看提醒详情后与家人确认。",
        )
    elif latest["活动状态"] == "静止":
        banner(
            "ok",
            "当前状态平稳",
            "房间内活动较少，系统暂未发现需要关注的告警。静止状态仅代表活动水平低，"
            "不能据此判断身体情况。",
        )
    else:
        banner(
            "ok",
            f"当前监测到{latest['活动状态']}",
            "系统暂未发现需要处理的告警，画面会随数据刷新持续更新。",
        )

    cols = st.columns(4, gap="medium")

    with cols[0]:
        metric_card("当前状态", latest["活动状态"], "系统识别结果，仅供参考", tone="accent")
    with cols[1]:
        metric_card("环境温度", f'{latest["环境温度"]:.1f} °C', "房间环境")
    with cols[2]:
        metric_card("表面温度", f'{latest["表面温度"]:.1f} °C', "接触面温度")
    with cols[3]:
        metric_card(
            "待处理提醒",
            len(pending),
            "需要您查看的事项",
            tone="danger" if pending else "ok",
        )

    section_title("今日监护情况")

    history_count = sum(1 for a in st.session_state.alerts if a["room"] == person["room"])

    kv_block(
        "监护摘要",
        [
            ("被监护人", f"{person['name']} · {person['age']} 岁 · {person['relation']}"),
            ("监测房间", person["room"]),
            ("数据更新时间", st.session_state.last_refresh.strftime("%Y-%m-%d %H:%M:%S")),
            ("历史告警总数", f"{history_count} 条"),
        ],
    )

    if pending:
        section_title("最新提醒", f"待处理 {len(pending)} 条")

        items = []
        for alert in pending[:3]:
            items.append(
                (
                    alert["category"],
                    f'{alert["time"].strftime("%Y-%m-%d %H:%M")} · {alert["message"]}',
                    state_badge(alert["level"]),
                )
            )
        st.markdown(mini_rows(items), unsafe_allow_html=True)

    st.caption("以上信息由 Wi-Fi 感知系统模拟生成，不能替代现场确认或医疗诊断。")


# ============================================================
# 家属 · 实时监护画面
# ============================================================


def page_family_live():
    if page_header(
        "实时监护画面",
        "当前活动状态与温度变化",
        "总览 / 实时画面",
        "refresh_family_live",
    ):
        refresh_data()
        st.rerun()

    person = get_current_person()

    if person is None:
        empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
        return

    df = st.session_state.demo_df

    if df is None or df.empty:
        empty_state("暂无监测数据", "点击右上角「刷新数据」生成 DEMO 数据。")
        return

    current = df[df["监测区域"] == person["room"]]

    if current.empty:
        empty_state("暂时没有收到该房间的数据", "请稍后刷新，或联系管理员确认监测区域配置。")
        return

    latest = current.iloc[-1]

    if latest["活动状态"] == "静止":
        banner(
            "ok",
            "当前活动较少",
            "仅凭静止状态不能判断人员是否存在异常，如需确认请直接联系家人。",
        )
    elif latest["活动状态"] == "活动":
        banner("ok", "当前监测到活动", "房间内存在活动迹象，系统未发现需要处理的告警。")
    else:
        banner("ok", "当前监测到移动", "房间内存在移动迹象，系统未发现需要处理的告警。")

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card("当前状态", latest["活动状态"], "系统识别结果")
    with cols[1]:
        metric_card("环境温度", f'{latest["环境温度"]:.1f} °C', "房间环境")
    with cols[2]:
        metric_card("表面温度", f'{latest["表面温度"]:.1f} °C', "接触面温度")

    st.caption(
        f"数据更新于 {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')} · {DATA_MODE_CAPTION}"
    )

    section_title("家里的空间状态", "每个房间当前的活动强度与设备连接情况")
    space_view(space_rooms(df, focus=person["room"]), st.session_state.last_refresh)

    section_title("活动变化", "近 3 小时活动等级变化")
    plot_chart(activity_figure(current, height=320, markers=True))

    section_title("温度情况", "环境温度与表面温度")
    plot_chart(temperature_figure(current, height=280))

    st.caption("提示：Wi-Fi 感知数据反映的是系统识别结果，不能替代现场确认或医疗诊断。")


# ============================================================
# 家属 · 我的告警
# ============================================================


def page_my_alerts():
    if page_header(
        "我的告警",
        "当前绑定的被监护人房间的待处理提醒",
        "告警 / 我的告警",
        "refresh_my_alerts",
    ):
        refresh_data()
        st.rerun()

    person = get_current_person()

    if person is None:
        empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
        return

    alerts = [
        a
        for a in st.session_state.alerts
        if a["room"] == person["room"] and a["status"] == "待处理"
    ]

    cols = st.columns(2, gap="medium")

    with cols[0]:
        metric_card("待处理提醒", len(alerts), f"{person['name']} · {person['room']}", tone="warn" if alerts else "ok")
    with cols[1]:
        metric_card(
            "历史告警总数",
            sum(1 for a in st.session_state.alerts if a["room"] == person["room"]),
            "含已确认记录",
        )

    section_title("需要关注的提醒", f"共 {len(alerts)} 条")

    if not alerts:
        empty_state("目前没有待处理的提醒", "系统运行平稳，新的提醒会在这里显示。")
        return

    for alert in alerts:
        with st.container(border=True):
            heart = "严重" if alert["level"] == "严重" else "关注"
            st.markdown(
                f'<div class="acard-head">{state_badge(alert["level"])}'
                f'<span class="acard-cat">{esc(alert["category"])}</span></div>'
                f'<div class="acard-msg">{esc(alert["message"])}</div>'
                f'<div class="acard-meta">{alert["time"].strftime("%Y-%m-%d %H:%M:%S")} · {esc(alert["room"])}</div>',
                unsafe_allow_html=True,
            )
            st.info(
                "建议您及时联系现场人员核实情况。"
                "如存在紧急危险，请直接联系当地急救或紧急服务。"
            )
            st.caption(
                f"提醒等级：{heart} · 状态：{alert['status']}"
                + ("（DEMO 模拟）" if DEMO_MODE else "")
            )


# ============================================================
# 家属 · 历史告警记录
# ============================================================


def page_alert_history():
    if page_header(
        "历史告警记录",
        "绑定房间的全部告警记录与处理状态",
        "告警 / 历史记录",
        "refresh_alert_history",
    ):
        refresh_data()
        st.rerun()

    person = get_current_person()

    if person is None:
        empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
        return

    alerts = [a for a in st.session_state.alerts if a["room"] == person["room"]]

    cols = st.columns(3, gap="medium")

    with cols[0]:
        metric_card("历史告警总数", len(alerts), person["room"])
    with cols[1]:
        metric_card(
            "严重告警",
            sum(1 for a in alerts if a["level"] == "严重"),
            "需要重点关注的记录",
            tone="danger",
        )
    with cols[2]:
        metric_card(
            "已确认",
            sum(1 for a in alerts if a["status"] == "已确认"),
            "管理员已完成处理",
            tone="ok",
        )

    section_title("告警记录", "按时间倒序")

    if not alerts:
        empty_state("暂无历史告警记录", "系统运行平稳，这里会记录历史提醒。")
        return

    for alert in alerts:
        tone_class = " danger" if alert["level"] == "严重" else ""
        st.markdown(
            f'<div class="titem{tone_class}">'
            f'<div class="acard-head">{state_badge(alert["level"])}'
            f'{alert_badge(alert["status"])}'
            f'<span class="acard-cat">{esc(alert["category"])}</span></div>'
            f'<div class="acard-msg">{esc(alert["message"])}</div>'
            f'<div class="acard-meta">{alert["time"].strftime("%Y-%m-%d %H:%M:%S")} · {esc(alert["room"])} · {alert["id"]}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )


# ============================================================
# 家属 · 个人信息
# ============================================================


def page_profile():
    if page_header(
        "个人信息",
        "被监护人资料与紧急联系方式",
        "账户 / 个人信息",
        "refresh_profile",
    ):
        refresh_data()
        st.rerun()

    person = get_current_person()

    if person is None:
        empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
        return

    section_title("被监护人资料", person["room"])

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        kv_block(
            "基本信息",
            [
                ("姓名", person["name"]),
                ("年龄", f"{person['age']} 岁"),
                ("与家属关系", person["relation"]),
                ("监测房间", person["room"]),
            ],
        )

    with col_right:
        kv_block(
            "紧急联系",
            [
                ("联系人", person["contact"]),
                ("联系电话", person["phone"]),
                ("档案编号", person["id"]),
                ("数据模式", DATA_MODE_TEXT),
            ],
        )

    st.caption("如需修改监护信息，请联系管理员在「人员档案管理」中更新。")

    st.info("如发现监测异常，请优先联系现场人员或紧急联系人；紧急情况请直接联系当地急救服务。")


# ============================================================
# 留意（AI 解读）：管理端看全局，家属端只看本户
# ============================================================

_AI_LEVEL_CN = {"info": "正常", "watch": "留意", "alert": "需确认"}
_AI_LEVEL_TONE = {"info": "ok", "watch": "warn", "alert": "danger"}


def _ai_today_summary(rooms):
    """本地汇总：只描述读数事实，不下结论。"""
    active = [r for r in rooms if r.get("activity") in ("活动", "移动")]
    alerts = sum(int(r.get("alerts") or 0) for r in rooms)
    silent = [r for r in rooms if r.get("activity") is None]
    if alerts:
        return f"有 {alerts} 条待处理事项，建议先确认；其余房间状态平稳。", "warn"
    if silent:
        return f"{len(silent)} 间房暂无数据，其余房间未见需要处理的情况。", "warn"
    if active:
        return f"{len(active)} 间房有活动，其余房间安静，未见需要处理的情况。", "ok"
    return "各房间以静止为主，未见需要处理的情况。", "ok"


def _ai_daily_brief(rooms, family=False):
    """生成一段可以直接复制给家人的当日简报，全部基于读数事实。"""
    stamp = st.session_state.last_refresh.strftime("%m月%d日 %H:%M") if st.session_state.last_refresh else ""
    alerts = sum(int(r.get("alerts") or 0) for r in rooms)
    lines = [f"【{stamp} 家里情况】"]
    for room in rooms:
        ai = room.get("ai") or {}
        label = ai.get("label") or (room.get("activity") or "暂无数据")
        plain = ai.get("plain") or ""
        temp = f"，环境 {room['temp']} ℃" if room.get("temp") is not None else ""
        lines.append(f"· {room.get('name')}：{label}{temp}。{plain}")
    if alerts:
        lines.append(f"· 待处理事项：{alerts} 条，建议先看一眼。")
    else:
        lines.append("· 待处理事项：无。")
    lines.append("（以上为 Wi-Fi 感知数据的自动解读，不替代现场确认或医疗判断。）")
    return "\n".join(lines)


def _ai_night_events(sub):
    """夜间（0–6 点）活动块计数：相邻读数间隔 ≤10 分钟视为同一次，只作参考。"""
    night = sub[(sub["活动状态"] != "静止") & (sub["时间"].dt.hour < 6)]
    if night.empty:
        return 0, 0
    stamps = sorted(night["时间"].tolist())
    blocks = 1
    for prev, cur in zip(stamps, stamps[1:]):
        if (cur - prev).total_seconds() > 600:
            blocks += 1
    return blocks, len(stamps)


def _ai_query_answer(question, df, rooms, family=False):
    """规则问答：只答五类有数据支撑的问题，答不上来直说。

    返回 (回答文本, 依据列表, 来源标记)。来源标记为 rule，接后端后改 backend。
    """
    q = (question or "").strip()
    if not q:
        return "", [], "rule"

    names = [r.get("name") for r in rooms]
    scope = "本户房间" if family else f"{len(rooms)} 间房"
    latest_ts = df["时间"].max()
    facts = [f"范围：{scope}（{'、'.join(str(n) for n in names)}）"]
    if latest_ts is not None:
        facts.append(f"数据截止：{latest_ts.strftime('%m-%d %H:%M')}")

    if any(k in q for k in ("告警", "异常", "需要处理", "要处理")):
        pending = [a for a in (st.session_state.alerts or []) if a.get("status") == "待处理"]
        if family:
            pending = [a for a in pending if a.get("room") in names]
        facts.append(f"待处理告警：{len(pending)} 条")
        if pending:
            detail = "；".join(f"{a.get('room')}·{a.get('category')}" for a in pending[:3])
            return f"当前有 {len(pending)} 条待处理事项：{detail}。建议先确认这些。", facts, "rule"
        return "当前没有待处理事项，房间状态平稳。", facts, "rule"

    if any(k in q for k in ("温度", "热", "冷", "℃")):
        limit = float(st.session_state.params.get("ambient_limit") or 26.0)
        hot = [r for r in rooms if isinstance(r.get("temp"), (int, float)) and r["temp"] >= limit]
        temps = "，".join(f"{r['name']} {r['temp']} ℃" for r in rooms if isinstance(r.get("temp"), (int, float)))
        facts.append(f"环境温度阈值：{limit} ℃")
        if hot:
            return f"{'、'.join(r['name'] for r in hot)} 环境温度达到或超过 {limit} ℃（{temps}），建议通风或确认。", facts, "rule"
        return f"各房间环境温度都在阈值内（{temps or '暂无读数'}，阈值 {limit} ℃）。", facts, "rule"

    if any(k in q for k in ("起夜", "夜间", "半夜", "凌晨", "昨晚", "晚上")):
        total_blocks, total_points = 0, 0
        detail = []
        for name in names:
            sub = df[df["监测区域"] == name]
            blocks, points = _ai_night_events(sub)
            if blocks:
                detail.append(f"{name} {blocks} 次")
            total_blocks += blocks
            total_points += points
        facts.append(f"夜间活动读数：{total_points} 条")
        if not total_blocks:
            return "夜间（0–6 点）没有检测到活动块，整夜以静止为主。", facts, "rule"
        tail = "（按相邻读数间隔 ≤10 分钟合并计为一次，仅作参考）"
        return f"夜间共记录到 {total_blocks} 次活动块：{'、'.join(detail)}{tail}。", facts, "rule"

    if any(k in q for k in ("设备", "在线", "离线", "节点", "掉线")):
        devs = [d for r in rooms for d in (r.get("devices") or [])]
        online = sum(1 for d in devs if d.get("online"))
        offline = [d.get("name") for d in devs if not d.get("online")]
        facts.append(f"设备：{len(devs)} 个，在线 {online} 个")
        if offline:
            return f"当前 {online}/{len(devs)} 个设备在线，离线：{'、'.join(str(d) for d in offline)}。", facts, "rule"
        return f"当前 {online}/{len(devs)} 个设备在线，没有掉线设备。", facts, "rule"

    if any(k in q for k in ("活动", "在不在", "有人", "动", "怎么样", "情况")):
        recent = df[df["时间"] >= (latest_ts - pd.Timedelta(minutes=30))] if latest_ts is not None else df
        active = [r for r in rooms if r.get("activity") in ("活动", "移动")]
        facts.append(f"近 30 分钟读数：{len(recent)} 条")
        if active:
            return f"近 30 分钟 {'、'.join(r['name'] for r in active)} 检测到活动或移动，其余房间安静。", facts, "rule"
        return "近 30 分钟各房间以静止为主，未见活动迹象。", facts, "rule"

    return (
        "这个问题暂时答不了。留意目前只能回答：房间活动、温度、夜间活动、告警、设备这五类；"
        "其余问题需要接入后端问答能力后再开放。",
        facts,
        "rule",
    )


def _ai_alert_review(alerts, names):
    """告警降噪：按「房间 + 类型」聚合待处理事项，给出合并/低优先/建议确认。"""
    pending = [
        a for a in (alerts or [])
        if a.get("status") == "待处理" and a.get("room") in names
    ]
    groups = {}
    for item in pending:
        groups.setdefault((item.get("room"), item.get("category")), []).append(item)

    reviewed = []
    for (room, category), items in groups.items():
        times = [a.get("time") for a in items if isinstance(a.get("time"), datetime)]
        count = len(items)
        span = int((max(times) - min(times)).total_seconds() / 60) if len(times) >= 2 else 0
        night_only = all(t.hour < 6 for t in times) if times else False
        if count >= 3 or (count == 2 and span <= 60):
            level, action = "注意", "合并为一条"
            when = f"{span} 分钟内" if span > 0 else "同一时刻"
            why = f"{count} 条同类事项在{when}重复出现，建议合并后再确认，避免重复打扰"
        elif night_only:
            level, action = "低优先", "可延后确认"
            why = "发生在 0–6 点，属于夜间正常起身；白天统一处理即可"
        else:
            level, action = "建议确认", "逐条确认"
            why = "只在当前时段出现一次，建议看原始读数后确认"
        reviewed.append(
            {
                "room": room,
                "category": category,
                "count": count,
                "first": min(times).strftime("%m-%d %H:%M") if times else "—",
                "last": max(times).strftime("%H:%M") if times else "—",
                "span": span,
                "level": level,
                "action": action,
                "why": why,
            }
        )
    reviewed.sort(key=lambda x: (x["level"] != "注意", x["level"] != "建议确认", -x["count"]))
    return reviewed


def _ai_rhythm_figure(df, names, height=260):
    """生活节律：按小时统计活动读数占比（%),单房间用柱状,多房间用热力。"""
    palette = get_palette()
    hours = list(range(24))

    def ratio(name, hour):
        block = df[(df["监测区域"] == name) & (df["时间"].dt.hour == hour)]
        if block.empty:
            return None
        return round(100.0 * (block["活动状态"] != "静止").mean(), 1)

    if len(names) <= 1:
        name = names[0]
        fig = go.Figure(
            go.Bar(
                x=hours,
                y=[ratio(name, h) for h in hours],
                marker=dict(color=palette["accent"], line=dict(width=0)),
                hovertemplate="%{x}:00 · 活动 %{y}%<extra></extra>",
            )
        )
        fig.update_yaxes(range=[0, 100], ticksuffix="%", title_text="活动占比")
    else:
        fig = go.Figure(
            go.Heatmap(
                x=hours,
                y=names,
                z=[[ratio(n, h) for h in hours] for n in names],
                zmin=0,
                zmax=100,
                colorscale=[[0, palette["surface2"]], [1, palette["accent"]]],
                hovertemplate="%{y} · %{x}:00 · 活动 %{z}%<extra></extra>",
                colorbar=dict(
                    title=dict(text="活动 %", font=dict(size=10, color=palette["muted"])),
                    thickness=8,
                    len=0.7,
                    tickfont=dict(size=9, color=palette["muted"]),
                    outlinewidth=0,
                ),
            )
        )
    fig.update_xaxes(
        tickmode="array",
        tickvals=[0, 3, 6, 9, 12, 15, 18, 21, 23],
        ticktext=["00", "03", "06", "09", "12", "15", "18", "21", "23"],
    )
    return apply_chart_theme(fig, height)


def _room_ai_card(room, family=False):
    name = str(room.get("name") or "未命名区域")
    ai = room.get("ai") or {}
    level = ai.get("level") if ai.get("level") in _AI_LEVEL_CN else "info"
    label = str(ai.get("label") or room.get("activity") or "暂无数据")
    plain = str(ai.get("plain") or "")
    meta = [f"环境 {room['temp']} ℃"] if room.get("temp") is not None else []
    if not family:
        if st.session_state.get("show_device_detail", True):
            devs = room.get("devices") or []
            online = sum(1 for d in devs if d.get("online"))
            meta.append(f"设备 {online}/{len(devs)} 在线")
            meta.append(f"待处理 {int(room.get('alerts') or 0)} 条")
        if st.session_state.get("show_confidence", True):
            conf = ai.get("confidence")
            if isinstance(conf, (int, float)) and conf:
                meta.append(f"置信 {int(round(float(conf) * 100))}%")
    with st.container(border=True):
        left, right = st.columns([4, 1.1], gap="large", vertical_alignment="center")
        with left:
            st.markdown(
                f'<div class="acard-head"><span class="acard-cat">{esc(name)}</span>'
                f'{badge(_AI_LEVEL_CN[level], _AI_LEVEL_TONE[level])}'
                f'{badge(label, "muted")}</div>'
                f'<div class="acard-msg">{esc(plain)}</div>'
                f'<div class="acard-meta">{esc(" · ".join(meta))}</div>',
                unsafe_allow_html=True,
            )
        with right:
            if st.button(
                "查看画面" if family else "打开房间",
                key="ai_open_" + name,
                width="stretch",
            ):
                if family:
                    st.session_state.page = "实时监护画面"
                else:
                    st.session_state.page = "实时监测"
                    if name in (st.session_state.areas or []):
                        st.session_state.live_room = name
                st.rerun()


def page_ai():
    family = st.session_state.role != "管理员"
    if page_header(
        "留意",
        "今天的家里怎么样，一间一间看" if family else "全局解读：哪间房需要留意、为什么",
        "总览 / 留意" if family else "监测 / 留意",
        "refresh_ai",
    ):
        refresh_data()
        st.rerun()

    df = st.session_state.demo_df

    if df is None or df.empty:
        empty_state("暂无数据", "点击右上角「刷新数据」，留意才能读到今天的读数。")
        return

    if family:
        person = get_current_person()
        if person is None:
            empty_state("未绑定监护人员", "请联系管理员为当前家属账号绑定监护人员。")
            return
        rooms = [r for r in space_rooms(df, focus=person["room"]) if r.get("name") == person["room"]]
        if not rooms:
            empty_state("暂时没有收到该房间的数据", "请稍后刷新，或联系管理员确认监测区域配置。")
            return
    else:
        rooms = space_rooms(df)

    names = [r.get("name") for r in rooms]
    source = "AI 后端" if (st.session_state.get("space_ai") or {}) else "本地模板"
    backend_summary = str(st.session_state.get("space_summary") or "")
    if backend_summary:
        summary, kind = backend_summary, "ok"
    else:
        summary, kind = _ai_today_summary(rooms)

    banner(
        kind,
        "留意 · 今天的家里" if family else "留意 · 当前整体状态",
        summary,
    )

    active = [r for r in rooms if r.get("activity") in ("活动", "移动")]
    alerts = sum(int(r.get("alerts") or 0) for r in rooms)
    devs = [d for r in rooms for d in (r.get("devices") or [])]
    online = sum(1 for d in devs if d.get("online"))

    cols = st.columns(3, gap="medium")
    with cols[0]:
        if family:
            metric_card("当前状态", rooms[0].get("activity") or "无数据", "房间级识别结果")
        else:
            metric_card("有活动的房间", f"{len(active)} / {len(rooms)}", "活动或移动")
    with cols[1]:
        metric_card("待处理事项", str(alerts), "告警中心待处理" if not family else "需要确认的事项")
    with cols[2]:
        metric_card("设备在线", f"{online} / {len(devs)}" if devs else "—", "采集节点")

    section_title("降噪队列", "同类重复先合并，夜间小事不打扰")
    reviewed = _ai_alert_review(st.session_state.alerts, names)
    if not reviewed:
        empty_state("没有需要甄别的事项", "待处理清单是空的；新告警出现后，这里会先做一次合并与分级。")
    else:
        for idx, item in enumerate(reviewed):
            tone = {"注意": "warn", "低优先": "muted", "建议确认": "accent"}.get(item["level"], "accent")
            with st.container(border=True):
                left, right = st.columns([0.72, 0.28], gap="medium")
                with left:
                    st.markdown(
                        f'<div class="acard-head">{badge(item["level"], tone)}'
                        f'{badge(item["action"], "muted")}'
                        f'<span class="acard-sub">{esc(item["room"])} · {esc(str(item["category"]))}</span></div>'
                        f'<div class="acard-msg">{esc(item["why"])}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f"共 {item['count']} 条 · 首次 {item['first']} · 最近 {item['last']}")
                with right:
                    if st.button("去告警中心" if not family else "去我的告警", key=f"ai_rev_{idx}", width="stretch"):
                        st.session_state.page = "告警中心" if not family else "我的告警"
                        st.rerun()

    section_title(
        "房间解读",
        "每间房一句解释；点进去可看该房间的原始读数" if not family else "每间房一句解释",
    )
    for room in rooms:
        _room_ai_card(room, family)

    section_title("问留意", "只回答有数据支撑的问题；答不上来会直说")
    presets = ["今天有活动吗", "昨晚起夜几次", "温度正常吗", "有待处理告警吗"]
    quick = st.columns(4, gap="small")
    for idx, text in enumerate(presets):
        if quick[idx].button(text, key=f"ai_preset_{idx}", width="stretch"):
            st.session_state.ai_query_text = text
            st.rerun()

    question = st.text_input(
        "问点什么",
        key="ai_query_text",
        placeholder="例如：昨晚起夜几次",
    )

    if question:
        answer, facts, src = _ai_query_answer(question, df, rooms, family)
        if answer:
            st.markdown(
                f'<div class="acard-head">{badge("留意回答", "accent")}'
                f'{badge("规则回答" if src == "rule" else "AI 后端", "muted")}</div>'
                f'<div class="acard-msg">{esc(answer)}</div>',
                unsafe_allow_html=True,
            )
            with st.expander("依据（可核对）"):
                for item in facts:
                    st.markdown(f"- {item}")
                st.caption("回答由当前读数直接计算得出，未经过语言模型改写；接入后端问答后会改为模型转述，依据仍会附上。")

    section_title("回溯", "选一个时刻，看当时的读数")
    if df["时间"].notna().any():
        dates = sorted(set(df["时间"].dt.date.dropna().tolist()))
        pick_date = st.selectbox(
            "日期",
            dates,
            index=len(dates) - 1,
            key="ai_back_date",
            format_func=lambda d: d.strftime("%m-%d"),
        )
        latest_hour = int(df["时间"].max().hour) if df["时间"].notna().any() else 0
        pick_hour = st.slider("时刻（小时）", 0, 23, value=latest_hour, key="ai_back_hour")

        window = df[(df["时间"].dt.date == pick_date) & (df["时间"].dt.hour == pick_hour)]
        if family:
            window = window[window["监测区域"] == rooms[0].get("name")]

        if window.empty:
            empty_state("该时段没有数据", "换一个日期或小时再试；没有数据时留意不会编造结论。")
        else:
            rows = []
            for name in [n for n in names if n in set(window["监测区域"])]:
                sub = window[window["监测区域"] == name]
                last = sub.iloc[-1]
                room_alerts = [
                    a for a in (st.session_state.alerts or [])
                    if a.get("room") == name
                    and isinstance(a.get("time"), datetime)
                    and a["time"].date() == pick_date
                    and a["time"].hour == pick_hour
                ]
                rows.append(
                    {
                        "房间": name,
                        "活动状态": last["活动状态"],
                        "环境温度": None if pd.isna(last["环境温度"]) else round(float(last["环境温度"]), 1),
                        "表面温度": None if pd.isna(last["表面温度"]) else round(float(last["表面温度"]), 1),
                        "最近读数": last["时间"].strftime("%H:%M"),
                        "该小时告警": len(room_alerts),
                    }
                )
            data_table(pd.DataFrame(rows))
            st.caption(f"{pick_date.strftime('%m-%d')} {pick_hour:02d}:00–{pick_hour:02d}:59 · 共 {len(window)} 条读数")

    section_title("生活节律", "看这一天的作息是否规律")
    if df["时间"].notna().any():
        plot_chart(_ai_rhythm_figure(df, names))
        st.caption(
            "按每小时「活动 / 移动」读数占比统计；"
            + ("柱子越高说明这个小时活动越多。" if len(names) <= 1 else "颜色越亮说明这个小时活动越多。")
            + " 0–6 点出现明显亮块，通常意味着夜间起身较多。"
        )
    else:
        empty_state("暂无节律数据", "拿到读数后这里会按小时显示活动分布。")

    section_title("今日简报", "一段可以直接发给家人的话")
    if st.session_state.get("auto_brief", True):
        brief = _ai_daily_brief(rooms, family)
        st.markdown(
            f'<div class="acard-msg" style="line-height:1.95">{esc(brief).replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "下载今日简报（Markdown）",
            data=brief.encode("utf-8"),
            file_name="留意-今日简报.md",
            mime="text/markdown",
            key="ai_brief_download",
        )
    else:
        empty_state("今日简报已在设置中关闭", "需要时可在「设置 → 显示内容 → 自动生成今日简报」重新打开。")

    st.caption(
        f"解读来源：{source}。留意只解释已有读数，不做诊断；"
        "结论均可回到原始读数核对，紧急情况请直接联系现场人员或急救服务。"
    )


# ============================================================
# 路由与页脚
# ============================================================

# ============================================================
# 设置（个人偏好，不影响识别参数）
# ============================================================



STYLE_OPTIONS = [
    ("glass", "深色玻璃", "暖光照片底，磨砂玻璃卡片，橙色强调"),
    ("glass_light", "浅色玻璃", "浅木日光底，白玻璃卡片，砖橙强调"),
    ("dark", "经典深色", "纯色深底，扁平卡片，冷蓝强调"),
    ("light", "经典浅色", "纯色浅底，扁平卡片，冷蓝强调"),
]

_STYLE_TOKENS = {
    "glass": dict(bg="radial-gradient(72% 62% at 17% 10%, rgba(255,178,102,0.30), transparent 62%),"
                     "radial-gradient(66% 58% at 84% 86%, rgba(126,88,58,0.34), transparent 66%),"
                     "linear-gradient(150deg,#3A2D22,#0B0D11)", rail="rgba(255,255,255,0.16)",
                  card="rgba(255,255,255,0.12)", bar="rgba(255,255,255,0.10)",
                  accent="#F08A4B", text="#F2F5F9", border="rgba(255,255,255,0.22)"),
    "glass_light": dict(bg="radial-gradient(62% 54% at 20% 12%, rgba(255,242,219,0.95), transparent 64%),"
                           "radial-gradient(58% 56% at 82% 74%, rgba(140,166,116,0.34), transparent 68%),"
                           "linear-gradient(150deg,#F8F4EB,#E1D6C5)", rail="rgba(255,255,255,0.72)",
                        card="rgba(255,255,255,0.78)", bar="rgba(255,255,255,0.66)",
                        accent="#C4622A", text="#1B2027", border="rgba(255,255,255,0.9)"),
    "dark": dict(bg="#0C1117", rail="#151C25", card="#151C25", bar="#1B242E",
                 accent="#5B9ED1", text="#E5EAF1", border="#27313C"),
    "light": dict(bg="#F4F6F8", rail="#FFFFFF", card="#FFFFFF", bar="#FFFFFF",
                  accent="#3C7BA8", text="#26313C", border="#DCE3EA"),
}


def style_preview(key, active=False):
    t = _STYLE_TOKENS[key]
    ring = ("box-shadow:0 0 0 2px %s inset;" % t["accent"]) if active else ""
    classic = key in ("dark", "light")

    if classic:
        side_bars = "".join(
            '<span style="background:%s;opacity:%s;width:%s"></span>' % (t["text"], o, w)
            for o, w in ((".85", "78%"), (".62", "64%"), (".45", "72%"), (".32", "55%"))
        )
        body = (
            '<div class="sw-side" style="background:' + t["rail"] + '">' + side_bars + "</div>"
            '<div class="sw-body">'
            '<div class="sw-bar" style="background:' + t["bar"] + ";border:1px solid " + t["border"] + '"></div>'
            '<div class="sw-card" style="background:' + t["card"] + ";border:1px solid " + t["border"] + '">'
            '<span style="background:' + t["accent"] + ';width:46%"></span>'
            '<span style="background:' + t["text"] + ';opacity:.55;width:78%"></span>'
            '<span style="background:' + t["text"] + ';opacity:.25;width:60%"></span>'
            "</div></div>"
        )
    else:
        dot_html = "".join(
            '<i style="background:%s;opacity:%s"></i>' % (c, o)
            for c, o in ((t["accent"], "1"), (t["text"], ".7"), (t["text"], ".45"), (t["text"], ".3"))
        )
        body = (
            '<div class="sw-rail" style="background:' + t["rail"] + '">' + dot_html + "</div>"
            '<div class="sw-body">'
            '<div class="sw-bar" style="background:' + t["bar"] + ";border:1px solid " + t["border"] + '"></div>'
            '<div class="sw-card" style="background:' + t["card"] + ";border:1px solid " + t["border"] + '">'
            '<span style="background:' + t["accent"] + '"></span>'
            '<span style="background:' + t["text"] + ';opacity:.55"></span>'
            '<span style="background:' + t["text"] + ';opacity:.25"></span>'
            "</div>"
            '<div class="sw-card sm" style="background:' + t["card"] + ";border:1px solid " + t["border"] + '"></div>'
            "</div>"
        )

    return (
        '<div class="sw-prev" style="background:' + t["bg"] + ";border-color:" + t["border"] + ";" + ring + '">'
        + body +
        "</div>"
    )


_STYLE_PICKER_CSS = """
<style>
.sw-prev {
    display: flex;
    gap: 7px;
    padding: 9px;
    border-radius: 12px;
    border: 1px solid transparent;
    height: 104px;
    box-sizing: border-box;
}
.sw-rail {
    width: 16px;
    border-radius: 999px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    padding: 7px 0;
    flex: 0 0 16px;
}
.sw-rail i { width: 7px; height: 7px; border-radius: 50%; display: block; }
.sw-body { flex: 1; display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.sw-bar { height: 12px; border-radius: 999px; }
.sw-card {
    flex: 1;
    border-radius: 8px;
    padding: 7px 8px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    justify-content: center;
}
.sw-card span { display: block; height: 5px; border-radius: 3px; }
.sw-card span:first-child { width: 46%; }
.sw-card span:nth-child(2) { width: 78%; }
.sw-card span:nth-child(3) { width: 60%; }
.sw-card.sm { flex: 0 0 24px; padding: 0; }
.sw-side {
    flex: 0 0 34%;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    gap: 7px;
    padding: 9px 8px;
    justify-content: center;
}
.sw-side span { display: block; height: 5px; border-radius: 3px; }
.sw-name { font-size: 13px; font-weight: 600; color: var(--text); margin: 8px 0 1px; }
.sw-head { display: flex; align-items: center; gap: 8px; }
.sw-badge {
    font-size: 11px;
    line-height: 1;
    padding: 3px 8px 4px;
    border-radius: 999px;
    color: var(--accent);
    background: rgba(240,138,75,0.14);
    border: 1px solid rgba(240,138,75,0.34);
    white-space: nowrap;
    margin-top: 7px;
}
.sw-desc { font-size: 11.5px; color: var(--muted); min-height: 30px; }

/* 整张卡可点：容器定位，按钮铺满并透明 */
[class*="st-key-stylecard_"] {
    position: relative;
    padding: 10px 10px 12px;
    border-radius: 20px;
    cursor: pointer;
    transition: transform .38s cubic-bezier(.32,.72,0,1),
                box-shadow .38s cubic-bezier(.32,.72,0,1);
}
[class*="st-key-stylecard_"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 34px rgba(0,0,0,0.18);
}
[class*="st-key-stylecard_"] [data-testid="stButton"] button {
    position: absolute;
    inset: 0;
    height: auto !important;
    min-height: 0 !important;
    padding: 0 !important;
    opacity: 0;
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    cursor: pointer;
}
[class*="st-key-stylecard_"] [data-testid="stButton"] {
    position: absolute;
    inset: 0;
    margin: 0 !important;
}
/* Streamlit 的元素容器自带 position:relative 且高度被绝对子元素压成 0，
   必须让位给卡片容器，否则透明按钮铺不满整卡 */
[class*="st-key-stylecard_"] [data-testid="stElementContainer"] {
    position: static !important;
    margin: 0 !important;
}
[class*="st-key-stylecard_"] .stButton > button:focus-visible {
    opacity: 1;
    background: rgba(240,138,75,0.10) !important;
    border: 1px solid rgba(240,138,75,0.55) !important;
}
[class*="st-key-stylecard_"] [data-testid="stElementContainer"]:has(.stButton) { margin: 0 !important; }
</style>
"""


def page_prefs():
    family = st.session_state.role != "管理员"
    if page_header(
        "设置",
        "工作台的个人偏好，只影响你自己看到的界面"
        if family
        else "工作台的个人偏好，只影响你自己看到的界面；识别参数与监测区域请到「系统配置」",
        "账户 / 设置" if family else "系统 / 设置",
        "refresh_prefs",
    ):
        refresh_data()
        st.rerun()

    section_title("视觉风格", "同一套界面，四种底色；点任意一张卡片即可切换")
    st.markdown(_STYLE_PICKER_CSS, unsafe_allow_html=True)
    current_style = st.session_state.get("theme", "glass")
    for row_start in (0, 2):
        cols = st.columns(2, gap="medium")
        for offset, col in enumerate(cols):
            item = STYLE_OPTIONS[row_start + offset]
            key, name, desc = item
            with col:
                with st.container(key="stylecard_" + key):
                    badge = '<span class="sw-badge">使用中</span>' if key == current_style else ""
                    st.markdown(
                        style_preview(key, key == current_style)
                        + '<div class="sw-head"><span class="sw-name">' + name + "</span>"
                        + badge
                        + "</div>"
                        + '<div class="sw-desc">' + desc + "</div>",
                        unsafe_allow_html=True,
                    )
                    if key != current_style:
                        # 透明按钮铺满整张卡：整卡可点，只保留可达名称
                        if st.button(
                            "切换到" + name,
                            key="style_set_" + key,
                            width="stretch",
                        ):
                            apply_theme(key)
                            st.rerun()

    density_now = st.session_state.get("density", "标准")
    st.segmented_control(
        "信息密度",
        ["标准", "紧凑"],
        default=density_now,
        key="density",
        help="紧凑会压小卡片内边距和区块间距，一屏能多看几行",
    )
    st.toggle(
        "减少动效",
        value=bool(st.session_state.get("reduce_motion")),
        key="reduce_motion",
        help="关闭页面过渡与脉冲动效，低配设备更顺",
    )

    section_title("显示内容", "决定页面露出多少技术细节")
    if family:
        st.toggle(
            "自动生成今日简报",
            value=bool(st.session_state.get("auto_brief", True)),
            key="auto_brief",
            help="关掉后「留意」页不再生成简报，减少无关打扰",
        )
        st.caption("置信度、设备在线等技术字段默认不对家属端展示，无需在此设置。")
    else:
        st.toggle(
            "显示置信度",
            value=bool(st.session_state.get("show_confidence", True)),
            key="show_confidence",
            help="房间解读里的置信百分比",
        )
        st.toggle(
            "显示设备明细",
            value=bool(st.session_state.get("show_device_detail", True)),
            key="show_device_detail",
            help="房间解读里的「设备 x/y 在线、待处理 n 条」",
        )
        st.toggle(
            "自动生成今日简报",
            value=bool(st.session_state.get("auto_brief", True)),
            key="auto_brief",
            help="关掉后「留意」页不再生成简报，减少无关打扰",
        )

    section_title("通知与打扰", "需要推送通道，接入后开放")
    with st.container(border=True):
        st.markdown(
            '<div class="acard-msg">计划中的三项：告警通知级别（全部 / 仅需确认 / 仅严重）、'
            "夜间免打扰时段（默认 22:00–07:00 只记录不提醒）、每日简报推送时间。</div>",
            unsafe_allow_html=True,
        )
        st.caption("当前版本没有推送通道（浏览器通知、短信、App 均未接入），所以这里只登记计划，不放无效开关。")

    section_title("关于与本机数据", "版本、数据来源与导出")
    mode_text = "DEMO 模拟" if DEMO_MODE else "后端接口"
    base = getattr(_HTTP_SOURCE, "base_url", "") or "未配置"
    last = st.session_state.last_refresh.strftime("%m-%d %H:%M:%S") if st.session_state.last_refresh else "—"
    cols = st.columns(3, gap="medium")
    with cols[0]:
        metric_card("当前版本", f"V{APP_VERSION}", "应用层")
    with cols[1]:
        metric_card("数据模式", mode_text, "WIFI_SENSE_DEMO_MODE")
    with cols[2]:
        metric_card("最近刷新", last, "本会话")
    st.caption(f"后端地址：{base}　·　偏好仅保存在当前会话，刷新页面后恢复默认；持久化需要后端偏好接口。")
    if PERSIST_LOGIN:
        st.caption(
            f"登录状态：默认 {SESSION_TTL // 3600} 小时、勾选「记住我」后 "
            f"{SESSION_TTL_REMEMBER // 86400} 天；凭证位于当前地址栏，请勿把带参数的链接转发给他人；退出登录会立即清除。"
        )

    df = st.session_state.demo_df
    alerts = st.session_state.alerts or []
    exp_left, exp_right = st.columns(2, gap="medium")
    with exp_left:
        if alerts:
            rows = [
                {
                    "时间": a.get("time").strftime("%Y-%m-%d %H:%M:%S") if isinstance(a.get("time"), datetime) else "",
                    "区域": a.get("room") or "",
                    "类型": a.get("category") or "",
                    "等级": a.get("level") or "",
                    "状态": a.get("status") or "",
                    "描述": a.get("message") or "",
                }
                for a in alerts
            ]
            st.download_button(
                "导出告警（CSV）",
                data=pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig"),
                file_name=f"wifi-sense-alerts-{datetime.now().strftime('%Y%m%d-%H%M')}.csv",
                mime="text/csv",
                key="export_alerts",
                width="stretch",
            )
        else:
            st.caption("当前没有告警记录可导出。")
    with exp_right:
        if df is not None and not df.empty:
            rooms = [r for r in space_rooms(df, focus=None) if not family or r.get("name") == (get_current_person() or {}).get("room")]
            md = _ai_daily_brief(rooms, family)
            st.download_button(
                "导出今日简报（md）",
                data=md.encode("utf-8"),
                file_name=f"wifi-sense-brief-{datetime.now().strftime('%Y%m%d-%H%M')}.md",
                mime="text/markdown",
                key="export_brief",
                width="stretch",
            )
        else:
            st.caption("暂无读数，无法生成简报。")


ADMIN_PAGES = {
    "管理工作台": page_dashboard,
    "人员档案管理": page_persons,
    "设备管理": page_devices,
    "实时监测": page_live,
    "留意": page_ai,
    "告警中心": page_alerts,
    "历史数据": page_history,
    "监测任务": page_tasks,
    "系统配置": page_settings,
    "设置": page_prefs,
}

FAMILY_PAGES = {
    "家庭监护首页": page_family_home,
    "实时监护画面": page_family_live,
    "留意": page_ai,
    "我的告警": page_my_alerts,
    "历史告警记录": page_alert_history,
    "个人信息": page_profile,
    "设置": page_prefs,
}


def mobile_sidebar_autoclose(page):
    """手机端切页后自动收起侧栏抽屉；桌面端与同一页内的刷新都不受影响。

    说明：需要访问父文档把抽屉点掉，st.iframe 的沙箱不允许跨文档操作，
    因此这里用 components.v1.html（Streamlit 1.67 仍支持，弃用日期为 2026-06-01）。
    """
    components.html(
        f"""
<script>
(function() {{
  try {{
    var last = window.localStorage.getItem('ws_last_page');
    if (last === {json.dumps(page)}) return;
    window.localStorage.setItem('ws_last_page', {json.dumps(page)});
    var p = window.parent;
    if (p.innerWidth > 640) return;
    setTimeout(function() {{
      var btn = p.document.querySelector('[data-testid=stSidebar] button[aria-label="Collapse sidebar"]');
      if (btn) btn.click();
    }}, 250);
  }} catch (e) {{}}
}})();
</script>
""",
        height=0,
    )


def render_footer():
    st.markdown("<hr>", unsafe_allow_html=True)
    left, right = st.columns([3, 1])

    with left:
        st.caption(
            f"Wi-Fi Sense V{APP_VERSION} · 应用层 · 基于角色的监测平台 · "
            f"全部数据为 {DATA_MODE_TEXT}" if DEMO_MODE else "全部数据来自后端接口"
        )

    with right:
        st.caption(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# 主题已从地址栏恢复，此刻再注入 CSS，避免刷新后先亮一帧默认深色玻璃
inject_css()

# 把当前风格补写回地址栏（切换时的那次写入会被紧随的 st.rerun() 抢断，
# 所以统一在本轮开头对齐一次；值相同时不写，避免多余 rerun）
try:
    _saved_theme = st.query_params.get(THEME_PARAM)
    _cur_theme = st.session_state.get("theme")
    if _cur_theme in THEMES and _saved_theme != _cur_theme:
        st.query_params[THEME_PARAM] = _cur_theme
except Exception:
    pass

if restore_session() and not DEMO_MODE:
    # 刷新回来等同于“刷新即更新”：重新拉一次全量数据
    try:
        with loading_state("正在刷新数据…"):
            source().hydrate()
    except DataSourceError as exc:
        st.session_state.api_error = str(exc)

if not st.session_state.logged_in:
    render_login()
    st.stop()

if st.session_state.pop("boot_anim", False):
    boot_overlay()
    time.sleep(1.25)
    st.rerun()

is_admin = st.session_state.role == "管理员"

render_sidebar(is_admin)

# 后端异常只提示一次，避免每轮 rerun 重复刷屏
if st.session_state.get("api_error"):
    banner(
        "danger",
        "后端接口异常",
        f"{st.session_state.api_error}。页面继续展示最近一次成功获取的数据。",
    )
    st.session_state.api_error = None

page = resolve_page(is_admin)
handler = (ADMIN_PAGES if is_admin else FAMILY_PAGES).get(page)

if handler is None:
    st.error("页面不存在，请重新选择功能导航。")
else:
    handler()

mobile_sidebar_autoclose(page)
render_footer()
