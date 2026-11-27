package ssh

import (
 "bytes"
 "net"
 "os"
 "path/filepath"
 "sync/atomic"
 "testing"
 "time"

 "github.com/pkg/sftp"
)

type countedConn struct {
 net.Conn
 read atomic.Int64
 written atomic.Int64
}
func (c *countedConn) Read(p []byte)(int,error){ n,e:=c.Conn.Read(p); c.read.Add(int64(n));return n,e }
func (c *countedConn) Write(p []byte)(int,error){ n,e:=c.Conn.Write(p); c.written.Add(int64(n));return n,e }
func fixtureClient(t *testing.T) (*SFTPClient,*countedConn){
 t.Helper()
 listener,e:=net.Listen("tcp","127.0.0.1:0");if e!=nil{t.Fatal(e)}
 done:=make(chan struct{})
 go func(){defer close(done); conn,e:=listener.Accept();if e!=nil{return};defer conn.Close(); server,e:=sftp.NewServer(conn);if e!=nil{return};defer server.Close();_ = server.Serve()}()
 conn,e:=net.Dial("tcp",listener.Addr().String());if e!=nil{t.Fatal(e)}
 counter:=&countedConn{Conn:conn}
 client,e:=sftp.NewClientPipe(counter,counter);if e!=nil{t.Fatal(e)}
 t.Cleanup(func(){client.Close();conn.Close();listener.Close();select{case <-done:case <-time.After(time.Second):}})
 return &SFTPClient{client:client},counter
}
func writeFixture(t *testing.T,p string,b []byte){t.Helper();if e:=os.WriteFile(p,b,0600);e!=nil{t.Fatal(e)}}
func sameFixture(t *testing.T,p string,b []byte){t.Helper();got,e:=os.ReadFile(p);if e!=nil||!bytes.Equal(got,b){t.Fatalf("content mismatch: %v",e)}}
func TestAuditTransfer(t *testing.T){
 c,w:=fixtureClient(t)
 root:=t.TempDir(); local:=filepath.Join(root,"local"); remote:=filepath.Join(root,"remote"); dest:=filepath.Join(root,"dest")
 payload:=bytes.Repeat([]byte("0123456789abcdef"),65536)
 changed:=bytes.Repeat([]byte("fedcba9876543210"),65536)
 writeFixture(t,local,payload)
 r,e:=c.Upload(local,remote,false,true);if e!=nil||r.Files!=1{t.Fatalf("dry run %v %v",r,e)}
 if _,e=os.Stat(remote);!os.IsNotExist(e){t.Fatal("dry run changed filesystem")}
 r,e=c.Upload(local,remote,false,false);if e!=nil||r.Bytes!=int64(len(payload)){t.Fatalf("upload %v %v",r,e)}
 sameFixture(t,remote,payload)
 r,e=c.Download(remote,dest,false,false);if e!=nil||r.Bytes!=int64(len(payload)){t.Fatalf("download %v %v",r,e)}
 sameFixture(t,dest,payload)
 for i:=0;i<3;i++ {
  for _,mode:=range []string{"download","sync-unchanged","sync-changed","upload","sync-up-unchanged"} {
   if arm:=os.Getenv("GSHELL_AUDIT_ARM"); arm!="" && mode!=arm {continue}
   writeFixture(t,remote,payload);writeFixture(t,dest,payload);writeFixture(t,local,payload)
   if mode=="sync-changed"{writeFixture(t,dest,changed)}
   beforeR,beforeW:=w.read.Load(),w.written.Load()
   start:=time.Now()
   switch mode{
   case "download":r,e=c.Download(remote,dest,false,false)
   case "sync-unchanged","sync-changed":r,e=c.SyncDown(remote,dest,false,false)
   case "upload":r,e=c.Upload(local,remote,false,false)
   case "sync-up-unchanged":r,e=c.Sync(local,remote,false,false)
   }
   elapsed:=time.Since(start)
   if e!=nil{t.Fatal(e)}
   sameFixture(t,dest,payload);sameFixture(t,remote,payload)
   wantSkip:=mode=="sync-unchanged"||mode=="sync-up-unchanged"
   if wantSkip && (r.Skipped!=1||r.Files!=0){t.Fatalf("wrong skip %+v",r)}
   if !wantSkip && r.Files!=1{t.Fatalf("wrong copies %+v",r)}
   read,write:=w.read.Load()-beforeR,w.written.Load()-beforeW
   t.Logf("repeat=%d mode=%s payload=%d reported_bytes=%d skipped=%d sftp_rx=%d sftp_tx=%d us=%d",i,mode,len(payload),r.Bytes,r.Skipped,read,write,elapsed.Microseconds())
   if mode=="sync-unchanged" && read<int64(len(payload)){t.Fatal("unexpected: checksum did not read full remote file")}
   if mode=="sync-changed" && read<2*int64(len(payload)){t.Fatal("unexpected: checksum and download did not read twice")}
  }
 }
}
