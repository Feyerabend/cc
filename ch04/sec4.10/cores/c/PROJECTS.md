
## Raspberry Pi Pico Display Projects

### Individual Work Structure

*Recommended Projects for Solo Work:*
- Drawing Canvas (Project 1)
- Game of Life (Project 2)
- Digital Clock (Project 5)
- Mandelbrot Extensions (Project 18)

*Individual Workflow:*
1. *Planning Phase (30-60 min)*
   - Sketch UI layout on paper
   - List required functions from existing codebase
   - Identify new functions needed
   - Create pseudocode for main game loop

2. *Implementation Phase (2-4 hours)*
   - Start with basic structure (init, main loop)
   - Implement one feature at a time
   - Test each feature before moving on
   - Use Git for version control

3. *Testing & Refinement (1-2 hours)*
   - Test edge cases
   - Optimize performance
   - Polish visual elements
   - Document your code

*Time Management Tips:*
- Use Pomodoro technique (25 min work, 5 min break)
- Set clear daily goals
- Keep a progress journal
- Celebrate small wins



### Group Work Structure (2-4 people)

*Recommended Projects for Groups:*
- Bouncing Ball Physics (Project 7)
- Platformer Game (Project 10)
- Flocking Behavior (Project 12)
- Ecosystem Simulator (Project 16)

*Role Distribution Examples:*

#### *Option A: Feature-Based Split*
- *Person 1:* Core game logic & state management
- *Person 2:* Rendering & visual effects
- *Person 3:* Input handling & UI
- *Person 4:* Testing & documentation

#### *Option B: Layer-Based Split*
- *Person 1:* Hardware abstraction (display, buttons)
- *Person 2:* Physics engine
- *Person 3:* Game objects & entities
- *Person 4:* Main loop & integration

#### *Option C: Component-Based Split (Platformer Example)*
- *Person 1:* Player character & controls
- *Person 2:* Level generation & collision
- *Person 3:* Enemy AI & spawning
- *Person 4:* Particles, sound, & effects

*Group Workflow:*

*Week 1: Planning & Architecture*
- *Day 1-2:* Group brainstorming session
  - Sketch the final product together
  - Create shared document with requirements
  - Define data structures (structs, globals)
  - Design header files (.h) collaboratively
  
- *Day 3:* Architecture design
  - Draw system diagram showing components
  - Define interfaces between components
  - Create shared constants/macros
  - Agree on naming conventions

- *Day 4-5:* Task assignment
  - Break project into independent modules
  - Assign modules to team members
  - Set up Git repository with branches
  - Create initial stub functions

*Week 2-3: Parallel Development*
- *Daily standup (15 min):*
  - What did you complete yesterday?
  - What will you work on today?
  - Any blockers?

- *Mid-week integration (1 hour):*
  - Merge completed modules
  - Test integration points
  - Resolve conflicts
  - Adjust interfaces if needed

- *End-of-week demo:*
  - Show progress to group
  - Discuss what's working/not working
  - Adjust timeline if needed

*Week 4: Integration & Polish*
- Combine all modules
- Extensive testing
- Performance optimization
- Documentation & presentation prep

*Communication Best Practices:*
- Use Discord/Slack for quick questions
- GitHub Issues for bug tracking
- Shared Google Doc for design decisions
- Weekly video calls for major discussions

*Code Integration Strategy:*
```
main branch (protected)
  ├── dev branch (integration)
  │   ├── feature/player-controls (Person 1)
  │   ├── feature/collision-system (Person 2)
  │   ├── feature/enemy-ai (Person 3)
  │   └── feature/particle-effects (Person 4)
```

*Merge Protocol:*
1. Complete feature on your branch
2. Test thoroughly
3. Create Pull Request to dev branch
4. At least one teammate reviews
5. Fix any issues found
6. Merge to dev
7. All teammates pull latest dev



### Individual + LLM Collaboration

*Effective LLM Usage Patterns:*

#### *1. Code Understanding Phase*
Ask the LLM to explain existing code:
```
"Explain how the display_blit_full() function works in this code:
[paste function]

Specifically, I want to understand:
- Why is it sending data in chunks?
- What does DMA do here?
- How does the framebuffer get transferred?"
```

#### *2. Design Phase*
Get architectural guidance:
```
"I want to build a Snake game using this display library. 
I need to:
- Track snake body segments
- Handle collision detection
- Render the snake and food

What data structures should I use? Show me the struct 
definitions and explain the tradeoffs."
```

#### *3. Implementation Phase*
Request specific code with context:
```
"Using the existing display.h API, write a function that:
- Draws a filled circle at position (x,y) with radius r
- Uses the display_draw_pixel() function
- Optimizes by only drawing necessary pixels
- Includes parameter validation

Here's the display.h file for reference: [paste header]"
```

#### *4. Debugging Phase*
Get help finding issues:
```
"This code should make particles bounce off walls, but they're 
getting stuck. Here's my update function: [paste code]

The particles have x,y positions and vx,vy velocities.
BOUNDS_LEFT=0, BOUNDS_RIGHT=320.
What's wrong with my boundary collision logic?"
```

#### *5. Optimisation Phase*
Improve performance:
```
"This particle rendering function is too slow (takes 50ms 
for 500 particles):
[paste code]

Can you:
- Identify the bottlenecks
- Suggest optimisations
- Show the improved code
- Explain why it's faster"
```

*LLM Best Practices for Individuals:*

*DO:*
- Provide full context (paste relevant code)
- Ask specific questions
- Request explanations of generated code
- Iterate on solutions ("That works, but now make it..")
- Use LLM to generate test cases
- Ask for multiple approaches and tradeoffs

*DON'T:*
- Copy-paste code blindly without understanding
- Skip reading the explanation
- Forget to test the generated code
- Let LLM make all design decisions
- Use it as a substitute for learning fundamentals

*Learning Workflow with LLM:*
```
1. Try to solve problem yourself (30 min)
2. If stuck, ask LLM for hints (not full solution)
3. Implement based on hints
4. If still stuck, ask LLM for solution
5. Study solution until you understand every line
6. Close LLM chat and rewrite solution from memory
7. Modify solution to add your own twist
```



### Group + LLM Collaboration

*Team-Wide LLM Strategies:*

#### *Strategy 1: The Architect Pattern*
One person acts as "LLM wrangler" for architecture:
```
Day 1: Architecture Design Session
- Designated person uses LLM to generate multiple 
  architecture proposals
- Team reviews proposals together
- Team votes on best approach
- Designated person asks LLM to refine chosen design
- Team reviews and finalizes
```

*Benefit:* Consistent architecture, one point of contact for design questions

#### *Strategy 2: The Specialist Pattern*
Each team member uses LLM for their module:
```
Person 1 (Physics): "How do I implement elastic collisions?"
Person 2 (Rendering): "Best way to draw sprites with transparency?"
Person 3 (AI): "Implement simple pathfinding for enemies"
Person 4 (Audio): "Generate tone frequencies for notes"
```

*Benefit:* Parallel progress, deep expertise in each area

*Weekly sync required:* Share LLM learnings with team

#### *Strategy 3: The Pair Review Pattern*
Use LLM as a "third pair of eyes":
```
- Developer writes code
- Teammate reviews code
- Both together ask LLM: "Review this code for bugs, 
  performance issues, and better practices"
- Team discusses LLM suggestions
- Implement improvements
```

*Benefit:* Catches more issues, team learns together

#### *Strategy 4: The Documentation Pattern*
Use LLM to maintain documentation:
```
After each integration:
1. Paste new code to LLM
2. Ask: "Generate API documentation for these functions"
3. Ask: "Create usage examples for the team"
4. Review and add to shared docs
```

*Benefit:* Always up-to-date docs, clear examples

*Group LLM Coordination:*

*Shared LLM Knowledge Base:*
Create a team document tracking:
- Useful prompts that worked well
- LLM-generated code that's been tested
- Patterns/solutions the LLM suggested
- Things the LLM got wrong (learn from mistakes)

*Weekly LLM Review Meeting (30 min):*
- What did LLM help you achieve this week?
- What prompts worked really well?
- What did LLM get wrong?
- What should we ask LLM about next week?

*LLM Ethics for Teams:*
```
Team Agreement:
- We use LLM as a learning tool, not a shortcut
- We understand all code before committing it
- We cite when LLM significantly helped with a solution
- We don't just copy-paste without testing
- We challenge each other to explain LLM-generated code
```



### Individual Projects

| Project | Complexity | Solo Time | LLM Time Saved | Key Challenges |
|---------|------------|-----------|----------------|----------------|
| Drawing Canvas | Easy | 4-6 hrs | 1-2 hrs | Button logic, cursor rendering |
| Game of Life | Easy-Med | 6-8 hrs | 2-3 hrs | Grid updates, optimization |
| Snake Game | Medium | 8-12 hrs | 3-4 hrs | Collision, body tracking |
| Starfield | Medium | 6-10 hrs | 2-3 hrs | 3D math, smooth animation |
| Clock | Easy-Med | 5-8 hrs | 1-2 hrs | Time math, hand rotation |


### Group Projects (2-4 people)

| Project | Complexity | Group Time | Coordination | Integration Effort |
|---------|------------|------------|--------------|--------------------|
| Ball Physics | Medium | 12-16 hrs | Medium | High (collision shared) |
| Maze Gen/Solve | Med-Hard | 16-20 hrs | Medium | Medium (clear interface) |
| Platformer | Hard | 20-30 hrs | High | High (many dependencies) |
| Flocking | Med-Hard | 16-24 hrs | Medium | Low (particles independent) |
| Ecosystem | Very Hard | 30-40 hrs | Very High | Very High (complex interactions) |



### Individual Work → You Learn:
- *Technical:* Full-stack embedded development
- *Problem-solving:* Debugging skills, algorithm design
- *Ownership:* Complete understanding of codebase
- *Time management:* Self-pacing, deadline management

### Group Work → You Learn:
- *Collaboration:* Git workflows, code review
- *Communication:* Technical writing, explaining code
- *Architecture:* Designing modular systems
- *Project management:* Task breakdown, timeline estimation
- *Integration:* Debugging interface issues, merge conflicts

### LLM Work → You Learn:
- *Prompt engineering:* Asking effective questions
- *Code review:* Evaluating generated solutions
- *Comparative analysis:* Choosing between multiple approaches
- *Documentation reading:* Understanding APIs and libraries
- *Abstraction:* Breaking down complex problems



### Example 1: Snake Game (Individual + LLM)

*Phase 1: Design (Use LLM as Brainstorming Partner)*
```
Prompt: "I'm building Snake for a 320x240 display with 4 buttons.
Help me design the data structures. The snake can have max 100 segments.
What's the best way to represent:
1. Snake body
2. Food position
3. Current direction
Show me the struct definitions and explain why."
```

*Phase 2: Implementation (Solo Work)*
- Write init function yourself
- Write basic game loop yourself
- *When stuck on collision:* Ask LLM for algorithm explanation

*Phase 3: Enhancement (LLM Assistance)*
```
Prompt: "Add scoring and high score tracking to my Snake game.
Show me how to:
1. Store high score (where?)
2. Draw score on screen using display_draw_string()
3. Detect when to update high score

Here's my current game state struct: [paste]"
```

### Example 2: Platformer (Group Project)

*Week 1: Architecture Design (Group + LLM)*

*Shared LLM Session (whole team together):*
```
Prompt: "We're 4 people building a platformer. Design a modular
architecture where we can work independently. We need:
- Player character with physics
- Level system with platforms
- Enemy AI
- Collision detection

Show us:
1. Main data structures (structs)
2. Module interfaces (.h files)
3. How modules communicate
4. What each person should work on"
```

*Team reviews LLM output together and adjusts.*

*Week 2-3: Parallel Development*

*Person 1 (Player):*
```
Individual LLM prompt: "I'm implementing the player character.
It needs jump physics with these properties:
- Jump height: 40 pixels
- Gravity: 0.5 pixels/frame
- Max fall speed: 10 pixels/frame

Calculate the initial jump velocity needed and show me the
physics update function."
```

*Person 2 (Levels):*
```
Individual LLM prompt: "I'm implementing level loading. Levels
are 320x240 with platforms. Show me:
1. Data structure for a platform (x, y, width, height)
2. Function to parse a level from a simple text format
3. Function to render all platforms

Keep it simple - just rectangles for now."
```

*Person 3 (Enemies):*
```
Individual LLM prompt: "Simple enemy AI that patrols between two
points. Enemy should:
- Walk back and forth
- Turn around at edges
- Detect player within 50 pixels

Show me the enemy struct and update function."
```

*Person 4 (Collision):*
```
Individual LLM prompt: "AABB collision detection for my platformer.
I have:
- Player rect (x, y, width, height)
- Platform array

Write a function that:
1. Returns true if player collides with any platform
2. Returns which side hit (top, bottom, left, right)
3. Is optimized for checking many platforms"
```

*Week 4: Integration*

*Group LLM prompt (together):*
```
"We're integrating our platformer modules. Here are the interfaces:
[paste all .h files]

We're having issues with:
1. Player falling through platforms sometimes
2. Enemy-player collision feels wrong
3. Performance drops with >10 enemies

Analyze our architecture and suggest:
1. What might be causing each issue
2. How to fix the integration
3. Better approach if needed"
```




### Template 1: Understanding Existing Code
```
"Analyze this [FUNCTION/FILE] from my Raspberry Pi Pico project:
[paste code]

Explain:
1. What does it do (high-level purpose)?
2. How does it work (step-by-step)?
3. What are the key techniques used?
4. Are there any subtle bugs or issues?
5. How could it be improved?

Keep explanations beginner-friendly but technically accurate."
```

### Template 2: Implementing New Feature
```
"I need to add [FEATURE] to my Pico display project.

Constraints:
- Display is 320x240, RGB565 color
- I have these functions available: [list key functions]
- Hardware: Raspberry Pi Pico (dual-core ARM)

Requirements:
- [List specific requirements]

Please provide:
1. Data structures needed
2. Pseudocode algorithm
3. Actual C implementation
4. Explanation of how it works
5. How to integrate with existing code: [paste relevant code]"
```

### Template 3: Debugging Help
```
"My [FEATURE] isn't working correctly.

Expected behavior: [describe what should happen]
Actual behavior: [describe what's happening]

Relevant code:
[paste the problematic function]

Context:
[paste relevant struct definitions, constants]

Please:
1. Identify the bug
2. Explain why it causes the observed behavior
3. Show the corrected code
4. Suggest how to prevent similar bugs"
```

### Template 4: Optimisation Request
```
"This function is a performance bottleneck:
[paste code]

Profiling shows it takes [X] ms for [Y] operations.
Target: Get it under [Z] ms.

Hardware: Raspberry Pi Pico (133 MHz, 264 KB RAM)

Please:
1. Identify specific performance issues
2. Suggest optimisations (with code)
3. Explain expected performance improvement
4. Note any tradeoffs (memory, complexity, etc.)"
```

### Template 5: Code Review
```
"Please review this code I wrote:
[paste code]

Review for:
1. Correctness (any bugs?)
2. Style (follows C best practices?)
3. Performance (any inefficiencies?)
4. Safety (buffer overflows, null checks, etc.)
5. Readability (clear variable names, comments?)

Be thorough but explain your reasoning for each suggestion."
```




### For Individuals:
- Can explain every line of your code
- Project works reliably (no crashes)
- Code is documented and readable
- Handled at least 3 edge cases
- Learned something new about embedded systems

### For Groups:
- All modules integrate cleanly
- Each person understands the whole system
- Git history shows good collaboration
- Documentation explains architecture
- Team can demo without preparation

### For LLM Usage:
- You can reproduce solutions without LLM
- You understood every suggestion before using it
- You caught at least one LLM mistake
- You improved on an LLM suggestion
- You can explain why solution works



### Additional Resources

*Version Control for Groups:*
- Learn Git branching: `learngitbranching.js.org`
- GitHub flow guide for teams
- Writing good commit messages

*Embedded Systems:*
- RP2040 datasheet (reference for optimization)
- Understanding DMA and SPI
- Real-time systems concepts

*LLM Prompt Engineering:*
- OpenAI prompt engineering guide
- How to ask good technical questions
- Evaluating AI-generated code

*Project Management:*
- Agile basics for small teams
- Kanban boards (Trello, GitHub Projects)
- Time estimation techniques

