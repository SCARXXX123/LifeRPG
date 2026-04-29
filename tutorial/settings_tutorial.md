# LifeRPG 数据源配置指南

本指南详细介绍如何配置 LifeRPG 系统的各个数据源，以实现完整的行为审计功能。

---

## 目录

1. [Bilibili 数据凭据配置](#1-bilibili-数据凭据配置)
2. [ActivityWatch 多端部署与保活](#2-activitywatch-多端部署与保活)
3. [ADB 无线调试隧道与链路激活](#3-adb-无线调试隧道与链路激活)

---

## 1. Bilibili 数据凭据配置

### 概述

为使系统能够抓取 Bilibili 观看历史数据，需要配置 SESSDATA 凭据。该凭据用于验证用户身份并获取相关的观看记录。

### 配置步骤

1. **获取 SESSDATA**：请参考 [获取 Credential 类所需信息](https://nemo2011.github.io/bilibili-api/#/get-credential) 中的详细教程，获取您的 SESSDATA 凭据。

2. **配置凭据**：在 LifeRPG 系统的凭据配置页面，将获取到的 SESSDATA 粘贴至对应输入框中。

3. **验证连接**：系统将自动验证凭据的有效性。验证成功后，即可开始抓取 Bilibili 观看历史数据。

### 注意事项

- SESSDATA 凭据具有时效性，若凭据过期请重新获取
- 请勿将您的凭据信息泄露给他人
- 系统不会存储您的凭据，仅用于当次数据抓取

---

## 2. ActivityWatch 多端部署与保活

### 概述

ActivityWatch 是一款开源的时间追踪工具，用于记录您在 PC 上的应用使用情况和活动数据。系统通过 ActivityWatch 获取用户的行为数据，以进行深入分析。

### 配置步骤

1. **下载安装**：访问 [ActivityWatch 官方网站](https://activitywatch.net/)，下载与您操作系统匹配的版本。

2. **启动服务**：安装完成后，启动 ActivityWatch 应用。

3. **验证运行状态**：确认软件已正常运行，系统托盘区域应显示 ActivityWatch 图标。

### 注意事项

- 无需进行额外的配置操作，ActivityWatch 将自动开始记录数据
- 为确保数据完整性，建议保持 ActivityWatch 持续运行
- 系统将在进行行为审计时自动读取 ActivityWatch 的数据

---

## 3. ADB 无线调试隧道与链路激活

### 概述

通过 Android Debug Bridge (ADB) 无线调试功能，系统可以获取 Android 设备的每日使用数据。本节将详细介绍如何配置 ADB 连接。

### 前置要求

- Android 手机与电脑连接至同一 Wi-Fi 网络
- 手机已开启开发者模式
- 电脑已安装 ADB 工具

### 手机端配置

#### 启用开发者模式

不同品牌手机的开发者模式开启方式可能有所不同，请根据您的手机品牌自行查询。以下以 Redmi Note 11T Pro 为例进行说明。

#### 启用 USB 调试

1. 进入手机「设置」→「关于手机」
2. 连续点击「MIUI 版本」多次以启用开发者选项
3. 返回「设置」→「更多设置」→「开发者选项」
4. 启用「USB 调试」

#### 启用无线调试

在开发者选项中，找到并启用「无线调试」功能。

![手机无线调试页面示意](E:\pythonProject\LifeRPG-Desktop_test\tutorial\Screenshot_2026-04-29-19-19-19-894_com.android.se.jpg)

![无线调试详情页面](E:\pythonProject\LifeRPG-Desktop_test\tutorial\Screenshot_2026-04-29-19-22-24-549_com.android.se.jpg)

### 电脑端配置

#### 安装 ADB 工具

1. 访问 [SDK 平台工具版本说明](https://developer.android.google.cn/tools/releases/platform-tools?hl=zh-cn) 页面下载 ADB 工具包。
2. 解压下载文件至指定目录（如 `E:\adb\platform-tools`）。

#### 连接设备

1. 按 `Win + R` 键，输入 `cmd` 打开命令提示符。
2. 切换至 ADB 工具所在目录：
   ```
   E:
   cd E:\adb\platform-tools
   ```

![命令提示符操作示意](E:\pythonProject\LifeRPG-Desktop_test\tutorial\QQ20260429-193450.png)

### 配对设备

1. 在手机的无线调试页面，点击「使用配对码配对设备」。
2. 记录显示的配对码、IP 地址和端口。
3. 在 ADB 命令行中输入以下命令进行配对：
   ```
   adb pair IP地址:端口
   ```
   例如：
   ```
   adb pair 192.168.1.100:12345
   ```
4. 输入配对码完成配对过程。

![配对命令执行示意](E:\pythonProject\LifeRPG-Desktop_test\tutorial\QQ20260429-193744.png)

### 连接设备

配对成功后，在无线调试页面获取新的 IP 地址和端口，然后执行连接命令：
```
adb connect IP地址:端口
```

![连接命令执行示意](E:\pythonProject\LifeRPG-Desktop_test\tutorial\QQ20260429-194424.png)

### 完成配置

连接成功后，在 LifeRPG 系统的 ADB 配置页面填写以下信息：

- **ADB 可执行文件路径**：ADB 工具所在目录（如 `E:\adb\platform-tools`）
- **设备 ID / IP 地址**：无线调试页面显示的 IP 地址和端口

确认信息无误后，系统将开始抓取手机的每日使用数据。

![配置完成示意](E:\pythonProject\LifeRPG-Desktop_test\tutorial\audit_pic.png)

### 注意事项

- 每次重新连接 Wi-Fi 后，可能需要重新进行配对和连接操作
- 请确保手机和电脑始终连接至同一网络
- 若连接失败，请检查防火墙设置是否阻止了 ADB 通信

---

## 技术支持

若在配置过程中遇到任何问题，请查阅以下资源：

- [ActivityWatch 官方文档](https://docs.activitywatch.net/)
- [Android ADB 官方文档](https://developer.android.com/studio/command-line/adb)
- [Bilibili API 文档](https://nemo2011.github.io/bilibili-api/)

---

*本文档最后更新于 2026 年 4 月*
