#!/bin/bash

dbg_file="/tmp/tk-switch.log"

TMUX_SCRIPTS="$HOME/.config/kitty/scripts"

export PATH=$TMUX_SCRIPTS:$PATH

dbg() {
  # return 0

  echo "$*" >>"$dbg_file"

  return 0
}

dbg "PATH=$PATH"

# for tmux when in tmux window
is_for_tmux() {
  if [[ -n "$for_tmux" ]]; then
    # echo "Specify tmux case"
    return 0
  fi

  local tmux_pattern="tmux"

  dbg "WinID: $KITTY_WINDOW_ID"
  local result=$(kitten @ ls -m id:$KITTY_WINDOW_ID | jq ".[] | .tabs[] | .windows[] | .foreground_processes[] | .cmdline[0]")
  if [[ "$?" -ne 0 ]]; then
    dbg "jq has error. result: $result"
    return 1
  fi

  dbg "ForeProcesses: $result"

  if echo "$result" | grep -qw "$tmux_pattern"; then
    dbg "Will be tmux"
    return 0
  fi

  return 1
}

kitty_cur_tab_wins() {
  kitten @ ls --match-tab window_id:$KITTY_WINDOW_ID | jq '.[] | .tabs[] | .windows | length'
}

kitty_run_action() {
  kitty @ kitten run_action.py "$@"
}

kitty_last_win() {
  local win_cnt=$(kitty_cur_tab_wins)
  dbg "WinCnt: $win_cnt"
  if [[ $win_cnt -le 1 ]]; then
    dbg "create new window"
    kitty_run_action "launch --cwd=current"
  else
    # to previous window
    kitty_run_action "nth_window -1"
  fi
}

tmux_is_zoomed() {
  tmux list-panes -F '#F' | grep -q 'Z'
}

tmux_last_win() {
  local do_zoom
  if tmux_is_zoomed; then
    do_zoom="1"
  fi

  local pane_num=$(tmux display -p '#{window_panes}')
  if [[ $pane_num -le 1 ]]; then
    tmux split-window -c'#{pane_current_path}'
  else
    tmux last-pane
  fi

  if [[ -n "$do_zoom" ]]; then
    tmux_zoom
  fi
}

kitty_last_tab() {
  kitty_run_action "goto_tab" "-1"
}

tmux_last_tab() {
  tmux last-window
}

kitty_pre_win() {
  kitty_run_action "previous_window"
}

kitty_next_win() {
  kitty_run_action "next_window"
}

tmux_pre_win() {
  tmux select-pane -t -
}

tmux_next_win() {
  tmux select-pane -t +
}

kitty_sel_tab() {
  # kitten @ focus-tab -m index:$(($1 - 1))
  kitty_run_action goto_tab "$1"
}

tmux_sel_tab() {
  tmux select-window -t "$1"
}

kitty_zoom() {
  kitty_run_action toggle_layout stack
}

tmux_zoom() {
  tmux resize-pane -Z
}

kitty_yank() {
  echo "cmdline: $*" >>$dbg_file
}

main() {
  local cmd="$1"
  shift 1

  local func="kitty_${cmd}"
  if is_for_tmux; then
    func="tmux_${cmd}"
  fi

  eval "$func $*"
}

main "$@"
