#!/usr/bin/env python3
"""
inject_dylib.py — 向 Mach-O 可执行文件追加 LC_LOAD_DYLIB 加载命令(自带实现,
无需第三方工具)。支持 fat(universal)与单架构、32/64 位。

原理:在现有 load commands 之后的对齐填充区(padding)里追加一条
LC_LOAD_DYLIB,并更新 ncmds/sizeofcmds;不移动任何段数据,因此
section 偏移保持有效。若填充区空间不足则拒绝修改(与 insert_dylib 相同)。

用法:
    python3 inject_dylib.py <dylib-load-path> <mach-o-binary>

示例:
    python3 scripts/inject_dylib.py \
        '@executable_path/../Frameworks/iTermZhPatch.dylib' \
        /Applications/iTerm.app/Contents/MacOS/iTerm2

幂等:目标路径已存在时直接跳过。修改后代码签名会失效,需 ad-hoc 重签名。
"""

import struct
import sys

FAT_MAGIC = 0xcafebabe
FAT_CIGAM = 0xbebafeca
MH_MAGIC = 0xfeedface
MH_MAGIC_64 = 0xfeedfacf
LC_SEGMENT = 0x1
LC_SEGMENT_64 = 0x19
LC_LOAD_DYLIB = 0xc
LC_LOAD_WEAK_DYLIB = 0x80000000 | 0x18


def _pad(n, align):
    return (n + align - 1) // align * align


def _slice_min_section_offset(data, base, is64, le):
    """返回该架构 slice 内最小的非零 section 文件偏移;无则 None。"""
    e = '<' if le else '>'
    hdr = 32 if is64 else 28
    ncmds, sizeofcmds = struct.unpack_from(e + 'II', data, base + 16)
    min_off = None
    off = base + hdr
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from(e + 'II', data, off)
        if cmd in (LC_SEGMENT, LC_SEGMENT_64):
            if is64:
                nsects = struct.unpack_from(e + 'I', data, off + 64)[0]
                sect = off + 72
                for _s in range(nsects):
                    so = struct.unpack_from(e + 'I', data, sect + 48)[0]
                    if so:
                        min_off = so if min_off is None else min(min_off, so)
                    sect += 80
            else:
                nsects = struct.unpack_from(e + 'I', data, off + 48)[0]
                sect = off + 56
                for _s in range(nsects):
                    so = struct.unpack_from(e + 'I', data, sect + 40)[0]
                    if so:
                        min_off = so if min_off is None else min(min_off, so)
                    sect += 68
        off += cmdsize
    return min_off


def _existing_dylibs(data, base, is64, le):
    e = '<' if le else '>'
    hdr = 32 if is64 else 28
    ncmds, = struct.unpack_from(e + 'I', data, base + 16)
    out = []
    off = base + hdr
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from(e + 'II', data, off)
        if cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB):
            name_off, = struct.unpack_from(e + 'I', data, off + 8)
            name = data[off + name_off:off + cmdsize].split(b'\0')[0]
            out.append(name.decode('utf-8', 'replace'))
        off += cmdsize
    return out


def _inject_slice(data, base, path_b):
    """对单个架构 slice 注入;返回 'ok' / 'exists' / 'nospace'。"""
    magic, = struct.unpack_from('<I', data, base)
    if magic == MH_MAGIC_64:
        is64, le, hdr = True, True, 32
    elif magic == MH_MAGIC:
        is64, le, hdr = False, True, 28
    elif struct.unpack_from('>I', data, base)[0] in (MH_MAGIC_64, MH_MAGIC):
        is64 = struct.unpack_from('>I', data, base)[0] == MH_MAGIC_64
        le, hdr = False, (32 if is64 else 28)
    else:
        raise SystemExit(f'错误:偏移 {base} 处不是有效的 Mach-O 头')
    e = '<' if le else '>'

    if path_b.decode() in _existing_dylibs(data, base, is64, le):
        return 'exists'

    ncmds, sizeofcmds = struct.unpack_from(e + 'II', data, base + 16)
    cmd_end = base + hdr + sizeofcmds
    name_off = 24
    cmdsize = _pad(name_off + len(path_b) + 1, 8 if is64 else 4)

    # section 文件偏移相对 slice 起始,按相对值比较填充区空间
    min_off = _slice_min_section_offset(data, base, is64, le)
    if min_off is not None and (hdr + sizeofcmds) + cmdsize > min_off:
        return 'nospace'

    newcmd = struct.pack(e + 'IIIIII', LC_LOAD_DYLIB, cmdsize, name_off,
                         2, 0x10000, 0x10000)
    newcmd += path_b + b'\0' * (cmdsize - name_off - len(path_b))
    data[cmd_end:cmd_end + cmdsize] = newcmd
    struct.pack_into(e + 'II', data, base + 16, ncmds + 1, sizeofcmds + cmdsize)
    return 'ok'


def inject(binary_path, dylib_path):
    with open(binary_path, 'rb') as f:
        data = bytearray(f.read())
    magic, = struct.unpack_from('>I', data, 0)
    path_b = dylib_path.encode()
    results = []
    if magic in (FAT_MAGIC, FAT_CIGAM):
        nfat, = struct.unpack_from('>I', data, 4)
        for i in range(nfat):
            off, = struct.unpack_from('>I', data, 8 + i * 20 + 8)
            results.append(_inject_slice(data, off, path_b))
    else:
        results.append(_inject_slice(data, 0, path_b))

    if all(r == 'exists' for r in results):
        print(f'跳过:{dylib_path} 已在加载命令中')
        return
    if any(r == 'nospace' for r in results):
        raise SystemExit('错误:load commands 后填充区空间不足,无法注入')
    with open(binary_path, 'wb') as f:
        f.write(data)
    done = sum(1 for r in results if r == 'ok')
    print(f'已注入 {dylib_path}({done} 个架构)')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    inject(sys.argv[2], sys.argv[1])
