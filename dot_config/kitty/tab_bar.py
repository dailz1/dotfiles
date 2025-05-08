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
from kitty.fast_data_types import wcswidth
import os
import socket


# 刷新间隔
REFRESH_TIME = 1

# 图标
ICON_LEFT = " 👻 "
ICON_RIGHT = " 🤡 "

# 颜色
BG = as_rgb(0x112D4E) # 深蓝色
FG = as_rgb(0xF5F0CD) # 米色
ACTIVE_BG = as_rgb(0x00ADB5)    # 浅蓝色
RIGHT_BG = as_rgb(0xff9494) # 粉色

# 分隔符
LEFT_SEPARATOR_SYMBOL = ""
RIGHT_SEPARATOR_SYMBOL = ""

WEEKDAYS = {
    0: "周一",
    1: "周二",
    2: "周三",
    3: "周四",
    4: "周五",
    5: "周六",
    6: "周日"
}

# 获取主机信息
def get_host_info() -> str:
    try:
        username = os.getenv('USER', 'unknown')
        hostname = socket.gethostname()
        return f"{username}:{hostname}"
    except:
        return "unknown:localhost"

# 获取cpu使用率
last_cpu_stats = None
last_cpu_time = 0
last_cpu_usage = 0
def get_cpu_usage_proc() -> str:
    global last_cpu_stats, last_cpu_time, last_cpu_usage
    try:
        with open('/proc/stat') as f:
            line = f.readline()
        fields = [int(x) for x in line.split()[1:]]
        now = time.time()
        if last_cpu_stats is not None and now - last_cpu_time > 0.5:
            total = sum(fields) - sum(last_cpu_stats)
            idle = fields[3] - last_cpu_stats[3]
            usage = 100 - (idle * 100 / total) if total > 0 else 0
            last_cpu_usage = usage
        # 如果采样间隔太短，直接返回上一次 usage
        else:
            usage = last_cpu_usage
        last_cpu_stats = fields
        last_cpu_time = now
        return f"CPU:{usage:.1f}%"
    except Exception as e:
        return "CPU:N/A"

# 获取内存使用率
def get_mem_usage() -> str:
    try:
        result = subprocess.run(
            "free -m | grep Mem",
            shell=True, capture_output=True, text=True
        )
        parts = result.stdout.split()
        total = float(parts[1]) / 1024  # MB 转 GB
        used = float(parts[2]) / 1024   # MB 转 GB
        percent = used / total * 100
        return f"Mem:{percent:.0f}%"
    except Exception as e:
        return "Mem: N/A"

# 获取时间
def get_date() -> str:
    now = datetime.now()
    return f"{WEEKDAYS[now.weekday()]} {now.strftime('%m-%d %H:%M:%S')}"

# 刷新标签栏
def _redraw_tab_bar(_):
    tm = get_boss().active_tab_manager
    if tm is not None:
        tm.mark_tab_bar_dirty()

def _draw_icon(screen: Screen, index: int) -> int:
    if index != 1:
        return 0
    fg, bg = FG, BG
    # 绘制图标
    # 左括号，需要米色前景，深蓝色背景
    screen.cursor.fg = fg
    screen.cursor.bg = bg
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    # 图标，需要米色背景，米色前景
    screen.cursor.bg = fg 
    screen.draw(ICON_LEFT)
    # 右括号，需要米色前景，深蓝色背景
    screen.cursor.bg = bg
    screen.draw(RIGHT_SEPARATOR_SYMBOL)
    
    # 绘制用户名:主机名
    screen.cursor.fg = fg
    screen.cursor.bg = bg 
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    # 需要设置深蓝色前景，米色背景
    screen.cursor.bg = fg
    screen.cursor.fg = bg 
    screen.draw(get_host_info())
    screen.cursor.fg = fg 
    screen.cursor.bg = bg
    screen.draw(RIGHT_SEPARATOR_SYMBOL)
    

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

    fg, bg = FG, BG
    
    # 判断是活动标签还是非活动标签
    if tab.is_active:
        screen.cursor.bg = bg 
        screen.cursor.fg = ACTIVE_BG
        screen.draw(LEFT_SEPARATOR_SYMBOL)

        screen.cursor.fg = bg 
        screen.cursor.bg = ACTIVE_BG
        draw_title(draw_data, screen, tab, index)

        screen.cursor.bg = bg
        screen.cursor.fg = ACTIVE_BG
        screen.draw(RIGHT_SEPARATOR_SYMBOL)
    else:
        screen.cursor.bg = bg
        screen.cursor.fg = fg 
        screen.draw(LEFT_SEPARATOR_SYMBOL)

        screen.cursor.fg = bg 
        screen.cursor.bg = fg
        draw_title(draw_data, screen, tab, index)

        screen.cursor.bg = bg
        screen.cursor.fg = fg 
        screen.draw(RIGHT_SEPARATOR_SYMBOL)
    return screen.cursor.x 


def _draw_right_status(screen: Screen, is_last: bool) -> int:
    if not is_last:
        return 0 
    draw_attributed_string(Formatter.reset, screen)
    
    total_length = (
        wcswidth(ICON_RIGHT) +
        wcswidth(get_cpu_usage_proc()) +
        wcswidth(get_mem_usage()) +
        wcswidth(get_date()) +
        wcswidth(LEFT_SEPARATOR_SYMBOL)*4 + 
        wcswidth(RIGHT_SEPARATOR_SYMBOL) * 4
    )

    available_length = screen.columns - screen.cursor.x

    if available_length < total_length:
        
        short_text = get_date()
        short_width = wcswidth(short_text) + wcswidth(LEFT_SEPARATOR_SYMBOL) * 2 + wcswidth(RIGHT_SEPARATOR_SYMBOL) * 2

        if available_length >= short_width:
            screen.cursor.bg = BG
            screen.cursor.fg = RIGHT_BG
            screen.draw(LEFT_SEPARATOR_SYMBOL)
            screen.cursor.bg = RIGHT_BG
            screen.cursor.fg = BG
            screen.draw(short_text)
            screen.cursor.bg = BG
            screen.cursor.fg = RIGHT_BG
            screen.draw(RIGHT_SEPARATOR_SYMBOL)
        return screen.cursor.x
    
    screen.cursor.x = screen.columns - total_length

    # 绘制图标
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    screen.cursor.bg = RIGHT_BG
    screen.draw(ICON_RIGHT)
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(RIGHT_SEPARATOR_SYMBOL)
    # 绘制cpu信息
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    screen.cursor.fg = BG 
    screen.cursor.bg = RIGHT_BG
    screen.draw(get_cpu_usage_proc())
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(RIGHT_SEPARATOR_SYMBOL)

    # 绘制内存信息
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    screen.cursor.bg = RIGHT_BG
    screen.cursor.fg = BG
    screen.draw(get_mem_usage())
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(RIGHT_SEPARATOR_SYMBOL)

    # 绘制日期时间
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(LEFT_SEPARATOR_SYMBOL)
    screen.cursor.bg = RIGHT_BG
    screen.cursor.fg = BG
    screen.draw(get_date())
    screen.cursor.bg = BG
    screen.cursor.fg = RIGHT_BG
    screen.draw(RIGHT_SEPARATOR_SYMBOL)

    

    return screen.cursor.x 

# 注册窗口变化事件
timer_id = None

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
        timer_id = add_timer(_redraw_tab_bar, REFRESH_TIME, True)

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
    )
    return screen.cursor.x

