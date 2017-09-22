#!/usr/bin/env python3
"""
  This program...
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

STRAIGHT_TIME_MS = 1500


class DataContainer(object):
    """ Since this program is intentionally not using the robot_controller Snatch3r class it merged the motor object
        into the DataContainer class for convenience.  You should separate your robot Snatch3r class out.  Things
        like motors don't really belong in the DataContainer class."""

    def __init__(self):
        """ Ugly merge of motor objects into the data container class for convenience. """

        # By having all the motors in the data container you don't have to pass them individually to functions.
        self.left_motor = ev3.LargeMotor(ev3.OUTPUT_B)
        self.right_motor = ev3.LargeMotor(ev3.OUTPUT_C)
        self.arm_motor = ev3.MediumMotor(ev3.OUTPUT_A)
        assert self.left_motor.connected
        assert self.right_motor.connected
        assert self.arm_motor.connected

        self.touch_sensor = ev3.TouchSensor()
        assert self.touch_sensor

        # Variable used to exit this program and end the while loop.
        self.exit_program = False

        # While the user is adding Forward (up), Back (down), Left, and Right commands is_running_commands if False
        # Once they hit Enter to start moving is_running_commands is True until complete
        self.is_running_commands = False

        # String that holds all of the commands, for example "FFFLFBB" would trace out a T shaped path
        # While adding commands with buttons F, L, R, or B is appended to the string
        # While running commands the first character is removed from the string.
        self.commands = ""

        # Flag to track if the arm is moving since the touch sensor is overloaded (used for two purposes).
        self.arm_is_moving = False


def main():
    print("--------------------------------------------")
    print("Hit the touch sensor to move the arm")
    print("Buttons up, down, left, right program moves")
    print("Then hit Enter to run your commands")
    print("Use Back button to exit")
    print("--------------------------------------------")

    ev3.Leds.all_off()  # Turn the leds off (optional)
    dc = DataContainer()  # Optional class to help you pass around data between different button events.

    # Buttons on EV3
    btn = ev3.Button()
    btn.on_up = lambda state: handle_up_button(state, dc)
    btn.on_down = lambda state: handle_down_button(state, dc)
    btn.on_left = lambda state: handle_left_button(state, dc)
    btn.on_right = lambda state: handle_right_button(state, dc)
    btn.on_enter = lambda state: handle_enter_button(state, dc)
    btn.on_backspace = lambda state: handle_shutdown(state, dc)

    ev3.Sound.speak("Ready")

    # Continue looping until the user presses the Back button to exit.
    while not dc.exit_program:
        btn.process()
        if dc.is_running_commands:
            if "running" not in dc.left_motor.state and "running" not in dc.right_motor.state:
                if len(dc.commands) == 0:
                    # ev3.Sound.speak("Mission complete")
                    ev3.Sound.play("awesome_pcm.wav")
                    dc.is_running_commands = False
                else:
                    execute_next_command(dc)
        elif not dc.arm_is_moving and dc.touch_sensor.is_pressed:
            dc.arm_is_moving = True
            play_song()  # None blocking version
            arm_calibration(dc)  # Note, this is a blocking command
        time.sleep(0.01)


# Movement handlers
def execute_next_command(dc):
    ev3.Sound.beep().wait()  # Fun little beep
    command = dc.commands[0]
    dc.commands = dc.commands[1:]
    if command == "F":
        print("Forward")
        dc.left_motor.run_timed(speed_sp=FAST_SPEED, time_sp=STRAIGHT_TIME_MS, stop_action="coast")
        dc.right_motor.run_timed(speed_sp=FAST_SPEED, time_sp=STRAIGHT_TIME_MS, stop_action="coast")
    elif command == "B":
        print("Back")
        dc.left_motor.run_timed(speed_sp=-FAST_SPEED, time_sp=STRAIGHT_TIME_MS, stop_action="coast")
        dc.right_motor.run_timed(speed_sp=-FAST_SPEED, time_sp=STRAIGHT_TIME_MS, stop_action="coast")
    elif command == "L":
        print("Left")
        turn_90(dc, True)
    elif command == "R":
        print("Right")
        turn_90(dc, False)
    else:
        print("Unknown command")
    time.sleep(0.2)  # See warning for wait_until on http://python-ev3dev.readthedocs.io/en/latest/motors.html


def turn_90(dc, is_left_turn):
    """Attempts to turn roughly 90 degrees."""
    motor_turns_deg = 440  # May require some tuning depending on your surface!
    left_position_sp = motor_turns_deg if is_left_turn else -motor_turns_deg
    dc.left_motor.run_to_rel_pos(position_sp=-left_position_sp, speed_sp=MEDIUM_SPEED)
    dc.right_motor.run_to_rel_pos(position_sp=left_position_sp, speed_sp=MEDIUM_SPEED)


def update_screen(dc):
    print("Commands: ", dc.commands)


# Functions that should be abstracted into method of a helper library class.
def arm_calibration(dc):
    """Runs the arm up until the touch sensor is hit then back down (beeping at both locations).
       Intended to be run with nothing in the jaws, but that isn't critical."""
    dc.arm_motor.run_forever(speed_sp=FAST_SPEED)
    time.sleep(2)  # Allow the user time to remove their figure from the button
    while not dc.touch_sensor.is_pressed:
        time.sleep(0.01)
    dc.arm_motor.stop(stop_action="brake")
    dc.arm_motor.run_to_rel_pos(position_sp=-SNATCH3R_ARM_DEGS)
    time.sleep(0.1)  # See warning for wait_until on http://python-ev3dev.readthedocs.io/en/latest/motors.html
    dc.arm_motor.wait_while("running")
    dc.arm_motor.position_sp = 0  # Calibrate the down position as 0.
    dc.arm_is_moving = False  # Allow the arm to be moved again now that it is complete


def play_song():
    """ From: http://python-ev3dev.readthedocs.io/en/latest/other.html#sound """
    # ev3.Sound.tone([
    #     (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
    #     (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
    #     (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
    #     (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
    #     (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
    #     (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
    #     (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
    #     (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
    #     (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
    #     (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
    #     (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
    #     (466.16, 25, 100), (587.32, 700, 100), (784, 350, 100), (392, 250, 100),
    #     (392, 25, 100), (784, 350, 100), (739.98, 250, 100), (698.46, 25, 100),
    #     (659.26, 25, 100), (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200),
    #     (554.36, 350, 100), (523.25, 250, 100), (493.88, 25, 100),
    #     (466.16, 25, 100), (440, 25, 100), (466.16, 50, 400), (311.13, 25, 200),
    #     (392, 350, 100), (311.13, 250, 100), (466.16, 25, 100),
    #     (392.00, 300, 150), (311.13, 250, 100), (466.16, 25, 100), (392, 700)
    # ])
    # I made the song just a little bit shorter so it doesn't take so long.
    ev3.Sound.tone([
        (392, 350, 100), (392, 350, 100), (392, 350, 100), (311.1, 250, 100),
        (466.2, 25, 100), (392, 350, 100), (311.1, 250, 100), (466.2, 25, 100),
        (392, 700, 100), (587.32, 350, 100), (587.32, 350, 100),
        (587.32, 350, 100), (622.26, 250, 100), (466.2, 25, 100),
        (369.99, 350, 100), (311.1, 250, 100), (466.2, 25, 100), (392, 700, 100),
        (784, 350, 100), (392, 250, 100), (392, 25, 100), (784, 350, 100),
        (739.98, 250, 100), (698.46, 25, 100), (659.26, 25, 100),
        (622.26, 25, 100), (659.26, 50, 400), (415.3, 25, 200), (554.36, 350, 100),
        (523.25, 250, 100), (493.88, 25, 100), (466.16, 25, 100), (440, 25, 100),
        (466.16, 50, 400), (311.13, 25, 200), (369.99, 350, 100),
        (311.13, 250, 100), (392, 25, 100), (466.16, 350, 100), (392, 250, 100),
        (466.16, 25, 100), (587.32, 700, 100)
    ])

# Event handlers
# Simply delete any contents of this template that you don't need for your application.


def handle_up_button(button_state, dc):
    """Handle IR / button event."""
    if button_state:
        if not dc.is_running_commands:
            dc.commands += "F"
            update_screen(dc)


def handle_down_button(button_state, dc):
    """Handle IR / button event."""
    if button_state:
        if not dc.is_running_commands:
            dc.commands += "B"
            update_screen(dc)


def handle_left_button(button_state, dc):
    """Handle IR / button event."""
    if button_state:
        if not dc.is_running_commands:
            dc.commands += "L"
            update_screen(dc)


def handle_right_button(button_state, dc):
    """Handle IR / button event."""
    if button_state:
        if not dc.is_running_commands:
            dc.commands += "R"
            update_screen(dc)


def handle_enter_button(button_state, dc):
    """Handle IR / button event."""
    if button_state:
        # Start processing commands (or cancel processing commands if appropriate)
        if dc.is_running_commands:
            dc.commands = ""  # About to stop. Clear all future commands
            dc.left_motor.stop(stop_action="coast")
            dc.right_motor.stop(stop_action="coast")
            dc.is_running_commands = False
        else:
            dc.is_running_commands = True


def handle_shutdown(button_state, dc):
    """Exit the program using the robot shutdown command."""
    if button_state:
        print("Goodbye")
        dc.left_motor.stop(stop_action="coast")
        dc.right_motor.stop(stop_action="coast")
        dc.arm_motor.stop(stop_action="coast")
        ev3.Sound.speak("Goodbye").wait()
        ev3.Leds.set_color(ev3.Leds.LEFT, ev3.Leds.GREEN)
        ev3.Leds.set_color(ev3.Leds.RIGHT, ev3.Leds.GREEN)
        # exit()
        dc.exit_program = True  # Decided to just let the while loop finish instead.

main()
