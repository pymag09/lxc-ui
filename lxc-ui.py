#!/usr/bin/env python3

__author__ = 'Bieliaievskyi Sergey'
__credits__ = ["Bieliaievskyi Sergey"]
__license__ = "Apache License"
__version__ = "1.0.0"
__maintainer__ = "Bieliaievskyi Sergey"
__email__ = "magelan09@gmail.com"
__status__ = "Release"


import curses
import curses.panel
import os
import lxc


def init_curses():
    screen_id = curses.initscr()
    curses.cbreak()
    curses.noecho()
    screen_id.keypad(1)
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    return screen_id


def shutdown_curses(scr_id):
    curses.nocbreak()
    curses.echo()
    scr_id.keypad(0)
    curses.curs_set(1)
    curses.endwin()


def radio_list(wind_prop):
    cur_win_id = {'cwi': curses.newwin(wind_prop['lines'] + 2,
                                       wind_prop['width'], wind_prop['y'], wind_prop['x']),
                  'subj': wind_prop['subj']}
    cur_win_id['panel'] = curses.panel.new_panel(cur_win_id['cwi'])
    cur_win_id['cwi'].bkgd(' ', curses.color_pair(3))
    cur_win_id['cwi'].clear()
    cur_win_id['cwi'].box()
    curses.curs_set(0)
    cur_win_id['cwi'].keypad(1)
    cur_win_id['radio_list'] = wind_prop['radio_list']
    cur_win_id['lines'] = wind_prop['lines']
    cur_win_id['panel'].top()
    cur_win_id['cur_page'] = 0
    cur_win_id['type'] = 'radio'
    cur_win_id['cursor_position'] = 1
    cur_win_id['max_curs_pos'], cur_win_id['items'] = show_lxc_list(cur_win_id['cwi'],
                                                                    cur_win_id['lines'],
                                                                    cur_win_id['cur_page'],
                                                                    cur_win_id['radio_list'])
    cur_win_id['cwi'].addstr(0, 2, wind_prop['subj'], curses.color_pair(3) & curses.A_BOLD)
    return cur_win_id


def edit_line(wind_prop, default_value=''):
    cur_win_id = {'char_x': 1, 'cn_line': [],
                  'cwi': curses.newwin(3, wind_prop['width'], wind_prop['y'], wind_prop['x'])}
    cur_win_id['panel'] = curses.panel.new_panel(cur_win_id['cwi'])
    cur_win_id['cwi'].bkgd(' ', curses.color_pair(3))
    cur_win_id['cwi'].clear()
    cur_win_id['cwi'].box()
    cur_win_id['cwi'].keypad(1)
    cur_win_id['cwi'].addstr(0, 2, wind_prop['subj'], curses.color_pair(3) & curses.A_BOLD)
    cur_win_id['cwi'].addstr(1, 1, default_value, curses.color_pair(3))
    cur_win_id['char_x'] = len(default_value) + 1
    cur_win_id['cn_line'] = list(default_value)
    curses.curs_set(1)
    cur_win_id['type'] = 'edit'
    cur_win_id['cwi'].move(1, cur_win_id['char_x'])
    cur_win_id['panel'].top()
    return cur_win_id


def buttons(wind_prop):
    cur_win_id = {'cwi': curses.newwin(3, wind_prop['width'], wind_prop['y'], wind_prop['x'])}
    cur_win_id['panel'] = curses.panel.new_panel(cur_win_id['cwi'])
    cur_win_id['cwi'].bkgd(' ', curses.color_pair(3))
    cur_win_id['cwi'].clear()
    cur_win_id['cwi'].box()
    cur_win_id['cwi'].keypad(1)
    cur_win_id['cwi'].addstr(1,
                             int((wind_prop['width'] / 2) - (len(wind_prop['txt']) / 2)),
                             wind_prop['txt'],
                             curses.color_pair(3) & curses.A_BOLD)
    curses.curs_set(1)
    cur_win_id['type'] = 'button'
    cur_win_id['cwi'].move(1, 3)
    cur_win_id['panel'].top()
    cur_win_id['char_x'] = int(wind_prop['width'] / 2)
    cur_win_id['return'] = wind_prop['return']
    return cur_win_id


def lxc_dialog_panel(win_array):
    offset = 0
    cur_win_id = win_array[offset]
    for radio in win_array:
        if radio['type'] == 'radio':
            radio['max_curs_pos'], radio['items'] = show_lxc_list(radio['cwi'],
                                                                  radio['lines'],
                                                                  0,
                                                                  radio['radio_list'])
    while True:
        if cur_win_id['type'] == 'radio':
            cur_win_id['cwi'].addstr(0, 2, cur_win_id['subj'], curses.color_pair(3) & curses.A_BOLD)
            cur_win_id['cwi'].addstr(cur_win_id['cursor_position'], 2, '*')
            cur_win_id['cwi'].move(cur_win_id['cursor_position'], 2)
        if cur_win_id['type'] == 'button' or cur_win_id['type'] == 'edit':
            cur_win_id['cwi'].move(1, cur_win_id['char_x'])
        char = cur_win_id['cwi'].getch()
        if char == 338 and cur_win_id['type'] == 'radio':
            cur_win_id['cursor_position'] = cur_win_id['max_curs_pos']
            cur_win_id['cursor_position'], cur_win_id['cur_page'] = move_cursor_down(cur_win_id['cur_page'],
                                                                                     cur_win_id['max_curs_pos'],
                                                                                     cur_win_id['cursor_position'],
                                                                                     cur_win_id['cwi'])
            cur_win_id['max_curs_pos'], cur_win_id['items'] = show_lxc_list(cur_win_id['cwi'],
                                                                            cur_win_id['lines'],
                                                                            cur_win_id['cur_page'],
                                                                            cur_win_id['radio_list'])
        if char == 339 and cur_win_id['type'] == 'radio':
            cur_win_id['cursor_position'] = 1
            cur_win_id['cursor_position'], cur_win_id['cur_page'] = move_cursor_up(cur_win_id['cur_page'],
                                                                                   cur_win_id['cursor_position'],
                                                                                   cur_win_id['cwi'])
            cur_win_id['max_curs_pos'], cur_win_id['items'] = show_lxc_list(cur_win_id['cwi'],
                                                                            cur_win_id['lines'],
                                                                            cur_win_id['cur_page'],
                                                                            cur_win_id['radio_list'])
        if char == 258 and cur_win_id['type'] == 'radio':
            cur_win_id['cwi'].addstr(cur_win_id['cursor_position'], 2, ' ')
            temp_cursor_pos = cur_win_id['cursor_position']
            cur_win_id['cursor_position'], cur_win_id['cur_page'] = move_cursor_down(cur_win_id['cur_page'],
                                                                                     cur_win_id['max_curs_pos'],
                                                                                     cur_win_id['cursor_position'],
                                                                                     cur_win_id['cwi'])
            if temp_cursor_pos != cur_win_id['cursor_position']:
                cur_win_id['max_curs_pos'], cur_win_id['items'] = show_lxc_list(cur_win_id['cwi'],
                                                                                cur_win_id['lines'],
                                                                                cur_win_id['cur_page'],
                                                                                cur_win_id['radio_list'])

            cur_win_id['cwi'].addstr(cur_win_id['cursor_position'], 2, '*')
            cur_win_id['cwi'].refresh()
        if char == 259 and cur_win_id['type'] == 'radio':
            cur_win_id['cwi'].addstr(cur_win_id['cursor_position'], 2, ' ')
            temp_cursor_pos = cur_win_id['cursor_position']
            cur_win_id['cursor_position'], cur_win_id['cur_page'] = move_cursor_up(cur_win_id['cur_page'],
                                                                                   cur_win_id['cursor_position'],
                                                                                   cur_win_id['cwi'])
            if temp_cursor_pos != cur_win_id['cursor_position']:
                cur_win_id['max_curs_pos'], cur_win_id['items'] = show_lxc_list(cur_win_id['cwi'],
                                                                                cur_win_id['lines'],
                                                                                cur_win_id['cur_page'],
                                                                                cur_win_id['radio_list'])
            cur_win_id['cwi'].addstr(cur_win_id['cursor_position'], 2, '*')
            cur_win_id['cwi'].refresh()
        if char == 263 and cur_win_id['type'] == 'edit':
            if len(cur_win_id['cn_line']):
                cur_win_id['cn_line'].pop()
                cur_win_id['char_x'] -= 1
                cur_win_id['cwi'].addstr(1, cur_win_id['char_x'], ' ')
                cur_win_id['cwi'].move(1, cur_win_id['char_x'])
            continue
        if cur_win_id['type'] == 'edit':
            if ((48 <= char <= 57) or (65 <= char <= 90) or (97 <= char <= 122) or
                        char == 45 or char == 95 or char == 44 or
                        char == 46 or char == 64) and len(cur_win_id['cn_line']) < 45:
                cur_win_id['cn_line'].append(chr(char))
                cur_win_id['cwi'].addstr(1, cur_win_id['char_x'], chr(char), curses.color_pair(3))
                cur_win_id['char_x'] += 1
        if char == 9:
            offset = offset + 1 if len(win_array) - 1 > offset else 0
            cur_win_id = win_array[offset]
        if (char == 10 or char == 32) and cur_win_id['type'] == 'button':
            break
    return cur_win_id['return']


def show_lxc_list(win, y_max, page, my_list):
    y, x = win.getmaxyx()
    for pos, fu in enumerate(my_list[page * y_max:(page * y_max) + y_max]):
        win.move(1 + pos if pos < y_max else y_max, 1)
        win.clrtoeol()
        win.addstr(1 + pos if pos < y_max else y_max,
                   1,
                   '[%s]%s' % (fu.state[0], fu.name) if isinstance(fu, lxc.Container) else '[ ]' + fu)
    win.box()
    if len(my_list) > y_max:
        win.addstr(0, x - 7, ' %s%s ' % (str(int(page * 100 / (int(len(my_list) / y_max) or 1))), '%'))
    return len(my_list[page * y_max:(page * y_max) + y_max]), my_list[page * y_max:(page * y_max) + y_max + 1]


def move_cursor_down(cur_page, max_curs_pos, cursor_pos, window):
    lxc_win_size_y, lxc_win_size_x = window.getmaxyx()
    if max_curs_pos >= cursor_pos:
        cursor_pos = cursor_pos + 1 if max_curs_pos >= cursor_pos else max_curs_pos
    if cursor_pos > max_curs_pos:
        if lxc_win_size_y - 2 == max_curs_pos:
            cur_page += 1
            cursor_pos = 1
            window.clear()
        else:
            cursor_pos -= 1
    return cursor_pos, cur_page


def move_cursor_up(cur_page, cursor_pos, window):
    lxc_win_size_y, lxc_win_size_x = window.getmaxyx()
    cursor_pos = cursor_pos - 1 if (cursor_pos and cur_page) or (not cur_page and cursor_pos > 1) else 1
    if cursor_pos == 0 and cur_page > 0:
        cur_page -= 1
        cursor_pos = lxc_win_size_y - 2
        window.clear()
    return cursor_pos, cur_page


def keyboard_shortcuts(scr_id):
    def destroy_conteiner(cd):
        if cd.running:
            cd.stop()
            cd.wait("STOPPED", 3)
        cd.destroy()

    def create_container(name, cached_template):
        if not curses.isendwin():
            curses.endwin()
        cd = lxc.Container(name)
        cached_template = cached_template.split('/')
        lxc_template_data = {}
        if cached_template[0] != 'Default':
            lxc_template_data = {'dist': cached_template[0], 'release': cached_template[1], 'arch': cached_template[2]}
        cd.create('download', 0, lxc_template_data)
        input('Press ENTER to continue')

    def run_console(container):
        if not curses.isendwin():
            curses.endwin()
        container.console(ttynum=1)

    def write_config(lxc_conf_key, value):
        if value:
            list_of_containers[cursor_pos - 1].clear_config_item(lxc_conf_key)
            list_of_containers[cursor_pos - 1].set_config_item(lxc_conf_key, value)
            list_of_containers[cursor_pos - 1].save_config()

    def clear_lxc_win():
        lxc_win.clear()
        lxc_win.redrawwin()
        lxc_win.bkgdset(' ', curses.color_pair(1))
        lxc_win.clrtobot()
        lxc_win.refresh()

    def edit_dialog():
        read_mem_limit = ''.join(list_of_containers[cursor_pos - 1].get_config_item('lxc.cgroup.memory.limit_in_bytes'))
        cpu_bindig = ''.join(list_of_containers[cursor_pos - 1].get_config_item('lxc.cgroup.cpuset.cpus'))
        cpu_shares = ''.join(list_of_containers[cursor_pos - 1].get_config_item('lxc.cgroup.cpu.shares'))
        winds = [edit_line({'x': int(size_x / 2) - 50,
                            'y': 2,
                            'width': 50,
                            'subj': 'Memory limit (M for MBytes,G for GBytes)'}, read_mem_limit),
                 edit_line({'x': int(size_x / 2) - 50,
                            'y': 5,
                            'width': 50,
                            'subj': 'CPU binding. Total %s cores' % os.sysconf('SC_NPROCESSORS_ONLN')}, cpu_bindig),
                 edit_line({'x': int(size_x / 2) - 50,
                            'y': 8,
                            'width': 50,
                            'subj': 'CPU priority'}, cpu_shares),
                 edit_line({'x': int(size_x / 2) - 50,
                            'y': 11,
                            'width': 50,
                            'subj': 'Autostart'}, list_of_containers[cursor_pos - 1].get_config_item('lxc.start.auto')),
                 buttons({'x': int(size_x / 2) - 50, 'y': 14, 'width': 25, 'txt': '[ OK ]', 'return': 1}),
                 buttons({'x': int(size_x / 2) - 25, 'y': 14, 'width': 25, 'txt': '[ Cancel ]', 'return': 0})]
        curses.panel.update_panels()
        scr_id.refresh()
        status = lxc_dialog_panel(winds)
        if status:
            return (''.join(winds[0]['cn_line']),
                    ''.join(winds[1]['cn_line']),
                    ''.join(winds[2]['cn_line']),
                    ''.join(winds[3]['cn_line']))
        else:
            return None

    def ask_string(subj):
        winds = [edit_line({'x': int(size_x / 2) - 50, 'y': 2, 'width': 50, 'subj': subj}),
                 buttons({'x': int(size_x / 2) - 50, 'y': 5, 'width': 25, 'txt': '[ OK ]', 'return': 1}),
                 buttons({'x': int(size_x / 2) - 25, 'y': 5, 'width': 25, 'txt': '[ Cancel ]', 'return': 0})]
        curses.panel.update_panels()
        scr_id.refresh()
        status = lxc_dialog_panel(winds)
        if status:
            return ''.join(winds[0]['cn_line'])
        else:
            return None

    def init_menu_panel():
        #y, x = lxc_win.getbegyx()
        m_any_w = curses.newwin(1, 48, size_y - 1, 0)
        m_any_p = curses.panel.new_panel(m_any_w)
        m_run_w = curses.newwin(1, 46, size_y - 1, 43)
        m_run_p = curses.panel.new_panel(m_run_w)
        m_stop_w = curses.newwin(1, 29, size_y - 1, 43)
        m_stop_p = curses.panel.new_panel(m_stop_w)
        return {'any': (m_any_w, m_any_p), 'run': (m_run_w, m_run_p), 'stop': (m_stop_w, m_stop_p)}

    def menu(menu_win, menu_type):
        offset = 0
        for item in menu_type:
            menu_win.addstr(0, offset, item.split(':')[0], curses.color_pair(2) | curses.A_BOLD)
            menu_win.addstr(0, offset + 2, '%s' % item.split(':')[1], curses.color_pair(3))
            offset = offset + len(item) + 2

    def new_lxc_dialog():
        winds = []
        cache_list = []
        try:
            for top in os.listdir('/var/cache/lxc/download'):
                cache_list.extend(['/'.join(d[0].split('/')[-3:]) for d in os.walk('%s/%s' % ('/var/cache/lxc/download', top))
                     if 'default' in d[1]])
        except FileNotFoundError:
            pass
        winds.append(edit_line({'x': int(size_x / 2) - 50, 'y': 2, 'width': 50, 'subj': 'LXC name'}))
        cache_list.insert(0, 'Default')
        winds.append(radio_list({'x': int(size_x / 2) - 50, 'y': 5,
                                 'width': 50, 'lines': 18,
                                 'subj': 'Choose default or cached', 'radio_list': cache_list}))
        winds.append(buttons({'x': int(size_x / 2) - 50, 'y': 25, 'width': 25, 'txt': '[ OK ]', 'return': 1}))
        winds.append(buttons({'x': int(size_x / 2) - 25, 'y': 25, 'width': 25, 'txt': '[ Cancel ]', 'return': 0}))

        curses.panel.update_panels()
        scr_id.refresh()
        status = lxc_dialog_panel(winds)
        if status:
            return (''.join(winds[0]['cn_line']),
                    winds[1]['items'][int(winds[1]['cursor_position']) - 1])
        else:
            return None

    menu_any = ['C:Create', 'D:Destroy', 'E:Properties', 'Q:Exit']
    menu_run = ['S:Stop', 'F:Freeze', 'U:Unfreeze', 'T:Console']
    menu_stop = ['R:Run', 'L:Clone', 'N:Rename']
    #key = 0
    cursor_pos = 1
    cur_page = 0
    size_y, size_x = scr_id.getmaxyx()
    lxc_win = curses.newwin(size_y - 2, 70, 0, int((size_x / 2) - 40))
    panel = curses.panel.new_panel(lxc_win)
    menu_panels = init_menu_panel()
    menu(menu_panels['any'][0], menu_any)
    menu(menu_panels['run'][0], menu_run)
    menu(menu_panels['stop'][0], menu_stop)
    lxc_win_size_y, lxc_win_size_x = lxc_win.getmaxyx()
    clear_lxc_win()
    max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                     lxc_win_size_y - 2,
                                                     cur_page,
                                                     lxc.list_containers(as_object=True))
    curses.panel.update_panels()
    scr_id.refresh()
    while True:
        lxc_win.addstr(0, 3, ' LXC list ', curses.A_BOLD)
        scr_id.move(size_y - 1, size_x - 20)
        scr_id.clrtoeol()
        if max_curs_pos >= 1:
            lxc_win.chgat(cursor_pos, 1, 68, curses.A_REVERSE)
            if list_of_containers[cursor_pos - 1].state[0] == 'R':
                menu_panels['run'][1].show()
                menu_panels['stop'][1].hide()
            if list_of_containers[cursor_pos - 1].state[0] == 'S':
                menu_panels['run'][1].hide()
                menu_panels['stop'][1].show()
            curses.panel.update_panels()
        else:
            lxc_win.addstr(int(lxc_win_size_y / 2), int((lxc_win_size_x / 2) - 3), 'no LXC')
        lxc_win.refresh()
        key = scr_id.getch()
        if key == 113:
            shutdown_curses(scr_id)
            break
        elif key == 100 and list_of_containers:
            destroy_conteiner(list_of_containers[cursor_pos - 1])
            clear_lxc_win()
            cursor_pos = cursor_pos - 1 if cursor_pos > 1 else 1
            max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                             lxc_win_size_y - 3,
                                                             cur_page,
                                                             lxc.list_containers(as_object=True))
        elif key == 338:
            lxc_win.chgat(cursor_pos, 1, 48, curses.color_pair(1))
            cursor_pos = max_curs_pos
            cursor_pos, cur_page = move_cursor_down(cur_page, max_curs_pos, cursor_pos, lxc_win)
            max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                             lxc_win_size_y - 2,
                                                             cur_page,
                                                             lxc.list_containers(as_object=True))
        elif key == 339:
            lxc_win.chgat(cursor_pos, 1, 48, curses.color_pair(1))
            cursor_pos = 1
            cursor_pos, cur_page = move_cursor_up(cur_page, cursor_pos, lxc_win)
            max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                             lxc_win_size_y - 2,
                                                             cur_page,
                                                             lxc.list_containers(as_object=True))
        elif key == 258:
            lxc_win.chgat(cursor_pos, 1, 48, curses.color_pair(1))
            temp_cursor_pos = cursor_pos
            cursor_pos, cur_page = move_cursor_down(cur_page, max_curs_pos, cursor_pos, lxc_win)
            if temp_cursor_pos != cursor_pos:
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 2,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
        elif key == 259:
            lxc_win.chgat(cursor_pos, 1, 48, curses.color_pair(1))
            temp_cursor_pos = cursor_pos
            cursor_pos, cur_page = move_cursor_up(cur_page, cursor_pos, lxc_win)
            if temp_cursor_pos != cursor_pos:
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 2,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
        elif key == 99:
            nlxcdata = new_lxc_dialog()
            if nlxcdata:
                create_container(*nlxcdata)
                clear_lxc_win()
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
            curses.panel.update_panels()
        elif key == 114:
            list_of_containers[cursor_pos - 1].start()
            lxc_win.addstr(cursor_pos, int(lxc_win_size_x / 2) - 3, 'WAIT',
                           curses.color_pair(1) | curses.A_BLINK | curses.A_REVERSE)
            lxc_win.refresh()
            list_of_containers[cursor_pos - 1].wait("RUNNING", 3)
            max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                             lxc_win_size_y - 3,
                                                             cur_page,
                                                             lxc.list_containers(as_object=True))
        elif key == 115:
            if list_of_containers[cursor_pos - 1].running:
                list_of_containers[cursor_pos - 1].stop()
                lxc_win.addstr(cursor_pos, int(lxc_win_size_x / 2) - 3, 'WAIT',
                               curses.color_pair(1) | curses.A_BLINK | curses.A_REVERSE)
                lxc_win.refresh()
                list_of_containers[cursor_pos - 1].wait("STOPPED", 3)
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
        elif key == 108:
            clone_name = ask_string(' Clone name ')
            if clone_name:
                clone = list_of_containers[cursor_pos - 1].clone(clone_name)
                clear_lxc_win()
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
            curses.panel.update_panels()
        elif key == 101:
            lxc_prop = edit_dialog()
            if lxc_prop:
                write_config('lxc.cgroup.memory.limit_in_bytes', lxc_prop[0])
                write_config('lxc.cgroup.cpuset.cpus', lxc_prop[1])
                write_config('lxc.cgroup.cpu.shares', lxc_prop[2])
                write_config('lxc.start.auto', lxc_prop[3])
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
            curses.panel.update_panels()
        elif key == 110:
            new_name = ask_string(' Rename ')
            if new_name:
                rename = list_of_containers[cursor_pos - 1].rename(new_name)
                clear_lxc_win()
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
            curses.panel.update_panels()
        elif key == 116:
            run_console(list_of_containers[cursor_pos - 1])
        elif key == 102:
            if list_of_containers[cursor_pos - 1].running:
                list_of_containers[cursor_pos - 1].freeze()
                lxc_win.addstr(cursor_pos, int(lxc_win_size_x / 2) - 3, 'WAIT',
                               curses.color_pair(1) | curses.A_BLINK | curses.A_REVERSE)
                lxc_win.refresh()
                list_of_containers[cursor_pos - 1].wait("FROZEN", 3)
                clear_lxc_win()
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))
        elif key == 117:
            if list_of_containers[cursor_pos - 1].running:
                list_of_containers[cursor_pos - 1].unfreeze()
                lxc_win.addstr(cursor_pos, int(lxc_win_size_x / 2) - 3, 'WAIT',
                               curses.color_pair(1) | curses.A_BLINK | curses.A_REVERSE)
                lxc_win.refresh()
                list_of_containers[cursor_pos - 1].wait("FROZEN", 3)
                clear_lxc_win()
                max_curs_pos, list_of_containers = show_lxc_list(lxc_win,
                                                                 lxc_win_size_y - 3,
                                                                 cur_page,
                                                                 lxc.list_containers(as_object=True))


def main():
    main_scr = init_curses()
    keyboard_shortcuts(main_scr)


if __name__ == '__main__':
    main()