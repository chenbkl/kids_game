#!/usr/bin/env bash
set -euo pipefail

# ===== 输出配置 =====
OUT_DIR="cartoon_animals_out"
RAW_DIR="${OUT_DIR}/raw"
WAV_DIR="${OUT_DIR}/wav"
MP3_DIR="${OUT_DIR}/mp3"

mkdir -p "$RAW_DIR" "$WAV_DIR" "$MP3_DIR"

# ===== 卡通化参数（你可以微调）=====
# 目标时长（秒）
DUR="1.2"

# 升调半音数：+4 ~ +7 更萌；太大会刺耳
SEMITONES="5"

# 由半音计算频率倍率：2^(n/12)
PITCH_FACTOR=$(python3 - <<PY
import math
n=float("${SEMITONES}")
print(math.pow(2.0, n/12.0))
PY
)

# 为了“只升调不变速”，用 asetrate + atempo 抵消
# atempo 允许范围 0.5~2.0，这里一般没问题
ATEMPO=$(python3 - <<PY
pf=float("${PITCH_FACTOR}")
print(1.0/pf)
PY
)

# ===== 素材清单（家禽/畜类）=====
declare -A URLS=(
  [cow]="https://upload.wikimedia.org/wikipedia/commons/4/48/Mudchute_cow_1.ogg"
  [pig]="https://upload.wikimedia.org/wikipedia/commons/7/73/Mudchute_pig_1.ogg"
  [sheep]="https://upload.wikimedia.org/wikipedia/commons/2/2a/Mudchute_sheep_1.ogg"
  [lamb]="https://upload.wikimedia.org/wikipedia/commons/7/72/Mudchute_lamb_1.ogg"
  [duck1]="https://upload.wikimedia.org/wikipedia/commons/a/a8/Mudchute_duck_1.ogg"
  [duck2]="https://upload.wikimedia.org/wikipedia/commons/f/f3/Mudchute_duck_2.ogg"
  [rooster]="https://upload.wikimedia.org/wikipedia/commons/1/17/Rooster_crowing.oga"
  [horse]="https://upload.wikimedia.org/wikipedia/commons/d/db/Wiehern.ogg"
)

echo "Pitch factor=${PITCH_FACTOR}, atempo=${ATEMPO}, dur=${DUR}s"

# ===== 下载 + 处理 =====
for key in "${!URLS[@]}"; do
  url="${URLS[$key]}"
  raw="${RAW_DIR}/${key}.ogg"

  echo "==> Download: ${key}"
  # macOS / Linux 通用：curl
  curl -L --retry 3 --retry-delay 1 -o "$raw" "$url"

  echo "==> Process cartoon: ${key}"
  # 处理链路说明：
  # 1) atrim 裁到 DUR
  # 2) aformat 统一采样率/声道
  # 3) asetrate+aresample+atempo => 升调不变速（卡通萌感）
  # 4) 轻微高通/低通避免轰鸣和刺耳
  # 5) 轻压缩 + 限幅，避免突然吓到小朋友
  FILTER="\
atrim=0:${DUR},\
aformat=channel_layouts=mono:sample_rates=44100,\
asetrate=44100*${PITCH_FACTOR},aresample=44100,atempo=${ATEMPO},\
highpass=f=80,lowpass=f=8000,\
acompressor=threshold=-18dB:ratio=3:attack=5:release=60,\
alimiter=limit=0.90\
"

  # 输出 WAV（游戏开发更友好）
  ffmpeg -y -i "$raw" -af "$FILTER" -ac 1 -ar 44100 "${WAV_DIR}/${key}_cartoon.wav" >/dev/null 2>&1

  # 同时输出 MP3（你做预览/小包体也方便）
  ffmpeg -y -i "${WAV_DIR}/${key}_cartoon.wav" -codec:a libmp3lame -b:a 128k "${MP3_DIR}/${key}_cartoon.mp3" >/dev/null 2>&1

done

echo "✅ Done! Output in: ${OUT_DIR}"
echo "   - WAV: ${WAV_DIR}"
echo "   - MP3: ${MP3_DIR}"
