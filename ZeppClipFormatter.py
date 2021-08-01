#! pythonw
import os
import threading
import time

import pyperclip
import wx
import wx.adv
from black import FileMode, format_str
from plyer import notification
import isort

APP_NAME = "ZeppClipFormatter"
TRAY_ICON = "icon.ico"


def notify(message):
    notification.notify(
        title=APP_NAME,
        message=message,
        app_name=APP_NAME,
        app_icon=os.path.join(os.getcwd(), TRAY_ICON),
    )

def is_pyspark_format(clipboard):
    if clipboard.startswith("%pyspark-format") or clipboard.startswith("#%format"):
        return True
    return False


def format_with_black_to_clipboard(clipboard_content):
    start_exp = ''
    if clipboard_content.startswith("%pyspark-format"):
        start_exp = '%pyspark\n'
    clipboard_content = clipboard_content.lstrip("%pyspark-format").lstrip("#%format")
    try:
        res = format_str(clipboard_content, mode=FileMode(line_length=100))
        res = start_exp + res
        notify("done!")
        return res
    except Exception as e:
        notify("oops\n" + str(e))
    return None

def is_pyspark_isort(clipboard):
    if clipboard.startswith("%pyspark-isort") or clipboard.startswith("#%isort"):
        return True
    return False

def isort_imports_to_clipboard(clipboard_content):
    start_exp = ''
    if clipboard_content.startswith("%pyspark-isort"):
        start_exp = '%pyspark\n'
    clipboard_content = clipboard_content.lstrip("%pyspark-isort").lstrip("#%isort")
    try:
        res = isort.code(clipboard_content)
        res = start_exp + res
        notify("done!")
        return res
    except Exception as e:
        notify("oops\n" + str(e))
    return None

class ClipboardWatcher(threading.Thread):
    def __init__(self, predicate_callbacks_list , pause=5.0):
        super(ClipboardWatcher, self).__init__()
        self._predicate_callbacks_list = predicate_callbacks_list
        self._pause = pause
        self._stopping = False

    def run(self):
        recent_value = ""
        while not self._stopping:
            try:
                tmp_value = pyperclip.waitForNewPaste()
                if tmp_value != recent_value:
                    recent_value = tmp_value
                    for (_predicate, _callback) in self._predicate_callbacks_list:
                        if _predicate(recent_value):
                            return_to_clipboard = _callback(recent_value)
                            if return_to_clipboard is not None:
                                recent_value = return_to_clipboard
                                pyperclip.copy(return_to_clipboard)
                            break
            except pyperclip.PyperclipWindowsException:
                pass
            time.sleep(self._pause)

    def stop(self):
        self._stopping = True


def create_menu_item(menu, label, func=None):
    item = wx.MenuItem(menu, -1, label)
    if func is not None:
        menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.set_icon(TRAY_ICON)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, APP_NAME)
        menu.AppendSeparator()
        create_menu_item(menu, "Exit", self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, APP_NAME)

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()
        os._exit(1)

    def on_left_down(self, event):
        pass


class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    watcher = ClipboardWatcher([(is_pyspark_format, format_with_black_to_clipboard), (is_pyspark_isort, isort_imports_to_clipboard)], 0.05
    )
    watcher.start()

    app = App(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
