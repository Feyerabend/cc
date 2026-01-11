; C64-Style Demo for Pico Display Pack
; Demonstrates character display, colors, and button input

.org $8000

; Zero page variables
counter = $20
color_idx = $21
button_prev = $22

start:
    ; Initialize
    LDA #$00
    STA counter
    STA color_idx
    LDA #$FF
    STA button_prev
    
    ; Set border and background colors
    LDA #$06        ; Blue border
    STA $D000
    LDA #$00        ; Black background
    STA $D001
    
    ; Clear screen with spaces
    LDX #$00
clear_loop:
    LDA #$20        ; Space character
    STA $0400,X
    STA $0500,X
    STA $0600,X
    STA $0700,X
    LDA #$0E        ; Light blue
    STA $D800,X
    STA $D900,X
    STA $DA00,X
    STA $DB00,X
    INX
    BNE clear_loop
    
    ; Draw title at top
    LDX #$00
title_loop:
    LDA title_text,X
    BEQ title_done
    STA $0428,X         ; Row 1, centered-ish
    LDA #$01            ; White
    STA $D828,X
    INX
    CPX #$28            ; Max 40 chars
    BNE title_loop
title_done:

    ; Draw instructions
    LDX #$00
inst_loop:
    LDA inst_text,X
    BEQ inst_done
    STA $04A0,X         ; Row 4
    LDA #$0D            ; Light green
    STA $D8A0,X
    INX
    CPX #$28
    BNE inst_loop
inst_done:

    ; Draw color bar labels
    LDX #$00
colorbar_loop:
    LDA colorbar_text,X
    BEQ colorbar_done
    STA $0518,X         ; Row 7
    LDA #$07            ; Yellow
    STA $D918,X
    INX
    CPX #$28
    BNE colorbar_loop
colorbar_done:

    ; Main loop
main_loop:
    ; Draw animated color bar (row 8)
    LDA color_idx
    AND #$0F
    TAX
    LDY #$00
draw_bar:
    TXA
    AND #$0F
    STA $D940,Y         ; Row 8 color RAM
    LDA #$A0            ; Full block character
    STA $0540,Y
    INX
    INY
    CPY #$28            ; 40 chars wide
    BNE draw_bar
    
    ; Increment color index slowly
    INC counter
    LDA counter
    AND #$0F
    BNE skip_color_inc
    INC color_idx
skip_color_inc:

    ; Check buttons
    LDA $DC00
    STA $23                 ; Save current state
    EOR button_prev         ; XOR with previous
    AND button_prev         ; Mask with previous (detect release)
    STA $24                 ; Save edge
    LDA $23
    STA button_prev         ; Update previous
    
    ; Button A - Change border
    LDA $24
    AND #$01
    BEQ check_b
    LDA $D000
    CLC
    ADC #$01
    AND #$0F
    STA $D000
    
check_b:
    ; Button B - Change background
    LDA $24
    AND #$02
    BEQ check_x
    LDA $D001
    CLC
    ADC #$01
    AND #$0F
    STA $D001

check_x:
    ; Button X - Show X pressed
    LDA $DC00
    AND #$04
    BNE check_y
    LDA #$58                ; 'X'
    STA $05E0               ; Row 12
    LDA #$02                ; Red
    STA $D9E0
    JMP check_done
    
check_y:
    ; Button Y - Show Y pressed  
    LDA $DC00
    AND #$08
    BNE check_done
    LDA #$59                ; 'Y'
    STA $05E0
    LDA #$05                ; Green
    STA $D9E0

check_done:
    ; Clear button display if nothing pressed
    LDA $DC00
    AND #$0C
    CMP #$0C
    BNE no_clear
    LDA #$20                ; Space
    STA $05E0

no_clear:
    ; Display counter at bottom
    LDA counter
    LSR A
    LSR A
    LSR A
    LSR A
    AND #$0F
    CLC
    ADC #$30                ; Convert to ASCII digit
    CMP #$3A
    BCC counter_ok
    ADC #$06                ; A-F
counter_ok:
    STA $0790               ; Bottom row
    LDA #$0F                ; Light grey
    STA $DB90
    
    LDA counter
    AND #$0F
    CLC
    ADC #$30
    CMP #$3A
    BCC counter_ok2
    ADC #$06
counter_ok2:
    STA $0791
    LDA #$0F
    STA $DB91
    
    ; Small delay loop
    LDX #$FF
delay_outer:
    LDY #$20
delay_inner:
    DEY
    BNE delay_inner
    DEX
    BNE delay_outer
    
    JMP main_loop

; Text data
title_text:
    .asc "** PICO 6502 EMULATOR **"
    .byte $00

inst_text:
    .asc "A=BORDER B=BG X/Y=TEST"
    .byte $00

colorbar_text:
    .asc "ANIMATED COLOR BAR:"
    .byte $00