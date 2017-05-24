import functools
import tkinter as tk
import _tkinter

import trio

try:
    DONT_WAIT = _tkinter.DONT_WAIT
except AttributeError:
    # this doesn't run on cpython or pypy, but i think having it here
    # doesn't matter
    DONT_WAIT = 2

__all__ = ['spawning_callback', 'AsyncButton', 'mainloop']


def spawning_callback(nursery, async_callback=None):
    """Return a new function that spawns *async_callback*.

    This can be also used as a decorator::

        @spawning_callback(nursery)
        def on_click():
            print("one")
            await trio.sleep(1)
            print("two")

        button['command'] = on_click

    Note that :class:`~AsyncButton` does this to its commands
    automatically, so usually you don't need to use this with buttons.
    """
    if async_callback is None:
        return functools.partial(spawning_callback, nursery)
    return functools.partial(nursery.spawn, async_callback)


class AsyncButton(tk.Button):
    """Like ``tkinter.Button``, but for asynchronous commands.

    The button works like this:

        async def the_callback():
            print("callback starting")
            await trio.sleep(1)      # doesn't freeze the gui
            print("callback completed")

        button = triotk.AsyncButton(
            root, nursery, text="Click me", command=the_callback)
        button.pack()

    This is a convenience class, and using this is equivalent to using
    :func:`spawning_callback` with ``tkinter.Button``. The nursery can
    be retrieved or changed later with the *nursery* attribute.
    """

    def __init__(self, parent, nursery, **kwargs):
        super().__init__(parent)
        self.nursery = nursery
        self._command = None
        self.configure(**kwargs)

    # tkinter makes adding custom options difficult :(
    @functools.wraps(tk.Button.configure)
    def configure(self, cnf=None, **kwargs):
        if cnf is None:
            cnf = {}

        if 'command' in cnf:
            command = cnf.pop('command')
        elif 'command' in kwargs:
            command = kwargs.pop('command')
        else:
            return super().configure(cnf, **kwargs)

        if callable(command):
            self._command = command
            command = spawning_callback(self.nursery, command)
        else:
            self._command = None

        return super().configure(cnf, command=command, **kwargs)

    config = configure

    # tkinter's __setitem__ does this too, but it's an implementation detail
    def __setitem__(self, key, value):
        self.config(**{key: value})

    @functools.wraps(tk.Button.cget)
    def cget(self, key):
        if key == 'command' and self._command is not None:
            return self._command
        return super().cget(key)

    __getitem__ = cget


async def mainloop(root=None):
    """Like ``root.mainloop()``, but this is asynchronous.

    The *root* argument can be any widget. If it's not specified, then
    tkinter's default root window is used.
    """
    if root is None:
        if tk._default_root is None:
            raise RuntimeError("create a tkinter.Tk() window "
                               "before calling triotk.mainloop()")
        root = tk._default_root

    try:
        dooneevent = root.tk.dooneevent
    except AttributeError:
        # probably pypy
        dooneevent = _tkinter.dooneevent

    while True:
        # do all pending things right away, but let other tasks run too
        while dooneevent(DONT_WAIT):
            await trio.sleep(0)

        # stop when the root window is destroyed
        try:
            root.winfo_exists()
        except tk.TclError:
            break

        # if nothing is going on, let's keep the cpu usage down
        await trio.sleep(1/60)
