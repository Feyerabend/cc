
## Particle Systems & Dual-Core Communication


### Single-Core Projects

#### 1. *Rain Simulator*
Create realistic rainfall with varying drop sizes, speeds,
and splash effects when drops hit the ground.

*What you'll add:*
- Different particle sizes (small drops, heavy drops)
- Splash particles spawn when drops hit bottom
- Wind affects rain angle
- Lightning flashes (random screen fills with white)

*Key modifications:*
```python
# Add to particle array: [x, y, vx, vy, color, size, type]
# Type: 0=raindrop, 1=splash
# When raindrop hits ground, spawn 3-5 splash particles
# Splash particles move sideways and fade quickly
```

*Learning goals:* Particle lifecycle, spawning/destroying particles



#### 2. *Color Mixing Sandbox*
Interactive particle system where different colored particles "mix" when they collide, creating new colors.

*What you'll add:*
- Collision detection between particles
- Color blending algorithm (RGB565 color mixing)
- Particle merging (two colliding particles become one larger particle)
- Button to spawn new particles at random positions

*Key concepts:*
```python
def check_collision(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dist = (dx*dx + dy*dy)*0.5
    return dist < 5  # collision threshold

def mix_colors(color1, color2):
    # Extract RGB components from RGB565
    # Average them, convert back to RGB565
```

*Learning goals:* Collision detection, color math, array manipulation



#### 3. *Gravity Well Simulator*
Add controllable gravity points that attract or repel particles.

*What you'll add:*
- Array of gravity wells `[[x, y, strength], ...]`
- Buttons cycle through wells and change their strength
- Visual indicator for wells (pulsing circle)
- Particles accelerate toward/away from wells

*Key physics:*
```python
# For each particle, for each well:
dx = well[0] - p[0]
dy = well[1] - p[1]
dist = (dx*dx + dy*dy)*0.5
force = well[2] / (dist * dist)  # inverse square law
p[2] += (dx/dist) * force  # apply to velocity
p[3] += (dy/dist) * force
```

*Learning goals:* N-body physics, gravitational simulation



#### 4. *Fireworks Display*
Launch fireworks that explode into colorful particle bursts.

*What you'll add:*
- Rocket particles that rise with trail effect
- Explosion at peak height spawns 20-50 particles
- Radial explosion pattern (particles shoot outward)
- Particles fade over time (decrease color brightness)

*Implementation:*
```python
# Add to particle: [x, y, vx, vy, color, lifetime, type]
# Type: 0=rocket, 1=explosion particle
# When rocket reaches peak (vy > 0 -> vy < 0):
#   Create explosion particles at rocket position
#   Set velocities in circle: vx=cos(angle)*speed, vy=sin(angle)*speed
#   Remove rocket particle
```

*Learning goals:* Particle lifecycle, polar coordinates, timing



#### 5. *Lava Lamp Effect*
Slow-moving, blob-like particles that rise when hot and sink when cool.

*What you'll add:*
- Temperature property for each particle
- Buoyancy force (negative gravity when hot)
- Particles heat up at bottom, cool at top
- Larger particles (5x5 or 7x7 filled circles)
- Smooth color transitions (hot=red, medium=orange, cool=purple)

*Physics tweaks:*
```python
# Add temperature to particle array
TEMP_CHANGE_RATE = 0.02
if p[1] > BOUNDS_BOTTOM - 30:  # near bottom
    p[5] += TEMP_CHANGE_RATE  # heat up
elif p[1] < BOUNDS_TOP + 30:   # near top
    p[5] -= TEMP_CHANGE_RATE  # cool down

# Buoyancy based on temperature
buoyancy = -GRAVITY * (p[5] - 0.5) * 2
p[3] += buoyancy
```

*Learning goals:* Temperature simulation, buoyancy, smooth color gradients



### Dual-Core Projects

#### 6. *Particle Attractor Game*
Two cores control competing attractors, trying to capture particles.

*What you'll add:*
- Core 0 controls red attractor (buttons X/Y for position)
- Core 1 controls blue attractor (auto-moves or simulated input)
- Particles are "captured" when within radius
- Score display shows particle count for each team
- First to 100 particles wins

*Core architecture:*
```python
# Shared: attractor positions, particle array, scores
# Core 0: Update attractor0, physics half 1, render, input
# Core 1: Update attractor1, physics half 2, count captured

# Particles change color when captured
# Captured particles removed after 1 second
```

*Learning goals:* Competitive simulation, shared state management



#### 7. *Wave Interference Simulator*
Two wave sources create interference patterns using particles.

*What you'll add:*
- Two wave sources (one per core)
- Particles move up/down based on combined wave amplitude
- Create constructive/destructive interference patterns
- Buttons control wave frequency and amplitude

*Wave calculation:*
```python
# Core 0 calculates wave1 influence on first half of particles
# Core 1 calculates wave2 influence on second half
# Particle y-offset = sin(time * freq1 + distance1) + 
#                     sin(time * freq2 + distance2)
```

*Learning goals:* Wave physics, interference, trigonometry



#### 8. *Predator-Prey Ecosystem*
Simulate hunting behavior with two types of particles.

*What you'll add:*
- Prey particles (green) - flee from predators
- Predator particles (red) - chase prey
- Core 0: Updates prey behavior
- Core 1: Updates predator behavior
- Prey multiply when safe, predators multiply when fed
- Population graph in status bar

*Behavior algorithms:*
```python
# Prey: flee from nearest predator
def flee_from_predators(prey, predators):
    nearest = find_nearest(prey, predators)
    if distance(prey, nearest) < FLEE_RADIUS:
        # Move away from predator
        angle = atan2(prey[1]-nearest[1], prey[0]-nearest[0])
        prey[2] += cos(angle) * FLEE_SPEED
        prey[3] += sin(angle) * FLEE_SPEED

# Predator: chase nearest prey
def chase_prey(predator, preys):
    nearest = find_nearest(predator, preys)
    angle = atan2(nearest[1]-predator[1], nearest[0]-predator[0])
    predator[2] += cos(angle) * CHASE_SPEED
    predator[3] += sin(angle) * CHASE_SPEED
```

*Learning goals:* AI behavior, ecosystem dynamics, population control



#### 9. *Real-Time Data Visualiser*
Each core generates data (simulated sensor readings), particles visualize it.

*What you'll add:*
- Core 0: Generates "temperature" data (sine wave + noise)
- Core 1: Generates "pressure" data (different frequency)
- Particles spawn at rate proportional to data values
- Color represents data source
- Height represents magnitude
- Creates beautiful, real-time data visualization

*Visualization:*
```python
# Core 0 generates value, spawns N particles where N = value/10
# Particles start at bottom, rise to height = value
# When reaching target height, fade out
# Different colors for different data streams
```

*Learning goals:* Data visualization, time-series display



#### 10. *Particle Traffic Simulation*
Simulate traffic flow with cars (particles) following lanes.

*What you'll add:*
- 4 horizontal lanes
- Particles follow lane rules (stay in lane, don't overlap)
- Core 0: Updates vehicles in lanes 0-1
- Core 1: Updates vehicles in lanes 2-3
- Traffic lights control flow (red=stop, green=go)
- Collision avoidance (slow down if vehicle ahead)

*Traffic logic:*
```python
# Each particle has: [x, y, vx, vy, color, lane, target_speed]
# Check distance to vehicle ahead in same lane
# If too close, reduce speed
# If far enough, accelerate toward target_speed
# Traffic lights toggle every 3 seconds
```

*Learning goals:* Lane following, collision avoidance, state machines





### Single-Pico Projects (Using both cores on one device)

#### 11. *Text Scrambler/Unscrambler*
Real-time text encryption visualization.

*What you'll add:*
- Core 0: Takes USB input, displays original text on screen
- Core 1: Encrypts text, displays encrypted version
- Show both side-by-side on display
- Animate the encryption process (characters changing)
- Multiple encryption algorithms to choose from

*Display layout:*
```
[Original Text]
Hello World!
↓ [Encrypting...]
[Encrypted Text]
Ifmmp!Xpsme"
```

*Learning goals:* Text processing, visual feedback, parallel display updates



#### 12. *Password Strength Analyser*
Analyse password security using both cores.

*What you'll add:*
- Core 0: Checks password length, character variety
- Core 1: Checks against common password list, runs dictionary attack
- Display strength meter (weak/medium/strong)
- Show which criteria are met (length, uppercase, numbers, symbols)
- Time estimate to crack password

*Analysis tasks:*
```python
# Core 0 (fast checks):
- Length >= 8 characters
- Has uppercase, lowercase, numbers, symbols
- No repeated patterns

# Core 1 (intensive checks):
- Not in top 10000 common passwords
- Not based on dictionary words
- Entropy calculation
```

*Learning goals:* Parallel analysis, security concepts, real-time feedback



#### 13. *Code Compression Visualiser*
Compress/decompress data, visualise the process.

*What you'll add:*
- Core 0: Run-length encoding compression
- Core 1: LZ77-style compression
- Show original vs compressed size
- Animated bars showing compression ratio
- Test with different data types (text, patterns, random)

*Visualisation:*
```
Original:  ████████████████ 100%
RLE:       ██████           60%
LZ77:      ████             40%
```

*Learning goals:* Data compression, algorithm comparison, visualization



### Two-Pico Projects (UART Communication)

#### 14. *Secure Remote Control*
One Pico controls another's display/LEDs over encrypted UART.

*What you'll build:*

*Pico 1 (Controller):*
- Buttons send encrypted commands
- Commands: "LED_ON", "LED_OFF", "DISPLAY_RED", "DISPLAY_BLUE"
- Core 0: Button input, encryption
- Core 1: UART transmission
- Show sent commands on console

*Pico 2 (Receiver):*
- Receives encrypted commands via UART
- Core 0: UART receive, decryption
- Core 1: Execute commands (control LED/display)
- Show received commands on console

*Protocol:*
```
[2 bytes: length][N bytes: encrypted command][2 bytes: checksum]
```

*Learning goals:* Command protocols, wireless-like control, error checking



#### 14. *Distributed Sensor Network*
Two Picos share sensor data over encrypted link.

*What you'll build:*

*Pico 1:*
- Reads sensor (button as simulated sensor)
- Encrypts sensor data
- Sends to Pico 2 every second
- Core 0: Sensor reading, encryption
- Core 1: Data transmission

*Pico 2:*
- Receives encrypted sensor data
- Decrypts and displays on screen
- Graphs data over time
- Core 0: UART receive, decryption
- Core 1: Display update, graphing

*Data format:*
```python
# Packet structure
{
  'timestamp': 12345,
  'sensor_id': 'TEMP_01',
  'value': 23.5,
  'unit': 'C'
}
```

*Learning goals:* Sensor networks, data logging, visualization



#### 15. *Two-Player Pong*
Classic Pong game over UART between two Picos with displays.

*What you'll build:*

*Both Picos run same code:*
- Core 0: Game logic, rendering on local display
- Core 1: UART communication (send/receive paddle positions)
- Each Pico controls one paddle
- Ball physics synchronized via UART
- Score displayed on both screens

*Synchronization:*
```python
# Pico 1 is "master" - simulates ball
# Pico 2 is "client" - receives ball position
# Both send paddle positions 30 times per second
# Master sends ball position 30 times per second

# Packet: [PADDLE_POS, y_position] or [BALL_POS, x, y]
```

*Learning goals:* Game networking, synchronization, latency handling




#### 16. *Morse Code Communicator*
Send messages in Morse code, encrypted over UART.

*What you'll build:*

*Pico 1 (Sender):*
- Type message via USB serial
- Core 0: Convert to Morse code, encrypt
- Core 1: Send encrypted Morse over UART
- LED blinks out the Morse code visually

*Pico 2 (Receiver):*
- Core 0: Receive encrypted Morse, decrypt
- Core 1: Decode Morse to text, display on screen
- LED blinks received Morse code

*Morse encoding:*
```python
MORSE_CODE = {
    'A': '.-',    'B': '-...',  'C': '-.-.',
    # ... etc
}
# Convert text -> Morse -> encode timing -> encrypt -> send
# '.' = short pulse (100ms), '-' = long pulse (300ms)
# Letter gap = 300ms, word gap = 700ms
```

*Learning goals:* Signal encoding, timing protocols, audio-visual feedback



#### 17. *File Transfer System*
Transfer files between two Picos with progress display.

*What you'll build:*

*Pico 1 (Sender):*
- Reads file from simulated storage (array in memory)
- Splits into chunks, encrypts each chunk
- Core 0: File reading, encryption
- Core 1: UART transmission with flow control
- Progress bar on display

*Pico 2 (Receiver):*
- Receives encrypted chunks
- Core 0: UART receive, decryption
- Core 1: Reassembly, verification (checksum)
- Progress bar on display
- Saves to memory

*Protocol:*
```
[START][filename_len][filename][file_size]
[CHUNK_1][data][checksum]
[CHUNK_2][data][checksum]
...
[END][overall_checksum]

# Flow control: Receiver sends ACK after each chunk
```

*Learning goals:* File protocols, flow control, error recovery





#### 18. *Networked Particle System*
Two Picos with displays share particle simulations.

*What you'll build:*
- Each Pico runs particle simulation
- Particles can "teleport" between displays via UART
- When particle hits right edge of Pico 1, it appears on left edge of Pico 2
- Buttons create attraction forces visible on both displays
- Synchronized physics

*Synchronization:*
```python
# Pico 1 sends: [PARTICLE_TRANSFER, x, y, vx, vy, color]
# Pico 2 receives and spawns particle
# Also sync button presses: [BUTTON_PRESS, button_id, x, y]
# Both displays show attractors from both Picos
```

*Learning goals:* Distributed simulation, state synchronization



#### 19. *Competitive Particle Painter*
Two players compete to "paint" the screen with their color particles.

*What you'll build:*

*Both Picos:*
- Display shows shared canvas
- Each player launches colored particles
- Particles stick where they land
- Core 0: Local particle physics
- Core 1: UART sync of particle positions
- After 60 seconds, count pixels of each color
- Winner announced on both displays

*Scoring:*
```python
# Count pixels of each color in framebuffer
red_pixels = count_color(framebuffer, COLOR_RED)
blue_pixels = count_color(framebuffer, COLOR_BLUE)
# Display bar graph of coverage percentage
```

*Learning goals:* Multiplayer games, pixel counting, competition logic




### Individual Projects - Recommended Approach

*Week 1: Planning & Setup*
- Study the base code (main.py or encryptor.py)
- Sketch UI layout on paper
- List required modifications
- Create pseudocode for new features

*Week 2-3: Implementation*
- Implement one feature at a time
- Test thoroughly before moving to next
- Use print statements for debugging
- Keep Git commits small and descriptive

*Week 4: Polish*
- Optimise performance (especially rendering)
- Add visual feedback (colors, animations)
- Handle edge cases
- Document your code

### Group Projects - Recommended Approach

*Role Distribution for Particle Projects:*
```
Person 1: Physics & core logic
Person 2: Rendering & visual effects  
Person 3: Input handling & UI
Person 4: Performance optimization & testing
```

*Role Distribution for Communication Projects:*
```
Person 1: Encryption/protocol design
Person 2: UART communication layer
Person 3: Application logic
Person 4: Display/UI & error handling
```

*Weekly Schedule:*
```
Monday:    Team meeting - plan week's tasks
Tue-Thu:   Parallel development on branches
Friday:    Integration session - merge & test
Weekend:   Bug fixes, documentation
```




### For Particle Projects

*Phase 1: Understanding Physics*
```
Prompt: "Explain how collision detection works between moving 
particles. I have particles with [x, y, vx, vy] and need to:
1. Detect when two particles overlap
2. Calculate new velocities after collision
3. Keep it efficient for 200+ particles

Show me the algorithm and explain the math."
```

*Phase 2: Implementing Features*
```
Prompt: "I want to add color mixing to my particle system.
When two particles collide, they should merge and create a
new color. Here's my particle structure:
[x, y, vx, vy, color_rgb565]

Show me:
1. How to extract RGB from RGB565
2. How to average two colors
3. How to convert back to RGB565
4. The complete merge function"
```

*Phase 3: Optimization*
```
Prompt: "My particle rendering is slow (50ms for 200 particles).
Current code:
[paste render_particles function]

The particles are 3x3 filled rectangles. Can you:
1. Identify bottlenecks
2. Suggest optimizations
3. Show improved code
Remember: MicroPython on Pico, framebuffer is bytearray"
```

### For Communication Projects

*Phase 1: Protocol Design*
```
Prompt: "I'm designing a protocol for two Raspberry Pi Picos
to communicate over UART at 115200 baud. I need to send:
- Text messages (variable length)
- Commands (fixed format)
- Sensor data (structured)

Design a packet format that includes:
- Length header
- Data type identifier
- Payload
- Error checking (checksum)

Show the format and Python struct/unpack code."
```

*Phase 2: Encryption Understanding*
```
Prompt: "Explain how XOR encryption works with key rotation.
Current code uses:
result.append(byte ^ key[(i + offset) % key_len])

1. Why is XOR used?
2. What does key rotation mean?
3. What's the security level?
4. How could it be improved?
5. Show example with 'HELLO' and key 'KEY'"
```

*Phase 3: Error Handling*
```
Prompt: "My UART communication drops packets sometimes.
Help me add:
1. Retry mechanism (send 3 times if no ACK)
2. Sequence numbers (detect missing packets)
3. Timeout handling

Here's my current send/receive code:
[paste code]

Show the improved version with error handling."
```

### LLM Collaboration Patterns

*Pattern 1: Debug Partner*
```
Workflow:
1. Encounter bug, spend 20 minutes trying to fix
2. Document what you tried
3. Ask LLM: "I tried X, Y, Z but still see [behavior]"
4. LLM suggests approach
5. Try it, report back results
6. Iterate until fixed
```

*Pattern 2: Concept Teacher*
```
Workflow:
1. Need to implement unfamiliar algorithm
2. Ask LLM for high-level explanation
3. Request pseudocode
4. Implement yourself from pseudocode
5. If stuck, ask for hints (not full solution)
6. Compare your code to LLM's suggestion
```

*Pattern 3: Code Reviewer*
```
Workflow:
1. Complete feature
2. Ask LLM: "Review for bugs, efficiency, style"
3. Understand each suggestion
4. Decide which to apply
5. Test that changes work
6. Document why you made each change
```



### Template: Adding New Feature
```
"I'm extending this MicroPython particle system on Raspberry Pi Pico:
[paste relevant base code]

I want to add: [describe feature]

Constraints:
- MicroPython (no numpy, limited libraries)
- 264KB RAM, must be memory-efficient
- 60 FPS target
- Display is 320x240 RGB565

Please provide:
1. Data structure changes needed
2. Algorithm pseudocode
3. Complete implementation
4. Integration steps
5. Performance considerations

Keep code comments detailed for learning."
```

### Template: Debugging
```
"My MicroPython code has this issue:
Expected: [what should happen]
Actual: [what's happening]
Observed when: [conditions]

Relevant code:
[paste code]

Debug info:
[paste print output]

Please:
1. Identify likely cause
2. Explain the bug
3. Show fix with explanation
4. Suggest how to prevent similar issues"
```

### Template: Optimization
```
"This MicroPython code on Pico is too slow:
[paste code]

Measured performance: [X] ms
Target performance: [Y] ms

Constraints:
- Can't use external libraries
- Must maintain accuracy
- Limited to [RAM amount]

Analyze and provide:
1. Profiling insights (likely bottlenecks)
2. Specific optimizations
3. Improved code
4. Expected speedup
5. Tradeoffs explained"
```



### Beginner Path (Projects 1-5)
Start with single-core particle modifications:
1. Rain Simulator (easy)
2. Fireworks (medium)
3. Gravity Wells (medium-hard)

*Skills gained:* Array manipulation, basic physics, rendering

### Intermediate Path (Projects 6-10)
Move to dual-core particle systems:
1. Particle Attractor Game (medium)
2. Predator-Prey (hard)
3. Traffic Simulation (hard)

*Skills gained:* Multi-core coordination, AI behavior, complex state

### Advanced Path (Projects 14-18)
Tackle UART communication:
1. Secure Remote Control (medium)
2. Morse Communicator (medium-hard)
3. Two-Player Pong (hard)

*Skills gained:* Protocols, synchronization, networking

### Expert Path (Projects 19-20)
Combine everything:
1. Networked Particle System (very hard)
2. Competitive Painter (very hard)

*Skills gained:* Distributed systems, real-time sync, complex integration



### Challenge 1: Memory Exhaustion
```
Error: MemoryError
LLM Prompt: "My MicroPython Pico program crashes with MemoryError
when I have 200 particles. Each particle is array.array('f', [x,y,vx,vy,color]).
How can I:
1. Calculate exact memory usage
2. Reduce memory footprint
3. Use memory more efficiently
Show specific code improvements."
```

### Challenge 2: Slow Rendering
```
Problem: 15 FPS instead of 60 FPS
LLM Prompt: "My framebuffer rendering is slow. I call fill_rect 
for each 3x3 particle 200 times per frame. Current code:
[paste code]
How can I batch operations or optimize for speed?"
```

### Challenge 3: UART Data Corruption
```
Problem: Received data doesn't match sent data
LLM Prompt: "UART between two Picos corrupts data sometimes.
I'm sending encrypted bytes at 115200 baud. What could cause this?
Check my code for:
1. Buffer overflow issues
2. Timing problems
3. Missing synchronization
[paste relevant code]"
```

### Challenge 4: Core Synchronization
```
Problem: Cores accessing same data cause crashes
LLM Prompt: "My dual-core MicroPython program crashes intermittently.
Core 0 and Core 1 both modify 'particles' list. I use _thread.lock:
[paste code]
Am I using locks correctly? Show proper synchronization."
```


### Summary

| Project | Solo Time | Group Time | LLM Time Saved | Core Concepts |
|---------|-----------|------------|----------------|---------------|
| Rain Simulator | 4-6h | 2-3h | 1-2h | Spawning, lifecycle |
| Color Mixing | 6-8h | 3-4h | 2h | Collision, color math |
| Gravity Wells | 8-10h | 4-5h | 2-3h | N-body physics |
| Fireworks | 6-8h | 3-4h | 2h | Patterns, timing |
| Lava Lamp | 8-10h | 4-5h | 2-3h | Buoyancy, gradients |
| Particle Game | 10-12h | 5-6h | 3h | Multi-core, competition |
| Wave Interference | 12-15h | 6-8h | 3-4h | Wave math, sync |
| Predator-Prey | 15-20h | 8-10h | 4-5h | AI, ecosystems |
| Data Visualizer | 12-15h | 6-8h | 3-4h | Real-time display |
| Traffic Sim | 15-18h | 8-10h | 4h | State machines |
| Text Scrambler | 6-8h | 3-4h | 2h | Text processing |
| Password Analyzer | 8-10h | 4-5h | 2-3h | Security concepts |
| Secure Remote | 10-12h | 5-6h | 3h | Protocols, commands |
| Sensor Network | 12-15h | 6-8h | 3-4h | Data logging |
| Two-Player Pong | 15-20h | 8-10h | 4-5h | Game networking |
| Morse Code | 10-12h | 5-6h | 3h | Signal encoding |
| File Transfer | 18-22h | 10-12h | 5-6h | Protocols, flow control |
| Chat App | 12-15h | 6-8h | 3-4h | Text UI, graphics |
| Networked Particles | 20-25h | 12-15h | 6-7h | Distributed sim |
| Competitive Painter | 18-22h | 10-12h | 5-6h | Multiplayer, sync |


### For Individual Projects:
- [ ] Read base code thoroughly
- [ ] Run and understand existing functionality  
- [ ] Sketch UI/behavior on paper
- [ ] List 3-5 specific features to add
- [ ] Estimate time for each feature
- [ ] Set up Git repository
- [ ] Create development branch
- [ ] Start with simplest feature first

### For Group Projects:
- [ ] Hold kickoff meeting (all members)
- [ ] Choose project together
- [ ] Sketch architecture diagram
- [ ] Define interfaces between modules
- [ ] Assign roles/modules to members
- [ ] Set up shared Git repository
- [ ] Create feature branches for each person
- [ ] Schedule weekly integration meetings
- [ ] Set up communication channel (Discord/Slack)

### For LLM-Assisted Work:
- [ ] Understand base code without LLM first
- [ ] Try implementing feature yourself (30 min)
- [ ] Document what you tried
- [ ] Prepare specific questions for LLM
- [ ] Get LLM explanation/solution
- [ ] Study response until fully understood
- [ ] Close LLM and implement from memory
- [ ] Test and debug without LLM
- [ ] Only return to LLM if truly stuck


*You've succeeded when you can:*

- Explain every line of code you wrote
- Modify the code without referring to LLM output
- Debug issues independently first
- Teach the concept to someone else
- Extend the project with new features
- Optimize performance on your own
 Write comprehensive documentation

*For group projects, also:*

- All members understand the full codebase
- Code integrates without major issues
- Git history shows good collaboration
- Team can demo without preparation
- Documentation explains architecture
- Everyone contributed meaningfully

*For LLM usage:*

- You improved on at least one LLM suggestion
- You caught at least one LLM mistake
- You asked progressively better questions
- You used LLM to learn, not just to complete
- You can reproduce solutions without AI

