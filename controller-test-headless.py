#!/usr/bin/env python3
"""
Controller diagnostic tool (headless) - shows all inputs from your controller
Press Ctrl+C to exit
"""
import pygame
import sys
import os

# Use dummy video driver (no display needed)
os.environ['SDL_VIDEODRIVER'] = 'dummy'

pygame.init()
pygame.joystick.init()

# Initialize controller
if pygame.joystick.get_count() == 0:
    print("ERROR: No controller detected!")
    print("Please connect a controller and try again.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("=" * 60)
print(f"Controller detected: {joystick.get_name()}")
print(f"Number of axes: {joystick.get_numaxes()}")
print(f"Number of buttons: {joystick.get_numbuttons()}")
print(f"Number of hats: {joystick.get_numhats()}")
print("=" * 60)
print("\nPress buttons, move sticks, and use D-pad...")
print("Watch the output below to see what's detected")
print("Press Ctrl+C to exit\n")

clock = pygame.time.Clock()
running = True

# Track last axis values to show changes
last_axes = [0.0] * joystick.get_numaxes()

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"✓ BUTTON DOWN: {event.button}")

            elif event.type == pygame.JOYBUTTONUP:
                print(f"  BUTTON UP:   {event.button}")

            elif event.type == pygame.JOYHATMOTION:
                print(f"⬆ HAT MOTION:  hat={event.hat} value={event.value}")

            elif event.type == pygame.JOYAXISMOTION:
                # Only show significant axis movements (ignore tiny drifts)
                if abs(event.value) > 0.2:
                    print(f"🕹 AXIS MOTION: axis={event.axis} value={event.value:7.3f}")

        # Poll axes continuously and show significant changes
        for i in range(joystick.get_numaxes()):
            value = joystick.get_axis(i)
            # Show if changed significantly
            if abs(value - last_axes[i]) > 0.3:
                print(f"🕹 AXIS {i}: {value:7.3f}")
                last_axes[i] = value

        clock.tick(30)

except KeyboardInterrupt:
    print("\n\nExiting...")

pygame.quit()
print("Done!")
