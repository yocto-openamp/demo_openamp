# Agent.md

## Context

## Objective

* A Zephyr ELF image for the Cortex-M7 core.
* A Linux app running on Toradex Verdin iMX8M Plus.

Both communicated using RpMsg:

Linux: Master (or Application)
M7: Remote

Linux: RPMsg driver/client
M7: RPMsg endpoint/service

M7 overlay template: hmp_mcuxpresso-zephyr/sources/rpmsg-lite/zephyr/samples/rpmsglite_pingpong/remote/boards

## Configuration

* M7 board overlays  
  sources/rpmsg-lite/zephyr/  samples/rpmsglite_pingpong/remote/boards

* Target configuration  
  zephyr_app/prj_verdin_imx8mp.conf

* Zephyr source:  
  zephyr

* Zephyr SDK  
  ~/zephyr-sdk-1.0.1

* West  
~/torizon_openamp/hmp_mcuxpresso-zephyr/.venv/bin/west

* Python  
~/torizon_openamp/hmp_mcuxpresso-zephyr/.venv/bin/python
