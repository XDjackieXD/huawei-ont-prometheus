# How to run it

```
[Unit]
  Description=huawei-ont-stats
  After=time-sync.target
[Service]
  ExecStart=/usr/bin/huawei-ont-prometheus.py
  Restart=on-failure
  RestartSec=10
[Install]
  WantedBy=multi-user.target
```
