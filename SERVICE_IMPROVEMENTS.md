# Football Match Tracking System - Service Improvements

This document details the service enhancements made to ensure reliable operation of the Football Match Tracking System.

## Key Service Components

### 1. service_wrapper.sh

Robust wrapper script that provides:
- Line 14-19: Automatic detection and termination of stuck processes
- Line 22-24: Stale lock file removal
- Line 26-30: System resource monitoring
- Line 32-37: Proper virtual environment activation
- Line 44-46: Enforced timeouts to prevent API call hangs

### 2. football_bot_continuous.service

Production-ready systemd service for continuous operation:
- Line 13-14: Implements continuous execution loop with 60s pause between runs
- Line 16-17: Automatic restart on any failure
- Line 18-20: Resource limits (256MB memory, 50% CPU)

### 3. debug_env.sh

Diagnostic tool for environment troubleshooting:
- Line 8-11: Environmental state logging
- Line 14-17: API connectivity testing
- Line 25-27: Virtual environment validation

## Usage Commands

```bash
# Start tracking service (runs continuously)
sudo systemctl start football_bot_continuous.service

# Stop tracking service
sudo systemctl stop football_bot_continuous.service

# Check service status
sudo systemctl status football_bot_continuous.service
```

## Monitoring & Troubleshooting

- Service logs: `journalctl -u football_bot_continuous.service -f`
- Wrapper logs: `tail -f /root/Complete_Seperate/logs/service_wrapper.log`
- Match summaries: `tail -f /root/Complete_Seperate/logs/combined_match_summary.logger`

## Implementation Notes

The service is designed to:
1. Run one complete cycle with proper virtual environment activation
2. Implement a hard 10-minute timeout for any cycle to prevent API hangs
3. Wait 60 seconds between cycles
4. Continue indefinitely until manually stopped
5. Maintain resource usage under defined limits (256MB memory, 50% CPU)

This implementation addresses the "stuck" pipeline issues observed with the original service by ensuring proper environment activation and implementing timeouts.
