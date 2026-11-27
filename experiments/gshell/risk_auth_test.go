package auth

import (
 "os"
 "path/filepath"
 "testing"
 "golang.org/x/oauth2"
)
func TestAuditExistingCredentialMode(t *testing.T){
 t.Setenv("XDG_CONFIG_HOME",t.TempDir())
 p,e:=CredentialsPath();if e!=nil{t.Fatal(e)}
 if e=os.MkdirAll(filepath.Dir(p),0700);e!=nil{t.Fatal(e)}
 if e=os.WriteFile(p,[]byte("fixture"),0644);e!=nil{t.Fatal(e)}
 if e=os.Chmod(p,0644);e!=nil{t.Fatal(e)}
 if e=SaveToken(&oauth2.Token{AccessToken:"synthetic-not-a-real-token"},"fixture@example.invalid");e!=nil{t.Fatal(e)}
 i,e:=os.Stat(p);if e!=nil{t.Fatal(e)}
 if i.Mode().Perm()!=0644{t.Fatalf("expected reproduced existing mode 0644, got %o",i.Mode().Perm())}
 t.Logf("GS-06 reproduced: existing credential file permission remains %04o after SaveToken",i.Mode().Perm())
}
