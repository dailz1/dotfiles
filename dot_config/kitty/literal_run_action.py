import kitty.key_encoding as ke
from kitty.options.utils import parse_key_action

def main(args):
  pass

from kittens.tui.handler import result_handler
@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
  _kitten = args[0]
  action_if_tabs = ' '.join(args[1:])

  tm = boss.active_tab_manager
  if tm is None:
    return

  boss.dispatch_action(parse_key_action(action_if_tabs))
  return