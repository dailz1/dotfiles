from kittens.tui.handler import Handler
from kitty.boss import get_boss

class PrefixHandler(Handler):
    def initialize(self):
        self.set_status("前缀模式: 按 h/j/k/l 方向键切换窗口，ESC 退出")

    def on_key(self, key_event):
        key = key_event.key
        boss = get_boss()
        if key == 'h':
            boss.active_window_manager.dispatch_action('neighboring_window left')
            self.quit()
        elif key == 'j':
            boss.active_window_manager.dispatch_action('neighboring_window down')
            self.quit()
        elif key == 'k':
            boss.active_window_manager.dispatch_action('neighboring_window up')
            self.quit()
        elif key == 'l':
            boss.active_window_manager.dispatch_action('neighboring_window right')
            self.quit()
        elif key == 'escape':
            self.quit()
        else:
            self.set_status("无效按键，按 h/j/k/l 或 ESC 退出")

def main(args):
    return PrefixHandler