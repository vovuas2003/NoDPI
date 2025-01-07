# No DPI [ver. 1.3]
Uses simple SSL fragmentation to avoid DPI.
No system privileges needed.

Currently works in Russia.

Alternatives: [GoodbyeDPI](https://github.com/ValdikSS/GoodbyeDPI)

## How to install

Requires: Python >= 3.8

1) Download file nodpi.py and run `python3 nodpi.py` or open nodpi.py file
2) Configure browser to use proxy on 127.0.0.1:8881
3) In browser disable kyber
4) Enjoy!

## Running on Windows without Python
1) Download [nodpi.exe](https://github.com/GVCoder09/nodpi/releases/tag/v1.3)
2) Download [blacklist.txt](https://github.com/GVCoder09/nodpi/blob/main/blacklist.txt) to the same folder
3) Configure browser to use proxy on 127.0.0.1:8881
4) In browser disable kyber
5) Enjoy!


## Known Bugs

- Doesn't bypass IP block
- Only TCP
- Doesn't work for HTTP only
- Not working with sites with old TLS
