/* cal.c — framebuffer computing for humans
   named for Callum. the first user.

   Linux:  cc -O2 -o cal cal.c platform_linux.c -ldrm
   macOS:  cc -O2 -o cal cal.c platform_macos.m -framework Cocoa
*/

#include "cal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <errno.h>
#include <sys/select.h>

#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

/* ================================================================
   json escape (shared — every inference call site uses this)
   ================================================================ */

static int json_escape(const char *in, char *out, int out_max) {
    int o = 0;
    for (int i = 0; in[i] && o < out_max - 6; i++) {
        switch (in[i]) {
        case '"':  out[o++] = '\\'; out[o++] = '"'; break;
        case '\\': out[o++] = '\\'; out[o++] = '\\'; break;
        case '\n': out[o++] = '\\'; out[o++] = 'n'; break;
        case '\r': out[o++] = '\\'; out[o++] = 'r'; break;
        case '\t': out[o++] = '\\'; out[o++] = 't'; break;
        default:
            if ((unsigned char)in[i] < 0x20) {
                o += snprintf(out + o, out_max - o, "\\u%04x", in[i]);
            } else {
                out[o++] = in[i];
            }
        }
    }
    out[o] = 0;
    return o;
}

/* ================================================================
   font rendering (stb_truetype)
   ================================================================ */

int cal_font_init(cal_font *f, const char *ttf_path, float px) {
    FILE *fp = fopen(ttf_path, "rb");
    if (!fp) return -1;
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    unsigned char *data = malloc(sz);
    if (!data) { fclose(fp); return -1; }
    if ((long)fread(data, 1, sz, fp) != sz) {
        free(data); fclose(fp); return -1;
    }
    fclose(fp);

    f->info = malloc(sizeof(stbtt_fontinfo));
    if (!stbtt_InitFont((stbtt_fontinfo *)f->info, data, 0)) {
        free(data); free(f->info); return -1;
    }
    f->scale = stbtt_ScaleForPixelHeight((stbtt_fontinfo *)f->info, px);
    stbtt_GetFontVMetrics((stbtt_fontinfo *)f->info,
                          &f->ascent, &f->descent, &f->linegap);
    f->ascent = (int)(f->ascent * f->scale);
    f->descent = (int)(f->descent * f->scale);
    f->linegap = (int)(f->linegap * f->scale);
    f->bitmap = data; /* keep the ttf data alive */
    f->h = f->ascent - f->descent + f->linegap;
    f->w = 0; /* variable width */
    return 0;
}

void cal_font_free(cal_font *f) {
    free(f->bitmap);
    free(f->info);
    memset(f, 0, sizeof(*f));
}

int cal_char_width(cal_font *f, uint32_t cp) {
    int ax, lsb;
    stbtt_GetCodepointHMetrics((stbtt_fontinfo *)f->info, cp, &ax, &lsb);
    return (int)(ax * f->scale);
}

int cal_line_height(cal_font *f) {
    return f->h;
}

void cal_draw_char(cal_surface *s, cal_font *f, int x, int y,
                   uint32_t cp, uint32_t color) {
    int w, h, xoff, yoff;
    unsigned char *bmp = stbtt_GetCodepointBitmap(
        (stbtt_fontinfo *)f->info, 0, f->scale, cp, &w, &h, &xoff, &yoff);
    if (!bmp) return;

    int baseline = y + f->ascent;
    uint8_t cr = (color >> 16) & 0xFF;
    uint8_t cg = (color >> 8) & 0xFF;
    uint8_t cb = color & 0xFF;

    for (int row = 0; row < h; row++) {
        int sy = baseline + yoff + row;
        if (sy < 0 || sy >= s->height) continue;
        uint32_t *scanline = (uint32_t *)((uint8_t *)s->pixels + sy * s->stride);
        for (int col = 0; col < w; col++) {
            int sx = x + xoff + col;
            if (sx < 0 || sx >= s->width) continue;
            uint8_t a = bmp[row * w + col];
            if (a == 0) continue;
            if (a == 255) {
                scanline[sx] = color;
            } else {
                uint32_t dst = scanline[sx];
                uint8_t dr = (dst >> 16) & 0xFF;
                uint8_t dg = (dst >> 8) & 0xFF;
                uint8_t db = dst & 0xFF;
                uint8_t ro = dr + (((int)cr - (int)dr) * a / 255);
                uint8_t go = dg + (((int)cg - (int)dg) * a / 255);
                uint8_t bo = db + (((int)cb - (int)db) * a / 255);
                scanline[sx] = 0xFF000000 | (ro << 16) | (go << 8) | bo;
            }
        }
    }
    stbtt_FreeBitmap(bmp, NULL);
}

int cal_draw_text(cal_surface *s, cal_font *f, int x, int y,
                  const char *text, uint32_t color) {
    int cx = x;
    const unsigned char *p = (const unsigned char *)text;
    while (*p) {
        uint32_t cp;
        /* minimal utf-8 decode */
        if (*p < 0x80) { cp = *p++; }
        else if ((*p & 0xE0) == 0xC0) {
            cp = (*p++ & 0x1F) << 6;
            if (*p) cp |= (*p++ & 0x3F);
        } else if ((*p & 0xF0) == 0xE0) {
            cp = (*p++ & 0x0F) << 12;
            if (*p) cp |= (*p++ & 0x3F) << 6;
            if (*p) cp |= (*p++ & 0x3F);
        } else if ((*p & 0xF8) == 0xF0) {
            cp = (*p++ & 0x07) << 18;
            if (*p) cp |= (*p++ & 0x3F) << 12;
            if (*p) cp |= (*p++ & 0x3F) << 6;
            if (*p) cp |= (*p++ & 0x3F);
        } else { p++; continue; }

        if (cp == '\n') break;
        cal_draw_char(s, f, cx, y, cp, color);
        cx += cal_char_width(f, cp);
    }
    return cx - x;
}

/* ================================================================
   gap buffer
   ================================================================ */

void gap_init(gap_buf *g) {
    g->cap = GAP_INIT;
    g->buf = malloc(g->cap);
    if (!g->buf) { g->cap = 0; return; }
    g->gap_start = 0;
    g->gap_end = g->cap;
}

void gap_free(gap_buf *g) { free(g->buf); }

static int gap_grow(gap_buf *g) {
    int new_cap = g->cap * 2;
    char *new_buf = malloc(new_cap);
    if (!new_buf) return -1;
    int tail = g->cap - g->gap_end;
    memcpy(new_buf, g->buf, g->gap_start);
    memcpy(new_buf + new_cap - tail, g->buf + g->gap_end, tail);
    g->gap_end = new_cap - tail;
    g->cap = new_cap;
    free(g->buf);
    g->buf = new_buf;
    return 0;
}

void gap_insert(gap_buf *g, char c) {
    if (g->gap_start == g->gap_end && gap_grow(g) < 0) return;
    g->buf[g->gap_start++] = c;
}

void gap_insert_str(gap_buf *g, const char *s, int len) {
    for (int i = 0; i < len; i++) gap_insert(g, s[i]);
}

void gap_delete(gap_buf *g) {
    if (g->gap_end < g->cap) g->gap_end++;
}

void gap_backspace(gap_buf *g) {
    if (g->gap_start > 0) g->gap_start--;
}

void gap_move(gap_buf *g, int pos) {
    int len = gap_length(g);
    if (pos < 0) pos = 0;
    if (pos > len) pos = len;
    while (g->gap_start < pos) {
        g->buf[g->gap_start] = g->buf[g->gap_end];
        g->gap_start++;
        g->gap_end++;
    }
    while (g->gap_start > pos) {
        g->gap_start--;
        g->gap_end--;
        g->buf[g->gap_end] = g->buf[g->gap_start];
    }
}

int gap_length(gap_buf *g) {
    return g->cap - (g->gap_end - g->gap_start);
}

char gap_char_at(gap_buf *g, int pos) {
    if (pos < g->gap_start) return g->buf[pos];
    return g->buf[g->gap_end + (pos - g->gap_start)];
}

int gap_pos(gap_buf *g) { return g->gap_start; }

void gap_get_text(gap_buf *g, char *out, int max) {
    int len = gap_length(g);
    if (len >= max) len = max - 1;
    for (int i = 0; i < len; i++) out[i] = gap_char_at(g, i);
    out[len] = 0;
}

/* ================================================================
   inference (direct socket to llama.cpp)
   ================================================================ */

static int tcp_connect(const char *host, int port) {
    char port_str[8];
    snprintf(port_str, sizeof(port_str), "%d", port);
    struct addrinfo hints = {0}, *res;
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    if (getaddrinfo(host, port_str, &hints, &res) != 0) return -1;
    int fd = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (fd < 0) { freeaddrinfo(res); return -1; }
    if (connect(fd, res->ai_addr, res->ai_addrlen) < 0) {
        close(fd); freeaddrinfo(res); return -1;
    }
    freeaddrinfo(res);
    return fd;
}

int cal_infer(const char *host, int port, const char *prompt,
              char *resp, int resp_max) {
    int fd = tcp_connect(host, port);
    if (fd < 0) return -1;

    char *escaped = malloc(strlen(prompt) * 6 + 1);
    if (!escaped) { close(fd); return -1; }
    json_escape(prompt, escaped, strlen(prompt) * 6 + 1);

    char *body = malloc(strlen(escaped) + 512);
    if (!body) { free(escaped); close(fd); return -1; }
    int blen = sprintf(body,
        "{\"messages\":[{\"role\":\"user\",\"content\":\"%s\"}],"
        "\"max_tokens\":4096,\"stream\":false}", escaped);
    free(escaped);

    char *req = malloc(blen + 256);
    if (!req) { free(body); close(fd); return -1; }
    int rlen = sprintf(req,
        "POST /v1/chat/completions HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n%s",
        host, port, blen, body);

    int sent = 0;
    while (sent < rlen) {
        int n = write(fd, req + sent, rlen - sent);
        if (n <= 0) { free(req); free(body); close(fd); return -1; }
        sent += n;
    }
    free(req);
    free(body);

    int buf_size = resp_max + 4096;
    char *buf = malloc(buf_size + 1);
    if (!buf) { close(fd); return -1; }
    int total = 0, n;
    while (total < buf_size
           && (n = read(fd, buf + total, buf_size - total)) > 0)
        total += n;
    buf[total] = 0;
    close(fd);

    /* find response body (after \r\n\r\n) */
    char *json = strstr(buf, "\r\n\r\n");
    if (!json) { free(buf); return -1; }
    json += 4;

    /* extract content from {"choices":[{"message":{"content":"..."}}]} */
    char *content = strstr(json, "\"content\":\"");
    if (!content) { free(buf); return -1; }
    content += 11;
    char *end = content;
    int out = 0;
    while (*end && out < resp_max - 1) {
        if (*end == '\\' && *(end + 1) == '"') { resp[out++] = '"'; end += 2; }
        else if (*end == '\\' && *(end + 1) == 'n') { resp[out++] = '\n'; end += 2; }
        else if (*end == '\\' && *(end + 1) == '\\') { resp[out++] = '\\'; end += 2; }
        else if (*end == '"') break;
        else resp[out++] = *end++;
    }
    resp[out] = 0;
    free(buf);
    return out;
}

/* streaming: returns socket fd, caller reads SSE chunks */
int cal_infer_stream(const char *host, int port, const char *prompt,
                     int *sock_out) {
    int fd = tcp_connect(host, port);
    if (fd < 0) return -1;

    char *escaped = malloc(strlen(prompt) * 6 + 1);
    if (!escaped) { close(fd); return -1; }
    json_escape(prompt, escaped, strlen(prompt) * 6 + 1);

    char *body = malloc(strlen(escaped) + 512);
    if (!body) { free(escaped); close(fd); return -1; }
    int blen = sprintf(body,
        "{\"messages\":[{\"role\":\"user\",\"content\":\"%s\"}],"
        "\"max_tokens\":4096,\"stream\":true}", escaped);
    free(escaped);

    char *req = malloc(blen + 256);
    if (!req) { free(body); close(fd); return -1; }
    int rlen = sprintf(req,
        "POST /v1/chat/completions HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n%s",
        host, port, blen, body);

    int sent = 0;
    while (sent < rlen) {
        int n = write(fd, req + sent, rlen - sent);
        if (n <= 0) { free(req); free(body); close(fd); return -1; }
        sent += n;
    }
    free(req);
    free(body);
    *sock_out = fd;
    return 0;
}

int cal_infer_recv(int sock, char *chunk, int chunk_max) {
    static char buf[8192];
    static int buf_len = 0;
    if (sock < 0) { buf_len = 0; return 0; }

    int space = (int)sizeof(buf) - buf_len - 1;
    if (space <= 0) buf_len = 0, space = (int)sizeof(buf) - 1;
    int n = read(sock, buf + buf_len, space);
    if (n <= 0) { buf_len = 0; return -1; }
    buf_len += n;
    buf[buf_len] = 0;

    int out = 0;
    char *p = buf;
    char *last_consumed = buf;
    while ((p = strstr(p, "\"content\":\""))) {
        p += 11;
        while (*p && *p != '"' && out < chunk_max - 1) {
            if (*p == '\\' && *(p + 1) == 'n') { chunk[out++] = '\n'; p += 2; }
            else if (*p == '\\' && *(p + 1) == '"') { chunk[out++] = '"'; p += 2; }
            else if (*p == '\\' && *(p + 1) == '\\') { chunk[out++] = '\\'; p += 2; }
            else chunk[out++] = *p++;
        }
        if (*p == '"') { p++; last_consumed = p; }
        else { last_consumed = p - 11; break; }
    }
    /* shift unconsumed data to front */
    if (last_consumed > buf) {
        int remain = buf_len - (int)(last_consumed - buf);
        if (remain > 0) memmove(buf, last_consumed, remain);
        buf_len = remain > 0 ? remain : 0;
    }
    chunk[out] = 0;
    return out;
}

/* ================================================================
   tool-calling inference (non-streaming, multi-turn)
   ================================================================ */

static const char *CAL_TOOLS =
    "[{\"type\":\"function\",\"function\":{\"name\":\"run_command\","
    "\"description\":\"Run a shell command on the local machine and return its output\","
    "\"parameters\":{\"type\":\"object\",\"properties\":{\"command\":{\"type\":\"string\",\"description\":\"The shell command to execute\"}},"
    "\"required\":[\"command\"]}}},"
    "{\"type\":\"function\",\"function\":{\"name\":\"read_file\","
    "\"description\":\"Read a file from the filesystem\","
    "\"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\",\"description\":\"File path to read\"}},"
    "\"required\":[\"path\"]}}},"
    "{\"type\":\"function\",\"function\":{\"name\":\"list_dir\","
    "\"description\":\"List directory contents\","
    "\"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\",\"description\":\"Directory path\"}},"
    "\"required\":[\"path\"]}}}]";

static int http_post_json(const char *host, int port, const char *body, int blen,
                          char *resp, int resp_max) {
    int fd = tcp_connect(host, port);
    if (fd < 0) return -1;
    char hdr[512];
    int hlen = snprintf(hdr, sizeof(hdr),
        "POST /v1/chat/completions HTTP/1.1\r\n"
        "Host: %s:%d\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: %d\r\n"
        "Connection: close\r\n\r\n", host, port, blen);
    int s = 0;
    while (s < hlen) { int w = write(fd, hdr + s, hlen - s); if (w <= 0) { close(fd); return -1; } s += w; }
    s = 0;
    while (s < blen) { int w = write(fd, body + s, blen - s); if (w <= 0) { close(fd); return -1; } s += w; }
    int total = 0, n;
    while (total < resp_max - 1 && (n = read(fd, resp + total, resp_max - 1 - total)) > 0)
        total += n;
    resp[total] = 0;
    close(fd);
    char *json = strstr(resp, "\r\n\r\n");
    if (!json) return -1;
    json += 4;
    memmove(resp, json, strlen(json) + 1);
    return (int)strlen(resp);
}

static char *find_json_string(const char *json, const char *key) {
    char needle[128];
    snprintf(needle, sizeof(needle), "\"%s\":\"", key);
    char *p = strstr(json, needle);
    if (!p) return NULL;
    p += strlen(needle);
    static char buf[65536];
    int o = 0;
    while (*p && *p != '"' && o < (int)sizeof(buf) - 1) {
        if (*p == '\\' && *(p+1) == '"') { buf[o++] = '"'; p += 2; }
        else if (*p == '\\' && *(p+1) == 'n') { buf[o++] = '\n'; p += 2; }
        else if (*p == '\\' && *(p+1) == '\\') { buf[o++] = '\\'; p += 2; }
        else if (*p == '\\' && *(p+1) == 't') { buf[o++] = '\t'; p += 2; }
        else buf[o++] = *p++;
    }
    buf[o] = 0;
    return buf;
}

static int execute_tool(const char *name, const char *args_json,
                        char *result, int result_max) {
    const char *arg = NULL;
    if (strcmp(name, "run_command") == 0)
        arg = find_json_string(args_json, "command");
    else if (strcmp(name, "read_file") == 0)
        arg = find_json_string(args_json, "path");
    else if (strcmp(name, "list_dir") == 0)
        arg = find_json_string(args_json, "path");

    if (!arg) { strncpy(result, "missing argument", result_max); return -1; }

    char cmd[4096];
    if (strcmp(name, "run_command") == 0)
        snprintf(cmd, sizeof(cmd), "%s", arg);
    else if (strcmp(name, "read_file") == 0)
        snprintf(cmd, sizeof(cmd), "cat '%s'", arg);
    else if (strcmp(name, "list_dir") == 0)
        snprintf(cmd, sizeof(cmd), "ls -la '%s'", arg);
    else {
        strncpy(result, "unknown tool", result_max);
        return -1;
    }

    FILE *fp = popen(cmd, "r");
    if (!fp) { strncpy(result, "command failed", result_max); return -1; }
    int len = fread(result, 1, result_max - 1, fp);
    result[len] = 0;
    pclose(fp);
    return len;
}

int cal_infer_tools(const char *host, int port, const char *prompt,
                    char *output, int output_max) {
    char *escaped = malloc(strlen(prompt) * 6 + 1);
    if (!escaped) return -1;
    json_escape(prompt, escaped, strlen(prompt) * 6 + 1);

    /* conversation buffer: up to 5 turns of tool calling */
    char *messages = malloc(256 * 1024);
    if (!messages) { free(escaped); return -1; }
    snprintf(messages, 256 * 1024,
        "[{\"role\":\"user\",\"content\":\"%s\"}]", escaped);
    free(escaped);

    char *resp = malloc(128 * 1024);
    char *body = malloc(384 * 1024);
    if (!resp || !body) { free(messages); free(resp); free(body); return -1; }

    int rounds = 0;
    while (rounds < 5) {
        rounds++;
        int blen = snprintf(body, 384 * 1024,
            "{\"messages\":%s,\"tools\":%s,\"max_tokens\":4096,\"stream\":false}",
            messages, CAL_TOOLS);

        int rlen = http_post_json(host, port, body, blen, resp, 128 * 1024);
        if (rlen <= 0) break;

        /* check for tool_calls */
        char *tc = strstr(resp, "\"tool_calls\":");
        char *content = NULL;
        if (!tc || strncmp(tc + 13, "null", 4) == 0) {
            content = find_json_string(resp, "content");
            if (content) {
                int len = strlen(content);
                if (len >= output_max) len = output_max - 1;
                memcpy(output, content, len);
                output[len] = 0;
                free(messages); free(resp); free(body);
                return len;
            }
            break;
        }

        /* parse tool call: find name and arguments */
        char *tc_name = find_json_string(tc, "name");
        if (!tc_name) break;
        char name_copy[64];
        strncpy(name_copy, tc_name, sizeof(name_copy) - 1);
        name_copy[sizeof(name_copy) - 1] = 0;

        /* extract arguments JSON object */
        char *args_str = strstr(tc, "\"arguments\":");
        char args_json[4096] = "{}";
        if (args_str) {
            args_str += 12;
            /* arguments may be a string (escaped JSON) or object */
            if (*args_str == '"') {
                char *decoded = find_json_string(tc, "arguments");
                if (decoded) snprintf(args_json, sizeof(args_json), "%s", decoded);
            } else if (*args_str == '{') {
                int depth = 0, i = 0;
                for (; args_str[i] && i < (int)sizeof(args_json) - 1; i++) {
                    args_json[i] = args_str[i];
                    if (args_str[i] == '{') depth++;
                    if (args_str[i] == '}') { depth--; if (depth == 0) { i++; break; } }
                }
                args_json[i] = 0;
            }
        }

        /* extract tool_call id */
        char *tc_id_str = find_json_string(tc, "id");
        char tc_id[64] = "call_0";
        if (tc_id_str) strncpy(tc_id, tc_id_str, sizeof(tc_id) - 1);

        /* execute tool */
        char tool_result[65536];
        execute_tool(name_copy, args_json, tool_result, sizeof(tool_result));

        /* escape tool result and rebuild messages */
        char *esc_result = malloc(strlen(tool_result) * 6 + 1);
        if (!esc_result) break;
        json_escape(tool_result, esc_result, strlen(tool_result) * 6 + 1);

        /* escape the arguments for the assistant message */
        char *esc_args = malloc(strlen(args_json) * 6 + 1);
        if (!esc_args) { free(esc_result); break; }
        json_escape(args_json, esc_args, strlen(args_json) * 6 + 1);

        /* append assistant tool_call + tool result to messages */
        int mlen = strlen(messages);
        snprintf(messages + mlen - 1, 256 * 1024 - mlen,
            ",{\"role\":\"assistant\",\"content\":null,\"tool_calls\":[{\"id\":\"%s\",\"type\":\"function\",\"function\":{\"name\":\"%s\",\"arguments\":\"%s\"}}]},"
            "{\"role\":\"tool\",\"tool_call_id\":\"%s\",\"content\":\"%s\"}]",
            tc_id, name_copy, esc_args, tc_id, esc_result);
        free(esc_result);
        free(esc_args);
    }

    free(messages); free(resp); free(body);
    strncpy(output, "(no response)", output_max);
    return -1;
}

/* ================================================================
   session log (TSV)
   ================================================================ */

static char log_path[512];

void cal_log_init(const char *program) {
    char *home = getenv("HOME");
    if (!home) home = "/tmp";
    char dir[512];
    snprintf(dir, sizeof(dir), "%s/.subtract/sessions", home);
    mkdir(dir, 0755);

    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    snprintf(log_path, sizeof(log_path),
             "%s/cal-%04d%02d%02d-%s.tsv",
             dir, t->tm_year + 1900, t->tm_mon + 1, t->tm_mday, program);
}

void cal_log_trial(const char *program, int trial,
                   const char *stimulus, const char *response,
                   int latency_ms, int correct) {
    FILE *fp = fopen(log_path, "a");
    if (!fp) return;
    time_t now = time(NULL);
    struct tm *t = gmtime(&now);
    fprintf(fp, "%04d-%02d-%02dT%02d:%02d:%02dZ\t%s\t%d\t%s\t%s\t%d\t%d\n",
            t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
            t->tm_hour, t->tm_min, t->tm_sec,
            program, trial, stimulus, response, latency_ms, correct);
    fclose(fp);
}

/* ================================================================
   rendering helpers
   ================================================================ */

static void fill_rect(cal_surface *s, int x, int y, int w, int h, uint32_t c) {
    for (int row = y; row < y + h && row < s->height; row++) {
        if (row < 0) continue;
        uint32_t *line = (uint32_t *)((uint8_t *)s->pixels + row * s->stride);
        for (int col = x; col < x + w && col < s->width; col++) {
            if (col < 0) continue;
            line[col] = c;
        }
    }
}

static void clear(cal_surface *s) {
    for (int y = 0; y < s->height; y++) {
        uint32_t *line = (uint32_t *)((uint8_t *)s->pixels + y * s->stride);
        for (int x = 0; x < s->width; x++) line[x] = COL_BG;
    }
}

/* ================================================================
   vi0 editor state
   ================================================================ */

typedef enum { VI_NORMAL, VI_INSERT, VI_COMMAND } vi_state;

typedef struct {
    gap_buf buf;
    vi_state state;
    int cx, cy;         /* cursor position in text (col, line) */
    int scroll;         /* first visible line */
    char cmd[256];      /* ex command buffer */
    int cmd_len;
    char yank[4096];    /* yank register */
    int yank_len;
    char filename[512];
    int dirty;
} vi_ctx;

static void vi_init(vi_ctx *v) {
    gap_init(&v->buf);
    v->state = VI_NORMAL;
    v->cx = v->cy = v->scroll = 0;
    v->cmd_len = 0;
    v->yank_len = 0;
    v->filename[0] = 0;
    v->dirty = 0;
}

static int vi_line_count(vi_ctx *v) {
    int len = gap_length(&v->buf);
    int lines = 1;
    for (int i = 0; i < len; i++)
        if (gap_char_at(&v->buf, i) == '\n') lines++;
    return lines;
}

static int vi_line_start(vi_ctx *v, int line) {
    int len = gap_length(&v->buf);
    int cur = 0;
    for (int i = 0; i < len && cur < line; i++)
        if (gap_char_at(&v->buf, i) == '\n') cur++;
    if (cur < line) return len;
    /* find start of this line */
    int pos = 0;
    cur = 0;
    for (int i = 0; i < len; i++) {
        if (cur == line) { pos = i; break; }
        if (gap_char_at(&v->buf, i) == '\n') cur++;
    }
    if (cur < line) return len;
    return pos;
}

static int vi_line_len(vi_ctx *v, int line) {
    int start = vi_line_start(v, line);
    int len = gap_length(&v->buf);
    int end = start;
    while (end < len && gap_char_at(&v->buf, end) != '\n') end++;
    return end - start;
}

static int vi_cursor_pos(vi_ctx *v) {
    int start = vi_line_start(v, v->cy);
    int ll = vi_line_len(v, v->cy);
    int col = v->cx;
    if (col > ll) col = ll;
    return start + col;
}

static void vi_save(vi_ctx *v) {
    if (!v->filename[0]) return;
    FILE *fp = fopen(v->filename, "w");
    if (!fp) return;
    int len = gap_length(&v->buf);
    for (int i = 0; i < len; i++) fputc(gap_char_at(&v->buf, i), fp);
    fclose(fp);
    v->dirty = 0;
}

static void vi_load(vi_ctx *v, const char *path) {
    strncpy(v->filename, path, sizeof(v->filename) - 1);
    FILE *fp = fopen(path, "r");
    if (!fp) return;
    int c;
    while ((c = fgetc(fp)) != EOF) gap_insert(&v->buf, c);
    fclose(fp);
    gap_move(&v->buf, 0);
    v->cx = v->cy = 0;
}

/* ================================================================
   ask mode state
   ================================================================ */

typedef struct {
    char input[4096];
    int input_len;
    char last_query[4096];
    int last_query_len;
    char output[65536];
    int output_len;
    int streaming;
    int infer_sock;
    int output_scroll;
    struct timespec t_sent;
    struct timespec t_first_token;
    int token_count;
    int ttft_ms;
    double tok_per_sec;
} ask_ctx;

/* ================================================================
   main application
   ================================================================ */

typedef struct {
    cal_surface surface;
    cal_font font;
    cal_font font_large;
    cal_mode mode;
    vi_ctx vi;
    ask_ctx ask;
    int running;
    int shift;
    char infer_host[64];
    int infer_port;
    int margin;
} cal_app;

static void draw_status(cal_app *app) {
    int sh = cal_line_height(&app->font);
    int y = app->surface.height - sh - 4;
    fill_rect(&app->surface, 0, y, app->surface.width, sh + 4, COL_INPUT_BG);

    const char *mode_str;
    uint32_t mode_col;
    switch (app->mode) {
    case MODE_ASK:  mode_str = " ASK";  mode_col = COL_GREEN; break;
    case MODE_EDIT: mode_str = " EDIT"; mode_col = COL_YELLOW; break;
    case MODE_CARDS: mode_str = " CARDS"; mode_col = COL_GREEN; break;
    case MODE_CLINICAL: mode_str = " CLINICAL"; mode_col = COL_GREEN; break;
    default: mode_str = " CAL"; mode_col = COL_FG; break;
    }
    int tx = cal_draw_text(&app->surface, &app->font, 4, y + 2, mode_str, mode_col) + 4;

    if (app->mode == MODE_ASK && (app->ask.ttft_ms > 0 || app->ask.tok_per_sec > 0.0)) {
        char stats[128];
        snprintf(stats, sizeof(stats), "  ttft %dms  %.1f tok/s  %d tokens",
                 app->ask.ttft_ms, app->ask.tok_per_sec, app->ask.token_count);
        cal_draw_text(&app->surface, &app->font, tx, y + 2, stats, COL_DIM);
    }

    if (app->mode == MODE_EDIT) {
        char info[128];
        const char *state_str = "NORMAL";
        if (app->vi.state == VI_INSERT) state_str = "INSERT";
        if (app->vi.state == VI_COMMAND) state_str = "COMMAND";
        snprintf(info, sizeof(info), " %s  %d:%d  %s",
                 state_str, app->vi.cy + 1, app->vi.cx + 1,
                 app->vi.filename[0] ? app->vi.filename : "[scratch]");
        cal_draw_text(&app->surface, &app->font, tx, y + 2, info, COL_DIM);
    }
}

static void draw_ask_wrap(cal_app *app, const unsigned char *p, int *y,
                          int max_y, int m, int max_x, uint32_t col) {
    int lh = cal_line_height(&app->font);
    int x = m;
    while (*p && *y < max_y) {
        if (*p == '\n') { x = m; *y += lh; p++; continue; }
        const unsigned char *ws = p;
        int ww = 0;
        while (*ws && *ws != '\n' && *ws != ' ') {
            uint32_t cp;
            if (*ws < 0x80) cp = *ws++;
            else if ((*ws & 0xE0) == 0xC0) { cp = (*ws++ & 0x1F) << 6; if (*ws) cp |= (*ws++ & 0x3F); }
            else if ((*ws & 0xF0) == 0xE0) { cp = (*ws++ & 0x0F) << 12; if (*ws) cp |= (*ws++ & 0x3F) << 6; if (*ws) cp |= (*ws++ & 0x3F); }
            else if ((*ws & 0xF8) == 0xF0) { cp = (*ws++ & 0x07) << 18; if (*ws) cp |= (*ws++ & 0x3F) << 12; if (*ws) cp |= (*ws++ & 0x3F) << 6; if (*ws) cp |= (*ws++ & 0x3F); }
            else { ws++; continue; }
            ww += cal_char_width(&app->font, cp);
        }
        if (x + ww > max_x && x > m) { x = m; *y += lh; }
        if (*y >= max_y) break;
        while (p < ws) {
            uint32_t cp;
            if (*p < 0x80) cp = *p++;
            else if ((*p & 0xE0) == 0xC0) { cp = (*p++ & 0x1F) << 6; if (*p) cp |= (*p++ & 0x3F); }
            else if ((*p & 0xF0) == 0xE0) { cp = (*p++ & 0x0F) << 12; if (*p) cp |= (*p++ & 0x3F) << 6; if (*p) cp |= (*p++ & 0x3F); }
            else if ((*p & 0xF8) == 0xF0) { cp = (*p++ & 0x07) << 18; if (*p) cp |= (*p++ & 0x3F) << 12; if (*p) cp |= (*p++ & 0x3F) << 6; if (*p) cp |= (*p++ & 0x3F); }
            else { p++; continue; }
            cal_draw_char(&app->surface, &app->font, x, *y, cp, col);
            x += cal_char_width(&app->font, cp);
        }
        if (*p == ' ') { x += cal_char_width(&app->font, ' '); p++; }
    }
}

static void draw_ask(cal_app *app) {
    int lh = cal_line_height(&app->font);
    int m = app->margin;
    int max_x = app->surface.width - m;

    /* header at top */
    cal_draw_text(&app->surface, &app->font_large, m, m, "cal.c", COL_FG);
    cal_draw_text(&app->surface, &app->font, m, m + cal_line_height(&app->font_large) + 4,
                  "subtract your questions, ask about anything", COL_DIM);

    /* input at bottom, above status bar */
    int status_h = lh + 4;
    int input_y = app->surface.height - status_h - lh - 16;
    int prompt_w = cal_draw_text(&app->surface, &app->font, 0, input_y + 4, "> ", COL_DIM);
    fill_rect(&app->surface, prompt_w, input_y, app->surface.width - prompt_w - m, lh + 8, COL_INPUT_BG);
    cal_draw_text(&app->surface, &app->font, prompt_w + 4, input_y + 4,
                  app->ask.input_len ? app->ask.input : "", COL_FG);
    if (!app->ask.streaming) {
        int cw = 0;
        for (int i = 0; i < app->ask.input_len; i++)
            cw += cal_char_width(&app->font, app->ask.input[i]);
        fill_rect(&app->surface, prompt_w + 4 + cw, input_y + 4, 2, lh, COL_CURSOR);
    }

    /* last query + output below header */
    int y = m + cal_line_height(&app->font_large) + lh + 16;
    int max_y = input_y - lh - 12;
    if (app->ask.last_query_len > 0) {
        cal_draw_text(&app->surface, &app->font, m, y, app->ask.last_query, COL_FG);
        y += lh + 8;
    }
    if (app->ask.output_len > 0) {
        uint32_t col = app->ask.streaming ? COL_YELLOW : COL_GREEN;
        draw_ask_wrap(app, (const unsigned char *)app->ask.output,
                      &y, max_y, m, max_x, col);
    }
}

static void draw_edit(cal_app *app) {
    int lh = cal_line_height(&app->font);
    int m = app->margin;
    int lines_visible = (app->surface.height - lh - 8) / lh;
    int total = vi_line_count(&app->vi);

    /* adjust scroll */
    if (app->vi.cy < app->vi.scroll) app->vi.scroll = app->vi.cy;
    if (app->vi.cy >= app->vi.scroll + lines_visible)
        app->vi.scroll = app->vi.cy - lines_visible + 1;

    for (int i = 0; i < lines_visible && (i + app->vi.scroll) < total; i++) {
        int line = i + app->vi.scroll;
        int start = vi_line_start(&app->vi, line);
        int ll = vi_line_len(&app->vi, line);

        /* line number */
        char num[8];
        snprintf(num, sizeof(num), "%4d ", line + 1);
        cal_draw_text(&app->surface, &app->font, 0, i * lh, num, COL_DIM);

        /* line content */
        char text[1024];
        int tl = ll < (int)sizeof(text) - 1 ? ll : (int)sizeof(text) - 1;
        for (int j = 0; j < tl; j++)
            text[j] = gap_char_at(&app->vi.buf, start + j);
        text[tl] = 0;
        cal_draw_text(&app->surface, &app->font, m, i * lh, text, COL_FG);

        /* cursor */
        if (line == app->vi.cy) {
            int col = app->vi.cx;
            if (col > ll) col = ll;
            int cx = m;
            for (int j = 0; j < col && j < tl; j++)
                cx += cal_char_width(&app->font, text[j]);
            if (app->vi.state == VI_INSERT) {
                fill_rect(&app->surface, cx, i * lh, 2, lh, COL_CURSOR);
            } else {
                int cw = col < tl ? cal_char_width(&app->font, text[col]) : 8;
                fill_rect(&app->surface, cx, i * lh, cw, lh, COL_CURSOR);
            }
        }
    }

    /* ex command line */
    if (app->vi.state == VI_COMMAND) {
        int y = app->surface.height - lh * 2 - 4;
        fill_rect(&app->surface, 0, y, app->surface.width, lh + 4, COL_INPUT_BG);
        char display[260];
        snprintf(display, sizeof(display), ":%s", app->vi.cmd);
        cal_draw_text(&app->surface, &app->font, 4, y + 2, display, COL_FG);
    }
}

/* ================================================================
   input handling — ask mode
   ================================================================ */

static void handle_ask_key(cal_app *app, int code, int value) {
    if (value == 0) return;
    int shift = app->shift;

    if (code == KEY_ESC) {
        if (app->ask.streaming && app->ask.infer_sock >= 0) {
            close(app->ask.infer_sock);
            app->ask.infer_sock = -1;
        }
        app->ask.streaming = 0;
        app->ask.input_len = 0;
        app->ask.output_len = 0;
        app->ask.last_query_len = 0;
        return;
    }

    if (app->ask.streaming) return;

    if (code == KEY_ENTER) {
        if (app->ask.input_len == 0) return;
        app->ask.input[app->ask.input_len] = 0;
        app->ask.output_len = 0;
        app->ask.output[0] = 0;

        memcpy(app->ask.last_query, app->ask.input, app->ask.input_len);
        app->ask.last_query_len = app->ask.input_len;
        app->ask.last_query[app->ask.last_query_len] = 0;
        char query[sizeof(app->ask.input)];
        memcpy(query, app->ask.input, app->ask.input_len);
        query[app->ask.input_len] = 0;
        app->ask.input_len = 0;
        app->ask.input[0] = 0;

        clock_gettime(CLOCK_MONOTONIC, &app->ask.t_sent);
        app->ask.t_first_token.tv_sec = 0;
        app->ask.token_count = 0;
        app->ask.ttft_ms = 0;
        app->ask.tok_per_sec = 0.0;

        if (query[0] == '!') {
            FILE *fp = popen(query + 1, "r");
            if (fp) {
                app->ask.output_len = fread(app->ask.output, 1,
                    sizeof(app->ask.output) - 1, fp);
                app->ask.output[app->ask.output_len] = 0;
                pclose(fp);
                struct timespec now;
                clock_gettime(CLOCK_MONOTONIC, &now);
                app->ask.ttft_ms = (int)((now.tv_sec - app->ask.t_sent.tv_sec) * 1000
                    + (now.tv_nsec - app->ask.t_sent.tv_nsec) / 1000000);
            } else {
                strcpy(app->ask.output, "(command failed)");
                app->ask.output_len = strlen(app->ask.output);
            }
        } else if (cal_infer_stream(app->infer_host, app->infer_port,
                             query, &app->ask.infer_sock) == 0) {
            app->ask.streaming = 1;
            cal_infer_recv(-1, NULL, 0);
        } else {
            strcpy(app->ask.output, "(no response)");
            app->ask.output_len = strlen(app->ask.output);
        }
        return;
    }

    if (code == KEY_BACKSPACE) {
        if (app->ask.input_len > 0) app->ask.input_len--;
        return;
    }

    /* map keycode to character */
    char c = 0;
    if (code >= KEY_Q && code <= KEY_P) {
        const char *row = "qwertyuiop";
        c = row[code - KEY_Q];
        if (shift) c -= 32;
    } else if (code >= KEY_A && code <= KEY_L) {
        const char *row = "asdfghjkl";
        c = row[code - KEY_A];
        if (shift) c -= 32;
    } else if (code >= KEY_Z && code <= KEY_M) {
        const char *row = "zxcvbnm";
        c = row[code - KEY_Z];
        if (shift) c -= 32;
    } else if (code == KEY_SPACE) c = ' ';
    else if (code == KEY_DOT) c = shift ? '>' : '.';
    else if (code == KEY_COMMA) c = shift ? '<' : ',';
    else if (code == KEY_SLASH) c = shift ? '?' : '/';
    else if (code == KEY_SEMICOLON) c = shift ? ':' : ';';
    else if (code == KEY_APOSTROPHE) c = shift ? '"' : '\'';
    else if (code == KEY_LEFTBRACE) c = shift ? '{' : '[';
    else if (code == KEY_RIGHTBRACE) c = shift ? '}' : ']';
    else if (code == KEY_MINUS) c = shift ? '_' : '-';
    else if (code == KEY_EQUAL) c = shift ? '+' : '=';
    else if (code == KEY_BACKSLASH) c = shift ? '|' : '\\';
    else if (code == KEY_GRAVE) c = shift ? '~' : '`';
    else if (code >= KEY_1 && code <= KEY_0) {
        const char *nums = "1234567890";
        const char *syms = "!@#$%^&*()";
        int idx = code - KEY_1;
        if (idx >= 0 && idx < 10) c = shift ? syms[idx] : nums[idx];
    }

    if (c && app->ask.input_len < (int)sizeof(app->ask.input) - 1)
        app->ask.input[app->ask.input_len++] = c;
}

/* ================================================================
   input handling — vi0 edit mode
   ================================================================ */

static void vi_exec_command(cal_app *app) {
    vi_ctx *v = &app->vi;
    v->cmd[v->cmd_len] = 0;

    if (strcmp(v->cmd, "w") == 0) {
        vi_save(v);
    } else if (strncmp(v->cmd, "w ", 2) == 0) {
        strncpy(v->filename, v->cmd + 2, sizeof(v->filename) - 1);
        v->filename[sizeof(v->filename) - 1] = 0;
        vi_save(v);
    } else if (strcmp(v->cmd, "wq") == 0) {
        vi_save(v);
        app->mode = MODE_ASK;
    } else if (strncmp(v->cmd, "wq ", 3) == 0) {
        strncpy(v->filename, v->cmd + 3, sizeof(v->filename) - 1);
        v->filename[sizeof(v->filename) - 1] = 0;
        vi_save(v);
        app->mode = MODE_ASK;
    } else if (strcmp(v->cmd, "q") == 0 || strcmp(v->cmd, "q!") == 0) {
        app->mode = MODE_ASK;
    } else if (strncmp(v->cmd, "!", 1) == 0) {
        /* :! — send to inference */
        char resp[32768];
        int n = cal_infer(app->infer_host, app->infer_port,
                          v->cmd + 1, resp, sizeof(resp));
        if (n > 0) {
            /* show response below cursor */
            int pos = vi_cursor_pos(v);
            gap_move(&v->buf, pos);
            gap_insert(&v->buf, '\n');
            gap_insert_str(&v->buf, resp, n);
            gap_insert(&v->buf, '\n');
            v->dirty = 1;
        }
    } else if (strncmp(v->cmd, "r !", 3) == 0) {
        /* :r ! — insert inference output at cursor */
        char resp[32768];
        int n = cal_infer(app->infer_host, app->infer_port,
                          v->cmd + 3, resp, sizeof(resp));
        if (n > 0) {
            int pos = vi_cursor_pos(v);
            gap_move(&v->buf, pos);
            gap_insert(&v->buf, '\n');
            gap_insert_str(&v->buf, resp, n);
            v->dirty = 1;
        }
    }
    /* TODO: :%! (filter buffer through inference) */

    v->cmd_len = 0;
    v->state = VI_NORMAL;
}

static void handle_edit_key(cal_app *app, int code, int value) {
    if (value == 0) return;
    vi_ctx *v = &app->vi;

    if (v->state == VI_COMMAND) {
        if (code == KEY_ENTER) { vi_exec_command(app); return; }
        if (code == KEY_ESC) { v->cmd_len = 0; v->state = VI_NORMAL; return; }
        if (code == KEY_BACKSPACE) {
            if (v->cmd_len > 0) v->cmd_len--;
            else v->state = VI_NORMAL;
            return;
        }
        /* append to command buffer */
        char c = 0;
        int shift = app->shift;
        if (code >= KEY_Q && code <= KEY_P) { c = "qwertyuiop"[code - KEY_Q]; if (shift) c -= 32; }
        else if (code >= KEY_A && code <= KEY_L) { c = "asdfghjkl"[code - KEY_A]; if (shift) c -= 32; }
        else if (code >= KEY_Z && code <= KEY_M) { c = "zxcvbnm"[code - KEY_Z]; if (shift) c -= 32; }
        else if (code == KEY_SPACE) c = ' ';
        else if (code == KEY_DOT) c = shift ? '>' : '.';
        else if (code == KEY_COMMA) c = shift ? '<' : ',';
        else if (code == KEY_SLASH) c = shift ? '?' : '/';
        else if (code == KEY_SEMICOLON) c = shift ? ':' : ';';
        else if (code == KEY_APOSTROPHE) c = shift ? '"' : '\'';
        else if (code == KEY_MINUS) c = shift ? '_' : '-';
        else if (code == KEY_EQUAL) c = shift ? '+' : '=';
        else if (code == KEY_LEFTBRACE) c = shift ? '{' : '[';
        else if (code == KEY_RIGHTBRACE) c = shift ? '}' : ']';
        else if (code == KEY_BACKSLASH) c = shift ? '|' : '\\';
        else if (code == KEY_GRAVE) c = shift ? '~' : '`';
        else if (code >= KEY_1 && code <= KEY_0) {
            int idx = code - KEY_1;
            c = shift ? "!@#$%^&*()"[idx] : "1234567890"[idx];
        }
        if (c && v->cmd_len < (int)sizeof(v->cmd) - 1)
            v->cmd[v->cmd_len++] = c;
        return;
    }

    if (v->state == VI_INSERT) {
        if (code == KEY_ESC) { v->state = VI_NORMAL; return; }
        if (code == KEY_ENTER) {
            int pos = vi_cursor_pos(v);
            gap_move(&v->buf, pos);
            gap_insert(&v->buf, '\n');
            v->cy++;
            v->cx = 0;
            v->dirty = 1;
            return;
        }
        if (code == KEY_BACKSPACE) {
            int pos = vi_cursor_pos(v);
            if (pos > 0) {
                gap_move(&v->buf, pos);
                gap_backspace(&v->buf);
                if (v->cx > 0) v->cx--;
                else if (v->cy > 0) {
                    v->cy--;
                    v->cx = vi_line_len(v, v->cy);
                }
                v->dirty = 1;
            }
            return;
        }
        /* insert character */
        char c = 0;
        int shift = app->shift;
        if (code >= KEY_Q && code <= KEY_P) { c = "qwertyuiop"[code - KEY_Q]; if (shift) c -= 32; }
        else if (code >= KEY_A && code <= KEY_L) { c = "asdfghjkl"[code - KEY_A]; if (shift) c -= 32; }
        else if (code >= KEY_Z && code <= KEY_M) { c = "zxcvbnm"[code - KEY_Z]; if (shift) c -= 32; }
        else if (code == KEY_SPACE) c = ' ';
        else if (code == KEY_DOT) c = shift ? '>' : '.';
        else if (code == KEY_COMMA) c = shift ? '<' : ',';
        else if (code == KEY_SLASH) c = shift ? '?' : '/';
        else if (code == KEY_SEMICOLON) c = shift ? ':' : ';';
        else if (code == KEY_APOSTROPHE) c = shift ? '"' : '\'';
        else if (code == KEY_MINUS) c = shift ? '_' : '-';
        else if (code == KEY_EQUAL) c = shift ? '+' : '=';
        else if (code == KEY_LEFTBRACE) c = shift ? '{' : '[';
        else if (code == KEY_RIGHTBRACE) c = shift ? '}' : ']';
        else if (code == KEY_BACKSLASH) c = shift ? '|' : '\\';
        else if (code == KEY_GRAVE) c = shift ? '~' : '`';
        else if (code == KEY_TAB) c = '\t';
        else if (code >= KEY_1 && code <= KEY_0) {
            int idx = code - KEY_1;
            c = shift ? "!@#$%^&*()"[idx] : "1234567890"[idx];
        }
        if (c) {
            int pos = vi_cursor_pos(v);
            gap_move(&v->buf, pos);
            gap_insert(&v->buf, c);
            v->cx++;
            v->dirty = 1;
        }
        return;
    }

    /* VI_NORMAL */
    switch (code) {
    case KEY_BACKSPACE: {
        int pos = vi_cursor_pos(v);
        if (pos > 0) {
            gap_move(&v->buf, pos);
            gap_backspace(&v->buf);
            if (v->cx > 0) v->cx--;
            else if (v->cy > 0) {
                v->cy--;
                v->cx = vi_line_len(v, v->cy);
            }
            v->dirty = 1;
        }
        break;
    }
    case KEY_H: case KEY_LEFT:
        if (v->cx > 0) v->cx--;
        break;
    case KEY_L: case KEY_RIGHT: {
        int ll = vi_line_len(v, v->cy);
        if (v->cx < ll - 1) v->cx++;
        break;
    }
    case KEY_J: case KEY_DOWN:
        if (v->cy < vi_line_count(v) - 1) {
            v->cy++;
            int ll = vi_line_len(v, v->cy);
            if (v->cx >= ll) v->cx = ll > 0 ? ll - 1 : 0;
        }
        break;
    case KEY_K: case KEY_UP:
        if (v->cy > 0) {
            v->cy--;
            int ll = vi_line_len(v, v->cy);
            if (v->cx >= ll) v->cx = ll > 0 ? ll - 1 : 0;
        }
        break;
    case KEY_I:
        v->state = VI_INSERT;
        break;
    case KEY_A: {
        int ll = vi_line_len(v, v->cy);
        if (v->cx < ll) v->cx++;
        v->state = VI_INSERT;
        break;
    }
    case KEY_O: {
        int start = vi_line_start(v, v->cy);
        int ll = vi_line_len(v, v->cy);
        gap_move(&v->buf, start + ll);
        gap_insert(&v->buf, '\n');
        v->cy++;
        v->cx = 0;
        v->state = VI_INSERT;
        v->dirty = 1;
        break;
    }
    case KEY_X: {
        int pos = vi_cursor_pos(v);
        int len = gap_length(&v->buf);
        if (pos < len && gap_char_at(&v->buf, pos) != '\n') {
            gap_move(&v->buf, pos);
            gap_delete(&v->buf);
            v->dirty = 1;
        }
        break;
    }
    case KEY_D: {
        /* dd — delete line (wait for second d via simple state) */
        /* simplified: single d deletes current line */
        int start = vi_line_start(v, v->cy);
        int ll = vi_line_len(v, v->cy);
        int end = start + ll;
        if (end < gap_length(&v->buf)) end++; /* include newline */
        /* yank before delete */
        v->yank_len = 0;
        for (int i = start; i < end && v->yank_len < (int)sizeof(v->yank) - 1; i++)
            v->yank[v->yank_len++] = gap_char_at(&v->buf, i);
        v->yank[v->yank_len] = 0;
        gap_move(&v->buf, start);
        for (int i = start; i < end; i++) gap_delete(&v->buf);
        v->cx = 0;
        if (v->cy >= vi_line_count(v) && v->cy > 0) v->cy--;
        v->dirty = 1;
        break;
    }
    case KEY_Y: {
        /* yy — yank line */
        int start = vi_line_start(v, v->cy);
        int ll = vi_line_len(v, v->cy);
        int end = start + ll;
        if (end < gap_length(&v->buf)) end++;
        v->yank_len = 0;
        for (int i = start; i < end && v->yank_len < (int)sizeof(v->yank) - 1; i++)
            v->yank[v->yank_len++] = gap_char_at(&v->buf, i);
        v->yank[v->yank_len] = 0;
        break;
    }
    case KEY_P:
        if (v->yank_len > 0) {
            int start = vi_line_start(v, v->cy);
            int ll = vi_line_len(v, v->cy);
            int end = start + ll;
            if (end < gap_length(&v->buf)) end++;
            gap_move(&v->buf, end);
            gap_insert_str(&v->buf, v->yank, v->yank_len);
            v->cy++;
            v->cx = 0;
            v->dirty = 1;
        }
        break;
    case KEY_SLASH: {
        /* enter command mode for search (reuse command buffer) */
        v->state = VI_COMMAND;
        v->cmd_len = 0;
        break;
    }
    case KEY_SEMICOLON: {
        if (app->shift) {
            v->state = VI_COMMAND;
            v->cmd_len = 0;
        }
        break;
    }
    case KEY_G: {
        /* gg — go to top (simplified: single g) */
        v->cy = 0;
        v->cx = 0;
        break;
    }
    }
}

/* ================================================================
   main event loop
   ================================================================ */

static void usage(void) {
    fprintf(stderr, "usage: cal [-f font.ttf] [-s size] [-h host] [-p port] [file]\n");
    exit(1);
}

int main(int argc, char **argv) {
    cal_app app;
    memset(&app, 0, sizeof(app));
    app.running = 1;
    app.mode = MODE_ASK;
    app.margin = 60;
    app.ask.infer_sock = -1;
    strcpy(app.infer_host, "127.0.0.1");
    app.infer_port = 8087;

    const char *font_path = NULL;
    float font_size = 20.0;
    float font_large_size = 48.0;
    const char *edit_file = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) font_path = argv[++i];
        else if (strcmp(argv[i], "-s") == 0 && i + 1 < argc) font_size = atof(argv[++i]);
        else if (strcmp(argv[i], "-h") == 0 && i + 1 < argc) strncpy(app.infer_host, argv[++i], 63);
        else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc) app.infer_port = atoi(argv[++i]);
        else if (argv[i][0] != '-') edit_file = argv[i];
        else usage();
    }

    /* find a font if none specified */
    if (!font_path) {
        static const char *search[] = {
            "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/TTF/LiberationMono-Regular.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/System/Library/Fonts/SFMono-Regular.otf",
            "/Library/Fonts/SF-Mono-Regular.otf",
            NULL
        };
        for (int i = 0; search[i]; i++) {
            if (access(search[i], R_OK) == 0) { font_path = search[i]; break; }
        }
    }
    if (!font_path) {
        fprintf(stderr, "cal: no font found. use -f path/to/font.ttf\n");
        return 1;
    }

    if (platform_init(&app.surface) < 0) return 1;

    if (cal_font_init(&app.font, font_path, font_size) < 0) {
        fprintf(stderr, "cal: failed to load font: %s\n", font_path);
        platform_cleanup();
        return 1;
    }
    int font_large_shared = 0;
    if (cal_font_init(&app.font_large, font_path, font_large_size) < 0) {
        memcpy(&app.font_large, &app.font, sizeof(cal_font));
        font_large_shared = 1;
    }

    vi_init(&app.vi);
    if (edit_file) {
        vi_load(&app.vi, edit_file);
        app.mode = MODE_EDIT;
    }

    /* main loop */
    while (app.running) {
        clear(&app.surface);

        switch (app.mode) {
        case MODE_ASK:      draw_ask(&app); break;
        case MODE_EDIT:     draw_edit(&app); break;
        case MODE_CARDS:    break; /* TODO */
        case MODE_CLINICAL: break; /* TODO */
        default: break;
        }

        draw_status(&app);
        platform_flip(&app.surface);

        /* drain streaming inference if active */
        if (app.ask.streaming && app.ask.infer_sock >= 0) {
            fd_set rfds;
            FD_ZERO(&rfds);
            FD_SET(app.ask.infer_sock, &rfds);
            struct timeval tv = {0, 0};
            if (select(app.ask.infer_sock + 1, &rfds, NULL, NULL, &tv) > 0) {
                char chunk[4096];
                int n = cal_infer_recv(app.ask.infer_sock, chunk, sizeof(chunk));
                if (n > 0) {
                    if (app.ask.t_first_token.tv_sec == 0) {
                        clock_gettime(CLOCK_MONOTONIC, &app.ask.t_first_token);
                        app.ask.ttft_ms = (int)((app.ask.t_first_token.tv_sec - app.ask.t_sent.tv_sec) * 1000
                            + (app.ask.t_first_token.tv_nsec - app.ask.t_sent.tv_nsec) / 1000000);
                    }
                    for (int i = 0; i < n; i++)
                        if (chunk[i] == ' ' || chunk[i] == '\n') app.ask.token_count++;
                    struct timespec now;
                    clock_gettime(CLOCK_MONOTONIC, &now);
                    double elapsed = (now.tv_sec - app.ask.t_first_token.tv_sec)
                        + (now.tv_nsec - app.ask.t_first_token.tv_nsec) / 1e9;
                    if (elapsed > 0.01)
                        app.ask.tok_per_sec = app.ask.token_count / elapsed;
                    int space = (int)sizeof(app.ask.output) - app.ask.output_len - 1;
                    if (n > space) n = space;
                    memcpy(app.ask.output + app.ask.output_len, chunk, n);
                    app.ask.output_len += n;
                    app.ask.output[app.ask.output_len] = 0;
                } else {
                    close(app.ask.infer_sock);
                    app.ask.infer_sock = -1;
                    app.ask.streaming = 0;
                }
            }
        }

        cal_event ev;
        if (platform_event(&ev, 16)) {
            if (ev.type == CAL_KEY) {
                if (ev.code == KEY_LEFTSHIFT || ev.code == KEY_RIGHTSHIFT) {
                    app.shift = (ev.value != 0);
                    continue;
                }
                /* F1-F5: mode switch */
                if (ev.code == KEY_F1 && ev.value == 1) { app.mode = MODE_ASK; continue; }
                if (ev.code == KEY_F2 && ev.value == 1) { app.mode = MODE_EDIT; continue; }
                if (ev.code == KEY_F3 && ev.value == 1) { app.mode = MODE_CARDS; continue; }
                if (ev.code == KEY_F4 && ev.value == 1) { app.mode = MODE_CLINICAL; continue; }
                if (ev.code == KEY_F5 && ev.value == 1) { app.running = 0; continue; }

                switch (app.mode) {
                case MODE_ASK:  handle_ask_key(&app, ev.code, ev.value); break;
                case MODE_EDIT: handle_edit_key(&app, ev.code, ev.value); break;
                default: break;
                }
            }
        }
    }

    cal_font_free(&app.font);
    if (!font_large_shared) cal_font_free(&app.font_large);
    gap_free(&app.vi.buf);
    platform_cleanup();
    return 0;
}
