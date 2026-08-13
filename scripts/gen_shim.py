#!/usr/bin/env python3
"""Generate zh_shim.m: runtime translation dylib source with embedded dict."""

import json
import os
import re

_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_dict = os.path.join(_here, 'translations_merged.json')
if not os.path.exists(_dict):
    _dict = '/tmp/translations_merged.json'
trans = json.load(open(_dict))
payload = json.dumps(trans, ensure_ascii=False)

# Escape for C string literal
c_payload = payload.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

SRC = r'''// iTerm2 runtime Simplified-Chinese translation shim.
// Swizzles AppKit string setters; translates via exact-match dictionary,
// with template (regex) support for strings containing format placeholders.
#import <Cocoa/Cocoa.h>
#import <objc/runtime.h>

static NSDictionary *ZHT = nil;
static NSArray *ZHTemplates = nil;

static NSString *ZHTrCore(NSString *s) {
    NSString *t = [ZHT objectForKey:s];
    if (t) return t;
    for (NSDictionary *e in ZHTemplates) {
        NSRegularExpression *rx = e[@"rx"];
        NSRange full = NSMakeRange(0, [s length]);
        NSTextCheckingResult *m =
            [rx firstMatchInString:s options:NSMatchingAnchored range:full];
        if (m && NSEqualRanges([m range], full)) {
            NSArray *parts = e[@"parts"];
            NSUInteger need = [parts count] - 1;
            if (m.numberOfRanges - 1 < need) continue;
            NSMutableString *out = [NSMutableString stringWithCapacity:[s length] + 16];
            for (NSUInteger i = 0; i < [parts count]; i++) {
                [out appendString:parts[i]];
                if (i < need) {
                    NSRange r = [m rangeAtIndex:i + 1];
                    if (r.location != NSNotFound) {
                        [out appendString:[s substringWithRange:r]];
                    }
                }
            }
            return out;
        }
    }
    return s;
}

static NSString *ZHTr(NSString *s) {
    if (!s || !ZHT || [s length] == 0 || [s length] > 4096) return s;
    NSString *r = ZHTrCore(s);
    if (r != s) return r;
    /* Strings padded with whitespace/newlines (e.g. "\nTitle" used by the
       advanced-settings table) still get translated; padding preserved. */
    NSString *t2 = [s stringByTrimmingCharactersInSet:
                    [NSCharacterSet whitespaceAndNewlineCharacterSet]];
    NSUInteger n2 = [t2 length];
    if (n2 > 0 && n2 != [s length]) {
        NSString *tr = ZHTrCore(t2);
        if (tr != t2) {
            NSRange rng = [s rangeOfString:t2];
            NSMutableString *out = [NSMutableString stringWithCapacity:[s length] + 16];
            [out appendString:[s substringToIndex:rng.location]];
            [out appendString:tr];
            [out appendString:[s substringFromIndex:rng.location + rng.length]];
            return out;
        }
    }
    return s;
}

/* Translate an attributed string run-by-run so each run keeps its own
   attributes (font size, color). Replacing the whole string at once would
   make the replacement inherit the FIRST character's attributes — e.g. the
   8pt spacer newline in the Advanced settings table — shrinking all text. */
static NSAttributedString *ZHTrAttr(NSAttributedString *a) {
    if (!a || !ZHT) return a;
    NSString *s = [a string];
    NSUInteger len = [s length];
    if (len == 0 || len > 65536) return a;
    NSMutableAttributedString *out = [[NSMutableAttributedString alloc] init];
    BOOL changed = NO;
    NSUInteger pos = 0;
    while (pos < len) {
        NSRange eff = NSMakeRange(pos, len - pos);
        NSDictionary *attrs = [a attributesAtIndex:pos effectiveRange:&eff];
        NSString *chunk = [s substringWithRange:eff];
        NSString *tr = ZHTr(chunk);
        if (![tr isEqualToString:chunk]) changed = YES;
        NSAttributedString *piece =
            [[NSAttributedString alloc] initWithString:tr attributes:attrs];
        [out appendAttributedString:piece];
        pos = NSMaxRange(eff);
    }
    return changed ? out : a;
}

static void ZHSwizzle(Class cls, SEL origSel, SEL swizSel) {
    Method orig = class_getInstanceMethod(cls, origSel);
    Method swiz = class_getInstanceMethod(cls, swizSel);
    if (!orig || !swiz) return;
    if (class_addMethod(cls, origSel, method_getImplementation(swiz),
                        method_getTypeEncoding(swiz))) {
        class_replaceMethod(cls, swizSel, method_getImplementation(orig),
                            method_getTypeEncoding(orig));
    } else {
        method_exchangeImplementations(orig, swiz);
    }
}

@interface NSMenuItem (ZH) @end
@implementation NSMenuItem (ZH)
- (instancetype)zh_initWithTitle:(NSString *)title action:(SEL)action
                   keyEquivalent:(NSString *)key {
    return [self zh_initWithTitle:ZHTr(title) action:action keyEquivalent:key];
}
- (void)zh_setTitle:(NSString *)title { [self zh_setTitle:ZHTr(title)]; }
- (void)zh_setToolTip:(NSString *)tip { [self zh_setToolTip:ZHTr(tip)]; }
@end

@interface NSMenu (ZH) @end
@implementation NSMenu (ZH)
- (NSMenuItem *)zh_addItemWithTitle:(NSString *)title action:(SEL)action
                      keyEquivalent:(NSString *)key {
    return [self zh_addItemWithTitle:ZHTr(title) action:action keyEquivalent:key];
}
- (void)zh_setTitle:(NSString *)title { [self zh_setTitle:ZHTr(title)]; }
@end

@interface NSWindow (ZH) @end
@implementation NSWindow (ZH)
- (void)zh_setTitle:(NSString *)title { [self zh_setTitle:ZHTr(title)]; }
@end

@interface NSControl (ZH) @end
@implementation NSControl (ZH)
- (void)zh_setStringValue:(NSString *)s { [self zh_setStringValue:ZHTr(s)]; }
- (void)zh_setAttributedStringValue:(NSAttributedString *)a {
    [self zh_setAttributedStringValue:ZHTrAttr(a)];
}
@end

@interface NSCell (ZH) @end
@implementation NSCell (ZH)
- (void)zh_setTitle:(NSString *)t { [self zh_setTitle:ZHTr(t)]; }
- (void)zh_setStringValue:(NSString *)s { [self zh_setStringValue:ZHTr(s)]; }
- (void)zh_setObjectValue:(id)v {
    if ([v isKindOfClass:[NSString class]]) v = ZHTr((NSString *)v);
    [self zh_setObjectValue:v];
}
- (void)zh_setAttributedStringValue:(NSAttributedString *)a {
    [self zh_setAttributedStringValue:ZHTrAttr(a)];
}
- (void)zh_setPlaceholderString:(NSString *)s {
    [self zh_setPlaceholderString:ZHTr(s)];
}
@end

@interface NSAlert (ZH) @end
@implementation NSAlert (ZH)
- (void)zh_setMessageText:(NSString *)t { [self zh_setMessageText:ZHTr(t)]; }
- (void)zh_setInformativeText:(NSString *)t { [self zh_setInformativeText:ZHTr(t)]; }
- (NSButton *)zh_addButtonWithTitle:(NSString *)t {
    return [self zh_addButtonWithTitle:ZHTr(t)];
}
@end

@interface NSTabViewItem (ZH) @end
@implementation NSTabViewItem (ZH)
- (void)zh_setLabel:(NSString *)l { [self zh_setLabel:ZHTr(l)]; }
@end

@interface NSToolbarItem (ZH) @end
@implementation NSToolbarItem (ZH)
- (void)zh_setLabel:(NSString *)l { [self zh_setLabel:ZHTr(l)]; }
- (void)zh_setPaletteLabel:(NSString *)l { [self zh_setPaletteLabel:ZHTr(l)]; }
- (void)zh_setToolTip:(NSString *)t { [self zh_setToolTip:ZHTr(t)]; }
@end

@interface NSView (ZH) @end
@implementation NSView (ZH)
- (void)zh_setToolTip:(NSString *)t { [self zh_setToolTip:ZHTr(t)]; }
@end

@interface NSSegmentedControl (ZH) @end
@implementation NSSegmentedControl (ZH)
- (void)zh_setLabel:(NSString *)l forSegment:(NSInteger)seg {
    [self zh_setLabel:ZHTr(l) forSegment:seg];
}
@end

/* macOS 26: NSSearchToolbarItem draws text/glyphs off-center (issue 12708);
   iTerm2's archiver round-trip workaround does not fully fix every 26.x
   build. Re-center the text and magnifier rects vertically. Scoped to
   iTermPrefsSearchFieldCell (the preferences toolbar search field). */
typedef NSRect (*ZHRectImp)(id, SEL, NSRect);
static ZHRectImp ZHOrigTitleRect = NULL;
static ZHRectImp ZHOrigSearchBtnRect = NULL;

/* Vertical nudge for the off-center placeholder/glyph on macOS 26.
   AppKit y-axis is up; content sits too high, so shift the rect down. */
static const CGFloat ZHSearchYShift = 3.5;

static NSRect ZHCenterY(ZHRectImp orig, id self, SEL _cmd, NSRect bounds) {
    NSRect r = orig(self, _cmd, bounds);
    if (r.size.height > 0 && bounds.size.height > r.size.height) {
        r.origin.y = NSMidY(bounds) - r.size.height / 2;
    } else if (r.size.height > 0) {
        r.origin.y -= ZHSearchYShift;
    }
    return r;
}
static NSRect zh_titleRectForBounds(id self, SEL _cmd, NSRect b) {
    return ZHCenterY(ZHOrigTitleRect, self, _cmd, b);
}
static NSRect zh_searchButtonRectForBounds(id self, SEL _cmd, NSRect b) {
    return ZHCenterY(ZHOrigSearchBtnRect, self, _cmd, b);
}
static ZHRectImp ZHOrigDrawRect = NULL;
static NSRect zh_drawingRectForBounds(id self, SEL _cmd, NSRect b) {
    return ZHCenterY(ZHOrigDrawRect, self, _cmd, b);
}

/* Title-lookup fallbacks: internal code looks items up by English titles;
   after translation those lookups must also try the translated title. */
@interface NSMenu (ZHLookup) @end
@implementation NSMenu (ZHLookup)
- (NSMenuItem *)zh_itemWithTitle:(NSString *)title {
    NSMenuItem *hit = [self zh_itemWithTitle:title];
    if (!hit && title && ZHT) {
        NSString *t = [ZHT objectForKey:title];
        if (t) hit = [self zh_itemWithTitle:t];
    }
    return hit;
}
@end

@interface NSPopUpButton (ZHLookup) @end
@implementation NSPopUpButton (ZHLookup)
- (NSInteger)zh_indexOfItemWithTitle:(NSString *)title {
    NSInteger idx = [self zh_indexOfItemWithTitle:title];
    if (idx == -1 && title && ZHT) {
        NSString *t = [ZHT objectForKey:title];
        if (t) idx = [self zh_indexOfItemWithTitle:t];
    }
    return idx;
}
- (void)zh_selectItemWithTitle:(NSString *)title {
    if (title && ZHT && [self zh_indexOfItemWithTitle:title] == -1) {
        NSString *t = [ZHT objectForKey:title];
        if (t && [self zh_indexOfItemWithTitle:t] != -1) {
            [self zh_selectItemWithTitle:t];
            return;
        }
    }
    [self zh_selectItemWithTitle:title];
}
@end

static const char *ZH_DICT_JSON = "%%PAYLOAD%%";

__attribute__((constructor)) static void ZHInit(void) {
    @autoreleasepool {
        NSData *d = [NSData dataWithBytes:ZH_DICT_JSON
                                   length:strlen(ZH_DICT_JSON)];
        id parsed = [NSJSONSerialization JSONObjectWithData:d options:0 error:nil];
        if (![parsed isKindOfClass:[NSDictionary class]]) return;
        NSMutableDictionary *plain = [NSMutableDictionary dictionaryWithCapacity:[parsed count]];
        NSMutableArray *templates = [NSMutableArray array];
        NSCharacterSet *digits = [NSCharacterSet decimalDigitCharacterSet];
        for (NSString *k in parsed) {
            NSString *v = parsed[k];
            if (![v isKindOfClass:[NSString class]]) continue;
            if ([k rangeOfString:@"%"].location == NSNotFound) {
                plain[k] = v;
                continue;
            }
            // Build regex template: placeholders -> capture groups
            NSString *esc = [NSRegularExpression escapedPatternForString:k];
            // escaped pattern still contains placeholders as %@ / %d etc.
            NSMutableString *rx = [NSMutableString string];
            NSScanner *sc = [NSScanner scannerWithString:esc];
            NSMutableArray *parts = [NSMutableArray array];
            NSMutableString *cur = [NSMutableString string];
            while (![sc isAtEnd]) {
                unichar c = [[sc string] characterAtIndex:[sc scanLocation]];
                if (c == '%') {
                    NSUInteger loc = [sc scanLocation] + 1;
                    NSString *s2 = [sc string];
                    // optional positional arg like %1$@
                    NSUInteger i = loc;
                    while (i < [s2 length] && [digits characterIsMember:[s2 characterAtIndex:i]]) i++;
                    if (i > loc && i < [s2 length] && [s2 characterAtIndex:i] == '$') i++;
                    if (i < [s2 length]) {
                        unichar spec = [s2 characterAtIndex:i];
                        if (spec == '@' || spec == 'd' || spec == 'l' || spec == 'f' ||
                            spec == 'u' || spec == 's' || spec == 'x') {
                            [parts addObject:[cur copy]];
                            [cur setString:@""];
                            [rx appendString:@"(.*)"];
                            // skip the placeholder in scanner
                            [sc setScanLocation:i + 1];
                            continue;
                        }
                    }
                }
                [cur appendFormat:@"%C", c];
                [rx appendFormat:@"%C", c];
                [sc setScanLocation:[sc scanLocation] + 1];
            }
            [parts addObject:cur];
            if ([parts count] < 2) { plain[k] = v; continue; }
            NSRegularExpression *re =
                [NSRegularExpression regularExpressionWithPattern:rx options:0 error:nil];
            if (re) {
                [templates addObject:@{@"rx": re,
                                       @"parts": [v componentsSeparatedByString:@"%@"]}];
            }
        }
        /* For multi-line entries, also register head/tail pieces split at the
           first newline so run-by-run attributed-string translation can match
           individual runs. "name\nrest" -> "zhname\nzhrest" additionally gives
           "name" -> "zhname" and "\nrest" -> "\nzhrest" (Advanced settings
           table builds each cell as spacer + name + subtitle runs). */
        NSArray *plainKeys = [plain allKeys];
        for (NSString *k in plainKeys) {
            NSRange nl = [k rangeOfString:@"\n"];
            if (nl.location == NSNotFound || nl.location == 0 ||
                nl.location + 1 >= [k length]) continue;
            NSString *v = plain[k];
            if (![v isKindOfClass:[NSString class]]) continue;
            NSRange vnl = [v rangeOfString:@"\n"];
            if (vnl.location == NSNotFound) continue;
            NSString *kh = [k substringToIndex:nl.location];
            NSString *kt = [k substringFromIndex:nl.location];
            NSString *vh = [v substringToIndex:vnl.location];
            NSString *vt = [v substringFromIndex:vnl.location];
            if ([kh length] && ![plain objectForKey:kh]) plain[kh] = vh;
            if ([kt length] && ![plain objectForKey:kt]) plain[kt] = vt;
        }

        ZHT = [plain copy];
        ZHTemplates = [templates copy];

        ZHSwizzle([NSMenuItem class], @selector(initWithTitle:action:keyEquivalent:),
                  @selector(zh_initWithTitle:action:keyEquivalent:));
        ZHSwizzle([NSMenuItem class], @selector(setTitle:), @selector(zh_setTitle:));
        ZHSwizzle([NSMenuItem class], @selector(setToolTip:), @selector(zh_setToolTip:));
        ZHSwizzle([NSMenu class], @selector(addItemWithTitle:action:keyEquivalent:),
                  @selector(zh_addItemWithTitle:action:keyEquivalent:));
        ZHSwizzle([NSMenu class], @selector(setTitle:), @selector(zh_setTitle:));
        ZHSwizzle([NSWindow class], @selector(setTitle:), @selector(zh_setTitle:));
        ZHSwizzle([NSControl class], @selector(setStringValue:), @selector(zh_setStringValue:));
        ZHSwizzle([NSControl class], @selector(setAttributedStringValue:),
                  @selector(zh_setAttributedStringValue:));
        ZHSwizzle([NSCell class], @selector(setTitle:), @selector(zh_setTitle:));
        ZHSwizzle([NSCell class], @selector(setStringValue:), @selector(zh_setStringValue:));
        ZHSwizzle([NSCell class], @selector(setObjectValue:), @selector(zh_setObjectValue:));
        ZHSwizzle([NSCell class], @selector(setAttributedStringValue:),
                  @selector(zh_setAttributedStringValue:));
        ZHSwizzle([NSCell class], @selector(setPlaceholderString:),
                  @selector(zh_setPlaceholderString:));
        ZHSwizzle([NSAlert class], @selector(setMessageText:), @selector(zh_setMessageText:));
        ZHSwizzle([NSAlert class], @selector(setInformativeText:), @selector(zh_setInformativeText:));
        ZHSwizzle([NSAlert class], @selector(addButtonWithTitle:),
                  @selector(zh_addButtonWithTitle:));
        ZHSwizzle([NSTabViewItem class], @selector(setLabel:), @selector(zh_setLabel:));
        ZHSwizzle([NSToolbarItem class], @selector(setLabel:), @selector(zh_setLabel:));
        ZHSwizzle([NSToolbarItem class], @selector(setPaletteLabel:), @selector(zh_setPaletteLabel:));
        ZHSwizzle([NSToolbarItem class], @selector(setToolTip:), @selector(zh_setToolTip:));
        ZHSwizzle([NSView class], @selector(setToolTip:), @selector(zh_setToolTip:));
        ZHSwizzle([NSSegmentedControl class], @selector(setLabel:forSegment:),
                  @selector(zh_setLabel:forSegment:));
        ZHSwizzle([NSMenu class], @selector(itemWithTitle:), @selector(zh_itemWithTitle:));
        ZHSwizzle([NSPopUpButton class], @selector(indexOfItemWithTitle:),
                  @selector(zh_indexOfItemWithTitle:));
        ZHSwizzle([NSPopUpButton class], @selector(selectItemWithTitle:),
                  @selector(zh_selectItemWithTitle:));

        /* The prefs search-field cell lives in the main executable, whose
           classes are registered AFTER our constructor runs. Install the
           rect hooks from the main queue once the run loop starts. */
        dispatch_async(dispatch_get_main_queue(), ^{
            Class prefsCell = objc_getClass("iTermPrefsSearchFieldCell");
            if (!prefsCell) prefsCell = objc_getClass("NSSearchFieldCell");
            if (prefsCell) {
                Method m1 = class_getInstanceMethod(prefsCell, @selector(titleRectForBounds:));
                Method m2 = class_getInstanceMethod(prefsCell, @selector(searchButtonRectForBounds:));
                Method m3 = class_getInstanceMethod(prefsCell, @selector(drawingRectForBounds:));
                if (m1) ZHOrigTitleRect =
                    (ZHRectImp)method_setImplementation(m1, (IMP)zh_titleRectForBounds);
                if (m2) ZHOrigSearchBtnRect =
                    (ZHRectImp)method_setImplementation(m2, (IMP)zh_searchButtonRectForBounds);
                if (m3) ZHOrigDrawRect =
                    (ZHRectImp)method_setImplementation(m3, (IMP)zh_drawingRectForBounds);
            }
        });
    }
}
'''

src = SRC.replace('%%PAYLOAD%%', c_payload)
import sys as _sys
_out = _sys.argv[1] if len(_sys.argv) > 1 else os.path.join(_here, 'build', 'zh_shim.m')
os.makedirs(os.path.dirname(os.path.abspath(_out)), exist_ok=True)
with open(_out, 'w') as f:
    f.write(src)
print(f'Generated {_out} ({len(src)} bytes, dict {len(c_payload)} bytes)')
