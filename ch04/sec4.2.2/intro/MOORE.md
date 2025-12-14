
## Moore's Law and Dennard Scaling

Moore’s Law and Dennard Scaling are two foundational concepts in the history of microelectronics and computer
architecture. They originated in the mid-to-late 20th century and shaped the trajectory of computing performance
for decades, setting expectations for both the pace of progress and the nature of technological development.


### Moore

Moore’s Law was first formulated by Gordon E. Moore in 1965, when he observed that the number of transistors on
an integrated circuit was doubling approximately every year. Ten years later, he revised the estimate to a
doubling every two years, which became the widely cited version of the law. Moore’s observation was not a
physical necessity but an empirical trend that held remarkably well for several decades. The law came to symbolise
the rapid pace of innovation in semiconductor manufacturing, enabling exponential improvements in processing speed
memory density, and cost efficiency. As more transistors could be packed into the same chip area, devices became
both more powerful and less expensive. This facilitated the explosive growth of personal computing, mobile devices,
and later cloud infrastructure and AI systems.

However, by the mid-2010s, Moore’s Law began to slow. Physical limitations, such as quantum tunnelling at nanometer
scales, increasing fabrication costs, and limits of photolithography, made continued doubling at historical rates
increasingly difficult. While transistor counts are still increasing, they are doing so more slowly, and with
diminishing returns in raw performance or cost per transistor. As a result, modern advancements rely more on
architectural improvements, parallel processing, specialised accelerators, and 3D chip designs than on transistor
scaling alone.


### Dennard

Dennard Scaling, formulated by Robert Dennard and colleagues in 1974, complements Moore’s Law by addressing power
consumption. The core idea was that as transistors shrink in size, their power requirements also decrease in such
a way that power density (power per unit area) remains constant. Specifically, if transistor dimensions scale by
a factor of $\kappa$, then voltage and current also scale by $\kappa$, leading to reduced power per transistor. As a
result, it became possible to build faster chips with more transistors without increasing the total power
consumption or heat dissipation, which was crucial for maintaining performance improvements.

Dennard Scaling was especially important during the era of frequency scaling, from the 1980s to the early 2000s,
when CPUs increased their clock speeds dramatically. However, around 2005, Dennard Scaling broke down. Transistor
dimensions could still be reduced, but voltage scaling could not continue due to threshold voltage limits. This
led to a significant rise in power density as frequencies increased, resulting in thermal issues and the
so-called “power wall.” Consequently, manufacturers stopped pushing clock speeds and turned to multicore processors
and parallelism as a way forward.

The breakdown of both Moore’s Law and Dennard Scaling has deeply influenced modern computing. The industry now
emphasises energy-efficient computing, domain-specific accelerators like GPUs and TPUs, and advanced packaging
techniques like chiplets and 3D stacking. Parallelism and concurrency have become central to both hardware
design and software development. The shift away from generic scaling has also given rise to the term
“More than Moore,” denoting an era focused on heterogeneous integration and specialised architectures rather
than simply increasing transistor density.

To summarise the relationship and historical trajectory of Moore’s Law and Dennard Scaling:

| Concept         | Moore's Law                           | Dennard Scaling                              |
|-----------------|---------------------------------------|----------------------------------------------|
| Focus           | Transistor count                      | Power efficiency & scaling                   |
| Proposed by     | Gordon Moore (1965)                   | Robert Dennard (1974)                        |
| Key Observation | Transistors double every ~2 years     | Power stays constant as transistors shrink   |
| Duration        | Held ~1970s–2010s (slowing now)       | Held ~1970s–2005 (broken)                    |
| Modern Status   | Slowed; now aided by chiplets, 3D ICs | Broken; replaced by parallel and efficient designs |

As we look to the future, these concepts continue to influence how we think about scaling and performance,
even if the original formulations no longer hold strictly. They serve as historical anchors in understanding
why computing has developed the way it has and how we might navigate its next challenges.


### References

G. E. Moore, "Cramming more components onto integrated circuits", *Electronics*, vol. 38, no. 8, pp. 114–117, 1965.

R. H. Dennard et al., "Design of ion-implanted MOSFETs with very small physical dimensions", *IEEE Journal of Solid-State Circuits*, vol. 9, no. 5, pp. 256–268, 1974.

Mark Horowitz, "Computing's energy problem (and what we can do about it)", *ISSCC Keynote*, 2014.

David Patterson, "The trouble with multicore: Chipmakers are busy designing microprocessors that most programmers can’t handle", *IEEE Spectrum*, 2007.
