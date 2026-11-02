package main

import (
  "io"
  "net/http"
  "net/http/httptest"
  "net/url"
  "strings"
  "testing"
  "time"
)

func TestMediaTrackingAndToken(t *testing.T) {
  src := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
     _, _ = io.WriteString(w, "test-movie-bytes")
  }))
  defer src.Close()
  parsed, _ := url.Parse(src.URL)
  tracker := &tracker{}
  tracker.lastMedia.Store(time.Now().Unix()-7200)
  server := httptest.NewServer(newHandler(parsed,"my-token",tracker))
  defer server.Close()
  req, _ := http.NewRequest("GET",server.URL+"/__bunny/activity",nil)
  resp, err := http.DefaultClient.Do(req)
  if err != nil || resp.StatusCode != 403 { t.Fatalf("expected forbidden got %v %v",resp,err) }
  resp.Body.Close()
  resp, err = http.Get(server.URL+"/echo")
  if err != nil { t.Fatal(err) }
  resp.Body.Close()
  if tracker.lastMedia.Load() > time.Now().Unix()-7100 { t.Fatal("echo updated media time") }
  resp, err = http.Get(server.URL+"/play/example")
  if err != nil { t.Fatal(err) }
  b, _ := io.ReadAll(resp.Body)
  resp.Body.Close()
  if !strings.Contains(string(b), "test-movie-bytes") || tracker.bytes.Load()< 16 || tracker.active.Load()!=0 {t.Fatalf("unexpected %s %+v",string(b),tracker)}
  if tracker.lastMedia.Load() < time.Now().Unix()-10 {t.Fatal("media did not update last activity")}
  req, _ = http.NewRequest("GET",server.URL+"/__bunny/activity",nil)
  req.Header.Set("X-Watchdog-Token", "my-token")
  resp, err = http.DefaultClient.Do(req)
  if err != nil || resp.StatusCode != 200 {t.Fatalf("status request failed %v %v",resp,err)}
  resp.Body.Close()
}
