# 同步课题2.0 — 实验任务设计
**Running Title: Brain-Heart Dynamics of Emotion Processing**
**基于 fNIRS-EEG-ECG 同步采集的针刺调节失眠患者情绪加工与脑-心交互机制研究**

---

## 一、任务总览

本项目通过 **三个实验 Session** 实现，每个 Session 对应一个独立的 PsychoPy 实验程序（`.psyexp`），均在 fNIRS-EEG-ECG 三模态同步采集下运行：

| Session | 对应文件 | 核心任务 | 定位 | 时长 |
|---|---|---|---|---|
| Session_01 | `Session_01.psyexp`<br>`Session_01_ShortStim.psyexp`<br>`Session_01_FixedStim.psyexp` | 情绪面孔-词冲突任务（训练+Part A+Part B）+ 闭眼/睁眼静息态 | **主任务**，评估情绪冲突加工和认知控制 | ~20 min |
| Session_02 | `Session_02.psyexp` | 情绪图片观看与 Slider 评分任务 | **次要任务**，评估情绪图片诱发的效价/唤醒度反应 | ~15 min |
| Session_03 | `Session_03.psyexp` | 冥想任务 + 针刺想象任务（3 blocks） | 辅助，观察放松与针刺表征的脑-心反应 | ~22 min |

**各 Session 均可通过按 `q` 键提前跳过当前阶段（计时阶段支持提前结束）。**

---

## 二、Session_01 — 情绪面孔-词冲突任务 + 静息态

### 2.1 流程总览

| 顺序 | 阶段 | Routine 名称 | 内容 | 时长 |
|---|---|---|---|---|
| 1 | Welcome | Welcome | "准备好后按下y键以开始" | 按y键继续 |
| 2 | 信号稳定 | Adapt | 注视点"+"，设备信号稳定 | 120 s |
| 3 | 闭眼静息 | Resting_EC | 闭眼静息，注视点"+" | 180 s (3 min) |
| 4 | 任务指导 | ExpIntro | 任务指导语（仅第一次指导含指导语） | 20 s |
| 5 | 训练试次 | TrainingISI→Stim→Resp→ITI→Ans | 练习试次（training CSV） | ~2 min |
| 6 | 训练-正式过渡 | Training2Main | "训练结束，按q以开始正式试验" | 按q键继续 |
| 7 | 正式试次 Part A | MainISI→MainStim→MainResp→MainITI | 96 个冲突判断 trial（Part A） | ~8 min |
| 8 | 睁眼静息 | Resting_EO | 睁眼静息，注视点"+" | 180 s (3 min) |
| 9 | 任务指导（重复） | ExpIntro | 任务指导语（再次确认） | 20 s |
| 10 | 正式试次 Part B | MainISI_B→MainStim_B→MainResp_B→MainITI_B | 96 个冲突判断 trial（Part B） | ~8 min |
| 11 | 结束 | Ending | 注视点"+" | 5 s |

**阶段 1–4、11 均配有语音提示（audio_prompts/Session_01/）。阶段 3 (Resting_EC) 和阶段 8 (Resting_EO) 有 SerialOut 事件标记。**

### 2.2 任务设计

采用 **面孔-词 Stroop 范式**，要求受试者判断面孔情绪效价（正性 / 负性），忽略面孔上叠加的情绪词含义。

任务分为三个阶段：
- **Training**（训练）：练习试次，每次回答后有正确答案反馈（TrainingAns），帮助被试理解任务。
- **Part A**（正式实验前半）：96 个正式试次，从 `Session_01/Session_01_260607_partA.csv` 加载。
- **Part B**（正式实验后半）：96 个正式试次，从 `Session_01/Session_01_260607_partB.csv` 加载。

Part A 与 Part B 之间插入 **180 s 睁眼静息 (Resting_EO)** 作为恢复期，随后重新显示任务指导语（ExpIntro）。

Part A/B 的分配通过 **Counterbalance（nGroups=2）** 控制，支持被试间 balance。

> **CSV 数据列前缀**：为确保 Part A、Part B 和 Training 三组循环的数据列在 PsychoPy 输出中不会混淆，CSV 列名已按模块加前缀：Part A 使用 `partA_*`（如 `partA_condition`、`partA_jitter`），Part B 使用 `partB_*`，Training 使用 `train_*`。在 `.psyexp` 的 Builder 变量引用中对应使用 `$partA_*` / `$partB_*` / `$train_*`。

### 2.3 实验条件

| 条件 | 面孔 | 词语 | 类型 | Trial数 |
|---|---|---|---|---|
| 正性一致 | 正性面孔 | 正性词 | 一致 | 24 |
| 负性一致 | 负性面孔 | 负性词 | 一致 | 24 |
| 正脸负词 | 正性面孔 | 负性词 | 冲突 | 24 |
| 负脸正词 | 负性面孔 | 正性词 | 冲突 | 24 |
| **合计** | | | | **96 per Part** |

试次从 CSV 文件加载，**随机呈现**。

### 2.4 正式试次时间结构（Part A: MainISI→MainStim→MainResp→MainITI / Part B: MainISI_B→MainStim_B→MainResp_B→MainITI_B）

> Part A 与 Part B 的试次时间结构完全相同，仅 Routine 名称以 `_B` 后缀区分，使得 SerialOut 标记和数据列可以分别识别两部分试次。

| Routine | 组件 | 内容 | 持续时长 |
|---|---|---|---|
| MainISI | text_21 ("+") | 注视点 | 0.5 s |
| | text_22 (blank) | jitter 间隔 | $partA_jitter（变量） |
| MainStim | image_2 (面孔图片) | 面孔，尺寸 (0.548, 0.8) | 1.0 s |
| | text_16 (情绪词) | 词语叠加于面孔上 | 1.0 s |
| | serialPort | SerialOut 标记 (4→2, 1.0s) | 1.0 s |
| MainResp | text_17 | "正性面孔→f键 / 负性面孔→j键" | —（按键结束） |
| | key_resp_10 | 按键 'f' / 'j'，forceEndRoutine | —（按键结束） |
| | serialPort_3 | SerialOut 标记 (9→13, 按键触发) | condition |
| MainITI | text_18 ("+") | 注视点 | 0.5 s |
| | text_22 (blank) | jitter 间隔 | $partA_iti（变量） |

> **Part B 对应命名**：Part B 使用 `MainISI_B` / `MainStim_B` / `MainResp_B` / `MainITI_B`，数据列前缀为 `partB_`，SerialOut 组件为 `serialPort_2` (4→2) 与 `serialPort_10` (10→15)。时间结构与上表一致。完整信号映射见附录 A.2。

**按键映射**：F 键（左手食指）= 正性，J 键（右手食指）= 负性。

### 2.5 训练试次时间结构（TrainingISI → TrainingStim → TrainingResp → TrainingITI → TrainingAns）

与正式试次相同，但额外包含 **TrainingAns**（正确答案反馈，3s，可按q跳过）。

### 2.6 任务指导语

ExpIntro 阶段屏幕显示（20s）：

> 请判断面孔的情绪是正性还是负性，
> 忽略面孔上叠加词语的含义。
> 请在保证正确的前提下尽快按键反应。

### 2.7 刺激材料

- **面孔材料**：优先采用亚洲/中国公开面孔数据集，根据授权可获得性、情绪类别完整性、图片质量和文化适配性确定。当前使用女性面孔，情绪为 happiness（正性）和 anger/disgust/fear（负性）。
- **词语材料**：两字中文词，正性词和负性词各 ≥24 个，在词频、笔画数、熟悉度、效价和唤醒度方面平衡。

### 2.8 主要分析指标

- **行为指标**：反应时、正确率、冲突效应（不一致RT − 一致RT）
- **EEG**：额中线θ冲突效应（θ_power_incongruent − θ_power_congruent），频段4–8 Hz，时间窗300–800 ms，电极ROI: Fz/FCz/Cz
- **fNIRS**：左/右DLPFC HbO冲突效应（HbO_incongruent − HbO_congruent）
- **ECG**：Mean HR、RMSSD

---

## 三、Session_02 — 情绪图片观看与评分任务

### 3.1 流程总览

| 顺序 | 阶段 | Routine 名称 | 内容 | 时长 |
|---|---|---|---|---|
| 1 | Welcome | Welcome | "按下y以开始试验" | 按y键继续 |
| 2 | 信号稳定 | Stable | 注视点"+"，设备信号稳定 | 120 s (2 min) |
| 3 | 恢复静息 | RestingEC | 注视点"+"，闭眼静息 | 180 s (3 min) |
| 4 | 任务指导 | ExpIntro | 任务指导语 | 20 s |
| 5 | 正式试次 | Exp → valence → arousal → isiroutine | 图片观看+Slider评分（循环） | 按图片数（~30张） |
| 6 | 疲劳评分 | Kessler_1 | Slider 1–9 评分 | ≤10 s |
| 7 | 困倦评分 | Kessler_2 | Slider 1–9 评分 | ≤10 s |

### 3.2 任务设计

采用 **情绪图片观看范式**，受试者自然观看每张情绪图片，随后对每张图片的 **情绪愉悦度（valence）** 和 **唤醒程度（arousal）** 分别通过 **Slider（1–9）** 进行评分。

图片从 `Session_02/Session_02.csv` 加载，**随机呈现**。包含正性（Positive）、负性（Negative）和中性（Neutral）三类图片。

### 3.3 单 trial 时间结构（Exp → valence → arousal → isiroutine）

| Routine | 组件 | 内容 | 持续时长 |
|---|---|---|---|
| Exp | text_4 ("+") | 注视点 | 1.0 s |
| | image | 图片，尺寸 (0.8, 0.8) | 3.0 s |
| | serialPort_2 | SerialOut 标记 (3→num, 3s) | 3.0 s |
| valence | valencetext | "请评价这张图片带给你的情绪愉悦度：" | 自由反应 |
| | slider | Slider 1–9，标签：非常不愉快 / 没有感觉 / 非常愉快 | ≤10 s |
| | serialPort_3 | SerialOut 标记 (5→6, slider.rating触发) | condition |
| arousal | arousaltext | "请评价这张图片带给你的唤醒程度：" | 自由反应 |
| | slider_2 | Slider 1–9，标签：非常平静 / 没有感觉 / 非常强烈 | ≤10 s |
| | serialPort_4 | SerialOut 标记 (1→2, slider_2.rating触发) | condition |
| isiroutine | isitext ("+") | ISI | $isi_dur (2.0–3.5 s jitter) |

### 3.4 评分 Slider 配置

| 评分项 | 问题 | Slider 标签 | 范围 |
|---|---|---|---|
| 效价 (valence) | 情绪愉悦度 | 非常不愉快 — 没有感觉 — 非常愉快 | 1–9 |
| 唤醒度 (arousal) | 唤醒程度 | 非常平静 — 没有感觉 — 非常强烈 | 1–9 |
| 疲劳 (Kessler_1) | 疲劳程度 | 完全不疲劳 — 一般疲劳 — 非常疲劳 | 1–9 |
| 困倦 (Kessler_2) | 困倦程度 | 完全清醒 — 一般困倦 — 几乎睡着 | 1–9 |

所有 Slider 均为 9 点刻度 (1–9)，滑块拖曳后自动结束当前 Routine（forceEndRoutine=True）。

### 3.5 任务指导语

ExpIntro 阶段屏幕显示（20s）：

> 接下来屏幕上会呈现不同类型的图片，
> 请你自然观看每张图片，
> 按照自己的真实感受进行反应，
> 无需刻意控制情绪。

### 3.6 主要分析指标

- **主观评分**：效价、唤醒度、疲劳、困倦
- **EEG**：θ/α/β 情绪反应
- **fNIRS**：前额叶血氧反应
- **ECG**：HR、HRV

---

## 四、Session_03 — 冥想任务 + 针刺想象任务

### 4.1 流程总览

| 顺序 | 阶段 | Routine 名称 | 内容 | 时长 |
|---|---|---|---|---|
| 1 | Welcome | Welcome | "按下y以开始试验" | 按y键继续 |
| 2 | 信号稳定 | Stable | 注视点"+"，设备信号稳定 | 120 s (2 min) |
| 3 | 冥想 | Meditation | 呼吸觉察冥想（指导语全程显示） | 360 s (6 min) |
| 4 | 放松评分 | RateMed | Slider 1–9 评分 | ≤10 s |
| 5 | 冥想后静息 | Resting_EC | 注视点"+"，闭眼静息 | 120 s (2 min) |
| 6 | 针刺想象 | Imaging × 3 | 3 个 block（60s 注视基线 + 60s 想象） | ~7 min |
| 7 | 针感评分 | RateIma | Slider 1–9 评分 | ≤10 s |
| 8 | 想象后静息 | Resting_EC | 注视点"+"，闭眼静息 | 120 s (2 min) |
| 9 | 结束 | Ending | 注视点"+" | 10 s |

### 4.2 冥想任务

#### 4.2.1 冥想指导语（屏幕持续显示 360 s）

> 请保持舒适坐姿，身体放松，
> 双眼轻闭或注视屏幕中央。
> 请将注意力放在自然呼吸上，
> 不需要刻意控制呼吸。
> 当你发现注意力被想法、
> 声音或身体感觉带走时，
> 只需轻轻把注意力带回呼吸。
> 整个过程中尽量保持清醒和放松。

采用 **呼吸觉察（breath awareness）** 正念冥想。Meditation Routine 包含 **3 个 SerialOut 标记**，分别在 0 s、120 s、240 s 发送 r→x（各 60 s 间隔），用于分段分析。

#### 4.2.2 放松程度评分（RateMed）

冥想结束后立即呈现，Slider 配置：

| 属性 | 值 |
|---|---|
| 问题文本 | "请评价你在冥想过程中的放松程度：" |
| 刻度 | 1–9 |
| 标签 | 完全不放松 — 一般放松 — 非常放松 |
| 最大时长 | 10 s（forceEndRoutine=True，拖曳后自动结束） |
| SerialOut | r→2（slider.rating 触发） |
| 语音提示 | 04_RelaxRating.wav |

---

### 4.3 针刺想象任务

#### 4.3.1 设计概述

采用 **Block 设计**，共 3 个想象 block（nReps=3），每个 block 包含 60 s 基线注视 + 60 s 针刺感觉想象。

#### 4.3.2 单 block 时间结构（Imaging Routine）

| 阶段 | 组件 | 内容 | 起始时间 | 时长 |
|---|---|---|---|---|
| 基线注视 | text_3 | 注视点"+" | 0 s | 60 s |
| 想象期 | text_2 | 针刺感觉想象指导语（屏幕显示） | 60 s | 60 s |
| | sound_5 | 05_ImagingStart.wav | 60 s | 20 s |
| | sound_6 | 06_ImagingRest.wav | 0 s（routine 开始时） | 10 s |
| | serialPort_6 | SerialOut 标记 (5→6) | 0 s | 60 s |
| | serialPort_7 | SerialOut 标记 (1→2) | 60 s | 60 s |

**block 之间无间隔**，上一个 block 结束后直接进入下一个 block。每个 block 总时长 120 s。

注：sound_6（ImagingRest.wav）在 Imaging Routine 开始时即播放，提示上一轮想象结束后的休息；sound_5（ImagingStart.wav）在 60 s 时播放，提示本轮想象开始。

#### 4.3.3 想象指导语（text_2，屏幕显示 60 s）

> 请回忆或想象针刺时可能出现的感觉，
> 例如酸、麻、胀、重、放松或轻微牵拉感。
> 请尽量在脑中体验这种感觉，
> 但不要移动身体。
> 屏幕提示'休息'时，请停止想象，
> 注视屏幕中央并自然放松。

#### 4.3.4 针感清晰度评分（RateIma）

全部 3 个想象 block 结束后呈现，Slider 配置：

| 属性 | 值 |
|---|---|
| 问题文本 | "请评价你想象针刺感觉（酸、麻、胀、重）的清晰程度：" |
| 刻度 | 1–9 |
| 标签 | 完全无法想象 — 可以想象一些 — 非常清晰逼真 |
| 最大时长 | 10 s（forceEndRoutine=True） |
| SerialOut | 3→4（slider_2.rating 触发） |
| 语音提示 | 09_ImagingRating.wav |

---

### 4.4 主要分析指标

- **冥想任务**：EEG α增强、β降低；ECG HRV变化（Mean HR、RMSSD、HF）；fNIRS 前额叶静息态变化
- **针刺想象任务**：EEG μ/β或感觉运动节律变化；fNIRS 前额叶/感觉运动区域；ECG Mean HR、RMSSD

---

## 五、睁眼/闭眼静息态

### 5.1 Session_01 静息态

| 阶段 | Routine | 位置 | 内容 | 时长 | SerialOut |
|---|---|---|---|---|---|
| Resting_EC | Resting_EC | Main Trials Part A 之前 | 闭眼静息，注视点"+" | 180 s (3 min) | r→x (180s) |
| Resting_EO | Resting_EO | Part A 与 Part B 之间 | 睁眼静息，注视点"+" | 180 s (3 min) | r→x (180s) |

### 5.2 Session_02 静息态

| 阶段 | Routine | 位置 | 内容 | 时长 | SerialOut |
|---|---|---|---|---|---|
| RestingEC | RestingEC | Stable 之后、ExpIntro 之前 | 闭眼静息，注视点"+" | 180 s (3 min) | r→x (180s) |

### 5.3 Session_03 静息态

| 阶段 | Routine | 位置 | 内容 | 时长 | SerialOut |
|---|---|---|---|---|---|
| Resting_EC（第1次） | Resting_EC | RateMed 之后、Imaging 之前 | 注视点"+"，闭眼静息 | 120 s (2 min) | 3→4 (120s) |
| Resting_EC（第2次） | Resting_EC | RateIma 之后、Ending 之前 | 注视点"+"，闭眼静息 | 120 s (2 min) | 3→4 (120s) |

### 5.4 主要分析指标

- **EEG**：α功率、β功率、θ功率
- **fNIRS**：各ROI静息态血氧水平
- **ECG**：Mean HR、RMSSD、SDNN、HF

---

## 六、针刺/TEAS即时采集（健康组特有，尚未实现为 PsychoPy 程序）

> ⚠️ **以下为设计规划，当前 `.psyexp` 文件中尚未实现。** 该部分采集在 PsychoPy 程序外通过其他方式完成。

### 6.1 设计概述

在申脉、照海电针基础上，比较足三里真实电针与TEAS的即时神经生理反应。

### 6.2 刺激条件

| 条件 | 申脉BL62 | 照海KI6 | 足三里ST36 |
|---|---|---|---|
| 条件A（完整电针） | 电针 | 电针 | 电针 |
| 条件B（足三里TEAS） | 电针 | 电针 | TEAS |

### 6.3 单次刺激段流程

| 阶段 | 内容 | 时长 |
|---|---|---|
| 刺激前稳定 | 设备信号稳定、中性注视 | 2–3 min |
| 刺激前静息 | fNIRS-EEG-ECG同步记录 | 3 min |
| 刺激准备 | 进针/贴附电极 | 1–3 min |
| 刺激期 | 条件A或条件B | 10–20 min |
| 刺激后恢复 | 停止刺激后继续记录 | 2–3 min |
| 主观评分 | 针感、疼痛、舒适度、盲法猜测 | 3–5 min |

### 6.4 电刺激伪迹说明

电针和TEAS均可能产生周期性电刺激伪迹，**刺激期间EEG指标作为探索性分析**。刺激期EEG数据需进行伪迹识别和质量控制，必要时剔除伪迹严重片段。

---

## 七、失眠治疗组采集流程

自身对照设计，治疗前后使用**同一套流程**，按 Session_01 → Session_02 → Session_03 顺序运行：

### Session_01：基础静息 + 情绪面孔-词冲突任务（~20 min）

| 顺序 | 阶段 | 时长 |
|---|---|---|
| 1 | Welcome + Adapt（中性注视/稳定信号） | ~2 min |
| 2 | 闭眼静息 | 3 min |
| 3 | 任务说明提示 | 0.5 min |
| 4 | 训练试次（practice） | ~2 min |
| 5 | 正式试次 Part A（96 trial） | ~8 min |
| 6 | 睁眼静息 | 3 min |
| 7 | 任务说明提示（重复） | 0.5 min |
| 8 | 正式试次 Part B（96 trial） | ~8 min |

### Session_02：情绪图片观看与评分任务（~15 min）

| 顺序 | 阶段 | 时长 |
|---|---|---|
| 1 | Welcome + Stable（中性注视/重新稳定信号） | ~2 min |
| 2 | 闭眼静息 | 3 min |
| 3 | 任务说明提示 | 0.5 min |
| 4 | 情绪图片观看与评分（~30张） | ~7 min |
| 5 | 疲劳 + 困倦评分 | ~1.5 min |

### Session_03：冥想 + 针刺想象任务（~22 min）

| 顺序 | 阶段 | 时长 |
|---|---|---|
| 1 | Welcome + Stable（中性注视/稳定信号） | ~2 min |
| 2 | 冥想任务 | 6 min |
| 3 | 放松程度评分 | 0.5 min |
| 4 | 冥想后静息 | 2 min |
| 5 | 针刺想象任务（3 blocks） | ~7 min |
| 6 | 针感清晰度评分 | 0.5 min |
| 7 | 想象后静息 | 2 min |

### 治疗干预

- **穴位**: 申脉BL62、照海KI6、足三里ST36三穴电针
- **波形**: 连续波（频率参考TEAS正交预实验结果）
- **强度**: 个体化调整，以受试者可耐受并出现酸麻胀重等针感为度
- **治疗频率**: 每周5次，连续4周，共20次
- **单次时长**: 30 min

---

## 八、健康对照组采集流程

### 8.1 模块化设计

| 模块 | 包含任务 | 侧重 |
|---|---|---|
| 模块A | Session_01 + Session_03 + 刺激采集 | 情绪冲突与放松调节 |
| 模块B | Session_01 + Session_03（替代版本）+ 刺激采集 | 情绪冲突与针刺表征 |

### 8.2 交叉平衡方案

每名受试者完成4次采集：模块A×条件A、模块A×条件B、模块B×条件A、模块B×条件B各1次。

随机分配至以下四种顺序之一（目标比例1:1:1:1）：

| 顺序 | 第1次 | 第2次 | 第3次 | 第4次 |
|---|---|---|---|---|
| S1 | 模块A+条件A | 模块B+条件B | 模块A+条件B | 模块B+条件A |
| S2 | 模块A+条件B | 模块B+条件A | 模块A+条件A | 模块B+条件B |
| S3 | 模块B+条件A | 模块A+条件B | 模块B+条件B | 模块A+条件A |
| S4 | 模块B+条件B | 模块A+条件A | 模块B+条件A | 模块A+条件B |

### 8.3 各任务完成次数

| 任务 | 完成次数 | 说明 |
|---|---|---|
| 情绪面孔-词冲突 | 2次 | A条件1次 + B条件1次 |
| 情绪图片观看与评分 | 2次 | A条件1次 + B条件1次 |
| 冥想任务 | 2次 | 均在模块A |
| 针刺想象任务 | 2次 | 均在模块B |
| 睁眼/闭眼静息态 | 4次 | 每次采集均完成 |
| 即时刺激采集 | 4次 | 真实电针2次 + TEAS 2次 |

---

## 九、分段采集原则

### 9.1 基本原则

1. 每个 Session 控制在 **22分钟** 以内
2. 每个 Session 结束后**暂停记录并重新开始设备**
3. Session 之间安排 **2–5分钟** 休息
4. 休息期间完成数据保存、信号检查和受试者状态确认
5. 高负荷任务后设置 **2–3分钟** 恢复性静息
6. 不在进针、行针或刺激感觉变化明显阶段重启设备

### 9.2 段间检查内容

1. fNIRS光强和通道信号质量
2. EEG电极阻抗和明显漂移
3. ECG电极稳定性和R波可识别性
4. 受试者疲劳、困倦、情绪状态
5. 数据文件是否正常保存
6. 任务标记是否完整

### 9.3 任务顺序原则

- 按照 Session_01 → Session_02 → Session_03 的顺序执行
- 总体按照「低负荷基线 → 高负荷情绪任务 → 恢复 → 低负荷任务 → 恢复」的原则安排
- 受试者可按 `q` 键提前结束各等候阶段，避免疲劳累积

---

## 十、任务版本与随机化

### 10.1 任务版本

- 情绪任务至少准备 **2–4个等价版本**
- 版本在面孔身份、性别、情绪类别、词语效价、词频、笔画数、按键方向和一致/不一致比例方面平衡

### 10.2 失眠组版本平衡

| 版本序列 | 治疗前 | 治疗后 |
|---|---|---|
| VSeq1 | Version A | Version B |
| VSeq2 | Version B | Version A |

受试者按入组顺序或随机分配至VSeq1或VSeq2。Session_01 内置 Counterbalance（nGroups=2）支持被试间 Part A/B 分配平衡。

### 10.3 健康组版本平衡

- 同一受试者相同任务重复时使用不同版本
- 不同顺序类型S1–S4中任务版本分布尽量均衡
- 任务版本不与刺激条件固定绑定，避免版本效应与刺激效应混杂

---

## 十一、两组任务可比性

| 任务 | 失眠组 | 健康组 |
|---|---|---|
| 闭眼/睁眼静息 | 治疗前、治疗后各1次 | 4次采集均完成 |
| 情绪面孔-词冲突 | 治疗前、治疗后各1次 | 模块A中完成2次 |
| 情绪图片观看与评分 | 治疗前、治疗后各1次 | 模块A中完成2次 |
| 冥想任务 | 治疗前、治疗后各1次 | 模块A中完成2次 |
| 针刺想象任务 | 治疗前、治疗后各1次 | 模块B中完成2次 |
| 针刺即时采集 | 不设置 | 真实电针2次 + TEAS 2次 |

---

## 附录 A：Session_01 事件标记（SerialOut）— 当前方案

### A.1 信号设计原理

两个串口设备共用 COM4（Y 分流），对发送字节的解读方式不同：

| 设备 | 可区分事件 | 编码方式 |
|---|---|---|
| **fNIRS 触发设备** | 3 个通道 (CH0/CH1/CH2) | 仅识别最低置位 bit：`0x01`=CH0, `0x02`=CH1, `0x04`=CH2 |
| **Synamp 设备** | 15 个值（低 4 位编码） | `output = 0x80 \| ((~b0 & 1) << 6) \| (b1 << 5) \| (b2 << 4) \| (b3 << 3)` |

详细协议见 `fnirs.md` 和 `synamp.md`。

### A.2 信号映射表

| Routine | 组件 | start→stop | fNIRS 看到 | Synamp 看到 | 数据类型 |
|---|---|---|---|---|---|
| Resting_EC / Resting_EO | serialPort_5 | `1→2` | CH0→CH1 | 160→224 | binary (巧合安全) |
| **MainStim** | serialPort | `4→2` | CH2→CH1 | 208→224 | **num** |
| **MainResp** | serialPort_3 | `9→13` | (无)→(无) | 168→184 | **num** |
| **MainStim_B** | serialPort_2 | `4→2` | CH2→CH1 | 208→224 | **num** |
| **MainResp_B** | serialPort_10 | `10→15` | (无)→(无) | 232→152 | **num** |
| Ending | serialPort_5 | `1→2` | CH0→CH1 | 160→224 | binary |

> **注意**：所有 trial SerialOut 组件必须使用 `num`（numeric）数据类型，不能使用 `binary`。原因见 A.5 节。

### A.3 fNIRS 解读

```
每次刺激试次: CH2(start) → CH1(stop)   // Part A 和 Part B 共用，靠对齐标记区分
每次按键响应: 无 fNIRS 事件              // 靠刺激试次上下文推断
静息态开始/结束: CH0→CH1                 // 但主要靠对齐标记识别
```

### A.4 块对齐标记（5 字节编码序列）

在 PsychoPy Code Component 中插入，用于两侧设备数据对齐：

| 标记 | 序列 | fNIRS | Synamp |
|---|---|---|---|
| **START** | `0x01→0x02→0x04→0x02→0x01` | CH0→CH1→CH2→CH1→CH0 | 160→224→208→224→160 |
| **END** | `0x04→0x02→0x01→0x02→0x04` | CH2→CH1→CH0→CH1→CH2 | 208→224→160→224→208 |

- 间隔 300ms，总长约 1.5s
- 对称金字塔结构，丢 1-2 个事件仍可识别
- 代码模板见 `beginroutine.py` / `endroutine.py`

### A.5 .ps1 补丁机制与数据类型陷阱

`.ps1` 脚本在运行前对 `_lastrun.py` 执行两个正则替换：

```
1. \b0b(\d+)\b → $1           # 删除 0b 前缀
2. \.sendMessage\((\d+)\) → .sendMessage(bytes(chr($1), 'utf-8'))
```

**陷阱**：`0b100`(二进制=4) 被替换为 `100`(十进制) 而非 `4`，导致 `sendMessage(100)` 发送 `0x64` 而非 `0x04`。

**解决方案**：`.psyexp` 中所有 SerialOut 数据类型必须设为 **`num`**（numeric），直接用十进制值（如 `4`），避免生成 `0b` 前缀代码。仅 `1` 和 `2`（`0b1=1`、`0b2=2`）在 `binary` 类型下巧合正确。

### A.6 Session_01 三变体

| 变体 | psyexp | ps1 |
|---|---|---|
| 标准 | `Session_01.psyexp` | `Session_01.ps1` |
| 短刺激 | `Session_01_ShortStim.psyexp` | `Session_01_ShortStim.ps1` |
| 固定时长 | `Session_01_FixedStim.psyexp` | `Session_01_FixedStim.ps1` |

三者的 SerialOut 信号方案和事件标记编码完全一致。区别在于 **刺激呈现方式** 和 **按键响应逻辑**，从而适用于不同的实验需求和数据分析策略。

#### A.6.1 标准版 (Session_01.psyexp)

**设计理念**：经典的分离式刺激-响应范式，刺激消失后进入独立的反应窗口。适合需要严格分离刺激编码和反应准备过程的 ERP/fNIRS 分析。

**单试次 Routines**（Part A 为例）：
```
MainISI(0.5s+jitter) → MainStim(1.0s固定) → MainResp(按键结束) → MainITI(0.5s+jitter)
```

| 特性 | 值 |
|---|---|
| 刺激呈现时长 | 1.0 s（固定，image + text 同时显示） |
| 反应窗口 | MainResp 独立 Routine，text_17 持续显示直到按键 |
| 按键行为 | `key_resp_10`: `forceEndRoutine=True`，`stopVal=""`（无超时，等待按键） |
| Part A SerialOut | MainStim: `serialPort` (4→2)，MainResp: `serialPort_3` (9→13) |
| Part B SerialOut | MainStim_B: `serialPort_2` (4→2)，MainResp_B: `serialPort_10` (10→15) |

**优点**：刺激编码期与反应准备期在时间上完全分离，便于 ERP 成分（如 N2、P3）和 fNIRS 血流动力学响应的精确锁时。

**缺点**：总试次时长较长（~5 s/trial），被试可能在反应窗口提前准备按键策略。

---

#### A.6.2 短刺激版 (Session_01_ShortStim.psyexp)

**设计理念**：按键响应嵌入刺激呈现 Routine 内部，刺激随按键消失。减少试次总时长，适合以行为指标（RT/ACC）为主要关注点的实验，或需要最大化试次数的场景。

**单试次 Routines**（Part A 为例）：
```
MainISI(0.5s+jitter) → MainStim(刺激+按键收集, 按键结束) → MainITI(0.5s+jitter)
```

| 特性 | 值 |
|---|---|
| 刺激呈现时长 | 无固定时长 — 按键后 Routine 结束，刺激消失 |
| 反应窗口 | **内嵌于 MainStim**，无独立 MainResp Routine |
| 按键行为 | `key_resp_12`: `forceEndRoutine=True`，`stopVal="key_resp_12.keys"`（按键立即结束） |
| Part A SerialOut | MainStim: `serialPort_2` (4→2)，按键时 `serialPort_3` (9→13) |
| Part B SerialOut | MainStim_B: `serialPort_9` (…)，按键时 `serialPort_10` (…) |

**优点**：试次时长最短（被试 RT + jitter），适合大量试次；刺激-反应时间耦合紧密，RT 测量更直接。

**缺点**：刺激消失与按键同时发生，难以分离刺激编码和运动准备的神经信号；刺激呈现时长不均等（由 RT 决定），可能引入视觉输入时长的混淆变量。

---

#### A.6.3 固定时长版 (Session_01_FixedStim.psyexp)

**设计理念**：刺激呈现时长固定（1.2 s），按键在刺激呈现期间收集但不终止 Routine。所有试次刺激暴露时间完全一致，适合需要严格控制视觉输入时长的 fNIRS/EEG 分析。

**单试次 Routines**（Part A 为例）：
```
MainISI(0.5s+jitter) → MainStim(1.2s固定: 刺激+按键收集+ITI)
```

| 特性 | 值 |
|---|---|
| 刺激呈现时长 | 1.2 s（固定，image + text_16） |
| 反应窗口 | **内嵌于 MainStim**，无独立 MainResp / MainITI Routine |
| 按键行为 | `key_resp_12`: `forceEndRoutine=False`，允许在刺激期内按键但不终止 Routine |
| ITI 实现 | `text_28`（指令文字）的 stopVal = `$partA_iti`，ITI 在 MainStim 内部完成 |
| Routine 结束条件 | `stopVal="bool(key_resp_12.keys) or text_28.status == FINISHED"`（按键或 ITI 文字结束均可触发） |

**优点**：每个试次的刺激暴露时长完全一致（1.2 s），消除视觉输入时长的混淆；ITI 整合在同 Routine 内，减少 Routine 切换开销。

**缺点**：若被试在 1.2 s 内未按键，无法获得该试次的 RT；刺激-反应时间耦合较松散。

---

#### A.6.4 三变体对比总结

| 维度 | 标准版 | 短刺激版 | 固定时长版 |
|---|---|---|---|
| **每试次 Routine 数** | 4（ISI + Stim + Resp + ITI） | 3（ISI + Stim + ITI） | 2（ISI + Stim） |
| **刺激时长** | 1.0 s 固定 | 由 RT 决定（按键结束） | 1.2 s 固定 |
| **反应窗口** | 独立 MainResp Routine | 内嵌于 MainStim | 内嵌于 MainStim |
| **forceEndRoutine** | True（响应 Routine） | True（刺激 Routine） | **False** |
| **典型试次时长** | ~5 s | ~2–3 s | ~2.5–3.5 s |
| **适用场景** | ERP/fNIRS 精确锁时分析 | 行为实验、大量试次 | 视觉输入严格控制分析 |
| **刺激-反应锁时** | 精确分离 | 紧密耦合 | 松散耦合（固定窗口） |
| **RT 可用性** | 全部试次 | 全部试次 | 仅 1.2 s 内按键的试次 |

> **版本选择建议**：
> - **默认使用标准版**：最经典的 Stroop 范式实现，适合绝大多数 ERP/fNIRS 研究。
> - **短刺激版用于**：需要最大化试次数的场景，或以行为指标（RT/冲突效应）为主要因变量的实验。
> - **固定时长版用于**：需要严格控制视觉输入时长的场景（如比较不同刺激类型诱发的血流动力学响应），或担心被试提前准备按键策略时。

## 附录 B：Session_02 事件标记（SerialOut）

| Routine | startDataNumeric | stopDataNumeric | stopType | 说明 |
|---|---|---|---|---|
| RestingEC | 114 (r) | 120 (x) | duration=180s | 闭眼静息标记 |
| Exp | 114 (r) | 4 | duration=3s | 图片呈现标记 (3→num) |
| valence | 114 (r) | 120 (x) | slider.rating | 效价评分标记 (5→6) |
| arousal | 114 (r) | 120 (x) | slider_2.rating | 唤醒度评分标记 (1→2) |
| Kessler_1 | 114 (r) | 120 (x) | slider_3.rating | 疲劳评分标记 (1→3) |
| Kessler_2 | 114 (r) | 120 (x) | slider_4.rating | 困倦评分标记 (2→4) |

## 附录 C：Session_03 事件标记（SerialOut）

| Routine | 组件 | startDataNumeric | stopDataNumeric | stopType | 说明 |
|---|---|---|---|---|---|
| Meditation | serialPort | 114 (r) | 120 (x) | duration=60s | 冥想段1 (1→2) |
| | serialPort_2 | 114 (r) | 120 (x) | duration=60s, start=120s | 冥想段2 (3→4) |
| | serialPort_3 | 114 (r) | 120 (x) | duration=60s, start=240s | 冥想段3 (5→6) |
| RateMed | serialPort_4 | 114 (r) | 120 (x) | slider.rating | 放松评分标记 (1→2) |
| Resting_EC | serialPort_5 | 114 (r) | 120 (x) | duration=120s | 冥想后静息 (3→4) |
| Imaging | serialPort_6 | 114 (r) | 120 (x) | duration=60s | 想象基线期 (5→6) |
| | serialPort_7 | 114 (r) | 120 (x) | duration=60s, start=60s | 想象期 (1→2) |
| RateIma | serialPort_8 | 114 (r) | 120 (x) | slider_2.rating | 针感评分标记 (3→4) |

## 附录 D：各 Session 语音提示清单（与 .psyexp 引用一致）

### Session_01

| 音频文件 | 对应 Routine | 触发时机 |
|---|---|---|
| `audio_prompts/Session_01/01_Welcome.wav` | Welcome | Routine 开始时 |
| `audio_prompts/Session_01/02_Adapt.wav` | Adapt | Routine 开始时 |
| `audio_prompts/Session_01/03_Resting_EC.wav` | Resting_EC | Routine 开始时 |
| `audio_prompts/Session_01/04_Resting_EO.wav` | Resting_EO | Routine 开始时 |
| `audio_prompts/Session_01/05_ExpIntro.wav` | ExpIntro | Routine 开始时 |
| `audio_prompts/Session_01/08_RestPrompt.wav` | Ending | Routine 开始时 |

### Session_02

| 音频文件 | 对应 Routine | 触发时机 |
|---|---|---|
| `audio_prompts/Session_02/01_Welcome.wav` | Welcome | Routine 开始时 |
| `audio_prompts/Session_02/02_Stable.wav` | Stable | Routine 开始时 |
| `audio_prompts/Session_02/03_ExpIntro.wav` | ExpIntro | Routine 开始时 |
| `audio_prompts/Session_02/06_RestingEC.wav` | RestingEC | Routine 开始时 |
| `audio_prompts/Session_02/07_Kessler_1.wav` | Kessler_1 | Routine 开始时 |
| `audio_prompts/Session_02/08_Kessler_2.wav` | Kessler_2 | Routine 开始时 |

### Session_03

| 音频文件 | 对应 Routine | 触发时机 |
|---|---|---|
| `audio_prompts/Session_03/01_Welcome.wav` | Welcome | Routine 开始时 |
| `audio_prompts/Session_03/02_Stable.wav` | Stable | Routine 开始时 |
| `audio_prompts/Session_03/03_Meditation.wav` | Meditation | Routine 开始时 |
| `audio_prompts/Session_03/04_RelaxRating.wav` | RateMed | Routine 开始时 |
| `audio_prompts/Session_03/04_MeditationEnd.wav` | Resting_EC | Routine 开始时 |
| `audio_prompts/Session_03/05_ImagingStart.wav` | Imaging | 60s 时播放（想象开始） |
| `audio_prompts/Session_03/06_ImagingRest.wav` | Imaging | Routine 开始时播放（休息提示） |
| `audio_prompts/Session_03/09_ImagingRating.wav` | RateIma | Routine 开始时 |
| `audio_prompts/Session_03/09_Finish.wav` | Ending | Routine 开始时 |

---

## 附录 E：提示音文本设计

在 fNIRS-EEG-ECG 同步采集实验中，提示音的作用是：
1. **事件标记** — 为数据分析提供精确时间锚点
2. **被试引导** — 特别在闭眼/冥想等无法阅读屏幕的阶段
3. **阶段过渡** — 标明任务切换

以下内容与 `.psyexp` 文件中的实际引用严格一致。

---

### E.1 Session_01 — 情绪面孔-词冲突任务

**实际 Flow**（来自 `Session_01.psyexp`）：
```
Welcome → Adapt(120s) → Resting_EC(180s) → ExpIntro(20s)
→ [Training trials loop] → Training2Main
→ [Main trials Part A (96 trials): MainISI→MainStim→MainResp→MainITI]
→ Resting_EO(180s) → ExpIntro(20s)
→ [Main trials Part B (96 trials): MainISI→MainStim→MainResp→MainITI]
→ Ending(5s)
```

#### 提示音列表

| # | 音频文件 (.wav) | 对应 Routine | 触发时机 | 提示音文本 |
|---|---|---|---|---|
| 1 | `01_Welcome` | Welcome | Routine 开始时 | 实验即将开始，请保持身体稳定，减少眨眼和吞咽。 |
| 2 | `02_Adapt` | Adapt | Routine 开始时 | 信号稳定阶段。请注视屏幕中央的十字，自然放松。 |
| 3 | `03_Resting_EC` | Resting_EC | Routine 开始时 | 请闭上双眼，保持清醒，自然放松，不要思考任何事情。 |
| 4 | `04_Resting_EO` | Resting_EO | Routine 开始时 (Part A/B 之间) | 请睁开双眼，注视屏幕中央的十字，保持放松。 |
| 5 | `05_ExpIntro` | ExpIntro | Routine 开始时（两次：Part A 前和 Part B 前） | 接下来请阅读屏幕上的任务说明，按Q键继续。 |
| 6 | `08_RestPrompt` | Ending | Routine 开始时 | 请放松休息，等待试验员操作。 |

**注**：训练试次（TrainingISI/Stim/Resp/ITI/Ans）和正式试次（MainISI/Stim/Resp/ITI）**不播放提示音**。按键响应（f/j）和 SerialOut 标记充当事件锚点。

---

### E.2 Session_02 — 情绪图片观看与评分任务

**实际 Flow**（来自 `Session_02.psyexp`）：
```
Welcome → Stable(120s) → RestingEC(180s) → ExpIntro(20s)
→ [Trials loop: Exp(1s+3s) → valence(slider) → arousal(slider) → isiroutine($isi_dur)]
→ Kessler_1(slider) → Kessler_2(slider)
```

#### 提示音列表

| # | 音频文件 (.wav) | 对应 Routine | 触发时机 | 提示音文本 |
|---|---|---|---|---|
| 1 | `01_Welcome` | Welcome | Routine 开始时 | 实验即将开始，请保持身体稳定，减少眨眼和吞咽。 |
| 2 | `02_Stable` | Stable | Routine 开始时 | 信号稳定阶段。请注视屏幕中央的十字，自然放松。 |
| 3 | `03_ExpIntro` | ExpIntro | Routine 开始时 | 接下来请阅读屏幕上的任务说明，按Q键继续。 |
| 4 | `06_RestingEC` | RestingEC | Routine 开始时（Stable 之后、ExpIntro 之前） | 请注视屏幕中央的十字，自然放松。请闭上双眼。 |
| 5 | `07_Kessler_1` | Kessler_1 | Routine 开始时 | 请按屏幕提示，用数字键1到9评价你现在的疲劳程度。 |
| 6 | `08_Kessler_2` | Kessler_2 | Routine 开始时 | 请按屏幕提示，用数字键1到9评价你现在的困倦程度。 |

**注**：
- 试次循环中（Exp/valence/arousal/isiroutine）**不播放提示音**，SerialOut 标记充当事件锚点。
- RestingEC（3 min 闭眼静息）位于 **Stable 之后、ExpIntro 之前**（而非 trial 之后），用于采集正式任务前的基线静息态数据。
- Kessler 评分使用 **Slider（1–9 拖曳）** 而非键盘输入。

---

### E.3 Session_03 — 冥想 + 针刺想象任务

**实际 Flow**（来自 `Session_03.psyexp`）：
```
Welcome → Stable(120s) → Meditation(360s) → RateMed(slider, 10s)
→ Resting_EC(120s)
→ [Imaging loop ×3: 60s基线注视 + 60s想象]
→ RateIma(slider, 10s)
→ Resting_EC(120s)
→ Ending(10s)
```

#### 提示音列表

| # | 音频文件 (.wav) | 对应 Routine | 触发时机 | 提示音文本 |
|---|---|---|---|---|
| 1 | `01_Welcome` | Welcome | Routine 开始时 | 实验即将开始，请保持身体稳定，减少眨眼和吞咽。 |
| 2 | `02_Stable` | Stable | Routine 开始时 | 信号稳定阶段。请注视屏幕中央的十字，自然放松。 |
| 3 | `03_Meditation` | Meditation | Routine 开始时 | 冥想阶段开始。请保持舒适坐姿，身体放松。将注意力放在自然呼吸上，不需要刻意控制呼吸。 |
| 4 | `04_RelaxRating` | RateMed | Routine 开始时 | 请按屏幕提示，用数字键1到9评价你在冥想过程中的放松程度。 |
| 5 | `04_MeditationEnd` | Resting_EC | Routine 开始时（两次：冥想后、想象后） | 冥想结束。请闭上双眼，自然放松，不要思考任何事情。 |
| 6 | `05_ImagingStart` | Imaging | 60 s 时（想象期开始） | 想象阶段开始。请回忆或想象针刺时可能出现的感觉，例如酸、麻、胀、重。请尽量在脑中体验这种感觉，但不要移动身体。 |
| 7 | `06_ImagingRest` | Imaging | Routine 开始时（提示上一轮结束） | 休息。请停止想象，注视屏幕中央并自然放松。 |
| 8 | `09_ImagingRating` | RateIma | Routine 开始时 | 请按屏幕提示，用数字键1到9评价你想象针刺感觉的清晰程度。 |
| 9 | `09_Finish` | Ending | Routine 开始时 | 本次采集结束，感谢您的配合。 |

**注**：
- Meditation Routine 包含 **3 个 SerialOut 标记**（0s/120s/240s 各发 r→x，间隔 60s），用于分段分析。引导语在屏幕上持续显示 360s，无需额外音频覆盖。
- Imaging Routine 内部包含两个文本组件：text_3（注视点"+"，60s）和 text_2（想象指导语，60s，从 60s 开始）。sound_6（ImagingRest）在 Routine 开始时即播放，sound_5（ImagingStart）在 60s 时播放。
- Resting_EC 在流程中出现 **两次**（冥想后和想象后），使用相同 Routine（含 `04_MeditationEnd.wav` 音频和 SerialOut 3→4 标记）。

---

### E.4 主观评分 Slider 配置

冥想和针刺想象任务后各插入一个 1–9 Slider 评分，格式与 Session_02 中的 Kessler 评分一致。

#### 冥想后 — 放松程度评分 (RateMed)

| 属性 | 值 |
|---|---|
| Routine | RateMed |
| 问题文本 | 请评价你在冥想过程中的放松程度： |
| 刻度 | 1–9 |
| 标签 | 完全不放松 — 一般放松 — 非常放松 |
| 最大时长 | 10 s（forceEndRoutine=True，拖曳后自动结束） |
| 语音提示 | `04_RelaxRating.wav` |
| 目的 | 评估冥想任务的主观放松效果，与 EEG α 增强、HRV 变化做相关分析 |

#### 针刺想象后 — 针感清晰度评分 (RateIma)

| 属性 | 值 |
|---|---|
| Routine | RateIma |
| 问题文本 | 请评价你想象针刺感觉（酸、麻、胀、重）的清晰程度： |
| 刻度 | 1–9 |
| 标签 | 完全无法想象 — 可以想象一些 — 非常清晰逼真 |
| 最大时长 | 10 s（forceEndRoutine=True） |
| 语音提示 | `09_ImagingRating.wav` |
| 目的 | 评估针刺想象任务的主观体验质量，用于筛选有效 trial 和与 fNIRS/EEG 感觉运动区激活做相关 |

---

### E.5 通用提示音（尚未在 .psyexp 中引用）

| 用途 | 提示音文本 |
|---|---|
| 通用实验准备 | 请调整至舒适坐姿，双手自然放在键盘或大腿上，在整个实验过程中请尽量保持头部和身体不动。 |
| 信号质量提醒 | 请保持身体稳定，减少眨眼和头动，以确保信号质量。 |

---

### E.6 generate_prompts.py 与 .psyexp 引用对照

以下列出 `generate_prompts.py` 中定义但 **未被 .psyexp 实际引用** 的提示音条目：

| Session | 条目 | 状态 |
|---|---|---|
| S01 | `06_MainTrials` | 未在 psyexp 中引用（MainTrials 循环无音频） |
| S01 | `07_Recovery` | 未在 psyexp 中引用（Ending 使用 08_RestPrompt） |
| S02 | `04_Trials` | 未在 psyexp 中引用（试次循环无音频） |
| S02 | `05_MidBreak` | 未在 psyexp 中引用（无中途休息阶段） |
| S03 | `08_ImagingResume` | 未在 psyexp 中引用（block 间直接过渡） |
| S03 | `10_ImagingEnd` | 未在 psyexp 中引用（RateIma 评分后直接 Resting_EC） |

> 注：`generate_prompts.py` 中 S03 的 `05_MeditationEnd` 生成的音频文件名为 `05_MeditationEnd.wav`，但 `.psyexp` 中 Resting_EC 实际引用的是 `04_MeditationEnd.wav`。如需一致，可将 generate_prompts.py 的键名改为 `04_MeditationEnd`，或修改 psyexp 中的引用路径。

---

### E.7 设计说明

1. **长度控制**：每条提示音控制在 5–15 秒朗读时长，避免打断实验节奏
2. **双语统一**：全中文，与现有实验指导语风格一致
3. **事件标记对齐**：每条提示音的 onset 时间可作为 EEG/fNIRS 分析的 event marker，与 `.psyexp` 中的 Routine start/stop 严格对齐；试次循环中 SerialOut 标记承担事件锚点角色
4. **闭眼特化**：Session_01 的 Resting_EC 和 Session_03 的 Meditation/Resting_EC 都有"请闭上双眼"的明确提示，因为闭眼时被试无法阅读屏幕
5. **冥想阶段**：Session_03 冥想期的指导语已在 `.psyexp` 中以屏幕文字呈现（360s 持续显示），无需额外音频覆盖；仅在阶段转换处添加简短提示
6. **避免不一致**：不添加未被 psyexp 引用的提示音条目到正式实验流程中（如 S02 的 MidBreak、S03 的 ImagingResume 等），避免与实验程序不一致
