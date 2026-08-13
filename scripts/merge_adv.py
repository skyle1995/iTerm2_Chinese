#!/usr/bin/env python3
"""Merge translations for the 157 missing advanced-setting strings.

For each full "name\ndescription" key we reuse the standalone head/tail
translations already present in the dict where available, and supply new
translations for the missing parts. Also adds quit-confirmation alert
strings and two small corrections.
"""
import json

D_PATH = '/tmp/translations_merged.json'
MISS_PATH = '/tmp/adv_missing.json'

d = json.load(open(D_PATH))
keys = json.load(open(MISS_PATH))['settings']
assert len(keys) == 157, len(keys)

# New head (name) translations for indices lacking a standalone entry.
NEW_HEADS = {
    2: '调试：在旧版（非 GPU）渲染器中高亮提示符标记的提示符/命令/排除范围。',
    8: '当会话的前台作业祖先列表意外缩短时记录详细跟踪。',
    9: '定期记录非 ASCII 字符串长度的直方图。',
    11: '将可恢复状态的大小信息记录到 /tmp/statesize.*.txt。',
    12: '将文本绘制性能统计信息记录到控制台。',
    25: '在旧版渲染器中用随机颜色勾画脏矩形。',
    33: '当 Codecierge 无法自动执行命令时发送给 LLM 的提示词。',
    34: '当 Codecierge 能够自动执行命令时发送给 LLM 的提示词。',
    55: '在新会话中设置指向此 iTerm2 构建应用包的 IT2_APP_PATH 环境变量？',
    56: '设置 ITERM2_COOKIE 环境变量，允许无需确认即启动 Python 脚本？',
    59: '在正在广播输入的会话中放大或缩小字体时，是否影响所有广播输入的会话？',
    69: '在 iTerm2 Buddy 直播流中打上帧号？',
    77: '抑制在启用鼠标报告时，拖动后按 Cmd-C 所显示的询问是否要禁用鼠标报告的通知？',
    78: '抑制询问是否要禁用调整大小报告的通知',
    79: '抑制「已恢复会话的配置文件不再存在」的通知？',
    80: '抑制「已保存的窗口布局具有无效初始工作目录」的通知。',
    81: '抑制「终端尝试访问剪贴板但被拒绝」的通知？',
    83: '粘贴以换行符结尾的单行时抑制多行粘贴警告。',
    85: '在 shell 提示符处粘贴以换行符结尾的单行时抑制警告。',
    107: 'uv 下载清单的 URL（使用 uv 配置 Python 运行时时使用）。',
    108: '检查 Python 脚本运行时新 Beta 版本的 URL。',
    109: '检查 Python 脚本运行时新版本的 URL。',
    110: '检查 AI 模型目录更新的 URL。',
    130: '当机器的国家和语言组合不受支持时，设置给 LC_CTYPE 的值。',
    133: '启用安全键盘输入时，如果 `open` 命令似乎失败则发出警告？',
    134: '当「在下一标记处警报」配置为播放声音时，上一个命令错误完成使用此名称的文件。',
    135: '当「在下一标记处警报」配置为播放声音时，上一个命令成功完成使用此名称的文件。',
    136: '启用焦点跟随鼠标时，iTerm2 变为激活状态时激活光标下的窗口？',
    137: '启用焦点跟随鼠标时，即使未激活也抢占键盘焦点。',
    138: '启用自适应帧率且使用 Metal 渲染器时，高吞吐量情况下以此帧率刷新（FPS）。',
    139: '启用自适应帧率时，高吞吐量情况下以此帧率刷新（FPS）。',
    140: '启用光标移动动画时，仅当光标移动至少这么多点距离时才执行动画。',
    144: '为自动命令补全排序命令历史时：命令的使用次数对其得分的贡献程度？得分越高，命令越靠近列表顶部。',
    145: '为自动命令补全排序命令历史时：距上次使用的时间对命令得分的贡献程度？得分越高，命令越靠近列表顶部。',
    150: 'iTerm2 Buddy 直播流：最大采集提前时间（毫秒）。',
    151: 'iTerm2 Buddy 直播流：手机解码队列最大深度。',
    152: 'iTerm2 Buddy 直播流：视频码率倍数。',
    153: 'iTerm2 Buddy 推送通知：唤醒推送之间的最小秒数。',
    155: '当 iTerm2 不是激活应用时，在激活窗格中 ⌘-点击会调用语义历史。',
    156: '在提示符处 ⌘-点击会显示命令信息窗口',
}

# New tail (description) translations for indices lacking a standalone entry.
NEW_TAILS = {
    0: 'macOS 存在一个会导致应用卡死的缺陷。由于这是一个很少使用的菜单，默认情况下已禁用。',
    1: '如果不为空，则每当你点击 iTerm2 原本会交给系统打开的 URL（包括 OSC 8 超链接和自动检测到的 URL）时，'
       '此命令会通过 /bin/sh -c 作为静默后台任务运行。这是一个插值字符串；使用 \\(url) 表示 URL，'
       '使用 \\(background) 表示是否请求了后台打开（点击时按住 Option 键则为 1，否则为 0）。'
       '该命令负责以自己选择的方式打开 URL（例如「open -g \\(url)」表示在后台打开）。'
       '为空时，URL 正常打开。iTerm2 内部 scheme（iterm2:）、绑定到配置文件的 URL scheme '
       '以及语义历史文件链接不受影响。',
    2: '启用后，旧版渲染器会在每个可见提示符标记的提示符范围（OSC 133 A 到 B）周围叠加蓝色轮廓，'
       '在其命令范围（B 到 C）周围叠加绿色轮廓，并在每个被排除的子范围（PS2 前缀以及通过 OSC 133 k= '
       '记录的右侧提示符区域）周围叠加红色轮廓。要查看效果请禁用 Metal 渲染器（「设置」→「通用」→「Magic」）。'
       '此功能面向开发和缺陷报告；正常使用请保持关闭。',
    3: '当代码审查工作组工具栏自动将审查结果发送到主会话时，它会粘贴结果然后发送 Return 提交。'
       '此项指定粘贴的结果完成后、发送该 Return 之前等待的时间。具有粘贴去抖动的 TUI（例如 Claude Code）'
       '会把一起到达的粘贴和 Return 作为一批处理，因此 Return 可能被吞掉，审查无法提交；'
       '此延迟可让 Return 落在之后的读取中从而成功提交。默认值与 Claude Code 的 500 毫秒粘贴稳定窗口一致。'
       '设为 0 表示立即发送。',
    5: '-1：使用旧版设置（默认）\n0：新建窗口\n1：新建标签页\n2：垂直拆分窗格\n3：水平拆分窗格\n'
       '这提供了一个统一的设置来控制外部实例的创建。',
    8: '当某个中间祖先进程（例如 claude CLI）在单次进程缓存更新中从被跟踪会话的前台作业祖先链中消失时，'
       '通过 RLog 记录持有该消失祖先的 pid、它是否仍在进程表中，以及从最深层前台作业向上遍历的完整过程。'
       '用于诊断可能拆毁 Claude Code 工作组的虚假作业结束事件。默认关闭；仅在复现问题时开启。',
    9: '有助于调整异步预转换的最小字符串长度。',
    10: '将发送给 AI 供应商以及从其接收的每一个字节（完整请求头、正文、流式分块、最终响应、错误和耗时）'
        '写入 ~/Library/Application Support/iTerm2/AIChatWire/。每次启动应用生成一个日志文件；'
        '完成后请自行轮换或删除。警告：日志会原样捕获 Authorization / API 密钥头以及完整的提示词和响应内容。'
        '默认关闭；仅在复现问题时开启，并在完成后删除文件。',
    13: '这也限制了 \\3 和 \\4 替换的大小。',
    24: '启用时，使用 tmux -CC 附加（或 tmux 创建新窗口时）将显示窗口或标签页但不移动键盘焦点。'
        '焦点停留在附加的会话上。',
    25: '有助于直观地验证文本视图每帧重绘了哪些区域。这只影响旧版（非 GPU）渲染器，'
        '在 GPU（Metal）渲染器启用时无任何作用，因此不能用来判断 GPU 渲染器是否启用。'
        '要使用它，请先在「设置」→「通用」→「Magic」中关闭 GPU 渲染器。',
    26: '不为空时，应用的行为就如同 [NSHost fullyQualifiedDomainName] 返回此值。'
        '这让你无需真正重命名电脑即可测试本地主机检测对主机名变化的反应。'
        '只影响更改后报告的主机；留空则使用真实主机名。',
    30: '这是为解决问题 10220 中与 AltTab 的不兼容而作的尝试。',
    31: '这将预转换与解析线程解耦，以获得更好的吞吐量。',
    32: '这利用了解析与屏幕变更之间的并行性，以获得更好的性能。',
    38: '必须是纯 https 源（协议和主机，无路径），例如 https://companion-relay.iterm2.com。'
        '中继是唯一的传输方式，因此必须设置此项配对才能工作；派生版本可将其指向自己的 Worker。'
        '留空则完全禁用中继。用户默认键为 `CompanionRelayOrigin`。',
    39: '绕过旧版 vim 无法正确解析 8 位值的缺陷。',
    42: '这需要关闭「系统设置 > 桌面与程序坞 > 退出应用时关闭窗口」。',
    44: '它们运行命令：ssh -t "cd $$PATH$$; exec \\$SHELL -l"',
    46: '某些不使用备用屏幕缓冲区的全屏程序通过将光标移到屏幕顶部并覆盖已有内容来重绘，'
        '从而破坏你仍可见的内容。启用后，iTerm2 会先将可见屏幕滚动保存到历史中，以免内容丢失。'
        '需要 shell 集成。',
    48: '值应使用 Vim 语法，例如用 \\e 表示 escape。',
    49: '值应使用 Vim 语法，例如用 \\e 表示 escape。',
    53: '值应使用 Vim 语法，例如用 \\n 表示换行，用 \\e 表示 escape。',
    54: 'iTerm2 附带了常见 TERM（xterm、xterm-new 和 xterm-256color）的扩展 terminfo 功能。'
        '例如启用了 undercurl。新会话创建时带有 TERMINFO_DIRS，使自定义 TERMINFO 优先于系统默认值。',
    55: '当多个具有相同 bundle 标识符的 iTerm2 构建同时运行时，这可消除 AppleScript 目标的歧义，'
        '使「it2」命令行工具向此 iTerm2 实例请求 cookie。面向 iTerm2 开发者。'
        '只影响更改此设置后创建的会话。',
    61: '启用后，插值字符串中引用未定义变量的表达式将被视为空字符串。例如「\\(bogus)」。'
        '作为函数调用参数引用未定义变量（例如「\\(f(bogus))」）仍会报错。',
    86: '此操作用于进程树，你可以在工具带中找到它，或点击状态栏的「作业」组件。',
    91: 'iTerm2 将字符串「%@」替换为要搜索的文本。查询参数使用百分号转义。',
    92: 'iTerm 将字符串「%@」替换为要搜索的文本。查询参数使用百分号转义。',
    95: '0 表示光标的背景色始终为单元格的文字颜色，1 表示始终为黑色或白色。',
    96: '0 表示光标的文字颜色始终为单元格的背景色，1 表示始终为黑色或白色。',
    100: '这适用于使用 Swift 内联表达式语法时调用脚本注册的函数。',
    110: '该目录定义内置 AI 模型（上下文窗口、功能以及每个供应商的推荐模型）。'
         'iTerm2 会定期下载签名的较新副本，使新模型无需更新应用即可用。'
         '仅在启用 AI 功能且已授予权限时才会执行；URL 非空本身不会启用检查。'
         '清空此 URL 可完全禁用检查。',
    117: 'COLORFGBG 变量指明与前景色和背景色匹配的 ANSI 颜色。如果没有颜色匹配且启用了此设置，'
         '则将该变量设为 15;0 表示深色背景，或 0;15 表示浅色背景。',
    124: '启用后，iTerm2 使用 uv 下载 Python 并为每个脚本构建环境，而不是使用内置的 Python 运行时。'
         'macOS 13 及更高版本默认开启。已配置好的脚本无论此设置如何都会继续运行；'
         '它只影响脚本的创建、导入和迁移。',
    126: '这会以更快的速度但更低的保真度绘制非 ASCII 文本。'
         '如果在「设置」>「配置文件」>「文本」中启用了连字，则忽略此设置。',
    131: '这是逗号分隔的变量列表，可通过 OSC 1337 ReportVariable=name 控制序列报告。'
         '每个变量名前必须加「allow:」或「deny:」前缀。',
    142: '这是一个插值字符串。使用 \\(filenames) 引用拖入文件的经 shell 引号处理、以空格分隔的完整路径。'
         '如果此偏好为空，则改为粘贴文件名。',
    143: '设为 -1 以禁用警告。\n字符按 UTF-16 计数。',
    146: '「焦点窗口」（默认）将窗口作为标签页附加到当前拥有键盘焦点的 iTerm2 窗口。'
         '「最上层会话窗口」则将其附加到已显示此 tmux 会话标签页的最前端 iTerm2 窗口，无论焦点在何处。',
    150: '一旦主机领先手机已确认的最后一帧超过此值，就停止发送新帧，并在手机赶上后恢复。'
         '较大的值可容忍更多链路延迟，但实时视图可能滞后更多。只影响帧率；每帧质量不变。',
    151: '一旦手机报告排队等待解码/显示的帧数超过此值，主机就停止发送新帧，并在队列排空后恢复。'
         '较大的值允许更多帧在手机上堆积后才退让。只影响帧率；每帧质量不变。',
    152: '缩放由分辨率得出的编码器码率。大于 1 的值使流中的文字更清晰但消耗更多带宽；'
         '小于 1 的值节省带宽但清晰度下降。结果仍会被限制在流的最低和最高码率之间。',
}

added = 0
for i, k in enumerate(keys):
    assert k not in d, f'full key already present: {i}'
    nl = k.find('\n')
    head = k if nl < 0 else k[:nl]
    tail = None if nl < 0 else k[nl + 1:]
    if head in d:
        zh_head = d[head]
    elif i in NEW_HEADS:
        zh_head = NEW_HEADS[i]
    else:
        raise SystemExit(f'MISSING HEAD for index {i}: {head!r}')
    if tail is None:
        value = zh_head
    elif tail == '':
        value = zh_head + '\n'
    else:
        if tail in d:
            zh_tail = d[tail]
        elif i in NEW_TAILS:
            zh_tail = NEW_TAILS[i]
        else:
            raise SystemExit(f'MISSING TAIL for index {i}: {tail[:80]!r}')
        value = zh_head + '\n' + zh_tail
    d[k] = value
    added += 1

# The two %@-bearing keys also need their leading-newline tails registered
# (runtime head/tail splitting only applies to plain, non-% entries).
for i in (91, 92):
    k = keys[i]
    tail_with_nl = '\n' + k.split('\n', 1)[1]
    d[tail_with_nl] = '\n' + NEW_TAILS[i]
    added += 1

# --- quit-confirmation alert + close-reason strings ---
extra = {
    'Quit iTerm2?': '退出 iTerm2？',
    'All sessions will be closed.': '所有会话都将关闭。',
    'Sessions will be restored automatically when iTerm2 is relaunched.':
        '重新启动 iTerm2 时会自动恢复会话。',
    'Why am I being prompted?': '为什么会出现此提示？',
    'You are being prompted because:\n\n%@': '出现此提示是因为：\n\n%@',
    '“Settings > General > Closing > Confirm closing multiple sessions” is enabled.':
        '已启用「设置 > 通用 > 关闭 > 关闭多个会话时确认」。',
    '“Settings > General > Closing > Confirm Quit iTerm2” and “Even if there are no windows” is enabled.':
        '已启用「设置 > 通用 > 关闭 > 退出 iTerm2 时确认」和「即使没有窗口」。',
    '“Settings > General > Closing > Confirm Quit iTerm2” is enabled and there is at least one terminal window.':
        '已启用「设置 > 通用 > 关闭 > 退出 iTerm2 时确认」，并且至少存在一个终端窗口。',
    # value uses %@ because gen_shim splits template values on %@ only
    'Tab #%d is pinned.': '标签页 #%@ 已被固定。',
    'The profile “%@” always requires confirmation.': '配置文件「%@」始终要求确认。',
    'A session with profile “%@” is running %@.': '一个使用配置文件「%@」的会话正在运行 %@。',
    'A session with profile “%@” is running %@, and %@ other %@.':
        '一个使用配置文件「%@」的会话正在运行 %@，另有 %@ 个其他 %@。',
    'A tmux session is configured to prompt if jobs are running, but tmux doesn’t expose the process tree.':
        '某个 tmux 会话被配置为在有作业运行时提示，但 tmux 不公开进程树。',
    'This pane is locked.': '此窗格已锁定。',
    'You can change this setting in Settings > Profiles > Session':
        '你可以在「设置 > 配置文件 > 会话」中更改此设置',
    'Don’t Save': '不存储',
}
for k, v in extra.items():
    if k not in d:
        d[k] = v
        added += 1
    else:
        print(f'note: already present: {k!r}')

# --- corrections of two earlier mistranslations ---
fixes = {
    'Tabs wrap around to the next line.': '制表符换行到下一行。',
    'Trackpad scrolls fast?': '触控板快速滚动？',
}
for k, v in fixes.items():
    old = d.get(k)
    d[k] = v
    print(f'fix: {k!r}: {old!r} -> {v!r}')

json.dump(d, open(D_PATH, 'w'), ensure_ascii=False, indent=0)
print(f'merged: +{added} entries; dict total {len(d)}')
