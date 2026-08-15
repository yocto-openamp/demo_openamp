
If arm64 can't be build, error:

```bash
ERROR: failed to solve: process "/bin/sh -c apt-get update     && apt-get install -y         git         wget         curl         cmake         ninja-build         gperf         ccache         dfu-util         device-tree-compiler         xz-utils         file         make     && rm -rf /var/lib/apt/lists/*" did not complete successfully: exit code: 255
```

This fixes the problem:

```bash
docker run --privileged --rm tonistiigi/binfmt --install arm64
```
