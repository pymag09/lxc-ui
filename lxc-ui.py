#!/usr/bin/env python3

__author__ = 'Bieliaievskyi Sergey'
__credits__ = ["Bieliaievskyi Sergey"]
__license__ = "Apache License"
__version__ = "2.0.0"
__maintainer__ = "Bieliaievskyi Sergey"
__email__ = "magelan09@gmail.com"
__status__ = "Release Candidate"


import curses
import curses.panel
import os
import lxc
import _lxc
import multiprocessing as mp
import configparser
from io import StringIO

class BugContainer(lxc.Container):
    def __init__(self, name, config_path=None):
        super(BugContainer, self).__init__(name, config_path)
        self.my_config = ''
        self.rootfs_size = '...'
        self.rootfs_q = mp.Queue()
        self.p = None

    def fork_size_calc(self, win_d=None, position=None):
        self.p = mp.Process(target=self._get_size, args=(self.config_file_name, self.rootfs_q, win_d, position))
        self.p.start()
        self.p.join()

    def _get_size(self, path, val_q, w_d, size_pos):
        def calc_suffix():
            nonlocal r
            r = 0
            r = int(len(str(total_size))) // 3
            tsize = total_size / 1024 ** r
            if tsize < 1:
                tsize *= 1024
                r -= 1
            return tsize

        total_size = 0
        r = 0
        if w_d:
            y, x = w_d.getyx()
        start_path = path.replace('config', 'rootfs')

        join = os.path.join
        getsize = os.path.getsize
        isfile = os.path.isfile
        islink = os.path.islink

        for tree in os.walk(start_path):
            for f in tree[2]:
                fp = join(tree[0], f)
                if isfile(fp) and not islink(fp):
                    total_size += getsize(fp)
                    if w_d and size_pos:
                        w_d.addstr(size_pos, 5, '%.1f%-4s' % (float(calc_suffix()), ['B', 'K', 'M', 'G', 'T'][r]), curses.A_REVERSE)
                        w_d.move(y, x)
                        w_d.refresh()
        total_size = calc_suffix()
        val_q.put('%.1f%s' % (float(total_size), ['B', 'K', 'M', 'G', 'T'][r]))

    def get_rootfs_size(self):
        if not self.rootfs_q.empty():
            self.rootfs_size = self.rootfs_q.get()
        return self.rootfs_size

    def stop(self):
        super(BugContainer, self).stop()
        #self.rootfs_size = self._get_size()
        self.fork_size_calc()


class Interface:
    def __init__(self, y, x, w, h, title_color, regular_text_color, title=''):
        curses.init_pair(80, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.panel_id = None
        self.win_id = None
        self.title = title
        self.title_color = title_color
        self.local_func = None
        self.value = None
        self.master = False
        self.regular_text_color = regular_text_color
        self.win_id = curses.newwin(self.h, self.w, self.y, self.x)
        self.shadow = curses.newwin(self.h, self.w, self.y + 1, self.x + 1)
        self.shadow.bkgd(' ', curses.color_pair(80))
        self.shadow.refresh()
        self.panel_id = curses.panel.new_panel(self.win_id)
        self.win_id.bkgd(' ', self.regular_text_color)
        self.win_id.clear()
        self.win_id.box()
        self.win_id.keypad(1)
        self.win_id.immedok(True)
        self.print_title()

    def call(self):
        self.local_func(*self.args)

    def print_title(self):
        self.win_id.addstr(0, 2, '%s' % self.title, self.title_color | curses.A_BOLD)

    def action(self, common_key):
        if common_key == 9:
            return False


class EditBar(Interface):
    def __init__(self, x, y, w, h, title_color, regular_text_color, title='',
                 default_value='', numeric=True):
        super(EditBar, self).__init__(x, y, w, h, title_color, regular_text_color, title)
        self.value = list(default_value)
        self.numeric = numeric
        self.cursor_position_x = len(self.value) + 1
        self.win_id.move(1, self.cursor_position_x)
        self.win_id.addstr(1, 1, default_value, regular_text_color)

    @staticmethod
    def focus():
        curses.curs_set(1)

    def update(self):
        self.cursor_position_x = len(self.value) + 1
        self.win_id.addstr(1, 1, ' ' * (self.w - 2))
        self.win_id.addstr(1, 1, ''.join(self.value), self.regular_text_color)

    def action(self, special_key):
        self.focus()
        if special_key == 263:
            if self.cursor_position_x > 1:
                self.value.pop(self.cursor_position_x - 2)
                self.cursor_position_x = self.cursor_position_x - 1 if self.cursor_position_x > 1 else 0
                self.win_id.addstr(1, self.cursor_position_x, '%s  ' % ''.join(self.value[self.cursor_position_x - 1:]))

        if special_key == 260:
            self.cursor_position_x = self.cursor_position_x - 1 if self.cursor_position_x > 1 else 1

        if special_key == 261:
            self.cursor_position_x = self.cursor_position_x + 1 if len(self.value) > self.cursor_position_x - 1 else \
                self.cursor_position_x

        if special_key == 262:
            self.cursor_position_x = 1

        if special_key == 360:
            self.cursor_position_x = len(self.value) + 1

        if (len(self.value) < self.w - 3 and ((48 <= special_key <= 57) or
                                              (65 <= special_key <= 90) or
                                              (97 <= special_key <= 122) or
                                              special_key in (45, 95, 58, 47, 44, 46, 64, 32))):
            if self.numeric and not chr(special_key).isdigit():
                return
            self.value.insert(self.cursor_position_x - 1, chr(special_key))
            self.cursor_position_x += 1
            self.win_id.addstr(1, self.cursor_position_x - 1, ''.join(self.value[self.cursor_position_x - 2:]))
        self.win_id.move(1, self.cursor_position_x)
        super(EditBar, self).action(special_key)


class List(Interface):
    def __init__(self, x, y, w, h, title_color, regular_text_color, rlist, title=''):
        super(List, self).__init__(x, y, w, h, title_color, regular_text_color, title)
        self.rlist = rlist
        self.y_max = h - 2
        self.page = 0
        self.pages = round(len(self.rlist) / self.y_max) - 1
        self.cursor_pos = 1
        self.value = 0
        self.print_rlist()
        self.win_id.move(1, 1)

    @staticmethod
    def focus():
        curses.curs_set(0)

    def _find_position(self):
        self.page = int(self.value / self.y_max)
        self.cursor_pos = self.value - (self.page * self.y_max) + 1

    def update(self):
        self._find_position()
        self.print_rlist()

    def print_rlist(self, check=''):
        for pos, fu in enumerate(self.rlist[self.page * self.y_max:(self.page * self.y_max) + self.y_max]):
            self.win_id.move(1 + pos if pos < self.y_max else self.y_max, 1)
            self.win_id.clrtobot()
            self.win_id.addstr(1 + pos if pos < self.y_max else self.y_max, 1, '%s%s' % (check, fu))
        self.win_id.box()
        self.print_title()

    def action(self, special_key):
        super(List, self).action(special_key)

        def scroll_progress():
            if len(self.rlist) > self.y_max:
                self.win_id.addstr(0, self.w - 7, ' %-3s%s ' % (
                    round((100 * (self.page * self.y_max + self.cursor_pos) / len(self.rlist))), '%'))

        self.focus()
        if special_key == 262:
            self.value = 0
            self._find_position()
            self.print_rlist()

        if special_key == 360:
            self.value = len(self.rlist) - 1
            self._find_position()
            self.print_rlist()

        if special_key == 338:
            if self.pages > self.page:
                self.value = (self.page + 1) * self.y_max
                self._find_position()
                self.print_rlist()

        if special_key == 339:
            if self.page > 0:
                self.value = (self.page - 1) * self.y_max
                self._find_position()
                self.print_rlist()

        if special_key == 258:
            temp_page = self.page
            if self.value < len(self.rlist) - 1:
                self.value += 1
            self._find_position()
            if temp_page != self.page:
                self.print_rlist()
            scroll_progress()

        if special_key == 259:
            temp_page = self.page
            if self.value > 0:
                self.value -= 1
            self._find_position()
            if temp_page != self.page:
                self.print_rlist()
            scroll_progress()


class MenuList(List):
    def __init__(self, x, y, w, h, title_color, regular_text_color, rlist, title=''):
        super(MenuList, self).__init__(x, y, w, h, title_color, regular_text_color, rlist, title)
        self.print_rlist()

    def print_rlist(self, check=''):
        super(MenuList, self).print_rlist()

    def update(self):
        super(MenuList, self).update()
        self.action(0)
        self.win_id.refresh()

    def action(self, special_key):
        if len(self.rlist):
            self.win_id.chgat(self.cursor_pos, 1, self.w - 2, self.regular_text_color)
            super(MenuList, self).action(special_key)
            self.win_id.chgat(self.cursor_pos, 1, self.w - 2, curses.A_REVERSE)

    @staticmethod
    def focus():
        curses.curs_set(0)


class RadioList(List):
    def __init__(self, x, y, w, h, title_color, regular_text_color, rlist, title='', default_item=1):
        self.choice = default_item
        super(RadioList, self).__init__(x, y, w, h, title_color, regular_text_color, rlist, title)
        self.print_rlist()

    def print_rlist(self, check=''):
        if len(self.rlist) > 0:
            super(RadioList, self).print_rlist('[ ]')
            if self.page * self.y_max <= self.choice <= self.page * self.y_max + self.y_max:
                self.win_id.addstr(self.choice - self.page * self.y_max, 2, '*', self.regular_text_color)
                self.win_id.move(self.cursor_pos, 2)

    def update(self):
        super(RadioList, self).update()
        self._redraw(self.value)
        self.win_id.refresh()

    def _redraw(self, val):
        if self.page == int(self.choice / self.y_max):
            self.win_id.addstr(self.choice - (self.page * self.y_max), 2, ' ', self.regular_text_color)
        self.choice = val + 1
        self.win_id.addstr(self.cursor_pos, 2, '*', self.regular_text_color)
        self.win_id.move(self.cursor_pos, 2)

    def action(self, special_key):
        super(RadioList, self).action(special_key)
        self.win_id.move(self.cursor_pos, 2)

        if special_key == 32:
            self._redraw(self.value)
            if self.master:
                return self.rlist[self.value]
        return None

    @staticmethod
    def focus():
        curses.curs_set(1)


class Button(Interface):
    def __init__(self, x, y, w, h, title_color, regular_text_color, title, value):
        super(Button, self).__init__(x, y, w, h, title_color, regular_text_color)
        self.title = title
        self.checked = 0
        self.win_id.addstr(1, int((self.w / 2) - (len(title) / 2)), '[%s]' % self.title, regular_text_color)

    def action(self, special_key):
        super(Button, self).action(special_key)
        if special_key == 10 or special_key == 32:
            self.checked = 1

    @staticmethod
    def focus():
        curses.curs_set(1)


class StatusBar(Interface):
    def __init__(self, x, y, w, h, title_color, regular_text_color, text):
        super(StatusBar, self).__init__(x, y, w, h, title_color, regular_text_color)
        self.text = text
        self.lines = []
        self.get_lines()
        for n, l in enumerate(self.lines):
            self.win_id.addstr(1 + n, 1, l, regular_text_color)

    def get_lines(self):
        splited_str = self.text.split(' ')
        tmp = []
        while splited_str:
            if len(self.text) <= self.w - 2:
                self.lines.append(self.text)
                break
            if len(' '.join(tmp)) + len(splited_str[0]) > self.w - 2:
                self.lines.append(' '.join(tmp))
                tmp.clear()
            tmp.append(splited_str.pop(0))
        self.lines.append(' '.join(tmp))


class Dialog:
    def __init__(self, *elist):
        self.elist = elist
        self.cur_elmt = 0
        self.key_map = None
        self.elist[self.cur_elmt].win_id.refresh()
        self.elist[self.cur_elmt].focus()

    def keyboard(self):
        get_key = 0
        while True:
            if get_key == 27 or \
                    (type(self.elist[self.cur_elmt]) is Button and self.elist[self.cur_elmt].checked == 1):
                break
            get_key = self.elist[self.cur_elmt].win_id.getch()

            if self.key_map and get_key in self.key_map:
                self.key_map[get_key]()

            if get_key == 10 and type(self.elist[self.cur_elmt]) is not Button:
                for button in list(filter((lambda o: type(o) is Button), self.elist)):
                    button.checked = 1
                break
            if get_key == 9:
                self.cur_elmt = self.cur_elmt + 1 if len(self.elist) - 1 > self.cur_elmt else 0
                self.elist[self.cur_elmt].win_id.refresh()
            ret = self.elist[self.cur_elmt].action(get_key)
            if ret:
                for obj in self.elist:
                    obj.args = [obj, ret]
                    if obj.local_func:
                        obj.call()
                self.elist[self.cur_elmt].win_id.refresh()


def my_list_containers(active=True, defined=True, as_object=False, config_path=None):
    """
    List the containers on the system.
    This function from original lxc library. It is rewrited to work with new class
    """
    if config_path:
        if not os.path.exists(config_path):
            return tuple()
        try:
            entries = _lxc.list_containers(active=active, defined=defined, config_path=config_path)
        except ValueError:
            return tuple()
    else:
        try:
            entries = _lxc.list_containers(active=active, defined=defined)
        except ValueError:
            return tuple()
    if as_object:
        return tuple([BugContainer(name, config_path) for name in entries])
    else:
        return entries


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


def get_release_info(path):
    def add_section(fp):
        content = "[DEFAULT]\n%s" % fp.read()
        return StringIO(content)

    def read_releasefile(filename):
        config = configparser.RawConfigParser(allow_no_value=True)
        config.read_file(add_section(open(filename)))
        return config

    pars = read_releasefile('%s%s' % (path,
                                      [rfile for rfile in next(os.walk(path))[2] if 'release' in rfile][0]))
    for n1, n2 in ['DISTRIB_DESCRIPTION', 'DISTRIB_CODENAME'], ['NAME', 'VERSION']:
        try:
            rel = '%s %s' % (pars['DEFAULT'][n1], pars['DEFAULT'][n2])
            break
        except KeyError:
            continue
    else:
        rel, v = pars.items('DEFAULT')[0]
    return rel.replace('"', '')


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
        tty_amount = container.get_config_item('lxc.tty')
        for tty_x in range(1, int(tty_amount) + 1):
            if container.console(ttynum=tty_x):
                break

    def write_config(lxc_conf_key, value):
        lxc_storage[lxc_win.value].clear_config_item(lxc_conf_key)
        res = lxc_storage[lxc_win.value].set_config_item(lxc_conf_key, value)
        if res != 'B':
            lxc_storage[lxc_win.value].save_config()

    def edit_dialog():
        read_mem_limit = ''.join(lxc_storage[lxc_win.value].get_config_item('lxc.cgroup.memory.limit_in_bytes'))
        cpu_bindig = ''.join(lxc_storage[lxc_win.value].get_config_item('lxc.cgroup.cpuset.cpus'))
        cpu_shares = ''.join(lxc_storage[lxc_win.value].get_config_item('lxc.cgroup.cpu.shares'))

        m_limit = EditBar(5, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), "Memory limit (M for MBytes,G for GBytes)", read_mem_limit, False)
        cpu = EditBar(8, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'CPU binding. Total %s cores' % os.sysconf('SC_NPROCESSORS_ONLN'), cpu_bindig, True)
        cpu_pr = EditBar(11, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'CPU priority', cpu_shares, True)
        tty = EditBar(14, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'tty amount', lxc_storage[lxc_win.value].get_config_item('lxc.tty'), True)
        astart = EditBar(17, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'Autostart', lxc_storage[lxc_win.value].get_config_item('lxc.start.auto'), True)
        sdeley = EditBar(20, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'Start delay', lxc_storage[lxc_win.value].get_config_item('lxc.start.delay'), True)
        sorder = EditBar(23, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), 'Start order', lxc_storage[lxc_win.value].get_config_item('lxc.start.order'), True)

        lxc_OK = Button(26, int(size_x / 2) - 50, 25, 3, curses.color_pair(3), curses.color_pair(3), 'OK', 1)
        lxc_Cancel= Button(26, int((size_x / 2) - 50 + 25), 25, 3, curses.color_pair(3),
                           curses.color_pair(3), 'Cancel', 0)
        start_dialog = Dialog(m_limit, cpu, cpu_pr, tty, astart, sdeley, sorder, lxc_OK, lxc_Cancel)
        start_dialog.keyboard()
        if lxc_OK.checked:
            return (''.join(m_limit.value),
                    ''.join(cpu.value),
                    ''.join(cpu_pr.value),
                    ''.join(tty.value),
                    ''.join(astart.value),
                    ''.join(sdeley.value),
                    ''.join(sorder.value))
        else:
            return None

    def ask_string(title):
        clone_name = EditBar(5, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                                 curses.color_pair(3), title, '', False)
        lxc_OK = Button(8, int(size_x / 2) - 50, 25, 3, curses.color_pair(3), curses.color_pair(3), 'OK', 1)
        lxc_Cancel= Button(8, int((size_x / 2) - 50  + 25), 25, 3, curses.color_pair(3),
                           curses.color_pair(3), 'Cancel', 0)
        start_dialog = Dialog(clone_name, lxc_OK, lxc_Cancel)
        start_dialog.keyboard()
        if lxc_OK.checked:
            return ''.join(clone_name.value)
        else:
            return None

    def init_menu_panel():
        m_any_w = curses.newwin(1, 75, size_y - 1, 0)
        m_any_p = curses.panel.new_panel(m_any_w)
        m_run_w = curses.newwin(1, 60, size_y - 1, 75)
        m_run_p = curses.panel.new_panel(m_run_w)
        m_stop_w = curses.newwin(1, 60, size_y - 1, 75)
        m_stop_p = curses.panel.new_panel(m_stop_w)
        return {'any': (m_any_w, m_any_p), 'run': (m_run_w, m_run_p), 'stop': (m_stop_w, m_stop_p)}

    def menu(menu_win, menu_type):
        offset = 0
        for item in menu_type:
            k, descr = item.split(':')
            try:
                menu_win.addstr(0, offset, k, curses.color_pair(2) | curses.A_BOLD)
                menu_win.addstr(0, offset + 2 + len(k), '%s' % descr, curses.color_pair(3))
                offset = offset + len(item) + 2
            except:
                pass

    def scan_cache_folders():
        buf = []
        try:
            for top in os.listdir('/var/cache/lxc/download'):
                buf.extend(['/'.join(d[0].split('/')[-3:])
                            for d in os.walk('%s/%s' % ('/var/cache/lxc/download', top))
                            if 'default' in d[1]])
        except FileNotFoundError:
            pass
        return buf

    def interface_dialog():
        def lxc_add_if():
            lxc_interface = lxc.ContainerNetworkList(lxc_storage[lxc_win.value])
            lxc_interface.add('veth')
            lxc_storage[lxc_win.value].save_config()
            if_index.rlist = [str(net.index) for net in lxc_storage[lxc_win.value].network]
            if_index.update()

        def lxc_del_if():
            lxc_interface = lxc.ContainerNetworkList(lxc_storage[lxc_win.value])
            lxc_interface.remove(if_index.cursor_pos - 1)
            lxc_storage[lxc_win.value].save_config()
            if_index.cursor_pos = if_index.value = 0
            if_index.rlist = [str(net.index) for net in lxc_storage[lxc_win.value].network]
            if_index.update()

        def get_all_interfaces():
            with open('/proc/net/dev') as ifc:
                if_names = ifc.readlines()
            if_list = [ifn.split(':')[0].lstrip() for ifn in if_names[2:] if not 'veth' in ifn.split(':')[0]]
            if_list.remove('lo')
            return if_list

        def find_host_if(this, arg):
            val = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.link' % arg)
            this.value = this.rlist.index(val) if val in this.rlist else 0
            this.update()

        def find_if_type(this, arg):
            val = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.type' % arg)
            this.value = this.rlist.index(val) if val in this.rlist else 0
            this.update()

        def find_if_stat(this, arg):
            val = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.flags' % arg) or 'down'
            this.value = this.rlist.index(val) if val in this.rlist else 0
            this.update()

        def find_if_name(this, arg):
            val = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.name' % arg)
            this.value = list(str(val))
            this.update()

        def find_if_mac(this, arg):
            val = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.hwaddr' % arg)
            this.value = list(str(val))
            this.update()

        def find_if_ip(this, arg):
            this.value = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.ipv4' % arg)
            this.update()

        lxc_if_index = [str(net.index) for net in lxc_storage[lxc_win.value].network]
        all_if = get_all_interfaces()
        if_i = (all_if.index(lxc_storage[lxc_win.value].get_config_item('lxc.network.0.link')) + 1
                if lxc_storage[lxc_win.value].get_config_item('lxc.network.0.link') in all_if else 1)
        type_index = lxc_storage[lxc_win.value].get_config_item('lxc.network.0.type')
        flags_index = lxc_storage[lxc_win.value].get_config_item('lxc.network.0.flags') or 'down'
        if_types_list = ['veth', 'vlan', 'macvlan', 'phys']
        if_flags_list = ['down', 'up']

        if_index = RadioList(5, int(size_x / 2) - 50, 25, 10, curses.color_pair(3),
                                 curses.color_pair(3), lxc_if_index, ' LXC Interface ')
        host_if = RadioList(5, int(size_x / 2) - 25, 25, 10, curses.color_pair(3),
                                 curses.color_pair(3), all_if, ' Host Interfaces ', if_i)
        find_host_if(host_if, 0)
        if_type = RadioList(15, int(size_x / 2) - 50, 25, 10, curses.color_pair(3),
                                 curses.color_pair(3), if_types_list, ' Network type ', if_types_list.index(type_index) + 1)
        find_if_type(if_type, 0)
        if_stat = RadioList(15, int(size_x / 2) - 25, 25, 10, curses.color_pair(3),
                                 curses.color_pair(3), if_flags_list, ' Status ', if_flags_list.index(flags_index) + 1)
        find_if_stat(if_stat, 0)
        lxc_name = EditBar(25, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                           curses.color_pair(3), ' Name ',
                           lxc_storage[lxc_win.value].get_config_item('lxc.network.0.name'), False)
        lxc_mac = EditBar(28, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                           curses.color_pair(3), ' MAC ',
                           lxc_storage[lxc_win.value].get_config_item('lxc.network.0.hwaddr'), False)
        lxc_ip = EditBar(31, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                           curses.color_pair(3), ' IP ',
                           ''.join(lxc_storage[lxc_win.value].get_config_item('lxc.network.0.ipv4')), False)

        lxc_OK = Button(34, int(size_x / 2) - 50, 25, 3, curses.color_pair(3), curses.color_pair(3), 'OK', 1)
        lxc_Cancel= Button(34, int((size_x / 2) - 50  + 25), 25, 3, curses.color_pair(3),
                           curses.color_pair(3), 'Cancel', 0)
        sb = StatusBar(37, int(size_x / 2) - 50, 50, 3,
                       curses.color_pair(3),
                       curses.color_pair(3),
                       '[ DEL/X ]: delete if [ INS/Z ]: add if')

        if_index.master = True
        host_if.local_func = find_host_if
        if_type.local_func = find_if_type
        if_stat.local_func = find_if_stat
        lxc_name.local_func = find_if_name
        lxc_mac.local_func = find_if_mac
        lxc_ip.local_func = find_if_ip
        start_dialog = Dialog(if_index, host_if, if_type, if_stat, lxc_name, lxc_mac, lxc_ip, lxc_OK, lxc_Cancel)
        start_dialog.key_map = {330: lxc_del_if, 97: lxc_add_if, 331: lxc_add_if, 120: lxc_del_if}
        start_dialog.keyboard()
        if lxc_OK.checked:
            return [if_index.rlist[if_index.value],
                    if_type.rlist[if_type.value],
                    host_if.rlist[host_if.value],
                    if_stat.rlist[if_stat.value],
                    ''.join(lxc_name.value),
                    ''.join(lxc_mac.value),
                    ''.join(lxc_ip.value)]
        else:
            return None

    def new_lxc_dialog():
        cache_list = scan_cache_folders()

        cache_list.insert(0, 'Default')
        lxc_name = EditBar(5, int(size_x / 2) - 50, 50, 3, curses.color_pair(3),
                           curses.color_pair(3), ' New LXC ', '', False)
        lxc_template = RadioList(8, int(size_x / 2) - 50, 50, 18, curses.color_pair(3),
                                 curses.color_pair(3), cache_list, ' Cache ')
        lxc_OK = Button(26, int(size_x / 2) - 50, 25, 3, curses.color_pair(3), curses.color_pair(3), 'OK', 1)
        lxc_Cancel= Button(26, int((size_x / 2) - 50  + 25), 25, 3, curses.color_pair(3),
                           curses.color_pair(3), 'Cancel', 0)
        start_dialog = Dialog(lxc_name, lxc_template, lxc_OK, lxc_Cancel)
        start_dialog.keyboard()
        return (''.join(lxc_name.value), lxc_template.rlist[lxc_template.value]) if lxc_OK.checked else None

    def snapshot_dialog():
        def snap_rm():
            snap_name = lxc_snap.rlist[lxc_snap.cursor_pos - 1].split(' ')[0]
            lxc_storage[lxc_win.value].snapshot_destroy(snap_name)
            lxc_snap.cursor_pos = lxc_snap.value = 0
            lxc_snap.rlist = [" ".join([snap[0], snap[2]]) for snap in lxc_storage[lxc_win.value].snapshot_list()]
            lxc_snap.update()

        snap_list = [" ".join([snap[0], snap[2]]) for snap in lxc_storage[lxc_win.value].snapshot_list()]
        lxc_snap = RadioList(5, int(size_x / 2) - 50, 50, 18, curses.color_pair(3),
                                 curses.color_pair(3), snap_list, ' Snapshot list ')
        lxc_OK = Button(23, int(size_x / 2) - 50, 25, 3, curses.color_pair(3), curses.color_pair(3), 'Restore', 1)
        lxc_Cancel= Button(23, int((size_x / 2) - 50  + 25), 25, 3, curses.color_pair(3),
                           curses.color_pair(3), 'Cancel', 0)
        sb = StatusBar(26, int(size_x / 2) - 50, 50, 3,
                       curses.color_pair(3),
                       curses.color_pair(3),
                       'DEL/X: delete snaphot')
        start_dialog = Dialog(lxc_snap, lxc_OK, lxc_Cancel)
        start_dialog.key_map = {330: snap_rm, 120: snap_rm}
        start_dialog.keyboard()
        return lxc_snap.rlist[lxc_snap.cursor_pos - 1].split(' ')[0] if lxc_OK.checked else None

    def show_me_screen():
        nonlocal lxc_win, size_y, size_x, menu_panel, lxc_win_size_y, lxc_win_size_x, menu_panels, panel
        size_y, size_x = scr_id.getmaxyx()
        lxc_win = MenuList(0, 0, size_x, size_y - 2, curses.color_pair(1), curses.color_pair(1), lxc_list, "LXC list")
        menu_panels = init_menu_panel()
        menu(menu_panels['any'][0], menu_any)
        menu(menu_panels['run'][0], menu_run)
        menu(menu_panels['stop'][0], menu_stop)

    def get_all_lxc_list():
        nonlocal lxc_storage, lxc_list
        lxc_storage = my_list_containers(as_object=True)
        return (lxc_storage, ['[%s] %-8s %-50s %s' % ('R' if fu.init_pid > 0 else 'S',
                                            fu.get_rootfs_size(),
                                            fu.name,
                                            get_release_info(str(fu.config_file_name).replace('config', 'rootfs/etc/')))
                              for fu in lxc_storage])

    def stop_it():
        if lxc_storage[lxc_win.value].running:
            if warning('Stop container???', 'Stop It!'):
                lxc_storage[lxc_win.value].stop()
                lxc_storage[lxc_win.value].fork_size_calc()
                sb = StatusBar(5, int(size_x / 2) - 50, 7, 3, curses.color_pair(3),
                           curses.color_pair(3) | curses.A_BLINK, 'WAIT')
                curses.panel.update_panels()
                lxc_storage[lxc_win.value].wait("STOPPED", 3)
                lxc_list[lxc_win.value] = lxc_list[lxc_win.value].replace('[R]', '[S]')
                del sb
                curses.panel.update_panels()

    def warning(warn_txt, b_title):
        warning = StatusBar(5, int(size_x / 2) - 40, 40, 5,
                       curses.color_pair(3),
                       curses.color_pair(3),
                       warn_txt)
        lxc_OK = Button(10, int(size_x / 2) - 40, 20, 3, curses.color_pair(3), curses.color_pair(3), b_title, 1)
        lxc_cancel = Button(10, int(size_x / 2) - 20, 20, 3, curses.color_pair(3), curses.color_pair(3), 'Cancel', 0)
        start_dialog = Dialog(lxc_OK, lxc_cancel)
        start_dialog.keyboard()
        return 1 if lxc_OK.checked else 0

    def attach_console(cmd):
        if not curses.isendwin():
            curses.endwin()
        lxc_storage[lxc_win.value].attach_wait(lxc.attach_run_command, cmd)
        input('Press ENTER to continue')


    menu_any = ['C:Create', 'D:Destroy', 'E:Properties', 'I:Interfaces', 'Space:Disk usage', 'Q:Exit']
    menu_run = ['S:Stop', 'F:Freeze', 'U:Unfreeze', 'T:Console', 'Ctrl+T: Cmd exec']
    menu_stop = ['R:Run', 'L:Clone', 'N:Rename', 'M:Snapshot', 'O:Snapshot menu']
    cursor_pos = 1
    cur_page = 0

    lxc_win, size_y, size_x, menu_panel, lxc_win_size_y, lxc_win_size_x, menu_panels, panel = None, 0, 0, \
                                                                                              None, 0, 0, \
                                                                                              None, None
    lxc_storage, lxc_list = get_all_lxc_list()
    show_me_screen()

    curses.panel.update_panels()
    scr_id.refresh()

    key = 0

    while True:
        if len(lxc_storage) and lxc_storage[lxc_win.value].state == "RUNNING":
            menu_panels['run'][1].show()
            menu_panels['stop'][1].hide()
        if len(lxc_storage) and lxc_storage[lxc_win.value].state == "STOPPED":
            menu_panels['run'][1].hide()
            menu_panels['stop'][1].show()
        curses.panel.update_panels()
        lxc_win.update()
        key = scr_id.getch()

        lxc_win.action(key)

        if key == curses.KEY_RESIZE:
            if curses.is_term_resized(lxc_win_size_y, lxc_win_size_x):
                scr_id.clear()
                scr_id.refresh()
                show_me_screen()
        elif key == 113:
            shutdown_curses(scr_id)
            for lc in lxc_storage:
                if lc.p and lc.p.is_alive():
                    lc.p.terminate()
            break
        elif key == 100 and lxc_storage:
            if warning('Destroy container???', 'Destroy It!'):
                destroy_conteiner(lxc_storage[lxc_win.value])
                lxc_storage, lxc_list = get_all_lxc_list()
                lxc_win.rlist.clear()
                lxc_win.win_id.clear()
                lxc_win.update()
                lxc_win.focus()
                if len(lxc_list) > 0:
                    lxc_win.rlist.extend(lxc_list)
                    lxc_win.action(259)
        elif key == 99:
            nlxcdata = new_lxc_dialog()
            if nlxcdata:
                create_container(*nlxcdata)
                lxc_storage, lxc_list = get_all_lxc_list()
                lxc_win.rlist.clear()
                lxc_win.rlist.extend(lxc_list)
            curses.panel.update_panels()

        elif key == 20:
            cmd = ask_string(' Run command ')
            if cmd:
                attach_console(cmd.split(' '))

        elif key == 111:
            '''o key'''
            sndil = snapshot_dialog()
            if sndil:
                if lxc_storage[lxc_win.value].state == "RUNNING":
                    lxc_win.update()
                    if not warning('Container need to be stopped!', 'Stop It!'):
                        continue
                    lxc_win.update()
                    stop_it()
                lxc_storage[lxc_win.value].snapshot_restore(sndil)
            curses.panel.update_panels()

        elif key == 109:
            '''m key'''
            if not curses.isendwin():
                curses.endwin()
            lxc_storage[lxc_win.value].snapshot()
            input('Press ENTER to continue')

        elif key == 114:
            lxc_storage[lxc_win.value].start()
            lxc_storage[lxc_win.value].fork_size_calc()
            sb = StatusBar(5, int(size_x / 2) - 50, 7, 3, curses.color_pair(3),
                           curses.color_pair(3) | curses.A_BLINK, 'WAIT')
            curses.panel.update_panels()
            lxc_storage[lxc_win.value].wait("RUNNING", 3)
            lxc_list[lxc_win.value] = lxc_list[lxc_win.value].replace('[S]', '[R]')
            del sb
            curses.panel.update_panels()

        elif key == 115:
            stop_it()
        elif key == 105:
            if_prop = interface_dialog()
            if if_prop:
                need_reinit_if = (lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.type' % if_prop[0]) !=
                                  if_prop[2])
                network_prop = ['type', 'link', 'flags', 'name', 'hwaddr', 'ipv4']
                print(lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.type' % if_prop[0]), if_prop[1])
                if need_reinit_if:
                    lxc_storage[lxc_win.value].clear_config_item('lxc.network.%s' % if_prop[0])
                    if_prop[0] = len(lxc_storage[lxc_win.value].network)
                for index, np in enumerate(network_prop, start=1):
                    if not need_reinit_if:
                        get_val_conf = lxc_storage[lxc_win.value].get_config_item('lxc.network.%s.%s' %
                                                                                  (if_prop[0], np))
                        if isinstance(get_val_conf, list):
                            get_val_conf = ''.join(get_val_conf)
                        if get_val_conf == if_prop[index]:
                            continue
                    write_config('lxc.network.%s.%s' % (if_prop[0], np), if_prop[index])
            curses.panel.update_panels()
        elif key == 108:
            clone_name = ask_string(" Clone name ")
            if clone_name:
                clone = lxc_storage[lxc_win.value].clone(clone_name)
                lxc_storage, lxc_list = get_all_lxc_list()
                lxc_win.rlist.clear()
                lxc_win.rlist.extend(lxc_list)
                curses.panel.update_panels()
        elif key == 101:
            lxc_prop = edit_dialog()
            if lxc_prop:
                write_config('lxc.cgroup.memory.limit_in_bytes', lxc_prop[0])
                write_config('lxc.cgroup.cpuset.cpus', lxc_prop[1])
                write_config('lxc.cgroup.cpu.shares', lxc_prop[2])
                write_config('lxc.tty', lxc_prop[3])
                write_config('lxc.start.auto', lxc_prop[4])
                write_config('lxc.start.delay', lxc_prop[5])
                write_config('lxc.start.order', lxc_prop[6])
            curses.panel.update_panels()
        elif key == 110:
            new_name = ask_string(' Rename ')
            if new_name:
                rename = lxc_storage[lxc_win.value].rename(new_name)
                lxc_storage, lxc_list = get_all_lxc_list()
                lxc_win.rlist.clear()
                lxc_win.rlist.extend(lxc_list)
                curses.panel.update_panels()

        elif key == 116:
            run_console(lxc_storage[lxc_win.value])
        elif key == 102:
            if lxc_storage[lxc_win.value].running:
                lxc_storage[lxc_win.value].freeze()
                sb = StatusBar(5, int(size_x / 2) - 50, 7, 3, curses.color_pair(3),
                           curses.color_pair(3) | curses.A_BLINK, 'WAIT')
                curses.panel.update_panels()
                lxc_storage[lxc_win.value].wait("FROZEN", 3)
                lxc_list[lxc_win.value] = lxc_list[lxc_win.value].replace('[R]', '[F]')
                del sb
            curses.panel.update_panels()

        elif key == 32:
            lxc_storage[lxc_win.value].fork_size_calc(lxc_win.win_id, lxc_win.cursor_pos)
            lxc_list = ['[%s] %-8s %-50s %s' % ('R' if fu.init_pid > 0 else 'S',
                                            fu.get_rootfs_size(),
                                            fu.name,
                                            get_release_info(str(fu.config_file_name).replace('config', 'rootfs/etc/')))
                        for fu in lxc_storage]
            lxc_win.rlist.clear()
            lxc_win.rlist.extend(lxc_list)

        elif key == 117:
            if lxc_storage[lxc_win.value].running:
                lxc_storage[lxc_win.value].unfreeze()
                sb = StatusBar(5, int(size_x / 2) - 50, 7, 3, curses.color_pair(3),
                           curses.color_pair(3) | curses.A_BLINK, 'WAIT')
                curses.panel.update_panels()
                lxc_storage[lxc_win.value].wait("FROZEN", 3)
                lxc_list[lxc_win.value] = lxc_list[lxc_win.value].replace('[F]', '[R]')
                del sb
            curses.panel.update_panels()


def main():
    main_scr = init_curses()
    keyboard_shortcuts(main_scr)


if __name__ == '__main__':
    main()
