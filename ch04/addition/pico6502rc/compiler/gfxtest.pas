VAR buttons, i, c;

PROCEDURE gfxDemo;
BEGIN
    CLRGFX;
    LINE 0, 0, 319, 239, 2;
    LINE 319, 0, 0, 239, 5;
    RECT 80, 60, 160, 120, 6;
    PLOT 160, 120, 7
END;

PROCEDURE fillTopWhite;
BEGIN
    i := 0;
    WHILE i < 40 DO
    BEGIN
        WRITE BLOCK TO SCREEN + i;
        WRITE 1 TO COLOR + i;
        i := i + 1
    END
END;

PROCEDURE fillTopColor;
BEGIN
    i := 0;
    WHILE i < 40 DO
    BEGIN
        WRITE BLOCK TO SCREEN + i;
        WRITE c TO COLOR + i;
        i := i + 1
    END
END;

PROCEDURE cycleRect;
BEGIN
    c := c + 1;
    IF c > 15 THEN
        c := 2;
    RECT 80, 60, 160, 120, c
END;

PROCEDURE handleInput;
BEGIN
    IN buttons;
    IF buttons = 254 THEN
        CALL gfxDemo;
    IF buttons = 253 THEN
        CLRGFX;
    IF buttons = 251 THEN
        CALL cycleRect;
    IF buttons = 247 THEN
        CALL fillTopColor
END;

BEGIN
    WRITE 6 TO BORDER;
    WRITE 0 TO BGCOLOR;
    CALL fillTopWhite;
    CALL gfxDemo;
    c := 2;
    WHILE 1 = 1 DO
        CALL handleInput
END.
