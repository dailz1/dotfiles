# pyright: reportMissingImports=false
from datetime import datetime
import time
import subprocess
from kitty.boss import get_boss
from kitty.fast_data_types import Screen, add_timer, get_options
from kitty.utils import color_as_int
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    Formatter,
    TabBarData,
    as_rgb,
    draw_attributed_string,
    draw_title,
)

# 直接定义颜色值
icon_fg = as_rgb(0x112D4E)  # 深蓝色
icon_bg = as_rgb(0xFFFBE9)  # 米色
date_color = as_rgb(0x222831)  # 深灰色
cpu_color = as_rgb(0x222831)  # 深灰色
net_color = as_rgb(0x222831)  # 深灰色

SEPARATOR_SYMBOL, SOFT_SEPARATOR_SYMBOL = ("", "")
RIGHT_SEPARATOR_SYMBOL = ""

RIGHT_MARGIN = 3
REFRESH_TIME = 1
ICON_LEFT = "👻 dailz-fedora  "
ICON_RIGHT = "🤡 "

WEEKDAYS = {
    0: "周一",
    1: "周二",
    2: "周三",
    3: "周四",
    4: "周五",
    5: "周六",
    6: "周日"
}


# 网络速度统计
last_net_stats = {'rx_bytes': 0, 'tx_bytes': 0, 'time': 0}

def format_bytes(bytes_per_sec):
    if bytes_per_sec < 1024:
        return f"{bytes_per_sec:.1f}B/s"
    elif bytes_per_sec < 1024 * 1024:
        return f"{bytes_per_sec/1024:.1f}K/s"
    else:
        return f"{bytes_per_sec/(1024*1024):.1f}M/s"

def get_net_bytes():
    try:
        # 尝试使用 ip 命令
        result = subprocess.run(['ip', '-s', 'link'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            rx_bytes = 0
            tx_bytes = 0
            for i, line in enumerate(lines):
                if 'RX:' in line and i + 1 < len(lines):
                    rx_line = lines[i + 1].strip()
                    rx_bytes = int(rx_line.split()[0])
                elif 'TX:' in line and i + 1 < len(lines):
                    tx_line = lines[i + 1].strip()
                    tx_bytes = int(tx_line.split()[0])
            return rx_bytes, tx_bytes
        
        # 如果 ip 命令失败，尝试使用 ifconfig
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            rx_bytes = 0
            tx_bytes = 0
            for line in lines:
                if 'RX packets' in line:
                    rx_bytes = int(line.split('bytes')[1].split()[0])
                elif 'TX packets' in line:
                    tx_bytes = int(line.split('bytes')[1].split()[0])
            return rx_bytes, tx_bytes
    except:
        pass
    return 0, 0

def get_net_speed() -> str:
    try:
        current_time = time.time()
        rx_bytes, tx_bytes = get_net_bytes()
        
        if last_net_stats['time'] > 0:
            time_diff = current_time - last_net_stats['time']
            if time_diff > 0.5:  # 确保时间差至少0.5秒
                rx_diff = rx_bytes - last_net_stats['rx_bytes']
                tx_diff = tx_bytes - last_net_stats['tx_bytes']
                
                rx_speed = rx_diff / time_diff
                tx_speed = tx_diff / time_diff
                
                # 更新统计信息
                last_net_stats.update({
                    'rx_bytes': rx_bytes,
                    'tx_bytes': tx_bytes,
                    'time': current_time
                })
                
                return f"↓{format_bytes(rx_speed)} ↑{format_bytes(tx_speed)} "
            else:
                return f"↓{format_bytes(0)} ↑{format_bytes(0)} "
        
        # 第一次运行
        last_net_stats.update({
            'rx_bytes': rx_bytes,
            'tx_bytes': tx_bytes,
            'time': current_time
        })
        return "↓0B/s ↑0B/s "
    except Exception as e:
        print(f"Network speed error: {e}")
        return "↓N/A ↑N/A "
    return "↓N/A ↑N/A "

def _draw_icon(screen: Screen, index: int) -> int:
    if index != 1:
        return 0
    fg, bg = screen.cursor.fg, screen.cursor.bg
    screen.cursor.fg = icon_fg
    screen.cursor.bg = icon_bg
    screen.draw(ICON_LEFT)
    screen.cursor.fg, screen.cursor.bg = fg, bg
    screen.cursor.x = len(ICON_LEFT)
    # screen.cursor.bg = 0
    # screen.cursor.fg = icon_bg
    # screen.draw(SEPARATOR_SYMBOL)
    return screen.cursor.x


def _draw_left_status(
    draw_data: DrawData,
    screen: Screen,
    tab: TabBarData,
    before: int,
    max_title_length: int,
    index: int,
    is_last: bool,
    extra_data: ExtraData,
) -> int:
    if screen.cursor.x >= screen.columns - right_status_length:
        return screen.cursor.x
    screen.cursor.bg = as_rgb(0xff9494) 
    screen.cursor.fg = as_rgb(0x222831)
    tab_bg = screen.cursor.bg
    tab_fg = screen.cursor.fg
    default_bg = as_rgb(int(draw_data.default_bg))
    if extra_data.next_tab:
        next_tab_bg = as_rgb(draw_data.tab_bg(extra_data.next_tab))
        needs_soft_separator = next_tab_bg == tab_bg
    else:
        next_tab_bg = default_bg
        needs_soft_separator = False
    if screen.cursor.x <= len(ICON_LEFT):
        screen.cursor.x = len(ICON_LEFT)
    screen.draw(" ")
    screen.cursor.bg = tab_bg
    draw_title(draw_data, screen, tab, index)
    if not needs_soft_separator:
        screen.draw(" ")
        screen.cursor.fg = tab_bg
        screen.cursor.bg = next_tab_bg
        screen.draw(SEPARATOR_SYMBOL)
    else:
        prev_fg = screen.cursor.fg
        if tab_bg == tab_fg:
            screen.cursor.fg = default_bg
        elif tab_bg != default_bg:
            c1 = draw_data.inactive_bg.contrast(draw_data.default_bg)
            c2 = draw_data.inactive_bg.contrast(draw_data.inactive_fg)
            if c1 < c2:
                screen.cursor.fg = default_bg
        screen.draw(" " + SOFT_SEPARATOR_SYMBOL)
        screen.cursor.fg = prev_fg
    end = screen.cursor.x
    return end


def _draw_right_status(screen: Screen, is_last: bool, cells: list) -> int:
    if not is_last:
        return 0
    draw_attributed_string(Formatter.reset, screen)
    screen.cursor.x = screen.columns - right_status_length
    # screen.cursor.fg = 0
    screen.cursor.bg = 0 
    screen.cursor.fg = as_rgb(0xff9494)
    screen.draw(RIGHT_SEPARATOR_SYMBOL)
    screen.cursor.bg = as_rgb(0xff9494) 
    for color, status in cells:
        screen.cursor.fg = color
        screen.draw(status)
    # screen.cursor.fg = as_rgb(0xff9494)  # 前景色为右侧背景色
    
    screen.cursor.bg = 0
    return screen.cursor.x


def _redraw_tab_bar(_):
    tm = get_boss().active_tab_manager
    if tm is not None:
        tm.mark_tab_bar_dirty()


def get_cpu_usage() -> str:
    try:
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('cpu '):
                    fields = line.split()
                    total = sum(int(x) for x in fields[1:])
                    idle = int(fields[4])
                    usage = 100 - (idle * 100 / total)
                    return f"CPU: {usage:.1f}% "
    except:
        return "CPU: N/A "
    return "CPU: N/A "

timer_id = None
right_status_length = -1

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
    global right_status_length
    if timer_id is None:
        timer_id = add_timer(_redraw_tab_bar, REFRESH_TIME, True)
    date = datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
    weekday = WEEKDAYS[datetime.now().weekday()]
    cells = [
        (date_color, ICON_RIGHT),
        (date_color, weekday+" "),
        # (cpu_color, get_cpu_usage()),
        # (net_color, get_net_speed()),
        (date_color, date)
    ]
    right_status_length = RIGHT_MARGIN
    for cell in cells:
        right_status_length += len(str(cell[1]))

    _draw_icon(screen, index)
    _draw_left_status(
        draw_data,
        screen,
        tab,
        before,
        max_title_length,
        index,
        is_last,
        extra_data,
    )
    _draw_right_status(
        screen,
        is_last,
        cells,
    )
    return screen.cursor.x
