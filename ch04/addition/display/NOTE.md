
## Note

There are very different C-*implementations* of the driver, or drivers, for the
Pimoroni DisplayPack 2.0 in the folders. They might be adjusted to the aiming
at the time: for games and animations perhaps we are not careful with the timing
of DMA transfers e.g., as they do not clearly affect the gaming itself. But
when drawing finer lines, like the clock hands, we would be more careful and
do consider aesthetics.

You might, as a project, try to mitigate these variations. Make a general driver
for different types of concerns, or different drivers (considering memory space)
for different purposes.

