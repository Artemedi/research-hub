package cloudshell

import (
 "context"
 "errors"
 "io"
 "net/http"
 "strings"
 "sync/atomic"
 "testing"
 "time"
)
type roundTripFunc func(*http.Request)(*http.Response,error)
func (f roundTripFunc) RoundTrip(r *http.Request)(*http.Response,error){return f(r)}
func TestAuditPollingHTTPError(t *testing.T){
 var calls atomic.Int32
 c:=&Client{httpClient:&http.Client{Transport:roundTripFunc(func(r *http.Request)(*http.Response,error){
  calls.Add(1)
  return &http.Response{StatusCode:403,Body:io.NopCloser(strings.NewReader("{\"error\":{\"code\":403,\"message\":\"synthetic denied\"}}")),Header:make(http.Header),Request:r},nil
 })}}
 ctx,cancel:=context.WithTimeout(context.Background(),2300*time.Millisecond);defer cancel()
 e:=c.WaitForOperation(ctx,"operations/synthetic")
 if !errors.Is(e,context.DeadlineExceeded)||calls.Load()<2{t.Fatalf("expected repeated 403 until deadline; calls=%d err=%v",calls.Load(),e)}
 t.Logf("GS-07 reproduced: %d HTTP 403 responses polled until context deadline",calls.Load())
}
