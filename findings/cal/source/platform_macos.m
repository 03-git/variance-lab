/*
 * platform_macos.m — one window, one bitmap, zero frameworks beyond Cocoa
 *
 * Copyright (C) 2026 subtract.ing
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#import <Cocoa/Cocoa.h>
#include "cal.h"
#include <string.h>

/* linux keycode mapping table */
static int mac_to_linux[128];

static void init_keymap(void) {
    memset(mac_to_linux, 0, sizeof(mac_to_linux));
    mac_to_linux[53]  = KEY_ESC;
    mac_to_linux[18]  = KEY_1;   mac_to_linux[19] = KEY_2;
    mac_to_linux[20]  = KEY_3;   mac_to_linux[21] = KEY_4;
    mac_to_linux[23]  = KEY_5;
    mac_to_linux[51]  = KEY_BACKSPACE;
    mac_to_linux[48]  = KEY_TAB;
    mac_to_linux[12]  = KEY_Q;   mac_to_linux[13] = KEY_W;
    mac_to_linux[14]  = KEY_E;   mac_to_linux[15] = KEY_R;
    mac_to_linux[17]  = KEY_T;   mac_to_linux[16] = KEY_Y;
    mac_to_linux[32]  = KEY_U;   mac_to_linux[34] = KEY_I;
    mac_to_linux[31]  = KEY_O;   mac_to_linux[35] = KEY_P;
    mac_to_linux[36]  = KEY_ENTER;
    mac_to_linux[0]   = KEY_A;   mac_to_linux[1]  = KEY_S;
    mac_to_linux[2]   = KEY_D;   mac_to_linux[3]  = KEY_F;
    mac_to_linux[5]   = KEY_G;   mac_to_linux[4]  = KEY_H;
    mac_to_linux[38]  = KEY_J;   mac_to_linux[40] = KEY_K;
    mac_to_linux[37]  = KEY_L;   mac_to_linux[41] = KEY_SEMICOLON;
    mac_to_linux[39]  = KEY_APOSTROPHE;
    mac_to_linux[56]  = KEY_LEFTSHIFT;
    mac_to_linux[6]   = KEY_Z;   mac_to_linux[7]  = KEY_X;
    mac_to_linux[8]   = KEY_C;   mac_to_linux[9]  = KEY_V;
    mac_to_linux[11]  = KEY_B;   mac_to_linux[45] = KEY_N;
    mac_to_linux[46]  = KEY_M;   mac_to_linux[43] = KEY_COMMA;
    mac_to_linux[47]  = KEY_DOT; mac_to_linux[44] = KEY_SLASH;
    mac_to_linux[60]  = KEY_RIGHTSHIFT;
    mac_to_linux[49]  = KEY_SPACE;
    mac_to_linux[122] = KEY_F1;  mac_to_linux[120] = KEY_F2;
    mac_to_linux[99]  = KEY_F3;  mac_to_linux[118] = KEY_F4;
    mac_to_linux[96]  = KEY_F5;
    mac_to_linux[126] = KEY_UP;  mac_to_linux[125] = KEY_DOWN;
    mac_to_linux[123] = KEY_LEFT; mac_to_linux[124] = KEY_RIGHT;
    mac_to_linux[117] = KEY_DELETE;
    mac_to_linux[29]  = KEY_0;
}

/* --- globals --- */

static cal_surface *g_surface;
static CGContextRef g_bitmap_ctx;
static NSWindow *g_window;
static cal_event g_pending;
static int g_has_event;
static int g_running = 1;

/* --- view --- */

@interface CalView : NSView
@end

@implementation CalView

- (BOOL)acceptsFirstResponder { return YES; }
- (BOOL)canBecomeKeyView { return YES; }

- (void)drawRect:(NSRect)rect {
    (void)rect;
    if (!g_bitmap_ctx) return;
    CGImageRef img = CGBitmapContextCreateImage(g_bitmap_ctx);
    if (!img) return;
    CGContextRef ctx = [[NSGraphicsContext currentContext] CGContext];
    CGContextDrawImage(ctx, [self bounds], img);
    CGImageRelease(img);
}

- (void)keyDown:(NSEvent *)event {
    int kc = [event keyCode];
    if (kc >= 0 && kc < 128 && mac_to_linux[kc]) {
        g_pending.type = CAL_KEY;
        g_pending.code = mac_to_linux[kc];
        g_pending.value = 1;
        g_pending.x = g_pending.y = 0;
        g_has_event = 1;
    }
}

- (void)keyUp:(NSEvent *)event {
    (void)event;
}

- (void)flagsChanged:(NSEvent *)event {
    int kc = [event keyCode];
    if (kc >= 0 && kc < 128 && mac_to_linux[kc]) {
        g_pending.type = CAL_KEY;
        g_pending.code = mac_to_linux[kc];
        g_pending.value = ([event modifierFlags] & NSEventModifierFlagShift) ? 1 : 0;
        g_has_event = 1;
    }
}

- (void)mouseDown:(NSEvent *)event {
    NSPoint p = [self convertPoint:[event locationInWindow] fromView:nil];
    g_pending.type = CAL_MOUSE;
    g_pending.code = 0;
    g_pending.value = 1;
    g_pending.x = (int)p.x;
    g_pending.y = g_surface->height - (int)p.y; /* flip y */
    g_has_event = 1;
}

@end

/* --- app delegate --- */

@interface CalDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate>
@end

@implementation CalDelegate

- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender {
    (void)sender;
    char *kiosk = getenv("CAL_KIOSK");
    if (kiosk && kiosk[0] == '1') return NSTerminateCancel;
    g_running = 0;
    return NSTerminateNow;
}

- (BOOL)windowShouldClose:(NSWindow *)sender {
    (void)sender;
    g_running = 0;
    return YES;
}

@end

/* --- platform API --- */

int platform_init(cal_surface *s) {
    init_keymap();
    g_surface = s;

    @autoreleasepool {
        [NSApplication sharedApplication];
        [NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];

        CalDelegate *delegate = [[CalDelegate alloc] init];
        [NSApp setDelegate:delegate];

        NSScreen *screen = [NSScreen mainScreen];
        NSRect frame = [screen frame];

        s->width = (int)frame.size.width;
        s->height = (int)frame.size.height;
        s->stride = s->width * 4;

        CGColorSpaceRef cs = CGColorSpaceCreateDeviceRGB();
        g_bitmap_ctx = CGBitmapContextCreate(
            NULL, s->width, s->height, 8, s->stride, cs,
            kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little);
        CGColorSpaceRelease(cs);
        if (!g_bitmap_ctx) return -1;

        s->pixels = (uint32_t *)CGBitmapContextGetData(g_bitmap_ctx);
        if (!s->pixels) return -1;

        NSUInteger style = NSWindowStyleMaskBorderless;
        g_window = [[NSWindow alloc]
            initWithContentRect:frame
            styleMask:style
            backing:NSBackingStoreBuffered
            defer:NO screen:screen];

        CalView *view = [[CalView alloc] initWithFrame:frame];
        [g_window setContentView:view];
        [g_window setDelegate:delegate];
        [g_window makeFirstResponder:view];

        char *kiosk = getenv("CAL_KIOSK");
        if (kiosk && kiosk[0] == '1') {
            [g_window setLevel:NSScreenSaverWindowLevel];
            [NSMenu setMenuBarVisible:NO];
            [NSCursor hide];
        } else {
            [g_window setLevel:NSFloatingWindowLevel];
        }

        [g_window makeKeyAndOrderFront:nil];
        [NSApp activateIgnoringOtherApps:YES];

        /* pump once to show window */
        NSEvent *ev;
        while ((ev = [NSApp nextEventMatchingMask:NSEventMaskAny
                      untilDate:nil inMode:NSDefaultRunLoopMode dequeue:YES])) {
            [NSApp sendEvent:ev];
        }
    }
    return 0;
}

int platform_event(cal_event *ev, int timeout_ms) {
    @autoreleasepool {
        g_has_event = 0;
        NSDate *until = [NSDate dateWithTimeIntervalSinceNow:timeout_ms / 1000.0];
        while (!g_has_event && g_running) {
            NSEvent *e = [NSApp nextEventMatchingMask:NSEventMaskAny
                          untilDate:until inMode:NSDefaultRunLoopMode dequeue:YES];
            if (!e) break;
            [NSApp sendEvent:e];
            if (g_has_event) {
                *ev = g_pending;
                return 1;
            }
            if ([[NSDate date] compare:until] != NSOrderedAscending) break;
        }
    }
    return 0;
}

void platform_flip(cal_surface *s) {
    (void)s;
    @autoreleasepool {
        [[g_window contentView] setNeedsDisplay:YES];
        /* service the display
           (drawRect will blit bitmap context to window) */
        NSEvent *ev;
        while ((ev = [NSApp nextEventMatchingMask:NSEventMaskAny
                      untilDate:nil inMode:NSDefaultRunLoopMode dequeue:YES])) {
            [NSApp sendEvent:ev];
        }
    }
}

void platform_cleanup(void) {
    if (g_bitmap_ctx) CGContextRelease(g_bitmap_ctx);
    @autoreleasepool {
        [NSMenu setMenuBarVisible:YES];
        [NSCursor unhide];
    }
}
