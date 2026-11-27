package ssh

import (
 "crypto/ed25519"
 "crypto/rand"
 "errors"
 "fmt"
 "io"
 "net"
 "os"
 "path/filepath"
 "testing"
 "time"

 "github.com/pkg/sftp"
 "golang.org/x/crypto/ssh"
 "gshell/internal/cloudshell"
)

type faultReader struct{}
func (faultReader) ReadAt(p []byte,off int64)(int,error){return 0,fmt.Errorf("synthetic read failure")}
type faultHandler struct{}
func (faultHandler) Fileread(*sftp.Request)(io.ReaderAt,error){return faultReader{},nil}

func TestAuditDestinationLoss(t *testing.T) {
 a,b:=net.Pipe()
 defer a.Close()
 defer b.Close()
 server:=sftp.NewRequestServer(a,sftp.Handlers{FileGet:faultHandler{}})
 go func(){_ = server.Serve();_ = server.Close()}()
 client,e:=sftp.NewClientPipe(b,b);if e!=nil{t.Fatal(e)}
 defer client.Close()
 s:=&SFTPClient{client:client}
 p:=filepath.Join(t.TempDir(),"existing")
 if e=os.WriteFile(p,[]byte("original-content"),0600);e!=nil{t.Fatal(e)}
 e=s.downloadFile("/synthetic",p,false,&Result{})
 if e==nil{t.Fatal("expected read failure")}
 got,e:=os.ReadFile(p);if e!=nil{t.Fatal(e)}
 if len(got)!=0{t.Fatalf("expected reproduced truncation, len=%d",len(got))}
 t.Logf("GS-02 reproduced: previous destination 16 bytes -> %d bytes after synthetic read error",len(got))
}

func signerFixture(t *testing.T) ssh.Signer {
 t.Helper();_,k,e:=ed25519.GenerateKey(rand.Reader);if e!=nil{t.Fatal(e)}
 s,e:=ssh.NewSignerFromKey(k);if e!=nil{t.Fatal(e)};return s
}

func TestAuditHostIdentityAndExit(t *testing.T) {
 clientKey:=signerFixture(t)
 var fingerprints []string
 for i:=0;i<2;i++{
  hostKey:=signerFixture(t)
  fingerprints=append(fingerprints,ssh.FingerprintSHA256(hostKey.PublicKey()))
  l,e:=net.Listen("tcp","127.0.0.1:0");if e!=nil{t.Fatal(e)}
  conf:=&ssh.ServerConfig{PublicKeyCallback:func(_ ssh.ConnMetadata,k ssh.PublicKey)(*ssh.Permissions,error){
   if ssh.FingerprintSHA256(k)!=ssh.FingerprintSHA256(clientKey.PublicKey()){return nil,fmt.Errorf("wrong test key")};return nil,nil
  }}
  conf.AddHostKey(hostKey)
  done:=make(chan error,1)
  go func(){
   c,e:=l.Accept();if e!=nil{done<-e;return};defer c.Close()
   sc,ch,req,e:=ssh.NewServerConn(c,conf);if e!=nil{done<-e;return};defer sc.Close();go ssh.DiscardRequests(req)
   for nc:=range ch {
    if nc.ChannelType()!="session"{_ = nc.Reject(ssh.UnknownChannelType,"session only");continue}
    channel,requests,e:=nc.Accept();if e!=nil{done<-e;return}
    for r:=range requests {
     if r.Type=="exec"{
      _ = r.Reply(true,nil)
      _,_ = channel.SendRequest("exit-status",false,ssh.Marshal(struct{Status uint32}{42}))
      _ = channel.Close()
      done<-nil;return
     }
     _ = r.Reply(false,nil)
    }
   }
   done<-nil
  }()
  addr:=l.Addr().(*net.TCPAddr)
  c,e:=Dial(&cloudshell.ConnectionInfo{Host:"127.0.0.1",Port:addr.Port,Username:"fixture",Signer:clientKey})
  if e!=nil{l.Close();t.Fatal(e)}
  e=RunCommand(c,"synthetic-command","")
  var exit *ssh.ExitError
  if !errors.As(e,&exit)||exit.ExitStatus()!=42{c.Close();l.Close();t.Fatalf("expected ssh exit 42, got %v",e)}
  c.Close();l.Close()
  select{case e:=<-done:if e!=nil{t.Fatal(e)};case <-time.After(2*time.Second):t.Fatal("fixture server timeout")}
 }
 if fingerprints[0]==fingerprints[1]{t.Fatal("expected distinct keys")}
 t.Log("GS-01 reproduced: two independently generated untrusted host keys accepted; library preserves exit status 42, CLI flattening established statically")
}
