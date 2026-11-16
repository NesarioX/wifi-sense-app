# Wi-Fi Sense

**Wi-Fi 感知（Wi-Fi CSI）家庭监护平台的「应用层」实现** —— 单文件 Streamlit 应用，把 ESP32 Wi-Fi 感知与温度传感的数据，组织成一套可直接上手的管理端 / 家属端界面。

A single-file Streamlit application layer for Wi-Fi CSI based home monitoring: dashboards, live alerts, device and resident management, four switchable visual themes.

> 当前为 **DEMO** 版本：全部数据为模拟数据，未连接真实 ESP32 设备与感知算法。接口契约已备好，填入 `WIFI_SENSE_API_BASE` 即切换到真实后端。

![深色玻璃主题](https://aka.doubaocdn.com/s/yK2vqfGHrY)

*深色玻璃（`glass`，默认）：暖光虚化底图 + 磨砂卡片*

![浅色玻璃主题](https://aka.doubaocdn.com/s/bUQS9BrGOV)

*浅色玻璃（`glass_light`）：浅木日光底图 + 白玻璃卡片*

## 功能

**双角色**
- 管理员：管理工作台（人员、设备、在线率、待处理告警、活动趋势、温度曲线、设备状态）、人员档案、设备管理、监测任务、系统配置
- 家属：家庭监护首页、实时监测、告警中心（只看自己绑定的房间）

**实时性**
- 告警区每 30 秒局部刷新（只打告警接口，不整页重绘），列表标注「更新于 hh:mm:ss」
- 告警中心支持状态 / 级别 / 区域筛选、每页 20 条分页、导出筛选后全量 CSV
- 工作台告警超过 4 条时给出「查看全部 N 条」入口
- 拉取失败保留上一次成功数据，只提示一行，不白屏

**视觉**
- 四套主题：深色玻璃 `glass`（默认）、浅色玻璃 `glass_light`、经典深色 `dark`、经典浅色 `light`
- 设置页 2×2 风格卡整卡可点切换，跨浏览器刷新保持（地址栏 `ws_t` 兜底，接入偏好接口后转服务端存储）
- Apple 风格入场与悬停动效，仅玻璃态生效，尊重「减少动效」与 `prefers-reduced-motion`
- 时间统一按 `Asia/Shanghai` 显示，容器时区（UTC / 本地）不影响界面

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Python 3.12（见 `runtime.txt`），依赖版本已锁定在 `requirements.txt`。

**演示账号**

| 账号 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 管理员 |
| `family` | `family123` | 家属（人员 P001） |
| `family2` | `family123` | 家属（人员 P002） |

## 配置

| 环境变量 | 默认 | 说明 |
|---|---|---|
| `WIFI_SENSE_API_BASE` | 空 | 后端基址；留空使用内置 DEMO 数据源 |
| `WIFI_SENSE_API_TIMEOUT` | 10 | 单次请求超时（秒） |
| `WIFI_SENSE_API_TTL` | 8 | 非轮询请求的进程内缓存（秒），轮询接口不使用缓存 |
| `WIFI_SENSE_ALERT_POLL` | 30 | 告警轮询周期（秒），设 `0` 关闭 |
| `WIFI_SENSE_ALERT_LIMIT` | 200 | 单次拉取告警条数上限 |
| `WIFI_SENSE_ALERTS_PAGE_SIZE` | 20 | 告警中心每页条数 |
| `WS_SESSION_SECRET` | 本地默认值 | 前端会话令牌签名密钥，**生产环境必须替换** |

## 目录结构

```
app.py                    # 全部应用代码（单文件）
assets/bg.jpg             # 深色玻璃底图
assets/bg_light.jpg       # 浅色玻璃底图
.streamlit/config.toml    # Streamlit 主题与服务器配置
docs/                     # 后端交接文档（一页纸 + 完整补充）
requirements.txt
runtime.txt
```

## 接口

完整的请求/响应契约在 `app.py` 的 `API_CONTRACT` 中（认证、人员、设备、遥测、告警、任务、识别参数、健康检查）。
数据源抽象为 `BaseDataSource` / `DemoDataSource` / `HttpDataSource`，接后端只需实现 `HttpDataSource` 对应的接口，页面代码无需改动。

需要后端配合的重点见 `docs/后端交接-一页纸.md`，其中包含四类异常态、告警轮询约定、时间戳用 UTC 毫秒等要求。

## 已知限制

- 真实后端尚未联调，HTTP 数据源只有契约与实现，没有与真实服务验证过
- 告警分页覆盖最近 200 条，更早记录需后端提供 `offset` / `before`
- 告警顶部三张指标卡不参与轮询，只随整页刷新更新（有意取舍）
- 登录鉴权为前端演示实现，`ws_s` 仅用于刷新不掉线，不承担权限判断
- 未做移动端布局（当前按 1440 宽设计）
- 「空间状态」3D 视图为深色底，浅色主题下对比偏硬

## 免责声明

本项目是家庭监护场景的原型与演示系统，**不是医疗设备、安防产品或安全认证产品**，不可用于医疗诊断、生命安全或安防值守等场景。演示模式下的所有数据均为模拟生成。

## 许可

[MIT](LICENSE)
