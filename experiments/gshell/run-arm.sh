#!/bin/sh
set -eu
export GSHELL_AUDIT_ARM="$1"
export TMPDIR=/output
/input/audit.test -test.v -test.run '^TestAuditTransfer$' -test.timeout=30s > /output/test.log
cat /output/test.log
awk '
/repeat=/ {
 for(i=1;i<=NF;i++){
 split($i,a,"="); if(a[1]=="reported_bytes") reported=a[2]+0;
 if(a[1]=="skipped") skipped=a[2]+0;
 if(a[1]=="sftp_rx") rx+=a[2]+0;
 if(a[1]=="sftp_tx") tx+=a[2]+0;
 }
 n++
}
END {
 if(n!=3) exit 2
 printf "{\"repeats\":%d,\"reported_bytes\":%d,\"skipped\":%d,\"full_payload_reads\":%d,\"sftp_rx_total\":%d,\"sftp_tx_total\":%d}\n",n,reported,skipped,(rx>=3*1048576),rx,tx
}' /output/test.log > /output/result.json
