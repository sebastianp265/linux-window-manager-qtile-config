# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from libqtile import bar, layout, qtile, hook
from qtile_extras import widget
from libqtile.config import Click, Drag, Group, Key, Match, Screen, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger

from qtile_extras.widget.decorations import PowerLineDecoration
import subprocess

mod = "mod4"
terminal = guess_terminal()



def get_keys():
    _keys = [
        # A list of available commands that can be bound to keys can be found
        # at https://docs.qtile.org/en/latest/manual/config/lazy.html
        # Switch between windows
        Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
        Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
        Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
        Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
        Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
        # Move windows between left/right columns or move up/down in current stack.
        # Moving out of range in Columns layout will create new column.
        Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
        Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
        Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
        Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
        # Grow windows. If current window is on the edge of screen and direction
        # will be to screen edge - window would shrink.
        Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
        Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
        Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
        Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
        Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
        # Toggle between split and unsplit sides of stack.
        # Split = all windows displayed
        # Unsplit = 1 window displayed, like Max layout, but still with
        # multiple stack panes
        Key(
            [mod, "shift"],
            "Return",
            lazy.layout.toggle_split(),
            desc="Toggle between split and unsplit sides of stack",
        ),
        Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
        # Toggle between different layouts as defined below
        Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
        Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),
        Key(
            [mod],
            "f",
            lazy.window.toggle_fullscreen(),
            desc="Toggle fullscreen on the focused window",
        ),
        Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating on the focused window"),
        Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
        Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
        Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
        # Custom screenshot keybinding
        Key(["control", "shift"], "print", lazy.spawn("maim -s | xclip -selection clipboard -t image/png", shell=True)),

        # mod + s for terminal
        Key([mod], "s", lazy.group["scratchpad"].dropdown_toggle("terminal")),
        # mod + d for browser
        Key([mod], "d", lazy.group["scratchpad"].dropdown_toggle("browser"))
    ]
    return _keys


keys = get_keys()


def get_number_of_connected_screens():
    try:
        subprocess.run(["xrandr", "--auto"])
        output = subprocess.check_output(["xrandr", "--listmonitors"])
        lines = output.splitlines()[1:]

        lines = filter(lambda x: b"eDP-1" not in x, lines)
        left = "eDP-1"
        i = 1
        for line in lines:
            right = line.decode().split()[-1]
            subprocess.run(["xrandr", "--output", right, "--right-of", left])
            left = right
            i+=1
        return i 
    except subprocess.CalledProcessError:
        return -1


NUMBER_OF_SCREENS = get_number_of_connected_screens()
SCREEN_GROUPS = ["1234", "56789"] if NUMBER_OF_SCREENS > 1 else ["123456789"]


def on_restart():
    autostart_path = "/home/sebastian/.config/autostart.sh"
    subprocess.run(autostart_path)

on_restart()

def get_groups():
    _groups = []
    for i, g in enumerate(SCREEN_GROUPS):
        for g_name in g:
            _groups.append(Group(name=g_name, screen_affinity=i))

    # ScratchPad
    _scratch_pad = ScratchPad("scratchpad", [
        DropDown("terminal", "alacritty",
                 height=0.8, width=0.8, x=0.1, y=0.1, opacity=1.00),
        DropDown("browser", "firefox", match=Match(
            wm_class="firefox"
        ), height=0.8, width=0.8, x=0.1, y=0.1, opacity=1.00),
    ])
    _groups.append(_scratch_pad)
    return _groups


groups = get_groups()


def extend_keys_with_group_switch_bindings(_keys):
    def _go_to_group(name: str):
        def _inner(_qtile):
            global SCREEN_GROUPS
            for screen_id, g in enumerate(SCREEN_GROUPS):
                if name in g:
                    _qtile.focus_screen(screen_id)
                    _qtile.groups_map[name].toscreen()

        return _inner

    for i in groups[:-1]:
        _keys.extend(
            [
                Key(
                    [mod],
                    i.name,
                    lazy.function(_go_to_group(i.name)),
                    desc="Switch to group {}".format(i.name),
                ),
                Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
                    desc="move focused window to group {}".format(i.name)),
            ]
        )
    return _keys


keys = extend_keys_with_group_switch_bindings(keys)

colors = {
    "foreground-primary": "#DCD7BA",
    "foreground-secondary": "#938AA9",
    "background-primary": "#1F1F28",
    "background-secondary": "#2D4F67"
}

layouts = [
    layout.Columns(border_width=4, margin=4, border_focus=colors["background-secondary"],
                   border_normal=colors["background-primary"]),
]

widget_defaults = dict(
    font="JetBrains Mono",
    fontsize=12,
    padding=3,
    foreground=colors["foreground-primary"]
)
extension_defaults = widget_defaults.copy()

powerline = {
    "decorations": [
        PowerLineDecoration(path="arrow_right")
    ],
    "padding": 10
}


def get_screens(main_screen: int):
    def _gen_screen(visible_groups: list[str], is_main):
        widgets_inside_bar = [
            widget.GroupBox(visible_groups=visible_groups,
                            active=colors["foreground-primary"],
                            this_current_screen_border=colors["background-secondary"],
                            ),
            widget.Prompt() if is_main else None,
            widget.WindowName(),
            widget.PulseVolume(background=colors["background-primary"], **powerline, fmt="Vol: {}"),
            widget.Wlan(background=colors["background-secondary"], format='Wi-Fi: {essid} {percent:2.0%}',
                        interface='wlo1',
                        **powerline),
            widget.Battery(
                battery='BAT1',
                discharge_char='↓',
                charge_char='↑',
                empty_char='-',
                full_char='=',
                format='{char} {percent:2.0%} {hour}h{min}min',
                update_delay=2,
                background=colors["background-primary"], **powerline
            ),
            widget.NvidiaSensors(background=colors["background-secondary"], format='GPU {temp} °C', **powerline),
            widget.CPU(background=colors["background-primary"]),
            widget.CPUGraph(graph_color=colors["foreground-primary"],
                            fill_color=colors["foreground-primary"],
                            border_color=colors["background-secondary"],
                            background=colors["background-primary"]),
            widget.ThermalSensor(background=colors["background-primary"], **powerline),
            widget.Memory(background=colors["background-secondary"], **powerline),
            widget.Clock(background=colors["background-primary"], format="%Y-%m-%d %a %H:%M:%S", **powerline),
        ]
        widgets_inside_bar = list(filter(lambda wib: wib is not None, widgets_inside_bar))

        bar_widget = bar.Bar(
            widgets_inside_bar,
            28,
            background=colors["background-primary"]
        )
        return Screen(top=bar_widget)

    global SCREEN_GROUPS
    screens_res = []
    for i, sg in enumerate(SCREEN_GROUPS):
        screens_res.append(_gen_screen([g_n for g_n in sg], i == main_screen))

    return screens_res


screens = get_screens(0 if NUMBER_OF_SCREENS == 1 else 1 )

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    border_width=4,
    border_focus=colors["background-secondary"],
    border_normal=colors["background-primary"],
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(wm_class="zoom"),  # Zoom meetings    
        Match(wm_class="project"),
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = None

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"
