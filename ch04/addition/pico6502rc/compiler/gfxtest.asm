; PL/0 to 6502 Assembly with I/O Extensions
; Generated code

        .org $8000

; Hardware registers
SCREEN    = $0400
COLOR    = $D800
BORDER    = $D000
BGCOLOR    = $D001
CURSOR_X    = $D002
CURSOR_Y    = $D003
BUTTONS    = $DC00
GFX_X    = $D010
GFX_Y    = $D012
GFX_COLOR    = $D013
GFX_CMD    = $D014
GFX_X2    = $D015
GFX_Y2    = $D017
BLOCK    = $0080
BLOCK_TOP    = $0081
BLOCK_BOT    = $0082
BLOCK_L    = $0083
BLOCK_R    = $0084
BLOCK_UL    = $0085
BLOCK_UR    = $0086
BLOCK_LL    = $0087
BLOCK_LR    = $0088
BLOCK_H    = $0089
BLOCK_V    = $008A
BLOCK_X    = $008B
BLOCK_BS    = $008C
BLOCK_FS    = $008D
BLOCK_CHK    = $008E
BLOCK_DOT    = $008F

proc_fillTop_0:
        LDA #$00
        LDX #$00
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
while_start_3:
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$28
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        TXA
        SBC $FF
        BCS while_end_4   ; Branch if left >= right
        LDA #$80    ; BLOCK
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
        JMP while_start_3
while_end_4:
        RTS

proc_fillBottom_1:
        LDA #$88
        LDX #$04
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
while_start_5:
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$B0
        LDX #$04
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        TXA
        SBC $FF
        BCS while_end_6   ; Branch if left >= right
        LDA #$80    ; BLOCK
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
        JMP while_start_5
while_end_6:
        RTS

proc_gfxDemo_2:
        LDA #$02
        STA $D014       ; CMD: CLRGFX
        LDA #$00
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$00
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$02
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$3F
        LDX #$01
        STA $D015       ; GFX_X2 low
        STX $D016       ; GFX_X2 high
        LDA #$EF
        LDX #$00
        STA $D017       ; GFX_Y2
        LDA #$03
        STA $D014       ; CMD: LINE
        LDA #$3F
        LDX #$01
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$00
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$05
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$00
        LDX #$00
        STA $D015       ; GFX_X2 low
        STX $D016       ; GFX_X2 high
        LDA #$EF
        LDX #$00
        STA $D017       ; GFX_Y2
        LDA #$03
        STA $D014       ; CMD: LINE
        LDA #$50
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$3C
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$06
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$A0
        LDX #$00
        STA $D015       ; GFX_X2 (width) low
        STX $D016       ; GFX_X2 (width) high
        LDA #$78
        LDX #$00
        STA $D017       ; GFX_Y2 (height)
        LDA #$04
        STA $D014       ; CMD: RECT
        LDA #$A0
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$78
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$07
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$01
        STA $D014       ; CMD: PLOT
        LDA #$A1
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$78
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$02
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$01
        STA $D014       ; CMD: PLOT
        LDA #$A0
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$79
        LDX #$00
        STA $D012       ; GFX_Y
        LDA #$05
        LDX #$00
        STA $D013       ; GFX_COLOR
        LDA #$01
        STA $D014       ; CMD: PLOT
        RTS

        LDA #$06
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; BORDER
        LDX #$D0
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$00
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$01    ; BGCOLOR
        LDX #$D0
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$00
        LDX #$00
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
while_start_7:
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$B0
        LDX #$04
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        TXA
        SBC $FF
        BCS while_end_8   ; Branch if left >= right
        LDA #$20
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$0E
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $22       ; i (low)
        LDX $23       ; i (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $22       ; i = (low byte)
        STX $23       ; i = (high byte)
        JMP while_start_7
while_end_8:
        JSR proc_fillTop_0    ; CALL fillTop
        JSR proc_fillBottom_1    ; CALL fillBottom
        LDA #$47
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$29
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$46
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2A
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$58
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2B
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$20
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2C
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$54
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2D
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$45
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2E
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$53
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2F
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$54
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$30
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$29
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2A
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2B
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$01
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2C
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$07
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2D
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$07
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2E
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$07
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$2F
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$07
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$30
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$41
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$51
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$3D
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$52
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$44
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$53
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$52
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$54
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$57
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$55
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$20
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$56
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$42
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$57
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$3D
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$58
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$43
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$59
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$4C
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5A
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$52
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5B
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$20
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5C
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$58
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5D
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$3D
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5E
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$43
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$5F
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$4F
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$60
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$4C
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$61
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$52
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$62
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$20
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$63
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$59
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$64
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$3D
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$65
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$42
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$66
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$4C
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$67
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA #$4B
        LDX #$00
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; SCREEN
        LDX #$04
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$68
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        JSR proc_gfxDemo_2    ; CALL gfxDemo
        LDA #$02
        LDX #$00
        STA $24       ; c = (low byte)
        STX $25       ; c = (high byte)
while_start_9:
        LDA #$01
        LDX #$00
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        BNE while_end_10
        CPX $FF
        BNE while_end_10
        LDA BUTTONS     ; Read buttons
        LDX #$00
        STA $20       ; Store to buttons
        STX $21
        LDA $20       ; buttons (low)
        LDX $21       ; buttons (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$FE
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        BNE if_end_11
        CPX $FF
        BNE if_end_11
        JSR proc_gfxDemo_2    ; CALL gfxDemo
if_end_11:
        LDA $20       ; buttons (low)
        LDX $21       ; buttons (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$FD
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        BNE if_end_12
        CPX $FF
        BNE if_end_12
        LDA #$02
        STA $D014       ; CMD: CLRGFX
if_end_12:
        LDA $20       ; buttons (low)
        LDX $21       ; buttons (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$FB
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        BNE if_end_13
        CPX $FF
        BNE if_end_13
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $24       ; c = (low byte)
        STX $25       ; c = (high byte)
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$0F
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        TXA
        SBC $FF
        BCC if_end_14   ; left < right
        BEQ if_end_14   ; left = right
        LDA #$02
        LDX #$00
        STA $24       ; c = (low byte)
        STX $25       ; c = (high byte)
if_end_14:
        LDA #$50
        LDX #$00
        STA $D010       ; GFX_X low
        STX $D011       ; GFX_X high
        LDA #$3C
        LDX #$00
        STA $D012       ; GFX_Y
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        STA $D013       ; GFX_COLOR
        LDA #$A0
        LDX #$00
        STA $D015       ; GFX_X2 (width) low
        STX $D016       ; GFX_X2 (width) high
        LDA #$78
        LDX #$00
        STA $D017       ; GFX_Y2 (height)
        LDA #$04
        STA $D014       ; CMD: RECT
if_end_13:
        LDA $20       ; buttons (low)
        LDX $21       ; buttons (high)
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$F7
        LDX #$00
        STA $FE         ; right (low)
        STX $FF         ; right (high)
        PLA             ; left (high)
        TAX
        PLA             ; left (low)
        CMP $FE
        BNE if_end_15
        CPX $FF
        BNE if_end_15
        JSR proc_fillTop_0    ; CALL fillTop
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$00
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$01
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$02
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$03
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
        LDA $24       ; c (low)
        LDX $25       ; c (high)
        PHA             ; Save value low
        TXA
        PHA             ; Save value high
        LDA #$00    ; COLOR
        LDX #$D8
        PHA             ; Save left (low)
        TXA
        PHA             ; Save left (high)
        LDA #$04
        LDX #$00
        STA $FE         ; right (low) -> temp
        STX $FF         ; right (high) -> temp
        PLA             ; Restore left (high)
        TAX
        PLA             ; Restore left (low)
        CLC
        ADC $FE         ; Add low bytes
        PHA
        TXA
        ADC $FF         ; Add high bytes with carry
        TAX
        PLA
        STA $FE         ; Address low
        STX $FF         ; Address high
        PLA
        TAX             ; Restore value high
        PLA             ; Restore value low
        LDY #$00
        STA ($FE),Y     ; Write to address
if_end_15:
        JMP while_start_9
while_end_10:

halt:
        JMP halt        ; Halt

; 16-bit multiply: (A:X) * ($FE:$FF) -> (A:X)
multiply:
        STA $F0         ; multiplicand low
        STX $F1         ; multiplicand high
        LDA #$00
        STA $F2         ; result low
        STA $F3         ; result high
        LDX #$10        ; 16 bits
mul_loop:
        LSR $F1         ; Shift multiplicand right
        ROR $F0
        BCC mul_skip
        CLC
        LDA $F2
        ADC $FE
        STA $F2
        LDA $F3
        ADC $FF
        STA $F3
mul_skip:
        ASL $FE         ; Shift multiplier left
        ROL $FF
        DEX
        BNE mul_loop
        LDA $F2
        LDX $F3
        RTS

; 16-bit divide: (A:X) / ($FE:$FF) -> (A:X)
divide:
        STA $F0         ; dividend low
        STX $F1         ; dividend high
        LDA #$00
        STA $F2         ; result low
        STA $F3         ; result high
        LDX #$10        ; 16 bits
div_loop:
        ASL $F0         ; Shift dividend left
        ROL $F1
        ROL $F2
        ROL $F3
        LDA $F2
        SEC
        SBC $FE
        TAY
        LDA $F3
        SBC $FF
        BCC div_skip
        STA $F3
        STY $F2
        INC $F0
div_skip:
        DEX
        BNE div_loop
        LDA $F0
        LDX $F1
        RTS

; Screen output: Write value in A:X to screen
screen_out:
        PHA             ; Save value
        LDA $D002       ; Get cursor X
        CLC
        ADC #$01        ; Increment
        CMP #$28        ; 40 columns?
        BNE so_no_wrap
        LDA #$00        ; Wrap to 0
        PHA
        LDA $D003       ; Increment Y
        CLC
        ADC #$01
        CMP #$1E        ; 30 rows?
        BNE so_save_y
        LDA #$00        ; Wrap
so_save_y:
        STA $D003
        PLA
so_no_wrap:
        STA $D002       ; Save cursor X
        PLA             ; Restore value
        LDX $D003       ; Y position
        LDY $D002       ; X position
        ; Calculate screen offset
        RTS
