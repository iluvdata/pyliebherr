# PyLiebherr:  Access the Smart Home Device API Library

![PyPI - Version](https://img.shields.io/pypi/v/pyliebherr)

Python library to access the [Liebherr Smart Home API](https://developer.liebherr.com/apis/smartdevice-homeapi/) (account required).

## Changelog

### 2025.11.4 ➡️ 2026.1.1
* Controls are now mapped by type, zone_id, and device.  This optimizes the number of cpu cycles that Home Assistant will have to perform to find the control (no more looping through controls until the corresponding control is found).
* Fixed the case of some constant variables for consistency.

### 2026.1.2
* Controls mapping had to change to by `control_name` then `zone_id` if applicable.

### 2026.1.3
* Fixed a duplicative debug log issue. 