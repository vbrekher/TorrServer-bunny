// Stream gateway transparently proxies TorrServer HTTP and tracks media-byte activity.
// It never receives a Bunny account API key. A separate scheduled controller decides
// when it is safe to issue Bunny's /undeploy API call.
package main

import (
    "crypto/subtle"
    "encoding/json"
    "io"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "os"
    "strings"
    "sync/atomic"
    "time"
)

type tracker struct {
    lastMedia atomic.Int64
    active atomic.Int64
    bytes atomic.Int64
}

type countedBody struct {
    io.ReadCloser
    tracker *tracker
}

func (c *countedBody) Read(p []byte) (int, error) {
    n, err := c.ReadCloser.Read(p)
    if n > 0 {
        c.tracker.lastMedia.Store(time.Now().Unix())
        c.tracker.bytes.Add(int64(n))
    }
    return n, err
}

func isMedia(path string) bool {
    return path == "/stream" || strings.HasPrefix(path, "/stream/") ||
        path == "/play" || strings.HasPrefix(path, "/play/") ||
        path == "/playlist" || strings.HasPrefix(path, "/playlist/") ||
        path == "/playlistall" || strings.HasPrefix(path, "/gst/")
}

func newHandler(target *url.URL, token string, t *tracker) http.Handler {
    proxy := httputil.NewSingleHostReverseProxy(target)
    proxy.FlushInterval = -1 // do not buffer video chunks
    proxy.ModifyResponse = func(res *http.Response) error {
        if isMedia(res.Request.URL.Path) {
            res.Header.Set("Cache-Control", "private, no-store, max-age=0")
            res.Body = &countedBody{ReadCloser: res.Body, tracker: t}
        }
        return nil
    }
    proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
        log.Printf("upstream error: %v", err)
        http.Error(w, "TorrServer temporarily unavailable", http.StatusBadGateway)
    }
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path == "/__bunny/activity" {
            w.Header().Set("Content-Type", "application/json")
            w.Header().Set("Cache-Control", "no-store, max-age=0")
            supplied := r.Header.Get("X-Watchdog-Token")
            if token == "" || subtle.ConstantTimeCompare([]byte(supplied), []byte(token)) != 1 {
                http.Error(w, "forbidden", http.StatusForbidden)
                return
            }
            _ = json.NewEncoder(w).Encode(map[string]int64{
                "last_media_unix": t.lastMedia.Load(),
                "active_streams": t.active.Load(),
                "media_bytes": t.bytes.Load(),
            })
            return
        }
        if strings.HasPrefix(r.URL.Path, "/__bunny/") {
            http.NotFound(w, r)
            return
        }
        if isMedia(r.URL.Path) {
            t.active.Add(1)
            defer t.active.Add(-1)
            t.lastMedia.Store(time.Now().Unix())
        }
        proxy.ServeHTTP(w, r)
    })
}

func main() {
    token := os.Getenv("BUNNY_WATCHDOG_TOKEN")
    if token == "" {
        log.Fatal("BUNNY_WATCHDOG_TOKEN is required")
    }
    upstream, _ := url.Parse("http://127.0.0.1:8090")
    t := &tracker{}
    t.lastMedia.Store(time.Now().Unix()) // hour begins at container startup, never before
    server := &http.Server{
        Addr: ":8080",
        Handler: newHandler(upstream, token, t),
        ReadHeaderTimeout: 15 * time.Second,
        IdleTimeout: 120 * time.Second,
    }
    log.Println("Bunny gateway listening on :8080")
    log.Fatal(server.ListenAndServe())
}
