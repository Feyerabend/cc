
## Introduction to Games

Games have been part of human culture for thousands of years. From ancient board games
like *Senet* in Egypt (c. 3000 BCE) and *Go* in China to modern video games, the core
idea has always been the same: create a structured play experience with rules, goals,
and challenges. The invention of computers in the mid-20th century added a new dimension.
Early electronic games such as *Spacewar!* (1962) and *Pong* (1972) were simple in design,
yet they laid the foundation for the vast gaming industry we know today.

As technology advanced, so did games. Arcade machines in the 1970s and 1980s, home consoles
in the 1980s and 1990s, and handheld devices all shaped the way games were played. Modern
games now range from massive, photorealistic worlds to tiny puzzle apps on a watch. Yet,
at their heart, even the most complex games share common building blocks.



### Core Components of Games

Even small games usually include a few essential elements:
- Game world / state: The “memory” of the game. It keeps track of positions, scores,
  levels, lives, or whatever the game needs.
- Rules and mechanics: Define what players can and cannot do. For example, a ball
  bounces off walls, or a car cannot leave the road.
- Input: The way players interact with the game — buttons, joysticks, keyboards,
  or sensors.
- Output / feedback: How the game communicates back to the player. Traditionally
  visuals and sound, but in this case primarily small displays and LEDs.
- Challenge and progression: What makes the game engaging--levels get harder, time
  runs out, or the player must improve their skill.
- Loop: Almost every digital game runs in a loop:
    1. Read input
    2. Update the game state
    3. Draw the output
  .. and then repeat, often many times per second.



### Games and Hardware

But games have also pushed the envelope on hardware. Demands from game developers and
players have often driven progress in computing. Arcade games pushed video hardware and
sound chips forward in the 1970s. The home console wars of the 1980s and 1990s drove
advances in graphics, controllers, and storage media. Today, modern graphics processing
units (GPUs), which originated to accelerate 3D games, are essential in areas far beyond
entertainment--from scientific simulations to machine learning.

Even at the small scale, games influence hardware choices. The need for fast updates on
a handheld or embedded device forces careful design of displays, input methods, and power
use. In this sense, games are both a product of hardware and a driver of its evolution.



### Small Games on Small Hardware

When working with microcontrollers like the Raspberry Pi Pico and small displays such
as the Pimoroni Display Pack or Display Pack 2.0, we return to the spirit of early video
games. Hardware limitations mean graphics are simple, input may be restricted to just
a few buttons, and memory is scarce. But these constraints are not a disadvantage--they
encourage creativity. Classic arcade games like Breakout, Snake, or Asteroids were
built with similar limitations.



### Why Study Games?

Building small games is not only fun, it is also a powerful way to learn about:
- Programming loops and timing
- Graphics rendering on limited displays
- Handling input devices
- State machines and logic
- Creativity in design

From simple bouncing balls to more elaborate puzzle or racing games, each project
adds another layer of understanding. Just as early computer scientists learned from
playful experiments, so can we--by making games for these tiny but capable machines.

