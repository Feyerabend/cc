
## Crafting Code by Hand ..

This is mainly intended to illustrate how crafting was done before the era of LLMs.
It was largely about communicating the code and implementing ideas as they were formulated.
This process took time, even when we only created prototypes rather than fully implementing everything.
The programmer had to understand every part of the implementation, reading up on details—like,
in this case, Bézier curves or how to fill an area.

__Here's a fictional dialogue that sets the stage for developing a PostScript-like interpreter.
This story provides context for students (you) to understand client-developer interactions and
problem-solving in software projects.__

### The Client-Developer Meeting

Client: *Thanks for meeting with me. We have a bit of a tricky situation, and I hope you can help. We’ve lost access to a collection of PostScript-like samples that were critical for a system we use to communicate with printers and computers. Without these, a lot of our processes are stuck.*

Developer: I see. Can you tell me more about these samples? What kind of scripts are they, and what role do they play in your system?

Client: *Well, these scripts define things like how pages are laid out, fonts, images—basically everything that gets sent to printers or rendered on a screen. The problem is that we don’t fully understand how they work anymore. The team that originally handled them is long gone, and all we have left are scattered fragments of documentation.*

Developer: That sounds challenging. Do you have any surviving examples of the scripts that we can analyze?

Client: *That’s the other issue. These scripts are likely considered proprietary, and we haven’t been able to locate any of them yet. The company’s legal department is cautious about sharing them even internally, let alone with a developer. For now, assume we have no samples to work from.*

Developer: Hmm, so your goal is to create something that can handle these scripts without revealing them to others, correct? Essentially, you need a tool that you can keep in-house to interpret and analyze these files.

Client: *Exactly. And we want full ownership of the source code so we can explore the files further ourselves without depending on an outside developer. But we’re at a loss on where to start since we don’t even know what the scripts look like.*

Developer: Understood. It sounds like the best approach would be to build a PostScript-like interpreter from scratch. This would give you complete control over the source code and flexibility to handle the scripts as you discover more about them. I’d start by building a prototype with common features from PostScript, and as we learn more about your specific needs, we can refine it.

Client: *That sounds promising, but I have to admit—I don’t really understand how PostScript works. Can you give me a clearer picture of what you’re proposing?*

Developer: Of course. Think of PostScript as a language for describing graphical elements—lines, shapes, colors, text—and the logic for drawing them. It’s like a recipe for creating an image or a printed page. An interpreter reads these instructions, and a rasterizer converts the abstract graphics into pixels. We’d also include a graphics state, which keeps track of details like colors and line widths while drawing.

Client: *That makes sense. But if we don’t have any examples to test with, how do we ensure this works?*

Developer: Great question. To start, we can develop the interpreter with a set of generic examples based on what’s commonly found in PostScript. These will serve as stand-ins for your actual scripts. Once we have access to your real samples—assuming we’re allowed to see them—we can customize the interpreter further.

Client: *And this would all be delivered in source form so we can continue to explore it ourselves?*

Developer: Absolutely. My goal is to provide you with a clean, well-documented codebase. That way, you can extend or modify it as needed, even after our work together is complete. Think of it as a toolkit, designed to be as transparent and flexible as possible.

Client: *That sounds perfect. When can we get started?*

Developer: Right now, first we turn to the [interpreter](./interpret) ..


### Craftsman Philosophy and Methodology

This fictional exchange illustrates a craftsman's approach to problem-solving:

1. Understanding the Client's Needs:
   The developer listens carefully, identifying the client’s technical and practical challenges. They focus
   on transparency, ownership, and adaptability, aligning their work with the client’s constraints and goals.

2. Building Incrementally:
   Without immediate access to real samples, the developer proposes starting with a prototype based on general
   knowledge. This iterative approach allows for flexibility as new requirements emerge.

3. Empowering the Client:
   The developer emphasizes delivering source code that the client can understand and build upon. This aligns
   with the craftsman's philosophy of creating tools that are both functional and educational.

By focusing on clarity, collaboration, and craftsmanship, this approach demonstrates how to bridge the gap between
technical expertise and client expectations. For students, this dialogue provides a sketch for approaching
real-world software challenges with a problem-solving mindset.
