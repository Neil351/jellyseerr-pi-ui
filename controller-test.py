#!/usr/bin/env python3
"""
Controller diagnostic tool - shows all inputs from your controller
Press Ctrl+C to exit
"""
import pygame
import sys

pygame.init()
pygame.joystick.init()

# Create a small window
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Controller Test")

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

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"BUTTON DOWN: {event.button}")

            elif event.type == pygame.JOYBUTTONUP:
                print(f"BUTTON UP:   {event.button}")

            elif event.type == pygame.JOYHATMOTION:
                print(f"HAT MOTION:  hat={event.hat} value={event.value}")

            elif event.type == pygame.JOYAXISMOTION:
                # Only show significant axis movements (ignore tiny drifts)
                if abs(event.value) > 0.1:
                    print(f"AXIS MOTION: axis={event.axis} value={event.value:.3f}")

        # Also show current axis values
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 24)
        y = 20

        # Show axes
        for i in range(joystick.get_numaxes()):
            value = joystick.get_axis(i)
            text = font.render(f"Axis {i}: {value:7.3f}", True, (255, 255, 255))
            screen.blit(text, (20, y))
            y += 30

        # Show hats
        for i in range(joystick.get_numhats()):
            value = joystick.get_hat(i)
            text = font.render(f"Hat {i}: {value}", True, (255, 255, 0))
            screen.blit(text, (20, y))
            y += 30

        pygame.display.flip()
        clock.tick(30)

except KeyboardInterrupt:
    print("\nExiting...")

pygame.quit()
print("Done!")
