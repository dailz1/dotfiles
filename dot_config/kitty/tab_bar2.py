# pyright: reportMissingImports=false
# flake8:noqa

import datetime
from typing import Any

from kitty.fast_data_types import Screen, add_timer, get_boss
from kitty.tab_bar import (
    DrawData,
    ExtraData,
    TabBarData,
    as_rgb,
)
from kitty.utils import color_as_int

# 全局变量
center: str = ""
timer_id: Any = None
last_time: str = ""

def _redraw_tab_bar(timer_id) -> None:
    """触发所有标签栏重绘"""
    global last_time
    
    # 获取当前时间
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    
    # 如果时间变化，就重绘
    if current_time != last_time:
        last_time = current_time
        for tm in get_boss().all_tab_managers:
            tm.mark_tab_bar_dirty()
    
    return True

class DrawTab:
    """标签栏绘制类"""
    
    # 颜色常量
    BG_COLOR = 0x112D4E
    FG_COLOR = 0xFFFBE9
    
    left_length: int = 0
    center_length: int = 0
    right_length: int = 0

    def __init__(self) -> None:
        self.right_length = len(self.get_datetime())
        # 确保定时器在类初始化时设置
        global timer_id
        if timer_id is None:
            timer_id = add_timer(_redraw_tab_bar, 0.1, True)  # 每0.1秒刷新一次

    def get_datetime(self) -> str:
        """获取当前时间"""
        now = datetime.datetime.now()
        return now.strftime(" %Y/%m/%d %H:%M:%S")

    def draw_left_status(self, screen: Screen, index: int) -> int:
        """绘制左侧状态"""
        screen.cursor.bg = as_rgb(self.BG_COLOR)
        screen.cursor.fg = as_rgb(self.FG_COLOR)
        text = f"👻 [{index}] "
        screen.draw(text)
        screen.cursor.x = len(text)
        self.left_length = len(text)
        return screen.cursor.x

    def draw_center_status(
        self,
        draw_data: DrawData,
        screen: Screen,
        tab: TabBarData,
        before: int,
        max_title_length: int,
        index: int,
        is_last: bool,
        extra_data: ExtraData,
    ) -> int:
        """绘制中心状态"""
        global center
        if index == 1:
            center = tab.title
        else:
            center = center + " ┇ " + tab.title
        self.center_length = len(center)

        draw_spaces = screen.columns - screen.cursor.x - self.center_length
        if draw_spaces < 0:
            screen.draw(" " * draw_spaces)
            
        screen.cursor.bg = as_rgb(self.BG_COLOR)
        screen.cursor.fg = as_rgb(self.FG_COLOR)
        screen.cursor.x = screen.columns // 2 - self.center_length // 2
        screen.draw(center)
        return screen.cursor.x

    def draw_right_status(self, screen: Screen, is_last: bool) -> int:
        """绘制右侧状态"""
        screen.cursor.bg = as_rgb(self.BG_COLOR)
        screen.cursor.fg = as_rgb(self.FG_COLOR)
        end = screen.cursor.x
        if not is_last:
            return end

        draw_spaces = screen.columns - screen.cursor.x - self.right_length
        if draw_spaces > 0:
            screen.draw(" " * draw_spaces)
        screen.draw(self.get_datetime())
        if screen.columns - screen.cursor.x > self.right_length:
            screen.cursor.x = screen.columns - self.right_length
        return end

    def draw_tab(
        self,
        draw_data: DrawData,
        screen: Screen,
        tab: TabBarData,
        before: int,
        max_title_length: int,
        index: int,
        is_last: bool,
        extra_data: ExtraData,
    ) -> int:
        """绘制整个标签"""
        if index == 1:
            global center
            center = ""
            self.draw_left_status(screen, index)

        self.draw_center_status(
            draw_data,
            screen,
            tab,
            before,
            max_title_length,
            index,
            is_last,
            extra_data,
        )

        if screen.cursor.x - (screen.columns - self.left_length - self.right_length - self.center_length) > 0:
            return screen.cursor.x

        self.draw_right_status(screen, is_last)
        return screen.cursor.x


def draw_tab(*args) -> int:
    """入口函数"""
    return DrawTab().draw_tab(*args)