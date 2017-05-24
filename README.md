# triotk

This is a tiny Python module for using
[trio](http://trio.readthedocs.io/en/latest/) with
[tkinter](https://github.com/Akuli/tkinter-tutorial). It works like
this:

```python
import tkinter as tk

import trio
import triotk


async def on_click():
    for i in range(3, 0, -1):
        print(i, "...")
        await trio.sleep(1)
    print("on_click done")


async def main(root):
    async with trio.open_nursery() as nursery:
        # clicking the button won't freeze the gui
        button = triotk.AsyncButton(
            root, nursery, text="Click me", command=on_click)
        button.pack()
        await triotk.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    trio.run(main, root)
```

If you want to install triotk you can just download or copy/paste
[triotk.py](triotk.py) to the folder that your program is in.
