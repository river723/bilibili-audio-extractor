#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('gui_extractor_simple.py', 'rb') as f:
    content = f.read()

# The exact old string in bytes (with 3 trailing \r\n and a space)
old_bytes = b'cmd = [\r\n\r\n \'yt-dlp\',\r\n\r\n \'--extract-audio\', # \xe6\x8f\x90\xe5\x8f\x96\xe9\x9f\xb3\xe9\xa2\x91\r\n\r\n \'--audio-format\', \'best\', # \xe4\xbd\xbf\xe7\x94\xa8\xe6\x9c\x80\xe4\xbd\xb3\xe5\x8f\xaf\xe7\x94\xa8\xe6\xa0\xbc\xe5\xbc\x8f\r\n\r\n \'--audio-quality\', \'0\', # \xe6\x9c\x80\xe9\xab\x98\xe8\xb4\xa8\xe9\x87\x8f\r\n\r\n \'--output\', str(temp_dir / \'%(title)s.%(ext)s\'),\r\n\r\n \'--no-playlist\', # \xe4\xb8\x8d\xe4\xb8\x8b\xe8\xbd\xbd\xe6\x92\xad\xe6\x94\xbe\xe5\x88\x97\xe8\xa1\xa8\r\n\r\n \'--retries\', \'3\', # \xe9\x87\x8d\xe8\xaf\x95\xe6\xac\xa1\xe6\x95\xb0\r\n\r\n \'--fragment-retries\', \'3\', # \xe7\x89\x87\xe6\xae\xb5\xe9\x87\x8d\xe8\xaf\x95\xe6\xac\xa1\xe6\x95\xb0\r\n\r\n ]\r\n\r\n\r\n'

# The new string with improved headers
new_bytes = b'cmd = [\r\n\r\n \'yt-dlp\',\r\n\r\n \'--extract-audio\',\r\n\r\n \'--audio-format\', \'best\',\r\n\r\n \'--audio-quality\', \'0\',\r\n\r\n \'--output\', str(temp_dir / \'%(title)s.%(ext)s\'),\r\n\r\n \'--no-playlist\',\r\n\r\n \'--retries\', \'5\',\r\n\r\n \'--fragment-retries\', \'5\',\r\n\r\n \'--no-check-certificate\',\r\n\r\n \'--add-header\', \'User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\',\r\n\r\n \'--add-header\', \'Referer:https://www.bilibili.com\',\r\n\r\n ]\r\n\r\n\r\n'

if old_bytes in content:
    content = content.replace(old_bytes, new_bytes)
    with open('gui_extractor_simple.py', 'wb') as f:
        f.write(content)
    print('Replaced cmd list successfully!')
else:
    print('Old pattern not found')