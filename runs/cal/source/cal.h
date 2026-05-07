#ifndef CAL_H
#define CAL_H

#include <stdint.h>

/* --- platform contract --- */

typedef struct {
    uint32_t *pixels;
    int width;
    int height;
    int stride; /* bytes per row */
} cal_surface;

typedef enum { CAL_KEY, CAL_MOUSE, CAL_TOUCH } cal_input_type;

typedef struct {
    cal_input_type type;
    int code;   /* KEY_* from linux/input-event-codes.h */
    int value;  /* 1=press 0=release 2=repeat */
    int x, y;   /* mouse/touch coords, 0 for keys */
} cal_event;

int  platform_init(cal_surface *s);
int  platform_event(cal_event *ev, int timeout_ms);
void platform_flip(cal_surface *s);
void platform_cleanup(void);

/* --- keycodes (linux canonical, macOS translates inbound) --- */

#ifndef KEY_ESC
#define KEY_ESC       1
#define KEY_1         2
#define KEY_2         3
#define KEY_3         4
#define KEY_4         5
#define KEY_5         6
#define KEY_MINUS     12
#define KEY_EQUAL     13
#define KEY_BACKSPACE 14
#define KEY_TAB       15
#define KEY_Q         16
#define KEY_W         17
#define KEY_E         18
#define KEY_R         19
#define KEY_T         20
#define KEY_Y         21
#define KEY_U         22
#define KEY_I         23
#define KEY_O         24
#define KEY_P         25
#define KEY_LEFTBRACE 26
#define KEY_RIGHTBRACE 27
#define KEY_ENTER     28
#define KEY_A         30
#define KEY_S         31
#define KEY_D         32
#define KEY_F         33
#define KEY_G         34
#define KEY_H         35
#define KEY_J         36
#define KEY_K         37
#define KEY_L         38
#define KEY_SEMICOLON 39
#define KEY_APOSTROPHE 40
#define KEY_GRAVE     41
#define KEY_LEFTSHIFT 42
#define KEY_BACKSLASH 43
#define KEY_Z         44
#define KEY_X         45
#define KEY_C         46
#define KEY_V         47
#define KEY_B         48
#define KEY_N         49
#define KEY_M         50
#define KEY_COMMA     51
#define KEY_DOT       52
#define KEY_SLASH     53
#define KEY_RIGHTSHIFT 54
#define KEY_SPACE     57
#define KEY_F1        59
#define KEY_F2        60
#define KEY_F3        61
#define KEY_F4        62
#define KEY_F5        63
#define KEY_UP        103
#define KEY_LEFT      105
#define KEY_RIGHT     106
#define KEY_DOWN      108
#define KEY_DELETE    111
#define KEY_0         11
#endif

/* --- modes --- */

typedef enum {
    MODE_ASK,
    MODE_EDIT,
    MODE_CARDS,
    MODE_CLINICAL,
    MODE_COUNT
} cal_mode;

/* --- colors --- */

#define COL_BG        0xFF000000
#define COL_FG        0xFFFFFFFF
#define COL_GREEN     0xFF50FA7B
#define COL_YELLOW    0xFFFFB86C
#define COL_DIM       0xFF666666
#define COL_CURSOR    0xFFFF79C6
#define COL_INPUT_BG  0xFF111111

/* --- font --- */

typedef struct {
    unsigned char *bitmap;
    int w, h;
    float scale;
    int ascent, descent, linegap;
    void *info; /* stbtt_fontinfo* */
} cal_font;

int  cal_font_init(cal_font *f, const char *ttf_path, float px);
void cal_font_free(cal_font *f);
void cal_draw_char(cal_surface *s, cal_font *f, int x, int y,
                   uint32_t cp, uint32_t color);
int  cal_draw_text(cal_surface *s, cal_font *f, int x, int y,
                   const char *text, uint32_t color);
int  cal_char_width(cal_font *f, uint32_t cp);
int  cal_line_height(cal_font *f);

/* --- gap buffer --- */

#define GAP_INIT 4096

typedef struct {
    char *buf;
    int gap_start;
    int gap_end;
    int cap;
} gap_buf;

void gap_init(gap_buf *g);
void gap_free(gap_buf *g);
void gap_insert(gap_buf *g, char c);
void gap_insert_str(gap_buf *g, const char *s, int len);
void gap_delete(gap_buf *g);
void gap_backspace(gap_buf *g);
void gap_move(gap_buf *g, int pos);
int  gap_length(gap_buf *g);
char gap_char_at(gap_buf *g, int pos);
int  gap_pos(gap_buf *g);
void gap_get_text(gap_buf *g, char *out, int max);

/* --- inference --- */

int  cal_infer(const char *host, int port, const char *prompt,
               char *resp, int resp_max);
int  cal_infer_stream(const char *host, int port, const char *prompt,
                      int *sock_out);
int  cal_infer_recv(int sock, char *chunk, int chunk_max);

/* --- session log --- */

void cal_log_init(const char *program);
void cal_log_trial(const char *program, int trial,
                   const char *stimulus, const char *response,
                   int latency_ms, int correct);

#endif
