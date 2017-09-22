#!/usr/bin/env python3
"""
  This is a demo program that is used on the first day of robot programming
  to have a little fun using the robot before getting down to programming.
  The code in this module is meant to be stand alone, but in a real project
  you'd divide different parts into different classes to allow for easier
  layers of abstraction.

  Use the IR remote control to test the motors on the Snatch3r robot.
  IR remote channel 1 to drive the crawler tracks around
  IR remote channel 2 to raise and lower the arm.
"""

import ev3dev.ev3 as ev3
import time

# A few global constants.
# In general don't use global variables, but Dr. Fisher doesn't mind for constants. :)
SNATCH3R_ARM_REVS = 14.2
SNATCH3R_ARM_DEGS = SNATCH3R_ARM_REVS * 360

# Full range of speeds is -900 to +900 (0 is stopped)
SLOW_SPEED = 200
MEDIUM_SPEED = 400
FAST_SPEED = 700
MAX_SPEED = 900


def main():
    print("--------------------------------------------")
    print("Running Snatch3r IR hardware test program")
    print(" - Use IR remote channel 1 to drive around")
    print(" - Use IR remote channel 2 to for the arm")
    print(" - Press backspace button on EV3 to exit")
    print("--------------------------------------------")

    ev3.Leds.all_off()  # Turn the leds off

    # Connect two large motors on output ports B and C and medium motor on A
    left_motor = ev3.LargeMotor(ev3.OUTPUT_B)
    right_motor = ev3.LargeMotor(ev3.OUTPUT_C)
    arm_motor = ev3.MediumMotor(ev3.OUTPUT_A)

    # Check that the motors are actually connected
    assert left_motor.connected
    assert right_motor.connected
    assert arm_motor.connected

    # Only using 1 sensor in this program
    touch_sensor = ev3.TouchSensor()  # address=in1
    assert touch_sensor

    # Remote control channel 1 is for driving the crawler tracks around.
    rc1 = ev3.RemoteControl(channel=1)
    assert rc1.connected
    rc1.on_red_up = lambda state: handle_ir_move_button(state, left_motor, ev3.Leds.LEFT, 1)
    rc1.on_red_down = lambda state: handle_ir_move_button(state, left_motor, ev3.Leds.LEFT, -1)
    rc1.on_blue_up = lambda state: handle_ir_move_button(state, right_motor, ev3.Leds.RIGHT, 1)
    rc1.on_blue_down = lambda state: handle_ir_move_button(state, right_motor, ev3.Leds.RIGHT, -1)

    # Remote control channel 2 is for moving the arm up and down.
    rc2 = ev3.RemoteControl(channel=2)
    assert rc2.connected
    rc2.on_red_up = lambda state: handle_arm_up_button(state, arm_motor, touch_sensor)
    rc2.on_red_down = lambda state: handle_arm_down_button(state, arm_motor)
    rc2.on_blue_up = lambda state: handle_calibrate_button(state, arm_motor, touch_sensor)

    # Allows testing of the arm without the IR remote
    btn = ev3.Button()
    btn.on_up = lambda state: handle_arm_up_button(state, arm_motor, touch_sensor)
    btn.on_down = lambda state: handle_arm_down_button(state, arm_motor)
    btn.on_left = lambda state: handle_calibrate_button(state, arm_motor, touch_sensor)
    btn.on_right = lambda state: handle_calibrate_button(state, arm_motor, touch_sensor)
    btn.on_backspace = lambda state: handle_shutdown(state)

    ev3.Sound.speak("Ready")
    arm_calibration(arm_motor, touch_sensor)

    while True:
        rc1.process()
        rc2.process()
        btn.process()
        time.sleep(0.01)


# Event handlers
def handle_ir_move_button(ir_button_state, motor, led_side, direction):
    """Handles all four buttons for the IR remote channel 1. Use the
       lambda function to properly set the motor, led, and direction."""
    if ir_button_state:
        # Move when the button is pressed
        # Full speed is -900 to 900
        motor.run_forever(speed_sp=MEDIUM_SPEED * direction)
        if direction > 0:
            led_color = ev3.Leds.GREEN
        else:
            led_color = ev3.Leds.RED
        ev3.Leds.set_color(led_side, led_color)
    else:
        # Stop when the button is released
        motor.stop(stop_action="coast")
        ev3.Leds.set(led_side, brightness_pct=0)


def handle_arm_up_button(button_state, arm_motor, touch_sensor):
    """Moves the arm up when the button is pressed."""
    if button_state:
        arm_up(arm_motor, touch_sensor)


def handle_arm_down_button(button_state, arm_motor):
    """Moves the arm down when the button is pressed."""
    if button_state:
        arm_down(arm_motor)


def handle_calibrate_button(button_state, arm_motor, touch_sensor):
    """Has the arm go up then down to fix the starting position."""
    if button_state:
        arm_calibration(arm_motor, touch_sensor)


def handle_shutdown(button_state):
    """Exit the program using the robot shutdown command."""
    if button_state:
        print("Goodbye")
        ev3.Sound.speak("Goodbye").wait()
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.GREEN)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.GREEN)
        exit()  # CONSIDER: Might instead setup a DataContainer to just finish the while loop by changing a variable.


# Functions that should be abstracted into method of a helper library class.
def arm_down(arm_motor):
    """Moves the Snatch3r arm to the down position."""
    arm_motor.run_to_abs_pos(speed_sp=MAX_SPEED, position_sp=0, stop_action="coast")
    time.sleep(0.2)  # See the warning for wait_until http://python-ev3dev.readthedocs.io/en/latest/motors.html
    arm_motor.wait_while("running")  # Blocks until the motor finishes running
    ev3.Sound.beep().wait()


def arm_up(arm_motor, touch_sensor):
    """Moves the Snatch3r arm to the up position."""
    arm_motor.run_forever(speed_sp=MAX_SPEED)
    while not touch_sensor.is_pressed:
        time.sleep(0.01)
    arm_motor.stop(stop_action="coast")
    ev3.Sound.beep().wait()


def arm_calibration(arm_motor, touch_sensor):
    """Runs the arm up until the touch sensor is hit then back down (beeping at both locations).
       Intended to be run with nothing in the jaws, but that isn't critical."""
    arm_motor.run_forever(speed_sp=MAX_SPEED)
    while not touch_sensor.is_pressed:
        time.sleep(0.01)
    arm_motor.stop(stop_action="brake")
    ev3.Sound.beep().wait()
    arm_motor.run_to_rel_pos(position_sp=-SNATCH3R_ARM_DEGS)
    arm_motor.wait_while("running")
    arm_motor.position = 0  # Calibrate the down position as 0.
    ev3.Sound.beep().wait()


main()
