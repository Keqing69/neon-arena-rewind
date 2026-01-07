# Neon Arena Rewind

Top-down arcade shooter built with Python & Pygame featuring a time-rewind ability.

## Features
- Fast-paced top-down arena shooter
- Time-rewind power-up (charge-up, then rewind your last 5 seconds)
- Rewind animation (2s), temporary invulnerability, no player control during rewind
- Modular frontend config (sprites + optional sounds)

## Controls
- Move: **WASD** / Arrow keys
- Aim: **Mouse**
- Shoot: **Left Click** or **SPACE**
- Time Rewind: **E** (only after picking up the power-up and charge completes)
- Restart after death: **R**
- Quit: **ESC**

## Run locally
```bash
# create/activate your env as you like, then:
pip install pygame
python neon_arena.py
