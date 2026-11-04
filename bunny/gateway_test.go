package main

import (
  "io"
  "encoding/json"
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

func TestGatewayDiagnosticCountersDoNotTreatUnknownVideoAsVerified(t *testing.T) {
  src := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    switch r.URL.Path {
    case "/other-video":
      w.Header().Set("Content-Type", "video/mp2t")
      _, _ = io.WriteString(w, strings.Repeat("x", 2048))
    case "/stream/example":
      w.Header().Set("Content-Type", "application/octet-stream")
      _, _ = io.WriteString(w, strings.Repeat("y", 4096))
    default:
      w.Header().Set("Content-Type", "text/plain")
      _, _ = io.WriteString(w, "ok")
    }
  }))
  defer src.Close()
  parsed, _ := url.Parse(src.URL)
  t0 := &tracker{}
  t0.lastMedia.Store(time.Now().Unix() - 7200)
  server := httptest.NewServer(newHandler(parsed, "secret", t0))
  defer server.Close()

  requestBody := func(path string) {
    t.Helper()
    resp, err := http.Get(server.URL + path)
    if err != nil { t.Fatal(err) }
    _, _ = io.Copy(io.Discard, resp.Body)
    _ = resp.Body.Close()
  }
  requestBody("/echo?auth-do-not-log=private")
  requestBody("/other-video?link=private")
  if t0.bytes.Load() != 0 { t.Fatal("unclassified video may not activate the verified-media counter") }
  if t0.unclassifiedMediaBytes.Load() != 2048 { t.Fatalf("unknown media bytes: %d", t0.unclassifiedMediaBytes.Load()) }
  requestBody("/stream/example?link=private")
  if t0.bytes.Load() != 4096 { t.Fatalf("stream bytes: %d", t0.bytes.Load()) }

  req, _ := http.NewRequest("GET", server.URL + "/__bunny/activity", nil)
  req.Header.Set("X-Watchdog-Token", "secret")
  resp, err := http.DefaultClient.Do(req)
  if err != nil { t.Fatal(err) }
  defer resp.Body.Close()
  var stats map[string]int64
  if err := json.NewDecoder(resp.Body).Decode(&stats); err != nil { t.Fatal(err) }
  if stats["proxy_requests"] != 3 || stats["media_requests"] != 1 || stats["other_requests"] != 2 {
    t.Fatalf("unexpected route-class counters: %+v", stats)
  }
  if stats["unclassified_media_bytes"] != 2048 || stats["media_bytes"] != 4096 || stats["other_response_bytes"] < 2050 {
    t.Fatalf("unexpected byte counters: %+v", stats)
  }
}
