#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Psychopy 提示音语音生成脚本
基于 Xiaomi MiMo TTS v2.5 API (mimo-v2.5-tts)

用法:
    1. 设置环境变量: set MIMO_API_KEY=your_api_key
    2. 运行: python generate_prompts.py
    3. 可选参数: python generate_prompts.py --voice 茉莉 --output ./audio --skip-existing

依赖: pip install openai
"""

import os
import sys
import time
import base64
import argparse
from pathlib import Path
from typing import Optional

# 修复 Windows 控制台 GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from openai import OpenAI

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
API_KEY = os.environ.get("MIMO_API_KEY", "")
BASE_URL = "https://api.xiaomimimo.com/v1"
MODEL = "mimo-v2.5-tts"

# 默认音色 (中国集群默认 冰糖 — 温和女声)
DEFAULT_VOICE = "冰糖"

# 全局风格标签 — 实验提示音需平静、温和、清晰
STYLE_TAG = "(温和 平静)"

# 输出根目录
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "audio_prompts"

# API 调用间隔 (秒)，避免触发限速
REQUEST_DELAY = 0.5

# ---------------------------------------------------------------------------
# 提示音文本定义 — 与 提示音文本设计.md 严格一致
# ---------------------------------------------------------------------------
PROMPTS = {
    "Session_01": {
        "01_Welcome": "实验即将开始，请保持身体稳定，减少眨眼和吞咽。",
        "02_Adapt": "信号稳定阶段。请注视屏幕中央的十字，自然放松。",
        "03_Resting_EC": "请闭上双眼，保持清醒，自然放松，不要思考任何事情。",
        "04_Resting_EO": "请睁开双眼，注视屏幕中央的十字，保持放松。",
        "05_ExpIntro": "接下来请阅读屏幕上的任务说明，按Q键继续。",
        "06_MainTrials": "正式实验开始。请在保证正确的前提下，尽快按键判断面孔情绪。正性面孔按F键，负性面孔按J键。",
        "07_Recovery": "任务结束。请放松休息，保持注视屏幕中央的十字。",
        "08_RestPrompt": "请放松休息，等待试验员操作。",
    },
    "Session_02": {
        "01_Welcome": "实验即将开始，请保持身体稳定，减少眨眼和吞咽。",
        "02_Stable": "信号稳定阶段。请注视屏幕中央的十字，自然放松。",
        "03_ExpIntro": "接下来请阅读屏幕上的任务说明，按Q键继续。",
        "04_Trials": "正式实验开始。请自然观看每张图片，按照自己的真实感受进行评分。",
        "05_MidBreak": "请稍作休息，保持身体不动，准备继续。",
        "06_RestingEC": "请注视屏幕中央的十字，自然放松。请闭上双眼。",
        "07_Kessler_1": "请按屏幕提示，用数字键1到9评价你现在的疲劳程度。",
        "08_Kessler_2": "请按屏幕提示，用数字键1到9评价你现在的困倦程度。",
    },
    "Session_03": {
        "01_Welcome": "实验即将开始，请保持身体稳定，减少眨眼和吞咽。",
        "02_Stable": "信号稳定阶段。请注视屏幕中央的十字，自然放松。",
        "03_Meditation": "冥想阶段开始。请保持舒适坐姿，身体放松。将注意力放在自然呼吸上，不需要刻意控制呼吸。",
        "04_RelaxRating": "请按屏幕提示，用数字键1到9评价你在冥想过程中的放松程度。",
        "05_MeditationEnd": "冥想结束。请闭上双眼，自然放松，不要思考任何事情。",
        "06_ImagingStart": "想象阶段开始。请回忆或想象针刺时可能出现的感觉，例如酸、麻、胀、重。请尽量在脑中体验这种感觉，但不要移动身体。",
        "07_ImagingRest": "休息。请停止想象，注视屏幕中央并自然放松。",
        "08_ImagingResume": "请再次回忆或想象针刺时的感觉。",
        "09_ImagingRating": "请按屏幕提示，用数字键1到9评价你想象针刺感觉的清晰程度。",
        "10_ImagingEnd": "任务结束。请闭上双眼，自然放松，不要思考任何事情。",
        "11_Finish": "本次采集结束，感谢您的配合。",
    },
}

# 通用提示音 (可选)
COMMON_PROMPTS = {
    "00_Prepare": "请调整至舒适坐姿，双手自然放在键盘或大腿上，在整个实验过程中请尽量保持头部和身体不动。",
    "00_SignalQuality": "请保持身体稳定，减少眨眼和头动，以确保信号质量。",
}

# ---------------------------------------------------------------------------
# 核心函数
# ---------------------------------------------------------------------------
def build_client() -> OpenAI:
    if not API_KEY:
        print("❌ 错误: 未设置 MIMO_API_KEY 环境变量")
        print("   PowerShell: $env:MIMO_API_KEY = 'your_key'")
        print("   CMD:        set MIMO_API_KEY=your_key")
        sys.exit(1)
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


def synthesize(
    client: OpenAI,
    text: str,
    voice: str = DEFAULT_VOICE,
    style_tag: str = STYLE_TAG,
    audio_format: str = "wav",
) -> bytes:
    """调用 MiMo TTS API 合成语音，返回原始音频字节。"""
    # 将风格标签注入 assistant content 开头
    assistant_text = text
    if style_tag and not assistant_text.startswith("("):
        assistant_text = f"{style_tag}{assistant_text}"

    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "用温和、平静、清晰的语调朗读以下实验指导语，语速适中，像实验室助手在引导被试。",
            },
            {
                "role": "assistant",
                "content": assistant_text,
            },
        ],
        audio={
            "format": audio_format,
            "voice": voice,
        },
    )

    message = completion.choices[0].message
    return base64.b64decode(message.audio.data)


def save_audio(audio_bytes: bytes, filepath: Path) -> None:
    """保存音频文件，自动创建目录。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(audio_bytes)


def generate_all(
    client: OpenAI,
    voice: str,
    output_dir: Path,
    skip_existing: bool = True,
    include_common: bool = False,
    delay: float = REQUEST_DELAY,
) -> dict:
    """
    遍历所有提示音文本，调用 API 生成音频。
    返回: {filename: success_or_error}
    """
    results = {}
    total = 0
    success = 0
    skipped = 0
    failed = 0

    # 统计总数
    all_prompts: list[tuple[str, str, str]] = []  # (session, phase, text)
    for session, phases in PROMPTS.items():
        for phase, text in phases.items():
            all_prompts.append((session, phase, text))

    if include_common:
        for phase, text in COMMON_PROMPTS.items():
            all_prompts.append(("Common", phase, text))

    total = len(all_prompts)
    print(f"🎙️  音色: {voice} | 模型: {MODEL}")
    print(f"📂 输出目录: {output_dir.resolve()}")
    print(f"📋 共 {total} 条提示音待生成\n")

    for idx, (session, phase, text) in enumerate(all_prompts, 1):
        filename = f"{phase}.wav"
        filepath = output_dir / session / filename

        # 显示进度
        print(f"[{idx:2d}/{total}] {session}/{filename} ", end="", flush=True)

        # 跳过已存在
        if skip_existing and filepath.exists():
            print("⏭️  已存在，跳过")
            skipped += 1
            continue

        try:
            audio_bytes = synthesize(client, text, voice=voice)
            save_audio(audio_bytes, filepath)
            size_kb = len(audio_bytes) / 1024
            print(f"✅ {size_kb:.1f} KB")
            success += 1
        except Exception as e:
            print(f"❌ {e}")
            results[f"{session}/{filename}"] = str(e)
            failed += 1

        if idx < total and delay > 0:
            time.sleep(delay)

    # 汇总
    print(f"\n{'='*50}")
    print(f"✅ 成功: {success} | ⏭️ 跳过: {skipped} | ❌ 失败: {failed}")
    print(f"📂 文件位于: {output_dir.resolve()}")

    return results


# ---------------------------------------------------------------------------
# 单条测试模式
# ---------------------------------------------------------------------------
def test_single(
    client: OpenAI,
    text: str,
    voice: str = DEFAULT_VOICE,
    output: Optional[Path] = None,
) -> None:
    """测试单条文本的合成效果。"""
    print(f"🎙️  测试合成: {text[:50]}...")
    audio_bytes = synthesize(client, text, voice=voice)
    if output is None:
        output = Path("test_prompt.wav")
    save_audio(audio_bytes, output)
    print(f"✅ 已保存: {output.resolve()} ({len(audio_bytes) / 1024:.1f} KB)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Psychopy 实验提示音批量生成 (MiMo TTS v2.5)"
    )
    parser.add_argument(
        "--voice",
        default=DEFAULT_VOICE,
        choices=["冰糖", "茉莉", "苏打", "白桦"],
        help=f"音色选择 (默认: {DEFAULT_VOICE})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出根目录 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="跳过已存在的音频文件 (默认开启)",
    )
    parser.add_argument(
        "--no-skip",
        dest="skip_existing",
        action="store_false",
        help="强制重新生成所有文件",
    )
    parser.add_argument(
        "--include-common",
        action="store_true",
        help="同时生成通用跨Session提示音",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"API 调用间隔秒数 (默认: {REQUEST_DELAY})",
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="TEXT",
        help="测试单条文本，不执行批量生成",
    )
    parser.add_argument(
        "--test-output",
        type=Path,
        default=None,
        help="测试模式输出路径 (默认: ./test_prompt.wav)",
    )

    args = parser.parse_args()

    client = build_client()

    if args.test:
        test_single(client, args.test, voice=args.voice, output=args.test_output)
        return

    generate_all(
        client,
        voice=args.voice,
        output_dir=args.output,
        skip_existing=args.skip_existing,
        include_common=args.include_common,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()
