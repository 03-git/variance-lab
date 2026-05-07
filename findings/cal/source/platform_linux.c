/*
 * platform_linux.c — DRM dumb buffer + evdev
 *
 * Copyright (C) 2026 subtract.ing
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include "cal.h"
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/select.h>
#include <dirent.h>
#include <linux/input.h>
#include <linux/kd.h>
#include <linux/vt.h>
#include <signal.h>
#include <xf86drm.h>
#include <xf86drmMode.h>

static int drm_fd = -1;
static uint32_t fb_id;
static uint32_t conn_id;
static uint32_t crtc_id;
static drmModeModeInfo mode;
static uint32_t handle;
static uint32_t pitch;
static uint64_t map_offset;
static void *map_ptr;
static size_t map_size;

static int kbd_fd = -1;
static int mouse_fd = -1;
static int tty_fd = -1;
static int prev_kbmode = -1;

/* probe /dev/dri/card* for a connected display */
static int drm_open(void) {
    char path[64];
    for (int i = 0; i < 8; i++) {
        snprintf(path, sizeof(path), "/dev/dri/card%d", i);
        int fd = open(path, O_RDWR | O_CLOEXEC);
        if (fd < 0) continue;
        if (!drmIsMaster(fd)) {
            drmSetMaster(fd);
            if (!drmIsMaster(fd)) {
                fprintf(stderr, "cal: %s: display held by another process\n", path);
                close(fd);
                continue;
            }
        }
        drmModeRes *res = drmModeGetResources(fd);
        if (!res) { close(fd); continue; }
        for (int c = 0; c < res->count_connectors; c++) {
            drmModeConnector *conn = drmModeGetConnector(fd, res->connectors[c]);
            if (!conn) continue;
            if (conn->connection == DRM_MODE_CONNECTED && conn->count_modes > 0) {
                conn_id = conn->connector_id;
                mode = conn->modes[0]; /* preferred mode */
                if (conn->encoder_id) {
                    drmModeEncoder *enc = drmModeGetEncoder(fd, conn->encoder_id);
                    if (enc) { crtc_id = enc->crtc_id; drmModeFreeEncoder(enc); }
                }
                if (!crtc_id && res->count_crtcs > 0)
                    crtc_id = res->crtcs[0];
                drmModeFreeConnector(conn);
                drmModeFreeResources(res);
                return fd;
            }
            drmModeFreeConnector(conn);
        }
        drmModeFreeResources(res);
        close(fd);
    }
    return -1;
}

static int drm_setup_fb(cal_surface *s) {
    struct drm_mode_create_dumb create = {0};
    create.width = mode.hdisplay;
    create.height = mode.vdisplay;
    create.bpp = 32;
    if (ioctl(drm_fd, DRM_IOCTL_MODE_CREATE_DUMB, &create) < 0) return -1;
    handle = create.handle;
    pitch = create.pitch;

    if (drmModeAddFB(drm_fd, mode.hdisplay, mode.vdisplay, 24, 32,
                     pitch, handle, &fb_id) < 0) return -1;

    struct drm_mode_map_dumb mreq = {0};
    mreq.handle = handle;
    if (ioctl(drm_fd, DRM_IOCTL_MODE_MAP_DUMB, &mreq) < 0) return -1;
    map_offset = mreq.offset;
    map_size = (size_t)pitch * mode.vdisplay;

    map_ptr = mmap(NULL, map_size, PROT_READ | PROT_WRITE, MAP_SHARED,
                   drm_fd, map_offset);
    if (map_ptr == MAP_FAILED) return -1;

    if (drmModeSetCrtc(drm_fd, crtc_id, fb_id, 0, 0,
                       &conn_id, 1, &mode) < 0) return -1;

    s->pixels = (uint32_t *)map_ptr;
    s->width = mode.hdisplay;
    s->height = mode.vdisplay;
    s->stride = pitch;
    return 0;
}

/* disable DPMS so screen stays on */
static void dpms_on(void) {
    drmModeConnector *conn = drmModeGetConnector(drm_fd, conn_id);
    if (!conn) return;
    for (int i = 0; i < conn->count_props; i++) {
        drmModePropertyRes *prop = drmModeGetProperty(drm_fd, conn->props[i]);
        if (!prop) continue;
        if (strcmp(prop->name, "DPMS") == 0) {
            drmModeConnectorSetProperty(drm_fd, conn_id, prop->prop_id, 0);
            drmModeFreeProperty(prop);
            break;
        }
        drmModeFreeProperty(prop);
    }
    drmModeFreeConnector(conn);
}

/* find evdev device with EV_KEY capability */
static int evdev_find(int want_key) {
    DIR *d = opendir("/dev/input");
    if (!d) return -1;
    struct dirent *ent;
    while ((ent = readdir(d))) {
        if (strncmp(ent->d_name, "event", 5) != 0) continue;
        char path[128];
        snprintf(path, sizeof(path), "/dev/input/%s", ent->d_name);
        int fd = open(path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
        if (fd < 0) continue;
        unsigned long evbits = 0;
        ioctl(fd, EVIOCGBIT(0, sizeof(evbits)), &evbits);
        if (want_key && (evbits & (1 << EV_KEY))) {
            /* check it has letter keys (not just power button) */
            unsigned long keybits[KEY_MAX / (8 * sizeof(unsigned long)) + 1];
            memset(keybits, 0, sizeof(keybits));
            ioctl(fd, EVIOCGBIT(EV_KEY, sizeof(keybits)), keybits);
            int has_letters = keybits[KEY_A / (8 * sizeof(unsigned long))]
                              & (1UL << (KEY_A % (8 * sizeof(unsigned long))));
            if (has_letters) { closedir(d); return fd; }
        }
        if (!want_key && (evbits & (1 << EV_ABS))) {
            closedir(d);
            return fd;
        }
        close(fd);
    }
    closedir(d);
    return -1;
}

/* kiosk: disable VT switching */
static void vt_lock(void) {
    tty_fd = open("/dev/tty0", O_RDWR);
    if (tty_fd < 0) tty_fd = open("/dev/tty", O_RDWR);
    if (tty_fd < 0) return;
    ioctl(tty_fd, KDGKBMODE, &prev_kbmode);
    ioctl(tty_fd, KDSKBMODE, K_OFF);
    struct vt_mode vtm = { .mode = VT_PROCESS, .waitv = 0, .relsig = 0, .acqsig = 0, .frsig = 0 };
    ioctl(tty_fd, VT_SETMODE, &vtm);
}

static void vt_unlock(void) {
    if (tty_fd >= 0 && prev_kbmode >= 0)
        ioctl(tty_fd, KDSKBMODE, prev_kbmode);
    if (tty_fd >= 0) {
        struct vt_mode vtm = { .mode = VT_AUTO, .waitv = 0, .relsig = 0, .acqsig = 0, .frsig = 0 };
        ioctl(tty_fd, VT_SETMODE, &vtm);
        ioctl(tty_fd, VT_UNLOCKSWITCH, 1);
        close(tty_fd);
        tty_fd = -1;
    }
}

static volatile sig_atomic_t cleaned_up = 0;

static void sig_restore(int sig) {
    if (!cleaned_up) {
        cleaned_up = 1;
        vt_unlock();
        platform_cleanup();
    }
    signal(sig, SIG_DFL);
    raise(sig);
}

static void unbind_fbcon(void) {
    char path[64];
    for (int i = 0; i < 8; i++) {
        snprintf(path, sizeof(path), "/sys/class/vtconsole/vtcon%d/bind", i);
        FILE *fp = fopen(path, "w");
        if (fp) { fprintf(fp, "0\n"); fclose(fp); }
    }
}

int platform_init(cal_surface *s) {
    drm_fd = drm_open();
    if (drm_fd < 0) { fprintf(stderr, "cal: no display found\n"); return -1; }
    unbind_fbcon();
    if (drm_setup_fb(s) < 0) { fprintf(stderr, "cal: framebuffer setup failed\n"); return -1; }
    dpms_on();
    kbd_fd = evdev_find(1);
    if (kbd_fd < 0) { fprintf(stderr, "cal: no keyboard found\n"); return -1; }
    mouse_fd = evdev_find(0); /* optional */

    char *kiosk = getenv("CAL_KIOSK");
    if (kiosk && kiosk[0] == '1') {
        vt_lock();
        signal(SIGTERM, sig_restore);
        signal(SIGINT, sig_restore);
        signal(SIGSEGV, sig_restore);
        signal(SIGABRT, sig_restore);
    }

    return 0;
}

int platform_event(cal_event *ev, int timeout_ms) {
    fd_set fds;
    FD_ZERO(&fds);
    int maxfd = kbd_fd;
    FD_SET(kbd_fd, &fds);
    if (mouse_fd >= 0) { FD_SET(mouse_fd, &fds); if (mouse_fd > maxfd) maxfd = mouse_fd; }

    struct timeval tv = { timeout_ms / 1000, (timeout_ms % 1000) * 1000 };
    int r = select(maxfd + 1, &fds, NULL, NULL, &tv);
    if (r <= 0) return 0;

    struct input_event ie;
    if (FD_ISSET(kbd_fd, &fds) && read(kbd_fd, &ie, sizeof(ie)) == sizeof(ie)) {
        if (ie.type == EV_KEY) {
            ev->type = CAL_KEY;
            ev->code = ie.code;
            ev->value = ie.value;
            ev->x = ev->y = 0;
            return 1;
        }
    }
    if (mouse_fd >= 0 && FD_ISSET(mouse_fd, &fds)
        && read(mouse_fd, &ie, sizeof(ie)) == sizeof(ie)) {
        if (ie.type == EV_ABS) {
            ev->type = CAL_TOUCH;
            ev->code = ie.code;
            ev->value = ie.value;
            /* caller handles coordinate mapping */
            if (ie.code == ABS_X) ev->x = ie.value;
            if (ie.code == ABS_Y) ev->y = ie.value;
            return 1;
        }
    }
    return 0;
}

void platform_flip(cal_surface *s) {
    (void)s;
    drmModeSetCrtc(drm_fd, crtc_id, fb_id, 0, 0, &conn_id, 1, &mode);
}

void platform_cleanup(void) {
    cleaned_up = 1;
    vt_unlock();
    if (map_ptr && map_ptr != MAP_FAILED) munmap(map_ptr, map_size);
    if (fb_id) drmModeRmFB(drm_fd, fb_id);
    if (handle) {
        struct drm_mode_destroy_dumb dreq = { .handle = handle };
        ioctl(drm_fd, DRM_IOCTL_MODE_DESTROY_DUMB, &dreq);
    }
    if (drm_fd >= 0) close(drm_fd);
    if (kbd_fd >= 0) close(kbd_fd);
    if (mouse_fd >= 0) close(mouse_fd);
}
