# Quick Reference Card

Print this for your gig!

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   M-VAVE CHOCOLATE PLUS → CQ-20B CONTROLLER    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                 ┃
┃  BUTTON LAYOUT:                                 ┃
┃  ┌─────┬─────┬─────┬─────┐                     ┃
┃  │  A  │  B  │  C  │  D  │                     ┃
┃  └─────┴─────┴─────┴─────┘                     ┃
┃                                                 ┃
┃  [A] Recording  ⏺️  USB/SD Start/Stop           ┃
┃  [B] Monitor    🔊 IEM Level Toggle (Hi/Lo)    ┃
┃  [C] FX Toggle  🎛️  Effects Mute On/Off        ┃
┃  [D] BREAK      ☕ Scene Switch                 ┃
┃                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  BREAK MODE (Button D):                        ┃
┃                                                 ┃
┃  OFF (Normal Performance):                     ┃
┃    ✓ Vocals      (Group 1)                     ┃
┃    ✓ Instruments (Group 2)                     ┃
┃    ✗ Break Music (Group 3) MUTED               ┃
┃    ✓ FX          (Group 4)                     ┃
┃                                                 ┃
┃  ON (Break Time):                               ┃
┃    ✗ Vocals      (Group 1) MUTED               ┃
┃    ✗ Instruments (Group 2) MUTED               ┃
┃    ✓ Break Music (Group 3) ST2 In              ┃
┃    ✗ FX          (Group 4) MUTED               ┃
┃                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  TROUBLESHOOTING:                              ┃
┃                                                 ┃
┃  No response from buttons?                      ┃
┃  → Check Bluetooth connection (blue light)      ┃
┃  → Press M-Vave power button                    ┃
┃                                                 ┃
┃  Break music not playing?                       ┃
┃  → Verify ST2 In source is connected            ┃
┃  → Check Button D is pressed (break mode ON)    ┃
┃                                                 ┃
┃  Recording not starting?                        ┃
┃  → Verify USB/SD card inserted in mixer         ┃
┃  → Check available storage space                ┃
┃                                                 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  EMERGENCY:                                     ┃
┃                                                 ┃
┃  Controller not working?                        ┃
┃  → Use CQ MixPad app as backup                  ┃
┃  → Restart Raspberry Pi if needed               ┃
┃                                                 ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Pre-Show Checklist

- [ ] Raspberry Pi powered on
- [ ] M-Vave Bluetooth connected (blue light)
- [ ] CQ-20B mixer on network
- [ ] ST2 In break music source playing
- [ ] Test all 4 buttons during soundcheck
- [ ] CQ MixPad app ready as backup

## Typical Workflow

**Sound Check:**
1. Start in normal mode (break OFF)
2. Test Button A → Recording
3. Test Button B → Monitor level
4. Test Button C → FX toggle
5. Test Button D → Break mode (in/out)

**Performance:**
```
[Performing] → Press D → [Break Music] → Press D → [Performing]
```

**Recording:**
```
Press A → START → Perform → Press A → STOP
```

## Support

System logs: `sudo journalctl -u cq-footcontroller -f`
Restart service: `sudo systemctl restart cq-footcontroller`
