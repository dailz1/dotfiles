import sys
import time
import datetime
import json
import subprocess
# import psutil
from collections import defaultdict

from kitty.boss import get_boss
from kitty.fast_data_types import Screen, add_timer
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Formatter,
    TabBarData,
    as_rgb,
    draw_attributed_string,
    draw_tab_with_powerline,
)

timer_id = None

# 用于存储网络流量统计
last_rx_bytes = 0
last_tx_bytes = 0
last_time = 0

def draw_tab(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    global timer_id

    if timer_id is None:
        timer_id = add_timer(_redraw_tab_bar, 3, True)
    draw_tab_with_powerline(
        draw_data, screen, tab, before, max_title_length, index, is_last, extra_data
    )
    if is_last:
        draw_right_status(draw_data, screen)
    return screen.cursor.x


def draw_right_status(draw_data: DrawData, screen: Screen) -> None:
    # The tabs may have left some formats enabled. Disable them now.
    draw_attributed_string(Formatter.reset, screen)
    cells = create_cells()
    # Drop cells that wont fit
    while True:
        if not cells:
            return
        padding = screen.columns - screen.cursor.x - \
            sum(len(c) + 3 for c in cells)
        if padding >= 0:
            break
        cells = cells[1:]

    if padding:
        screen.draw(" " * padding)

    # 定义不同的背景颜色
    right_bg = as_rgb(0xff9494) 
    separator_color = as_rgb(0xffffff)  # 白色分隔符
    tab_bg = as_rgb(int(draw_data.inactive_bg))
    tab_fg = as_rgb(int(draw_data.inactive_fg))
    default_bg = as_rgb(int(draw_data.default_bg))
# 🤡
    for i, cell in enumerate(cells):
        cell_bg = right_bg

        # Draw the separator
        # if cell == cells[0]:
        #     screen.cursor.fg = cell_bg
        #     screen.draw("")
        # else:
        #     screen.cursor.fg = separator_color
        #     screen.cursor.bg = cell_bg
        #     screen.draw("")
        # screen.cursor.fg = tab_fg
        # screen.cursor.bg = cell_bg
        screen.draw(f" {cell}")


def format_speed(speed):
    if speed < 1024:
        return f"{speed:.1f}B/s"
    elif speed < 1024 * 1024:
        return f"{speed/1024:.1f}KB/s"
    else:
        return f"{speed/(1024*1024):.1f}MB/s"


def get_network_speed():
    global last_rx_bytes, last_tx_bytes, last_time
    try:
        # 读取网络接口的流量统计
        with open('/proc/net/dev', 'r') as f:
            data = f.read()
        
        # 获取所有接口的总接收和发送字节数
        total_rx_bytes = 0
        total_tx_bytes = 0
        for line in data.split('\n')[2:]:  # 跳过前两行
            if line.strip():
                parts = line.split()
                if len(parts) >= 10:
                    total_rx_bytes += int(parts[1])  # 接收字节数
                    total_tx_bytes += int(parts[9])  # 发送字节数
        
        current_time = time.time()
        
        # 计算速度
        if last_time > 0:
            time_diff = current_time - last_time
            rx_diff = total_rx_bytes - last_rx_bytes
            tx_diff = total_tx_bytes - last_tx_bytes
            rx_speed = rx_diff / time_diff  # 下载速度
            tx_speed = tx_diff / time_diff  # 上传速度
            
            rx_str = format_speed(rx_speed)
            tx_str = format_speed(tx_speed)
        else:
            rx_str = "0B/s"
            tx_str = "0B/s"
        
        last_rx_bytes = total_rx_bytes
        last_tx_bytes = total_tx_bytes
        last_time = current_time
        
        return f"↓{rx_str} ↑{tx_str}"
    except Exception:
        return "NET: N/A"


def get_cpu_usage():
    try:
        cmd = "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'"
        cpu_percent = float(subprocess.getoutput(cmd))
        return f"CPU: {cpu_percent:.1f}%"
    except Exception:
        return "CPU: N/A"


def create_cells() -> list[str]:
    now = datetime.datetime.now()
    return [
        get_cpu_usage(),
        get_network_speed(),
        now.strftime("%Y:%m:%d:%H:%M:%S"),
    ]

# def get_cpu_usage():
#     try:
#         cpu_percent = psutil.cpu_percent(interval=1)
#         return f"CPU: {cpu_percent}%"
#     except Exception:
#         return "CPU: N/A"
    
def get_headphone_battery_status():
    try:
        battery_pct = int(subprocess.getoutput("headsetcontrol -b -c"))
    except Exception:
        status = ""
    else:
        if battery_pct < 0:
            status = ""
        else:
            status = f"{battery_pct}% {''[battery_pct // 10]}"
    return f" {status}"


STATE = defaultdict(lambda: "", {"Paused": "", "Playing": ""})


def currently_playing():
    # TODO: Work out how to add python libraries so that I can query dbus directly
    # For now, implemented in a separate python project: dbus-player-status
    status = " "
    data = {}
    try:
        data = json.loads(subprocess.getoutput("dbus-player-status"))
    except ValueError:
        pass
    if data:
        if "state" in data:
            status = f"{status} {STATE[data['state']]}"
        if "title" in data:
            status = f"{status} {data['title']}"
        if "artist" in data:
            status = f"{status} - {data['artist']}"
    else:
        status = ""
    return status


def _redraw_tab_bar(timer_id):
    for tm in get_boss().all_tab_managers:
        tm.mark_tab_bar_dirty()
