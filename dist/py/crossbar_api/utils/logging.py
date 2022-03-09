# 重载默认print函数，使得其刷新缓冲区直接输出，避免其他控制台捕获程序捕获不到
def print(*args, end='\r\n'):
    import sys
    for msg in args:
        sys.stdout.write(msg)
    sys.stdout.write(end)
    sys.stdout.flush()
