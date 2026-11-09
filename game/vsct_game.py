"""Visuospatial cue task (VSCT) for rats - touchscreen paradigm.


Run on the Raspberry Pi:   python vsct_game.py --chamber standard
                           python vsct_game.py --chamber degraded
Run without GPIO (desktop testing): python vsct_game.py --no-electronics

Keys on the start screen: RETURN start session, LEFT laser test pulse,
DOWN toggle pump cleaning, RIGHT habituation mode, ESC quit.


Sounds: sound_02.wav = correct response, sound_01.wav = incorrect / premature response.
"""
import argparse
import asyncio
import csv
import random
import sys
import time
from pathlib import Path

import pygame

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
CHAMBER = "standard"   # "standard" or "degraded" (chambers with electronic faults)
ELECTRONICS = True     # False: run without Raspberry Pi GPIO (desktop testing)

_parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
_parser.add_argument("--chamber", choices=["standard", "degraded"], default=CHAMBER)
_parser.add_argument("--no-electronics", action="store_true")
_args, _ = _parser.parse_known_args()
CHAMBER = _args.chamber
electronics = ELECTRONICS and not _args.no_electronics

if CHAMBER == "standard":
    REWARD_PIN = 11
    CLEAN_PIN = 13
    HABITUATION_PULSE = 5.0
else:  # "degraded"
    REWARD_PIN = 18
    CLEAN_PIN = 18
    HABITUATION_PULSE = 0.2
DEGRADED_REWARD_PULSE = 0.2

if electronics:
    import RPi.GPIO as GPIO

HERE = Path(__file__).resolve().parent


class game():
    def __init__(self, name="Rat paradigm"):
        pygame.init()
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(str(HERE / "sound_01.wav"))
        self.good_sound = pygame.mixer.Sound(str(HERE / "sound_02.wav"))
        self.sound.set_volume(1.0)
        self.good_sound.set_volume(1.0)
        self.sound_time = 1
        self.info = pygame.display.Info()
        self.size = self.w, self.h = self.info.current_w, self.info.current_h
        self.screen = pygame.display.set_mode(self.size, flags=pygame.FULLSCREEN)
        self.white = (255, 255, 255)
        self.red = (150, 0, 0)
        self.blue = (0, 25, 50)
        self.black = (0, 0, 0)
        self.gray = (150, 150, 150)
        self.input_colors = (self.white, self.gray)
        self.clock = pygame.time.Clock()

        self.gap_ratio = 0.7  ## how much horizontal space between buttons
        self.button_count = 3  ## number of buttons
        self.h_pos = self.h // 1.7  ##height at which buttons are displayed
        self.button_h = self.h // 5  ##height of buttons
        self.blink_speed = 0.2  ##speed at which b
        self.time_out = 5  ##time out time
        self.initial_ws = [self.w, self.w // 2, self.w // 5]  ##width of intiate button at trials 1, 2 and 3+ respectively
        self.initial_hs = [self.h // 3, self.h // 4, self.h // 6]  ##height of intiate button at trials 1, 2 and 3+ respectively
        self.black_time1 = 2
        self.laser_extension = 2.0  ## for stage 7
        self.laser_backwards_extension = 2.0  ## for stage 8
        self.max_trials = 450

        # Pseudorandom laser order: chunks of 10 trials, 50 % laser,
        # never more than max_reps_laser identical statuses in a row.
        self.laser_chunk_size = 10
        self.laser_ratio = 0.5
        self.max_reps_laser = 2
        self.laser_chunk_count = self.max_trials / self.laser_chunk_size
        if self.laser_chunk_count % 1 != 0:
            raise Exception("Maximum trial number must be a multiple of laser chunk size")
        if self.laser_chunk_size * self.laser_ratio % 1 != 0:
            raise Exception("Laser trials in laser chunk must be whole number")
        self.laser_chunk_count = int(self.laser_chunk_count)
        running = True
        while running:
            self.laser_lst = []
            for chunk_nr in range(self.laser_chunk_count):
                restart = False
                chunk_options = [int(self.laser_chunk_size * self.laser_ratio), int(self.laser_chunk_size * (1 - self.laser_ratio))]
                for pos in range(self.laser_chunk_size):
                    going = True
                    remaining_options = [False, True]
                    while going:
                        going = False
                        flip = 0
                        choice = random.choices(remaining_options, k=1)[0]
                        if (chunk_options[choice] == 0 or len(set(self.laser_lst[-self.max_reps_laser:] + [choice])) == 1) and len(self.laser_lst) >= self.max_reps_laser:
                            remaining_options.remove(choice)
                            going = True
                            if not remaining_options:
                                restart = True
                                break
                    if restart:
                        break
                    chunk_options[choice] -= 1
                    self.laser_lst.append(choice)
                if restart:
                    break
            if not restart:
                running = False

        # Pseudorandom cue position: chunks of 9 trials (3 per position),
        # never more than max_reps_choice identical positions in a row.
        self.choice_chunk_size = 9
        self.max_reps_choice = 2
        self.choice_chunk_count = self.max_trials / self.choice_chunk_size
        if self.choice_chunk_count % 1 != 0:
            raise Exception("Maximum trial number must be a multiple of choice chunks size")
        if self.choice_chunk_size / self.button_count % 1 != 0:
            raise Exception("Chunk size must be multiple of button count")
        self.choice_chunk_count = int(self.choice_chunk_count)
        running = True
        while running:
            self.choice_lst = []
            for chunk_nr in range(self.choice_chunk_count):
                restart = False
                chunk_options = [int(self.choice_chunk_size / self.button_count)] * self.button_count
                for pos in range(self.choice_chunk_size):
                    going = True
                    remaining_options = list(range(self.button_count))
                    while going:
                        going = False
                        flip = 0
                        choice = random.choices(remaining_options, k=1)[0]
                        if (chunk_options[choice] == 0 or len(set(self.choice_lst[-self.max_reps_choice:] + [choice])) == 1) and len(self.choice_lst) >= self.max_reps_choice:
                            remaining_options.remove(choice)
                            going = True
                            if not remaining_options:
                                restart = True
                                break
                    if restart:
                        break
                    chunk_options[choice] -= 1
                    self.choice_lst.append(choice)
                if restart:
                    break
            if not restart:
                running = False

        self.trial_count = 0
        self.clean = False
        self.habituation_event = pygame.USEREVENT

        self.button_w = self.w // (self.button_count + (self.button_count - 1) * (1 / self.gap_ratio) + 2 / (self.gap_ratio * 4))  ## for small gaps
        self.w_pos = []
        self.counters = [0] * self.button_count
        self.buttons = []
        for button_nr in range(self.button_count):
            self.w_pos.append((1 / (self.gap_ratio * 4) + button_nr * (1 + 1 / self.gap_ratio)) * self.button_w)  ##for small gaps
            self.buttons.append(pygame.Rect(self.w_pos[button_nr], self.h_pos, self.button_w, self.button_h))

    def intro(self):
        if electronics:
            GPIO.setmode(GPIO.BOARD)
            # Pin 7: TTL pulse to the laser
            GPIO.setup(7, GPIO.OUT)
            GPIO.output(7, 0)
            # Pin 11: reward pump (standard chambers)
            GPIO.setup(11, GPIO.OUT)
            GPIO.output(11, GPIO.LOW)
            # Pin 15: input from the Arduino, HIGH when the reward has been collected
            GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            # Pin 13: run the pump continuously for cleaning (standard chambers)
            GPIO.setup(13, GPIO.OUT)
            GPIO.output(13, 0)
            # Pin 16: house light
            GPIO.setup(16, GPIO.OUT)
            GPIO.output(16, 1)
            if CHAMBER == "degraded":
                # Pin 18: reward pump + cleaning ("degraded" chamber)
                GPIO.setup(18, GPIO.OUT)
                GPIO.output(18, 0)
        self.base_font = pygame.font.SysFont("arial", self.h // 25)
        self.category_font = pygame.font.SysFont("arial", self.h // 20)
        self.title_font = pygame.font.SysFont("arial", self.h // 10)
        self.user_input = {
            "name": "r",
            "stage": "5",
            "ITI": "3",
            "LH": "10",
            "CPT": "0.5",
            "BT2": "1.0",
        }
        self.parameter_h = self.h // 30
        self.parameter_w = self.w // 7
        self.input_rects = {
            "name": pygame.Rect(self.w // 2.7, self.h // 2.8, self.parameter_w, self.parameter_h),
            "stage": pygame.Rect(self.w // 1.8, self.h // 2.8, self.parameter_w, self.parameter_h),
            "ITI": pygame.Rect(self.w // 2.7, self.h // 2, self.parameter_w, self.parameter_h),
            "LH": pygame.Rect(self.w // 1.8, self.h // 2, self.parameter_w, self.parameter_h),
            "CPT": pygame.Rect(self.w // 2.7, self.h // 1.55, self.parameter_w, self.parameter_h),
            "BT2": pygame.Rect(self.w // 1.8, self.h // 1.55, self.parameter_w, self.parameter_h),
        }
        active = False
        for name, rect in self.input_rects.items():
            pygame.draw.rect(self.screen, self.white, rect)
            surf = self.category_font.render(name, True, self.white)
            self.screen.blit(surf,
                             (self.input_rects[name].x,
                              self.input_rects[name].y - self.input_rects[name].h * 1.5))
        for name, text in self.user_input.items():
            surf = self.base_font.render(text, True, self.black)
            self.screen.blit(surf,
                             (self.input_rects[name].x + self.input_rects[name].w // 20,
                              self.input_rects[name].y - self.input_rects[name].h // 10))
        surf = self.title_font.render("Rat paradigm", True, self.white)
        self.screen.blit(surf, (self.w // 2.7, self.h // 5))
        pygame.display.update()

        while True:
            flip = False
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for name, rect in self.input_rects.items():
                        if rect.collidepoint(event.pos):
                            active = name
                            flip = True
                    if flip == True:
                        for name, rect in self.input_rects.items():
                            pygame.draw.rect(self.screen, self.input_colors[active == name], rect)
                            surf = self.base_font.render(self.user_input[name], True, self.black)
                            self.screen.blit(surf,
                                             (self.input_rects[name].x + self.input_rects[name].w // 20,
                                              self.input_rects[name].y - self.input_rects[name].h // 10))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_RETURN:
                        self.screen.fill(self.black)
                        pygame.display.update()
                        time.sleep(2)
                        return
                    elif event.key == pygame.K_LEFT:
                        if electronics:
                            GPIO.output(7, 1)
                            time.sleep(0.5)
                            GPIO.output(7, 0)
                    elif event.key == pygame.K_DOWN:
                        self.clean = not self.clean
                        if electronics:
                            if self.clean == True:
                                GPIO.output(CLEAN_PIN, 1)
                            else:
                                GPIO.output(CLEAN_PIN, 0)

                    elif event.key == pygame.K_RIGHT:
                        self.screen.fill(self.black)
                        pygame.display.update()
                        habituation_count = 0
                        pygame.time.set_timer(self.habituation_event, 20000)  # change habituation parameters here
                        while True:
                            for event in pygame.event.get():
                                if event.type == pygame.KEYDOWN:
                                    if event.key == pygame.K_ESCAPE:
                                        pygame.quit()
                                        sys.exit()
                                if event.type == self.habituation_event:
                                    habituation_count += 1
                                    if habituation_count < 60:
                                        pygame.mixer.Sound.play(self.good_sound)
                                        if electronics:
                                            GPIO.output(REWARD_PIN, GPIO.HIGH)
                                        time.sleep(HABITUATION_PULSE)
                                        if electronics:
                                            GPIO.output(REWARD_PIN, GPIO.LOW)

                    elif active:
                        flip = True
                        if event.key == pygame.K_BACKSPACE:
                            self.user_input[active] = self.user_input[active][:-1]
                        else:
                            self.user_input[active] += event.unicode
                        pygame.draw.rect(self.screen, self.gray, self.input_rects[active])
                        self.screen.blit(self.base_font.render(self.user_input[active], True, self.black),
                                         (self.input_rects[active].x + self.input_rects[active].w // 20,
                                          self.input_rects[active].y - self.input_rects[active].h // 10))

            if flip:
                pygame.display.flip()
            self.clock.tick(60)

    def play(self):
        self.stage = int(self.user_input["stage"])
        self.iti = float(self.user_input["ITI"])
        self.initial_button_w = self.initial_ws[min(self.stage + 1, 2)]
        self.initial_button_h = self.initial_hs[min(self.stage + 1, 2)]
        self.initial_button = pygame.Rect(self.w // 2 - self.initial_button_w // 2, self.h - self.initial_button_h, self.initial_button_w, self.initial_button_h)
        self.playing = True
        self.repeat = False
        self.sleep = float(self.user_input["ITI"])
        with open(f"{self.user_input['name']}.csv", 'a', newline='') as file:
            writer = csv.writer(file, delimiter=",")
            writer.writerow(["Trial Number", "Initiation Time", "Response Time", "Trial Correct", "Correct Square", "Chosen Square", "Collection_latency", "Laser status"])
        while self.playing == True and self.trial_count < self.max_trials:
            if self.stage <= 1:
                self.idx = None
            self.next_timing = "cue"
            self.trial_correct = None
            self.chosen_rect = None
            self.response_time = None
            self.collection_time = None
            self.screen.fill(self.black)
            pygame.draw.rect(self.screen, self.white, self.initial_button)
            time.sleep(0.001)
            pygame.display.flip()
            pygame.event.clear()
            self.trial_stage = 0
            self.timing = False
            self.initiation_zero = time.time()
            self.response_zero = 0
            self.trial_running = True
            while self.trial_running == True:
                self.breaking = False
                if self.timing == True:
                    # All times below are relative to response_zero, i.e. 0.5 s before cue onset
                    # (laser TTL onset). Stage 7: cue extended on laser trials; stage >= 8: delay
                    # before the cue extended on laser trials.
                    if time.time() - self.response_zero > (float(self.user_input["LH"]) + float(self.user_input["CPT"]) + (self.stage == 7) * self.laser_status * self.laser_extension + self.laser_backwards_extension * self.laser_status * (self.stage >= 8) + 0.5 + float(self.user_input["BT2"])):
                        self.trial_running = False
                        self.screen.fill(self.black)
                        time.sleep(0.001)
                        pygame.display.update()
                        time.sleep(0.001)
                        break
                    if time.time() - self.response_zero > (float(self.user_input["CPT"]) + (self.stage == 7) * self.laser_status * self.laser_extension + self.laser_backwards_extension * self.laser_status * (self.stage >= 8) + 0.5 + float(self.user_input["BT2"])) and self.trial_stage == 1:

                        if self.stage == 3:
                            pygame.draw.rect(self.screen, self.gray, self.buttons[self.idx])
                        else:
                            for idx in range(self.button_count):
                                pygame.draw.rect(self.screen, self.gray, self.buttons[idx])
                        time.sleep(0.001)
                        pygame.display.update()
                        if electronics:
                            GPIO.output(16, 1)
                        self.trial_stage = 2
                    if self.next_timing == "black" and time.time() - self.response_zero > (float(self.user_input["CPT"]) + (self.stage == 7) * self.laser_status * self.laser_extension + self.laser_backwards_extension * self.laser_status * (self.stage >= 8) + 0.5) and self.trial_stage == 1:
                        self.screen.fill(self.black)
                        time.sleep(0.001)
                        pygame.display.update()
                        self.next_timing = "done"
                    if self.next_timing == "cue" and time.time() - self.response_zero > (0.5 + self.laser_backwards_extension * self.laser_status * (self.stage >= 8)) and self.trial_stage == 1:
                        if electronics:
                            GPIO.output(7, 0)
                        self.target((self.w_pos[self.idx], self.h_pos))
                        time.sleep(0.001)
                        pygame.display.flip()
                        self.next_timing = "black"
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                if pygame.mouse.get_pressed()[0]:
                    self.progression(mouse_pos=pygame.mouse.get_pos())
                pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            if electronics:
                GPIO.output(7, 0)
                time.sleep(0.001)
            with open(f"{self.user_input['name']}.csv", 'a', newline='') as file:
                writer = csv.writer(file, delimiter=",")
                writer.writerow([self.trial_count, self.initiation_time,
                                 self.response_time, self.trial_correct, self.idx, self.chosen_rect, self.collection_time, self.laser_status])
            if self.trial_correct == False or self.trial_correct == "PR":
                time.sleep(self.time_out - self.sound_time)
                self.screen.fill(self.black)
                if self.trial_correct == "PR" and electronics:
                    GPIO.output(16, 1)
                time.sleep(0.001)
                pygame.display.update()
                time.sleep(self.iti)
            elif self.trial_correct == None:
                time.sleep(self.iti)
        self.screen.fill(self.black)
        pygame.display.update()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def target(self, button_pos):
        target_thickness = self.button_h // 10
        target_size = self.button_h // 2
        vertical_line = pygame.Rect(button_pos[0] + self.button_w // 2 - target_thickness // 2, button_pos[1] + (self.button_h - target_size) // 2, target_thickness, target_size)
        horizontal_line = pygame.Rect(button_pos[0] + (self.button_w - target_size) // 2, button_pos[1] + self.button_h // 2 - target_thickness // 2, target_size, target_thickness)
        pygame.draw.rect(self.screen, self.gray, vertical_line)
        pygame.draw.rect(self.screen, self.gray, horizontal_line)

    async def blinking(self, blink_idx):
        pygame.mixer.Sound.play(self.good_sound)
        for reps in range(3):
            if type(blink_idx) == int:
                pygame.draw.rect(self.screen, self.gray, self.buttons[self.idx])
            else:
                pygame.draw.rect(self.screen, self.black, self.initial_button)
            await asyncio.sleep(0.001)
            pygame.display.flip()
            await asyncio.sleep(self.blink_speed)
            if type(blink_idx) == int:
                pygame.draw.rect(self.screen, self.black, self.buttons[self.idx])
            else:
                pygame.draw.rect(self.screen, self.white, self.initial_button)
            await asyncio.sleep(0.001)
            pygame.display.flip()
            await asyncio.sleep(self.blink_speed)
        pygame.mixer.Sound.stop(self.good_sound)
        if type(blink_idx) == int:
            self.trial_correct = True
        self.repeat = False
        self.screen.fill(self.black)
        await asyncio.sleep(0.001)
        pygame.display.flip()
        self.trial_running = False
        return

    async def reward(self):
        self.start_collection_time = time.time()
        if CHAMBER == "standard":
            # Pump runs until the Arduino reports collection (pin 15) or the ITI elapses.
            if electronics:
                GPIO.output(REWARD_PIN, GPIO.HIGH)
            while True:
                await asyncio.sleep(0.005)
                self.collection_time = time.time() - self.start_collection_time
                if electronics:
                    if self.iti - self.collection_time < 0 or GPIO.input(15) == 1:
                        break
                else:
                    if self.iti - self.collection_time < 0:
                        break
            if electronics:
                GPIO.output(REWARD_PIN, GPIO.LOW)
        else:
            # Fixed pulse; collection is not detected in the "degraded" chamber.
            if electronics:
                GPIO.output(REWARD_PIN, GPIO.HIGH)
            await asyncio.sleep(DEGRADED_REWARD_PULSE)
            if electronics:
                GPIO.output(REWARD_PIN, GPIO.LOW)
            self.collection_time = time.time() - self.start_collection_time
        return

    async def correct(self, blink_idx):
        task1 = asyncio.create_task(self.blinking(blink_idx))
        task2 = asyncio.create_task(self.reward())
        await asyncio.wait([task1, task2])
        await asyncio.sleep(max(0, self.iti - self.collection_time))

    def progression(self, mouse_pos):
        if self.trial_stage == 0:
            if self.initial_button.collidepoint(mouse_pos):
                self.breaking = True
                self.trial_count += 1
                self.initiation_time = time.time() - self.initiation_zero
                if self.stage >= 6:
                    self.laser_status = self.laser_lst.pop()
                else:
                    self.laser_status = False
                if self.stage <= 1:
                    self.trial_correct = True
                    asyncio.run(self.correct(blink_idx=False))
                    return
                self.screen.fill(self.black)
                time.sleep(0.001)
                pygame.display.update()
                time.sleep(self.black_time1 - 0.5)
                if electronics and self.stage >= 3:
                    GPIO.output(16, 0)
                if self.laser_status and electronics:
                    GPIO.output(7, 1)

                if self.repeat == False or self.stage >= 5:
                    self.idx = self.choice_lst.pop()
                self.response_zero = time.time()
                self.timing = True
                if self.stage == 2:
                    time.sleep(0.5)
                    if electronics:
                        GPIO.output(7, 0)
                    pygame.draw.rect(self.screen, self.gray, self.buttons[self.idx])
                    pygame.display.update()
                    self.trial_stage = 2
                else:
                    self.trial_stage = 1
                pygame.event.clear()
                return
        if self.trial_stage == 1 and self.next_timing == "black":
            # Premature response: touch after cue onset but before the choice stimuli appear.
            self.breaking = True
            self.response_time = time.time() - self.response_zero
            self.screen.fill(self.red)
            time.sleep(0.001)
            pygame.display.flip()
            pygame.mixer.Sound.play(self.sound)
            time.sleep(self.sound_time)
            pygame.mixer.Sound.stop(self.sound)
            self.repeat = True
            self.trial_correct = "PR"
            self.trial_running = False
            return

        if self.trial_stage == 2:
            if self.stage < 4:
                if self.buttons[self.idx].collidepoint(mouse_pos) == True:
                    self.breaking = True
                    self.chosen_rect = self.idx
                    self.response_time = time.time() - self.response_zero
                    asyncio.run(self.correct(self.idx))
                    return
            else:
                for idx in range(self.button_count):
                    if self.buttons[idx].collidepoint(mouse_pos) == True:
                        self.breaking = True
                        self.chosen_rect = idx
                        self.response_time = time.time() - self.response_zero
                        if idx == self.idx:
                            asyncio.run(self.correct(idx))
                            return
                        else:
                            self.trial_correct = False
                            self.screen.fill(self.red)
                            time.sleep(0.001)
                            pygame.display.flip()
                            pygame.mixer.Sound.play(self.sound)
                            time.sleep(self.sound_time)
                            pygame.mixer.Sound.stop(self.sound)
                            self.repeat = True
                            self.trial_running = False
                            return


if __name__ == "__main__":
    if electronics:
        try:
            this_game = game()
            this_game.intro()
            this_game.play()
        except Exception:
            pass
        finally:
            GPIO.output(7, GPIO.LOW)
            GPIO.output(11, GPIO.LOW)
            GPIO.output(13, GPIO.LOW)
            if CHAMBER == "degraded":
                GPIO.output(16, GPIO.LOW)
                GPIO.output(18, GPIO.LOW)
    else:
        this_game = game()
        this_game.intro()
        this_game.play()
