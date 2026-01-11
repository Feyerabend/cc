
## Get the Pico 6502 Retro Computer Running ..

Start assembling the demo program (in assembly):

```bash
python asm.py demo.asm demo.bin -v
```

The output:

```bash
Pass1 L4: .org $8000
Pass1 L7: counter = $0020
Pass1 L8: color_idx = $0021
Pass1 L9: button_prev = $0022
Pass1 L11: start: @ $8000
Pass1 L27: clear_loop: @ $8016
Pass1 L43: title_loop: @ $8037
Pass1 L52: title_done: @ $8049
Pass1 L56: inst_loop: @ $804B
Pass1 L65: inst_done: @ $805D
Pass1 L69: colorbar_loop: @ $805F
Pass1 L78: colorbar_done: @ $8071
Pass1 L81: main_loop: @ $8071
Pass1 L87: draw_bar: @ $8078
Pass1 L104: skip_color_inc: @ $8093
Pass1 L125: check_b: @ $80B3
Pass1 L136: check_x: @ $80C4
Pass1 L147: check_y: @ $80D8
Pass1 L157: check_done: @ $80E9
Pass1 L166: no_clear: @ $80F7
Pass1 L179: counter_ok: @ $8108
Pass1 L191: counter_ok2: @ $811D
Pass1 L198: delay_outer: @ $8127
Pass1 L200: delay_inner: @ $8129
Pass1 L209: title_text: @ $8132
Pass1 L213: inst_text: @ $8134
Pass1 L217: colorbar_text: @ $8136
Assembled 380 bytes to demo.bin
```

We now have a file named `demo.bin`. Next convert the
binary to a header file for compiling with `main.c`:

```bash
python bin2header.py program.bin rom.h rom_data
```

The output:

```bash
Generated rom_data: 380 bytes as 'rom_data'
```

Then compile all the .c/.h files, and transfer to the Pico.


