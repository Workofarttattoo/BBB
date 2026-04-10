#!/usr/bin/env python3
"""
HUMAN BEHAVIOR SIMULATOR - Realistic Mouse & Interaction Patterns
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This module provides realistic human-like behavior for web automation:
- Natural mouse movements with bezier curves
- Occasional misclicks (1 in 7-15 clicks)
- Random delays and hesitations
- Typing speed variations
- Scrolling patterns
- Inefficient but human-like navigation choices
"""

import random
import time
import math
from typing import Tuple, List
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement


class HumanBehaviorSimulator:
    """
    Simulates realistic human behavior for web automation.
    Makes bots undetectable by mimicking natural human patterns.
    """

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)
        self.click_counter = 0
        self.misclick_pattern = self._generate_misclick_pattern()

    def _generate_misclick_pattern(self) -> List[int]:
        """
        Generate a randomized misclick pattern.
        Returns list of click counts between misclicks.
        Example: [7, 6, 9, 11, 8, 10, 7, ...]
        """
        pattern = []
        for _ in range(100):  # Generate 100 intervals
            # Misclick every 7-15 clicks, weighted toward 7-10
            interval = random.choices(
                population=[7, 8, 9, 10, 11, 12, 13, 14, 15],
                weights=[25, 20, 15, 15, 10, 7, 5, 2, 1],
                k=1
            )[0]
            pattern.append(interval)
        return pattern

    def _should_misclick(self) -> bool:
        """Determine if this click should be a misclick."""
        self.click_counter += 1
        pattern_index = (self.click_counter // sum(self.misclick_pattern[:10])) % len(self.misclick_pattern)
        cumulative = 0

        for i, interval in enumerate(self.misclick_pattern):
            cumulative += interval
            if self.click_counter % cumulative == 0:
                return True

        # Fallback: roughly 1 in 10 clicks
        return random.random() < 0.10

    def bezier_curve(self, start: Tuple[int, int], end: Tuple[int, int], steps: int = 20) -> List[Tuple[int, int]]:
        """
        Generate a bezier curve path for natural mouse movement.
        Humans don't move in straight lines.
        """
        points = []

        # Generate control points for bezier curve
        x1, y1 = start
        x4, y4 = end

        # Add randomness to control points
        dx = x4 - x1
        dy = y4 - y1

        # Control point 1: roughly 1/3 of the way with offset
        x2 = x1 + dx * 0.33 + random.randint(-50, 50)
        y2 = y1 + dy * 0.33 + random.randint(-50, 50)

        # Control point 2: roughly 2/3 of the way with offset
        x3 = x1 + dx * 0.66 + random.randint(-50, 50)
        y3 = y1 + dy * 0.66 + random.randint(-50, 50)

        for i in range(steps + 1):
            t = i / steps

            # Cubic bezier formula
            x = (
                (1 - t) ** 3 * x1 +
                3 * (1 - t) ** 2 * t * x2 +
                3 * (1 - t) * t ** 2 * x3 +
                t ** 3 * x4
            )
            y = (
                (1 - t) ** 3 * y1 +
                3 * (1 - t) ** 2 * t * y2 +
                3 * (1 - t) * t ** 2 * y3 +
                t ** 3 * y4
            )

            points.append((int(x), int(y)))

        return points

    def human_move_to_element(self, element: WebElement):
        """
        Move mouse to element with human-like bezier curve motion.
        """
        # Get current mouse position (approximate - center of viewport)
        viewport_width = self.driver.execute_script("return window.innerWidth")
        viewport_height = self.driver.execute_script("return window.innerHeight")
        current_pos = (viewport_width // 2, viewport_height // 2)

        # Get element position
        location = element.location
        size = element.size
        target_pos = (
            location['x'] + size['width'] // 2,
            location['y'] + size['height'] // 2
        )

        # Generate bezier curve path
        path = self.bezier_curve(current_pos, target_pos, steps=random.randint(15, 30))

        # Move along path with varying speed
        for i, (x, y) in enumerate(path):
            # Humans slow down near the target
            if i < len(path) * 0.7:
                delay = random.uniform(0.001, 0.005)  # Fast movement
            else:
                delay = random.uniform(0.01, 0.02)  # Slow down near target

            time.sleep(delay)

        # Final move to element
        ActionChains(self.driver).move_to_element(element).perform()

        # Small hesitation before click
        time.sleep(random.uniform(0.05, 0.15))

    def human_click(self, element: WebElement):
        """
        Click element with human-like behavior including occasional misclicks.
        """
        # Move to element naturally
        self.human_move_to_element(element)

        # Check if we should misclick
        if self._should_misclick():
            print("[HUMAN] Simulating misclick...")

            # Misclick: Click slightly off target
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)

            ActionChains(self.driver).move_to_element_with_offset(
                element, offset_x, offset_y
            ).click().perform()

            # Realize mistake, pause
            time.sleep(random.uniform(0.3, 0.7))

            # Move back to correct element
            self.human_move_to_element(element)

        # Actual click
        element.click()

        # Random post-click delay
        time.sleep(random.uniform(0.1, 0.3))

    def human_type(self, element: WebElement, text: str):
        """
        Type text with human-like speed variations and occasional typos.
        """
        element.click()
        time.sleep(random.uniform(0.1, 0.3))

        for i, char in enumerate(text):
            # Typing speed variation
            base_delay = random.uniform(0.08, 0.15)

            # Humans type faster in the middle of words
            if i > 0 and i < len(text) - 1:
                base_delay *= random.uniform(0.7, 0.9)

            # Occasional typo (5% chance)
            if random.random() < 0.05 and i < len(text) - 1:
                # Type wrong character
                wrong_chars = 'qwertyuiopasdfghjklzxcvbnm'
                wrong_char = random.choice(wrong_chars)
                element.send_keys(wrong_char)
                time.sleep(base_delay)

                # Realize mistake, pause
                time.sleep(random.uniform(0.2, 0.5))

                # Backspace
                element.send_keys('\ue003')  # BACKSPACE
                time.sleep(base_delay)

            # Type correct character
            element.send_keys(char)
            time.sleep(base_delay)

        # Pause after typing
        time.sleep(random.uniform(0.2, 0.5))

    def human_scroll(self, direction: str = "down", amount: int = None):
        """
        Scroll page with human-like patterns (not smooth, has pauses).
        """
        if amount is None:
            amount = random.randint(300, 600)

        # Humans scroll in bursts, not smoothly
        bursts = random.randint(3, 7)
        scroll_per_burst = amount // bursts

        for i in range(bursts):
            if direction == "down":
                self.driver.execute_script(f"window.scrollBy(0, {scroll_per_burst});")
            else:
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_per_burst});")

            # Random pause between scroll bursts
            time.sleep(random.uniform(0.1, 0.4))

            # Occasional longer pause (reading)
            if random.random() < 0.3:
                time.sleep(random.uniform(0.5, 1.5))

    def inefficient_navigation(self, target_element: WebElement, other_elements: List[WebElement]):
        """
        Navigate inefficiently like a human - look at other things first.
        Humans don't always take the most direct path.
        """
        # 40% chance to look at other elements first
        if random.random() < 0.4 and other_elements:
            # Look at 1-3 other elements
            num_distractions = random.randint(1, min(3, len(other_elements)))
            distractions = random.sample(other_elements, num_distractions)

            for distraction in distractions:
                print("[HUMAN] Looking at other element first (inefficient navigation)...")
                self.human_move_to_element(distraction)
                time.sleep(random.uniform(0.3, 0.8))

        # Finally go to target
        self.human_click(target_element)

    def reading_pause(self, content_length: int = None):
        """
        Simulate human reading time based on content length.
        """
        if content_length:
            # Average reading speed: 200-250 words per minute
            # Assume ~5 chars per word
            words = content_length / 5
            reading_time = (words / 225) * 60  # seconds
            actual_time = reading_time * random.uniform(0.7, 1.3)  # Variation
        else:
            # Default: random pause
            actual_time = random.uniform(2, 8)

        print(f"[HUMAN] Reading pause: {actual_time:.1f} seconds")
        time.sleep(actual_time)

    def random_mouse_movement(self):
        """
        Occasional random mouse movements (humans fidget).
        """
        if random.random() < 0.15:  # 15% chance
            print("[HUMAN] Random mouse fidget...")

            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")

            # Move to random location
            random_x = random.randint(100, viewport_width - 100)
            random_y = random.randint(100, viewport_height - 100)

            self.driver.execute_script(f"""
                var event = new MouseEvent('mousemove', {{
                    clientX: {random_x},
                    clientY: {random_y}
                }});
                document.dispatchEvent(event);
            """)

            time.sleep(random.uniform(0.1, 0.3))

    def natural_page_arrival_behavior(self):
        """
        Simulate natural behavior when arriving at a new page.
        """
        # Initial load pause
        time.sleep(random.uniform(0.5, 1.5))

        # Scroll down a bit to see the page
        self.human_scroll("down", amount=random.randint(100, 300))

        # Small pause (orientation)
        time.sleep(random.uniform(0.3, 0.8))

        # Maybe scroll back up
        if random.random() < 0.3:
            self.human_scroll("up", amount=random.randint(50, 150))
            time.sleep(random.uniform(0.2, 0.5))


# Usage Example
if __name__ == "__main__":
    from selenium import webdriver
    from selenium.webdriver.common.by import By

    driver = webdriver.Chrome()
    human = HumanBehaviorSimulator(driver)

    try:
        driver.get("https://example.com")

        # Natural page arrival
        human.natural_page_arrival_behavior()

        # Find elements
        elements = driver.find_elements(By.TAG_NAME, "a")

        if len(elements) > 2:
            # Click target with inefficient navigation
            human.inefficient_navigation(
                target_element=elements[1],
                other_elements=elements[2:5]
            )

    finally:
        time.sleep(2)
        driver.quit()
